# WP-P 完了メモ：BAR 不確かさと論文手順の照合

## 小仕様と実装

`estimate_logical_error` の `uncertainty` は既定を `block_bootstrap` に固定し、`cross_chain` を追加した。
`cross_chain` は保存軌道と pooled BAR 点推定をそのまま使い、同じ chain 番号の隣接 BAR log ratio を組にして標本共分散を chain 数で割る。
この組により共有 rung を通じた比の相関を含め、anchor の独立 log 分散を従来どおり別に加える。
これは論文 `main.tex` 615–623 行の観測量平均に対する cross-chain 標準誤差を BAR に漸近的に適用したものであり、論文が full BAR の被覆を検証したと主張しない。
chain が 1 本なら `ValueError` とし、各 chain に双方向 overlap がないときは点推定を残して MCMC 区間を未定義にする。
既定引数、点推定、seed 系列、block bootstrap の計算経路は維持した。
`uncertainty_method` は既存の metadata に方法を記録し、cross-chain の比の共分散も metadata に保存する。

`benchmarks/bar_paper_protocol.py` は同一 seed の保存軌道を block と cross-chain で再利用できる設定を持ち、固定 cohort 2026–2045 の一部を invocation ごとに出力する。
`--samples` は固定 cut 群では cut 後の保存数を表し、paper 群では IAT cut 前の全 trace 歩数を表し、CSV に `total_steps` と各 chain の cut を残す。
paper 設定は研究 `src/postprocess.py` と `cluster_scripts/lowp_audit.py` に合わせ、各 chain ごとに最初の負の自己相関で打ち切る IAT を反復推定し、5·IAT の cut が非収束なら半 trace に落とす。
この反復 cut を `diagnostics.py` の `paper_burn_in_cut` に分離し、既存の初期正値ペア IAT とその API 挙動は変えなかった。
paper 設定は研究 runner に独立 lazy 抽選がないため `lazy=0` とし、現行既定の 4 chain 設定は `lazy=0.05` を維持する。
論文本文の各 chain の記述と研究の実験 runner は一致し、`postprocess.py` の 2D 入力だけにある共通中央値 cut はこの実験では使わない。
四条件の scaling と drift は未burnの checkpoint、multistart と dispersion は各 chain の burn 後を用いる。
toric d=3 の最小・最大論理基底状態は同一なので、論文どおりの multistart 判定は未判定とし、残る三条件の合格を `paper_vacuous_pass` に分離する。
`--aux-multistart` は異なる faulty な論理組合せから追加 chain を走らせ、その補助四条件を別の欄へ記録する。
BAR の ragged な burn 後標本は pooled BAR を解き、chain 単位の比の散らばりで区間を作るため、同数標本の API に対する漸近誤差近似を不等長 chain に延ばしたものである。
`--make-truth-cache` は同一問題の失敗重みヒストグラムを一度列挙し、符号行列と問題 metadata、パッケージ source、重み counts の SHA-256 を付けて保存する。
`--truth-cache` はその digest を検証し、各 p の exact 真値と exact anchor を重みヒストグラムから求める。
`cached_exact` は重みごとの確率質量の加重和から exact 条件付き重みも復元する。
低 p の `--anchor both` は MC と exact anchor に対して同じ rung 状態・cut・BAR 比・MCMC log 分散・収束診断を一度だけ計算して再利用し、anchor ごとの per-seed CSV と要約 CSV を別々に出す。
`--aggregate` は checked truth cache を必須とし、各 CSV の問題 digest と exact 真値を再計算して一致し、設定ごとに 2026–2045 が重複なく全件ある場合だけ cohort CSV を作る。
per-seed CSV、要約 CSV、標準出力には、診断は証明でないこと、有限 chain の BAR bias は区間外であること、toric の論文 multistart が未判定であること、不等長 cut の cross-chain 共分散が漸近近似であることを明記する。
`bar_sensitivity.py` の正式長さ比較も同じ checked cache から exact 真値と条件付き重みを復元し、20 seed の重複・欠落と provenance を検査してから集計する。
過去の `--truth-file` 入口は WP-M の既存実験用に残すが、dev5 の正式計測には使用しない。

## 実行済みの検証

