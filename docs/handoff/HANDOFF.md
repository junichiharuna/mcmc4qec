# RIMC ライブラリ実装 引き継ぎ書

更新日: 2026-09-30（JH-homePC ローカル作業）

## 現在の状態

**ユーザーの明示指示により中断済み。自動再開しない。**

ユーザーは仕様案 v0.2 を受けて「これで実装してみようか」と実装を承認した。その後「いったん、codexに引き継がせるから、中断して、引き継ぎ書を作って」と依頼した。実装コードの追加・変更はまだない。準備・調査のみ完了し、テスト・wheel 作成・依存インストール・ジョブ投入は未実施。

## パスと取得済み成果物

- ホスト: `JH-HOMEPC`、シェル: PowerShell 7。
- 作業ルート: `C:\Users\user\Documents\Codex\2026-09-30\task`
- 参照用独立 clone: `C:\Users\user\Documents\Codex\2026-09-30\task\research-source`
- 仕様書: `spec/RIMC_ライブラリ仕様書_v0.1.md`。**ファイル名は v0.1 だが本文は 2026年9月29日版 v0.2**。全文を読み取り済み。30,646 bytes。
- 仕様書 SHA256: `E94731DFCC25AFB44DC5F9E3A30080B5618E52459DBDE37AB4917F8418EFE66B`
- Library 識別情報: `spec/library-identity.json`。Library ID `libfile_3d013a24a82c8191b018b5ddc0e61c52`、backing file ID `file_000000005cf48230a3bd5f335e953cec`、取得時 version `1`。メタデータは JSON に保存。OS 拡張属性の適用は未確認。
- この引き継ぎ書: `HANDOFF.md`。
- `rimc-library`、`src/rimc`、仮想環境、wheel、実装進捗ファイルは未作成。前回の `IMPLEMENTATION_STATUS.md` 書込みは接続断で完了せず、再開時にも存在しないことを確認。

仕様書は取得済みのローカルファイルを再利用できる。最新版を再確認する場合は Library スキルに従い同じ Library ID を解決する。クラウドのパスをローカルパスとして使わず、取得後に読めるバイト列を検証する。既存 Library ファイルを新規作成扱いにしない。

## ソースと変更保護

- 非公開ソース: https://github.com/junichiharuna/RIMC
- 現在の main とローカル参照 clone の HEAD はともに `69efcfcc86af3bf24ca977a098dab0f348601aff` と確認済み。
- 中断時 `git status --porcelain=v1` の変更出力なし。既存研究チェックアウトや未コミット変更には触れていない。この作業で作った独立 clone も未変更。
- 作業ルート自体は Git リポジトリとして初期化していない。次の実装は参照 clone と別のパッケージディレクトリで行う。
- `research-source/AGENTS.md` を読了。軽量ローカル計算のみ、日本語応答、ユーザー指示なしの commit/push 禁止。文書内の研究上の主張は独立検証結果とは扱わない。必要に応じて再読する。
- 別の `.agents/skills` は発見していない。ユーザーホーム全体の列挙はアクセス拒否、`C:\Users\user\.agents` は存在しなかった。
- ローカルメモリは読んでおらず変更もしていない。
- 元リポジトリに LICENSE がないとの仕様記載がある。ユーザー自身のローカル実装として進める依頼だが、ライセンスを代理で選ばない。第三者コードの権利は公開前に確認する。

## 実行環境・確認結果

Python の絶対パス:

```text
C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe
```

Python 3.11.9。中断時に installed metadata を読み取った結果:

| 依存 | バージョン |
| --- | --- |
| numpy | 2.4.6 |
| scipy | 1.17.1 |
| pytest | 9.1.1 |
| pymatching | 2.4.0 |
| ldpc | 2.4.1 |
| stim | 1.16.0 |
| bposd | 2.1 |
| pymbar | 4.0.3 |
| setuptools | 83.0.0 |
| build / wheel | 未インストール |

NumPy/SciPy の import は成功。他の依存は metadata 確認のみで、アダプター動作検証ではない。PATH 経由の `python` 検索は不安定だったため絶対パスを使った。

Git: `C:\Program Files\Git\cmd\git.exe`、2.53.0.windows.2。clone を所有するユーザーと sandbox ユーザーが異なるため、Git コマンドでは次のように **コマンド単位** の指定を使う（global 設定は変更していない）。

```powershell
& 'C:\Program Files\Git\cmd\git.exe' `
  -c safe.directory=C:/Users/user/Documents/Codex/2026-09-30/task/research-source `
  -C research-source status --porcelain=v1
```

global ignore ファイルへの Permission denied 警告が出るが、HEAD と status は取得できた。通常 sandbox のネットワークでは clone が接続失敗し、承認された権限付き実行で取得した。既存 clone を再利用し、再 clone は不要。

