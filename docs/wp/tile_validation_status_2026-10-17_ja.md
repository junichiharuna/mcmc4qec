# Tile code-capacity検証の進捗

## 2026-10-19 11:19 JST: C0T0標本生成完了・集約投入

C0T0 sample1の265316は10:14:06にF/exit0/run_count1、wall04:32:08で終了した。
既定collectorのprepareでanchor265312・sample0の265313・sample1の265316について実PBSと保存metadataの正常終了を確認した。
prepare・preflight後、qsubでsampling collector265323を投入し、実R/run_count1を確認した。
collectorは1node・1CPU・32GiB・要求上限02:00:00であり、この上限はETAではない。
265319は引き続きRで、265323と合わせた要求node数は2である。
prepared SHA256は`45c9015ab98bd1468a7305630106c4161602516737f705df2445e67470de4db6`で、実記録は[data_tile_validation_2026-10-17/low_partition_collection_0_0_execute_once_v1_receipt.json](data_tile_validation_2026-10-17/low_partition_collection_0_0_execute_once_v1_receipt.json)にある。
collectorの完了受理・解析・trace監査・最終比較は未完了であり、正式比較の完了数は3/12条件のままである。

## 2026-10-19 08:51 JST: C0T1資源計測完了・次の標本生成

C0T1解析capacityの265318はF/exit0/run_count1・00:26:53で終了した。
固定observerで35artifactと4派生JSONを回収し、source・native・実PBS・前後snapshotとlocal hashの一致を確認した。
本解析の資源案は96worker・234GiB・1partition・要求上限07:30:00であり、人工データによる資源計測であって精度の証拠や所要時間保証ではない。
空いた1nodeでC0T1 sample0を既定入口からqsub265319として投入し、265316と265319の実R・要求node合計2を確認した。
実記録は[data_tile_validation_2026-10-17/low_partition_dispatch_20261019_0851.json](data_tile_validation_2026-10-17/low_partition_dispatch_20261019_0851.json)に保存した。
正式比較は3/12条件完了のままで、次にC0T0 sample1が終了したら同条件のsampling collectorを優先する。

08:48時点の予想として、265316は同条件の先行partition実測04:28:24を05:41:58の開始時刻に加え、10:10頃を目安とした。
残り9条件のsampling resourceのpredicted_secondsから完了済み3partitionを除き、実行中265316の観測経過03:04:44を引いた合計は144.1237node時間だった。
2nodeを標本生成だけに充てた単純外挿は72.0619時間で、10月22日朝頃に相当する。
これは制限時間の合計や完了下限ではなく、予備計測に基づく条件付きの目安である。
解析・監査・独立計時とのnode共有、待ち行列、転送・最終文書作業を含まないため、全体の完了時刻は未確定とする。

## 2026-10-19 08:24 JST: 次条件のcapacity回収準備

実265318に固定したC0T1解析capacity observerを、既受入observerの条件literalと入力pinだけを変更して作成した。
16件・0.91秒の受入と、literal以外のAST一致を確認した。
実remoteのrunning1観測も成功し、R/run_count1とsource・小artifactの前後一致を確認した。
capacityはまだ実行中でmeasured_profileはnullであり、完了profileの回収・本解析の資源決定は未実施である。
08:24のqstatでは265316と265318がともにR/run_count1で、要求node数合計2を維持している。
正式比較は3/12条件完了のままである。

## 2026-10-19 08:22 JST: sampling partition完了と次条件の投入

C0T0のsample0・265313はF/exit0/run_count1・04:28:24で終了した。
凍結readerで実plan・保存summary・native metadata・PBSを照合し、61,440 task・失敗0を確認した。
これは1partitionのmetadata受理であり、raw payload全確認やC0T0全体の正式比較完了ではない。
sample1・265316は引き続き実行中である。
空いたnodeでC0T1・p=0.003のanchorをqsub265317として投入し、F/exit0/run_count1・00:00:30、192 task・失敗0を確認した。
続いて同条件の解析capacityをqsub265318として投入し、実行中であることを確認した。
capacityは人工データによる資源計測であり、精度・混合・被覆の科学的証拠には含めない。
実active jobから要求node数合計2を確認し、待機中を含む最大2nodeを維持した。
sample0確認の最初のobserverは保存PBSの縮約形式にrun_countがないため停止したが、失敗証拠を保持し、v2で実qstatのrun_countを別途照合した。
数値計算の再実行や既存成果物の上書きは行っていない。
正式比較は3/12条件完了のままであり、C0T0の両sampling終了後はsampling collectorを優先する。

## 2026-10-19 08:18 JST: 算術レビュー入力の実転送確認

最終reportが固定するproduction planとrowsをscpで回収する入口を実装し、Windows15件・0.74秒とLinux15件・0.05秒の受入に成功した。
分割samplingのsampling_manifestとwrapper manifestを区別し、回収後のplan identityと全ファイルSHAを照合する。
完了済みC2T2で実転送し、2,362 byteのplanと330,061,028 byteのrowsがreportの固定hashに一致した。
既存の算術レビューに使用したbytesと同じであるため、数値再計算は繰り返していない。
残り9条件の本番適用は未実施で、正式比較は3/12条件完了のままである。
08:18時点で265313はR/run_count1・04:26:59、265316はR/run_count1・02:34:39、要求node数は合計2だった。

## 2026-10-19 08:15 JST: 全条件向け算術レビュー

C2専用だった集計算術の独立レビューを一般化し、production planから352設定と最長traceの比較行を構成するようにした。
tile72 bit-flipの16chain・60,000保存と、他条件の設定を区別する。
参照下端0・参照未取得・point欠損・微小確率を扱い、失敗・未定義診断・区間未取得を全192 replicateの分母に残す。
Windows17件・0.37秒、Linux17件・0.04秒が成功した。
完了済みC2T2の実67,584 row・352設定を独立算術で再確認し、11,968項目を照合した最大絶対差は1.6940658945086007e-21だった。
これは保存rowの集計算術の一致であり、decoder・raw trace・WSSラベルの独立再計算や95%被覆保証を意味しない。
source・CSV・review記録を保存したが、残り9条件への本番適用は未実施で、正式比較は3/12条件完了のままである。
08:14時点で265313はR/run_count1・04:22:58、265316はR/run_count1・02:30:38、要求node数は合計2だった。

## 2026-10-19 08:10 JST: final回収入口の検証

実assembly・prepare・preflight・execute・sealの全記録から回収authorityを再構成する入口を実装した。
remoteで14件のreport・実行証拠・現在のPBSを照合し、localではmetadataの厳密decodeと別途scpしたreportのSHA・byte数を確認する。
途中変更・不正scope・異なるartifact・転送失敗ではcollection.jsonを作らず、証拠を保持して自動再試行しない。
Windowsでremote受入24件・1.96秒、local受入22件・2.18秒、Linuxで合計46件・0.54秒が成功した。
合成PBS・転送による受入とは別に、完了済みC2T2の実14ファイル・現在のPBS・既存回収済みbytesとの一致も読み取り専用で確認した。
この確認では数値再計算・raw trace走査・qsubを行っておらず、残り9条件の本番回収成功を意味しない。
84 sourceと外部証拠をpartition_final_recovery_transport_v1へ保存し、runbookにseal後の回収手順を追加した。
正式比較は3/12条件完了のままであり、残り9条件の実計算・解析・監査・数値レビュー、独立低ノイズtiming、rawデータ回収が残る。
08:09時点で265313はR/run_count1・04:18:57、265316はR/run_count1・02:26:37、要求node数は合計2だった。

## 2026-10-19 07:57 JST: C0T0 samplingの観測

実sampling planと凍結sourceから各partitionの予定task名を構成し、稼働中directoryの完了marker名を一度だけ数えた。
265313のreplicate 0–95は予定61,440件中58,016件、265316のreplicate 96–191は予定61,440件中30,173件のmarker名が存在した。
期待集合外のmarker名は0件で、両partitionのsummaryはまだ存在しなかった。
観測前後とも両jobはR/run_count1で、観測後のwalltimeは04:06:55と02:14:35、要求node数は合計2だった。
markerの内容・recordの成功失敗・raw payloadは読み取っておらず、これを科学的完了件数として扱わない。
taskごとの費用が異なるため、marker割合からETAを出さない。
観測記録はdata_tile_validation_2026-10-17/low_partition_sampling_observation_20261019_0758.jsonに保存した。
記録名の0758ではなく、内部の実観測timestampは07:57である。
凍結analysis・trace readerと同じbytesのsourceを確認し、analysis context、collector summaryのPBS identity、trace read_planの戻り値がfinal接続の前提と一致することを静的に確認した。
静的確認は実cohortの最終検証や終了証拠ではない。
正式比較は3/12条件完了のままであり、final後のreport回収・数値レビューと独立低ノイズtimingも残る。

## 2026-10-19 07:54 JST時点の更新

実assembly記録を照合して既存final v3のprepare・preflight・execute・sealを呼ぶ一回実行CLIを接続した。
controlは実prepare、executeの脚本・manifest・resourceは実preflight、sealのjob IDは実executeから固定する。
前段記録の欠落・改変をSSH前に拒否し、応答不明のexecuteは証拠を保持して自動再投入しない。
既存final v3のqsub・共有lock・待機中を含む最大2node検査は変更していない。
合成SSH応答を使った受入はWindows24件・5.07秒、Linux24件・1.42秒で成功した。
依存80ファイルをpartition_final_invocation_transport_v1に保存し、low_partition_final_runbook_2026-10-19_ja.mdへ実行順をまとめた。
残り9条件の本番assembly・final各phaseは未実施であり、正式比較は3/12条件完了のままである。
07:54時点で265313はR/run_count1・04:02:54、265316はR/run_count1・02:10:34、要求node数は合計2だった。

## 2026-10-19 07:50 JST時点の更新

完了証拠からconfigを生成するremote assemblyとlocal一回実行CLIを接続した。
既存final v3のsource bindingでbootstrap・scienceを実行し、completed_inputs→entry→upstream→writeを順に呼ぶ。
localでは両completionの実連鎖からrequestを再構成し、固定source・script・intent・stdout/stderr・receiptを保持する。
通信失敗・不正response・実行中のlocal証拠変更は未受理とし、同じ出力先へ再実行しない。
Windows17件・1.28秒、Linux17件・0.28秒が成功した。
実Linuxではnative bootstrap・science通過後に意図的な不正rootを拒否することも確認した。
実C0T0の未完了記録をCLIで検出し、process呼出し0件・production intent生成0件で停止した。
依存78ファイルと外部証拠をpartition_final_assembly_transport_v1へ保存した。
この入口はqsubを呼ばず、本番assembly・config生成とfinal prepare/preflight/execute/sealの接続は未実施である。
正式比較は3/12条件完了のままである。
07:50時点で265313はR/run_count1・03:58:53、265316はR/run_count1・02:06:33、要求node数は合計2だった。

## 2026-10-19 07:45 JST時点の更新

最終比較のmetadata entry構築とconfig保存処理を実装した。
受理済みplan・context・summaryとの一致、両completionの外部hash、追加sourceの凍結manifest、WSS全16条件のmarkerとpayload hashを固定する。
既存final v3のvalidate・provenance・upstream・resource検査と現在のPBS再照合に成功してからconfig.jsonを保存する。
既存の一般metadata制限に従い、sampling-submissions/anchors以下の台帳は専用upstream欄だけに固定する。
Windows21件・6.46秒、Linux21件・0.96秒が成功した。
合成plan・PBSを使用し、native bootstrapとcontroller状態はmockであり、本番cohortの検証成功ではない。
WSS payloadとrows本体をこの段階では読まず、既存final computeの検証範囲に残す。
依存75ファイルと外部証拠をpartition_final_config_v1へ保存した。
全helperを結ぶ実assembly入口とfinal一回実行transport、本番config生成・投入は未実施である。
正式比較は3/12条件完了のままである。
07:45時点で265313はR/run_count1・03:54:53、265316はR/run_count1・02:02:33、要求node数は合計2だった。

## 2026-10-19 07:40 JST時点の更新

最終比較の上流job一覧を既存final v3のselector_jobsで構成し、全sampling・sampling collector・BAR partition・監査・reference・BAR collectorの役割と台帳集合を照合する処理を追加した。
既存check_terminalとcheck_pbsで実終端・脚本・資源・hostを照合し、sampling失敗終了codeやWSS未取得を成功へ置き換えない。
この処理の合成fixture受入はWindows26件・5.01秒、Linux26件・0.65秒で成功した。
初回final資源要求を1 CPU・24時間とし、実collector wall/RSSと追加hash用の未測定予算を分ける処理も追加した。
24時間は完了予測ではなく、実collectorの費用が初回要求枠を超える場合は拒否する。
実trace監査・WSS監査のwall/RSSは別の観測値として保持し、並列時間をserial hash時間へ換算しない。
資源処理の合成fixture受入はWindows13件・0.65秒、Linux13件・0.06秒で成功した。
依存73ファイルと外部証拠をpartition_final_resource_v1へ保存した。
config保存とfinal一回実行transportは未実装であり、本番の資源確定・final接続は未実施である。
正式比較は3/12条件完了のままである。
07:40時点で265313はR/run_count1・03:48:52、265316はR/run_count1・01:58:32、要求node数は合計2だった。

## 2026-10-19 07:29 JST時点の更新

最終比較のremote完了証拠照合を実装し、Windows・Linuxで各19件が成功した。
実completionとpreparedを固定し、既存plan/terminal readerで同一production plan・192 anchor・現在のPBS終端を確認する。
既存final v3のEvidenceを使用し、途中変更・metadata欠落・異なるcohortやscopeを拒否する。
依存69ファイルと外部証拠をpartition_final_assemble_inputs_v1へ保存した。
全上流job census、resource decision、config保存、final transportは残る。
本番のfinal接続は未実施で、正式比較は3/12条件完了のままである。
07:29時点で265313はR/run_count1・03:38:52、265316はR/run_count1・01:46:32、要求node数は合計2だった。

## 2026-10-19 07:24 JST時点の更新

BAR集約とfull trace監査のlocal完了記録を結合する処理を実装した。
Windowsで記録再構成12件と結合条件17件、Linuxで結合条件17件が成功した。
同じsampling collector authority・条件・root・full cohort・scopeを要求し、入力hashの上書きや未完了記録を拒否する。
実C0T0についてprocess呼出し0件で未完了記録を拒否するnegative gateも確認した。
依存66ファイルと外部証拠2件をpartition_final_join_inputs_v1に保存した。
remote metadata組立・resource decision・final一回実行transportは残る。
正式比較は3/12条件完了のままである。
07:24時点で265313はR/run_count1・03:32:52、265316はR/run_count1・01:40:32、要求node数は合計2だった。

## 2026-10-19 07:19 JST時点の更新

既存final v3と生成元環境のsource結合を実クラスタで確認した。
analysis24・trace24・collection42ファイルの絶対パスとbytesが両環境で一致し、finalのbootstrap・science・native/runtime検証も成功した。
静的report closureの外にあるsubmitter1ファイルは凍結acceptance manifestで検証し、final入力にも追加で固定する仕様を保存した。
source配置や科学コードの変更は不要である。
成功記録はlow_partition_final_source_bridge_v2.jsonであり、v1の過剰なsubset仮定による拒否記録も保持した。
完了証拠の結合・remote metadata組立・resource decision・final一回実行transportの実装は残る。
正式比較は3/12条件完了のままである。
07:19時点で265313はR/run_count1・03:28:50、265316はR/run_count1・01:36:32、要求node数は合計2だった。

## 2026-10-19 07:14 JST時点の更新

BAR collectorのremote完了受理とlocal一回実行入口を接続した。
remote側17件がWindows・Linux、local側11件がWindowsで成功した。
実PBS終端・resource・host、実台帳とworker入力証拠、全partition summary hashを照合する。
全768 group・67584行と区間未取得・診断未定義・flag・sampling失敗の件数を保持する。
大きなrowsデータは親側で再hashせず、後続final v3のPBS readerによる内容検証と区別する。
依存38ファイルとLinux記録をpartition_bar_collection_completion_transport_v1へ保存した。
production collector prepare・preflight・execute・completionは全条件で未実施である。
残る親側接続はBAR collector・full trace監査の実証拠をfinal v3へ渡す構築処理である。
正式比較は3/12条件完了のままである。
07:14時点で265313はR/run_count1・03:22:50、265316はR/run_count1・01:32:32、要求node数は合計2だった。

## 2026-10-19 07:09 JST時点の更新

BAR collectorのremote qsub guardとlocal一回実行入口を接続した。
remote側23件がWindows・Linux、local側14件がWindowsで成功した。
共有lockの所有者、全上流証拠と生成物、旧controller停止、待機中を含む最大2nodeを投入直前まで再確認する。
qsub応答が不明な場合はlockとintent・receiptを保持し、自動再投入しない。
依存34ファイルとLinux記録をpartition_bar_collection_submit_transport_v1へ保存した。
production collector prepare・preflight・executeは全条件で未実施であり、完了受理とfinal v3用証拠の接続が残る。
正式比較は3/12条件完了のままである。
07:09時点で265313はR/run_count1・03:18:48、265316はR/run_count1・01:26:30、要求node数は合計2だった。

## 2026-10-19 07:05 JST時点の更新

BAR collectorのremote準備処理とlocal一回実行入口を接続した。
remote側18件がWindows・Linux、local側16件がWindowsで成功した。
凍結bundle・source・native binary・Pythonと全partitionの実完了記録を結合し、worker・control・脚本を固定する。
実C0T0の未完了sampling collectorをSSH前に拒否するnegative gateも確認した。
依存30ファイル・Linux記録・negative gateをpartition_bar_collection_prepare_transport_v1と同階層に保存した。
production collector prepareは未実施であり、qsub入口・親側完了受理・final v3用証拠の接続は残る。
正式比較は3/12条件完了のままである。
07:05時点で265313はR/run_count1・03:14:48、265316はR/run_count1・01:22:30、要求node数は合計2だった。

## 2026-10-19 06:59 JST時点の更新

BAR collectorの入力検証と計算ノードworkerを実装し、Windowsで21件・13件、Linuxで合計34件が成功した。
全partitionの完了受理・metadata・実PBS終端・計画順を確認し、重複なしの768 group・67584行を要求する。
workerは固定controlからPBS脚本を再構成して照合し、既存collectを呼んで全group payloadを検証する設計である。
今回の実行は合成fixtureであり、本番データの集約は未実施である。
依存を含む26ファイルとLinux記録をpartition_bar_collection_components_v1へ保存した。
collectorのprepare・qsub入口・親側完了受理と、final v3に渡す証拠構築は残る。
正式比較は3/12条件完了のままである。
06:59時点で265313はR/run_count1・03:08:47、265316はR/run_count1・01:16:28、要求node数は合計2だった。

## 2026-10-19 06:48 JST時点の更新

full trace監査ジョブの完了受理を接続し、remote側18件がWindows・Linux、local側11件がWindowsで成功した。
768 group全体のmeasurementと件数を照合し、sampling失敗を分母から落とさず保持する。
親側での検証範囲はmetadata・measurement・done markerまでとし、大きな監査payload・raw traceは後続PBS集約で検証する。
全依存39ファイルとLinux記録を保存した。
production full prepare・preflight・execute・completionは全条件で未実施である。
残る接続はBAR collectorと、既存final v3入口へ渡す正式collector・監査の証拠構築である。
正式比較は3/12条件完了、sampling265313・265316は要求2nodeで稼働中である。

## 2026-10-19 06:43 JST時点の更新

full trace監査のlocal qsub入口を接続し、Windows13件が成功した。
full prepareの実記録を再構成して改変をSSH前に拒否し、投入結果が不明な場合は記録を保持して自動再投入しない。
全依存35ファイルを保存した。
production full prepare・preflight・executeは全条件で未実施である。
full完了受理とBAR collector・監査済み集約の親側接続を引き続き進める。
正式比較は3/12条件完了、直近PBSではsampling265313・265316が2nodeで稼働中である。

## 2026-10-19 06:40 JST時点の更新

full trace監査のlocal prepare入口を接続し、Windows12件が成功した。
実データの未完了collectorをSSH前に拒否することも確認した。
full qsubのremote guardはWindows・Linuxで各20件が成功し、同条件capacity・実終端・資源と最大2nodeを投入直前に再確認する構成となった。
全依存33ファイルとLinux記録を保存した。
full qsubのlocal入口、full完了受理、BAR collector・監査済み集約の親側接続は残る。
production full prepare・preflight・executeは全条件で未実施である。
直近PBSでは265313・265316がR/run_count1、要求node数合計2で、正式比較は3/12条件完了のままである。

## 2026-10-19 06:34 JST時点の更新

実測capacityからfull trace監査を準備するremote部品を追加し、WindowsとLinuxで各13件が成功した。
192 replicateの計画と選択worker・資源を既存prepare_fullで検証する構成であり、qsubは行わない。
全依存29ファイルとLinux記録を保存した。
full prepareのlocal入口、full投入・完了受理、BAR collector・監査済み集約の親側接続は残っている。
production full prepareは未実施で、正式比較3/12とsampling2ジョブ稼働という状態は変わらない。

## 2026-10-19 06:31 JST時点の更新

trace capacityの正式完了受理をremote・local双方に接続した。
remote側16件がWindowsとLinuxで、local側11件がWindowsで成功した。
実execute台帳とPBSを照合し、既存readerを通じて2 replicate・8 groupのcapacityを検証する構成で、全192 replicateの本監査完了とは区別する。
全依存27ファイルとLinux受入記録を保存した。
production trace prepare・preflight・execute・completionは全条件で未実施である。
実測full監査の準備・投入・完了受理と、BAR collector・監査済み集約の親側接続が残る。
直近PBSでは265313・265316がR/run_count1、要求node数合計2で、正式比較は3/12条件完了のままである。

## 2026-10-19 06:26 JST時点の更新

分割sampling対応trace capacityのpreflight・一回qsub入口を接続した。
remote側28件がWindowsとLinuxで、local側13件がWindowsで成功した。
準備台帳と実source・入力、上流job終端、共有lock、待機中を含む最大2nodeを確認し、投入応答不明時の自動再試行を拒否する。
人工fixtureでの受入であり、production trace prepare・preflight・executeは全条件で未実施である。
再現source・テスト・依存23ファイルとLinux記録を保存した。
capacity完了受理と実測full監査、BAR collectorと監査済み集約の親側接続は残る。
sampling265313・265316が引き続き2nodeで稼働し、正式比較は3/12条件完了のままである。

## 2026-10-19 06:21 JST時点の更新

分割sampling対応trace監査のcapacity準備をremote部品とlocal入口まで接続した。
remote側15件がWindows・Linuxで、local側12件がWindowsで成功した。
BAR解析とは独立してcollector完了証拠から準備できる。
実case0 target0にはcollector完了記録がまだないため、SSH前に拒否され、production prepare・qsubは未実施である。
source・依存17ファイル、検証記録、実行手順を保存した。
trace側のqsub・完了受理・実測full接続と、BAR側のcollector・監査済み集約の親側接続は残っている。
正式比較は3/12条件完了、samplingは265313・265316の2ジョブが稼働中である。

## 2026-10-19 06:17 JST時点の更新

分割BAR解析の親側完了受理を実装し、remote側はWindows13件・Linux13件、local側はWindows11件が成功した。
実executeの記録、PBS終端、計画と資源、全groupのdone markerを照合し、途中変更や不明な応答を受理しない。
この処理はmetadataとmarkerの確認であり、JSON/NPZ本体の全検証は後続のPBS collectorで行う。
source・テスト・依存22ファイルとLinux実行記録を保存した。
production解析のprepare・preflight・execute・completionは全条件で未実施である。
直近のPBS観測では265313・265316がともにR/run_count1、要求node数合計2で、正式比較は3/12条件完了のままである。
解析collectorと分割samplingに対応するtrace監査の親側接続を引き続き進める。

## 2026-10-19 06:07 JST時点の更新

