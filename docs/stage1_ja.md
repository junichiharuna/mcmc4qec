# 第1段階: bit-flip 基盤の設計と制約

**履歴文書:** これは binary 基盤を完成した時点の記録である。続いて実装した三種のノイズ、
BAR、Stim DEM と現在の制約は [初期ライブラリの設計](initial_library_ja.md) を参照。
以下の「未実装」「次に進める」は第1段階時点の記述として残す。

2026-09-30。仕様 v0.2 を段階的に実装するための、独立パッケージの最初の到達点。
仕様ファイル名は v0.1 だが本文は v0.2 である。本書は全仕様の実装完了や公開を意味しない。

## 今回の範囲

静的 CSS の bit-flip を、小規模列挙と比較できる基盤として実装する。
計算中核は研究用 CSV、符号名 factory、PBS、CLI、研究チェックアウトの import に依存しない。
必須の外部依存は NumPy のみとし、外部デコーダーとの接続を任意の薄い wrapper として分離する。

| 機能 | 第1段階で扱う範囲 |
| --- | --- |
| 状態とモデル | 有限長の二値ベクトル、二値線形の syndrome / observable 写像、CSS bit-flip |
| ノイズ | 独立 bit-flip。位置ごとに `p * scales[i]` の異なる確率を指定可能 |
| 復号と失敗 | 固定された決定論的 decoder、予測論理 observable、共通の failure predicate |
| 更新 | OBF、Zanella、単一状態内の cluster exchange、静的 stabilizer flip |
| 推定 | 小規模 exact 列挙、試行数固定の direct MC |
| 条件付き標本 | `sample_faulty`。棄却と lazy step を保持した複数の独立 chain |
| 診断 | Hamming weight 系列の IAT・ESS・split R-hat。推定不能は理由とともに返す |
| 保存 | `Result.to_json()` / `Result.from_json()` と実行条件・識別情報 |

独立 chain は同じ温度の別乱数系列である。parallel tempering の replica 交換は実装しない。
一般二値線形モデルや独自二値ノイズを使える契約と、非二値・回路モデルへの対応は区別する。

## 共有する確率と失敗の定義

`Problem` が model、noise、decoder、failure を束ねる。
標準の failure は予測 observable と真の observable の不一致である。
exact、direct MC、MCMC は同じ predicate を呼び、列挙だけを decoder と異なる式で判定しない。
独自の predicate は `CallableFailure` に識別子とともに渡す。

`CSSCode.bit_flip_model()` は X 誤り `e` に対して `hz @ e mod 2` を syndrome、
`lz @ e mod 2` を observable とする。decoder が返すものは observable の予測値であり、
物理補正そのものではない。物理補正を返す外部 decoder は利用者が指定した論理写像で変換する。
出力の型や長さから物理補正と論理予測を推測しない。

`noise.log_prob(state, p)` はその同じ状態空間の正規化確率の対数を返す。
support 外は負の無限大で表し、不正な確率・NaN・状態はエラーにする。
`noise.sample(p, rng)` は同じ分布を生成しなければならない。
一般ノイズの MH に iid の重み差の式を代用しない。
独自 noise の正規化や decoder の決定性は利用者側の契約でもあり、有限個のテストで任意の
callable の性質を証明するものではない。

固定状態に対して異なる結果を返す確率的 decoder は対象外。
実行途中に prior、設定、predicate を変えて同一の定常分布として扱わない。
独自実装の識別子・metadata と、その実装のソースを利用者が保存する必要がある。
JSON は実行結果を復元するもので、任意の Python callable を再構築しない。

## 外部デコーダーの薄い adapter

`DecoderAdapter` は既存の `decode` を持つ object を受ける。
`output_kind="correction"` なら物理補正を observable に写す `logical_map` が必須、
`"observable"` なら既に論理予測なので `logical_map` は禁止する。
BP-OSD はこの generic wrapper に `distribution="ldpc"` を指定して接続する。
`settings` は記録情報であり、wrapped object をその設定に変更する機能ではない。
入力の 1D / 2D syndrome 表現は保持するが、phenomenological の履歴の意味と境界を
検証済みであることは意味しない。

`PyMatchingAdapter` は構築時に相関を有効にしたかを `built_with_correlations` で必須指定し、
decode 時の `enable_correlations` を一致させる。
静的な `matching_from_check_matrix` は二つを超える check に接続する column を拒否する。
既存 object を受け取る wrapper だけでは、元 DEM の情報欠落や graph の完全性を確認できない。
既存 decoder の構築条件は利用者が管理し記録する。

## カーネルと公開既定値

| 設定 | 公開既定 |
| --- | --- |
| OBF | 0 |
| Zanella (Z) | 0.7 |
| Cluster exchange (H) | 0.3 |
| Stabilizer flip | 0 |
| Cluster size | 2 組の occupied / empty 位置 |
| Chain 数 | 1 |
| Lazy probability | 0.05 |

lazy は混合カーネルの選択に先立つ自己ループの確率である。
上表の OBF/Z/H/stabilizer の和は 1 を要求し、暗黙に正規化しない。
したがって既定の一歩あたりの確率は Z 0.665、H 0.285、lazy 0.05 となる。
lazy が正であれば support 内の状態に自己ループを与えられるが、失敗集合の非連結性は解消しない。
既定値を展開した設定を結果に記録する。

OBF は一つの bit を反転する提案、Z は単一 bit 近傍の密度に応じた提案を行う。
Z は一般の `log_prob` を使って近傍を走査する参照実装であり、研究 runner の高速化を
そのまま移植したものではない。長い状態や高価な density / decoder での速度は保証しない。

