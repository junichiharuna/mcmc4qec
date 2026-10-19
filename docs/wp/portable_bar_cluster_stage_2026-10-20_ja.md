# 最終集計用コードのクラスタ配置と80群の回収

2026-10-20 00:28 JST時点の記録である。
公開候補 `47ef1b6` と既存の計算bundleを変更せず、最終集計用コードを別directoryへ配置した。

## クラスタへの配置

配置先は `/home/user/workspace/mcmc4qec/20261020-portable-final-provider-v1` である。
固定済みの26ファイルをarchiveから転送し、転送archiveと展開した全ファイルのhashを照合した。
archiveのSHA-256は `20f1c70c26b0bf08bb6f7a7178d0e815df6aadb271cb4e70bcf4775a3a524250`、source manifestは `28cb875a47447a75dd3965e580621c0298258c1f22f874d12f9a2cc40de0f744` である。
既存bundleのvenv（Python 3.11.9）と元sourceを用い、最終CLIのhelp表示、import、analyzerとloaderのsource変換規則を確認した。
照合した元analyzerのSHA-256は `4b2e4fa26ab54180dbdf4bc9cdfadd2cbe0781087037c84ac343def481080f7e` であり、固定した元実装と一致した。
配置結果は [stage receipt](data_portable_bar_2026-10-19/final-provider-stage-receipt-v1.json)、実行した配置scriptとログは同じdata directoryへ保存した。
この確認はimportとCLIの起動確認であり、native trace監査や最終cohort解析を実行したものではない。
今回の配置ではqsubを実行せず、新しい科学計算jobを投入していない。

## 回収と後続バッチ

DGX batch 3の20群を回収し、後続batch 4が起動した。
batch 0～3の4 archiveを再検証した [80群の途中index](data_portable_bar_2026-10-19/first80-cohort-inventory-v1.json) では、全768群・67584行に対し、回収済み80群・7040行、未回収688群・60544行である。
回収済みのflagged行は7040、診断未定義行は4264、区間未取得とinfrastructure failureは0だった。
診断とACF配列は各186240件であり、未定義やflagged行を分母から除外していない。
これらは設定を含む行数であり、独立seed数とは区別する。
batch 4の回収準備も完了し、実行中のexecution intentをhashで固定した。
次のbatch 5は、元samplingの完了groupが255群になった時点でも固定host割当の20群が揃わず、予約・起動していない。
入力の選択に推定値や診断結果は使っていない。

## 実行中資源の確認

クラスタの `265334.node-PRISM` と `265338.node-PRISM` は実PBS状態がRで、それぞれ96 CPUを使用していた。
最大2ノードの制限を維持している。
Laboの本計算は24 workerが生存し、各workerの累積CPU時間は約8100秒、優先度は全てNormalだった。
Laboの全設定照合も別の1 processでCPU時間の増加を確認している。
これらは稼働確認であり、比較条件を揃えた速度benchmarkではない。

## 残作業

Labo側の全設定照合の完了・回収、全samplingと全768群の後処理、元native環境のtrace監査が残る。
全入力が揃ってから最終contextを固定し、既存のqsub手順と2ノード制限の下で正式なreference比較を実行する。
名目95%被覆や母集団RMSEの保証は引き続き行わない。
