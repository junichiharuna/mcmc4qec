# 標準の統計誤差とオプション診断

基準commitは `7f8d7ba` で、版番号とsamplingの公開既定は維持する。
利用者の追加指定に従い、統計誤差を標準で返し、追加の診断解析だけをオプションにした。
計算部分と独立レビューを別々のAstra担当に分担し、統合担当がAPI・保存形式・既定MCSE・文書を実装した。

## 返却する値

`sample_faulty` は `conditional_weight` と `conditional_weight_standard_error` を常に返す。
誤差は既存のchain別IATを再利用した、独立chainの重み平均に対するMCSEであり、絶対論理誤り確率の標準誤差ではない。
`diagnose` にも `mean`、`chain_standard_errors`、`mean_standard_error`、`standard_error_method` を追加した。
direct MCのWilson区間とBARの既定誤差区間・log標準誤差は従来どおり返す。
短い系列・定数系列・非正IAT推定などで計算できないMCSEは `None` とする。
新しいResult fieldは末尾に追加し、古いJSONでfieldが存在しない場合も読み込める。

`sample_faulty(..., diagnostics=True)` または `diagnostics=DiagnosticsConfig(...)` は `result.diagnostics["trace_analysis"]` を追加する。
`estimate_logical_error` も同じkeywordを受け付け、rungごとの `result.diagnostics[i]["trace_analysis"]` に返す。
追加解析にはclassical split Gelman–Rubin R-hat、chain別IAT/ESS、推定ACF配列、非重複ブロック平均のSE、円環block bootstrapのSEとpercentile区間がある。
ブロック長別に使用標本数・末尾除外数・切詰め平均との差を記録し、ブロック長の影響を数値で比較できる。
R-hatはrank-normalized/folded版ではなく、ESSの和は一般にpooled mean用ESSとは一致しない。
追加解析の既定は無効で、bootstrapだけを省く場合は `DiagnosticsConfig(bootstrap_replicates=0)` を使う。
解析のseed既定は0とし、samplingとBARの乱数を消費しない。
詳細な観測量誤差とBARの論理誤り確率誤差は別々の計算と保存先を持つ。

後処理の `diagnostic_report` は既存Result群と名前付きの独自スカラー観測量を扱い、`analyze_traces` は数値系列を直接受け付ける。
自動作図やplot依存は追加せず、JSONへ保存できる数値を返す。
サンプル列・acceptance・BAR点推定・既存区間・共分散は追加診断の有効化前後で一致することを受入テストで確認した。

## 検証と限界

数値公式、定常AR(1)の既知値、円環bootstrapの列挙分散、定数・短い系列、seed再現性、JSON往復、custom observableの入力をテストした。
独立レビューが発見した小数定数系列の偽ACFと、複素観測量の虚部黙殺を修正し、再検証した。
検証ログと最終集計は `data_diagnostics_2026-10-15/` に保存する。
source全suiteは469 passed、176.87秒、skipなしで、既存のWindows notebook由来zmq warningが1件あった。
strict mypyと公開consumer型テストは全suiteに含めて成功した。
installed core wheelでは関連103テストが10.62秒で成功し、verify_wheelの28 Python sourceとの一致・core例・文書例も成功した。
今回optional wheel全suiteの再実行は未実施で、optional経路はsource全suiteで確認した。
commit依頼後のREADME更新指定により、英日両READMEに統計誤差とMCMC診断の専用節・同一の実行例・設定と解釈を追加した。
README更新後もpackage source fingerprintは同じであり、文書整合3テストが0.29秒で成功し、wheelを再buildしてcore verify_wheelを再実行した。
有限長の診断・区間は定常性、独立chain、十分な混合を仮定し、共通の混合biasや名目95%被覆を保証しない。
新しい実符号被覆sweepや速度benchmarkは今回実施していない。
commit・push・remote CI・公開は今回実施していない。

APIの設定と各fieldは [API文書](../api_en.md#default-statistical-errors-and-optional-detailed-diagnostics)、実行可能な例は [tutorial](../tutorial_en.md#initialization-cache-and-diagnostics) にある。
小仕様は `diagnostic_options_spec_2026-10-15_ja.md` と `trace_stats_spec_2026-10-15_ja.md`、独立レビューは `diagnostic_review_2026-10-15_ja.md` に分けて記録した。
