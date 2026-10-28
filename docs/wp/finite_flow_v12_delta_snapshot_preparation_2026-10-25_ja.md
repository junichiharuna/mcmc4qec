# v12復旧差分の追加保存候補

以下は最終pin未確定時の準備記録である。
その後、確定pinを反映した別versionでqsub 265676の10 fixtureと実採取に成功した。
最終count・hash・取得先・レビュー後の追加1件は[保存結果](finite_flow_v12_delta_snapshot_acceptance_2026-10-25_ja.md)を参照する。

旧v11 delta snapshot（qsub 265662）を不変の基準とし、namespace・acceptance observer・tail・flowの追加sourceと小metadataを別deltaに保存する候補を準備した。
最終tail/flowのpinと切替証拠が未確定のため、本採取qsub・fixture実行・snapshot生成は行っていない。
これは保存候補の整理であり、本番復旧や科学的完了の証拠ではない。

固定入口はobserver production-readyの原本SHA `e498798f93748a0a9e07b04c520b04daba4b8c1b78f84b4e91e5f59cfdad5d21` である。
回収済みの小さい原本metadataと宣言pinを照合し、ready・observer authority/binding・namespace authorityから明示的な1段の候補参照を抽出した。
参照先を再帰的に開かず、raw/native・巨大result・selection・過去ZIPを読んでいない。
候補inventoryはignored領域 `output/reproduction_snapshot_v12_delta_preparation_v1/inventory-candidate.json` に保存する。
この候補は実snapshot requestではなく、確定していない項目をpendingとして保持する。
private原本pathと識別子を含むため、そのまま共有する資料ではない。

最終採取に必要なpinは次のとおりである。

- 最終flow source v11とfixture/nativeのaccepted・terminal。
- actual config v12・migration・旧停止と新immutable launchの各原本。
- 最終tail binding/dispatch source、導出前後source map、実config/bindingとfixture/native受入。
- observer/namespace受入stageのsource/worker/deployment manifestと、相対source mapごとの明示base。
- 新しい採取stage/request/scriptと、投入時点のfresh shared gateの正規の受理。

本番担当から各final ready/manifestのpathとSHAを受領すればよく、保存のために本番sourceを変更したり再試験・再実行したりする必要はない。
旧v11のaccepted・receipt・archive宣言hashを参照として結び、既存ZIPの内容は再読・再圧縮しない。
新規source prefixと明示entrypointだけを追加し、各file 4 MiBと差分合計16 MiBの既存上限を採用する予定である。
元hashを変更せず、外部のraw/native/resultは宣言と境界だけ残す。

受入済みv9 Scope helperとsnapshot_v2 library、v11 delta_scopeのboundedな収集機能を再利用する。
v11 wrapperにはpurpose・基準世代・過去2map検査・merge終端の固定値があるため、そのままv12へ適用したとは扱わない。
最終pin確定後に別versionの薄いwrapperで対象の明示mapを固定し、旧fixture成功を新wrapperの成功へ拡大せず、新しい受入をPBSで実施する。
既存stage・原source・active controllerは変更せず、採取専用の新submission adapterは作らない。
科学再現・完全閉包・execution_ready・公開可能性はfalseを維持し、final pinと親の投入指示まで待機する。