分割BAR解析のpreflight・一回qsub入口を接続した。
remote側22件がWindowsとLinuxで成功し、local側14件も成功した。
共有lock owner、prepared台帳との一致、source/nativeと入力、実終端、旧controller終了、待機中を含む最大2nodeを確認し、不明な応答では記録を残して再投入しない。
実qsubを行わない人工fixtureでの受入であり、実解析prepare・preflight・executeは全条件で未実施である。
解析結果の完了受理・回収は引き続き未実装で、次に接続する。
再現source/test18ファイルとLinux receiptをデータディレクトリへ保存した。
実PBSで265313・265316の稼働と要求2nodeを確認し、正式比較3/12条件という状態は変わらない。

## 2026-10-19 06:00 JST時点の更新

BAR解析の親側prepareに、正式collector記録と同条件capacityを読むlocal入力helperと一回実行入口を接続した。
入力helper13件・transport10件がWindowsで成功し、case0 target0の実capacity受理記録も全artifactを照合して読み込めた。
現時点ではcollector完了記録がないため、実local入力構築がSSH前に拒否されることを確認し、production prepareとqsubは行っていない。
source・テスト・依存13ファイルをデータディレクトリへ保存した。
解析qsub guardと完了回収は未実装で、詳細は`low_partition_analysis_parent_review_2026-10-19_ja.md`に追記した。
正式比較は3/12条件完了のままである。

## 2026-10-19 05:54 JST時点の更新

分割sampling後のBAR解析について、親側remote prepare部品を小仕様・受入テスト・実装の順に追加した。
WindowsとLinuxで各22件が成功し、未完了・別条件・入力変化・既存出力を拒否してqsubを行わないことを人工fixtureで確認した。
科学計算コードと事前固定した設定は変更していない。
実データ用のlocal入力構築・一回実行入口・解析qsub guard・完了回収は未実装で、production prepareも未実施である。
詳細は`low_partition_analysis_parent_review_2026-10-19_ja.md`に保存した。
実PBSでsample265313・265316のR/run_count1と要求node数合計2を確認した。
正式比較は3/12条件完了のままである。

## 2026-10-19 05:50 JST時点の更新

次のtile72 bit-flip p=.003について、anchorとsample両分割の固定入口preflightが全て成功した。
3preflightは消費済みで、executeは全て未実施である。
実source・実行環境・計画を確認したが、265313と265316が2nodeで稼働中のためqsubは行っていない。
同条件のanalysis capacityはローカルdry-runで入口と固定資源を確認し、実行は未実施である。
次の空き枠では、現条件の両sampleが終了済みならcollector、片方が稼働中なら次条件のanchorとcapacityを進められる。
正式比較は3/12条件完了のままである。

## 2026-10-19 05:47 JST時点の更新

受理済みtile72 depolarizingの3条件について、同じ8 chain・burn6000・保存12000・fineの12設定断面を横断整理した。
相対RMSEはp*=.01で約2.66〜3.14%、.003で約3.46〜4.02%、.001で約4.34〜4.86%だった。
全12行の全192 seedに診断flagが残り、未定義診断を含むseedは順に0、139〜152、192だった。
各p*でdecoder priorが異なるため、failure集合の同一性やpのみの効果を仮定しない。
日本語報告・12行CSV・入力と出力のhashは`data_tile_validation_2026-10-17/low_case2_three_targets_v1/`に保存した。
これは保存済みの受理済み集計の整理であり、新たな科学計算やqsubではなく、正式比較は3/12条件のままである。

## 2026-10-19 05:44 JST時点の更新

tile72 depolarizing p=.001の最終比較265315は47分24秒でF/exit0/run_count1となり、正式seal・結果回収・全352設定の算術照合を完了した。
全67,584行に基づく10,208項目の最大絶対差は2.141×10^-16未満で、事前に集計した診断件数とも一致した。
低ノイズ正式比較は3/12条件完了となった。
8 chain・burn6000・保存12000・fineの固定sliceでは相対RMSE約4.34〜4.86%、block1024の参照区間全体包含は173〜174/192、cross-chainは174〜181/192だった。
点推定と区間は全seedで取得したが、全seedに診断flag・未定義診断が残り、収束・名目95%被覆の保証や推奨設定とは扱わない。
日本語報告とtrace長比較図は`data_tile_validation_2026-10-17/low_final_case2_target2_scientific_review_v1/report_ja.md`から参照できる。
空いた枠にcase0 target0・tile72 bit-flip p=.01のsample partition1をqsub265316として投入した。
実PBSで265313と265316がともにR/run_count1、要求node数合計2であることを確認した。
残り9条件の分割本計算26jobは3job投入済み・23job未投入である。
case0 target0の全anchor/sampleは投入済みで、sample両分割の終了後に準備済みcollectorを実行する。
低ノイズ独立計時、残り9条件の正式比較、全raw archive回収は未完了である。

## 2026-10-19 05:03 JST時点の更新

case2 target2・p=.001の回収済み67,584行を標準ライブラリで独立集計し、全352設定で各192 seedの重複・欠落がないことを確認した。
点推定・区間は全設定192/192、task失敗と区間未取得は0だった。
一方、全設定でflag・high R-hat・low ESSが各192/192で、未定義診断を含むseedは190〜192/192だった。
最大予定8 chains・burn6000・保存12000・fine ladderの固定16設定では未定義も各192/192だった。
これはseed内の観測量やrungを集約した保存指標の件数であり、全chainの個々の診断を一律に未定義と扱わない。
区間取得を混合確認・精度保証とは扱わず、分母から診断未定義を除外していない。
結果は`data_tile_validation_2026-10-17/low_case2_target2_row_diagnostics_v1/`に保存した。
最終比較265315の出力との全統計量照合は未実施で、正式比較2/12条件という状態は維持する。

## 2026-10-19 04:53 JST時点の更新

case2 target2・tile72 depolarizing p=.001のcollection265314は46分23秒でF/exit0/run_count1となった。
最新r8で全768group・192 replicate・67,584行の正式completionを受理し、4ファイル・455,697,306 bytesを回収してproducer hashと照合した。
この回収は集約結果と証拠であり、元trace全体のlocal回収ではない。
固定final wrapper v3用のmetadata configを作成し、prepareとpreflight後に最終比較をqsub265315として投入した。
要求は1 CPU・32 GiB・8時間30分であり、既存の保守的な式による資源上限であってETAではない。
04:53の実PBS観測ではsample265313とfinal265315がともにR/run_count1、要求node数合計2だった。
target2 finalのprepare・preflight・executeは消費済み、sealと結果回収・全行照合は未実施である。
正式比較は結果検証まで終えた2/12条件のままとし、次の空き枠でcase0 target0 sample partition1を投入する。

## 2026-10-19 04:34 JST時点の更新

次に実行するcase0 target0・tile72 bit-flip p=.01のsample partition1について、固定入口のpreflightを実施した。
実source・manifest・Python/native・fixture・PBS脚本と旧controller終了を確認し、成功した。
観測した要求node数は2で空き枠なしのため、qsubは行っていない。
このpartitionのpreflight操作は消費済み、executeは未実施である。
preflight成功時点の空き枠を後の投入可否として扱わず、execute時にも固定入口が現状を再確認する。
実行中は引き続き265313と265314で、低ノイズ正式比較は2/12条件完了である。

## 2026-10-19 04:29 JST時点の更新

case2 target2・p=.001の最終比較metadata adapterを、受理済みtarget1の処理から対象条件と実入力証拠だけの置換で準備した。
定数以外のASTが同一であることを確認し、統計処理と資源算定の式は維持した。
投入receiptの誤用と別targetの完了receiptを渡す2件は、subprocess呼出前に拒否された。
collection265314が実行中のため、assembler実行・最終比較config・prepare・qsubは未実施である。
詳細は`low_target2_final_adapter_2026-10-19_ja.md`に記録した。
低ノイズ正式比較は2/12条件完了のままである。

## 2026-10-19 04:26 JST時点の更新

残る9条件すべてで、固定sampling計画とanalysis capacity計画のproduction設定が実remoteファイル上で一致した。
case0 target0の受理済みcapacity265276を全artifact・実PBS・Python/nativeと再照合し、v11で得る解析資源が受理済みv3結果の1 partition・96 workers・226 GiB・6時間と一致した。
この要求上限をETAとは扱わず、未測定のほか8条件へ流用しない。
全9条件のsampling completionと解析prepareは未実施で、完了sampling受理後にBAR解析とtrace監査へ進める。
根拠と後段の実行順は`low_partition_analysis_bridge_2026-10-19_ja.md`に保存した。
今回の検査によるqsubとremoteファイル変更はない。

## 2026-10-19 04:23 JST時点の更新

分割collectorの完了を実投入receipt・F/exit0/run_count1・全task indexと照合する別入口を実装した。
失敗taskを除外せず、親側でraw payloadを再走査したという扱いも避ける。
Windowsで21件・1.55秒、Linuxでremoteの11件・0.09秒が成功し、sourceと再現手順を保存した。
実collectorの完了受理は未実施で、後段解析・監査への接続が残る。
04:23の実PBS観測では265313と265314が引き続きR/run_count1、要求node数合計2だった。
低ノイズ正式比較は2/12条件完了のままであり、この追加受入で科学計測の完了数は増やしていない。

## 2026-10-19 04:22 JST時点の更新

残る9条件向けに、全generator投入証拠・実PBS終端・run_count1を結合する分割collectorのprepare・preflight・execute入口を実装した。
固定科学計算sourceとgenerator guardは変更せず、失敗taskも保持する。
新規受入はWindowsで27件・2.55秒とguard10件・0.71秒、Linuxでremoteとguard28件・0.34秒が成功した。
詳細・再現手順・source保管先は`low_partition_collection_transport_review_2026-10-19_ja.md`に記録した。
実collectorのprepareと投入は未実施で、case0 target0はsample partition1の投入・終了待ちである。
04:20の実PBS観測ではsample265313とcase2 target2 collection265314がともにR/run_count1、要求node数合計2だった。
低ノイズの正式比較は2/12条件完了のままである。

## 2026-10-19 04:03 JST時点の更新

p*=.001のBAR解析265306は1時間32分6秒でF/exit0/run_count1となり、全768group・67,584行の正式completionを受理した。
受理済みの全trace監査265311と結び付けて結果集約を準備・dry-runし、qsub265314として投入した。
要求は1 CPU・32 GiB・24時間の既定初回上限であり、ETAではない。
実receiptを用いた最新readinessはtarget2 r8、SHAは`ebc0be880797037df36df976474dc60d2178572ff634d4707c976039126502e8`である。
collectionのprepare・dry-run・executeは消費済みで、completionは未実施である。
04:02の実PBS観測ではcase0 target0 sample265313とcollection265314がともにR、要求node数は合計2だった。
集約終了後に正式completion・回収・WSS最終比較を行い、それまでは低ノイズ正式比較2/12条件という状態を維持する。

## 2026-10-19 03:51 JST時点の更新

tile72 bit-flip・p=.01のanchor265312は30秒でF/exit0/run_count1となった。
summaryのmetadata観測では予定192 task・観測192・欠落0・失敗0だったが、raw payloadの照合と全分割を合わせた正式検証は後段collectorで行う。
空いた枠に同条件のsample partition0をqsub265313として投入し、96 workers・32 GiB・15時間30分の事前資源上限を維持した。
この要求時間はETAではない。
sample partition1と他8条件は未投入で、残り9条件の全26jobのうち投入済みは2本である。
03:50の実PBS観測はtarget2解析265306とsample265313がともにR、要求node数合計2だった。
次は265306の終了後に正式completionを受理し、p=.001のcollectionを準備する。
低ノイズ正式比較は引き続き2/12条件完了である。

## 2026-10-19 03:48 JST時点の更新

p*=.001の全trace監査265311は7分54秒でF/exit0/run_count1となり、全768group・92,160予定task・監査失敗0の正式completionを受理した。
これは保存compact値・initial/checkpoint等の既定監査であり、全物理trajectoryの再復号や混合・被覆の保証ではない。
同条件のBAR解析265306は継続中で、終了後に既存phase入口とreadiness r6でcompletionを受理してからcollectionへ進む。

残り9条件の分割本計算を開始し、tile72 bit-flip・p=.01の192 seedそれぞれの独立anchorをqsub265312として投入した。
anchorは同じseedのkernel・初期化設定間で共有し、異なるseed間では共有しない。
これは事前固定26分割jobの最初の1本で、96 workers・32 GiB・1時間の要求上限を維持する。
1時間は資源上限でありETAではない。
sample index0の実クラスタpreflightも成功したが、sample本体はまだ未投入である。
03:48のPBS観測では265306・265312がともにR、要求node数は合計2である。
低ノイズ正式比較は2/12条件完了のままで、独立計時・raw archive実回収は残る。

## 2026-10-19 03:39 JST時点の更新

p*=.003の最終比較265308は42分19秒でF/exit0/run_count1となり、正式seal・14ファイル110,996,144 bytesの回収・全352設定の別算術照合を完了した。
低ノイズ正式比較は2/12条件まで完了した。
照合は67,584行・10,208 scalarで一致し、最大絶対差は2.12×10^-16未満である。
[p=.003の比較報告](data_tile_validation_2026-10-17/low_final_case2_target1_scientific_review_v1/report_ja.md)に有限WSS区間に対するbias・RMSE・被覆と制約を保存した。
固定8 chain・burn6,000・保存12,000・fineの16設定は点推定・区間を全192 seedで取得したが、全192 seedに診断flagが残り、診断未定義も139〜152 seedだった。
診断未定義を分母から除かず、名目95%被覆や推奨設定を確定していない。

一回投入待機は正常終了を検出し、p*=.001の全trace監査をqsub265311として投入してreadiness r6を作成した。
session58846は成功終了し、再起動しない。
r6 SHAは`0ff44a6dd700a776133233ed3b966be24792b9d053b750f83f5fe9206d0ba6fd`で、trace-full executeは消費済みである。
03:39のPBS観測では解析265306と全trace監査265311がともにR、要求node数は合計2である。
両jobのcompletion、target2集約・最終比較、残り9条件の分割本計算、低ノイズ独立計時とraw archive実回収は未実施である。

## 2026-10-19 03:22 JST時点の更新

03:21の実PBS観測では解析265306・最終比較265308がともにR/run_count1で、固定脚本pathも一致した。
準備済みtarget2 trace-fullだけを対象とする一回投入待機を起動した。
入口は`data_tile_validation_2026-10-17/low_trace_full_dispatch_waiter_v1.py`、稼働sessionは58846である。
待機は両jobを45秒ごとに観測し、いずれかのF/exit0を確認後、既存phase入口のexecuteとactual receiptによるreadiness r6更新を各1回だけ行う。
qsub直前の共有lock・全jobの要求node数・最大2node検査は既存入口に任せ、空き枠の観測だけで上限を判断しない。
待機中に同じtrace-full executeを手動で並行実行しない。
観測失敗は終了と解釈せず、最大3時間の待機期限や投入・readiness失敗時は証拠を残して親の確認へ戻る。
追加9テストは0.32秒で成功したが、現時点では新たなqsubは未実施である。
仕様・固定source SHA・次操作はdispatch台帳に記録した。

## 2026-10-19 03:15 JST時点の更新

03:14のPBS観測では解析265306と最終比較265308がともにR、要求node数は合計2である。
両jobのcompletion・sealは未実施で、低ノイズ正式比較の完了件数は1/12のままである。
次の空き枠では準備済みtarget2のtrace-fullを優先する。

完了済みp=.01の解析データ回収処理を追加し、全768group・2,307 archive memberの受理済みhash一覧を作成した。
解析archiveのWindows受入72件・Linux v7受入92件に加え、PBS worker追加後の関連62件がWindows4.14秒・Linux0.95秒で成功した。
投入制御の追加10件も0.58秒で通過し、解析exportのstageと実クラスタpreflightを完了した。
preflightは2ノード使用中を正しく検出し、qsubは行っていない。
sampling・解析の両exportとも実投入とローカルraw archive回収は未実施である。
詳細は[回収処理の検証記録](tile_low_noise_archive_review_2026-10-19_ja.md)とdispatch台帳に保存した。
サブエージェント利用上限のため、この追加処理の独立レビューは未実施であり、親エージェントによる実装・受入・確認までである。

## 2026-10-19 02:58 JST時点の更新

p*=.003の最終比較をqsub265308として投入した。
投入receipt SHAは`ef02eca8863ca054931882670eaa88a6c3d639de4ac75869dabf0b4d2fd6ab8a`で、正式seal・最終report回収は未実施である。
p*=.001の監査capacity265307は5分54秒でF/exit0/run_count1となり、全8group・960予定task・失敗0を正式受理した。
全trace監査の準備は96 workers・87 GiB・3時間30分で完了し、実qsubはまだ行っていない。
最新readinessはtarget2 r5、SHAは`a0fe65f9fd47e12470e2b05a6292832470dc1b5ce1817db1d919c1f0ae6a4823`である。
02:57のPBS観測では解析265306と最終比較265308がともにR、要求node数は合計2である。

回収処理と投入・再現用の20 sourceファイルを`local_orchestration_sources_v14/`とZIPへ保存し、全memberのbytes一致を確認した。
同ZIPはsource snapshotと参照hashの記録であり、raw trace archiveではない。
残り9条件の分割本計算・低ノイズ独立計時・sampling export実投入は未実施で、低ノイズ正式比較の完了件数は1/12のままである。

## 2026-10-19 02:51 JST時点の更新

p*=.003の結果集約265305は42分41秒でF/exit0/run_count1となり、全768group・192 seed・67,584行のcompletionを正式受理した。
集計結果4ファイル377,887,333 bytesを回収し、元completionのhashと転送前後のPBS・metadataを照合した。
回収記録SHAは`3be061a257c984356e2d38322b01aed80f970700266e838fdf09b57371c646c5`で、これは全raw trace回収ではない。
最終比較のconfig assembly・prepare・preflightを完了し、control SHAは`22d4670880e2422154ead7f2bd4be0a1c88c87e4372e312c3a86854b87eebfe7`である。
実qsubはまだ行っておらず、1 CPU・32 GiB・7時間15分という要求は保守的な資源予算で、ETAではない。

p*=.001のtrace監査capacityをqsub265307として投入し、最新readinessをtarget2 r4へ更新した。
r4 SHAは`e9bd8f35078745adfed57b511dc421dacd394ea2c5b1c5e9524bb1dc9aa2a8ae`である。
02:51のPBS観測では解析265306と監査capacity265307がともにR、要求node数は合計2である。

p*=.01のsampling archiveについて、最終比較で検証済みの全184,897ファイルのhash indexを抽出した。
archive・metadata gate・workerの受入はWindowsとLinuxで各56件、投入制御の追加受入は10件を通過した。
固定export配置と実クラスタpreflightも完了したが、export qsubと実回収は未実施である。
詳細は`tile_low_noise_archive_review_2026-10-19_ja.md`、次の具体的な入口とhashはdispatch台帳の02:51追記にある。
低ノイズの正式比較完了は引き続き12条件中1条件であり、推奨設定や名目被覆を確定していない。

## 2026-10-19 02:25 JST時点の更新

p*=.001の転送265304は19分33秒でF/exit0/run_count1となり、転送summary・seal・固定入力の対応を照合した。
本解析をqsub265306として投入し、96 workers・51 GiB・5時間を要求した。
5時間は自身の予備計測と転送実測を反映した資源上限であり、完了予定時刻ではない。
最新readinessはtarget2 r3、SHAは`3709f7fb04b0fd69aa377cca655a8196f151acdbd6917c3fe36c479cde35a961`である。
同条件のtrace監査capacityも準備済みで、実投入は未実施である。
02:25のPBS観測では結果集約265305と解析265306がともにR、要求node数は合計2である。
低ノイズの正式比較は12条件中1条件まで完了し、残りの比較・独立計時・低ノイズ全raw traceのローカルarchive回収は未完了である。
元traceはクラスタ上の計算元と封印済み転送先に保持し、集計結果の回収を全raw trace回収とは扱わない。

## 2026-10-19 02:05 JST時点の更新

p*=.003の全trace監査265302は9分42秒でF/exit0/run_count1となり、全768group・79,872予定task・失敗0の正式completionを受理した。
結果集約のprepare・dry-runを通し、qsub265305として投入した。
最新readinessはtarget1 r8、SHAは`7904e99ee2a701fb5a12696cb9ca18e3efb69b6ff6e2829d49174de7934413d2`で、collection completionは未実施である。
p*=.001の解析capacity265303は6分10秒でF/exit0となり、全35成果物と固定source/native・PBSを照合した。
自身の予備計測に基づく基礎要求は96 workers・51 GiB・2時間で、データ転送の時間は別途加える。
target2自身の証拠でauthorityを作り、copyをqsub265304として投入した。
02:04の観測では265304と265305がともにR、要求node数は合計2である。
次の具体的手順とhashは`data_tile_validation_2026-10-17/low_noise_pending_dispatch_ledger_v5_ja.md`の02:05追記に保存した。

## 2026-10-19 01:52 JST時点の更新

p*=.01の最終比較265299は30分40秒でF/exit0/run_count1となり、正式seal・14ファイル86,595,446 bytesの回収を完了した。
元report SHAは`af5a324a8aedbdf5d38f56f8f58b5a6ba55311cacf0d81d718d6ac8fb131fa8f`、回収記録SHAは`4af89a00b7861b0c302655338b0b6bb635aef2bb3d2db298f93ac8d118557259`である。
全352設定・67,584行の別算術照合は10,208 scalarで一致し、数値と制約を`data_tile_validation_2026-10-17/low_final_case2_target0_scientific_review_v1/report_ja.md`へ保存した。
低ノイズ12条件中の正式比較完了は1条件であり、名目95%被覆や推奨設定の保証は与えない。

p*=.003の全trace監査をqsub265302、p*=.001自身の解析資源測定をqsub265303で投入した。
01:51の観測で両jobはR、要求node数は合計2である。
target1の最新readinessは`low_noise_case2_target1_readiness_r6_v1.json`、SHAは`f2a5d2fa57a6d7e2bc86ff864bc82292dd3779d38e9a14195a28b524e1b3d626`である。
target2資源測定の読取り専用observerを自身のjobと入力hashへ固定し、既存契約の16テストを通した。

後段selector・計時評価の保存参照対応とホスト間検査は、隔離Linux v3で307 passed・111.76秒・skipなしとなった。
87 source・native8件・保存fixture2件を検証し、変更しない83 sourceは従来の固定値と一致した。
新source binding SHAは`d61b03b550dbbfd2c33141d8acc038eda585a9459ab06d80cc91ba05d263dd8d`である。
実装・テスト・検査起動スクリプト・小仕様・レビューの24ファイルを`local_orchestration_sources_v12/`とZIPへ保存した。
これらは後続の実行準備の受入であり、正式selector投入や低ノイズ計時の完了を意味しない。

## 2026-10-19 01:45 JST時点の更新

tile72 depolarizing・p*=.001のsampling265287はF/exit0/run_count1、実時間2時間55分20秒で終了した。
2回の終端metadata観測を照合し、verification SHAは`41c95f8ae0308dfdfb488165e8546329839de776e9d30664b4065b049b874e8a`、stability SHAは`9af7b738c6fd615a90fb4b8b6433363aca2ed34211b64d13dafac49a8d826976`である。
sampling完了だけでBAR解析・trace監査・被覆比較が完了したとは扱わない。
target2自身のanalysis capacityは未投入であり、正式受理後の独自capacity測定が次工程に残る。
空いた枠へtarget1の全trace監査を既存の一回投入入口から実行中であり、この記録時点ではqsub応答をまだ取得していない。

後段selector・計時評価の保存WSS source対応とselector親のホスト間snapshot比較を修正した。
Windowsではsource対応130件、親55件、後続122件の計307テストを通過した。
Linuxの検査用スクリプトにpath比較とspawn起動の問題があり、失敗記録を残して別配置v3で受入を実行中である。
修正の範囲・証拠・制約は`tile_timing_portability_review_2026-10-19_ja.md`に記録する。
正式selectorの全12条件比較と低ノイズ計時は引き続き未実施である。

## 2026-10-19 01:14 JST時点の更新

