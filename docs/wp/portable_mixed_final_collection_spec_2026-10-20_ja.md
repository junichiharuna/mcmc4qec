# portable最終reportの回収

対象は固定済みportable_bar_mixed_qsub_v1.pyが正常終端を受理した最終reportだけとする。
remote root、config SHA-256、terminal.json SHA-256は、実際のprepare・completeから取得した値を外部指定する。
回収helper自身はqsub・complete・最終readerを再実行しない。

remoteでは固定wrapperのhashを検査してread_plan・ledgerを読み、config、source、入力metadata、実qstatのF・Exit_status 0・run_count 1・script・resourceを再確認する。
terminal、completion、execution、reportのjob ID・config・report hashを照合し、C0T2の192 seed・352設定・67,584行と既存readerのscopeを確認する。
failure.jsonまたはsubmission-error.jsonが存在する場合は受理しない。
対象13ファイルはconfig.json、report.sh、submission-intent.json、submission.json、qsub-response.json、execution.json、completion.json、terminal.json、reader.stdout、reader.stderr、report.out、report.err、final-report.jsonとする。
metadataはsnapshot内でbytesとhashを保存し、大きいreportだけをSCPで回収する。
前後snapshotのfile census・hash・size・PBSの安定した項目が一致し、localの全13ファイルのhash・sizeも一致した場合だけaccepted=trueとする。
既存の回収先を上書きせず、転送失敗・hash差・観測失敗時はintentと部分結果を保持して自動再実行しない。

受入テストでは正常fixture、実行中・失敗・再実行job、script/resource差、異なるterminal/report/config、欠けたfile、転送破損、前後変化、既存出力を検査する。
mockのqstat・SCPの成功を、本番最終reportの正常回収とは扱わない。
保存traceやreferenceの再監査を回収helperが行ったとは記録せず、元の最終readerのscopeを保つ。