すべて `A:/dev/mcmc4qec-wt/p` で Python 3.11 の `A:/dev/mcmc4qec/.venv-dev5-source/Scripts/python.exe` を使用した。
研究を参照する際は `RIMC_RESEARCH_ROOT=A:/dev/RIMC` と `PYTHONDONTWRITEBYTECODE=1` を設定し、研究側へ書き込まなかった。
研究側の `git status --porcelain=v1` は出力なしだった。
`python -m pytest tests/test_crossval_research.py -q` は 20 passed、2.13 秒で、凍結された研究 BAR 値 `-1.2130084485394683` とライブラリの Fermi 関数の値の一致を含む。
この照合は live pymbar を再計算するテストではない。
別に `PYTHONDONTWRITEBYTECODE=1` と `RIMC_RESEARCH_ROOT=A:/dev/RIMC` を設定し、読み取り専用 import した研究 `src/splitting_pl.py` の `estimate_pl_ladder_bar` と同じ合成 trace を live pymbar 4.0.3 で評価した。
研究の log ratio `-1.2130084485394683` とライブラリの `-1.213008448539711` の絶対差は `2.426947531830592e-13` だった。
`python -m pytest tests/test_bar_uncertainty.py tests/test_estimation.py -q` は anchor 分散の追加テスト前に 15 passed、8.09 秒だった。
追加後の `python -m pytest tests/test_bar_uncertainty.py -q` は 5 passed、5.62 秒だった。
反復 cut のテスト追加後の同じコマンドは 6 passed、4.94 秒だった。
現行差分の `python -m pytest tests/test_bar_uncertainty.py tests/test_estimation.py tests/test_crossval_research.py -q` は JSON 往復の追加 assert 前に 37 passed、10.57 秒だった。
JSON 往復の追加 assert 後の `python -m pytest tests/test_bar_uncertainty.py -q` は 6 passed、5.78 秒だった。
最終実装差分の `python -m pytest tests/test_bar_uncertainty.py tests/test_estimation.py tests/test_crossval_research.py -q` は 32 passed、5 skipped、9.26 秒だった。
合成 chain の既知の標準誤差と共有 rung の負の共分散、同 seed の点推定一致、1 chain と不正方法の拒否、10 seed の小問題の被覆の緩い回帰を確認した。
研究 `paper/main.tex` 261–282 行の Fermi 関数 `h(t)=1/(1+t)` と `bennett_log_ratio` の score の符号、`src/splitting_pl.py` の BAR の向きを照合した。
研究 `src/postprocess.py` の 1D `burn_in(method="tau",c=5)` と benchmark の `paper_burn_cut` を同じ seed 71 の長さ 250 の合成重み trace に適用し、cut 6 と cap `False` が一致した。
`python -m py_compile benchmarks/bar_paper_protocol.py benchmarks/bar_sensitivity.py src/mcmc4qec/estimation.py tests/test_bar_uncertainty.py` は成功した。
旧 protocol の `--quick --protocol paper50 --region paper --anchor exact --aux-multistart` は 199.98 秒で動作したが、旧共通 cut と burn 後 checkpoint を使うため最終表には使わない。
修正版の `--quick --protocol default_block --region dev4 --anchor mc --verify-api` は 88.62 秒で動作し、seed 2026 の benchmark と API の点推定、全隣接比、log 標準誤差、区間が許容差 `1e-12` 以内で一致した。
この短い実行の点推定 0.43237450 と区間幅 0.077939 は保存 80 の smoke であり、被覆を評価する数値として使わない。
Q 統合後の `--quick --protocol default_cross --region dev4 --anchor mc --truth-cache <cache> --verify-api` は 2.57 秒で、benchmark と API の点推定・比・標準誤差・区間が一致した。
同じ Q 統合後の paper 領域 `--quick --protocol default_cross --anchor both --aux-multistart --verify-api` は 4.26 秒で、MC と exact の両方が API と一致した。
同条件の `default_block` でも MC と exact の両方が API と一致し、4.0 秒以内に終わった。
その MC CSV と単独 `--anchor mc` の CSV は全列一致し、MC/exact 間では BAR 比、cut、scaling、drift、補助 multistart、dispersion が全て一致した。
paper50・paper 領域・全長 250・補助初期値有の seed 2026 でも、`--anchor both` の MC CSV は単独 MC と全列一致し、exact CSV は単独 exact とファイルの bytes が完全一致した。
同じ seed の MC/exact の BAR 比、cut、scaling、drift、補助 multistart、dispersion は一致し、両 anchor を同時に出す所要時間は 19.84 秒だった。
これらは seed 2026 の短い smoke であり、名目被覆の根拠ではない。
Q 統合後の `--make-truth-cache` は全 262144 状態を 36.2 秒で列挙し、失敗状態数 196608、問題 SHA-256 `16d53d251117bb3f52c9e7cff4aa63514d16409364f7d7b7e773977db84f974d`、counts SHA-256 `909d867052c997ee5d0445df5701dd6b8ff1295d61d497af64a36438195056af` を得た。
直接 `exact()` と cache の値は p=0.22 で `0.6026625647015839` と `0.602662564701594` の差 `1.01e-14`、p=0.03 で `0.02107475985928002` と `0.021074759859217335` の差 `6.27e-14` だった。
pilot の package source SHA-256 は `9a09dd24288f3d60bccdd8eef131d538b1357ba07842cb33f0fa81bf81548462` であり、dev5 version を組み込む最終 main の cache は再生成する。

## 統合後に残る科学的計測

