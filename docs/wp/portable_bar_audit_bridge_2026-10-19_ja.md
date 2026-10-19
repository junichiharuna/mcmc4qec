# Portable BARのgroup単位のtrace監査結合

最終結合の小仕様に沿い、portable markerの入力集合を元のtrace監査へ渡す明示的なadapterを追加した。
これは最終readerの構成要素であり、全cohortのPBS終端・native環境・anchor・referenceを検証する処理はまだ未統合である。

成功groupでは、mode、production manifest、group、固定したanalyzer/loader変換を照合し、portable markerが持つ入力marker集合を既存`verify_group`へ渡す。
元のartifactやmarkerを書き換えず、PCでの後処理をクラスタのPBS解析として記録しない。
このadapterの呼出し前には、archive全memberとrecord/markerのhashを検証する必要がある。
元の`verify_group`による全task集合・raw payload・記録済みsampling failure・checkpoint数の照合を保持する。

解析のinfrastructure failureで結果が存在しないgroupでは、元のtraceと監査だけを照合する。
その場合は`analysis_trace_markers_matched=False`、`trace_inputs_from_audit_only=True`とし、存在しない解析入力の照合を主張しない。
全88設定の予定行を残し、推定値・区間・所要時間は未取得として`None`にする。
診断は`diagnostics_available=False`、`undefined=True`、`flagged=True`とする。
この場合の`high_rhat=False`と`low_ess=False`は未評価のscreenであり、混合が良好という意味ではない。
失敗理由`postprocessing_infrastructure_failed`と元errorを保持する。

実装前の受入テスト失敗を保存し、実装後は11テストが20.81秒で通った。
保存済みartifactを作る既存の小fixtureで、groupのpayload照合、payload改変の拒否、mode・manifest・変換・入力marker・failure集合の不一致、PBS identityの注入を検証した。
結果がない場合のtrace監査を、解析入力の照合と区別して返すことも確認した。
有限の2 replicate例では、未取得行を既存のsummaryに渡しても全予定行が分母に残り、point meanを取得済みとして返さないことを確認した。
これらは小fixtureの受入であり、全768 groupの実データによる最終監査ではない。

source・受入logは`data_portable_bar_2026-10-19/audit_bridge_sources_v1/`に保存した。
全cohortのreader、実PBS実行を伴う最終監査、独立referenceとの照合は引き続き未完了である。
公開候補`47ef1b6`と実行中のsampling・portable driverは変更していない。
