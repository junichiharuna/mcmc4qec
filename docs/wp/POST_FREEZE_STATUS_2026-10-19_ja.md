# 公開候補固定後の状態：2026-10-19 21:35 JST

GitHub experimental版の公開準備は、配布物・利用例・日英文書・local検証まで揃っている。
今回の公開候補のcommit・push、そのcommitに対するremote CI、tag・Release・公開操作は未実施である。
長期の数値検証は未完了であり、ソフトウェアの公開準備完了と区別する。

## 公開候補

固定candidateは915ファイル、treeは`7ae747cc7fda60095d73d119dc0d0eb6648aea9d`である。
そのsource ZIPとwheelは変更していない。
[公開準備記録](experimental_release_readiness_2026-10-19_ja.md)と[その後の確認](experimental_release_followup_2026-10-19_ja.md)を保持し、過去時点の未完了記述をこのcheckpointで補足する。
直近に確認したGitHubの成功CIは旧remote main `6f7528645ddf988ed8008bad5c81e321aa2aaaf8`に対するものであり、今回の固定candidateのCI成功として扱わない。
local HEADは`d78377e0f965f6aacc8a5e5b610c9153ebff9c3b`、実indexのstaged fileは0だった。

DGX SparkとLabo PCでも同じwheelを検証し、各2308 passed・5 skippedを確認した。
DGXの初回setup失敗とLaboの初回時間制限超過は隠さず保持し、修正した実行環境・並列数で全suiteを再確認した。
詳細は[追加PCの検証記録](personal_hosts_validation_result_2026-10-19_ja.md)にある。

source固定後の環境差比較を含む[日英の追記と追加ZIP](experimental_platform_supplement_2026-10-19_ja.md)を準備した。
追加ZIPは約20MBで、展開した配布物だけから16条件・1048576対の集計JSON全項目の一致を確認した。
最終添付予定はsource ZIP・wheel・platform validation ZIP・combined SHA256SUMSの4ファイルである。
全tile研究のraw datasetを公開準備済みとするものではない。

## 数値検証

| 対象 | 状態 | 根拠と限界 |
| --- | --- | --- |
| 主4条件 | 固定cohortの正式比較完了 | [主報告](tile_validation_report_2026-10-18_ja.md)に混合診断と被覆不足を記録しており、名目95%を保証しない。 |
| tile72 depolarizing、p=.01/.003/.001 | 低ノイズ3条件の正式比較完了 | case2 target0/1/2の各reportを読み、192 replicate・67584行を確認した。 |
| tile72 bit-flip、p=.01（C0T0） | 正式比較・回収完了 | [復旧後の結果](low_c0t0_recovered_result_2026-10-19_ja.md)に、672 group再利用と96 group復旧の履歴を保持する。 |
| tile72 bit-flip、p=.003（C0T1） | sampling集約とtrace監査を受理、BAR解析中 | [解析投入](low_c0t1_bar_dispatch_2026-10-19_ja.md)、[監査完了と後続手順](low_c0t1_trace_completion_2026-10-19_ja.md)を参照する。 |
| tile72 bit-flip、p=.001（C0T2） | anchor終了、sampling partition 0実行中 | [投入記録](low_c0t2_generator_dispatch_2026-10-19_ja.md)に実qsubと資源を保存した。 |
| その他の低ノイズ条件・独立計時 | 未完了 | 最終設定選択と同精度到達時間の評価は、必要な全条件の終端・監査後に進める。 |

低ノイズ正式比較は4/12条件まで完了しており、残り8条件は未完了として扱う。
有限MC・WSS referenceを厳密な真値として扱わず、独立referenceのない領域の設定間整合性を精度や被覆の保証として扱わない。
BP-LSD・BeliefFind・Union-Findの接続と小規模検証は候補に入っているが、それらのBAR精度・被覆・速度順位の校正完了は主張しない。

## 稼働中の資源と次の処理

21:35 JSTのqstat照会では、265334（C0T1 BAR）と265338（C0T2 sampling）はともにR・run_count 1だった。
両jobは各1要求nodeであり、最大2nodeを維持している。
BARの完了markerは先行観測で96/768 groupであり、7時間30分の上限以内に終わるかは未確定である。
正常終了時は通常の完了受理・BAR集約・trace/referenceとの最終比較へ進む。
時間上限で失敗した場合に備え、[復旧helperの配置](low_c0t1_recovery_preparation_2026-10-19_ja.md)と[復旧後の完了受理](low_c0t1_recovery_completion_preparation_2026-10-19_ja.md)を準備したが、復旧jobは未投入である。
曖昧な応答や観測timeoutを理由に、実行中jobを再投入しない。

## 追加PCで分かったこと

[固定予算の環境差比較](paired_platform_mc_result_2026-10-19_ja.md)では、同じ物理誤り状態に対するfailure判定不一致を観測した。
主4条件の不一致率は約1.63%、1.47%、1.53%、0.0137%で、LER差の区間は全16条件で0を含んだ。
これは同じfailure集合や同じLERの証明ではなく、OS・architecture・native binaryの効果は未分離である。
今回の追加PCの結果を既存クラスタcohortへ合算していない。

