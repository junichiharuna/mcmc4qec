# dev3 実行例整備の統合記録

## Phase 0

開始時 main と origin/main は `8cbc0b1c4eef64519cc6320b3ddd5565876d168e` で一致し、作業ツリーは clean だった。
更新済み AGENTS.md と依頼書 `docs/dev_request_2026-09-30_examples.md` が同commitに含まれることを確認した。
着手前の指定文書、既存6例、CI、wheel検証helperを読んだ。
指定 Python 3.11 による全 suite は 268 passed / 4 skipped、46.08秒で、ファイル別合計最大は11.00秒だった。
研究リポジトリは `69efcfcc86af3bf24ca977a098dab0f348601aff`、status cleanであり、読み取り専用とする。

## 統合方針

作業枝は wp/f〜wp/j、統合順は H → F → G → I → J とする。
verify_wheel.pyはexamples以下を再帰的に列挙し、マニフェストの依存分類を使い、各例を `--quick --seed ... --out <一時ディレクトリ>` で実行する。
READMEのPythonブロックは英語版だけを実行し、日本語版はコードの完全一致試験で保証する。
notebookはinstalled wheelを使うカーネルでquick実行し、既定出力の再生成とは分けて記録する。

## マニフェストの依存修正の判断

make_toric_codeは既存実装でldpcとbposdをimportし、matching extraだけでは動かない。
ライブラリ本体やmatching extraの意味を変えず、toricを使うFの2例、Gの3例、Iの最初の3notebookの必要extrasにcodesを追加する。
ファイル名とSUMMARYキーは変更しない。
この不足は依頼書のマニフェストとdev2公開契約の不整合であり、メイン判断として依頼書の該当extrasとWP-Jの一覧に同じ修正を適用する。

## 既存6例のSUMMARYキー

依頼書に指定のない既存6例については、Fの提案をメインが承認し次の集合を使う。

| script | keys |
| --- | --- |
| bit_flip.py | exact, pl, pl_interval, ew_exact, ew_chain |
| three_noise.py | cases |
| bar_ladder.py | ladder, bar, intervals, exact |
| toric_pymatching.py | code, p, pl, pl_interval, ew_direct, ew_chain |
| stim_dem.py | mechanisms, exact, pl, pl_interval |
| circuit_baseline.py | locations, detectors, pl, pl_interval |

## version更新の確認対象

pyprojectの配布版番号はPhase 2で0.1.0.dev3へ更新する。
実行時 `mcmc4qec.__version__` は現在 src/mcmc4qec/results.py の `VERSION = "0.1.0.dev2"` に固定されている。
実行時番号も揃える最小差分はこの1行を `VERSION = "0.1.0.dev3"` にすることであり、アルゴリズムや公開APIは変わらない。
当初はsrc変更禁止との整合を確認したが、依頼書全体の再実行指示を受けて第1節のメイン向け最小修正の例外と第7.2節のdev3指定を再確認し、この1行を同範囲として更新する。
配布設定と実行時versionの一致テストを先に追加し、dev2対dev3で失敗することを確認してから修正した。

## 回路例のquick時間上限への対応

Fが既存circuit_baseline.pyのquick実行12.43秒、構築単体10.88秒を報告した。
profileでは単一faultを2588回注入するたびに理想回路を1命令ずつ組み立て、Stimのappend約40万回が主な費用になっていた。
依頼書第1節のメイン向け最小修正として、ノイズ命令間の理想区間だけを保持し、注入時に区間を一括連結する変更を行った。
公開API、fault配置順、物理noiseの分布、decoder、failureの意味は変更していない。
重複target・2qubit fault・選択locationについて、全80配置の注入回路を独立に組み立てた期待値と比較する受入テストを先に追加した。
修正前のsurface d=3構築9.61秒で保存したH/L全2588列と修正後の列は完全一致し、修正後の構築は0.92秒だった。
回路の4テストファイルは22 passed、9.83秒だった。

## 統合時の検証と裁定

Hを独立レビュー受入後にmergeし、全suiteは284 passed / 4 skipped、69.79秒だった。
続いてFをmergeし、全suiteは295 passed / 4 skipped、98.44秒だった。
両実行時には他WPのfocused検証・notebook再生成が並行していたため、最終的な時間予算は統合完了後にも確認する。
SteaneのBAR区間のexact被覆はCLI既定seedで既定2/3、quick1/3であり、全rungの比較結果を出力とメモに残すことを受入とする。
有限標本の区間被覆を全seedで保証するためのseed選別や区間の恣意的な拡大は行わない。
PyMatching 2.4はmatplotlib.cbookを読み込むため、toric workflowについてmatplotlib本体を欠く実行環境は成立しない。
描画用pyplotのImportError時に同じ数値のCSVを残す経路を検証し、matplotlib本体なしの実行成功とは区別してREADMEと最終報告に記録する。
この依存境界を隠すstubや依存packageの書き換えは行わない。

## BAR例の時間予算とスリープ中断

G/Iの曲線例は同じ4 chainを維持し、quickを40 samples / 12 burn-in、既定を600 samples / 180 burn-inへ揃えた。
anchor試行数200/1500、独立確認点180/1200、bootstrap回数10/30は維持した。
縮小前の単独profileは61.13秒で、条件付き標本生成39.13秒とBAR用密度差評価12.88秒が主な費用だった。
profileには計測自体の費用が含まれるため、通常実行時間の代わりには用いない。
Gの縮小後の単独実行はquick3.61秒、既定19.37秒だった。
短いchainの結果が研究精度を保証するとは扱わず、BARと独立MCの区間が非交差なら警告し、anchor点のMC再利用は独立確認点と区別する。
Iの長時間timeoutは、Windows Systemログで確認した16:02〜16:52および17:08〜17:36 JSTのスリープと一致した。
これらの中断試行を合格や通常実測時間として扱わず、復帰後の成功した検証結果を別途記録する。
通常実行にも時間変動は観測したが、すべての変動原因まで特定したわけではない。

## 最終統合後の時間予算調整

G統合後は314 passed / 4 skipped（138.40秒）、I統合後は318 passed / 4 skipped（151.79秒）だった。
J統合後は321 passed / 4 skipped（265.15秒）だったが、workflowファイル60.987秒、追加5ファイル合計113.506秒で時間予算を超過したため、この実行を最終受入には用いない。
初期状態の衝突修正は9 seedで検証済みであり、継続する回帰試験は最小・最大セクターとの衝突を代表するseed 0と4の2件に整理した。
conditional_weightのquickだけを4 chain、40 samples、12 burn-inに縮小し、実行確認用で精度を保証しないことを出力に追加した。
同例の既定600 samples、180 burn-in、direct MCの試行数、計算経路とSUMMARY契約は維持した。
最終件数が321から314へ減るのはこの重複seed 7件の整理によるものであり、他の検証項目は残した。
調整後のsource全suiteは314 passed / 4 skipped、231.28秒で、追加5ファイルの同一実行内合計は84.876秒、ファイル別最大はworkflowの32.055秒だった。
Phase 0からの壁時計差には既存テストの実行時間変動も含むため、それを追加テストだけの費用とは扱わない。
