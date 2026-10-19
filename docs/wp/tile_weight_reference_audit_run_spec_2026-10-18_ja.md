# 全16条件の重み層別reference監査runner

事前固定したreferenceの全16条件を各1task・16workerで一度ずつ監査する。
部分chunkを別referenceとして扱うcapacity計画は作らず、referenceの標本数・seed・層・条件を変更しない。
初回要求は1ノード・96 CPU・340 GiB・24時間の明示的な上限であり、測定に基づく終了時刻や消費資源の予測ではない。
この全監査のcondition別wall time・CPU time・RSSと全phase wall timeを資源実測として保存し、異なるnやnoiseへの外挿は行わない。

各conditionは既存 `audit_saved_condition` をそのまま呼び、全raw draw再生成・checksum・count・summary再現とfirst16+lastのlabel checkpoint再復号を維持する。
available labelsとchecked labelsを別々に記録し、全label再復号とは扱わない。
監査が完了しても、記録済み失敗chunkのためreference区間が未取得の場合は `reference_available=False` を残す。
破損・欠落・例外はfailed conditionとして全16taskの分母へ残し、summary保存後に非zero終了する。

`prepare(root,reference_root)` は独立した新規output rootへmanifestを固定する。
元reference rootへは書き込まない。
`read_plan(root,reference_root)` は元PBS記録、固定context、summary、native fixture、source/input hashを再確認してplanを返す。
`run(root,reference_root)` はPBS_JOBID・単一thread環境・排他的execution intent・新規条件出力を要求する。
current native profileと監査jobのPBS/hostnameを `native_preflight.json` に保存する。
既存output、部分結果、intentがあれば自動再実行しない。

condition出力は `conditions/{index}.json/.npz/.done.json` とし、成功時には元監査reportを省略せず保存する。
`raw_artifact_bytes` は監査後の原artifactのファイルサイズ合計であり、重複readを含む実デバイスI/O量ではない。
summaryは全16conditionのstatus、独立のreference_available、時間、RSS、marker hashとnative/PBS evidenceを保存する。
全conditionの終了後にsource/input/native bindingが変化した場合もsummaryと全結果を保存し、`terminal_binding_valid=False` と `phase_failure` を記録して非zero終了する。
成功reportについては、元の個別condition summaryと全raw chunkを含む `input_sha256` 全体をphase終端で再ハッシュする。
reportのsource bindingが失敗してもこの再照合を試み、検出した各異常を `phase_failures` に条件番号とともに残す。
再ハッシュI/Oは `phase_wall_seconds` に含む。
qsub submitterと同時最大2ノードの運用は別moduleで扱う。

受入では小さい既存reference fixtureを全16条件のまま使用し、元計画を変更しないこと、失敗保持、fresh guard、source/native/PBS bindingを検証する。
受入の小計算は本番97M trialsの監査や資源実測とは区別する。

2026-10-18のWindows Python 3.11受入は10件が19.30秒で成功した。
全16条件を保った小referenceで成功監査・失敗1件保持・全失敗と終端binding変化の保存を確認した。
Linux受入、実qsub、本番reference全監査・資源測定はこの時点では未実施である。

独立レビュー後、成功16taskの終了直後にaudit依存source・raw chunk・個別condition summaryを変える3受入を追加し、旧実装のsummary欠落と誤った終端成功を再現した。
修正後のWindows受入は13件が39.05秒で成功し、3ケースとも全16outcomeとsummaryを保存して終端binding失敗にすることを確認した。