[BAR後処理の分担調査](portable_bar_postprocessing_review_2026-10-19_ja.md)では、数値部分が保存済み観測量を使い、再復号を呼ばないことをsourceで確認した。
samplingと後処理の環境を分けて記録する実装と実環境での一致検証が必要であり、現在の固定経路に未検証の結果を差し込んでいない。
GPU専用実装は将来課題とし、今回追加していない。

## 22:01 JSTの追加進捗

[後処理の移植結果](portable_bar_postprocessing_result_2026-10-19_ja.md)のとおり、両PCで実traceの短いwindowの一致を確認し、C0T2の初回44 groupの全window後処理を開始した。
DGXは20 worker、laboは24 workerの生存とCPU使用を実観測し、クラスタの2jobも引き続きRだった。
元のsampling failure集合を保存したまま処理し、新たな復号結果を混ぜない。
全groupの処理・sampling終端・trace監査・referenceとの集約は未完了であり、正式比較の完了数は4/12のままである。

22:14 JSTには[回収helperの準備](portable_bar_collection_preparation_2026-10-19_ja.md)を終え、関連44テストと実parity出力の構造確認を通した。
両PCの終端gateは未完了を返しており、全window結果の回収はまだ実施していない。

22:25 JSTには[次batchの事前配置と引継ぎ](portable_bar_batch1_handoff_2026-10-19_ja.md)を準備し、controller PID 34240の稼働を確認した。
次の44 groupは配置済みだが未起動で、現batchの終端・回収検証後にhostごとに進める。
このcontrollerがbatch 0の回収とbatch 1の起動を担当しているため、別processから同じ操作を重複実行しない。

その後、[最初の全window結果](portable_bar_first_full_group_2026-10-19_ja.md)としてDGXの1 groupの全88設定・診断2328件・ACF2328配列の構造とprovenanceを確認した。
区間未取得は0だったが、全88行に診断flagがあり、48行は未定義診断を含んだ。
これは1 groupの途中結果であり、全seedのbias・被覆やbatch全体の受理を意味しない。

22:38 JSTには[DGX batch 0の全20 groupを回収](portable_bar_dgx_batch0_result_2026-10-19_ja.md)し、全1760行・診断46560件と生データの構造・hash・provenanceを確認した。
区間未取得は0行だったが全1760行に診断flagがあり、1044行は未定義診断を含んだ。
DGXは次の20 groupへ自動的に進み、親PID 519556・20 workerのCPU使用を確認した。
後続batchの回収には、起動済み実行intentへ結び付けた別transportを用意した。
全768 group・全192 replicateの科学集約を終えていないため、正式比較の完了数は4/12のままである。

22:54 JSTには[samplingの生成順に合わせたbatch 2](portable_bar_batch2_preparation_2026-10-19_ja.md)を両PCへ配置した。
固定したhost割当と全groupを維持し、推定値を見ずに未予約の完了入力から選ぶ。
DGXのbatch 1→2はcontroller PID 40396が担当し、既存PID 34240によるbatch 0→1の処理を重複実行しない。
両hostのbatch 2は未起動であり、実計算の完了を主張しない。

23:08 JSTまでに[固定候補のcommit・push](experimental_commit_push_2026-10-19_ja.md)を完了し、remote mainが`0d509c5`であることと検証済みtreeとの一致を確認した。
対象commitのCIは起動済みで、repositoryの公開切替とrelease作成は未実施である。

23:13 JSTには[DGX batch 1の回収](portable_bar_dgx_batch1_result_2026-10-19_ja.md)とbatch 2の起動を確認した。
回収済みは計40 groupであり、全768 groupの集約、trace監査、referenceとの結合は引き続き未完了である。

その後、初回CIのoptional suiteが5分制限に達したため、全testを保持した4分割へCI workflowだけを修正し、`47ef1b6`をcommit・pushした。
[修正後のremote CI](experimental_remote_ci_2026-10-19_ja.md)は全12 jobが成功した。
Python 3.11／3.12のoptionalは各2306 passed / 7 skippedで、全146ファイルの実行とcaseの重複がないことを回収したJUnit・inventoryから確認した。
最新配布物は`assets_with_platform_v2`、source exportは`git_export_v5`であり、wheel・数値計算コード・科学データは旧候補と同一である。

23:29 JSTには[batch 3の配置とDGX側の引継ぎ](portable_bar_batch3_preparation_2026-10-19_ja.md)を準備した。
予約済みは重複なしの176 groupであり、実完了・回収済みの40 groupと区別する。
全cohortの最終結合と追加の全設定移植比較は未実施で、受入条件を別の小仕様へ記録した。

23:35 JSTには[全設定での移植照合](portable_bar_full_parity_launch_2026-10-19_ja.md)を両PCで開始し、remote PIDとCPU使用を確認した。
事前指定したC0T0の1 groupについて、元planの88設定を保存済みcluster結果と比較する。
全設定の一致はまだ未確認で、受入テスト21件の成功と実測結果を区別する。

23:40 JSTには[cohortの途中index](portable_bar_cohort_inventory_2026-10-19_ja.md)を実回収済み2 archiveへ適用した。
回収済み40 group・3520設定行と、未回収728 group・64064設定行を区別して全予定分母を保持した。
indexの受入テストは21件成功したが、最終trace監査・reference結合のreaderと正式比較は未完了である。