H は**一つの状態内**で 1 の位置と 0 の位置を交換し、Hamming weight を保つ。
複数 replica 間の交換ではない。必要な数の 1 または 0 がなければ状態を動かせない。
位置によって確率が違う noise では、重みが同じでも密度が同じとは限らないため、
一般の密度比と提案比で MH 判定する。三量子ビットの例では `cluster_k=1` を明示する。

Stabilizer flip も候補の failure を再評価する。標準論理判定の不変性を独自 predicate に
無条件で仮定して復号を省略しない。
既存研究コードの `run_rimc_mixed` の既定 Z+PT は変更しない。
その引数体系を維持する互換 wrapper は第1段階には含めない。

## 結果を解釈する際の境界

`exact` は全状態数に上限を設け、小さい基準問題の絶対失敗確率と条件付き重みを計算する。
指数的な列挙を大きな符号の通常経路にしない。

`direct_mc` は固定試行数で独立試行し、失敗数、試行数、点推定、95% Wilson 区間を返す。
この区間は有限標本の二項比率に対する近似区間であり、被覆率の厳密保証ではない。
失敗数が 0 でも正の区間上限と警告を残す。MC で失敗を見なかったことを真の率 0 の証明としない。
失敗数で途中停止する推定器の区間と混同しない。

`sample_faulty` が生成するのは failure に条件付けた分布であり、絶対失敗確率ではない。
burn-in 後も棄却・lazy を一歩として数え、採否によらず thinning を適用する。
移動した状態だけを保存するフィルタは行わず、同じ状態の反復を保存する。
保存状態の shape は `(chains, samples, bits)` である。
初期化は有限回の探索で打ち切り、見つからなければ `InitializationError` とする。
これは空の失敗集合の証明ではない。希少領域では既知の supported faulty state を明示的に渡す。
初期値の形状、support、failure 条件は検査する。

診断は Hamming weight という一つの観測量に対する診断である。
定数・短い系列、chain が一つの場合など、計算不能な量は欠測と理由を返す。
IAT、ESS、split R-hat が良好でも、他の領域に到達できたこと、収束、エルゴード性、
有限時間の正確性は証明されない。既存の min-weight decoder の定理の仮定を、
BP-OSD・独自 decoder・将来の phenomenological / 回路モデルに自動適用しない。

結果は設定、seed と乱数系列、モデルの行列 hash、noise / decoder / predicate の識別情報、
ライブラリやソースの識別情報、実行時間を保存する。
ソース commit が取得不能なら欠測として扱い、wheel のみから完全な provenance を推測しない。
現在の未 commit パッケージの `source_commit` と、研究ソースの `research_reference_commit` は
別の情報として記録する。研究参照 commit をこの新規コードの commit として表示しない。

## 検証の読み方

受入テストは小さい repetition code の `P_L = 3p² - 2p³`、非同一 bit 確率での
遷移確率と詳細釣合い、同じ predicate による exact / MC / MCMC の比較、
support 端点、初期化、不正入力、棄却保持、seed 再現、JSON 往復を対象にする。
詳細釣合いに加え、到達可能性・周期性や、失敗集合に閉じ込められる反例も分けて評価する必要がある。
小規模での一致を大きい符号・全ノイズ・すべての decoder の保証に拡張しない。

CI 定義は wheel をインストールして Python 3.11 / 3.12 で検証する。
source tree の `pythonpath` を無効にし、core と任意依存の確認を分ける。
CI ファイルを追加したことと、ホストされた CI が実行済みであることは別である。
実際に実施した検証、環境、件数は作業の進捗記録に残す。

## 次に進める段階

1. **Depolarising**: I/X/Y/Z の同時カテゴリ分布と両セクターの failure を実装する。
   Y の相関を保ち、単一カテゴリ更新と cluster の forward / reverse 比、正規化、詳細釣合いを
   列挙で検証する。X/Z を独立 bit-flip として生成する近道は採らない。
2. **Phenomenological**: ラウンド数、初期・終端境界、データと測定の確率、履歴と差分の表現を
   明示する spacetime model を実装する。少数ラウンド列挙で観測と failure を照合し、
   最後のデータ状態だけを静的 decoder に渡す置換を防ぐ。
3. **Splitting / BAR**: 一般 `log_prob` の比を使う固定 decoder・共通失敗集合の標準経路を
   先に検証する。その後 p ごとに decoder を変える明示近似モードを分離し、
   sampling p、decoder prior、近似理由と感度を記録する。
4. **Adapter の拡張**: Depolarising の両セクターと phenomenological の履歴入力を接続する。
   Stim DEM では一つの `error` 機構を保持し、`^` の各片を独立故障に分割しない。
   p 間の機構同一性と H/L を検証し、Stim sampler と照合する。
5. **初期公開準備**: 三種のノイズについて受入条件を満たし、必要な互換層と文書を整える。
   正式配布名・公開先・license・第三者権利・引用情報を確定してから公開を判断する。
6. **回路 baseline と拡張**: 排他的な物理 location fault を持つ独立経路を設計し、
   単一 fault の追加・削除・置換と同条件 direct MC を先に検証する。
   論文のラウンド数・境界・補正範囲に揃えてから再現を評価し、続いて Z / cluster を検証する。
   回路 stabilizer flip は当面対象外とする。

初期公開の目標は bit-flip・depolarising・phenomenological の三種である。
第1段階の完了だけでこの目標を満たしたとは扱わない。
この段階では重い sweep、cluster ジョブ、公開 repo 作成、push、package publish、license 選択を行わない。