WSS監査sourceの配置対応をfinal v3へ実装し、Windowsで108 passed・11.30秒、隔離Linuxで108 passed・2.61秒を確認した。
旧・現のsource双方を実bytesで照合し、source配置以外のplan全field、全16監査report、選択条件のraw入力hash、元reference evidenceの保持を検証する。
既存科学source85件とnativeバイナリ8件の一致と、Linuxの試験前後のsource/import/bootstrap一致を確認した。
別bundleと別runでprepare・preflightを実施し、同じ入力・分母・seed・資源要求の最終比較をqsub265299で投入した。
01:14のPBS観測では265299とsampling265287がともにRで、要求node数の合計は2である。
final v3のcontrol SHAは`7898fd4b34d9e34e122bb4989342ef8218ac59cfef58d8cae2361c6240da694d`であり、sealは未実施である。
修正source4件と18証拠参照は`data_tile_validation_2026-10-17/local_orchestration_sources_v11/`とZIPに保存し、全bytesを照合した。
後段selectorにも同じ配置依存の照合があるため、その修正と受入テストは別途必要である。
case2 target1のtrace-capacity265297は8分24秒でF/exit0/run_count1となり、8group・832予定trace・sampling失敗0・監査group失敗0の正式completionを受理した。
全768groupのtrace監査prepare・dry-runを完了し、実測に基づく要求は96 CPU・96 workers・84 GiB・3時間で、全監査jobはまだ投入していない。
target1の最新readinessは`low_noise_case2_target1_readiness_r5_v1.json`、SHAは`c8d728a12c47e66cb1b96c3a80c092ac452442bb608a580f490b4e822a960be9`である。

## 2026-10-19 01:01 JST時点の更新

case2 target0の最終比較v2・265294は28分03秒でF/exit1となり、正式比較結果は得られていない。
停止箇所は`saved_reference`から呼ぶWSS監査planの再検証で、`audit plan, reference context, source or native binding changed`が記録された。
失敗出力・固定control/config・元監査manifestの11ファイルを`data_tile_validation_2026-10-17/low_final_case2_target0_reference_failure_evidence_v1/`へ回収し、転送hashと前後のPBS終端一致を確認した。
completionとfinal-reportが未生成であることを確認し、失敗jobに対するsealは実行しない。
元監査のsource 11件は旧v7配置であり、旧ファイルの現bytesは元hashと一致し、今回の固定configにある同名v11 sourceのhashとも一致する。
配置先に依存した照合があるため、旧証拠を保ったまま明示的なsource対応を検証する小仕様・受入テストを準備する。
配置差以外の入力・native等の一致条件を緩めず、修正後の正式比較を完了するまでは結果を受理しない。
空いた枠へcase2 target1のtrace-capacityをqsubし、job ID `265297.node-PRISM`を取得した。
最新readinessは`low_noise_case2_target1_readiness_r4_v1.json`、SHAは`8ca7ad34e260eace8e8a25a9d2d7b0c83fd7b5a88a0b62571c73cd7f31145bb9`である。
01:01の観測では265297とsampling265287がともにRであり、要求node数の合計は2である。

## 2026-10-19 00:30 JST時点の更新

tile72 depolarizing・p*=.003のBAR解析265290はF/exit0/run_count1、実時間1時間19分39秒で終了した。
既存のcompletion検証を実行し、768 group・67,584行とsource/native/入力の照合を含む正式completionを受理した。
summary SHAは`29d2974f068fa41352e71478ca420c0f6d785137398416fe8e85e71ccf1bb79b`、completion SHAは`492d23c2cedb0b0f6b35cce6185d8ca1a5d23d83291094a7ddddedc1b657476d`である。
trace監査とWSSとの最終比較は引き続き未完了であり、低ノイズ校正全体の完了とは扱わない。
空いた枠へp*=.01の最終比較v2をqsubで投入し、job ID `265294.node-PRISM`を取得した。
投入receiptは`data_tile_validation_2026-10-17/low_final_case2_target0_execute_v2_receipt.json`、qsub応答stdoutのSHAは`ea52c42b57c5527b3a2b5c448459b9e1d272bd8dc3d88ac0d84e336bf6b6f6d4`である。
投入後のPBS照会で265294とp*=.001のsampling265287がともにRであり、要求node数の合計は2である。
265294は1 CPU・32 GiB・6時間の要求上限であり、6時間を完了予測とは扱わない。
次の空き枠ではcase2 target1の準備済みtrace監査capacityを優先し、265287終了後にcase2 target2のsampling終端検証と独自のanalysis capacity測定を進める。

## 2026-10-18 集約データの回収

完了済みcase2 target0のsampling計画・全67,584行・入力証拠・producer completionをlocalへ回収した。
4ファイル269,835,386 bytesについて、正式受理済みcompletionに記録されたSHAと転送後bytesを照合し、回収前後のPBS終端も一致した。
`data_tile_validation_2026-10-17/low_collection_case2_target0_evidence_v1/collection_verification.json` のSHAは `a44eb871f202477860ea9f6b828efcd5f67361804ecc927123da16dac6596aa0` である。
localの軽量census確認は7.21秒で完了し、352設定の各192 replicate、768 group、全67,584行、重複0、未知設定0を確認した。
行を除外せず、未取得・未定義・混合診断flagのboolean形状も保持している。
これは転送と行識別の検証で、数値統計の再計算、全元traceのlocal回収、WSS比較の完了ではない。
23:21のPBS照会では265287と265290がともにRであり、準備済みfinal v2の投入は空きnode待ちである。

## 2026-10-18 23:17 JST時点の更新

ホスト間照合修正版v2はLinuxでも82 passed・1.97秒を確認し、科学source85件とnative/import環境の前後一致を確認した。
別bundleへ隔離配置し、受理済み入力configのbundleとwrapper source/resolvedだけを変更して、metadata validation・prepare・preflightを完了した。
新control SHAは`a9fdc2285699611eaa6a7dcf8fec700ba5f8765773d9c298acb6b76fb759dee6`で、要求は1 CPU・32 GiB・6時間を維持する。
265287と265290で2nodeを使用中のため、v2のqsubはまだ行っていない。
実装・試験・配置helperの原bytesと18証拠参照は `local_orchestration_sources_v10/` に保存し、ZIPを含むhashを照合した。
詳細は `data_tile_validation_2026-10-17/low_final_cross_host_identity_acceptance_v2_ja.md` にある。
case2 target1のtrace監査capacityもprepare済みで、実投入は未実施である。

## 2026-10-18 23:12 JST時点の更新

tile72 depolarizing・p*=.01のcollection265284はF/exit0/run_count1、34分26秒で終了し、全768group・192 replicate・67,584行の正式completionを受理した。
続くWSS最終比較265288は4秒でF/exit1となり、準備時のファイル同一性照合で停止した。
execution intentも科学的成果物も生成されておらず、このjobから比較結果を得たとは扱わない。
短いqsub診断265289はF/exit0となり、141入力すべての差がホスト依存のdevice番号だけで、hash・target・inode・modeの一致と読み取り中の安定を確認した。
証拠は `data_tile_validation_2026-10-17/low_final_case2_target0_identity_failure_evidence_v2/collection.json` にある。
小仕様と再現テストを先に用意し、ホスト間照合だけを修正した別名v2の親wrapperで82テストが39.52秒で成功した。
旧source・失敗jobは保持し、Linux受入と新規bundleの準備を進めているが、修正版の本投入は未実施である。

p*=.003のcopy265286はF/exit0、15分50秒で終了し、対象自身のauthorityを使ってreadiness R0〜R2を新規作成した。
コピー実測944.843秒によるI/O予算を加え、BAR解析をqsub265290として投入した。
要求は96 CPU・50 GiB・96 workers・4時間30分で、解析と全trace監査・正式比較は未完了である。
p*=.001の本サンプリングはqsub265287で稼働中で、全192 replicate・92,160 sample・192 anchorの固定計画を維持した。
265287と265290の最大2要求nodeをqsub gateで維持する。
残る9条件の分割本計算26jobと、全低noise独立計時は未投入である。
サブエージェントは利用上限で停止しており、親が修正と投入管理を続行している。

## 2026-10-18 22:32 JST時点の更新

case2・target1のanalysis capacity265285はF/exit0/run_count1、PBS wall5分12秒で終了した。
固定job用のmetadata observerを既存処理から座標・実投入pinsだけ変更して用意し、16 passed・3.07秒の受入後に、全8group・88設定・各group 3,264診断・35成果物26,625 bytesを照合した。
回収binding SHAは`289d1a29b1785f03fb0f9a8ad5d645d45ab0a56af5f39783a89402f4cbd76c58`、measured profile SHAは`a02cf249bcbac2e03509f0ebe93e4497128e5a1c7d4f75473af159505183c0b4`である。
本解析の基礎要求は96 workers・50 GiB・2時間の1 partitionで、全768groupを保持し、copy実測によるI/O余裕はまだ含まない。
これは合成配列の資源計測で、混合・精度・被覆の結果ではない。

対象自身のsamplingとcapacityのF0証拠6件を結ぶ `low_noise_case2_target1_authority_v1.json` を作成し、既存authority validatorを通した。
SHAは`57259d7fdeefa23ac308631c37574ee3bbd15d64cbe8a797e85aad052c6eff87`である。
新T1入口による実prepare・preflightが成功し、検証付きcopyをqsub265286として投入した。
copy plan SHAは`5eb00807a247bd3e3a6b7ce6980ad6299efb5ac466f8dc315062fca6ce32cca8`、script SHAは`614675d834c0b4e7e3411525197cf16ae5cb819ec3140ca773a41551f121cc79`、実投入stdout SHAは`e1645b577ba503cca489dd24715383e375bdc556d202cb8c43adf79379e62519`である。
要求は1 node・1 CPU・8 GiB・24時間の初回上限で、既存要求1nodeをqsub直前に確認した。
p*=.01のcollection265284と合わせ最大2要求nodeを維持し、copy実F0後にT1 readinessを新規作成する。
両条件の正式WSS比較と全低noise校正・独立計時は未完了である。

## 2026-10-18 22:25 JST時点の更新

tile72 depolarizing・p*=.003の本計算265281はF/exit0/run_count1、PBS wall2時間45分02秒で終了した。
既存metadata observerによる独立した2観測を照合し、全79,872 sample・192 anchorのsummary census、失敗0、保存native・receipt/script/manifest/PBSの対応を受理した。
保存phase wallはanchor37.004秒、sample9859.880秒であり、copy・BAR解析・監査費用は含まない。
証拠`low_sampling_production_2_1_terminal_metadata_verification_v1.json`のSHAは`c23e9310e3b6f8506a91816570fa1a0e4f843d3350099216870115395e3d4298`、PBS stability証拠のSHAは`4d7abaf7a10d20cdd6abe15bbb3ec170dea05bc5c77abe873bd78bf94447e1cb`である。
これはsummaryと各phase最大3件のJSON metadataの確認で、全payload監査・再復号・混合・精度・被覆を代替しない。

空いた枠へ同条件のanalysis capacityをqsub265285として投入した。
要求は1 node・96 CPU・340 GiB・8 workers・24時間の初回上限で、合成データによる資源計測である。
実投入stdout SHAは`da552d91ece44f832b11da650b3ebe8c8358ec7dbcfd1623079701de2af1ce8e`、local receipt SHAは`1c0ea600ba3dc388243cebf30963b7486d18c0a259da3a7d3504650a55705aac`である。
p*=.01のcollection265284と合わせ最大2要求nodeを既存gateで維持した。

T1/T2入口の親レビューを `data_tile_validation_2026-10-17/low_noise_case2_entries_parent_review_v1_ja.md` に保存し、軽量受入と静的点検では新たなblocking指摘はなかった。
実target authorityと接続はcapacity受理後に行う。
p*=.01の正式WSS比較configを作るmetadata処理は作成・構文確認・source保存済みで、collection終端待ちのため未実行である。
手順と資源予算の根拠は `data_tile_validation_2026-10-17/low_final_case2_target0_config_assembly_plan_v1_ja.md` にある。

## 2026-10-18 22:13 JST時点の更新

tile72 depolarizing・p*=.01のBAR解析265278はF/exit0/run_count1、PBS wall1時間00分52秒で終了した。
親が正式completionを受理し、全768group・67,584行とsource/native・prepared/receiptの対応を確認した。
summary SHAは`04468e1bc82108348d299109293e86c32cab877bf7c3c5ad1fd74d167eeab5c9`、completion SHAは`a4a77dfefe2bd4e69486e5ffa3b4b0d11cee9ae5866818f8fa23ebb6d387228e`である。
既に受理した全trace監査265280と結合するcollectionをqsub265284として投入した。
要求は1 node・1 CPU・32 GiB・24時間の初回上限で、完了予測ではない。
実投入stdout SHAは`69aa999cb7f420fa0da4e95017b4c827ada8d58f878f0bd3971cf6f5bd859624`、remote receipt SHAは`d89fc9a11b29939d227140697cde271db8f92266f24e8240ea7447f202f95e2f`である。
p*=.003の本計算265281との最大2要求ノードを既存qsub gateで維持した。
collection終端・実測資源の確認とWSS正式比較は未完了である。

T1/T2後段接続は実装とWindowsの所有者143件・別受入150件が通過したが、最終レビューと実環境での接続は未完了である。
サブエージェントが利用上限で停止したため、残るレビューとクラスタ進行は親が継続する。
最終WSS処理の追加hash読込みと固定native fixture検査を静的に確認し、`data_tile_validation_2026-10-17/low_final_case2_target0_io_passes_parent_review_v1_ja.md`へ記録した。
全低noise校正・独立計時・日本語最終報告の統合は引き続き未完了である。

## 2026-10-18 19:38 JST時点の更新

case2・target0の全trace監査265280はF/exit0/run_count1、PBS wall6分14秒で終了した。
親が正式completionを一度実行し、全768group・61,440予定trace、sampling失敗0・監査失敗group0、native/source・prepared/receipt・PBSとの対応を受理した。
summary SHAは`a43f0b1b79e404265b453d869a3ec3de14aacb391de440c56143373bc4833e54`、completion SHAは`de9bd333cf89acfd097c96dfb4cec7384619e55fc79b043935cf482967a0f0b8`である。
全物理状態の再生成や全trajectoryの再復号を行ったという意味ではなく、既存のcompact trace・保存checkpoint監査契約の成功である。
BAR解析265278は直近の観測でR/run_count1であり、解析終端後のcollection・WSS比較はまだ未実施である。

空きノードへtile72 depolarizing・p*=.003の本計算をqsub265281として投入した。
固定192 replicate、79,872 sample taskと192 anchorsを保持し、要求は1 node・96 CPU・32 GiB・10時間上限である。
manifest SHAは`03eb882ab5073709b3817a772426b65d9238e4743f0d11ce9d249deaa1ee0003`、実投入stdout SHAは`487f4aad1f07d345042954dd95efc95aa97273ec18969965018501178bb8ee3d`である。
既存入口の重複拒否・共有lock・qsub直前の最大2ノードgateを使い、原sampling sourceと科学設定は変更していない。
残り10条件の本計算は未投入で、全低noise校正と独立計時は未完了である。

T1/T2後段の最小接続仕様は`tile_low_noise_case2_t1_t2_staging_entry_spec_2026-10-18_ja.md`に保存し、先行受入から実装を進めている。
最初の低noise結果を正式WSS reportへ接続する証拠・費用の手順は`data_tile_validation_2026-10-17/low_final_case2_target0_config_handoff_v1_ja.md`にあり、未取得のcollection completionや費用を仮置きしない。

## 2026-10-18 19:29 JST時点の更新

case2・target0の全trace監査を、実測capacityに基づく96 CPU・69 GiB・96 workers・2時間30分の要求でqsub265280として投入した。
対象は全192 replicate・768groupで、短いcapacityを本監査の代用にしない。
要求時間はbaseline30分にcopy実測由来のI/O予算2時間を加えた上限で、96 workerでのI/O競合や完了時刻を保証しない。
prepared SHAは`bb5ca38fea7dbdf1a6695598444579719d3cd3a44d1d1721c1d06f09f86064ef`、実投入stdout SHAは`30b2af31833eebd40997746474b0546d665f11840e254d2180128163676ee8fe`である。
R6のSHAは`91c98cdee35268db9d0e7ceed3c8463b5a6cff3ae234683292fdfb6d3c8fee46`で、analysisとtrace-capacity/fullのprepared・submitted pinを保持する。
投入直前gateは既存要求1ノードを確認し、新規1ノードと合わせ最大2ノードを維持した。
analysis265278と全監査265280のF0・正式completion受理後に、既存collection処理へ進む。

## 2026-10-18 19:26 JST時点の更新

trace監査capacity265279はF/exit0/run_count1、PBS wall4分50秒で終了した。
親が正式completionを一度実行し、全8group・640予定traceと失敗0、native/source・prepared/receipt・PBSとの結合を受理した。
summary SHAは`fe0ad020574e37d1c470ed192bb833f0dad6a9c49022de5388b780696927b854`、completion SHAは`6cf616f4db89284ed99166cc131bb30347accea3eb32c498d31b9cb22453e8a3`である。
全768groupのtrace監査を実測資源に基づきprepare中で、analysis265278は直近の観測でR/run_count1だった。

終端からcollectionまでの既存CLI・依存関係を`data_tile_validation_2026-10-17/low_noise_staged_terminal_collection_handoff_v1_ja.md`に整理した。
既存wrapperで後処理でき、新collectorを追加する必要はない。
残る11本計算と10 synthetic analysis capacityの未投入root/index・資源・依存関係は`data_tile_validation_2026-10-17/low_noise_pending_dispatch_ledger_v1_ja.md`に保存した。
goalの15要件と一次証拠・限界を`data_tile_validation_2026-10-17/goal_scope_gap_audit_v1_ja.md`で点検し、全52リンクを確認した。
全体の未完了項目は低noise本校正・独立計時と最終報告の統合であり、未証明の理論事項は適用限界として保持する。

## 2026-10-18 19:21 JST時点の更新

主8条件の正式精度・費用比較の科学的レビューを完了し、blocking指摘はなかった。
全8条件でMC/BAR各192点・区間、失敗0を確認し、既存MC判定との一致、有限reference区間全域の精度gate、3条件だけの費用比と他5条件のnullを維持した。
レビュー・全8行表・平均task wall/CPU・被覆表は`data_tile_validation_2026-10-17/main_timing_scientific_review_v1/`に保存し、主報告第6節へ統合した。
review.jsonのSHAは`1b7d713c297fe0d9421c5567005790d9a3d995fa0fb054517cb98307e4ebe12f`である。
短い計時設定のBAR点reference被覆は158〜172/192で、精度gate通過と名目95%被覆を区別する。
実行host差は未補正であり、独立計時の混合診断は未取得で、保存placeholderを実測flag数に読み替えない。
主4条件の校正・混合比較・独立計時評価は完了し、残る科学計算は低noise本校正・独立計時である。

最新の軽量観測では、解析265278とtrace監査capacity265279はそれぞれR/run_count1で、要求資源・prepared/receipt・source/native pinsとの対応を確認した。
終端前のphase completion操作は行わず、他jobを追加投入していない。
次の本計算候補case2・target1は既存準備8ファイル・capacity・source固定値とlocal未投入を確認済みで、空きslotと直前gateを確認してから既存qsub入口を使用する。

## 2026-10-18 19:18 JST時点の更新

主8条件の正式report265277の15成果物・5,376,948 bytesを回収し、全転送hash、各192 replicate、有限reference gateと時間比null規則の照合を完了した。
回収証拠は`data_tile_validation_2026-10-17/main_timing_report_result_evidence_v1/collection_verification.json`（SHA `5d0b56050ba65a772e17a327a0ee74bfc0bfed92ab9f5e7ae7c9dbc9700ecb7d`）に保存した。
直接MCは目標内4・超過2・reference依存2、BARは目標内6・超過1・reference依存1で、両手法が目標内だった3条件だけ時間比を表示する。
3条件の平均task wallのMC/BAR比は0.0208〜0.0455で、今回の環境・固定候補ではMCの方が短時間だった。
残り5条件の比はnullを維持し、科学的解釈の独立レビューを進めている。

case2・target0のtrace監査capacityもqsub265279として投入した。
要求は1 node・96 CPU・340 GiB・8 workers・24時間の初回上限で、完了予測ではない。
実投入stdout SHAは`65b4d18c7ef6ea40c1a41b5c8164e24d049ba933ed26cb0b2295e552767dd5a5`である。
analysis265278とtrace-capacity265279のsubmitted記録を含むR4のSHAは`0b226e62ee5c3f9188d43547811aa0c8e49eae81e2a55406e46c35bbb57627c2`である。
両jobは同じsealed rawをread-onlyで共有し、別出力先を使うが、共有I/Oの競合による時間変動はあり得る。
qsub直前の既存gateで待機を含め最大2ノードを維持し、同時に追加jobは投入していない。

## 2026-10-18 19:15 JST時点の更新

主8条件の精度・計時report265277はF/exit0/run_count1、PBS wall7分41秒で終了した。
成果物の回収と科学的判定の独立レビューは進行中であり、正常終了だけで精度達成とは判定しない。
低noiseのcase0・target0 synthetic analysis capacity265276もF/exit0/run_count1で終了し、35小成果物の回収・hash検証を完了した。
全8groupで88設定・1,536診断を確認し、既存資源式の候補は96 workers・226 GiB・6時間・1partitionで、stagingと追加hash検査の費用は別途必要である。
証拠は`data_tile_validation_2026-10-17/low_analysis_capacity_case0_target0_terminal_v1/collection_binding.json`に保存した。

新readiness builder v3は独立56テストが成功し、固定7driverの順序だけを再現して送信program全bytesの一致検査を維持した。
既存prepareを再実行せずR1を作成し、dry-run後にcase2・target0の低noise解析をqsub265278として投入した。
要求は1 node・96 CPU・48 GiB・96 workers・3時間30分で、実投入stdout SHAは`aef0cb8da1806a3e72211c94c33a787893cccbddbb6be4bf58894ae3fe7ef989`である。
submitted記録を含むR2のSHAは`f91fe07ce07255227f5be2c69adf3ed1a4c717ada3f049d62bbd7a3c13e66bf9`である。
trace監査capacityはこのR2から準備中で、元のsealed rawをread-onlyで共有し、解析とは別の出力先を使う。
全低noise本校正・独立計時・最終報告は引き続き未完了である。

## 2026-10-18 19:04 JST時点の更新

BAR本計時の全4case・1,536taskと全保存chainの独立照合が完了した。
case3の独立proof SHAは`b2d0879dcdd22a06d786df575de5fe5b50d48252e69013607ca1f1c897608477`で、全caseの失敗・区間未取得・再利用は0だった。
実28pinを用いた正式config（SHA `818550c8bd201eabfa3672cb8c630582d060f879fb62dbce60200fc55ef143ac`）で親がmetadata-only prepareを実行し、6準備filesと元5jobのfresh F/exit0/run_count1・controller終了を照合した。
親の正式readiness受理SHAは`7fda78050e4355d4cb1b61f721dda54bb77f1eb375d74db1405c78ed293d3406`で、preflight後に精度・時間比reportをqsubで265277として投入した。
要求は1 node・1 CPU・16 GiB・2時間で、実投入stdout SHAは`4e3ffa418e761220547cc9ac99af044e03f75b85fe1ee53bc6d0ffb627fe6ebb`である。
19:04の親qstatでreport265277とsynthetic capacity265276の2ジョブ稼働を確認した。
正常終了や全区間取得を達成精度へ読み替えず、全8条件の正式判定はreport終端と回収を待つ。