23:47 JSTには[group単位のtrace監査への結合](portable_bar_audit_bridge_2026-10-19_ja.md)と、解析が失敗した場合の未取得行を実装した。
保存artifactを使う小fixtureと有限のsummary例を含む11テストが20.81秒で通った。
全cohortのPBS・native環境・anchor・referenceをまとめて検証する最終readerは未統合であり、正式比較の完了を意味しない。

10月20日00:04 JSTの[進捗追記](portable_bar_progress_2026-10-20_ja.md)では、DGXの事前指定1群について全88設定の移植照合と、実cohort累計60群の回収・再検証を記録した。
全768群のうち708群は未回収であり、未定義診断・flagged行を除外していない。
最終集計の制御とレポート境界の31テストが成功したが、実archive provider、全sampling、元環境のtrace監査とreference結合は未完了である。
クラスタは既存2 jobの実行を継続し、DGX batch 3とLabo batch 0も実行中である。

続いて[回収archiveのgroup reader](portable_bar_archive_reader_2026-10-20_ja.md)を追加し、27テストとDGX batch 2の実データ20群・1760行の再照合を完了した。
profileの生ファイルhashとcanonical JSONのdigestを別々に検証する修正を含み、初回の拒否ログも保持した。
全cohort providerと元native環境での正式なtrace監査・reference結合は引き続き未完了である。

[最終cohort providerと移植照合gate](portable_bar_final_provider_2026-10-20_ja.md)を実装・接続し、統合44テストと移植照合33テストを確認した。
DGXの実保存artifactでも全88設定の値を再比較した。
全768群の最終context作成、元環境への配置、最終qsub投入と正式なreference比較は未実施である。

00:28 JSTの[配置・回収記録](portable_bar_cluster_stage_2026-10-20_ja.md)では、最終集計用コード26ファイルをクラスタの独立directoryへ配置し、既存venvでCLIとimportを確認した。
最終qsubは未投入であり、既存2 jobを継続している。
DGX batch 3の回収により累計80群・7040行となり、batch 4は起動済みである。
batch 5は固定割当の完了入力が揃わず未予約であり、全768群の最終contextと正式なreference比較は引き続き未完了である。

00:34 JSTには固定割当の入力が揃い、[DGX batch 5の配置と引継ぎ](portable_bar_batch5_preparation_2026-10-20_ja.md)を準備した。
予約済みは重複なし216群で、回収済み80群と区別する。
batch 4の実PIDを確認するcontrollerが終了後の回収・後続起動を担当し、batch 5の本計算はまだ開始していない。

10月20日の[公開候補の再確認](data_experimental_release_2026-10-19/release_ready_recheck_20261020_v1.json)では、local HEAD・remote main・成功したCIの対象が `47ef1b6ad957a93dae3bbd6cf1d79fab86457e96` に一致した。
source ZIP・wheel・platform検証補足の3配布物、checksum一覧とrelease文面のhashが固定した候補から変わっていないことを確認した。
repositoryは引き続きprivateで、公開切替・release作成は未実施である。
この再確認は未完了の数値校正を完了扱いにするものではない。

[最終contextと転送一覧の作成処理](portable_bar_distribution_2026-10-20_ja.md)を追加し、13テストを確認した。
実データ80群の途中indexは全群未完了として拒否し、最終集計用directoryを作らないことを確認した。
全cohortのcontext作成・転送・最終qsubは未実施である。

[C0T2 sampling後半分割のpreflight](low_c0t2_sample1_preflight_2026-10-20_ja.md)を既存入口で実施し、source・native環境・未使用出力先の確認が成功した。
対象はreplicate 96～191の92160 taskで、現在は2ノード使用中のためqsubは未実施である。
投入時には共有lockと実PBSのノード数を再確認する。

[Portable BARの100群回収時点](portable_bar_first100_2026-10-20_ja.md)を追記した。
全768群中100群の回収記録を検証し、668群を未回収のまま分母に保持した。
DGX batch 5は実行中で回収準備を完了し、batch 6の入力配置を進めている。
Labo PCの計算・一致検証とクラスタ2ジョブの実行を確認し、新規qsubは行っていない。
その後DGX batch 6の入力配置が完了し、batch 5の完了・回収検証を待つ引継ぎcontrollerを起動した。

[最終cohortの転送処理](portable_bar_transfer_2026-10-20_ja.md)を追加し、local fixtureで21テストを確認した。
全群の固定planを新規remote directoryへ配置する入口であり、実cohortの転送・最終qsubは未実施である。

Labo batch 0の24群が完了し、既存controllerが回収・検証後にbatch 1を起動した。
[124群の途中index](data_portable_bar_2026-10-19/first124-cohort-inventory-v1.json)では全768群中124群を回収済み、644群を未回収とし、全67584行の予定分母を保持している。
観測済み10912行はすべて診断flag付きで、うち6668行に診断未定義があり、区間未取得・infra failureは0である。
元traceの全監査・独立referenceとの最終比較は引き続き未完了である。
Labo batch 1の実execution intentに結び付けた回収準備を完了し、batch 2への引継ぎcontrollerを起動した。
終了済みのLabo batch 0のforeground接続は終了コード0を確認して整理した。

