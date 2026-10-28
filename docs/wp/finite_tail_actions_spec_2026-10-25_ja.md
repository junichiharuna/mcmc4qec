# Tail 全段階の有限 PBS action と投入引継ぎ

対象は census / independent / report の準備・実行の全6 roleと final-reportである。
現行 v8、元環境、科学source、既存出力を変更せず、新版 adapter と設定で実装する。
outer CLIは `--config PATH --config-sha256 SHA --role ROLE` を維持する。

大きい result / selection / bundle / plan の読込・deepcopy・hash・元 read_plan / validate / seal は有限PBS actionの中で実行する。
元の科学的検査、計画digest、seed、選択、数値結果は削除・変更しない。
外側controllerは上限付き小JSON、qstat、小source/script/intentのhash、大きいcarrier fileのstat fingerprintだけを扱う。
大きいJSONや結果hashを外側で再計算しない。
待受のqstatは検証済み科学結果を意味せず、terminal候補を発見した後は元のobserve / finish / sealをPBSで実行する。
準備roleは上流完了を確認してから起動し、待受ループをPBSで保持しない。
最終reportのhash・回収確認も有限PBS actionに含める。

## 二段階の submit

三系統の元submitはqsub直前にuncertain=Trueを設定し、runner例外時に元lockを保持する契約を持つ。
既存runner注入APIを使い、元submitの全deep検査・元intent保存・最終検査を実施して本物のqsub呼出し直前へ到達する。
専用Deferred例外を返すrunnerはqsubを実行せず、偽job IDや成功ledgerを生成しない。
元lockのbytes/hash/inode、元intent、実script/command/resource、元plan digest、action request/source/PBS identityを小さいdispatch-ready receiptへ固定する。
このreceiptは「投入待ち」であり、既存qsub成功receiptとは別purposeにする。
親PBSがF / exit0 / run_count1で退場したことを確認するまで、外側は子jobを投入できない。
外側は同じ元lockの所有権を継承して検査し、同じlockを再取得しない。
そのlockを保持したまま実際のgateを再実行し、小script/source/intent pinと大carrierのstatを照合してからqsubを一度だけ実行する。
元形式のqsub response / submission ledgerを保存し、結果を確定できた場合だけ元lockを解放する。
曖昧応答、timeout、途中中断、元intentやlockの変更は再投入せず、記録とlockを保持して照合待ちにする。

## 親自身の資源計上

深い検証を行う親PBSの現在の実qstat観測は原本として保存する。
元submitの事前gateへ渡す「親退場後の投入可能性」用viewでは、この検証済み親jobだけを除外できる。
除外は実PBS観測の書換えではなく、別の明示viewであり、現在の資源空きや投入許可を主張しない。
親の実job ID・script・resource・stateを検証できない場合は除外しない。
外側は親退場後に除外なしの実観測でgateを再実行する。
親R＋他の子R、親F＋二つの子R、親F＋一つの子Rを別fixtureとし、前二者で実投入しない。
helperのqsubは既存physical gateを使い、元science lockを保持している間は次のhelper投入を始めない。
capacityの340 GiB、benchmarkの96 CPUと親の予約を同時に必要とする状態で待ち続けない。

## 検証の時間差と真正性

deep検証は親PBS内の記録時点に行われ、外側stat確認を内容hashの再検証とは呼ばない。
元input pinとdigest、親actionのsource、request、実PBS終端、外部から固定したreceipt hashを結び付ける。
dispatchまでの時間差を記録し、元source/script/intent/lockのhashと大carrierのstatが変われば拒否する。
元の本計算側のdeep input検証はそのまま実行され、外側のstat検査で置き換えない。
大きいplan/resultを含むproof全体をouter stdoutへ戻さず、PBS内のartifactとその小さいpinで渡す。
report内部の巨大proof IPCと120秒制限は、元検査を保った別operational overlayで扱う。

## 分担用API

family pluginは `execute(action, ctx, task=None, post_source='', *, sources, hooks=None)` を提供する。
`sources` は外部で固定した元remote/helperのpinを持ち、pluginは実bytesを検証してから元関数を使う。
`hooks` はsubmit専用であり、`runner` と `exclude_parent(jobs)` を提供する。
runnerは正しい一つのqsub commandだけをDeferredとして記録し、qstat等の既存読取は元runnerへ渡す。
非submit actionにはhooksを渡さず、元のremote処理をそのまま実行する。
共通action worker、receipt、Deferred/finalizer、outer orchestrationは別moduleに置き、family pluginは科学的な行の省略や書換えをしない。

受入は元submit内のdeep call順と回数、qsub前停止、元lock/intent保持、親退場条件、gate再入deadlock、曖昧応答、fingerprint/source改変拒否、大小payloadのcontroller読込境界を含める。
実CLIのnative bootstrapと実大metadata actionのRSS・時間はPBSで別途検証し、未測定の資源予算を性能保証とは扱わない。

## 外側の実装境界と有限carrier

外側は元のexecution driverとschedulerを読み込み、既存の24選択行・48計時行・192 replicateの判定を変更せず、remote actionと大きい回収処理だけを有限PBSへ委譲する。
未終端の待受は実qstatの小さい観測だけとし、科学的な検証結果とは呼ばない。
終端を見つけた後は元observeとfinish/sealの検査をPBS内で実行し、投入前は元submitの全deep検査を実行する。
準備3役は上流のcompleted receiptが存在し、変更されていないことを確認してからPBSへ移し、PBS内で上流待受を始めない。
最終報告の回収とhash照合もPBS内で行い、外側へ返すのは小さいreceiptとartifact pinだけとする。

元driverのcollection用stable closureが保持しているsource・environment・accepted receiptのpinを、待機前にそのままpayloadへ複製する。
PBS開始後の新しいhashを元pinとして採用せず、元のキー集合と値を照合する。
census/reportの回収suffixは元bytesから抽出し、コピー、hash、descriptor比較、completedとmanifestの生成を残す。

外側の通常ファイル読込は4MiBを上限とし、qstat・ps・qsubの出力も一旦fileへ受けて上限付きで読む。
元submitのfinalizerには、このboundedな実query・実gate・実qsub runnerを明示して渡す。
この運用上の読込制限はsandboxや科学検証を意味せず、native bootstrapと大payloadの検証をPBSへ配置する境界である。

Deferred carrierはmanifest・plan・config・selection・bundle・environment・script・intent・lock等の有限control集合に限る。
数十万のraw入力mapを外側へ展開してstatせず、deep検証時点の照合とdispatch時点のcontrol statを区別する。
raw全体がdispatch時点でも不変である保証は主張せず、本計算の既存deep入力検査を維持する。
承認済みaliasは宣言pathとresolved targetを分け、aliasのlstat・link target・target stat・宣言hashを記録する。
native binaryの外側read/hashは行わず、runtime pathも変更しない。

## 動的な物理nodeの接続

元の科学jobのunbound selectをbound selectへ書き換えない。
既知の科学jobが1件Rの場合に限り、実job ID・元submission/script pin・実R観測のrun count・stime・exec_vnode等を別の動的policyへ束縛し、他の1nodeへ有限helperを配置する。
Q等で配置不明、未知job、2node占有、同一性不一致の場合は待機または拒否し、元のqstatを別の状態へ置換しない。
有限helperがF0で資源を解放した後に実gateを再確認してから次の科学jobをqsubする。
動的policyが利用できない経路では既知child全件の終端を待つ安全側の経路を保ち、この経路を並列性能の達成とは扱わない。
helperのCPU・memory・walltimeは1 CPU・96 GiB・4時間の未測定予算を保ち、動的に変えるのは物理nodeだけとする。
