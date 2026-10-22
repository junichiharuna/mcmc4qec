# 残り5条件の最終集計設定の準備

## 小仕様

受入済みC1T0設定作成処理を基に、C1T1・C1T2・C3T0・C3T1・C3T2の独立した設定を準備する。
対象条件・監査config・source・sampling rootは既存の受入記録とassignmentから固定し、実行時の推測で選ばない。
旧処理からの差分は、planned readerと初回collector authorityへの接続、条件別path、native reference terminalの外部pinに限定する。
元処理のpath検査・hash検査・実PBS終端照合・入力metadata収集・保存先排他を維持する。
全件転送receiptと192 seedのfull監査完了がそろうまで、本番設定を作らない。
全38 batchと同条件のproduction manifestを要求し、別条件の転送・監査・referenceは拒否する。
保存parityの外部pinを持つnative terminalは、転送後の同一ファイルと照合する。
prepareと非投入preflightのみを行い、この処理からqsub executeや数値workerは呼ばない。
資源要求は既存の実終了証拠に基づく1 CPU・32 GB・12時間上限を保持し、実行時間予測として扱わない。
元C1T0の稼働中sourceと入力を変更しない。

## 受入条件

全5条件のpath・監査config hash・production manifestを既存記録と照合する。
変換対象のsource式は一致数を確認し、想定外の変更を拒否する。
異なる条件の転送、未完了full監査、native terminalの不正hash、受入済みcontrolの変更を拒否する。
資源上限とmetadata path検査について元の回帰を維持する。
Linuxの元venvで実配置sourceと5条件のbootstrapを検証する。
可能なfixtureではprepareから非投入preflightまでを確認し、実PBS・科学入力が未検証の範囲を記録する。
本番full監査と転送が未完了の条件は、テスト成功を最終設定作成や科学的完了として扱わない。

## 実施結果

元C1T0 preparerをbyte単位で保存し、12箇所の明示的な差分と条件ごとの独立namespaceでplanned readerへ接続した。
元source・native control受入記録・5条件のbindingをSHA-256で固定した。
元のreadiness・資源判断・metadata path検査の関数はAST比較で無変更を確認した。
Windows43件・1.12秒、クラスタの元venvでLinux43件・0.30秒のテストが成功した。
5条件のprepareから非投入preflightまでと、実PBS応答・full監査終端・context条件・native terminal hashの不一致拒否をfixtureで確認した。
fixtureではPBSと科学入力を置き換えており、本番入力や本番集計の成功を示さない。
元venvの実配置で、全5条件の監査configと元bundle・planned controlのbootstrapを確認した。
この確認では本番設定作成・qsub・raw trace監査・最終report実行を行っていない。
元の1 thread環境をPython起動前に明示した。
配置先は `/home/user/workspace/mcmc4qec/20261021-planned-final-preparation-v1` である。
preparer SHA-256は `4c9740b189aeac20ef431c015661e7cfbb31e2cd305e827574f986d4e1267b88` である。
source・red/greenログ・実配置照合は [受入記録](data_tile_validation_2026-10-17/planned_final_preparation_acceptance_v1/accepted.json) と同directoryのmanifestに保存した。
受入記録SHA-256は `99d30c6b6958786fc4ac2ae500946b9db84460169d4a3901be5104c9ae6713ac` である。
全件転送とfull監査を待つ親driver、および最終集計qsubと回収への自動接続は未実装である。
