# WP-G 独立レビュー

## 判定と指摘

WP-G の担当範囲は受入と判定する。
指摘した3件は修正され、残る数値の食い違いは原因未特定の警告とともに表示される。
第1回レビューでは、収束例の無作為論理セクターが別の初期状態と衝突する問題を発見した。
`convergence_check.py --quick --seed 0` では最小重み群と無作為論理セクター群がともに重み3、observable sector `[0, 1]` であり、意図的に異なる初期値を比較する `multistart` の条件を満たさない。
同じ構成で seed 4 は無作為群と最大重み群が一致する。
第2の指摘は、`pl_curve.py --quick --seed 2026` の d=5、p=0.26 と p=0.22 で BAR と独立 direct MC の95%区間が交差しないのに、その不一致を行ごとに警告しない点である。
p=0.26 は BAR `[0.4541, 0.5547]` と direct MC `[0.6527, 0.7825]`、p=0.22 は BAR `[0.3621, 0.4692]` と direct MC `[0.6179, 0.7520]` だった。
原因は未特定で、混合不足と有限標本などを検討する必要があり、この例の quick 数値を研究結果と見なせない。
両指摘は WP-G 担当に連絡し、対応を依頼した。
修正コミット `e089c51` は、無作為初期状態が既存の2状態と一致すると再抽選し、3状態の相違を検査する。
同コミットは BAR と direct MC の区間交差を CSV、標準出力、SUMMARY に記録し、非交差と quick 設定の精度制限を警告する。
修正後の専用テストは 18 passed、29.47 秒であり、衝突が起きた seed 0、1、2、3、4、5、7、8、9 の回帰テストを含む。
追加で、anchor 行の direct MC は BAR anchor と同一の試行を再掲しており、独立の確認点ではないため、そのラベルと完了メモの訂正を依頼した。
修正コミット `4e128cd` は anchor 行を `mc_role=anchor_reuse`、残りの行を `mc_role=independent_direct_mc` と CSV と SUMMARY に記録し、docstring、標準出力、完了メモも訂正した。
最終コミット `67f4d06` は quick の chain 長を 4 chain × 40 samples / 12 burn-in、既定を 4 chain × 600 samples / 180 burn-in とし、BAR 区間が無い場合は図の誤差棒を省いて CSV と SUMMARY に null と未判定警告を残す。
担当の最終実測では曲線例は quick 3.61 秒、既定 19.37 秒であり、全4例が quick 10 秒以内、既定 120 秒以内だった。
最終設定の seed 2026 では既定の d=3、p=0.22 にも BAR と direct MC の区間非交差があり、警告が表示される。
この例が論文用精度に達したという判断はしていない。

## 科学的な確認

`pl_curve.py` は同じ `Problem` と重みなし MWPM decoder を全 rung に渡し、最大 p の direct MC anchor の失敗数を表示する。
BAR から独立した direct MC 確認点は anchor を除く2 rung であり、anchor 行の区間交差は独立照合ではない。
`--demo-overlap` は 1 bit の共通 failure 集合を持つ問題で p=0 と p=1 の排他的 support を `estimate_logical_error` に渡し、`OverlapError` を実際に捕捉する。
内点の toric bit-flip 分布は full support なので、粗い刻みだけで厳密な zero support になるとは説明していない。
`p_dependent_decoder.py` は固定 prior の BP-OSD を標準 ladder で再利用し、別の明示的な近似モードでは decoder を p ごとに再構築する。
近似モードの区間に failure 集合の変化による bias が入らないことは出力と docstring に明記されている。
`conditional_weight.py` は `E[w|faulty]` と絶対 `P_L` を区別し、chain の状態頻度から `P_L` を推定していない。
`convergence_check.py` は独立な無条件 noise 試行の失敗例だけから重みの標本分散を計算し、平均推定値の分散ではなく条件付き観測量の分散を `evaluate_convergence` に渡す。
ESS、split R-hat、4 条件と各条件の検出範囲を表示し、診断が収束・エルゴード性・正しさの証明にならないと明記する。
全スクリプトの乱数は `--seed` から派生し、最終行は指定キー集合の厳格 JSON `SUMMARY` である。
図は Agg backend で利用可能な BAR 区間と direct MC 区間を示し、CSV に同じ数値を保存する。

## 実施した検証と範囲

`C:/dev/mcmc4qec/.venv-dev3-optional/Scripts/python.exe -m pytest tests/test_examples_workflows.py -q` は第1回版で 9 passed、17.25 秒だった。
同じ Python で quick の4例を実行し、`pl_curve.py` は4.99秒、`conditional_weight.py` は1.83秒、`convergence_check.py` は約1.1秒、`p_dependent_decoder.py` は0.85秒で終了コード0だった。
`pl_curve.py --demo-overlap` は期待どおり `OverlapError` を表示した。
描画不能時のテストは `matplotlib.pyplot` の import を拒否して CSV を確認するものであり、PyMatching が `matplotlib.cbook` を import するため matplotlib パッケージ全体を外した環境は未検証である。
既定設定、全 suite、installed wheel、別 OS はこの独立レビューでは未実施である。
WP-G 完了メモ記載の既定時間は担当者の測定値であり、このレビューでは再測定していない。
`4e128cd` の後、別作業と並行した私の `pytest -k workflow_quick` では曲線例の subprocess が30秒で timeout し、1 failed / 3 passed だった。
同じ時期に担当も quick 31.83 秒と報告したため、timeout を延長して合格とはしなかった。
その後に担当が単独で最終設定を測り、専用の既存18件は 18 passed / 38.91 秒、BAR 区間欠落の追加テストは 1 passed / 0.52 秒と報告した。
最終コミット後の専用ファイル全19件をこのレビュー担当は再実行しておらず、全 suite、installed wheel、別 OS も未実施である。