前回は `exec-server transport disconnected` で停止し、復旧操作の自動承認レビューも timeout（安全性による拒否ではない）。ユーザーが接続復旧を報告した後、ローカルコマンド実行成功を確認した。現在の中断理由は **ユーザーの指示** であり接続断ではない。

実装・テスト用の常駐プロセスは起動していない。再開後のコマンドはすべて完了した。以前の接続復旧／進捗書込みの待機は前回終了時に停止済み。`Get-Process` では Python PID `11252`（開始 2026-09-30 08:24:57）を確認したが、この作業が起動した実装・テストジョブではない。コマンドライン確認は `Get-CimInstance Win32_Process` がアクセス拒否となったため用途を特定していない。網羅的な確認はできておらず、他作業の可能性があるこのプロセスを終了していない。

## 完了／未実施

完了: 仕様書全文読取、Library ID 保存、ソース clone、main/HEAD と clean status 確認、AGENTS 読取、CSS/decoder 契約と既存 kernels、runner 引数、postprocess、BAR 実装の読取、主要依存の metadata 確認、回路論文 v2 の該当節の確認。

失敗した準備操作: 通常 sandbox の clone（ネットワーク接続失敗）、Library 補助資料 `materialization.md` の読取（resource 読取失敗）、汎用添付 download（保存ディレクトリの権限拒否）。最終的には Library が返した認可済み転送先から仕様書を取得し、ローカル UTF-8 本文を確認した。PowerShell の初回出力は文字化けしたが `[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new()` で正常に全文を読めた。

**テスト合格数・失敗数はともに未計測。pytest は一度も実行していない。** installed wheel、exact/MC、seed 再現性、外部アダプター、無効入力、回路 baseline、既存 tests の移植・実行はすべて未実施。新コード・性能改善・数値的一致を報告できる段階ではない。

## 実装の必須要件（仕様本文を優先）

1. 独立した再利用パッケージ（提案構成 `src/rimc`、`pyproject.toml`）。ユーザー独自の code/model、noise、decoder、failure predicate を注入可能にする。計算中核を CSV、CLI、並列ジョブ、研究 factory から分離する。
2. 初期対象 CSS。独立 bit-flip、I/X/Y/Z 同時分布を保つ depolarising、データ・測定故障と syndrome 履歴を持つ phenomenological を含む。X/Z を独立生成して Y 相関を失わせない。時間境界・測定表現・ラウンド数・データと測定の確率を明示する。
3. OBF、Z-OBF、cluster exchange、任意の静的 CSS stabilizer flip を独立・合成可能にする。公開既定は Z+H。README の候補値は Z 0.7、cluster 0.3、cluster_k=2、1 replica。既存研究 runner は Z+PT（Z 1、cluster 0、4 replicas）であり変更しない。展開後の設定を結果に残す。
4. `noise.log_prob` は同じ状態空間上の正規化確率を扱い、ゼロ support を明示。MH は log density と forward/reverse proposal ratio を使う。全ノイズに weight-only 式を流用しない。混合確率を暗黙に再正規化しない。対応しない組合せは明示エラー。
5. decoder の出力意味は明示する。物理補正を論理予測に写す L を指定し、型・長さから意味を推測しない。exact、direct MC、MCMC で同じ failure predicate を使う。stabilizer による failure 不変を独自 predicate に仮定しない。
6. `sample_faulty`、`direct_mc`、`estimate_logical_error`、`diagnose` 相当の公開入口、名前付き config/result、seed・config・モデル識別/ハッシュ・decoder 設定/version・ソース commit・実行時間・診断を残す。失敗ゼロを確定した率ゼロとしない。棄却時の同一状態も標本に残す。
7. BAR は固定 decoder／共通失敗集合の標準経路と、p ごとに BP-OSD を変える **明示選択された近似経路** を分ける。後者はユーザーが既に認識した研究上の選択であり、新発見の誤りと扱わない。sampling_p、decoder_prior、近似理由を保存。BAR でも一般 log_prob を使う。
8. 既存 PyMatching／BP-OSD オブジェクトを受ける薄い wrapper。phenomenological では履歴入力を保つ。PyMatching の hyperedge を黙って欠落させない。correlated matching は構築時と decode 時の設定を揃える。
9. Stim DEM の各 error 機構を保ち、`^` は同じ機構の相関する分解片として扱う。独立故障として分割しない。潜在故障・detector・observable を Stim sampler と照合。p 依存モデル族の故障同一性/H/L を検証。物理回路の排他カテゴリ分布と DEM の独立 Bernoulli 分布を同一視しない。`approximate_disjoint_errors` を無断で有効にしない。
10. 診断良好は正しさ・収束・エルゴード性の証明ではない。`misc/ergodicity_note` の主定理には generic weighted minimum-weight decoder 等の仮定があり、BP-OSD・phenomenological・回路一般へ無条件適用しない。
11. 日本語の設計/進捗/制約文書と英語 quickstart、例、CI、引用情報、公開手順を整える。巨大 MC sweep・クラスタジョブはしない。公開 repo 作成、push、package publish、可視性変更、ライセンス選択は承認範囲外。

