# C3T2回収・監査の依存先再接続

旧C3T2監視はregistry取得待ちのまま先行auditの停止を検出し、回収・監査の操作前に終了した。
旧保存先がintent・error・registry観測だけで、停止理由が先行audit失敗の場合だけ別保存先へ再接続する。
元の固定collector・capacity audit・full auditのconfig、実行手順、PBS終端検証、共有lockと最大2要求nodeを維持する。
新しいC3T2 generatorとC3T1 auditのintent・sourceを固定し、旧記録は保持する。
generator registryが完成するまでは待機し、全samplingの正常終了後だけ回収処理へ進む。
本変更で既存のnative referenceやPC計算を再起動しない。

受入では未知の停止理由、旧保存先の追加操作記録、完了記録、欠損を拒否する。
実入力の照合と新監視processの稼働確認を別に記録し、小規模受入を科学的検証の完了とは扱わない。

## 21:58 JSTの稼働確認

guardの7 testは0.73秒、保存sourceからの再実行は7 passed・1.76秒で成功した。
新しい先行intentと固定collector・audit configの実照合も成功した。
[受入記録](data_tile_validation_2026-10-17/c3t2_audit_slot_resume_acceptance_v1/accepted.json)のSHA256は `12b06c066a95f136f77d2a79601bc7300af0e429c3120c3631e46c167daaaede` である。
旧監視の実processが存在しないことを確認し、新driver PID45828をhiddenで起動した。
実processとcommandを確認し、registry_ready=falseの観測が保存された。
新driverはgenerator registryの完成を待機しており、この時点では回収・監査jobの新規qsubは未実施である。
