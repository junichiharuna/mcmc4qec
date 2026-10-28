# Report familyの有限PBS action

共通仕様は `finite_tail_actions_spec_2026-10-25_ja.md` とする。
既存のv8、元driver、report_job helper、環境、科学sourceは変更しない。
新しいpluginのAPIは `execute(action, ctx, task=None, post_source='', *, sources, hooks=None)` とする。
`sources` は元report driverとhelperの明示pinを持つ `driver`、`helper` の2項目だけとする。
元driverのSHA-256は `1d3b5a7ab35e5deafdc6a2f3d9ee9908027695883a9d036e6ad6c1c5d2f6fcbd` とする。
元helperのSHA-256は `8fc3f81a53e9d18771c0c484a6173823d0075dd7a9548d4d7c18b03b57e9ddc2` とする。
pinで固定したhelperの実bytesを元のfilenameとmodule名で読み込み、実行後にも元sourceの不変を確認する。

prepare、gate、observe、sealの呼出順、元検査、引数、返却valueは元driver.call内programと同じとする。
prepareは元 `j.prepare` を呼ぶ。
他actionは元 `j.read` によるcontrol読込、preparationとのenvironment一致、元bootstrapを先に行う。
gateは元のrequested node count、live controller、lock存在の観測を返す。
observeは元bindingとqstatを行い、元と同じjob ID・state・exit・run count・resourcesを返す。
sealは元 `j.seal` により大きいplan/resultの再検証をPBS内で行う。
例外は共通action workerへ伝播し、成功に変換しない。

submitだけはhooksを必須とし、元 `j.submit` の既存引数へ `gate` と `runner` を渡す。
gateは元gate_liveと同じ順序でlive_controllersを検査し、その後own_active_jobsのうち共通hooksが証明付きで親自身を除外したviewをrequested_nodesへ渡す。
このviewは親退場後の投入可能性を判断するためのものであり、実際の投入許可や現在の観測の書換えではない。
runnerは共通hooksのrunnerをそのまま渡し、本物のqsub直前にDeferredを返す。
plugin自身はDeferredを捕捉して成功ledgerを生成しない。
元submit内のdeep検証、lock、intent、uncertain flag、例外時のlock保持を変更しない。
hooksなしsubmitと非submitへのhooks注入は拒否する。

受入では元driver.callの固定programを抽出してfixture上で実行し、全5actionの戻り値と元helper呼出順をpluginと比較する。
元programのsubmit比較時も実qsubは行わず、fixtureのsubmit関数を使用する。
追加fixtureでは元report_job.submit本体を使用し、Deferredが発生するまでのdeep call順、3回のgate、元lockとintentの保持、submission ledger未生成を確認する。
live controller、source改変、ctx/helper不一致、environment不一致、未定義action、不適切hooksを拒否する。
受入テストはqsubでのみ実行し、このPCでは実行しない。

report preparation全体は上流の固定完了markerを確認してから、元v3adapter.runのreport-preparation roleを共通の有限PBS actionとして呼ぶ。
大きいtiming state、selection、科学bundle、planの読込と検証はそのPBS内に置く。
final-reportの元adapter.final_reportと成果物hash・回収確認も共通の有限PBS actionに置く。
外側controllerへ返すのは固定された小さいreceiptとartifact pinのみとし、巨大proofのJSONをstdoutへ戻さない。
report内部のpartition_check IPCとtimeout変更は独立した小仕様とsource overlayで扱う。
初期4時間は未実測の運用予算であり、性能や完走の保証ではない。