[Labo PCの全設定照合](portable_bar_labo_full_parity_2026-10-20_ja.md)が完了し、raw artifact回収と最終providerの保存値再照合も成功した。
DGX・Labo PCの両hostについて、事前指定C0T0 groupの88設定・1536 diagnostics・1536 ACFを確認した。
検証専用groupはC0T2の768群へ加算せず、全cohortの元trace監査・独立reference比較は引き続き未完了とする。

DGX batch 5の20群を回収・検証し、[144群の途中index](data_portable_bar_2026-10-19/first144-cohort-inventory-v1.json)へ更新した。
全768群中144群を回収済み、624群を未回収として保持し、観測済み12672行・未回収54912行で全67584行の予定分母を維持した。
観測済み12672行はすべて診断flag付きで、7760行に診断未定義があり、区間未取得・infra failureは0である。
batch 6は起動済みで実execution intentに結び付けた回収準備を完了した。
終了済みbatch 5のforeground接続は終了コード0を確認して整理した。
batch 7は最初の確認では入力不足で予約せず、その後の確認で入力が揃ったため配置処理を開始した。
01:40 JSTにbatch 7の20群の配置が完了し、batch 6の終了・回収検証後に引き継ぐcontrollerを起動した。
入力archiveは279078623 byte・14577 memberで、SHA-256は `f7a3d55ef8cb499e9ecc60a06e4fb719466a62d99a68959b9c146cc69e930a3a` である。
batch 7本計算の開始とは区別し、controllerの実PID観測は `data_portable_bar_2026-10-19/dgx-batch7-handoff-observations-v1.jsonl` に保存する。

02:10 JSTまでに、sampling前半の384群すべてについて必要な保存markerが揃ったことを既存readiness処理で確認し、DGX batch 8の20群の配置を完了した。
これはsampling job 265338のPBS終端受入や、全768群の科学検証完了とは区別する。
batch 8入力archiveは279044727 byte・14577 memberで、SHA-256は `e1d57c626826305d6b1cf87ee39445651108d430d52e5c802d22b711af11211b` である。
最初のbatch 8配置確認では375群readyで予約せず、その記録を保持している。
batch 8本計算は未開始であり、batch 7が起動した後に実execution intentに結び付けた回収準備と引継ぎcontrollerを設定する。
この時点ではクラスタ2ジョブともPBS状態Rで、新規qsubは行っていない。

02:16 JSTにDGX batch 6の20群の回収・検証を確認し、[164群の途中index](data_portable_bar_2026-10-19/first164-cohort-inventory-v1.json)へ更新した。
全768群中164群を回収済み、604群を未回収として保持し、観測済み14432行・未回収53152行で全67584行の予定分母を維持した。
観測済み14432行はすべて診断flag付きで、8844行に診断未定義があり、区間未取得・infra failureは0である。
batch 7の本計算を実PIDで確認し、実execution intentに結び付けた回収準備とbatch 8への引継ぎcontrollerを設定した。
終了済みbatch 6のforeground接続は終了コード0を確認して整理した。
クラスタ2ジョブは引き続きPBS状態Rで、sampling後半のqsubは未実施である。

2026-10-20にsampling前半job `265338.node-PRISM` のPBS状態F・終了コード0・run_count 1を確認した。
固定sourceの `partition_evidence` で実PBS情報とsummary・投入記録・native identityを照合し、予定92160 taskに対し観測92160、missing 0、failed 0、errorsなしを確認した。
前半の検査証拠とsummary・terminalのSHA-256は `data_tile_validation_2026-10-17/low_c0t2_sample0_terminal_check_20261020_v1.json` に保存した。
空いた1ノードに、事前準備済みのC0T2 sampling後半（replicate 96–191）を既存の一回限りの投入wrapperからqsubで投入した。
受理jobは `265339.node-PRISM` であり、1ノード・96 worker・32 GB・walltime上限17時間30分である。
投入直前に共有lock・既存controller終了・source/native binding・最大2ノードの制約を再検査し、投入receiptは `data_tile_validation_2026-10-17/low_partition_0_2_sample_1_submission_once_v1_receipt.json` に保存した。
投入後の実qstatで既存BAR job 265334と新規sampling job 265339が各1ノードのR状態であることを確認し、`data_tile_validation_2026-10-17/low_c0t2_sample1_after_submission_20261020_v1.json` に保存した。
前半の正常終了は全768群の校正完了を意味せず、後半sampling・全体collector・native audit・BAR集計・reference照合は引き続き必要である。

最終portable集計のqsubラッパーを小仕様・受入テスト・実装の順で追加し、Windowsと元クラスタ環境で各27テストの成功を確認した。
共有lock・待機を含む最大2ノード・二重投入防止・実PBS IDと終端の照合を備え、既存の科学readerは変更していない。
実cohortのconfiguration作成・最終集計のqsubは未実施であり、詳細と固定sourceは [投入ラッパーの記録](portable_bar_qsub_2026-10-20_ja.md) に保存した。

DGX batch 7のforeground接続は終了コード0で終了し、引継ぎcontrollerによる20群の回収・転送hash・execution bindingの検証成功を確認した。
[184群の途中index](data_portable_bar_2026-10-19/first184-cohort-inventory-v1.json)を作成し、全768群中184群回収済み・584群未回収、観測16192行・未回収51392行として全67584行の予定分母を保持した。
観測16192行はすべて診断flag付きで、9904行に診断未定義があり、区間未取得とinfrastructure failureは0である。
batch 8の起動を確認し、実execution intentに結び付けた回収準備を完了した。
batch 9の3回目の入力確認では418群readyだったが固定割当の必要数が揃わず、予約も本計算の起動も行っていない。
全sampling・元環境のtrace監査・reference照合は未完了であり、この途中indexを最終bias・RMSE・被覆の検証として扱わない。

