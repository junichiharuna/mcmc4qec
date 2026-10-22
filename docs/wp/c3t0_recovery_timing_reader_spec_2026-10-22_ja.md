# C3T0復旧結果の計時readerへの接続仕様

現行readerは復旧回収をC1T0に限定し、成功collectorを4時間・旧失敗collectorを2時間としている。
C3T0は成功collectorが8時間のretry8h、旧失敗collectorが4時間のbudget4hであるため、保存先だけの差替えでは受理しない。
既存readerを保存し、case 3・target 0・recoveryの組合せだけを新たに扱う別版を作る。
当該組合せは検証済みC3T0用snapshot validatorのsource hashを要求し、成功collectorのsubmissionを `sampling-collection-submission-retry8h-v1`、旧失敗のsubmissionを `sampling-collection-submission-budget4h-v1` とする。
成功はF・exit 0・run_count 1・8時間、旧失敗はF・exit -29・run_count 1・4時間とし、旧失敗のguardと実PBSを一致させる。
他の既存条件のreader・資源・履歴契約は維持する。
metadataでのcase・target・noise・physical p・192 seed・context・監査config・wrapper照合と、full readerでのraw input・authority・reference・全terminalの照合を維持する。
fixtureで旧版の拒否、新版のC3T0読み取り、別条件・改変・旧2時間または4時間資源へのすり替え拒否を確認する。
fixtureの成功は実C3T0の最終report完成や全12条件の計時完了を意味しない。
実candidate生成・算術確認の待機係と新native環境への接続は、このreaderの受入後に行う。