解析用copy265275はF/exit0/run_count1、PBS wall12分51秒で終了し、2回のmetadata観測でsummary・seal・元265259との結合を確認した。
終端証拠は`data_tile_validation_2026-10-17/low_staging_copy_2_0_terminal_metadata_v2.json`（SHA `52904eec35698bc20cdfa64db4351b0addefe240c4299cf3dadcf275358ebb38`）に保存した。
親は正式R0（SHA `8e971b11437e2a381b10e43fe17bef5207502251a10e4c32bf631de46f3bae20`）を作成し、analysis0のprepareも成功した。
解析要求は96 CPU・48 GiB・96 workers・3時間30分であり、copyの実費用に基づく追加hash時間を含む上限として準備したが、まだqsubしていない。
prepared SHAは`76f54fbf1c09d3e60f37271e96254f6f72db736e9d788a03424b16e0d2f79ad0`である。
その準備記録をreadinessへ追加する段階で、別processのset反復による固定7driverの辞書順差を検出し、local検査で停止した。
payload全値と他のASTは一致し、当該7件の順だけを再現すると送信program全LF bytesが一致することを確認した。
実R0・prepare記録・remote planを保持し、限定した順序再現と全bytes照合を行う新builder v3を小仕様・受入・独立レビューの順で準備している。
再prepare・解析qsub・R1の作成はこの停止後に行っていない。

## 2026-10-18 18:57 JST時点の更新

主4条件の混合診断summary比較を実行し、元保存field全20,160cohortと出力の数値セル1,705,968件の照合が成功した。
全20,160cohortは診断19,008とsector1,152を含み、各cohortの分母192とchain配列の192×chainsを区別する。
新しいACF・BAR・decoder再計算や巨大JSONLの再走査は行っていない。
成果物は`data_tile_validation_2026-10-17/mixing_comparison_four_case_v1/`に保存し、主報告第5節へ主要所見と全表のリンクを追加した。
固定最大chain・burn6000・最長保存長の全kernel/initでは、tile72 bit-flipは全観測量flag0、tile72 depolarizingはweight/Bennettが0〜1でもlogical bitが最大154/192だった。
tile288 bit-flipはweight/fine Bennettが192/192、tile288 depolarizingはweight/両ladder Bennettが192/192で、個別観測量の周辺件数とBARのseed単位flagを区別する。

BAR本計時case3は全384task・1,167ファイルの初回回収とhash照合まで完了し、失敗・区間未取得・再利用は0、phase時間3361.570382秒だった。
全chainの固定prior・RNG・保存形状等の独立照合を実施中で、正式時間比の集計はまだ行っていない。
copy265275とcapacity265276は既定監視で稼働を継続している。

## 2026-10-18 18:49 JST時点の更新

主ノイズBAR本計時case3の265268は18:48:02の既定観測でF/exit0/run_count1、PBS wall56分4秒を確認した。
全384taskの回収と独立照合を実施中であり、正常終了から達成精度や時間比を補完しない。
実独立proofが揃った後に全4caseの正式configを作成し、全8条件の精度・費用reportへ進む。

空いた枠へlow-noise analysis capacityのcase0 target0をqsubで265276として投入した。
元prepared manifestは`5017b9b7254e06d63f5b73c07a022c781b9020d5d0fbb4297552acd0a20c0b3f`で、親の実stdout SHAは`06fb19c8f3cded58c713813b1e56ae4567c9c7638315ebbc90d24aee6b229e90`である。
要求は1 node・96 CPU・340 GiB・24時間の初回上限、8 workersのsynthetic解析計測であり、科学的精度のデータには混ぜない。
18:49の親qstatでcopy265275とcapacity265276の2ジョブ稼働を確認した。
残り10条件のanalysis capacityは未投入で、case2 target0は既に受理済みである。

## 2026-10-18 18:46 JST時点の更新

主4caseの全cohort混合診断は全てF/exit0となり、各768group・全48ファイルの回収とremote前後・localの全hash照合を完了した。
合計3,072group・3,870,720行の保存診断を保持し、回収索引は`data_tile_validation_2026-10-17/mixing_full_collection_index_v1.json`（SHA `6d0aeb23a3a339dc656daab69651cdef25603546adbeae1ea016a4b013ed2dcd`）に保存した。
case3のPBS wallは2分15秒であり、全4caseの後処理時間をMCMC本計算の時間へ読み替えない。
未定義診断も保持したsummary比較reportを別途受入・独立レビュー中で、全JSONLやACFを再計算したとは扱わない。

copy・phase・readinessの新v2三入口は独立142件の受入と実クラスタ上のbindings-only検査を通過した。
旧三入口とv1失敗証拠は不変で、実wheel配置・28package files・7driver・元manifest・Pythonの対応を確認した。
証拠は`data_tile_validation_2026-10-17/low_noise_staging_copy_v2_independent_acceptance_v1.json`（SHA `15365aad2a35291732aafa0802cfa1bc90d63fee273e62470c11692b732252a8`）である。
親は新v2のprepare・preflight・executeを順に実行し、copyをqsubで265275として投入した。
prepare stdout SHAは`27a4fcf61356455aa7585b9bbe8da9a6f49af240456e9fc934abd145fa308c19`、実投入receipt SHAは`db890c07cadc2e8240c35199bf1c44047b45d131c65fc1ced1e99c2111e9243b`である。
copy要求は1 node・1 CPU・8 GiB・24時間の初回上限であり、24時間を完了予測としない。
18:46の親qstatでcopy265275とBAR本計時265268の2ジョブ稼働を確認した。
copyの実終端とsealを確認してから解析・trace監査の正式readinessを作成する。

## 2026-10-18 18:40 JST時点の更新

親の18:39:59 qstatで混合診断case2の265273はF/exit0、PBS wall3分23秒を確認した。
case2の正式回収は担当agentが継続し、親は最後のcase3をqsubで265274として投入した。
case3も1 node・1 CPU・4 GiB・1時間30分で、BAR本計時265268と合わせて最大2ノードを維持する。
全4caseの混合診断は投入済みであり、現時点でcase0・1は回収照合済み、case2は回収待ち、case3は実行開始段階である。
新しいcopy v2三入口は作者側142件の受入が成功し、独立差分レビュー中で、実prepareとcopy qsubはまだ行っていない。

## 2026-10-18 18:38 JST時点の更新

全cohort混合診断のcase0（265271、PBS wall2分22秒）とcase1（265272、1分30秒）はF/exit0で終了し、各12ファイルの回収とremote前後・localの全hash照合を完了した。
両caseとも768group・192replicate、保存診断はcase0が875,520行、case1が617,472行で、inventory側のundefinedは2行・290行だった。
nonfinite・stored missing fields・failed samplingはいずれも0で、これらの件数は診断の収束保証を意味しない。
証拠は`data_tile_validation_2026-10-17/mixing_execution_full_case0_evidence_v1/verification.json`（SHA `35a1d9353c1d0b467b1bb8f86fd51060b4aa8c99402e443c989dd03b5daab926`）とcase1の同名ファイル（SHA `cd788a7b5289b15d9b5330fd06ba294d4963bb1d91151185df6288b11fded7cb`）に保存した。
case2を265273としてqsub投入し、18:37:55の親qstatでBAR本計時265268とともに稼働中、計2ノードを確認した。
全4caseの受理後に保存summaryだけを使う混合診断比較を作成し、新しいACF・BAR再計算や巨大JSONLの再走査は追加しない。

copy prepare停止の原因は、元sampling bundleがwheel配布なのにsource directoryを仮定したことだった。
実installed packageと元配布manifestの一致、remote copy rootとdestinationが未作成であることを読み取り専用で確認した。
旧版と失敗記録を保持し、copy・後続phase・readinessの新v2入口について小仕様と受入を進めている。
残11 analysis capacityと残2 single productionの入口も実配置を点検し、現在のpath/hash不一致はなく、既存invocationは未消費である。
点検記録は`data_tile_validation_2026-10-17/pending_low_entry_topology_audit_v1_ja.md`に保存した。

低noise selector親入口は独立Linux配置で42件、最終WSS比較report親入口は別配置で70件の軽量受入が成功した。
既存source・実origin・Python・native binary hashを前後照合したが、正式12入力・資源確定・本番prepare/qsub・本番raw読取は未実施である。
証拠は`data_tile_validation_2026-10-17/low_noise_timing_selector_parent_source_binding_v2.json`と`low_noise_final_reference_parent_source_binding_v1.json`に保存した。

## 2026-10-18 18:31 JST時点の更新

低noise case2 target0の265259はF/exit0で終了し、PBS実行時間は2時間25分11秒だった。
sample61,440件とanchor192件の全summary task census、欠落・重複なし、failed0、native・receipt・script・PBS hostの結合を2回のmetadata観測で確認した。
証拠は`data_tile_validation_2026-10-17/low_sampling_production_2_0_terminal_metadata_verification_v1.json`（SHA `8edc47712b1b321b4821c52aaab5c4ec420c28c66a97ddeec54e59d195a4ae26`）に保存した。
これは全raw payloadの再監査や混合・精度の確認ではなく、後続copyへ進むための終端確認である。

親がcopy wrapperのprepareを実行したところ、source照合が`20261018-tile-low-noise-v2/src/mcmc4qec/__init__.py`の不存在を検出し、helper importとremote prepareより前に停止した。
当該copyのqsubは未実施で、v1 invocationとstderrを保持し、実配置とsource照合表の対応を修正するため調査中である。
停止を成功として扱わず、同じinvocationを再実行しない。

独立に実行可能な主ノイズcase0の全cohort混合診断を、親がqsubで265271として投入した。
既存traceに対する全768groupの後処理であり、新たなMCMC samplingではない。
要求は1 node・1 CPU・4 GiB・1時間30分で、18:31のqstatで265271とBAR本計時case3の265268の2ジョブが稼働していることを確認した。
終端後に全出力の回収・照合を行う。

低noise最終WSS比較report入口は、今回のstaged3条件とpartitioned9条件について独立レビューを完了した。
旧single入力は必要なproducer completionがないため明示拒否し、未対応と記載した。
証拠は`data_tile_validation_2026-10-17/low_noise_final_reference_parent_independent_review_v3.json`で、正式入力・資源確定・実report qsubは未実施である。
主ノイズBAR case1・2の独立証拠8ファイルを新しい外部保存先へ配置し、全転送SHAと既存v2入力の不変を確認した。
正式な全8条件の時間比reportはcase3の独立受理後に作成する。

## 2026-10-18 18:22 JST時点の更新

低noise265259は18:18:36の既定観測で57,120/61,440 sample marker（93.0%）、anchor192/192成功であり、summaryとPBS終端は未確認である。
親の18:22 qstatでも265259と主ノイズ本計時case3の265268は稼働中であり、計2ノードで継続する。
元samplingの終端と全task確認後にcopyへ進み、稼働中のsourceを解析用に封印しない。

readiness builderは独立レビューの2指摘を修正し、40件と独立再現2件が成功した。
受理source SHAは`9021c0d20ff3a34d60f54b15a56f987b0df670bb918de3dffc90a90e0d77a092`で、証拠は`data_tile_validation_2026-10-17/low_noise_staged_readiness_builder_independent_acceptance_v1.json`に保存した。
低noise selector親wrapperもimport前照合・実PBS費用結合・qsub部分応答保存の3指摘を修正し、独立42件が成功した。
受理source SHAは`70554a13dca33f7ec12dab4e975dc0a1fd591193effac474661a8bb0b53b1173`で、証拠は`data_tile_validation_2026-10-17/low_noise_timing_selector_parent_independent_review_v2.json`に保存した。
両入口の正式入力作成・remote実行・qsubは未実施であり、最終WSS比較report入口は別途レビュー指摘の修正中である。

## 2026-10-18 18:15 JST時点の更新

265259と265268は親のqstat確認で稼働中であり、2ノードを維持している。
低noise265259は18:06:25の既定観測で51,760/61,440 sample marker、anchor192/192成功だった。
主ノイズ本計時case3は18:07:42の軽量観測で192/384 marker、summary未生成で、終了後に全結果を回収する。

完了済み主4caseの固定ZH/rejection条件について、相対RMSEとMC点基準の被覆を比較するPNG/SVGを作成し、中間報告へ組み込んだ。
全12表示行を受理済みsummaryへ結び、19入力hashの不変、CSV/JSON一致、画像の目視を確認した。
数値、source/環境、再生成script、日本語captionは`data_tile_validation_2026-10-17/figures_main_calibration_v1/`に保存した。
有限reference区間の全域包含・交差は図の点とは別の数値として保持し、95%の名目線を被覆保証と扱わない。

低noise selector親wrapperとreadiness builderは独立レビューの改変検出・実費用結合の指摘を補強中で、正式入力・実qsubは未実施である。
低noiseの最終WSS比較report用親入口も、保存監査と既存数値関数を結ぶ仕様に従って受入・実装を進めている。

## 2026-10-18 18:04 JST時点の更新

主ノイズ本計時case0・case1・case2は全結果の独立照合まで完了し、case3の265268と低noise265259は稼働を継続している。
親の18:04 qstatで265259と265268の2ノードのみを確認した。
精度と同精度時間比の正式集計はcase3の受理後に行い、正常終了や区間取得で精度達成を代替しない。

single-PBS copy後の解析・trace監査・collection用親wrapperは独立64件を通過し、source SHA `378cca64cec2852c61ffa36f0ed79654d4cb01e4447d74a48475831b14b5e025`で固定した。
独立証拠は`data_tile_validation_2026-10-17/low_noise_staged_phase_wrapper_independent_acceptance_v1.json`で、実copy readiness・remote prepare・qsubは未実施である。
元samplingとcopyの実終端後に受理済みsource・PBS証拠からreadinessを作る手順を整えている。

低noise selectorの実呼出を確認し、保存ACFのshape、保存rows、auditとcurrent raw hashを照合するが、BAR・ACF・trace監査を全再実行する経路ではないと確認した。
小native fixtureの再実行と、保存point・interval・WSS countからの算術再集計は行う。
新readerの追加は不要とし、全12 final/collectionとstaged copy/hashの実費用を根拠に資源を確定するまでprepare/executeを拒否する親入口の仕様を承認した。
1 CPU・340 GiB・24時間は現時点では政策上限候補であり、実測済み完走予測ではない。
第4段階報告adapterは独立61件で承認済みで、既存実pathを保つ別Linux v2配置も61件・10.77秒・skipなしで完了した。
既存source/packageと実import先85件を照合し、固定native profileとの差分は0で、`data_tile_validation_2026-10-17/low_noise_timing_stage4_source_binding_v2.json`へ保存した。
この検証は軽量fixtureと環境照合であり、正式input・本番全raw走査・qsubは未実施である。
主ノイズ報告の投入wrapperは独立50件に通過した後、運用手順の確認でWindows側がremote POSIX絶対pathを拒否する問題を発見した。
旧受入を保持し、remote側だけのpath検査を修正して実`/home/...`形状の受入を追加し、独立55件で修正版を承認した。
現受理sourceは`d704877778ae0c37edb376be22bdd3399657c37bac0b2d11d476f709452ad8a5`で、手順は`tile_timing_report_submission_runbook_2026-10-18_ja.md`に保存した。
正式request・remote preflight・qsubはcase3受理後に行うため未実施である。
`output/`にある凍結済み親helperは、元pathを変更せずデータ文書側へsnapshotと索引を保存している。
過去投入時のlocal helper SHAが残っていないものは、現在の保存bytesと過去一致未確認を区別し、実投入の根拠を保存済みremote script・入力・receiptへ限定する。
再現snapshotの初版は`data_tile_validation_2026-10-17/local_orchestration_sources_v1/index.json`に保存し、20 snapshotと既存11参照を索引化した。
主ノイズ報告wrapper修正版は`data_tile_validation_2026-10-17/local_orchestration_sources_v2_main_report/index.json`へ別差分として保存し、旧版と初版索引を変更していない。
低noiseのstaged collectionは保存rowsとaudit evidenceまでで、selectorが要求する最終WSS比較reportを作る入口が不足していた。
single/partitioned/stagedのreaderと保存済み16条件reference auditを結合し、既存compare_rowsで最終reportを作る最小親PBS仕様を承認し、受入・実装へ進めている。

## 2026-10-18 17:52 JST時点の更新

主ノイズ独立BAR本計時のcase1は全384 task・6,144 chainを独立照合し、失敗・区間未取得・再利用は0だった。
phase時間は1,407.972879秒、PBS wallは23分30秒で、証拠は`data_tile_validation_2026-10-17/bar_main_case1_evidence_v1/independent_payload_verification.json`に保存した。
case2の265267もF・exit 0・run_count 1、PBS wall3分35秒で終了し、全384 task・13,824 chainの回収と独立照合を完了した。
phase時間は212.362993秒、失敗・区間未取得・再利用は0で、証拠は`data_tile_validation_2026-10-17/bar_main_case2_evidence_v1/independent_payload_verification.json`に保存した。
case3は実preflightと保存capacityの照合後、265268としてqsubした。
要求は1 node・96 CPU・32 GiB・2時間30分、manifestは`62bae0cf20bd96d2d59426e6e26281c13d3e14ced74d8b59b5c6e0cc181e59bf`である。
親receiptを保存し、17:51:55の開始時source/native/runtime・実PBS資源の結合を確認して監視を開始した。
低noise265259は17:51:11時点でsample marker45,040/61,440、anchor192/192成功、summary未生成である。

低noise報告adapterの独立レビューでは、予定分母と実割当の区別、区間なしMC点の保持、checkpoint検査範囲の表示、出力親pathの途中変更拒否を補強した。
作成者の修正版61件と独立61件は成功し、全4指摘を解消した。
独立受入は`data_tile_validation_2026-10-17/low_noise_timing_evaluation_report_independent_review_v2.json`に保存し、Linux配置と本番評価は未実施である。
single-PBS copy後の汎用親wrapperも独立レビューの改変検出・controller確認の指摘を修正中で、まだ本番には使っていない。
主ノイズ正式報告の親投入入口は小仕様を承認し、受入・実装・独立レビューへ進めている。
低noise selectorの投入仕様は、全12条件の既存readerが要求する読取・再計算費用を確認してから資源方針を確定する。

## 2026-10-18 17:45 JST時点の更新

tile288 bit-flipの独立BAR本計時265266はF・exit 0・run_count 1で終端し、PBS wallは23分30秒だった。
全384 taskの回収・独立照合は進行中で、達成精度と速度比の正式集計はまだ行っていない。
空いた枠でtile72 depolarizingの本計時case2を実preflight後、265267としてqsubした。
親の保存receiptと実qstatで96 CPU・32 GiB・30分の要求と稼働を確認し、265259と合わせて2ノードを維持している。
case2のmanifestは`d572c9b2fd30014a1090c65534d52faf326b6f09b3be43d2d84c4502ef8ee79a`である。
case3本計時は準備済み・未投入であり、case2終端後の空き枠で進める。

低noise計時runner/submitterの最終独立レビューを承認し、別Linux配置へ進んだ。
初回配置v1は既存staging moduleのaliasとresolved pathの差を検出して受入前に停止し、元bytesの変更はなかった。
失敗証拠と既存bundleを保持し、両pathを固定した新v2配置でLinuxの軽量受入70件を完了した。
実source closure 54件と既存core/nativeの前後一致、固定native profileとの一致を確認し、`data_tile_validation_2026-10-17/low_noise_timing_stage3_deployment_v2.json`へ保存した。
この配置では正式selection・科学manifest・全数census・qsubは行っていない。
新旧seed監査入口も別Linux rootへ配置し、26件と独立2件の受入、55 moduleと既存入力・runtime/nativeの前後一致を確認した。
証拠は`data_tile_validation_2026-10-17/low_noise_timing_census_bridge_deployment_v1.json`に保存し、旧56 namespaceの監査を再実行したものでも新stageの本番監査を完了したものでもない。
低noise計時の報告adapterは53件の作成者受入を通過し、独立レビュー中である。
中間報告では192主分母と96層別、有限referenceの被覆、共有traceによる非独立性、正常終了と精度達成を区別する記述を整えた。

## 2026-10-18 17:39 JST時点の更新

BAR計時capacityは全4caseの独立payload照合まで完了し、各192 taskの点推定と区間を取得した。
本計時case0は全384 taskを回収・照合済みで、case1の265266は実行中、case2・case3は準備済みで未投入である。
親のqstat確認では265259と265266の2ジョブのみが稼働し、queuedを含む最大2ノードを維持している。
265259は17:32:55時点でsample marker36,960/61,440、anchor192件成功であり、本計算の終端検証はまだ行っていない。

低noise独立計時の新旧seed監査入口は独立受入26件と追加2件を通過し、lock所有確認とintent保存直後の最終投入条件を補強した。
小fixtureから正式readerへの接続を確認したが、本番selection・pilot・全数census・qsubは未実施である。
低noise計時runnerは独立66件を通過し、submitterの投入直前検査も追加10件で確認して全指摘を解消した。
最終受入証拠は`data_tile_validation_2026-10-17/low_noise_timing_stage3_independent_review_v3.json`であり、実qsubや本番科学計測の成功を示すものではない。
本計算開始時のcapacity payload全照合と、prepare時に保存済み照合証拠だけを読む処理を区別する。
第4段階の報告adapterは実装中であり、既存stage2の実import先を維持したrunner・監査入口の別Linux配置を順に進める。

単一PBS計算のcopy後に使う親用wrapperの小仕様を承認し、受入・実装・独立レビューを並行して進める。
実copyと後段の解析・trace監査・collectionは、265259の正常終端と実copy証拠を待つ。
collectionの1 CPU・32 GiB・24時間は初回の資源上限であり、完了予測や実測済み費用として扱わない。

## 2026-10-18 17:23 JST時点の更新

case3のBAR計時capacity265265はF・exit 0、PBS wall28分03秒で終了した。
全192 taskが点推定・区間を取得し、失敗・未取得・再利用は0、全591ファイルの回収とhash照合を完了した。
全chainの独立payload照合とmain case3の準備は進行中である。
空いた枠でcase1本計時の実preflightを通し、265266としてqsubした。
source/native・親receipt・実PBS資源96 CPU/32 GiB/1時間の開始時結合を確認し、265259と合わせて2ノード稼働を維持している。
265259は17:20時点でsample marker31,591/61,440、anchor192件成功であり、sample summaryは未生成だった。

主ノイズ正式報告adapterの別Linux v2配置は35件に通過し、実MCとmain case0のmetadataによるprepare接続も確認した。
正式4caseの集計は残りmain結果を待ち、1 CPU・16 GiB・2時間の後処理要求を準備したが、正式prepare・qsubは未実施である。
親の独立受入で報告request helper 7件と全混合診断collector 18件に通過し、`data_tile_validation_2026-10-17/parent_report_collection_review_v1.json`へ証拠を保存した。
全混合診断4caseは準備済み・未投入で、collectorは全JSONLの転送とhash照合を行うが数値診断を再計算しない。

低noise独立計時の第2段階は別Linux配置で26件に通過し、第3段階runnerと第4段階報告adapterを並行実装している。
旧census CLIには新4 manifestの供給口がないため、既存engineを使う新旧全seedの単一監査入口も小仕様から実装を進める。
全行非選択で新seed allocationが0なら監査の再実行を要求せず、その未実施理由を記録し、60 namespace監査済みとは扱わない。
残り11条件の合成解析capacity用wrapperとsingle-PBS copy用wrapperは独立レビューを通過したが、実投入は未実施である。

## 2026-10-18 17:10 JST時点の更新

低noiseの独立計時selectorは独立レビュー後、既存bundleを変更しない別Linux rootへ配置し、38 passed・8.09秒・skipなしを確認した。
実import先47 moduleと既存入力・runtime・native binaryの前後一致を保存したが、本番selection・全raw走査・qsubは未実施である。
第2段階の科学manifest・seed adapterは全24行と新stage160–163を保持し、独立受入26件に通過した。
正式manifest生成と新旧seedの全数監査はまだ行っていない。
第3段階の実行・資源仕様を確認し、固定2 replicateのfull-estimator capacityから最大96 workersと192 replicateの分割を決めるrunnerを実装中である。
巨大予算・timeout・費用不明・資源方針での実行不能を区別し、計算量や分母を減らさず記録する。

主ノイズの正式計時報告adapterは、受理済み全payloadのhash結合と公開直前のtask censusに関する独立指摘2件を解消した。
独立受入では元35件と追加2件に通過し、別Linux環境の配置・接続検証を進めている。
既存MC保存stdoutと実submission ledgerの異なるbytes hashは、それぞれの元記録とJSON内容の一致へ結合し、元の証拠を書き換えていない。
全4 caseの独立BAR本計時と正式な同精度比較は引き続き未完了である。