DGX batch 9の20群の配置・転送検証を完了し、batch 8終了・回収検証後に引き継ぐcontrollerを起動した。
対象は後半samplingの `(0,2,0,0,96..107)` と `(0,2,0,0,132..139)` であり、固定host割当と入力ready判定だけで選択した。
入力archiveは294022344 byte・14577 member、SHA-256は `c39f9925d3ccca9354361564becba4a28a4873ad3a4de0c5c2ec18c873c49c20`、export manifestは `10a385409e146fee3bac6ed7386cfc481f5c7dbd0e7253ed408f7389d4dfad58` である。
配置receiptは `data_portable_bar_2026-10-19/dgx-batch9-prepared-v1.json`、観測記録は `data_portable_bar_2026-10-19/dgx-batch9-handoff-observations-v1.jsonl` に保存した。
初回観測ではbatch 8の実PID 785075がliveであり、batch 9の本計算はまだ開始していない。
前の5回の入力不足確認は予約なしとして保持し、6回目で配置を行った。
この時点でクラスタjob 265334と265339はいずれもR・run_count 1であり、新規qsubは行っていない。

2026-10-20にBAR job `265334.node-PRISM` のF・exit −29・run_count 1・実walltime 07:31:35を確認した。
元の上限07:30:00と終端証拠を保持し、固定した回復controllerのobserve・prepare・preflight・executeを順に実施して受入成功を確認した。
回復job `265340.node-PRISM` をqsubで投入し、1ノード・96 worker・234 GB・walltime上限12時間のR状態を実qstatで確認した。
保存済みBAR成果物のpayload検証と正確な再利用・未完了集合の確定は、この回復jobのPBS内で行う。
投入直後はrecovery inventoryが未生成であり、前の576個というmarker file数を検証済み再利用数として扱わない。
投入後の状態は `data_tile_validation_2026-10-17/low_c0t1_recovery_after_submission_20261020_v1.json` に保存し、sampling job 265339と各1ノードの合計2ノードを維持した。

DGX batch 8の終了コード0と20群の回収・転送・execution binding検証を確認し、[204群の途中index](data_portable_bar_2026-10-19/first204-cohort-inventory-v1.json)を保存した。
全768群中204群回収済み・564群未回収、観測17952行・未回収49632行として全67584行の予定分母を保持した。
観測17952行はすべて診断flag付きで、10992行に診断未定義があり、区間未取得とinfrastructure failureは0である。
batch 9が起動し、実execution intentに結び付けた回収準備を完了した。
batch 10の最初の確認では462群readyでも固定割当の必要数が揃わず、予約せず待機した。
全sampling・元環境のtrace監査・reference照合は引き続き未完了であり、途中集計を最終bias・RMSE・被覆の検証として扱わない。

DGX batch 10の20群の配置・転送検証を完了し、batch 9終了・回収検証後の引継ぎcontrollerを起動した。
対象は固定割当の `(0,2,0,0,140..151)` と `(0,2,0,0,176..183)` である。
入力archiveは294050618 byte・14577 member、SHA-256は `340ee679e1a768cbad25e4c47bbd150aea616552af8cf1d8b36186f6960b297d`、export manifestは `0a5cb516f476fb0a3d218f7a7a57343d11007802d8e124aebdebc8cab6e325b5` である。
最初の2回は入力不足のため予約せず、3回目で配置を行った。
配置receiptは `data_portable_bar_2026-10-19/dgx-batch10-prepared-v1.json`、実PID観測は `data_portable_bar_2026-10-19/dgx-batch10-handoff-observations-v1.jsonl` に保存した。
初回観測ではbatch 9の実PID 837234がliveで、batch 10の本計算は未開始だった。
この時点でsampling job 265339と回復job 265340はいずれもR・run_count 1であり、回復jobのinventoryとintentはまだ未生成だった。

回復job 265340の `recovery-inventory.json` と実execution intentが生成され、元job 265334のauthority、各入力hash、全768群の集合を照合した。
保存済みBAR payloadの再hash検証を経て629群を再利用可能、139群を未完了として分離し、集合の重複・欠落がないことを確認した。
観測証拠は `data_tile_validation_2026-10-17/low_c0t1_recovery_inventory_observation_20261020_v1.json` に保存した。
inventory SHA-256は `af53b8ced668e3814e857ae78954b680bb57e4906c2ccc8dadc9478dbc0cd449`、execution intentは `36ce458beee80800dbacebae700244c799edd8c7208c51cb897c08080b86429a` である。
この段階はBAR保存結果の再利用検証であり、元samplingの全payload再hash、回復jobの正常終端、最終collection、trace・reference照合の完了とは区別する。