## 既存コードから確認した重要点

- `src/css_code.py`: `CSSCode(hx,hz,lx,lz,n)`、`Decoder.decode_syndrome` / `is_faulty`、depolarising 用の両セクター decoder が既存。
- `src/runners.py`: `run_rimc_mixed` は code/decoder/seed 注入と `p_stab` に対応済み。既定値を壊さず互換経路を検討する。
- `src/kernels.py`: bit-flip cluster は **単一状態内で cluster_k 個の 1 と 0 の位置を交換する**。複数 replica 間交換ではない。depolarising は occupied/empty の移動と Pauli relabel を使う。仕様表中の「複数状態」の表現をそのまま別アルゴリズムとして実装しない。
- stabilizer は現行 bit-flip 経路で Hx 行 XOR と iid weight 比を使い、failure 再評価を省略する。一般化時はこの前提を検証する。
- `src/postprocess.py`: burn-in、thinning、ESS、chain 間散らばり等が既存。`metrics.iat` / `diagnostics.split_rhat` に依存。
- `src/splitting_pl.py`: iid weight trace から隣接 BAR を計算し、pymbar を使用。一般 noise では完全な log density に拡張する。
- `compare/exact_ew.py` は仕様にある通り独自 predicate と統一が必要。まだこのファイル自体の詳細レビューは未了。

## 回路 workstream と未決事項

一次資料: https://arxiv.org/html/2509.13678v2 （Rare Event Simulation of Quantum Error-Correcting Circuits）。原著者の公開コードが見つかったことを前提にせず独立実装とする。

第 III 節: 物理的な (gate,fault) を一様選択し、空 location なら追加、同じ fault なら削除、異なる fault なら置換する。各 gate は最大 1 fault。一般 MH の提案比と、論文の受理規則を区別して文書化する。論文の追加受理式の確率範囲、置換受理、非一様 alphabet の扱いは実装時に詳細釣合いで確認する。

第 IV 節の実験は rotated surface code、MWPM、**2d ラウンドの noisy syndrome extraction と前半 d ラウンドのみの補正**による logical idle。通常の Stim logical-memory 実験と同じ再現ではない。この境界・補正範囲を揃えるまで図表の再現成功と呼ばない。

元の依頼は物理 fault baseline → 同条件 direct MC 比較 → Z-OBF/cluster 拡張まで進めるもの。仕様上は回路が次段階であることと区別し、完成範囲を正確に報告する。回路 stabilizer flip は当面対象外。common-F BAR の仮定を満たす基準問題を用いる。

未決: 正式 package 名、ライセンス、公開先、phenomenological の境界・表現・既定値、回路の基準問題と具体的 circuit schedule、BAR 近似モード名と評価方法、互換 wrapper の範囲。

中断直前に提示した実装案（未実装、ユーザー確定ではない）: phenomenological 境界を必須の明示引数にする。公開 Z+H の数値に README の 0.7/0.3、k=2、1 replica を採用し、設定に記録する。

## 次の Codex で再開する順序

ユーザーが再開を指示した場合のみ進める。

1. この文書、ローカル v0.2 仕様、`research-source/AGENTS.md` を読み、既存ファイル・clean status を再確認。取得済み成果物を複製しない。
2. `rimc-library` など独立ディレクトリに小さな package/config/result と受入テストを作る。独立 workspace を維持し、研究用ファイルを変更しない。
3. CSS/noise/spacetime/failure 契約と一般 MH を実装し、既存 OBF/Z/cluster/stabilizer の資産・意味を適切に抽出する。
4. 小規模列挙で確率正規化、Y 相関、時間境界、提案比、詳細釣合い、失敗条件、無効入力、seed 再現性を検証する。空失敗集合や p=0/1 を含む。
5. direct MC/BAR/診断と metadata、薄い外部アダプター、Stim DEM の相関保持を検証。固定 failure と近似 failure を別々に評価。
6. 物理回路 baseline を独立実装し、同じ境界/decoder/noise の exact・direct MC と比較。続いて回路 Z/cluster を検証し、未対応範囲を明示。
7. installed wheel の別環境 smoke、既存 relevant tests の移植・検証、optional dependency なし import、serialization、日英文書・進捗表を完了。実行した検証だけを合格として報告。

自動的な再開、公開、push、ライセンス決定は行わない。
