# C1T0最終設定からqsub・回収への引継ぎ

既存の最終設定作成driverが正常終了した後、保存されたconfig hashとpreflightを固定して既存復旧qsub wrapperを使う。
設定作成driverが未完了なら待機し、失敗記録があれば停止する。
稼働中の先行driver・公開候補・配置済みwrapper・reader・collectorは変更しない。

投入前に保存preflightとの完全一致を確認し、実PBSで所有者の全要求ノードを数える。
Qを含む未終端ジョブの要求が2ノードに達している場合は待機する。
実投入は既存wrapperの共有lock、直前の入力照合、最大2要求ノードの検査を通し、qsubで一度だけ行う。
リモート側の事前確認で空きなしと判明し、qsub未実施を明示する厳密な応答を受けた場合だけ、空き待ちへ戻る。
timeout・不正応答・例外・不明なjob ID・wrapper内部での停止は記録して停止し、自動でqsubを再実行しない。

投入後は同じjob IDをqstatで追い、観測timeoutは同じIDの再観測に限る。
正常終端はF・Exit_status 0・run_count 1に加え、所有者・script・1 CPU・32 GB・12時間の要求一致を確認する。
その後、既存wrapperのcompleteを一度だけ呼び、復旧authority・report hash・実PBS終端を検査してterminalを保存する。
既存collectorで13成果物を回収し、転送前後のsnapshot一致とlocal hash一致を確認する。
最終reportの受理まで終わって初めて、この引継ぎを完了とする。
reportの受理を混合・母RMSE・名目95%被覆の保証として扱わない。

受入は正常経路、準備前の待機、先行失敗、空きなしの明示応答、曖昧応答と例外の再投入禁止、設定/preflight差異の拒否を確認する。
既存wrapper・collectorの試験を置き換えず、追加引継ぎの責務を検査する。
本番configは未作成のため、本番投入・実reader・回収の検証は実際の完了後に記録する。

## 実装・受入と起動

`output/c1t0_final_execution_handoff_v1/driver.py` を実装し、Windowsで24 passed・0.61秒、クラスタLinuxで24 passed・0.04秒だった。
正常経路、設定/preflightと投入receiptの一致、空きなしの厳密な否定応答、曖昧応答・timeout時の再投入禁止を検査した。
実際に送るリモートprogramをfixture wrapperで実行し、空きなしではsubmitを呼ばず、preflight・submit・completeが対応する既存操作へ進むことを確認した。
実配置済みの復旧wrapperをhash照合し、元venvからbackend importとCLIのhelpが成功した。
本番configを使ったsubmit・completeや数値readerの実行を検査した結果ではない。

[受入manifest](data_tile_validation_2026-10-17/c1t0_final_execution_handoff_acceptance_v1/manifest.json)はsource・試験・実入力照合を保持し、SHA-256は `36d6ec3c71e17f70bf9cf198aae9c606b8d343a73f029e253e1e3ab6e14897f7` である。
既存の設定作成driverのsource・intent、復旧collector、共有PBS helperなど15入力を固定した。
23:43 JSTにlocal PID21844で起動し、23:44 JSTのpollで継続中を確認した。
[開始intent](data_tile_validation_2026-10-17/c1t0_final_execution_handoff_v1/intent.json)と同directoryのobservationsに状態を保存する。
稼働sourceのSHA-256は `3c6b416afa16b0b6a238e3caa9094f647cec1c0b5d45aed7c5de425ed02e1aa1` であり、稼働中に変更しない。

現時点では先行の最終設定作成を待っており、新しいqsub・本番最終report・回収は未実施である。
両PCの処理、復旧full監査、設定作成が成功した後にこの引継ぎが進む。
最終report回収先は `docs/wp/data_tile_validation_2026-10-17/recovery_c1t0_final_collected_v1/` とし、既存directoryがあれば上書きしない。