2026-10-20にC0T1回復後の独立reference比較の準備を進め、既存report parent・資源方針・result/trace/reference binderの59 testが119.19秒ですべて成功した。
科学処理6 helperは変更せず、前の配置transportのcontrol参照・証拠名・report出力先の3か所だけをC0T1用に変更した。
クラスタの `20261019-tile-low-bar-recovery-c0t1-v1/report_helpers_v1` へ配置し、元deployment/source/runtime照合、実Linux importとbash構文確認が成功した。
report deployment SHA-256は `7045dcb03d29bd46c081385c736662c6230e4f393662f72ea396f34f1c193c3b` であり、配置receiptは `data_tile_validation_2026-10-17/low_bar_recovery_report_c0t1_deployment_v1_receipt.json` に保存した。
変更箇所の記録は `low_bar_recovery_report_c0t1_transport_derivation_v1.json`、15ファイルのsource・テスト・ログの保存先は同データディレクトリの `low_bar_recovery_report_c0t1_preparation_sources_v1` である。
手順と受入条件は [C0T1回復後のreport準備](low_bar_recovery_c0t1_report_preparation_2026-10-20_ja.md) に記録した。
reportの起動transport、実終端に基づく準備・資源確定、qsub、数値比較、回収は未実施であり、今回の配置でC0T1の最終検証完了とはしない。

C0T1用のreport起動・完了受入・回収transportを追加し、起動・入力照合14 testが2.32秒、完了受入・回収10 testが1.57秒で成功した。
実trace受入証拠を再構築し、case 0・target 1・job 265336・completion hash `7258dc00e6372b103e6ba668c1a7bb8cefc3e555019c259e2a497a31b0db9edd` を照合した。
回復completionがない場合、prepareがネットワーク呼出しや実行証拠作成前に拒否されることをテストした。
実クラスタへのobserveは成功し、回復job 265340はR・run_count 1、report launch未作成、占有2ノードだった。
17ファイルのコード・テスト・ログ・導出記録・手順書を `data_tile_validation_2026-10-17/low_bar_recovery_report_c0t1_control_sources_v1` に保存した。
起動から回収までの具体的なコマンド順を [C0T1回復後のreport準備](low_bar_recovery_c0t1_report_preparation_2026-10-20_ja.md) に追記した。
reportのprepare・preflight・execute、実終端受入、回収、最終bias・RMSE・被覆の検証は未実施であり、全体goalは継続する。

DGX batch 9の正常終了・20群の回収検証が完了し、batch 10の実起動とexecution intentに結び付けた回収準備を確認した。
終了したbatch 9保持端末はexit 0で回収済みである。
回収済みは全768群中224群、観測19712行・未回収47872行となり、予定67584行の分母を維持した。
観測19712行はすべて診断flag付きで、12052行に診断未定義があり、区間未取得とinfrastructure failureは0である。
途中indexは `data_portable_bar_2026-10-19/first224-cohort-inventory-v1.json`、SHA-256は `f3a6feda2930972bf089a102ffedb93ad8a20ced8fd38039d7dab1cfbb3ee29b` に保存した。
DGX batch 11の入力確認は全体507群readyでも固定割当の必要数が揃わず、予約・配置・実行を行わなかった。
全sampling・元環境のtrace監査・独立reference照合は未完了であり、この途中indexを最終bias・RMSE・被覆の検証とは扱わない。

DGX batch 11の入力は3回目の確認でも不足したが、全体512群ready・固定DGX割当ての未予約20群readyを確認し、4回目で配置と転送hash照合を完了した。
対象は `(0,2,0,0,184..191)` と `(0,2,0,1,116..127)` の20群であり、数値結果による選別やホスト割当て変更は行っていない。
入力archiveは294316460 byte・14577 member、SHA-256は `945af1e3be9fd631e92fdcb4d5ba0937e2296912b923adafc4774d7542a987ff`、export manifestは `3e1ccf7c87b060bfe35e14f2ed2475d8984fef19ef9b57aac5910563f8b2890a` である。
配置receiptは `data_portable_bar_2026-10-19/dgx-batch11-prepared-v1.json`、SHA-256は `951002c68edd26d74a08ace13b449190061e35c6f17af35ff8aee486dbe7743a` である。
batch 10の終了・回収検証後にbatch 11へ進むcontrollerを起動し、初回観測でbatch 10の実PID 854049がliveであることを確認した。
実PID観測は `data_portable_bar_2026-10-19/dgx-batch11-handoff-observations-v1.jsonl` に保存し、この時点ではbatch 11の計算は未開始である。

Labo batch 1の終了コード0と24群の回収・転送・execution binding検証を確認し、[248群の途中index](data_portable_bar_2026-10-19/first248-cohort-inventory-v1.json)を保存した。
全768群中248群回収済み・520群未回収、観測21824行・未回収45760行として全67584行の予定分母を維持した。
観測21824行はすべて診断flag付きで、13356行に診断未定義があり、区間未取得とinfrastructure failureは0である。
index SHA-256は `fabf6356b1aeaeeea08e19875516074aca35ecefe9241d20f1ed029babeb0804` である。
batch 2が起動し、実execution intentに結び付けた回収準備と、配置済みbatch 3への引継ぎcontrollerの起動を完了した。
batch 3 controllerの初回観測ではbatch 2の実PID 23152がliveであり、batch 3の計算は未開始だった。
終了したbatch 1保持端末はexit 0で回収し、batch 2・3の観測記録を保持した。
この時点のクラスタjob 265339・265340はR・run_count 1で、回復summaryは未生成だった。
全sampling・元環境のtrace監査・reference照合は未完了であり、途中indexを最終bias・RMSE・被覆の検証とは扱わない。