265259と265265は稼働中で、最大2ノードを維持している。
single-PBSのcopy投入wrapperは実prepare前の独立レビュー中で、元265259の終端後にのみ準備・投入する。

## 2026-10-18 16:57 JST時点の更新

case0の独立BAR本計時265263は全384 taskの点推定・区間を取得し、失敗・未取得・再利用は0だった。
全1,167ファイルと8,448 chainのseed座標・固定prior・保存形状・初期状態metadataを独立照合した。
証拠は`data_tile_validation_2026-10-17/bar_main_case0_evidence_v1/independent_payload_verification.json`に保存し、達成精度とMCとの計時比の正式集計は別途実施する。

低noise合成解析capacity265264はF・exit 0、PBS wall4分03秒で終了し、全8 group・35 artifactを回収・独立照合した。
全groupで88設定・2,496診断を処理し、未取得は0だった。
実測から得た本解析の基本資源は96 workers・48 GiB・1時間30分だが、後段のcopy・全payload hash検査の追加費用は含まない。
このcapacityの旧保存契約は数値ACF配列を保存しないため、配列の数値照合を実施したとは扱わない。

case3のBAR計時capacityを265265としてqsubし、低noise本計算265259と合わせて2ノード稼働を確認した。
本計時case1・case2、低noise分割本計算、全混合診断集計は準備済みで投入待ちである。
single-PBS staging controlの独立レビューとLinux受入37件を完了したが、元265259の終了前であり実copy・後段qsubは未実施である。

主ノイズの正式計時報告adapterと、低noise全24条件の独立計時selector・新seed manifestを並行して実装・レビューしている。
既存56 namespaceのseed監査は新しい低noise独立計時のstage160–163を含まず、その実行前に新旧集合の全数監査を別途必要とする。
低noiseの正式設定選択は全12条件の校正・監査・回収が揃ってから行い、幅の広いreferenceや精度未達を理由に条件を分母から除外しない。

## 2026-10-18 16:43 JST時点の更新

case2のBAR計時capacity265262はF・exit 0、PBS wall1分49秒で終了した。
case1・case2とも全192 task/区間を取得し、全3,072/6,912 chainの固定prior・seed座標・形状・初期状態metadataを独立照合した。
case0の本計時265263を実preflight後にqsubし、PBS上でF・exit 0、wall1分31秒となることを確認した。
stage140の本計時384 taskの全保存結果と達成精度は検証中で、PBS終了だけで科学結果を受理していない。

空いた枠へ低noise case2/target0の合成解析capacityを265264としてqsubし、265259と265264の2ノード稼働を確認した。
v3 bundleの既存固定planを用い、8 group/8 workerの資源profileを測定する。
これは低noise samplingのraw traceとは独立した合成計測であり、科学的精度の証拠ではない。
初期要求96 CPU・340 GB・24時間は上限で、完了予定ではない。
実投入の記録は`data_tile_validation_2026-10-17/low_analysis_capacity_case2_target0_submission_v3_*`に保存した。

## 2026-10-18 16:39 JST時点の更新

case1のBAR計時capacity265261はF・exit 0、PBS wall11分47秒で終了した。
全artifact回収と独立payload照合を進める間に、case2の事前確認を通し265262としてqsubした。
低noise本計算265259と265262の稼働を確認し、最大2ノードを維持している。
BAR本計時用wrapperは親レビューとmock13件に通過し、case0の全capacity結果に基づく本計時planを用意したが、本計時はまだ投入していない。

single-PBSデータ引き渡しhelperを独立control bundleへ配置し、Linux55 passed・2.83秒とnative 8 binary・既存187入力の不変を確認した。
実copyと後段実行は未実施で、後段各jobのactual PBS終了/資源と追加hash予算を結合するcontrol入口を別仕様で補っている。
低noise解析capacityの投入helperで親が指摘した2件は修正版v3で解消し、owner23件・独立33件の受入とread-only接続確認を通過した。
この解析capacityは未投入である。

独立MC計時の全8条件を保存summaryから再集計し、経験的精度判定が目標内4・超過2・reference依存2となることを確認した。
閾値・seed・cohortは変更せず、同精度比を出せない条件を残す。
現在の計時manifestは主p*=.03/.05のみで、低noise計画が要求する独立計時は別の残作業である。
低noise候補が精度判定を通らない場合はineligibleを保存し、設定間整合性や既存費用の比例配分から速度比を作らない。
報告書と`data_tile_validation_2026-10-17/timing_mc_achieved_precision_v1_ja.md`に範囲を反映した。

## 2026-10-18 16:29 JST時点の更新

BAR計時capacityのcase0・265260はF・exit 0、PBS wall49秒で終了した。
全192 taskの結果と区間を取得し、失敗・区間未取得・再利用は0だった。
591ファイルの転送hashと4,224 chainの固定prior・seed座標・config・保存shape・初期状態metadataを照合したが、全物理状態の再復号と達成精度の判定は行っていない。
本計時の資源要求は実測により1 node・96 CPU・32 GB・30分として受理された。
証拠は`data_tile_validation_2026-10-17/bar_capacity_case0_evidence_v1/independent_payload_verification.json`に保存した。
case1のBAR計時capacityを265261としてqsubし、低noise本計算265259と合わせて2ノード稼働を確認した。

分割samplingの一回限り投入helperはmock受入21件と独立レビューを通過した。
case0/target0/anchors0のread-only preflightも成功し、v11 source・runtime・native・plan・scriptとcontroller終了を実照合した。
その時点で要求2ノードのため`slot_available=false`を記録し、分割本計算のqsubは行っていない。
低noise解析capacityの別helperは、親レビューで受入manifest/readinessの外部hash固定とimport前source検査の不足を指摘し、未投入のまま修正している。
single-PBSデータの解析用コピーは途中変更拒否と計算ノード上の全payload検査をレビュー済みで、追加hash走査時間の資源見積もりとLinux配置は準備中である。

## 2026-10-18 16:22 JST時点の更新

追加seed監査265253はF・exit 0、PBS wall25分14秒で終了した。
全56 namespace・3,963,562件に未確認・意図しない衝突はなく、意図した共有8,448件を除くunique seedは3,955,114件だった。
stage140/141の全4条件を含み、予約した未列挙stageは残っていないが、乱数系列の統計的独立性を証明したものではない。
172ファイルの転送hashとsource/runtime/input/PBSを照合し、`data_tile_validation_2026-10-17/bar_seed_census_evidence_v1/independent_verification.json`に保存した。
このproofを外部pinしたwrapperのread-only preflight後、tile72 bit-flipのBAR計時capacityを265260として一度だけqsubし、稼働を確認した。
初期要求1 node・96 CPU・340 GB・24時間は資源上限であり、実測消費量や完了予定ではない。
低noise本計算265259と合わせて要求ノード数は2で、BAR capacityの終端検証と本計時は未完了である。

## 2026-10-18 16:16 JST時点の更新

低noise本計算265259と追加seed全数監査265253は稼働中で、要求ノード数は合計2である。
265259の192 anchorは全て正常終了し、samplingを継続している。
全12条件のcapacityを正式検証し、単一PBS上限を超える9条件の分割計画をv11に用意した。
Linux受入は163 passed・skipなしで、固定source/runtime/nativeと既知入力4,184ファイルの最終hash照合が一致した。
全192 replicate・768 groupを保持し、anchor 9 jobとsample 17 jobを準備したが、分割本計算のqsubは未実施である。
詳細は`data_tile_validation_2026-10-17/low_sampling_partition_preparation_v1_ja.md`と同JSONに保存した。
要求時間の合計322 node-hourは資源上限の和で、完了予定ではない。
既存単一PBSのcase2三条件は重複生成せず、終了後に元PBSと全artifact hashを保持して解析用保存先へコピーする接続手順を検証している。
BAR独立計時のcapacity4条件もdry-runまで準備済みで、追加seed監査の正常終了確認後に投入する。

## 2026-10-18 16:03 JST時点の更新

tile72 depolarizing・p=.01の低noise本計算を265259としてqsubし、稼働を確認した。
既存単一PBS路線の`20261018-tile-low-noise-v2/runs/production-2-0`を用い、固定192 seed、61,440 sampling taskと192 anchorを実行する。
96 CPU・32 GB・9時間30分の要求は資源上限であり、完了予定ではない。
追加BAR seed監査265253も稼働中で、全体2ノードを維持している。

WSS export265254はF・exit 0、wall3分18秒で終了し、71,904ファイル・23,954 artifactの回収と全member/identity/hash/size・監査消費hash・source/native/PBS・転送終端照合を完了した。
証拠は`data_tile_validation_2026-10-17/weight_reference_recovery_terminal_validation_v1.json`、archiveと検証結果は`weight_reference_recovered_v1/`に保存した。

混合診断一覧のcapacity4条件265255〜265258も全てF・exit 0となり、固定1groupの入力・実測・出力を照合した。
全件一覧の4planと投入commandは`mixing_execution_full_preparation_v1.json`にあり、各1 CPU・4 GB・1時間30分の実測外挿要求で、full一覧は未投入である。

分割sampling・BAR解析/最終collection・trace監査の追加moduleはWindows受入と独立レビューを通過した。
共通sourceをfreezeし、旧sourceを維持するv11 bundleのLinux受入・後続統合・正式分割prepareを進めている。
分割本計算と後続科学解析はまだ実行していない。

## 2026-10-18 15:57 JST時点の更新

低noise全12条件のcapacityと全artifact照合が完了し、sampling 1,216件とanchor 24件は全て正常だった。
元の資源gateでtile72 depolarizingの3条件だけが受理され、要求時間は9.5・10・11時間、各32 GBである。
残る9条件は26〜47時間の外挿要求となり、24時間上限を超えるため分割が必要である。
これは資源要求であり完了予定や精度保証ではない。
全12条件の結果は`data_tile_validation_2026-10-17/low_sampling_capacity_all12_summary_v1_ja.md`、単一PBS本計算3条件の準備は`low_sampling_single_production_preparation_v1_ja.md`に保存した。
本計算はまだ未投入である。

主4条件の最終再集計から固定規則で独立BAR計時の全8候補を選び、8本のmanifestを生成した。
これらには全192 seedの診断flagが残るため、推奨設定と扱わない。
追加stage140/141を含む3,963,562件の全数seed監査を265253としてqsubし、稼働中である。
層別referenceと監査の全71,904ファイルを回収するexportも265254としてqsubし、最大2ノードを維持した。
保存済み全混合診断のcapacity4条件もLinux受入と独立レビューを通過し、空き枠で実行する準備ができている。
混合一覧runnerの初版venv経路不一致はprepare時に停止して証拠を保存し、v2では実際のbundle経由Pythonでruntime/native・受入・prepareを確認した。

## 2026-10-18 15:45 JST時点の更新

主4条件の最終再集計と独立回収検証が完了した。
case0/2の265241/265240もF・exit 0、各4/5 phase成功で、全192 replicate・768 groupを保持している。
case0のPBS wallは5分18秒、case2は3分58秒だった。
全4条件の証拠を`data_tile_validation_2026-10-17/final_reaggregation_case{0,1,2,3}_evidence_v1/`に保存した。
これを用いた固定規則による独立BAR計時候補の選択接続と、保存済み全混合診断の一覧化を準備している。

低noise sampling capacityのtile72 bit-flipはp=.01/.003/.001の全3条件で正常終了し、全artifact・実seed・prior・source/native/PBSを確認した。
元資源式の要求は順に31時間30分・31時間30分・35時間30分で、いずれも24時間上限を超えるため単一本計算を投入しない。
固定taskを保つ分割runnerと複数PBSの後続監査接続を並行実装している。
次のtile288 bit-flipのp=.01/.003を265244/265245としてqsubし、待機中を含め最大2ノードを維持した。

## 2026-10-18 15:40 JST時点の更新

tile288 bit-flip・depolarizingの最終再集計265236/265238は正常終了し、全192 replicate・768 groupと全phase成果物の回収・照合が完了した。
case1は4 phase・wall 2分45秒、case3は初期化strataを含む5 phase・wall 3分3秒だった。
証拠は`data_tile_validation_2026-10-17/final_reaggregation_case{1,3}_evidence_v1/`に保存した。
tile72のcase2/0は265240/265241としてqsubし、最大2ノードで実行している。

独立MC本計時265237も正常終了し、全1,536 task・10,358,784試行・失敗0件を回収した。
phase時間226.898秒、PBS wall 3分50秒で、全artifact・seed・model・native環境・PBSとの結合を確認した。
証拠は`data_tile_validation_2026-10-17/mc_timing_main_evidence_v1/`に保存した。
BARの独立計時と同精度速度比較は未完了である。

低noise samplingの分割仕様を独立レビューし、固定192 seedとtask・anchor共有を保つ明示的な複数PBS証拠の実装へ進んだ。
分割samplingと後続解析・監査の接続が受入を通るまで低noise本校正を投入しない。
保存済み混合診断の全件一覧化とWSS生データの専用回収も並行して準備している。

## 2026-10-18 15:33 JST時点の更新

残るanalysis case0とsampling case2のarchive回収・全member/identity/payload/hash検証が完了し、主4条件のsampling・BAR解析の全archiveが揃った。
case0 analysisは4,439,599,537 bytes・2,315ファイル・768 artifact、case2 samplingは1,119,120,228 bytes・129,606ファイル・43,200 artifactだった。
根拠は`production_analysis_recovery_case0_20261018-v2-tile-case0-analysis-recovery.json`と`sampling_case2_collection_stage_binding_v1.json`に保存した。

MC primary referenceと監査済みWSSのmain4条件を照合し、全4条件で99.9%区間が交差した。
tile288のWSS区間はMCより広く、事前計画のMC primaryを変更しない。
数値と範囲は`main_mc_wss_summary_comparison_v1.json`に保存し、真値や被覆の保証とは扱わない。

最終再集計case1を265236としてqsubし、F・exit 0・wall 2分45秒で完了した。
担当がphase成果物を回収・照合中であり、次のcase3再集計265238を実行している。
case0/2の入力配置と固定planも準備済みで、未投入である。
MC計時capacity265234は全768 task・5,179,392試行が成功し、phase114.642秒と計測artifactの結合を確認した。
その実測に基づくMC本計時265237をqsubし、case3再集計と合わせ最大2ノードで稼働している。

低noise capacity0-0の265235はF・exit 0、80 sampling taskと2 anchorが全て成功した。
全192 seedへの既存資源外挿は31時間30分・32 GBとなり、24時間上限のため単一fullジョブ投入を拒否した。
固定seed/task集合・anchor共有・複数PBSの証拠と後続監査を保つ分割仕様を作成し、独立レビューする。
この制限を回避するためにcohortを減らしたり、単一jobの完了証拠を偽装したりしない。
根拠は`low_sampling_capacity_0_0_terminal_v1.json`と同名`_files/`に保存した。

## 2026-10-18 15:26 JST時点の更新

analysis case0回収265231とsampling case2回収265232は共にF・exit 0となり、各担当が固定collectorを一回実行してarchiveの転送と全member照合を進めている。
この時点では両archiveの全照合完了とは扱わない。

診断一覧化と最終再集計runnerを新immutable bundle `20261018-tile-low-analysis-v10`へ配置し、Linuxでも46件の受入を完了した。
旧core29ファイルとv9継承入力は不変で、native照合も一致した。
`data_tile_validation_2026-10-17/low_analysis_source_binding_v10.json`と関連acceptance/deployment記録に根拠を保存した。
case1/3の最終再集計は、検証済みarchive証拠とfull trace監査を結合する入力配置・plan準備を進めている。

空いた枠で独立MC計時capacityを265234としてqsubした。
stage122・768 task・5,179,392試行、1ノード96 CPU/32 GB/30分の初期予算であり、主計時はcapacity実測後に別途投入する。
さらにtile72 bit-flip・目標p=0.01の低ノイズcapacityを265235としてqsubした。
固定80 sampling taskと2 anchor、1ノード96 CPU/340 GB/24時間は初期上限であり、全192 seedの本校正や完了時間保証ではない。
両ジョブの稼働を確認し、最大2ノードを維持している。
投入証拠は`mc_timing_capacity_submission_v1_stdout.txt`と`low_sampling_capacity_0_0_submission_v1_stdout.txt`および対応する実行script/stderrに保存した。

## 2026-10-18 15:22 JST時点の更新

主4条件のfull trace監査が全てF・exit 0で完了し、各768群・全192 seedの監査失敗は0だった。
合計190,464 traceの全compact点、保存初期状態と7,747,584 checkpointを検査した。
case順のphase時間は72.624秒・48.880秒・23.390秒・79.991秒だった。
全予定group identityと回収したsummary/native/jobの結合を親担当が照合し、`data_tile_validation_2026-10-17/main_trace_audit_completion_v1.json`に保存した。
現在の全group payloadと解析rowの結合確認は後続のaudited-results adapterで行い、全物理状態の再生や混合・被覆の保証とは区別する。

seed照合265220もF・exit 0・wall 24分42秒で終了し、予定3,855,274件の未検査0・予期しない衝突0・意図共有8,448件を独立件数式で確認した。
`data_tile_validation_2026-10-17/seed_census_evidence_v1/REPORT_ja.md`に全証拠と適用範囲を保存した。
予約したBAR計時stage140/141は未列挙であり、乱数streamの統計的独立性を証明したとは扱わない。

重み層別referenceの独立監査265227はF・exit 0で終了し、16条件・97,857,608試行のdraws/counts監査と固定checkpoint 406,690件の再復号を完了した。
監査失敗0・終端結合一致で、phase時間は171.350秒だった。
`weight_reference_audit_summary_v1.json`と`weight_reference_audit_terminal_validation_v1.json`に証拠を保存し、全label再復号や名目被覆保証とは扱わない。

残るanalysis case0回収を265231、sampling case2回収を265232としてqsubし、最大2ノードで実行している。
全rung診断一覧化は15件、最終集計runner/submitterは31件の軽い受入と独立レビューを完了した。
新bundleへの配置とLinux受入を進めており、最終再集計・独立計時・低ノイズ本番は未完了である。

## 2026-10-18 15:13 JST時点の更新

重み層別referenceの265221はF・exit 0、PBS wall 9分46秒で正常終了した。
固定16条件・97,857,608 trials・23,938 chunksが全て完了し、実行失敗は0だった。
正式summaryとsource/runtime/input/native/receiptの結合確認を完了し、`data_tile_validation_2026-10-17/weight_reference_summary_v1.json`と`weight_reference_terminal_validation_v1.json`に保存した。
raw数値の独立監査は未実施であり、この段階ではreferenceの精度判定に使用しない。

case0のtrace監査capacity265222は96群・失敗0、phase 10.789秒で終了した。
実測から本監査の資源要求を算出して265223をqsubし、全192 seed・768群の監査がF・exit 0、phase 72.624秒で終了した。
保存全時点のcompact配列と保存済みinitial/checkpointを検査し、監査失敗は0だった。
未保存の物理状態の再生、独立decoderによる正しさの証明、混合や被覆の保証は行っていない。
PBS・manifest・native・summary・脚本・ログの原本と結合証拠は`data_tile_validation_2026-10-17/trace_audit_evidence_v1/capacity-0/`と`full-0/`に回収した。
全groupの監査payloadはremoteに保持し、最終集計adapterで照合する。

続くcase1のtrace監査capacityを265224としてqsubした。
seed照合265220と合わせ最大2ノードを維持する。
保存診断を全rung・全観測量で一覧化する処理と、最終集計をqsubで実行するrunnerを、それぞれ実装担当と独立レビュー担当に分けて並行作業している。

## 2026-10-18 15:00 JST時点の更新

重み層別referenceの固定16条件・97,857,608 trials・23,938 chunksを既存submitter経由でqsubし、265221の稼働を確認した。
資源は1ノード・96 CPU・32 GB・4時間30分要求であり、完了時刻や推定精度の保証ではない。
直前に固定80ファイル、入力、Python/native、manifest、resource、脚本、未投入intentを別担当が照合した。
証拠は`data_tile_validation_2026-10-17/weight_reference_pre_submission_recheck_v1.json`と`weight_reference_submission_stdout_v1.txt`に保存した。
seed照合265220と合わせて最大2ノードを維持している。

case0 sampling回収265219はF・exit 0で終了し、7,866,545,400 bytesのarchiveを回収した。
全86,208 artifact・258,630ファイルのidentity/payload/hash検証、およびworkerと脚本の事前stage hashへの結合を確認した。
証拠は`data_tile_validation_2026-10-17/sampling_case0_collection_stage_binding_v1.json`にある。
これは保存データの整合性検証であり、traceの数値監査・再復号・混合や被覆の検証完了を意味しない。
残るsampling case2とanalysis case0の回収、主4条件のtrace監査、独立計時、低ノイズ本番を引き続き進める。

## 2026-10-18 14:50 JST時点の更新

最後のtile72 bit-flip解析265212がPBS F・exit 0・wall 4時間30分34秒で正常終了し、主4条件のsamplingとBAR解析が全て完了した。
各caseで352設定×192 seed、768群・67,584行の正式summaryを回収した。
case0の完了証拠は`data_tile_validation_2026-10-17/production_bar_case0_completion_v1.json`にある。
独立担当がcase0も21項目のsummary照合を完了した。
事前指定した60,000保存・burn-in 6,000・16 chains・fine ladderの全16設定では、診断flag・high R-hat・low ESS・未定義はいずれも0/192だった。
point被覆は180〜186/192だが、referenceの99.9%区間全体を含むentireは132〜150/192、交差するpossibleは188〜191/192で、有限referenceの不確かさが影響する。
全16設定とbias/RMSE範囲は[case0の暫定summary読取](data_tile_validation_2026-10-17/case0_bar_summary_read_v1_ja.md)に保存した。
診断警告がないことを収束・既約性・正しさの証明や名目95%被覆の保証とは扱わない。
case0解析の5,299,576,841 bytes・2,315ファイルの回収stageも準備済みだが、その回収qsub・collectは未実施である。

controllerは14:48:31 JSTの記録でfinishedとなり、実PID不在を独立確認した。
証拠は`production_controller_finished_status_v1.json`と`production_controller_finished_observation_v1.json`に保存した。
その後、既存submitterのcontroller不在・固定入力・共有lock・最大2ノード検査を通して、予定3,855,274 seed指定の全照合を265220としてqsubした。
1ノード・1 CPU・2 GB・30分要求で実稼働を確認し、sampling回収265219と合わせて計2ノードである。
投入証拠は`seed_census_submission_stdout_v1.txt`と`seed_census_submission_invocation_v1.py`に保存した。
全seed照合の結果は未取得で、予約したBAR計時stage 140/141はこの全照合の対象外である。
全traceの数値監査、重み層別reference、独立計時と低ノイズ本番は引き続き未完了である。

## 2026-10-18 14:43 JST時点の更新

case2解析archiveの転送と全2,315 member・768 artifactの整合性検証が完了し、親担当が回収証拠と検証記録のhashを照合した。
archiveは4,477,986,977 bytes、SHA256は`3431a5a84aa13ca0773ed8ebd92dab34feb3840b357496a7e614264183707410`である。
証拠は`data_tile_validation_2026-10-17/production_analysis_recovery_case2_20261018-v2-tile-case2-analysis-recovery.json`に保存した。
解析済みcase1/2/3のraw rowsを含むarchiveは全て回収済みとなったが、raw rowsの独立再集計・全traceの数値監査は未実施である。
case0解析265212とsampling回収265219は稼働中で、最大2ノードを維持する。

## 2026-10-18 14:40 JST時点の更新

case3解析の3,087,175,636 bytesのarchive転送と全2,315 member・768 artifactの整合性検証が完了し、親担当も回収証拠と検証記録のhashを照合した。
証拠は`data_tile_validation_2026-10-17/production_analysis_recovery_case3_20261018-v2-tile-case3-analysis-recovery.json`で、raw rowsの再集計・全traceの数値監査は未実施である。
case2解析の回収265218もPBS F・exit 0・wall 3分33秒となり、担当がcollectと全archive検証を開始した。