| 事前固定の群 | ladder | anchor | chain | burn | 保存数 | 誤差法 | seed |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| 長さ比較 | 0.30/0.26/0.22 | MC 1500 試行 | 4 | 固定 180 | 600、2400、9600 | block 8・30反復 | 2026–2045 |
| dev4 被覆 | 0.30/0.26/0.22 | MC 1500 試行 | 4、4、16、50 | 固定 180 または各 chain 5·IAT | 4 chain は cut 後 600、16/50 は cut 前の全長 250 | block または cross-chain | 2026–2045 |
| 論文領域被覆 | 0.10/0.07/0.05/0.03 | MC 1500 試行と exact | 4、4、16、50 | 固定 180 または各 chain 5·IAT | 4 chain は cut 後 600、16/50 は cut 前の全長 250 | block または cross-chain | 2026–2045 |

4 chain の `default_block` と `default_cross` は同じ seed で同じ保存軌道を再利用し、点推定を変えずに区間幅だけを比較する。
16/50 chain の全長 250 は被覆結果を見る前に計算時間だけから固定し、論文の 2,000,000 step と大きく違うことを表に示す。
全 4 構成で `--aux-multistart` を用い、論文どおりの同一 basis の M は未判定に保ち、異なる faulty start の補助四条件数を別に報告する。
低 p の MC/exact anchor は `--anchor both` で同じ軌道から出すため、4 構成×2領域の 8 回の sampling で 12 cohort の CSV を作る。
paper 領域で最も遅い 50 chain・全長 250・補助初期値有の 1 seed pilot は単独 MC で 24.03 秒、両 anchor 同時出力の改善後で 19.84 秒だった。
両 anchor 同時出力の 20 seed 線形見積は約 397 秒である。
同じ条件の dev4 領域は 13.77 秒、paper 領域の 16 chain は 7.22 秒、固定 4 chain・保存 600 は dev4 5.04 秒と paper 7.55 秒であり、各構成の 20 seed は 600 秒以内の見積である。
計算時間は環境負荷で変動するため、正式実行でも 1 invocation 600 秒を監視し、区間や被覆を見て保存数を変更しない。
全長 250 は非常に短く、pilot でも半 trace cap が発生したため、この探索を論文精度の再現や収束確認とは扱わない。
Q 統合後の main で、事前固定 seed 2026–2045 に対し、dev4 ladder `[0.30,0.26,0.22]` の保存 600・2400・9600 と同じ seed 2026 の点推定差を測る。
保存長を変えるときは固定 burn 180 と block 8 を維持し、`benchmarks/bar_sensitivity.py --samples <N> --burn-in 180 --block 8 --seeds <slice> --label <unique>` を分割実行する。
保存 9600 の seed 2026 pilot は 46.50 秒で、20 seed 全体は約 930 秒と見積もるため、2026–2035 と 2036–2045 の事前固定 10 seed ずつ 2 invocation に分ける。
この pilot の cache 由来 exact 条件付き重みは `4.530131731513127` で、Q 統合後の seed 2026 の BAR 点推定は `0.593407854636081` だったが、正式 20 seed の表には採用しない。
この分割は各 invocation の 600 秒上限のためで、20 seed 全体が 600 秒以内という主張はしない。
初めから決めた全 seed の結果を残し、平均 bias、seed 間散らばり、個別 seed 2026 の推移を示す。
差の縮小が `1/sqrt(N)` に似ても bias 不在の証明とは扱わず、縮小しない場合は固定 180、5·IAT、半 trace の cut と 4、16、50 chain の比較を計画どおりに行う。
`bar_paper_protocol.py` は dev4 と paper ladder `[0.10,0.07,0.05,0.03]`、4 構成、paper 領域では MC と exact anchor の両方を扱う。
各構成の保存長は Q 統合後の sampling だけの pilot に基づき、4 chain は cut 後 600、16/50 chain は cut 前 250 と結果を見る前に固定した。
全 seed の CSV を `--aggregate` で検証する。
被覆数と Wilson 区間、平均区間幅、平均点推定と exact の差、四条件の合否・未判定を `docs/bar_sensitivity_ja.md` に追記する。
この最終表は現時点で未実施であり、短い pilot や dev4 の 13/20 を dev5 の結果と取り違えない。

## 共有ファイルへの統合依頼

`docs/api_en.md` の `estimate_logical_error` に `uncertainty="block_bootstrap"` と `"cross_chain"`、2 chain 以上、独立 chain と定常性の仮定、共有 rung 共分散、独立 anchor 分散を追記する。
README の BAR 制約段落には、区間は混合と不確かさ推定の仮定に依存し、診断合格や論文の平均重み実験が BAR 被覆を保証しないこと、`docs/bar_sensitivity_ja.md` の実測表へ進めることを書く。
`examples/workflows/pl_curve.py` の説明と出力には、既定の短い d=3・p=0.22 実行が名目被覆を保証せず、exact との反例と cohort 表を参照するよう記す。
notebook 02 の同じ説明も直し、メインが再生成する。
公開既定の誤差法や chain 数を変える判断は最終被覆表を見て所有者へ提示する。
共有ファイル、version、wheel、CI、push はメインの担当として未実施である。
