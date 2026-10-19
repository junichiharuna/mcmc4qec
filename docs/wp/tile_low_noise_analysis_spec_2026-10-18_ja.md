# 低ノイズ固定prior BAR解析の小仕様

対象は `tile_low_noise_study.py` の本計画で、各case・targetについて192個の独立replicateと事前固定した全設定を残す。
groupは `(case,target_index,kernel,initialization,replicate)`、traceとanchorは7成分task座標を用いる。
目標priorで構築した同一Problemのmetadata hashと、各rungの物理p・実際のRNG・設定を照合する。
1chainしか保存しないsampling capacityを複数chainのBAR入力として利用しない。
解析capacity用stage155は予約のままとし、本解析はstage153と明示的target座標を用いる。

samplingとanchorの完了summaryは全予定taskを含み、成功・失敗件数とnative preflight・PBS execution intentを結び付ける。
記録済み失敗taskは、対応する全設定で区間未取得の行を残す。
artifact未取得、hash不一致、異なるdecoder・seed・設定は入力破損として停止し、記録済みsampling failureと混同しない。
全入力artifactを読み直して検証した後にのみ解析cacheを利用し、cache identityは入力marker群のhashを含む。

事前指定したchain数、burn-in、保存長、coarse/fine ladder、block bootstrapとcross-chain法を比較する。
点推定と共有rung共分散は既存のBAR関数を再利用し、独立anchorの二項分散を加える。
weight、syndrome weight、各logical bit、Bennett overlapのIAT・ESS・split R-hat・数値ACFとlogical sector移動を保存する。
未収束screen・未定義診断・数値的に取得できない区間を除外しない。
有限traceの診断は収束・既約性・精度・被覆の保証ではない。

この解析ではreference point・bias・coverageを設定しない。
weight stratified samplingの部分和を真の失敗率の点referenceとして使わず、後段の `tile_weight_reference_comparison.py` が独立reference区間に対する範囲を計算する。
解析行には `reference=None` と `reference_available=False` を残す。

`analysis_context` はsampling manifest、解析関連source、runtime、完了phase evidenceを固定する。
CLIのplan/runは本番の固定manifestを再構築して照合し、runはqsub・1〜96worker・固定thread環境・独立native preflightを要求する。
worker数は計算資源計画に従い、実行intentとsummaryに保存する。
既存の解析intentやartifactがあれば自動再実行しない。
submitterと資源推定は別実装であり、このdriverはqsubを直接呼ばない。
`analyze_arrays` は入力済み配列を処理する数値coreであり、provenance検査済みであることを単独では保証しない。
資源測定の合成配列はこのcoreを利用できるが、結果を合成資源fixtureと明示し、科学計測のcohortへ混入させない。

受入は全4caseの短い実trace・anchorによる計算、失敗task全行保持、欠落・改変入力拒否、seed target分離、capacity拒否、phase evidence不整合拒否、PBS実行guardを含む。
短い受入データは本番cohort、混合、精度、被覆の検証とは扱わない。

2026-10-18のWindows Python 3.11受入は `tests/test_tile_low_noise_analysis.py` の27件が24.80秒で成功した。
Linux受入、実PBS解析、完全traceの独立再復号、低ノイズのbias・被覆校正はこの時点では未実施である。