別担当がstage済みsampling回収case0/2の脚本・helper・元sampling完了・固定manifest/resource/ledgerを読み取り専用で照合した。
両rootは未投入のhelperとexport脚本のみで、根拠は`sampling_export_stages_readonly_check_v1.json`に保存した。
親担当が全8ledger/pins・追加投入予定なし・stage hash・直前global要求ノード数1以下を再照合し、case0 sampling回収をqsubして265219を得た。
投入証拠は`sampling_export_case0_submission_stdout_v1.txt`と対応する`submission_script_v1.py`にあり、実行intentを排他的に保存して再投入を防ぐ。
265219の正常終了・collect・全archive検証は未完了で、別担当へ分担した。
sampling v2 collectの自己申告hash照合に加え、回収したworkerとexport脚本を事前固定stageのhashへ結合する追加照合を行う。
科学解析265212と回収265219の最大2ノードを維持する。

## 2026-10-18 14:35 JST時点の更新

case1解析の回収265216はPBS F・exit 0・wall 1分42秒で終了し、1,943,166,818 bytesのarchive転送と全2,315 memberのhash検証が完了した。
768群の識別・marker・固定manifest/context/referenceとaccepted stageのworker/scriptも一致し、親担当が回収証拠とarchive検証記録のhashを確認した。
証拠は`data_tile_validation_2026-10-17/production_analysis_recovery_case1_20261018-v2-tile-case1-analysis-recovery.json`にある。
これは転送・識別・整合性の検証であり、全traceの数値監査やBAR再計算とは区別する。
workerの記録時刻がPBS終了時刻より先行していたため、原本を未補正で保持し、所要時間は単調時計elapsedとPBS wall timeを分けて記録した。

同じ全8ledger・pins・追加投入予定なし・直前global要求ノード数1以下の検査を各投入前に行い、case3回収265217とcase2回収265218を順にqsubした。
265217はPBS F・exit 0・wall 2分36秒で完了し、担当が転送・archive検証を進めている。
265218は1ノード・1 CPU・4 GBの回収jobとして投入し、別担当がPBS確認と正常終了後のcollectを担当する。
科学解析265212と回収1 jobの計2ノードを維持し、controller・固定科学計算bundleは変更していない。
投入証拠は`analysis_export_case3_submission_stdout_v1.txt`と`analysis_export_case2_submission_stdout_v1.txt`、実際の検査・投入コードは対応する`submission_script_v1.py`に保存した。

## 2026-10-18 14:30 JST時点の更新

独立確認により全8投入ledgerと固定controllerから追加投入予定がないことを確認し、親担当もpins・ledger・stage hashと直前のglobalノード数を再照合した。
空いた1ノードでcase1解析データの回収job 265216をqsubし、1 CPU・4 GB・1時間要求の実稼働を確認した。
tile72 bit-flipの解析265212と合わせて計2ノードである。
従来のcontroller終端待ちを今回のexportに限り追加投入予定なしの確認で置き換えた根拠は[全数監査・回収手順](tile_full_audit_execution_2026-10-18_ja.md)に記録した。
回収jobの正常終了、collectとarchive検証はこの時点で未完了で、担当を分けて進めている。

## 2026-10-18 14:27 JSTの完了と暫定集計

tile72 depolarizingのBAR解析265215はPBS F・終了コード0で完了し、768群・67,584行・352設定各192 seedの正式summaryを回収した。
PBS wall timeは37分39秒で、完了証拠は`data_tile_validation_2026-10-17/production_bar_case2_completion_v1.json`に保存した。
独立担当が設定・分母・固定context/referenceとの結合とsummary算術を21項目で照合した。
全352設定で区間未取得・記録された失敗は0だが、診断未定義は設定ごとに0〜164/192、延べ10,935/67,584設定×seed行だった。
同じtraceを再利用するため、この延べ件数は独立例の件数ではない。
事前固定した12,000保存・burn-in 6,000・8 chains・fine ladderの16設定では未定義0だが、診断flagは190〜192/192に残る。
block 1024/cross_chainのpoint被覆は172〜186/192（89.58〜96.88%）で、有限MC referenceの不確かさと全16設定を[case2の暫定summary読取](data_tile_validation_2026-10-17/case2_bar_summary_read_v1_ja.md)に保存した。
raw rows再集計・全analysis archive照合・全trace監査は未実施で、一部のpoint被覆が95%を超えても名目被覆の保証や推奨設定の確定とは扱わない。
case2解析の2,315ファイル・5,593,125,982 bytesの回収脚本を`20261018-v2-tile-case2-analysis-recovery`へstageし、固定hash・bash構文・LFを確認した。
回収qsub・圧縮・collectはこの時点で未実施である。
主4条件のBAR解析は3条件が正常終了し、残るtile72 bit-flipの265212が1ノードで稼働中、controllerも生存している。

## 2026-10-18 13:54 JST時点の更新

tile72 depolarizingの事前固定group `(2,0,0,0)`について、独立担当が予定88行の一意性・網羅性、診断1,728件とACF1,728配列の参照・shapeを確認した。
context/runtime/source/manifest/referenceと完成marker・payloadのhashは検査前後で一致した。
sampling失敗・推定失敗・区間未取得は0だったが、全88行にhigh R-hatとlow ESSの警告があり、12/88行が未定義診断を含む。
診断record単位の未定義は4/1,728で、推定行とは分母が異なる。
検査はremote 0.319秒、SSH込み2.229秒で、証拠は`data_tile_validation_2026-10-17/bar_analysis_first_artifact_case2_validation_v1.json`に保存した。
これは単一artifactの整合性確認であり、全trace再復号・BAR/bootstrap再計算・全cohortの校正ではない。
265212と265215は各1ノードで稼働中で、controllerの生存も確認している。

## 2026-10-18 13:50 JST時点の更新

tile288 bit-flipのBAR解析265214はPBS F・終了コード0で完了し、768群・67,584行・352設定各192 seedの正式summaryを回収した。
PBS wall timeは1時間42分6秒で、完了証拠は`data_tile_validation_2026-10-17/production_bar_case1_completion_v1.json`に保存した。
独立担当は予定設定・分母・固定context/referenceとの結合とsummaryの算術を21項目で照合した。
全設定で区間未取得・記録された失敗は0だったが、全192 seedにlow ESSの警告がある。
事前固定した12,000保存・burn-in 6,000・8 chains・fine ladderの全16設定では、high R-hatも全192 seedに残り、block 1024/cross_chainのpoint被覆は169〜182/192（88.02〜94.79%）だった。
有限MC referenceの不確かさ、全16設定と適用限界は[case1の暫定summary読取](data_tile_validation_2026-10-17/case1_bar_summary_read_v1_ja.md)に保存した。
全analysis archive照合・raw rows再集計・全trace監査は未実施で、名目95%被覆や推奨設定の保証とは扱わない。

case1解析の2,315ファイル・2,492,080,765 bytesの回収脚本を新root `20261018-v2-tile-case1-analysis-recovery`へstageし、固定hashとbash構文を確認した。
回収脚本のqsub・圧縮・collectは未実施である。
controllerは後続のtile72 depolarizing解析265215をqsubで投入し、13:49:58 JST時点で265212と265215が各1ノードで稼働している。
265215の要求は96 CPU・46 GB・2時間で、投入ledger・脚本・固定context/runtime/source/native hashと実PBSの結合25項目を照合した。
記録は`data_tile_validation_2026-10-17/production_bar_case2_submission_observation_v1.json`にあり、最大2ノードを維持している。
主4条件のsamplingとtile288両noiseのBAR解析は完了したが、tile72両noiseのBAR解析、全数監査、重み層別reference、同精度の計時比較、低ノイズ本番は未完了である。

## 2026-10-18 12:30 JST時点の更新

BAR解析265212・265214とcontroller PID 3756042の稼働を確認し、保存済み群はcase0が298/768、case1が119/768に増えた。
同時稼働は各1ノードの計2ノードで、追加の手動qsubは行っていない。
監視記録は`output/tile_live_wait_observations.jsonl`に追記している。
独立担当がcase1の事前固定group `(1,0,0,0)`について、予定88行の一意性・網羅性、診断744件とACF744配列の参照・shape、context/runtime/source/manifest/referenceとpayload hashの前後一致を確認した。
この群のsampling失敗・推定失敗・区間未取得・診断未定義は0件だったが、88行全てに診断flagがある。
検査はremote 0.139秒、SSHを含め2.059秒で、証拠は`data_tile_validation_2026-10-17/bar_analysis_first_artifact_case1_validation_v1.json`に保存した。
これは単一artifactの整合性確認であり、全trace再復号・BAR/bootstrap再計算・全cohortの精度や被覆の確認ではない。

## 2026-10-18 12:13 JST時点の更新

tile288 depolarizingのBAR解析265213はPBS F・終了コード0で完了し、768群・67,584行・352設定各192 seedの正式summaryを回収した。
PBS wall timeは1時間39分1秒で、記録は`data_tile_validation_2026-10-17/production_bar_case3_completion_v1.json`にある。
独立担当が予定設定の網羅性、固定context/referenceとの結合、被覆件数とbias/RMSE範囲の算術をsummary上で照合した。
全352設定で区間未取得・記録された失敗は0だったが、全設定の全192 seedにhigh R-hatとlow ESSの警告が残った。
事前指定した12,000保存・burn-in 6,000・8 chains・fine ladderの全16設定では、block 1024/cross_chainのpoint被覆は175〜178/192（91.15〜92.71%）だった。
point被覆は有限MC referenceの点推定を区間が含む率であり、真値に対する名目95%被覆の保証ではない。
reference区間全体を含む件数・交差する件数、診断未定義、bias/RMSE範囲を含む全16設定は[暫定summary読取](data_tile_validation_2026-10-17/case3_bar_summary_read_v1_ja.md)に保存した。
raw rowsの独立再集計・全analysis archive照合・全trace監査は未実施で、推奨設定は確定していない。

別担当がcase3解析の2,315ファイル・3,890,389,474 bytesを対象とする回収脚本を新root `20261018-v2-tile-case3-analysis-recovery`へstageし、固定hashとbash構文を確認した。
この回収脚本のqsub・圧縮・collectは未実施である。
12:12:48 JSTのqstatではBAR解析265212と、controllerが追加投入した265214が各1ノードで稼働しており、最大2ノードを維持している。
265214はtile288 bit-flipで、実PBS要求は96 CPU・98 GB・3時間、投入ledger・脚本・context・固定source/native hashと実PBSとの結合を独立担当が確認した。
証拠は`production_bar_case1_submission_observation_v1.json`で、runtime辞書の追加フィールドによる比較差は原記録を保持したまま`production_bar_case1_submission_runtime_binding_v1.json`で説明した。
この確認は投入と保存された環境情報の整合性であり、実行node上の新たなdecoder再現性検査ではない。
主4条件のsamplingは完了しているが、残りのBAR解析、全数監査、重み層別reference、同精度の計時比較、低ノイズ本番は引き続き未完了である。

## 2026-10-18 11:51 JST時点の更新

BAR解析265212・265213は各1ノードで稼働を継続し、case0は192/768群、case3は611/768群の完了markerを確認した。
controller PID 3756042も稼働中で、根拠は`data_tile_validation_2026-10-17/bar_analysis_live_observation_v4.json`に保存した。
解析完了や全体のbias・被覆・混合の確認とは扱わない。
本番の大きいBAR artifactをPBS内で圧縮して回収するhelperを準備し、独立レビューでstage時のworker/script hashへの結合を追加した。
最終受入はWindows27 passed・2.80秒、独立Linux rootでも27 passed・0.23秒で、PBS脚本テンプレートのbash構文と受入後のsource hashも確認した。
固定source・小仕様・受入・レビューの結合は`analysis_recovery_preparation_v2.json`、実行手順は[全数監査・回収手順](tile_full_audit_execution_2026-10-18_ja.md)に保存した。
このhelperによる本番stage・圧縮・collect・qsubは未実施で、既存sampling helperとproduction bundleは変更していない。

## 2026-10-18 10:56 JST時点の更新

BAR解析265212・265213は各1ノードで稼働し、case0は96/768群、case3は192/768群の完了markerを確認した。
controller PID 3756042も稼働中で、追加qsubは行っていない。
観測記録は`data_tile_validation_2026-10-17/bar_analysis_live_observation_v3.json`に保存した。
完了marker数は解析処理の進捗であり、全cohortのbias・被覆や収束の確認とは区別する。
11:03 JSTにはcase0の固定group `(0,0,0,0)`について、予定88行の一意性、診断とACF各1,056件の参照・shape、context/runtime/source/manifest binding、入力hashの前後一致を0.21秒で確認した。
この群の区間未取得・推定例外・sampling失敗記録は0件で、根拠は`bar_analysis_first_artifact_case0_validation_v1.json`に保存した。
この確認は単一artifactの整合性に限り、全trace監査・bootstrap再計算・全cohort校正を代替しない。

独立する準備をサブエージェントへ分担し、低ノイズsamplingと合成データによるBAR解析のcapacity計画を、それぞれ既定の全12条件について揃えた。
各11件の新規計画でnative環境照合・dry-run・PBS脚本の構文確認が成功し、既存root・固定bundle・Python環境は変更していない。
sampling側の証拠は`low_sampling_capacity_preparation_v1.json`、解析側は`low_analysis_capacity_remaining_preparation_v1.json`と対応する個別記録にある。
親担当でも個別記録の成功状態・保存原文のhash・解析source bindingを照合した。
主校正trace監査もcase0・1・2のcapacity/full計画を追加し、既存case3と合わせて全4条件を準備した。
根拠は`trace_audit_remaining_plans_preparation_v1.json`にある。
これらは準備のみで、実capacity・full監査・低ノイズ本番・qsubは未実施である。
低ノイズcapacityの96 CPU・340 GiB・24時間は未計測の要求上限で、所要時間の予測ではない。

## 2026-10-18 10:40 JST時点の更新

BAR解析265212・265213とcontrollerの稼働を再確認し、10:39:58 JSTにcase3の96/768群の完了markerを確認した。
case0は同時点で完了group 0件だったがCPUを使用して稼働しており、停止・再投入は行っていない。
両jobの使用メモリは要求枠内で、観測値は`data_tile_validation_2026-10-17/bar_analysis_live_observation_v2.json`に保存した。
固定group `(3,0,0,0)`だけについて、analysis context・全予定88条件・group/replicate identity・診断1,224件・ACF配列1,224個・payload/marker hashを0.18秒で照合した。
この群の区間未取得・推定例外・sampling失敗記録は0件で、入力は読込前後で一致した。
根拠は`bar_analysis_first_artifact_validation_v1.json`に保存し、trace再復号・bootstrap再計算・全cohort統計・混合や精度の判断を行ったとは扱わない。
BAR4条件の完了、全数値監査、低ノイズ検証、同精度計時は引き続き未完了である。

## 2026-10-18 10:28 JST時点の更新

tile72-depolarizingのsampling265211も終了コード0・walltime01:56:39で完了し、全43,008 task・失敗0件のsummaryを予定集合へ照合した。
これで主校正4条件のsamplingはすべて完了し、全190,464 task・失敗記録0件となった。
4jobのPBS終端とsummaryを再照合し、case1/3は回収済みarchive内のhash、case0/2は取得したsummaryのhashへ結合した。
根拠は`data_tile_validation_2026-10-17/production_sampling_complete_2026-10-18.json`に保存した。
失敗記録0件は混合・bias・被覆を示す値ではなく、全数値trace監査とBAR本集計は未完了である。

controllerが10:26:34 JSTにqsubでtile288-depolarizingのBAR解析265213を投入し、tile72-bitの解析265212と各1ノードで実行中である。
case2の回収対象1,245,641,312 bytesも新規root `20261018-v2-tile-case2-recovery`へstageし、固定helper hashとPBS脚本のbash構文を確認した。
gateは4.69秒、SSH込み6.66秒、stage全体14.10秒で、qsub/exportは未実施である。
根拠は`production_sampling_export_gate_case2_20261018-v2-tile-case2-recovery.json`、`production_sampling_export_stage_case2_20261018-v2-tile-case2-recovery.json`、`production_sampling_export_script_validation_case2_v2.json`に保存した。
case0/2の大きい圧縮処理は、既存controller終了後にqueued込み最大2ノードを確認してqsub投入する。

## 2026-10-18 10:19 JST時点の更新

tile72-bitのsampling265209が終了コード0・walltime07:07:40で完了し、全86,016 task・失敗0件のsummaryと固定manifest・予定task集合を照合した。
summaryのphase時間は25,634.37秒であり、PBS全walltimeと区別する。
controllerは10:17:27 JSTにqsubでBAR解析265212を投入し、tile72-depolarizingのsampling265211と各1ノードで稼働している。
完了・summary hash・解析script/ledger・PBS記録は`data_tile_validation_2026-10-17/production_case0_completion_2026-10-18.json`に保存した。
sampling完了は混合・BAR bias・被覆の確認ではなく、全payload回収と数値監査も未完了である。

case0の大きいarchive圧縮をPBS内で行う回収helperを別担当で準備し、元samplingの終端と全task/marker、入力8,074,369,747 bytesを確認して新規export rootへstageした。
初回はWindows text-mode転送で脚本がCRLFとなりhash検査で停止したため、失敗rootを保持し、binary転送の合成受入後に別のv2 rootでsource/script一致を確認した。
v2は`/home/user/workspace/mcmc4qec/20261018-v2-tile-case0-recovery`で、qsubとexportは未実施である。
既存controllerの終了とqueued込み2ノード以内をlogin側で確認してから投入する。
転送前gateは8.70秒、SSH込み10.61秒、stage全体18.02秒だったが、archive圧縮の実測ではない。
根拠は`production_sampling_export_stage_case0_v1_hash_failure.json`と`production_sampling_export_gate_case0_20261018-v2-tile-case0-recovery.json`、`production_sampling_export_stage_case0_20261018-v2-tile-case0-recovery.json`に保存した。

## 2026-10-18 10:05 JST時点の更新

主校正と低ノイズの解析結果を全数trace監査へ結合する読み取り専用adapterを、別担当で並列実装・独立レビューした。
全192 replicate・768群と予定task、native/PBS証拠、markerと現在payload、保存rowsとsummaryを照合し、記録済みsampling失敗を分母から除外しない。
主校正には解析当時の消費入力hashがないため、その歴史的証明を行わないと明記し、保存BAR値の算術再現と現在入力の整合確認を区別した。
Windowsは主17件・43.23秒、低ノイズ10件・33.83秒、旧coreを保持したLinux v9でも計27件と厳密native照合が成功した。
本番全artifact通しは未実施であり、受入は小さい実保存artifactと明示した全数制御fixtureの組合せである。
手順・証拠・限界を[全数監査実行文書](tile_full_audit_execution_2026-10-18_ja.md)に追記した。
中間報告には追加3decoderの実装受入と適用制約も集約し、新decoderの統計校正とは区別した。

10:05:29 JSTのqstatでは265209・265211が各1ノードで実行中、controller PID3756042も稼働していた。
case0は83,740/86,016、case2は34,984/43,008 trace markerで、完了summaryは未作成だった。
観測証拠は`data_tile_validation_2026-10-17/low_analysis_cluster_observation_v8.json`にある。
本番全数監査・BAR被覆校正・低ノイズ本番・同精度計時は未完了で、既存稼働環境の変更・追加qsub・commit・pushは今回行っていない。

## 2026-10-18 09:47 JST時点の更新

低ノイズtrace監査の資源plannerと専用qsub submitterを追加し、8群の実測から全768群のworker数・メモリ・時間を選択する手順を接続した。
終了時の全入力再hashを費用へ含め、sampling失敗を含むcapacityを資源profileとして拒否し、1ノード・340 GiB・24時間を超える場合は別partition設計を要求する。
保存済みartifactからfull plan作成・資源再検証・qsub dry-runまでの結合受入と、変更された入力の拒否を確認した。
Windowsは20・33件、旧coreを保持したLinux v8でも計53件が成功し、独立レビューと厳密native照合を完了した。
再現手順と限界は[全数監査実行準備](tile_full_audit_execution_2026-10-18_ja.md)へ追記した。

WSS reference・MC計時capacity・main trace監査capacity・seed監査の既存planとクラスタ実fileの一致をread-onlyで確認し、`data_tile_validation_2026-10-17/next_stage_readiness_v1.json`に保存した。
これは投入準備の確認であり、計算成功や精度確認ではない。
live controllerは既存計画どおりsampling完了後にBAR解析を進め、全数監査とBAR解析の両方が最終校正判断の前提になる。
中間報告の古い記述を修正し、全4case・768 anchorの監査済み記録とphase summaryのhash・件数を再照合した。
09:47:58 JSTのqstatでは265209・265211が各1ノードで実行中、controller PID3756042も稼働していた。
case0は80,064/86,016、case2は28,224/43,008 trace markerで、完了summaryは未作成だった。
観測証拠は`data_tile_validation_2026-10-17/low_analysis_cluster_observation_v5.json`にある。
追加した監査手順の実qsub・全監査の資源実測・低ノイズ本番・BAR校正・同精度計時は未実施または未完了で、今回も稼働環境の変更・commit・pushを行っていない。

## 2026-10-18 09:38 JST時点の更新

低ノイズproductionの全768群を対象にしたtrace監査runnerと、元referenceの全16条件を変更せず監査するWSS runner、そのqsub submitterを追加した。
全draw・count・hashの検査と、事前固定checkpointだけの再復号を区別し、sampling失敗・reference未取得・監査失敗も予定分母に保持する。
独立レビューで見つかったWSS監査の終端binding2経路を追加受入で再現して修正し、全条件の記録を保存したまま異常を検出するようにした。
Windowsは新3 fileの13・13・22件が成功し、旧coreを保持したLinux v7でも計48件と厳密native検査が成功した。
実装範囲、受入・source・環境証拠、再現CLIは[全数監査実行準備](tile_full_audit_execution_2026-10-18_ja.md)に保存した。
低ノイズtrace監査の資源選択と専用submitter、全監査の実計測、reference本番・低ノイズ本番・BAR校正・同精度計時は未完了である。
実qsub・commit・pushと既存production環境の変更は行っていない。
09:38:56 JSTのqstatでは265209・265211が各1ノードで実行中、controller PID3756042も稼働していた。
case0は78,160/86,016、case2は24,747/43,008 trace markerで、完了summaryは未作成だった。
観測証拠は`data_tile_validation_2026-10-17/low_analysis_cluster_observation_v4.json`に保存した。

## 2026-10-18 早期混合診断とreference接続の更新

完了済みtile288-bit/depolarizingから事前固定した16群を診断し、128 traceの入力検査、initial128状態とcheckpoint2432状態の再復号が全て一致した。
診断未定義は0件で、flagはbit-flip 25/80観測量群、depolarizing 144/144観測量群だった。
depolarizingの全観測量群でR-hat > 1.01かつ最小chain ESS < 100となり、この部分集合で十分な混合を確認できたとはいえない。
各設定2 replicateだけの早期診断であり、全192 replicateのBAR校正、kernel間の統計的優劣、収束や非収束の証明には使わない。
生診断・入力hash・事前計画・再現手順は[早期混合診断報告](tile_early_mixing_2026-10-18_ja.md)に保存した。

低ノイズpartition専用qsub submitter、重み層別referenceの条件別監査、bounded referenceと低ノイズBARの比較を追加した。
全設定・全replicateの分母を保持し、部分weight和を全論理誤り率の点referenceとしない。
Windowsの最終対象は28・9・27件が成功し、旧coreを保持したLinux v6でも計64件と厳密native検査が成功した。
独立レビューで数値依存sourceの証跡不足を修正し、v5のtest fixture梱包漏れは失敗証拠を残した別v6で修正した。
実装範囲、環境・受入証拠、再現CLIは[reference接続検証記録](tile_low_noise_reference_validation_2026-10-18_ja.md)に保存した。
reference本番・低ノイズ本番・実データのreference比較・全数trace監査・同精度計時・最終校正は未完了である。
今回の追加検証ではqsub・commit・pushを行わず、既存production bundleとvenvも変更していない。
09:28:30 JSTのqstatでは265209・265211が各1ノードで実行中、controller PID3756042も稼働していた。
case0は75,936/86,016、case2は20,775/43,008 trace markerで、完了summaryはまだ作成されていない。
観測証拠は`data_tile_validation_2026-10-17/low_analysis_cluster_observation_v3.json`、早期診断の生記録・文書照合は`early_mixing_report_validation_v1.json`に保存した。