Labo batch 4の24群 `(0,2,0,0,108..131)` の配置・転送hash照合を完了した。
入力archiveは352856856 byte・17469 member、SHA-256は `3441fc00f6e2598217598fcc50d6bd03f37cc95b899d8d3670b6b825135cc2c0`、export manifestは `30af243ab547527943a00c68fc9b9dfb6ef0d33859970c9c11b320cbe2a077c9` である。
配置receiptは `data_portable_bar_2026-10-19/labo-batch4-prepared-v1.json` に保存した。
この時点でLabo batch 2が実行中、batch 3は引継ぎ待機、batch 4は配置のみで未実行であり、固定割当てやworker数は変更していない。

DGX batch 10の終了コード0と20群の回収検証を確認し、batch 11の実起動とexecution intentに結び付けた回収準備を完了した。
終了したbatch 10保持端末はexit 0で回収済みである。
全768群中268群回収済み・500群未回収、観測23584行・未回収44000行として全67584行の予定分母を維持した。
観測23584行はすべて診断flag付きで、14436行に診断未定義があり、区間未取得とinfrastructure failureは0である。
途中indexは `data_portable_bar_2026-10-19/first268-cohort-inventory-v1.json`、SHA-256は `2124f521df5c5c20c29443d49f3310929afabe98a4b4cf1fc003952e81740250` に保存した。
DGX batch 12は全体554群readyでも固定割当ての必要数が揃わず、予約・配置・実行を行わなかった。
クラスタjob 265339・265340はR・run_count 1で、回復summaryは未生成だった。
全sampling・元環境のtrace監査・独立reference照合は未完了であり、この途中indexを最終bias・RMSE・被覆の検証とは扱わない。

DGX batch 12は最初の2回は固定割当ての入力不足で予約せず、3回目に全体557群readyの中から未予約20群を確保して配置・転送hash照合を完了した。
対象は `(0,2,0,1,128..135)` と `(0,2,0,1,160..171)` である。
入力archiveは294507314 byte・14577 member、SHA-256は `76bf7bae91adcfcf7445857514d469e05d7211450b67fa213cc514f9e5c4b1d2`、export manifestは `bedf8fe91e14b1351530713cb833decd558ff549a416451051b1858cfe537a40` である。
配置receiptは `data_portable_bar_2026-10-19/dgx-batch12-prepared-v1.json`、SHA-256は `16e8fc0ffd56bfb78ab1779e95415117685020c34d25f933a335ac25397b1737` に保存した。
batch 11の終了・回収検証後にbatch 12へ進むcontrollerを起動し、初回観測ではbatch 11の実PID 906631がliveだった。
観測記録は `data_portable_bar_2026-10-19/dgx-batch12-handoff-observations-v1.jsonl` に保存し、この段階でbatch 12の本計算は未開始である。

DGX batch 11の終了コード0と20群の回収・転送・execution binding検証を確認し、終了した保持端末を回収した。
batch 12の実起動とexecution intentに結び付けた回収準備を完了し、[288群の途中index](data_portable_bar_2026-10-19/first288-cohort-inventory-v1.json)を保存した。
全768群中288群回収済み・480群未回収、観測25344行・未回収42240行として全67584行の予定分母を維持した。
観測25344行はすべて診断flag付きで、15528行に診断未定義があり、区間未取得とinfrastructure failureは0である。
index SHA-256は `0e3b260cf067b27513fbe6b734209bd8d74583b9bdb60c0f3ebdc33baaad52bf` である。
全sampling・元環境のtrace監査・独立reference照合は未完了であり、途中indexを最終bias・RMSE・被覆の検証とは扱わない。

DGX batch 13は全体598群readyの中から固定割当ての未予約20群を確保し、配置・転送hash照合を完了した。
対象は `(0,2,0,1,172..179)` と `(0,2,1,0,100..111)` である。
入力archiveは285015970 byte・14577 member、SHA-256は `3884b588a367d7adbaf6abfcd13a9a6eedd1804ec67ba2a7c0165b39efafd632`、export manifestは `d3bc07ff77c0c5d4de40347a2976b55c5adb4a857079334c98b7e1638b9ed59b` である。
配置receiptは `data_portable_bar_2026-10-19/dgx-batch13-prepared-v1.json`、SHA-256は `f28f2fa5c3fe7ebf4c1e51d0c2affe2e8a7c118e1676a4a6b3b9a32b5cb2ab1f` に保存した。
batch 12の終了・回収検証後にbatch 13へ進むcontrollerを起動し、初回観測ではbatch 12の実PID 959165がliveだった。
観測記録は `data_portable_bar_2026-10-19/dgx-batch13-handoff-observations-v1.jsonl` に保存し、この段階でbatch 13の本計算は未開始である。
クラスタjob 265339・265340はR・run_count 1で、回復先に725個のmarkerを観測したが、最終summaryは未生成だった。
このmarker数はファイルの存在確認であり、回復cohort全体のpayload検証や終端受入済み群数とは区別する。

