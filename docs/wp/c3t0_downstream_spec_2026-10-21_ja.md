# C3T0生成後のnative・PC・収集・監査への接続

## 小仕様

C3T0の3 generator registryが完成した後、受入済みnative reference driverを起動する。
各PCは、直前条件C1T2のserial開始記録とC3T0 native開始記録がそろってから既存handoffへ渡し、実計算の開始条件は既存driverに委ねる。
親は子の実process handleを保持し、正常終了と完了記録の両方を要求する。
収集・監査は固定されたC3T0 collectorとaudit configを使い、実sampling正常終端とC1T2 full監査の受理を確認してから進める。
既存の共有lock・qsub・最大2要求ノード・一度限りの操作を維持する。
元C1T2 launcherとaudit driverを変更せず、条件と直前処理の対応だけを別sourceへ導出する。
数値worker、native判定、失敗の分母、source・入力の照合を変更しない。

## 受入条件

元sourceとテストからの導出差分を保存し、条件依存のpath・config・case・target_indexを照合する。
生成registry未完成では子を起動しない。
失敗した子や先行処理を自動再起動せず、実process handleと完了証拠を区別する。
各PCの前提がそろう順序、先行停止、別条件や異なる監査configの拒否を再検証する。
本番driverを起動しても、前提未完了の間は新しいqsubや数値workerを起動しない。

## 実施結果

元driverと受入テストからの導出差分を保存し、変更箇所の一致数と生成byteの一致を確認した。
Windowsで元受入36件と導出・priority確認5件、計41件・0.94秒が成功した。
実process handleを使った小さいchildの終了確認、二重起動拒否、registry・source改変の拒否を含む。
C3T0の実collector config・audit configと、C1T2 full監査を待つpriorityを照合した。
新しい親driverのLinux単独テストと、本番child・collector・監査の実行は未実施である。
source・red/greenログ・導出記録は [受入manifest](data_tile_validation_2026-10-17/c3t0_downstream_acceptance_v1/manifest.json) に保存した。
manifest SHA-256は `5504a679fcd11c7a5d94c90a9c8e8a6366d614d2dc2701b604453f71a66af9ae` である。
launcher SHA-256は `56b3b89f5639555932a1406db66784bda0546deee2e3666539f87b8f06741e80`、audit driver SHA-256は `666718212c838dfd3f4c4911ad8c5f18c189914596f45e108f041bf951cbb2a9` である。
01:38 JSTにlauncherのPID47520とaudit driverのPID12660でlive sessionを確認した。
いずれも生成registry待ちで、childや新しいqsubは起動していない。
既存の全件index driverをPID46444、distribution driverをPID41120でC3T0に対して起動し、全件回収待ちのlive sessionを確認した。
全件index・転送・最終設定・最終reportの本番完了はまだなく、最後の設定準備とqsub・回収への自動接続は残る。