## 2026-10-18 09:14 JST時点の更新

低ノイズBARの資源計画に沿ったpartition実行・全768群回収、独立referenceなしの全cohort集計と設定比較、低ノイズcheckpoint監査、全seed監査用qsub wrapperを追加した。
新4 fileはWindowsで140 passed・12.32秒、旧coreのLinux v4 bundleでも140件が成功し、独立レビューを完了した。
missing partitionは未完了として停止し、記録済みsampling失敗・診断未定義・区間未取得は分母に残す。
checkpoint再復号を全物理状態の再復号とは扱わず、独立referenceのない設定一致をbias・RMSE・被覆の保証へ置き換えない。
Linuxで全seed計画の実1000件pilotとqsub dry-run・PBS構文確認を完了し、全数は約378.17秒と外挿したが未投入である。
全予定3,855,274件中3,854,274件は未検査で、stage140/141は実際の選択manifest待ちとして残す。
実測capacityと本番sampling完了を必要とするpartition本番plan、全数trace監査runner、独立reference接続と最終統計校正は未完了である。
再現手順と適用限界は[低ノイズ実行検証記録](tile_low_noise_execution_validation_2026-10-18_ja.md)に保存した。
09:14:09 JSTには265209・265211が各1ノードで実行中、controllerも稼働し、case0は72,987/86,016、case2は15,624/43,008 trace markerだった。
既存production環境を変更せず最大2ノードを維持し、追加qsub・commit・pushは行っていない。

## 2026-10-18 08:59 JST時点の更新

低ノイズ専用BAR解析、全chain・全trace長の合成解析capacity、stage150〜155を含む拡張seed監査を実装した。
Windowsの関連62件は31.13秒で成功し、既存科学計測と同じpackageを使うLinux v2でも62件と厳密native preflightが通った。
最新packageではnative応答が一致してもpackage hashが異なるため検査が拒否されることを確認し、既存profileの書き換えは行っていない。
tile72-bit・target .001・15 rungのcapacity planは生成済みで、全寸法の資源実測と実qsubは未実施である。
解析のpartitionは全768群を保持する資源計画だけで、本番driverへのpartition実行接続は未実装である。
seedの予定3,855,274件に対し1000件pilotを実行し、全数照合と選択manifest待ちのstage140/141は未完了として記録した。
適用限界と受入・環境差の証拠は[低ノイズ解析検証記録](tile_low_noise_analysis_validation_2026-10-18_ja.md)にある。
09:02 JSTまでに合成capacity用qsub submitterの独立レビュー・受入を完了し、最終Windows 85件・35.91秒、Linux 85件が通った。
queued込み2ノード上限・coordinator競合拒否・共有lock・不明応答時の再投入防止を検証し、v3 bundleのnative preflight・plan・qsub dry-run・PBS構文確認も成功した。
実qsubと全寸法の資源計測は未実施で、v3 archiveは`5a1861baef1fe943d57238c18b90c2a47205bd85ba492323d690cdc84a6ec995`である。
08:59:18 JSTには265209と265211が各1ノードで実行中、controllerも稼働し、case0は69,869/86,016、case2は10,304/43,008 trace markerだった。
低ノイズ本番、BAR被覆校正、全数値trace監査、重み層別reference本番と独立計時は未完了で、今回も追加qsub・commit・pushは行っていない。

## 2026-10-18 08:43 JST時点の更新

ユーザーがgoalを更新し、必要に応じた重み層別sampling、tile以外を含むBP-LSD・BeliefFind・UFの実装検証、サブエージェントによる並列作業を明示した。
追加3decoderと各sector版を公開APIへ統合し、独立レビューを反映した最終版はWindowsで202件、Linuxでは利用例を含む210件が通った。
補正のHc=sを検査し、BP-LSDはorder0、単独UFはldpc 2.4.1に対応を限定する。
適用制約・wheel検証・再現手順は [基本decoder検証記録](basic_decoders_validation_2026-10-18_ja.md) に保存した。
新decoderの速度・LER・BAR被覆は未校正であり、実装受入と統計校正を区別する。

tile288-bitの265210は08:29:17 JSTにExit_status=0で終了し、全30,720 traceと192 anchorを回収した。
1,084,152,515 byteのarchive内30,912 artifactについてidentity・payload hash・manifestとsummaryを照合した。
case2の192 anchorも監査済みとなり、4caseのanchor監査が揃った。
物理p=.1・fixed decoder prior=.03のcase2 anchorは3,145,728試行・1,480,773失敗であり、target pの独立referenceとは区別する。
証拠は`data_tile_validation_2026-10-17/production_case1_recovery_validation_2026-10-18.json`と`production_anchor_audit-2.json`にある。
08:43:17 JSTには265209と265211が各1ノードで実行中、controllerも稼働し、case0は66,512/86,016、case2は4,583/43,008 trace markerだった。
自動controllerがcase2をqsub投入し、この実装作業では追加投入・稼働bundle変更・commit・pushをしていない。
全数値trace監査、BAR本解析と被覆校正、層別reference本番、低noise本番、独立計時・最終報告は未完了である。

確認済みの符号構成・failure定義・decoderの制約・直接MC reference・未完了事項を [日本語中間報告](tile_validation_report_2026-10-18_ja.md) に集約した。
2026-10-18 06:19 JSTに、完了済み3caseのanchor監査と予定seedの重複検査を中間報告へ反映した。
reference表のcount・丸め値・区間、20個のローカルリンク、利用例source、anchor監査の集計値とsummary hash、seed監査の入力hashを再照合し、`data_tile_validation_2026-10-17/interim_report_validation.json` に保存した。
これは文書と保存済み根拠の整合確認であり、BAR校正の完了を示すものではない。

## 追加依頼：符号全般の基本decoder調査

ユーザーの「並列して、ほかのdecoder」「tile code以外でもいい」に合わせ、UF・BP-LSD・BeliefFind・単独BPを文献と導入済みldpc 2.4.1で調べた。
surface・toric・Steane・HGP・BB・tile72/288の7符号について各19状態のAPI/整合性probeをWindowsとLinuxで実行し、両環境37条件のraw配列・source・環境・native binary hashを保存した。
導入済み単独UFのbool/str binding不整合、単独BPでsyndrome不一致をlogical-only判定が見落とす例、BP-LSDやBeliefFindのOS間failure label差を確認した。
これは小さな共通入力probeであり、論理エラー率・速度順位・決定性全般の保証ではない。
調査結果と追加順は [基本decoder調査](decoder_survey_2026-10-18_ja.md)、rawと再計算は `data_decoder_survey_2026-10-18/` にある。
新しいpublic factoryは未実装で、低p専用BAR解析への接続も引き続き未実施である。
08:22 JSTにはcoordinator・265209・265210が稼働し、trace markerは62,121件・29,880件で、追加qsubは行っていない。

## 2026-10-18 08:15 JST時点の更新

低p用submitterを実装し、全capacity taskとnative実行証跡に基づく本番資源外挿、qsub前の排他的intent、coordinatorと2ノード上限の検査を追加した。
複数の低p submitter間の共通lockと、qsub応答不明時にintent・lockを保持して再投入しない動作も受入に含めた。
関連53件はWindowsで12.39秒、Linuxで6.14秒で成功し、小予算の実tile taskと合成した資源・実行証跡を使う検査の範囲を記録した。
新bundle `20261018-tile-low-noise-v2` に配置し、tile72-bit・target .01のcapacity plan・login native preflight・qsub dry-runを保存した。
初回capacityの要求は1ノード・96 CPU・340 GiB・24時間上限であり、実消費や終了時間の予測ではない。
受入・manifest・scriptとhashは `data_tile_validation_2026-10-17/low_noise_deployment_v2.json` にある。
08:14 JSTにcoordinator・265209・265210が稼働し、trace markerは60,559件・29,000件だった。
最大2ノードを維持し、低pの実qsub・capacity計測・本番、全seed重複照合と専用BAR解析は未実施である。
commit・pushは行っていない。

## 2026-10-18 08:09 JST時点の更新

低p専用 `tile_low_noise_study.py` のplan・sampling・独立MC anchorを実装し、関連36件をWindowsで5.06秒、Linuxで2.86秒で確認した。
4caseの短い実tile計測で、physical p=.1/.001に対して同じprior=.001とProblem hashを維持し、初期logical係数・syndrome/sector・失敗判定・seed metadataを検査した。
初期化失敗も予定seed付きで残し、native不一致ではworkerを起動せず、phaseごとの排他的intentにより自動再実行を拒否する。
新bundle `20261018-tile-low-noise-v1` のtile72-bit・target .01 capacity planは80 sampling task・2 anchor taskで、login nodeのnative照合に成功した。
受入・bundle・manifestと証跡は `data_tile_validation_2026-10-17/low_noise_deployment_v1.json` に記録し、再現手順は [低ノイズ実行準備](tile_low_noise_plan_2026-10-18_ja.md) に追記した。
低p用submitter、qsub容量測定、全seed重複照合、専用BAR解析への接続と本番は未実施である。
08:08 JSTにはcoordinator・265209・265210が稼働し、trace markerは59,248件・28,280件だった。
計2ノードを維持し、追加qsub・commit・pushは行っていない。

## 2026-10-18 08:03 JST時点の更新

本校正のsamplingと並行して、層別referenceとBAR cohortを比較する `tile_weight_reference_comparison.py` を追加した。
小仕様・受入・実装の順に進め、partial estimateを全体の点referenceにせず、未評価尾部を含むreference区間内のbias/RMSE範囲と区間包含・交差の割合を返す。
推定値未取得・区間未取得・診断フラグ・reference未取得を保持し、reference下端0では相対精度の達成判定を行わない。
関連54件はWindowsで10.17秒、Linuxで6.81秒で成功し、4caseの小予算実tile層別結果から比較関数への接続も検査した。
本番reference・低p BARの比較は未実施で、集計算術の検査をraw artifactやnative decoder環境の監査とは扱わない。
新しい不変bundle `20261018-tile-weight-reference-comparison-v1` へ配置し、hashと受入範囲を `data_tile_validation_2026-10-17/weight_reference_comparison_deployment_v1.json` に保存した。
低ノイズの12条件、固定prior、fine/coarse ladder、初期化候補、seed stage 150〜155と容量測定の順序を [低ノイズ実行準備](tile_low_noise_plan_2026-10-18_ja.md) に記録した。
低p専用driver・その受入・capacity jobは未実施であり、この仕様を本番完了や確定ETAとは扱わない。
08:00 JSTの実観測では265209・265210とcoordinatorが稼働し、trace markerは57,552件・27,317件だった。
計2ノードを維持し、実行中bundleの変更・追加qsub・commit・pushは行っていない。

## 2026-10-18 05:53 JST時点の更新

固定sourceとmanifestからreference 1,248、anchor 768、MCMC初期化190,464、sampling 190,464の計382,944 seedを列挙し、cohort間を含め重複0件を確認した。
回収済みcase 0・1・3の576 anchorについて、記録seedが各case/replicateの予定値に一致することも確認した。
referenceの記録seedについては、archiveとsummaryに結び付いた既存の全chunk監査を使用した。
未完了caseを含む予定seedの検査であり、全sampling artifactの記録seedを確認した結果ではない。
bootstrap・計時用namespaceは今回の範囲外で、seedの一意性を乱数列の統計的独立性の証明とは扱わない。
Windowsで10.73秒の照合を実行し、結果・再現script・環境を `data_tile_validation_2026-10-17/seed_namespace_audit.json`、`audit_seed_namespaces.py`、`seed_namespace_environment.json` に保存した。
05:53 JSTにcoordinatorと265209・265210は稼働し、trace markerは31,776件・12,562件だった。
計2ノードを維持し、sampling完了・BAR解析・被覆校正は未完了で、追加qsub・commit・pushは行っていない。

## 2026-10-18 05:49 JST時点の更新

tile72-bitとtile288-bitはsampling継続中だが、その前段で完了した各192 anchorを別archiveへ回収し、全payload hash・identity・固定manifestを照合した。
全replicateの記録seed・固定16,384試行・Problem hash・countから再計算した推定値とWilson区間・phase summaryの一致を確認した。
各3,145,728試行で、tile72-bitは1,838,748失敗、tile288-bitは2,114,117失敗、task失敗と0失敗countのreplicateはいずれもなかった。
これは物理sampling p=.1、decoder priorがそれぞれ.03と.05のanchorであり、target pの独立referenceではない。
各BAR replicateの独立anchorを維持し、監査用に合算した推定値で置き換えない。
元の物理誤り列と完全なdirect_mc RNG metadataは保存されていないため、独立なraw試行再集計・再復号とは扱わず、sampling pとRNG呼出しは固定source/manifestによる確認と区別する。
原summary・転送検証・監査結果は `data_tile_validation_2026-10-17/production_anchors-0.json` / `production_anchors-1.json` と対応する `production_anchor_archive_verification-*` / `production_anchor_audit-*` に保存した。
回収元の不変性とarchive hashは `production_anchor_recovery_01.json` にある。
05:49 JSTにcoordinatorと265209・265210は稼働し、trace markerは31,008件・12,160件だった。
計2ノードを維持し、samplingの完了・BAR解析・bias/被覆校正は未完了で、追加qsub・commit・pushは行っていない。

## 2026-10-18 05:28 JST時点の更新

計時artifactの読込みと、前回の精度・費用集計を接続した。
固定manifest・native preflightと実行intent・全taskのidentityとJSON/NPZ hash・summary・seed/model metadata・独立referenceを照合する。
失敗taskの費用や選択未達を残し、元job全体のphase時間は条件別に按分しない。
関連36件がWindowsで28.04秒、Linuxで2.74秒で通り、最も長いWindows testも25.51秒だった。
不変bundle `20261018-tile-timing-comparison-v1` に配置し、既存MC v3の両manifestとの一致も確認した。
今後のBAR計時はこの新bundleで準備し、MC計時は準備済みv3を使用する。
実計時artifactへの適用・比較ジョブの容量測定とqsub・独立精度と時間比の評価は未実施である。
本処理のhashとmetadata照合を、全物理状態の再復号や選択元校正の再解析とは扱わない。
05:28 JSTにcoordinatorおよび265209・265210の稼働を確認し、trace markerは26,880件・9,882件だった。
計2ノードを維持し、追加qsub・commit・pushは行っていない。

## 2026-10-18 05:16 JST時点の更新

独立計時cohortの全replicateから精度と費用を比較する集計の中核を追加した。
MC・BARの双方が有限reference区間全域で経験的精度基準を満たす場合だけ平均task wall・CPU時間の比を出し、失敗taskの費用と時間欠測を保持する。
BAR計時で未収集の混合診断は未取得として数え、良好な診断や名目被覆の確認と扱わない。
短い実MC recordの入力を含め関連32件がWindowsで1.73秒、Linuxで0.47秒で通った。
不変bundle `20261018-tile-timing-metrics-v1` に配置し、証跡は `data_tile_validation_2026-10-17/timing_metrics_deployment_v1.json` にある。
実計時artifactを読み込んで監査するadapterと、実測への適用は未完了である。
05:16 JSTにcoordinatorと265209・265210の稼働を実確認し、trace markerは24,640件・8,656件へ増加した。
既存の計2ノードで計算中であり、追加qsub・commit・pushは行っていない。

## 2026-10-18 05:07 JST時点の更新

MC計時の新規runは既存task・summary・実行intentを拒否し、保存artifactの読み込み時間を新規計算のphase時間として使えないようにした。
本計測の資源見積もりは全容量taskのJSON/NPZ hashとidentity、summaryとの一致、metadataのdigestとsampling p・RNG entropy、native preflightとcompute実行の結合を要求する。
小仕様・受入失敗・実装の順に進め、関連59件がWindowsで22.99秒、Linuxで9.40秒で通った。
新しい `20261018-tile-mc-timing-v3` でmanifest作成、login node上の実native preflightとcapacity dry-runを確認した。
今後のMC計時はv3を使用し、証跡は `data_tile_validation_2026-10-17/mc_timing_deployment_v3.json` に保存した。
これは短い実MCと合成容量cohortによる検証で、実容量測定・本計測・同精度比較は未実施である。
05:07 JSTに実processとPBSでcoordinatorおよび265209・265210の稼働を確認し、trace markerは22,799件・7,633件だった。
計2ノードを維持し、追加qsub・commit・pushは行っていない。

## 2026-10-18 04:49 JST時点の更新

targetの失敗条件付き平均weightを独立MC referenceと比較する追加集計を実装した。
全replicateの欠測・診断未定義を保持し、平均差・reference点に対するRMSE・独立replicate間SE・referenceのchunk delta SEを区別して保存する。
同じtraceを使うladder・BAR誤差法別に重複集計せず、weight観測量の誤差をBAR論理エラー率の誤差とは扱わない。
短い実tile traceと保存解析diagnosticの平均一致を含む13件がWindowsで2.61秒、Linuxで1.42秒で通った。
不変bundle `20261018-tile-weight-comparison-v1` に配置し、使用法は事前計画、証跡は `data_tile_validation_2026-10-17/weight_comparison_deployment_v1.json` に保存した。
本校正への適用は未実施で、metadataの照合だけで元traceやACF配列の全件監査を済ませたとは扱わない。
04:49:31 JST時点でcoordinatorと265209・265210は稼働し、trace markerは19,376件・5,760件だった。
各1ノードの計2ノードを維持し、sampling summaryとBAR校正の完了を待っている。

## 2026-10-18 04:23 JSTの稼働確認

実process表とPBSでcoordinator PID3756042、265209・265210の稼働を確認した。
04:22:07から04:23:07の約1分でtile72のtrace markerは14,080から14,238へ、tile288は2,837から2,925へ増加した。
各1ノードの計2ノードを維持し、controllerもnode budgetを理由に追加投入を待っている。
両caseのsampling summaryは未生成で、stderrも共有先にまだ存在しないため、エラーなしや科学的校正の完了は主張しない。
これは停止や再投入が必要な状態ではなく、実稼働と出力増加を確認した待機である。
証跡は `data_tile_validation_2026-10-17/verified_wait_2026-10-18_0423.json` に保存し、既存ジョブ・条件・seedを変更していない。

## 2026-10-18 04:20 JST時点の更新

全cohortの相対精度から独立計時候補を選ぶ固定規則と処理を追加した。
全192点が取得でき、reference区間全域で経験的相対RMSEが目標以下の条件から、予定step数と固定tie規則で候補を選ぶ。
診断不良・区間未取得・被覆も保持し、最速設定・推奨設定・独立精度確認とは扱わない。
候補なしの場合もunmetとして全4case×2精度の8行を保存し、入力・再集計・規則・sourceのhashを結び付ける。
関連30件はWindowsで2.14秒、Linuxで0.99秒で通り、不変bundle `20261018-tile-selection-v1` に配置した。
受入は合成cohortと保存raw rowsを用いたもので、実校正への適用・設定選択は未実施である。
詳細は [計算効率の計画](tile_time_to_accuracy_plan_2026-10-17_ja.md)、証跡は `data_tile_validation_2026-10-17/timing_selection_deployment_v1.json` にある。
04:20:15 JST時点でcoordinator PID3756042と265209・265210は実稼働し、各1ノードの計2ノードを維持していた。
case0/1/2のsampling summaryはまだなく、全件監査・BAR解析・被覆校正と独立計時は未完了である。

## 2026-10-18 04:15 JST時点の更新

単独BAR計時にcase別分割と専用qsub submitterを追加し、case分割後も元のseed・全選択結果・192 replicateを保持するようにした。
capacityは独立96 replicateで測定し、全artifactとcompute nodeのnative証跡を照合して本計時の時間・memoryを見積もる。
資源測定前のcapacity要求は1ノード96 CPU・340 GiB・24時間の暫定上限で、実測値ではない。
coordinatorとの競合、2ノード超過、欠落・再利用を含む不完全な資源測定、qsub応答不明時の再投入を拒否する。
関連42件がWindowsで12.47秒、Linuxで8.49秒で通り、新しい不変bundle `20261018-tile-bar-timing-v2` に配置した。
単一threadを明示したlogin nodeのnative profile照合も通った。
最初のthread指定なしprobeの拒否も保存し、指定後とのcanonical差がthread環境変数だけであることを確認した。
実際の選択設定・capacity・計時本番・同精度の比較は未実施で、受入の資源・投入試験は合成データと模擬qsubによる。
詳細と再現手順は [計算効率の計画](tile_time_to_accuracy_plan_2026-10-17_ja.md)、証跡は `data_tile_validation_2026-10-17/bar_timing_deployment_v2.json` にある。
04:15:09 JSTの実process・PBS確認ではcoordinatorと265209・265210が稼働し、要求2ノードを維持していた。
case0/1/2のsampling summaryは未生成で、BARの全cohort解析・混合と被覆の校正は未完了である。

## 2026-10-18 段階別decoder確認

保存済みの環境間不一致1状態について、BP最終LLR・hard decision・OSD-0は両環境で一致し、X側のOSD-Wだけが26ビット異なった。
両correctionは重み22でsyndromeを満たすが、logical predictionが5ビット異なり、Windowsでは成功、固定Linuxでは失敗となる。
原因と頻度は未確定で、単一反例から論理エラー率差・BAR biasを推定しない。
同梱Cython sourceのraw hash差は改行正規化で解消した。
新probeの受入3件はWindowsで2.47秒、Linuxで1.72秒で通り、実測・比較・source照合を `decoder_stages_validation.json` に保存した。
詳細は [環境間差の記録](tile_decoder_platform_2026-10-17_ja.md) にある。
04:07 JST時点で265209・265210はともにR、各1ノード96 CPUで、coordinator PID3756042も稼働していた。
weight stratified本番はv4の独立配分・実行計画まで準備済みで、coordinatorと競合する投入は行っていない。
全件数値監査・BAR解析・被覆校正と層別reference値の取得は引き続き未完了である。

## 2026-10-18 03:56 JST時点の稼働確認

待機していた265210（tile288 bit-flip）が03:53:40 JSTに開始し、265209（tile72 bit-flip）と合わせて2ジョブともRとなった。
各1ノード・96 CPUを使用し、coordinator PID3756042も実process表で稼働を確認した。
約80秒の間にtile72のtrace markerは8,791から9,056へ、tile288は0から96へ増加した。
両caseともanchor markerは192件でanchor summaryが存在し、sampling summaryはまだ作成されていない。
これらは処理進行の観測であり、全件の数値監査・BAR解析・校正の完了ではない。
観測時刻・PBS状態・資源使用・marker件数・controller実processは `data_tile_validation_2026-10-17/live_jobs_2026-10-18_0356.json` に保存した。

## 2026-10-18 03:51 JST時点の更新

完了pilotの全64 prior比較についてpairedな成功/失敗の4セル表、失敗率差、判定不一致の質量、全比較を含む保守的な同時信頼範囲を保存した。
physical p=.1でprior .1→.0001としたtile288-bitは成功→失敗16例・失敗→成功7例、depolarizingは7例・8例だった。
判定が変わった割合は11.98%・7.81%だが、失敗率の純差は+4.69・-0.52百分率点で、相殺を区別する必要がある。
これらは既存の192誤り/条件に対するpilot効果量で、BAR biasや低noiseの相対誤差ではない。
関連18件がWindowsで1.96秒、Linuxで0.98秒で通り、実pilotの派生結果も両環境で照合した。
詳細は `tile_decoder_prior_effect_2026-10-18_ja.md` と `data_tile_validation_2026-10-17/prior_effect_validation.json` に保存した。
265209 R・265210 Q・coordinator PID3756042の稼働を確認し、要求2ノードを維持した。

## 2026-10-18 03:44 JST時点の更新