2026-10-20 05:30 JSTの観測で、C0T1回復先のmarkerが768/768個そろった。
job 265340はR・run_count 1で、recovery-summaryは未生成であり、全payload検証・集計・終端受入は未完了である。
同時点のjob 265339もR・run_count 1であり、クラスタは引き続き2ジョブである。
観測値は [768 markerの観測記録](data_tile_validation_2026-10-17/low_c0t1_recovery_768_marker_observation_20261020_v1.json) に保存した。

2026-10-20、C0T1回復job 265340のF・exit 0・run_count 1を確認し、専用completion transportで終端metadataとmarker hashを受け入れた。
実walltimeは02:16:08、累積CPU時間は129:34:10で、768群・67584行、再利用629群・再計算139群だった。
completion SHA-256は `f5ce222b6655005d60a1200923d438a44274669a8a3336824485c3a78902dff9`、回復summary SHA-256は `002820ab778a531645d3d7c7134286897a3bc78d108b287fa5c487b0a260220b` である。
証拠は `data_tile_validation_2026-10-17/low_bar_recovery_c0t1_completion_once_v1_{intent,remote,stdout,stderr,receipt}` に保存し、受入時にqsubは呼んでいない。
この受入は終端metadataの確認であり、全数値payload・元trace・独立referenceの照合と最終bias・RMSE・被覆の検証は引き続き未完了である。
C0T1 reference比較controllerのprepareを開始し、ログを `output/low_bar_recovery_report_c0t1_prepare_run_v1.log` に保存している。

C0T1 reference比較のprepareが成功し、prepared SHA-256は `7b2199c09a7574c6c2ca2e0f4e86cc48af5542607947ec256a5c1c19f9d73181` である。
既存資源方針から1ノード・1 CPU・251 GB・上限24時間となり、これは終了時刻の予測ではない。
report.sh SHA-256は `4ae7a96698b6393f5dacb24b9bb3e7e4a46ded4d234d6f53e4fdaa344ffa8504` で、preflightを開始した。

DGX batch 14は全体639群readyの時点で固定割当ての20群を確保し、入力配置と転送hash照合を完了した。
対象は `(0,2,1,0,112..119)` と `(0,2,1,0,144..155)` で、本計算は未開始である。
入力archiveは278690501 byte・14577 member、SHA-256は `e8330c4b55dd26cf000b3bf37e73af6580ebe6e496b067aeeb28d19b9b77521b`、export manifestは `e38a125b39b3d8e52a71570a93242e2253a4a73f135b5660159326467184bc9f` である。
配置receiptは `data_portable_bar_2026-10-19/dgx-batch14-prepared-v1.json`、SHA-256は `0a53745242791700b939e47e321fe50eddd82495c8b6e26f4441cd7b3ed3da16` に保存した。

DGX batch 12の20群を回収・検証し、保持端末のexit 0を確認した。
completion SHA-256は `e9d3831adda6d8dc21441ffcf877ebd935962f6b0920dc2442d6a350b987bea9`、転送検証記録は `a834b8e4a50dd0e6157b8bd302272201c1d619a5ea73bd575ba2c377571286cd` である。
batch 13は実PID 978219で起動し、実行intentに結び付けた回収準備とbatch 14へのhandoff controllerを設定した。
[308群の途中index](data_portable_bar_2026-10-19/first308-cohort-inventory-v1.json) は全768群中308群回収済み・460群未回収、観測27104行・未回収40480行として全67584行の分母を維持する。
観測27104行はすべて診断flag付きで、16624行に診断未定義があり、区間未取得とinfrastructure failureは0である。
index SHA-256は `b8e45951047087ab1e90fe2d66e88917b0f6b6305b8ee687cd046a2b27a66a39` である。
全sampling・元環境trace監査・独立reference照合は未完了であり、この途中indexは最終bias・RMSE・被覆の検証ではない。

C0T1 reference比較のpreflightとexecuteが成功し、qsubで `265341.node-PRISM` を投入した。
2026-10-20 05:58 JSTの実qstatで、job 265341はR・run_count 1、1ノード・1 CPU・251 GB・上限24時間で、準備済みreport.shからの投入を確認した。
同時にsampling job 265339もR・1ノードであり、合計2ノードを維持した。
実観測は [C0T1 report投入後のqstat](data_tile_validation_2026-10-17/low_c0t1_report_after_submission_20261020_v1.json)、投入証拠は `data_tile_validation_2026-10-17/low_bar_recovery_report_c0t1_control_execute_v1_{intent,remote,stdout,stderr,receipt}` に保存した。
reportの正常終端受入・回収・最終数値評価は未実施である。

Labo batch 5は全体651群readyの時点で固定割当ての24群 `(0,2,0,0,152..175)` を確保し、入力配置と転送hash照合を完了した。
入力archiveは352714110 byte・17469 member、SHA-256は `4d0417a77ee6335a1f96ed9a1ed669891e33df2559924702ffba3ba0c681b39c`、export manifestは `2f2e403fe053b4e2a32354d95164cc9db813d8d3d33d87caf8cf24955d7c66bd` である。
配置receiptは `data_portable_bar_2026-10-19/labo-batch5-prepared-v1.json`、SHA-256は `6d67019aa85804a8d7c1befd35dbb62b9bbe61202dce757d2bdeea439d8b35b8` に保存した。
これは後続入力の配置であり、batch 5の本計算は未開始である。
2026-10-20 06:01 JSTの実qstatでsampling job 265339とreference比較job 265341のR・run_count 1を確認した。