全固定cohortの相対RMSEをreference区間全体で評価する追加集計を実装した。
分母の変動も含めた内部最小点・端点最大を求め、未取得seed・0下端・数値範囲外を経験的精度達成と扱わない。
区間未取得と診断未定義は従来の分母のまま別に記録する。
関連26件がWindowsで0.85秒、Linuxで0.19秒で通り、新bundle `20261018-tile-precision-assessment-v1` に配置した。
本校正の全件BAR出力への適用と設定選択は未実施で、経験的な判定から母RMSEや95%被覆を保証しない。
265209はR、265210はQ、coordinator PID3756042は稼働中で、要求計2ノードを維持している。
詳細は `tile_time_to_accuracy_plan_2026-10-17_ja.md` と `data_tile_validation_2026-10-17/precision_assessment_deployment_v1.json` に保存した。

## 2026-10-18 03:39 JST時点の更新

単独BARの計時driverを追加し、短い実tile traceを含む関連32件がWindowsで9.46秒、Linuxで7.57秒で通った。
選択設定ごとに新しい独立anchorとtraceを作り、構築・初期化・sampling・compact検証・解析のwall/CPUを分けて記録する。
既存traceの時間按分を行わず、sampling失敗やanchor未取得を分母から除かない。
新bundle `20261018-tile-bar-timing-v1` を配置してlogin node native照合も通ったが、比較設定の選択・独立精度確認・計時本番の投入は未実施である。
265209はR、265210はQ、coordinator PID3756042は稼働中で、要求計2ノードを維持している。
詳細は `tile_time_to_accuracy_plan_2026-10-17_ja.md` と `data_tile_validation_2026-10-17/bar_timing_deployment_v1.json` に保存した。

## 2026-10-18 03:32 JST時点の更新

265209（tile72 bit-flip）は実行中、265210（tile288 bit-flip）はCPU資源待ちで、coordinator PID3756042も稼働を確認した。
待機中を含む要求node数は計2である。
完了済みtile288 depolarizingに対する全trace監査の資源計測wrapperとqsub submitterを追加した。
固定96 groupの資源計測後に全768 groupの本監査を別rootで行い、sampling失敗と監査失敗を区別して保存する。
関連テストはWindowsで41 passed・7.36秒、Linuxで41 passed・2.35秒だった。
新v2 bundleでcase3のplan、実sampling summaryを使うcapacity dry-run、login node native照合まで確認した。
資源計測・本監査のqsubとcompute node上の確認は未実施で、controllerに競合する追加投入は行っていない。
仕様と実行記録は `tile_trace_audit_execution_2026-10-18_ja.md` と `data_tile_validation_2026-10-17/trace_audit_execution_deployment_v2.json` に保存した。
BARのbias・被覆・混合・同精度までの時間比較と最終報告は引き続き未完了である。

## 2026-10-18 03:11 JST時点の更新

tile288・depolarizingの本校正sampling（265200）は終了コード0・PBS walltime7時間16分10秒で完了し、30,720 traceは全て成功記録だった。
sampling phaseは26,049.337秒で、anchor phaseや解析時間を含まない。
30,720 traceと192 anchorを回収し、全30,912 artifactのidentity・payload hashを照合した。
全件の数値trace監査・BAR解析・混合と被覆の評価は未実施で、sampling完了を科学的校正の完了と扱わない。
層別pilot（265201）も終了コード0・PBS walltime13秒で完了し、1,536 task・721,024試行を回収した。
192層すべてのraw乱数再生成・weight/alphabet・count・seed・metadataと同一状態のfailure label整合性を監査し、本番driverのpilot入力検査も通った。
最大worker RSSは89.5625 MiB、最大task時間は2.301052秒で、資源配分に必要な記録が揃った。
pilotは未測定weightを含むため論理エラー率referenceとして使わず、本番の独立予算固定とqsubはこれから行う。
controllerは続いてtile72-bitを265209、tile288-bitを265210としてqsub投入し、最新確認はそれぞれR・Qで要求計2ノードだった。
終了記録・archive照合・pilot監査・投入台帳は `data_tile_validation_2026-10-17/case3_weight_pilot_completion.json` と同階層の索引に保存した。

同日、監査済みpilotだけから層別referenceの独立本番予算を固定し、16条件・97,857,608試行・23,938 chunkの計画を保存した。
4,000,000パターン以下の層は全列挙し、他の層も0失敗を理由に省略しない。
pilot平滑化率と費用を使う配分の関連受入はWindowsで30 passed・2.94秒、Linuxで30 passed・1.11秒だった。
全条件の未評価binomial尾部は1e-14以下だが、これは低noiseでの相対精度を保証しない。
v4 bundle上で実pilotによるplan、login node native照合、配分JSONのbyte一致とdry-runを確認した。
資源要求は1ノード・96 CPU・32 GiB・4時間30分で、本番投入・compute node照合・reference値の取得は未実施である。
既存coordinatorと競合する手動投入は行わず、今後の層別本番には `20261018-tile-weight-reference-v4/runs/reference` を使う。

## 完了

基準HEAD d78377eから新しい計画・seed・bundleで開始した。
小仕様を先に保存し、未実装で受入テストが失敗することを確認してからdriverを実装した。
tile72の全256 X logical組合せ、bit/depolarizingのfailure定義・syndrome整合性・反復/逆順/新instance再現性を受入検査した。
既定ZHと候補ZHSの有限Steane例の正規化・詳細釣合い・stationarity・成分数・自己loopも既存受入で再検査した。
この有限例からtile全体の支持連結性を推論しない。
最初の受入は7 passed・21.09秒、reference集計は2 passed・2.13秒、長trace保存・anchor分散・noise比・node上限は4 passed・2.29秒、解析の有限groupとreference区間の扱いは2 passed・3.24秒だった。

pilotジョブ265196は終了コード0、PBS walltime34秒、96task全て成功した。
ただしtile288のp=.01では両noiseともrejection初期化が各6seedで上限20,000試行に達し、p=.03のdepolarizingでも1seedが上限に達した。
初期化1回を両kernelで共有するpilotなので、chain記録ではそれぞれ12件・12件・2件のinitialization_failedとなる。
これらを別seedで置き換えず、初期化制約として保存した。
全pilotのmarker・物理状態・compact trace・metadataを含むarchiveを回収し、remote/localのarchive SHA-256一致を確認した。
さらにarchive内の96artifactすべてでmanifest・task identity・data/meta両hashを照合し、欠落・重複・破損がないことを確認した。
これは転送完全性の検査であり、別実装による科学的正しさの証明ではない。

pilotの3,072誤りに対し、logical predictionの反復・逆順・新instance不一致、訂正syndrome違反、failure定義不一致はすべて0だった。
一方、tile288-bitのphysical p=.1でpriorを.1から.0001へ変えると、同一192誤りのうち23例で成功/失敗が入れ替わり、失敗数は121から130になった。
tile288-depolarizingの同じphysical条件・physical prior比較では、15例で入れ替わり、失敗数は55から54になった。
depolarizingでは各sectorのpriorをphysical priorの2/3としている。
失敗総数の差が小さくてもfailure集合が同じとは限らず、これらの差をBAR biasの測定値とは呼ばない。
小規模pilotの再現性は、全syndrome・別backend版での決定性の証明ではない。
集計と入力hashは `data_tile_validation_2026-10-17/pilot_decoder_counts.json` に保存した。

未取得を含む全seed集計、archive照合、人工データによる解析容量測定、容量実測に基づく本番qsub driverを追加した。
関連9 test fileの統合受入は23 passed・19.33秒で、最大file内テストは有限Steane列挙の14.05秒だった。
その後、全artifactからの集計と欠落conditionの拒否テストを追加し、集計fileの5 testsが0.92秒で通った。

直接MC referenceのqsub265197は終了コード0・walltime28分38秒で完了し、全81,788,928試行・1,248chunkの回収とhash照合も完了した。
全chunkのseed・実際のRNG・sampling p・符号/decoder/failure metadataを照合し、生countからsummary全項目を再現した。
referenceは有限MCであり、exact真値として扱わない。

| case | target p | 試行数 | 失敗数 | 推定P_any | 標準誤差 |
|---|---:|---:|---:|---:|---:|
| tile72-bit | .03 | 6,291,456 | 270,328 | .04296748 | .00008085 |
| tile288-bit | .05 | 6,291,456 | 182,133 | .02894926 | .00006684 |
| tile72-depolarizing | .03 | 6,291,456 | 189,804 | .03016853 | .00006819 |
| tile288-depolarizing | .05 | 62,914,560 | 185,628 | .002950478 | .000006838 |

区間・環境・PBS最終状態・archive照合・再集計監査はデータ索引に保存した。
条件付きweight平均のchunk間delta MCSEも別監査記録に保存し、その近似を明記した。
このMCSE計算の手計算との受入は1 passed・0.71秒だった。

本校正case 3のanchor phaseは192 replicate全成功で完了し、MCMC本体の終了を待たず、全192 artifactを回収・hash照合した。
各16,384試行、合計3,145,728試行・743,334失敗で、各replicateの失敗数は3,727〜4,005、0失敗・失敗taskはなかった。
physical sampling p=.1、physical decoder prior=.05であり、target p=.05の独立referenceと同じ確率を測っているわけではない。
監査用合算値は.23629951、合算Wilson95%区間は[.23583040,.23676928]だが、各replicateの独立anchorをこの値で置き換えない。
countからの各推定値・Wilson区間、保存seed・Problem hash、全phase summaryを再現し、関連受入は9 passed・0.50秒だった。
各anchorのbinomial delta log-SE寄与は.013735〜.014397で、これはBARに加算されるanchor側の項であり、最終被覆の保証ではない。
phase walltimeは118.14秒、個別direct_mc elapsedの合計は10,843.90秒で、後者をCPU時間とは扱わない。
物理誤り列とdirect_mcの全RNG metadataはanchor artifactに保存されていないため、physical p・RNG呼出しは固定source/manifestに基づく照合と明記した。
監査は元のproduction artifactを変更せず、MCMC本体とcontrollerは引き続き稼働している。

sampling容量測定のqsub265198も終了コード0・walltime3分11秒で完了した。
384task全成功、全artifact回収・hash照合済みで、標本は本校正へ流用しない。
その実測からsampling予測はcase 0/1/2/3の順に8.79/5.54/2.28/8.80ノード時間、合計約25.4ノード時間とした。
これは投入待ちと本解析を含まない外挿であり、完了時刻の保証ではない。

## 実行中・待機中

人工配列での解析容量測定qsub265199は96group全成功、終了コード0・walltime20分14秒で完了した。
全artifactを回収してhash照合し、実測に基づく本解析の資源計画を保存した。
解析予測はcase 0/1/2/3の順に2.63/1.37/.67/1.39ノード時間で、要求walltimeは6/3/2/3時間、memoryは218/98/46/98GBとした。
この人工データの測定値を混合・被覆の結果に使わない。
sampling全件・anchor全件の記録を検査してから失敗を含む解析を投入するcontrollerを追加し、受入はlocal 2 passed・1.02秒、cluster 2 passed・0.42秒だった。
本校正の最初のcase 3（tile288-depolarizing）はqsub265200で実行中である。
投入順は容量実測による予測降順のcase 3/0/1/2とした。
最初の2条件の予測差は約30秒で、実際の混合・精度の良否による選択ではない。
各ジョブは1ノード96CPUで、実行中・待機中を合算して最大2ノードの上限内である。
productionの科学manifest・解析manifest・資源計画・投入台帳を保存した。
配置先、manifest、投入台帳、環境とpilot数値は [データ索引](data_tile_validation_2026-10-17/README.md) にある。

## Weight-stratified referenceの追加

ユーザーの追加指示を受け、RIMCの実装を読み取り専用で調べ、別の[小仕様](tile_weight_stratified_spec_2026-10-17_ja.md)を保存した。
層の全列挙・一様sampling・合成と、0失敗層や省略質量を含めた保守的区間を実装した。
binary/Pauliの全列挙との数値一致、tile72の公開failure判定との一致、pilot保存・再開の受入は6 passed・2.02秒だった。
低weightの訂正を符号距離だけから仮定せず、BP-OSDのtarget priorごとに別の層表を作る。
資源・配分pilotの1,536taskを固定し、qsub265201として投入した。
この時点で空き待ちであり、実測結果は未取得である。
pilotは一部weightのみを扱うため、これをP_L referenceとして用いない。
追加で小標本binomial区間の全count照合と、全失敗率1の丸めによる区間反転の回帰を検査し、丸め境界を修正した。
層別primitiveとpilotの最終受入は8 passed・2.08秒だった。
修正前のweight-pilot-v1はdry-runのみで投入せず、修正済みのweight-pilot-v2を使用する。
pilot回収後の集計に向け、全taskのhash・固定prior・seedと保存状態を照合し、層別count・時間・memoryを再集計する監査を追加した。
同一状態のfailure不整合、欠落・重複・改変を拒否し、失敗taskと計測できないRSSも明示して残す。
受入はlocal 11 passed・1.99秒、clusterのpinned環境で11 passed・1.05秒で、tile72-bit/depolarizingの小さな実pilot artifactも検査した。
監査は別のtile-audit-v1 bundleへ配置し、投入済みジョブのsource・manifestは変更していない。
本pilot 1,536taskの監査はジョブ終了後に行うため、この時点では未実施である。

## 公開APIの利用例

`examples/workflows/tile_capacity_fixed_prior.py` を追加し、tile72/288・bit/depolarizingの4 quick例をseed 7で実行した。
全rungのdecoder同一性とsector priorを保存JSONから照合し、4例すべて成功した。
workflowの受入にも固定priorの検査を加え、1 passed・3.74秒だった。
短いtile72-depolarizing例のBAR 95%区間[.01563,.02815]は独立MC参考区間[.03004,.03030]と交差しなかった。
後の監査で、別のtile288状態についてWindowsとLinuxのBP-OSD判定差が確認されたため、この環境をまたぐ区間比較を同一failure集合の校正として扱わない。
例内の小予算MC区間とは交差するため、短いMCとの区間一致を精度保証としない。
この1seedの結果からbiasや被覆率を推定せず、例の設定を推奨精度設定とは呼ばない。
数値・source hash・再現コマンドと出力archiveのhashはデータ索引に保存した。

## 対応比較の準備

本校正のkernel・初期化・chain数・burn・保存長・ladder・誤差法を一要因ずつ変えた条件対の集計を追加した。
全replicateを照合し、推定値差・対数比・二乗誤差差・被覆の対応差と、reference不確実性を保存する。
診断未定義・区間未取得・sampling失敗を除外せず、推定値差を取得例だけで計算した場合は補助量として分離する。
仕様と受入を先行し、手計算との一致・共有変動の相殺・欠落と重複の拒否・file経由の全条件検査は10 passed・0.49秒だった。
追加driver群の統合検証は71 passed・4.92秒で、ログと対象test一覧を保存した。
本校正の解析完了前なので、実データの対応比較は未実施である。
既存のproduction bundle・manifest・sampling・解析sourceは変更していない。

## 固定ジョブの投入継続

長時間ジョブの完了後に残りの固定samplingと解析をqsubする軽量controllerを別bundleへ配置し、2026-10-17 11:18 UTCに起動した。
投入済みsource・manifest・資源計画をhashで固定し、待機中を含む自分の全ジョブが要求するノード数を毎回確認する。
未投入samplingを既定順で優先し、その後、全sampling・anchorの記録がそろったcaseの解析を投入する。
投入前の意図と投入後の受領を別記録にし、応答不明時は自動再試行しない。
PBSの観測エラーでは同じjob IDを再観測し、既存ジョブを取り消したり再投入したりしない。
controllerと既存submitterの受入はlocal 13 passed・1.31秒、cluster 13 passed・0.55秒だった。
起動時には265200が実行中、265201が待機中で、要求2ノードのため新規投入せず待機した。
controller PIDは3756042で、process表から該当コマンドの稼働を確認した。
60秒間隔・最大72時間で動き、controllerの終了時も既存ジョブは取り消さない。
このcontrollerが生きている間は、同じproductionの手動qsubと別controller起動を行わない。
生存確認にはPIDのprocess表とコマンドを確認し、process.jsonやstatus.jsonだけを生存証拠としない。
各投入台帳と観測イベントはcontroller配置先へ継続保存される。
controllerは固定済み4caseのsamplingと解析までを扱い、層別の本番予算を選択したり、研究上の完了判定を行ったりしない。

## 支持・初期化の確認

tile72/288のbit/depolarizingで、stabilizerのrow spaceがsyndrome・logical mapを同時に保存する差分空間と一致することをrankで確認した。
対応するrankは32/140/64/280で、4caseの受入は4 passed・2.23秒だった。
同じsyndrome・残余logicalのfiber内をstabilizerでつなげることと、全failure支持の連結性・混合・被覆を区別した[説明と根拠](tile_kernel_support_2026-10-17_ja.md)を保存した。
source確認により、depolarizingのlogical初期化は偶数replicateがX basis、奇数replicateがZ basisとなることを明示した。
全192 replicateの主結果を再現してから各96 replicateの補助集計を行う、独立した後処理を追加した。
失敗・未定義・区間未取得を各層の分母へ残し、rejection条件の同じ偶奇区分はX/Z初期化と呼ばず対照として保存する。
層別の受入は6 passed・1.30秒で、反対向きのbiasの平均による相殺、元replicate IDの保持、実際のtile72/288初期化関数との一致、主summaryの再現と改変拒否を確認した。
追加driver群の統合は90 passed・6.56秒で、以前の71-testのログを上書きせず新しいログへ保存した。
層別の実データ評価は本解析の完了後に行うため未実施であり、production/coordinatorの固定bundleには変更を加えていない。

## 同精度の計算時間比較

BAR本校正の結果を見る前に、相対RMSE 20%・10%を基準とする[時間比較計画](tile_time_to_accuracy_plan_2026-10-17_ja.md)を保存した。
既存の独立referenceの99.9%参考区間下端を使い、直接MCの試行予算を64単位で切り上げて固定した。
各192 replicate、全4case・2精度で10,358,784試行とし、既存とは別のseed stage 121を予約した。
有限binomial分布のMSE、reference範囲、固定予算への切上げの受入は7 passed・0.40秒だった。
この予算は未実行であり、目標精度や時間の優位性を確認した結果ではない。
直接MCの計時driverを実装し、実際のRNG・sampling p・decoder metadata、構築時間・MC経過時間・task CPU時間を保存するようにした。
本計測192 replicateのstage 121と、capacity用96 replicateのstage 122を分離し、受入は予算と合わせ14 passed・2.38秒だった。
固定予算での計測・capacity測定・追加qsubは未実施である。
計時用submitterも別bundleへ配置し、Windowsの21 passed・2.75秒、Linuxの21 passed・1.69秒とcapacity dry-runを確認した。
容量測定は独立stage 122・5,179,392試行、本計測はstage 121・10,358,784試行で、各manifestを保存した。
稼働中controllerと要求2ノードを検出しており、追加ジョブはまだ投入していない。
BAR設定の選択・独立確認と単独計時は本校正の結果を踏まえて行い、既存traceの長さ比による時間外挿を実測と呼ばない。
MC計時driverにも固定native profileと再現状態の照合を追加し、worker開始前に不一致を拒否する。
関連受入はWindowsで24 passed・9.34秒、Linuxで24 passed・1.75秒だった。
新しい `20261017-tile-mc-timing-v2` bundleでmanifest作成、login node上の実preflightとcapacityのdry-runを確認し、今後の投入先をv2とする。
既存controllerが稼働中のため追加qsubは実施せず、compute node上の照合と計時実測は未実施である。

## 残り

層別reference本番用のchunk処理と条件別合成を追加し、既存の層別primitiveと合わせ14 passed・16.15秒だった。
全列挙と独立MCを区別し、固定seed stage 130・連続するweight層・固定試行数を保ち、raw stateの再生成とcount照合を行う。
失敗chunkがあればreferenceを未取得にし、成功chunkだけで完全なreferenceを作らない。
pilot監査・固定配分・native preflightを照合するplan/run driverも実装し、chunk処理との関連受入は20 passed・21.99秒だった。
driverの入力と実行順序は合成fixture・模擬workerで検査したもので、実pilotの成功や本番referenceの取得を示す結果ではない。
driverを独立bundleへ配置し、Linuxで層別primitiveを含む27 passed・6.66秒とlogin node上のnative preflightを確認した。
実際のpilot監査を受けた予算選択、compute node上のpreflight、resource計画とqsubは未実施である。
層別reference driverのplan/runで実probe・hostname・PBS_JOBID・照合時間の証跡を別々に保存し、run証跡をchunk summaryと最終summaryからhashで参照するよう補った。
関連受入はWindowsで27 passed・17.24秒、Linuxで27 passed・6.87秒で、新しい `20261017-tile-weight-reference-v2` へ配置した。
login node上の固定native profileとの一致も確認し、今後の本番準備先をv2とする。
実pilotに基づくplan/runとcompute nodeでの証跡取得は未実施である。

実traceの監査で[BP-OSDの環境間差](tile_decoder_platform_2026-10-17_ja.md)を1状態について確認した。
同じpackage版・source/Problem hash・単一thread設定でも、Windowsではsector 0、固定Linux環境では保存どおりsector 94となった。
それぞれの環境では10反復・新規4instanceで一致したが、差の頻度と論理エラー率への影響は未評価である。
校正結果とreferenceは生成元Linux環境に結び付け、native binary hashを含む環境情報と再現状態を保存した。
独立referenceのnative ldpc binaryも本校正環境と一致することを確認した。
全件監査にnative環境と再現状態の一致を要求するguardを追加し、関連27 passed・5.38秒だった。
guard付き版を独立bundleへ配置し、Linuxで27 passed・1.92秒とlogin node上の実preflightを確認した。
生成元Linuxで固定2trace・計36,000保存値の構造検査と38checkpoint・2初期状態の再復号を確認したが、全件監査ではない。

本校正のcase別archiveについて、全trace・anchor・解析groupの欠落、identity、payload hashとsampling/analysis/referenceの対応を検査する回収手順を追加した。
関連受入は13 passed・1.32秒で、固定manifestからの期待集合を実際のsampling・analysis生成関数とも照合した。
実ジョブの全archive回収と科学的な数値監査は未実施であり、回収検査の受入成功を本校正の完了とは扱わない。
数値trace監査driverを追加し、全compact値の形・値域、記録seed・config・初期状態、全checkpointの再復号を検査するようにした。
実際の4caseの短いtraceと意図的な改変で、関連26 passed・5.01秒を確認した。
失敗sampling taskを分母から除かず、監査結果の再読込み時にも元artifactのmarkerとpayloadを再照合する。
未保存の中間物理状態やMCMC乱数軌道全体の再現を確認したとは扱わず、全件監査の資源測定・qsub実行は未実施である。
compute node上のnative preflightも実ジョブの開始時に確認し、login node上の確認をcompute nodeの検証済み結果とは扱わない。

残りcaseの192 replicateのsampling・MC anchorと本解析を、2ノード上限を守って順次qsub投入する。
解析は4chainと最大chain数、複数長さ・burn・ladder・誤差法、両kernel・両初期化を対応比較し、失敗・未定義・区間未取得も残す。
混合・bias・被覆・計算効率を評価し、必要な提案改善と追加校正を行う。
weight-stratified本番の予算固定と独立reference、低noiseへの拡張、再現可能な利用例、適用限界、全件監査・最終報告は未完了である。
公開既定、RIMCを変更せず、commit・pushは実施していない。

2026-10-18、層別referenceの資源見積もりとqsub submitterを追加し、関連受入はWindowsで39 passed・10.43秒だった。
完全なpilot監査と固定manifestを再確認し、未測定weightの外挿と合成用予備時間を明示する。
実プロセスのcoordinator稼働・最大2要求ノード・qsub前のintentを検査し、応答不明時は自動再投入しない。
実pilotの監査・予算固定・資源見積もりと、このsubmitterのLinux配置・実投入は未実施である。
投入済みジョブと既存bundleは変更していない。
その後、追加submitterを `20261018-tile-weight-reference-v3` へ配置し、Linuxで39 passed・7.24秒とlogin node上の実native probe一致を確認した。
今後の層別reference準備先はv3とし、実pilotからの予算固定・資源要求・compute nodeのpreflight・実投入は引き続き未実施である。
