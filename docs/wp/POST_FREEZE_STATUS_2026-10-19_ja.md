# 公開候補固定後の状態：2026-10-19 21:35 JST

現在の要約は[2026-10-22の公開準備と数値検証](PROJECT_STATUS_2026-10-22_ja.md)を参照し、[2026-10-21の要約](PROJECT_STATUS_2026-10-21_ja.md)と以下は時点ごとの履歴として保持する。

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

DGX batch 15は全体682群readyの時点で固定割当ての20群を確保し、入力配置と転送hash照合を完了した。
対象は `(0,2,1,0,156..163)`・`(0,2,1,0,188..191)`・`(0,2,1,1,96..103)` で、本計算は未開始である。
入力archiveは278837065 byte・14577 member、SHA-256は `e9ae1585daf173d26b5109f0ad69a22bbf2dfe28e681c3b258a84d8b82476913`、export manifestは `3e00cce4c9c87702da14081b56a539f8b2caf1ddeb80142f50ab3497d2d3da92` である。
配置receiptは `data_portable_bar_2026-10-19/dgx-batch15-prepared-v1.json`、SHA-256は `fbcf359e2e14f6bf1ac4aaafd194b2c0349f83f6c3962ad31705432e9d8303ed` に保存した。
2026-10-20 06:24 JSTの実qstatでsampling job 265339とreference比較job 265341のR・run_count 1を確認し、合計2ノードを維持した。

DGX batch 13の保持端末はexit 0で終了し、20群の回収・転送・execution binding検証を完了した。
completion SHA-256は `562313237389f052cfcdf2c2eee838bff6da1b84650c4f08bc39a3cb7251f6ff` である。
batch 14は実PID 1032573で起動し、実行intentに結び付けた回収準備とbatch 15へのhandoff controllerを設定した。
[328群の途中index](data_portable_bar_2026-10-19/first328-cohort-inventory-v1.json) は全768群中328群回収済み・440群未回収、観測28864行・未回収38720行として全67584行の分母を維持する。
観測28864行はすべて診断flag付きで、17708行に診断未定義があり、区間未取得とinfrastructure failureは0である。
index SHA-256は `26082939870208806069ff894b7dfe18c55f1ee6501e6ced43d9f0ea1b387446` である。
全sampling・元環境trace監査・独立reference照合は未完了であり、この途中indexは最終bias・RMSE・被覆の検証ではない。

次の固定条件C1T0のanchorについて、既存 `submit_low_partition_once.py` のpreflightを一度実行し、source・native環境・未使用出力先の照合が成功した。
responseはreturncode 0・ambiguous false・qsub_executed false・slot_available falseであり、既存2ジョブの稼働中に追加投入はしていない。
receiptは `data_tile_validation_2026-10-17/low_partition_1_0_anchors_0_preflight_once_v1_receipt.json`、SHA-256は `642e1232b25c18bed8af18f0c71a9bc3255f7fcfea0b69daf4b9edd243024226` に保存した。
production manifestは `d2e3be26cc75202f15dc4bb1874fb0e210f906451d2cbb0522d4222e8441a06a`、脚本SHA-256は `958d59280796534ee879594dec45f3505c45f65cef8bf7f982cbb8bc01752c8e` である。
事前計画の要求は1ノード・96 CPU・32 GB・上限2時間で、preflightは使用済み、executeは未使用である。
実際の投入時には既存入口が共有lock内で待機中を含む最大2ノードを再確認する。
C0T2のsampling全体が先に終わった場合は、そのcollectorと元環境trace監査を優先する。

C0T1 reference比較job 265341はF・exit 0・run_count 1、walltime 00:51:11で終了した。
終端受入と13ファイルの転送前後照合が成功し、completion SHA-256は `296349b1910bfce5c05cc55bb0fec44caa2945dbd49514e4a8533848dafa91cf`、report SHA-256は `db0fbd9ea104bf55c5f5a84d29f5cf291e4312a47061f567fa4de156d537bcb2` である。
回収先は `data_tile_validation_2026-10-17/low_bar_recovery_report_c0t1_collection_v1/` で、reportは454663531 byte、collection receipt SHA-256は `fe3a69e447ebe63de819c98420d962b49e3a4942a310bbeb299b91b7d25d5117` である。
[C0T1の数値報告](low_c0t1_recovered_result_2026-10-20_ja.md)と集約JSON・再現スクリプトを保存し、352設定×192 seedの67584行を保持した。
事前指定の16 chain・burn-in 6000・保存60000・fine ladderの8設定では、相対RMSE約1.16–1.22%、被覆件数179–182/192だったが、flaggedとlow ESSがすべて192/192であり、混合・名目95%被覆を保証しない。
低ノイズの正式reference比較は5/12条件まで完了し、残る条件と同精度までの時間比較は未完了である。

空いた枠にC1T0 anchorをqsubで投入し、job 265342のF・exit 0・run_count 1、walltime 00:01:37を確認した。
凍結readerで192 anchor task・失敗0のmetadataと実PBS・native記録を確認し、受入receipt SHA-256は `59244893745aff78875294d819cc73b509c88617dc02c38230c69ab29aeef1a4` である。
確認スクリプトと記録は `data_tile_validation_2026-10-17/accept_low_partition_1_0_anchors_0_terminal_v1.py` と `low_partition_1_0_anchors_0_terminal_acceptance_v1.json` に保存した。
C1T0 sample0のpreflightでslot_available trueを確認後、既存入口からqsubで265343を投入した。
投入receipt SHA-256は `c1c98021c4ad59e07dee4c901c6d22f09431406d0561147f458b801e0d6efd5f`、脚本SHA-256は `e0e3612e9eb57c0ad8bbe7b86b3a24b57139464e7260e9f1ad3775a62484d811` である。
2026-10-20 06:54 JSTの実qstatで265343のR・run_count 1・1ノード・96 CPU・32 GB・上限24時間を照合し、C0T2 sample1の265339と合わせて2ノードを維持した。
実観測は [C1T0 sampling投入後のqstat](data_tile_validation_2026-10-17/low_c1t0_sample0_after_submission_20261020_v1.json) に保存し、C1T0のanchor・sample0のpreflightとexecuteは使用済みである。

DGX batch 16は全体728群readyの時点で固定割当ての20群 `(0,2,1,1,128..147)` を確保し、入力配置と転送hash照合を完了した。
入力archiveは279087236 byte・14577 member、SHA-256は `1e6d7f1804124bf07d469d605ff1340b87606536ddbb0cc47906ef3bc5427017`、export manifestは `d831f23b1f099d034dbfc0e588896956a932c5a2f7532a90bd745f3417a3eb7c` である。
配置receiptは `data_portable_bar_2026-10-19/dgx-batch16-prepared-v1.json`、SHA-256は `e6234eb14c4f59f31e850127993dff64b7ed52103b734d9d5fdae67a39561579` に保存した。
これは後続入力の配置であり、batch 16の本計算は未開始である。

既存の予約と終了時間を読み取り、[分担見直しの基準snapshot](data_portable_bar_2026-10-19/remaining_assignment_baseline_v1.json)を保存した。
snapshot SHA-256は `fe32506b2f50f7e8aba3a3ac1fc1ecd20e7f61166cc981976fbd5f2a0a5df26d` で、DGXは340群予約済み・20群未予約、Laboは144群予約済み・264群未予約だった。
既存実運用の経過時間はDGX直近4 batchが20群で約35–36分、Labo batch 1が24群で約195分であり、追加benchmarkは実施していない。
全seedと予約済み担当を保持してLabo未予約264群をDGXへ移す[小仕様](portable_bar_remaining_assignment_spec_2026-10-20_ja.md)を作成した。
この時点で新経路の受入テスト・実装・再割当て実行は未実施であり、従来経路の実行と回収を継続する。

2026-10-20 07:16 JST時点では、固定分担planと旧新経路の割当て・群数検査を実装し、既存予約処理の回帰確認を含む48テストが24.88秒で成功した。
詳細は[未予約群の分担planと群数検査の受入記録](portable_bar_remaining_assignment_acceptance_2026-10-20_ja.md)に記録した。
plan SHA-256は `d866e2a0df455dc267aade83ec9f05b3a5d19f0fc936368a17017f191f459b11`、86ファイルを保存したarchive manifest SHA-256は `8e2d08fd155efe8ee71530c569e83321742cb6b17e30345b0e53502aac727b88` である。
この検査は合成終端記録による群数・担当・失敗保持の受入であり、新経路の配置・実行・回収・実artifact混合集約・最終provider接続は未実施である。
再割当ての264群はまだ実行していない。

DGX batch 14の20群の回収と検証が完了し、batch 15を実行中である。
batch 15の回収準備とbatch 16への自動引き継ぎ待機を設定し、実remote PID 1055479の生存を確認した。
Labo batch 2の実remote PID 23152も生存しており、batch 3への引き継ぎ待機を継続している。
[348群の途中index](data_portable_bar_2026-10-19/first348-cohort-inventory-v1.json)は全768群中348群回収済み・420群未回収、観測30624行・未回収36960行で全67584行の分母を維持する。
index SHA-256は `150217a07452038d1d799216c560c7fdb7e00884cba5c0d7c1043b71248deaff` である。
観測30624行はすべて診断flag付きで、18788行に診断未定義があり、区間未取得とinfrastructure failureは0である。
これは途中回収の検査であり、最終bias・RMSE・被覆の検証ではない。
既存DGX batch 17の入力配置を試みたが、全体751群readyの時点では対象20群が揃わず、予約も実行も行っていない。
07:16 JSTの実qstatで265339と265343はともにR・run_count 1・各1ノード96 CPUであり、最大2ノードを維持している。

2026-10-20 07:24 JSTまでに、[再割当てrunner](portable_bar_reassigned_runner_acceptance_2026-10-20_ja.md)を追加し、実行制御の29テストが6.57秒で成功した。
既存の初期化・解析関数を直接再利用し、固定plan・入力hash・実runtime・前batchの終了・排他制御を検査する。
テストは合成入力・代替workerによる制御の検証であり、新runnerによる本番BAR計算は未実施である。
DGXの新規検査先で7 sourceのhash一致、隔離モードでのimport・CLI、既存の数値関数と同一の関数を使うことを確認した。
source archive manifest SHA-256は `dfb8ed71e5d572ce62ba4b0e6ab93b926aac82cc5daa80db72597c3796e6f6de`、実機検査receiptは `3a42d9a69398e464a755c3fe680841a5fd15ba0e011fbbf86842acdcc883cb05` である。
本番config・配置・起動制御・回収・実artifactの混合集約・最終provider接続は未完了であり、再割当て計算はまだ開始していない。
07:23 JSTの実qstatで265339と265343はR・run_count 1・各1ノードのままであり、DGX batch 15とLabo batch 2も実PIDの生存を確認している。

2026-10-20 07:33 JSTまでに、[再割当て結果の回収と旧新混合集計](portable_bar_reassigned_collection_acceptance_2026-10-20_ja.md)を追加した。
既存の数値行・診断・ACF検査を保ち、固定plan・config・実際の担当を照合し、元担当と実行先を分けて記録する。
collector初回49件・11.90秒、追加修正後の新規検査29件・5.79秒、archive検査15件・0.77秒、新旧集計31件・44.11秒、導出source検査1件・0.43秒の成功を保存した。
これらは合成記録と既存の小さい数値fixtureによる検査であり、新経路の本番回収・最終科学検証は未実施である。
39ファイルの保存先は `data_portable_bar_2026-10-19/remaining_assignment_collection_sources_v1/`、manifest SHA-256は `57a9c81740431160357bfd601236c687b3e61631004e616624ebfac9aceb5b2c` である。
payload reader・最終provider・転送contextと本番自動制御の対応を引き続き必要とする。

DGX batch 17は全体768群readyの時点で既存担当の最後の20群 `(0,2,1,1,172..191)` を予約し、入力配置と転送hash照合を完了した。
配置receipt SHA-256は `da58f4291c88ec1fec532f86a15f052ff134ed74de1423aad54bec3a111cfa24` である。
入力archiveは279054091 byte・14577 member、SHA-256は `6fa64c7534507a6aeac090f3e612ecea33fb8a3d2156f6b7e6d0a429c3a33ed2`、export manifestは `8d4791ca3b9955475d9be1e2dd07fda956ff29e16b6d89e5a8e664cbbd6a9828` である。
この追加予約は固定planが元のDGX担当として保持する20群であり、移動対象264群を変更しない。
全768群のmarker readyはsampling jobの正式終了や元環境trace監査の完了を意味しない。
07:31 JSTの実qstatでは265339と265343はともにRであり、最大2ノードを維持している。

2026-10-20 07:40 JSTの実qstatでC0T2 sample1の265339がF・exit 0・run_count 1となり、walltime 05:15:35を確認した。
既存のcollection入口でanchor 265337・sample0 265338・sample1 265339の全終端、source・native環境・実PBSを検査し、C0T2 collectionのprepareとpreflightが成功した。
prepared SHA-256は `2219cd0e4fd652955510c03019566ac548abf8ea0392e685d0e34467d9d5d76c`、prepare receiptは `0668fc5a52ae0e80b6e4f01d0576422ad952006323c0a9fd18608752f37ff20e` である。
slot_available trueを確認後、qsubでcollection job 265345を投入し、execute receipt SHA-256は `1e14afeaa649d9bde84c79646079b1aa7cb633662872a53b5cc89f7f9e476a96` である。
脚本SHA-256は `639d9ca35339a7e8e7f72c2c2e4e8e920f6aa57f589ba3d86bf7a3b1cc29e423`、資源は1ノード・1 CPU・32 GB・上限2時間である。
07:43と07:47 JSTの実qstatで265345のR・run_count 1を確認し、C1T0 sample0の265343と合わせて最大2ノードを維持した。
C0T2 collectionのprepare・preflight・executeは使用済みであり、正常終了後のcompleteと元環境trace監査が未実施である。

DGX batch 15の20群を回収・照合し、batch 16を開始した。
batch 15のcompletion SHA-256は `75590e4f7e0538e3bdd5ba948a93e48a4b33a80a73ea90758d9dde4b7d8d8671` である。
batch 16の回収準備とbatch 17への自動引き継ぎ待機を設定し、実remote PID 1110511の生存を確認した。
[368群の途中index](data_portable_bar_2026-10-19/first368-cohort-inventory-v1.json)は全768群中368群回収済み・400群未回収、観測32384行・未回収35200行で全67584行の分母を維持する。
index SHA-256は `4cf5cb02e4dd4fb1218393bf88bab8fd2a454dae5c6dc7b9082ab4ae4061210b` である。
観測32384行はすべて診断flag付きで、19860行に診断未定義があり、区間未取得とinfrastructure failureは0である。
この途中indexは最終bias・RMSE・被覆の検証ではない。

[再割当てarchiveの読み取りと最終provider](portable_bar_mixed_provider_acceptance_2026-10-20_ja.md)を追加し、新旧payload 37件・6.51秒、provider制御15件・30.04秒、最終監査・report入口32件・13.93秒の成功を保存した。
数値行の既存検査と、元環境のtrace・native・PBS・独立referenceの検査を維持している。
51ファイルの保存先は `data_portable_bar_2026-10-19/mixed_provider_sources_v1/`、manifest SHA-256は `6432d594c0e9d561494f29d70fbbfc630c8f6c7ac0ffb1ff0896fac38a1fef74` である。
クラスタの新規配置先でhash・import・CLIの確認が成功し、配置archive SHA-256は `306fa9c4140f4b4548270b391dcca2c265021199ce977a86c3e65595793a87b7` である。
この配置確認では科学計算もqsubも起動していない。
新しい転送contextとqsub入口、本番config・配置・起動・回収の自動制御は未完了であり、再割当て264群は未実行である。

2026-10-20の追記として、[混在index・転送・qsub制御](portable_bar_mixed_controls_acceptance_2026-10-20_ja.md)を実装・検証した。
転送contextは18件・33.61秒、転送は24件・1.22秒、qsub制御はWindowsで31件・17.68秒、クラスタLinuxで31件・12.98秒のテストが成功した。
実392群の途中indexから全群contextへの移行は拒否され、出力先も作成されなかった。
保存した58ファイルのmanifest SHA-256は `3c92eede73d4a65a5d59f0081a72590ee05b713a8f1aef3972d69f626e1d6e86` であり、新しい本番qsub投入は実施していない。
Labo batch 2の24群の回収後にbatch 3が開始し、batch 3の回収準備とbatch 4への自動引継ぎ待機を設定した。
途中indexは392/768群・観測34496行で、全行に診断flag、21144行に診断未定義があり、未回収376群・33088行も予定67584行の分母に保持する。
08:03 JSTの実qstatでC0T2回収265345とC1T0 sample0の265343はともにRであり、最大2ノードを維持した。
再割当て264群の本番config・配置・起動・回収の自動制御、C0T2の全元環境trace監査と最終科学評価は引き続き未完了である。

2026-10-20 08:18 JSTの追記として、[再割当ての配置・起動・回収driver](portable_bar_reassigned_lifecycle_acceptance_2026-10-20_ja.md)を接続し、Windowsの計49件とクラスタLinuxの49件・6.48秒の受入テストが成功した。
固定planの最初の2 batch・計40群をDGXへ配置し、入力・source・転送hashを確認した。
14 batch・264群を順次処理するdriverをPID 4108で開始し、既存DGX batch 17の開始・終了・回収を待っている。
再割当ての数値計算はこの時点では未開始であり、driverは先行PID消滅、正常終端、回収照合を必須として次を実行する。
55ファイルのsource保存manifest SHA-256は `7327e7ccd80367ab1c49a9adfd89ed280a3f9be2ce56a3d12191894f3e0d4442` であり、controller記録SHA-256は `a5993a933093ae5384ee45fdb15c28b370e7d73bd81dde84e42342c289149eac` である。
このdriver起動は使用済みで、重複起動せず、その観測・実行・回収記録を追う。
08:11 JSTの実qstatではC0T2回収265345とC1T0 sample0の265343はともにRで、最大2ノードを維持している。
未完了の科学評価と公開候補の準備を区別し、公開候補の配布物は変更していない。

2026-10-20 08:23 JSTの追記として、DGX batch 16の20群の回収・照合が完了し、batch 17の実PID 1171348が生存中であることを確認した。
再割当てdriverはPID 4108で稼働し、batch 17の回収準備を自動で完了して、その終端を待っている。
batch 17のcollection preparation SHA-256は `a065a8d8462f0afe19fb795d20436c671590c04bea684f90debda8bdcc7924ee` であり、別の手動回収を並行実行しない。
[途中index v2](data_portable_bar_2026-10-19/mixed-collected-snapshot-20261020-v2.json)は412/768群回収済み、観測36256行・未回収31328行で、予定67584行の分母を維持する。
index SHA-256は `506a164a1860283a0a7be2382af7e873792953a00cc80f7456a002a8b0b2b418` である。
観測全36256行に診断flag、22220行に診断未定義があり、区間未取得とinfrastructure failureは0である。
[C0T2最終評価runbook](portable_bar_c0t2_final_runbook_2026-10-20_ja.md)に、sampling collector終端受理、trace capacity/full監査、混在全群context、転送、最終qsubの順序と実入口を整理した。
本番全群context・最終config・最終qsubは未実施であり、08:20 JSTの実qstatでは265345と265343がともにRだった。

2026-10-20 08:37 JSTの追記として、C0T2 collector 265345はF・Exit_status 0・run_count 1を確認して受理を完了した。
collectorの実walltimeは39分11秒であり、completion SHA-256は `522913222494090124f4426034e821a486795c8ee122a0834746915addf8bc35` である。
trace capacityをqsub 265346として投入し、同じ正常終端とwalltime 34秒を確認した。
8群・2 seedのcapacity summaryで監査失敗0、sampling失敗0、native platform一致を確認したが、全seedの監査完了ではない。
capacity受理の最初のSSH接続失敗は [回復記録](trace_capacity_transport_recovery_2026-10-20_ja.md) に保存し、実remoteの未実行確認後、失敗bytesを保持して受理のみを一度回復した。
計算ジョブの再投入はなく、正常受理を入力に全192 seedのtrace監査prepareを開始した。
公開候補は `47ef1b6` に固定したままであり、現在のmain `886b44b` の追加差分は文書・TODO・gitignoreである。
08:26 JSTの [再確認](data_experimental_release_2026-10-19/release_ready_recheck_20261020_v2.json) は両commitのCI成功、private状態、配布物のhash維持を記録し、その実行sourceも同directoryに保存した。
今回の作業でcommit・push・公開操作は行っていない。

2026-10-20 08:47 JSTの追記として、C0T2全trace監査のprepareと別記録による読み取り専用preflightが成功した。
prepared SHA-256は `20d8d409972a29b037ee11f33c6200b6516c21a7093526fce8aea8a1b6de12be` で、1ノード・96 worker・83 GB・上限1時間を固定した。
最初のpreflightのSSH resetを保持し、成功した再観測を検査してkeepalive付きexecuteを開始した。
08:47 JSTの実qstatで確認できたactive jobは265343だけであり、この時点のfull監査job IDは未取得である。
同じexecuteを繰り返さず、既存の実行handleとreceiptを確認する。
投入の詳細は [C0T2全監査記録](low_c0t2_trace_full_dispatch_2026-10-20_ja.md)、次のtile288生成条件は [残条件の手順](low_remaining_generator_order_2026-10-20_ja.md) を参照する。

2026-10-20 08:55 JSTの追記として、全監査をqsub job 265348として受け付け、execute receiptのaccepted=true・ambiguous=falseを確認した。
receipt SHA-256は `69e9fd5bf77175bf52c9fd3151f3e3fe9907cd69a3ae735b779f7302d2d24e99` である。
08:55:08 JSTの実qstatでは265348がQ、265343がRで、それぞれ1ノードの要求で上限2ノードを維持した。
full監査の終端受理は未完了であり、投入を繰り返さない。
08:49 JSTのtile288生成rootにはtrace完了markerが16995件あったが、これは進行観測であり、payloadの検証や成功件数の認定ではない。

2026-10-20 09:03 JST前後の追記として、DGX batch 17の正常終端・20群の回収照合が完了し、再割当てbatch 0を実PID 1198428で開始した。
driver PID 4108が同batchの回収準備も作成し、手動で重複操作していない。
[途中index v3](data_portable_bar_2026-10-19/mixed-collected-snapshot-20261020-v3.json) は432/768群・38016行の回収済みと、336群・29568行の未回収を記録する。
index SHA-256は `18d4199c6af5cfd66eb2d5c2fecff48bedc58639c26b59ad6c66b6d6536c541e` である。
全38016行に診断flag、23280行に診断未定義があり、未回収・flag・未定義を予定67584行の分母から除外していない。
最終集計の [資源設定](portable_bar_mixed_final_resource_2026-10-20_ja.md) を、以前の同規模jobの実walltimeとmemoryを根拠に1 CPU・32 GB・4時間へ固定し、根拠receipt・source・manifestとともにクラスタへ配置した。
この配置はqsubを行わず、全入力の準備完了や科学的精度を認定しない。
監査265348の実qstatはQで、scheduler commentは空きncpus不足、開始時刻の見積りは未取得だった。
生成265343と合わせて待機中を含む2ノードの上限を維持する。

2026-10-20 09:09 JST前後の追記として、[低ノイズreportの要約処理](low_noise_report_summary_acceptance_2026-10-20_ja.md)を小仕様・受入テスト・実装の順で追加した。
12テストが0.79秒で成功し、欠測・未取得・診断未定義を除外せず、独立referenceがない場合の指標をnullに保つ。
保存済みC0T1 reportから抽出した要約は従来の選択8設定・全設定範囲など15項目と一致し、新しい数値計算は行っていない。
source・ログ・実データ照合の11ファイルを保存し、manifest SHA-256は `a8c3458662788926f174ff2651ebe7368445f51e4b3fb98b4d6d79a6781ebe03` である。
09:08 JSTの実qstatでは監査265348がQ、生成265343がRであり、C0T2の最終reportは未取得のままである。

2026-10-20 09:21 JST前後の追記として、[最終report回収helper](portable_mixed_final_collection_acceptance_2026-10-20_ja.md)を小仕様・受入テスト・実装の順で追加した。
Windowsの26テスト・22.67秒、クラスタLinuxの26テスト・15.34秒が成功した。
固定wrapper・実PBS終端・転送前後snapshot・local bytesを照合して13ファイルを回収し、失敗時は部分結果を保持する。
本番最終reportがないため、今回の試験はfixtureによる制御の検証であり、本番回収は未実施である。
10ファイルのsource保存manifest SHA-256は `416c3388b752399a9a4295ee039590145351e5f1e9b1be598cb9b6da9ba3454e` である。
既存の計算sourceとmixed-controlsの配置を変更せず、別directoryでLinux検証した。

2026-10-20 09:38 JST前後の追記として、DGXの再割当てbatch 0の正常終端と20群の回収照合が完了した。
実PID 1198428の消滅とterminalを確認し、既存driverが回収・照合後にbatch 1をPID 1248985で起動したことを観測した。
batch 0の計算実時間は2,103.40秒で、回収receipt SHA-256は `6be9aa7cb1a6fda1e232a70bc5312f3d46530de0b167a364bec9be31cccd969e` である。
[途中index v4](data_portable_bar_2026-10-19/mixed-collected-snapshot-20261020-v4.json) は452/768群・39,776行の回収済み、316群・27,808行の未回収を記録する。
index SHA-256は `f3d397906d978128934605732c0e555596ad81801e349a4d1a63244cb34ca15f` である。
回収済み全39,776行に診断flag、24,320行に診断未定義があり、区間未取得とinfrastructure failureは0だった。
予定67,584行の分母を維持し、途中indexを最終科学検証の完了と扱わない。
Labo batch 3のPID 27908は実在し、09:36 JSTの実qstatでは監査265348がQ、生成265343がRだった。
次のクラスタ投入は待機中を含む2ノード上限の空きが得られてから行う。

2026-10-20 09:40 JST前後の追記として、低ノイズ独立計時のselector接続をsourceから点検した。
既存selectorはsingle・partitioned・stagedの3 readerと従来analysis metadataを要求し、C0T0/C0T1の回復済み結果とC0T2のportable経路を直接扱えない。
stage2とstage4もselectorの実source・argvを固定するため、report名やsource hashだけを書き換える対応は使えない。
[接続仕様](low_noise_timing_reader_extension_spec_2026-10-20_ja.md)に既存分母・候補順位・reference監査・経路固有の実行履歴を保持する拡張と受入範囲を記録した。
新接続のテスト・実装・配置は未実施であり、公開候補と稼働中driverは変更していない。
09:39 JSTの実qstatは監査265348がQ、生成265343がRであり、既存計算は継続している。

2026-10-20 09:45 JST前後の追記として、別directoryでselectorのWSS参照監査を共通化した。
追加15件・5.60秒、分離版selectorでの既存回帰65件・16.02秒が成功し、元selectorと新2 sourceの試験前後のhash一致を確認した。
[実装記録](low_noise_timing_reference_refactor_2026-10-20_ja.md)と14ファイルの保存manifestを作成し、manifest SHA-256は `c7e185db68757e13c61239970dcaa82ed6031e11b6171521ba4935653f45ec25` である。
新reader経路そのもの、親入口・後段の接続、Linux受入と配置は未実施である。
09:45 JSTの実qstatでは監査265348がQ、生成265343がRで、DGX batch 1のPID 1248985も実在しterminalは未作成だった。

2026-10-20 09:50 JST前後の追記として、readerの返り値と保存reportの共通照合を隔離directoryへ追加した。
各192 seed・16設定の実数値再集約を使う25件が4.00秒で成功し、欠測・未定義・失敗群を除外しないことと改変拒否を確認した。
source・受入・ログ6ファイルのmanifest SHA-256は `d9f64be60d45945382823ae7d4c7a35f3defdaa2e2b16f666bfe9d6fb5150347` であり、詳細は [接続部品の実装記録](low_noise_timing_reference_refactor_2026-10-20_ja.md) に追記した。
経路ごとの正式reader呼出し・PBS終端検証・親入口の接続は未完了で、公開候補と稼働中driverは変更していない。
09:49 JSTの実qstatでは監査265348がQ、生成265343がRであり、上限2ノードを維持した。

2026-10-20 09:57 JST前後の追記として、回復処理v1/v2の同名moduleを分離する子プロセス実行部品を追加した。
Windows15件・1.28秒、別directoryに配置したクラスタLinux15件・2.93秒が成功し、Linuxの起動を含む経過時間は8.23秒だった。
実handle・終了code・ログを保存し、非0終了、出力欠落、入力変更、未終端、既存directoryへの再起動を成功扱いしない。
qsubや正式科学readerの実行は行わず、12ファイルの保存manifest SHA-256は `5f099dbaec4a4d13cf29ac287ffd473475670ec575af103cf4d0c97f2f01674d` である。
詳細を [接続部品の実装記録](low_noise_timing_reference_refactor_2026-10-20_ja.md) に追記した。
09:57 JSTの実qstatは監査265348がQ、生成265343がRであり、元の計算を継続している。

2026-10-20 10:05 JST前後の追記として、回復済みcohortのreader入口を隔離directoryへ追加し、14件の接続試験が4.93秒で成功した。
既存の数値再集約とPBS ledger checkerを使い、元解析の異常終端を保持して各job役割を結ぶが、heavy reader・native・WSS監査は縮小試験のmockである。
C0T1の実analysis/full-trace metadataを読み、sampling完了記録が完全一致することを確認した。
本番traceの読取、子プロセスCLI・親selectorの接続、portable入口、全経路Linux受入は未実施である。
9ファイルの保存manifest SHA-256は `a7659d29641d70fbd16c7dc0aca114ddd11f979aea4308d942a8dda6896299fe` であり、[段階的実装記録](low_noise_timing_reference_refactor_2026-10-20_ja.md) に詳細を保存した。
10:03 JSTの実qstatでは監査265348がQ、生成265343がRだった。

2026-10-20 10:11 JST前後の追記として、C0T2 portable結果の読取入口を追加し、14件・5.11秒の縮小接続試験が成功した。
全5受入fileの統合実行は83 passed・16.59秒で、6 sourceと5 testの前後hashが一致した。
archive/native/snapshot/WSS境界はmockを含み、PC処理をPBS jobへ読み替えず、クラスタ上の実役割だけを照合する構成を確認した。
15ファイルの保存manifest SHA-256は `0e34070f3c704eddf669830b1adfef2883465912f78649185a32aec290f2e566` であり、詳細を [段階的実装記録](low_noise_timing_reference_refactor_2026-10-20_ja.md) に追記した。
子プロセスCLI・bootstrap・親selector接続・全経路Linux受入・本番実行は未完了である。
10:09 JSTの実qstatでは監査265348がQ、生成265343がRで、DGX batch 1のPID 1248985も実在しterminalは未作成だった。

2026-10-20 10:28 JST前後の追記として、子プロセスCLI・source/native bootstrapを追加し、全8受入fileで129 passed・20.53秒、Linuxの関連4 fileで61 passed・8.06秒を確認した。
Windows venvの中継プロセスに起因する即時親PIDの不一致を検出し、検査を緩めず実プロセスfixtureをbase interpreterへ固定した。
失敗記録を含む21ファイルのmanifest SHA-256は `dc1880d4c56b5cd75b72de348c7ee3f14b4604191c76f24fc941d7b30eb4f450` であり、[段階的実装記録](low_noise_timing_reference_refactor_2026-10-20_ja.md)に範囲と未完了項目を保存した。
親selector接続・本番reader・全科学readerのLinux受入は未完了であり、公開候補のsourceは変更していない。
DGX再割当てbatch 1を回収したmixed snapshot v5は472/768群、41,536/67,584行で、flagged 41,536・undefined 25,388・infrastructure failure 0だった。
snapshot SHA-256は `d96d7da84ab68a686b5559c127a4c9501876f53b083438c450a12c932299c2ea`、全科学検証完了flagはfalseである。
10:24 JSTの実qstatは監査265348がQ、生成265343がRで、待機中を含め最大2ノードを維持している。

2026-10-20 10:35 JST前後の追記として、親による子の返り値受理部品を追加し、実子プロセスを含む16件が5.71秒で成功した。
全9受入fileの統合はWindowsで145 passed・25.00秒、Linuxで145 passed・27.61秒だった。
Linux初回の配置では既存profile/fixture JSONが不足して68 failed・77 passedとなり、その失敗記録を保持した上で、必要な2 metadataを追加した別配置で通過した。
174ファイルのmanifest SHA-256は `afdad91e65a91ffbf8cf196c2927a6c070c7d6e005671c102c1f5ec9b66875a5` で、[段階的実装記録](low_noise_timing_reference_refactor_2026-10-20_ja.md)に試験範囲と失敗原因を保存した。
正式selectorへの起動・受理の組込み、実descriptor、計画・資源・stage4接続と本番reader実行は未完了であり、公開候補は変更していない。
10:33 JST前後にDGX batch 2の実PID 1301224とLabo batch 3の実PID 27908を確認し、10:34 JSTの実qstatは監査265348がQ、生成265343がRだった。

2026-10-20 10:47 JST前後の追記として、隔離selectorへ子プロセスの逐次起動・受理を接続し、全11受入fileはWindows 167 passed・31.91秒、Linux 167 passed・33.60秒で成功した。
旧3経路とsource bindingの回帰65件も確認し、その後に入力rootの申告漏れと親script hashの循環を防ぐ受入・修正を追加した。
最終191ファイルのmanifest SHA-256は `cdf456f6ef0ac5c0bd4fe0a06c21caae332d12d326a3bbd350240327f2b7a6ba` で、[段階的実装記録](low_noise_timing_reference_refactor_2026-10-20_ja.md)に各段階の範囲を記録した。
全12条件が未完了なら24行pendingを維持して子を起動せず、待機timeoutから同じ計算を再起動しない。
外側のqsub用wrapperの新経路metadata・資源接続、実descriptor、後段plan/stage4と本番reader実行は未完了である。
10:45 JSTの実qstatは監査265348がQ、生成265343がRであり、最大2ノードと公開候補の固定を維持している。

2026-10-20 10:58 JST前後の追記として、親側の最終job metadata readerを追加し、Windows/Linux各26件が成功した。
C0T1の元report bytesと実qstatも照合し、job 265341のwalltime 3071秒・peak memory 2,049,712,128 byteを確認した。
要求251 GiBを実使用メモリとして扱わず、実測値で資源根拠を作るための部品である。
16ファイルのmanifest SHA-256は `c0771be6c717b338170149a3522e81f40091fe8267822eed16f40331c8076b99` であり、外側wrapperへの組込みとportable本番記録の照合は未完了である。
DGX再割当てbatch 2の20群を受理し、mixed snapshot v6は492/768群・43,296/67,584行、flagged 43,296・undefined 26,476・infrastructure failure 0となった。
snapshot SHA-256は `ba5fd71ce42c1c91ea1aa8632e0bb85e159cf84fd289a4a8184655bff7ecec9e`、全科学検証完了flagはfalseである。
10:55 JST前後にDGX batch 3の実PID 1315863とLabo batch 3の実PID 27908を確認し、10:47 JSTの実qstatは監査265348がQ、生成265343がRだった。

2026-10-20 11:30 JST前後の追記として、隔離親wrapperの新経路接続とfixtureによるstage4 descriptor受理までを検証した。
追加受入はWindows/Linux各212件、既存回帰は各120件で成功し、別プロセスで実97 source・137 native fileのbyte/import originも照合した。
205ファイルの保存manifest SHA-256は `8de7cfbe6ba4e54f29db8de097294eff877ed68c0294fb5871c4449f499e7aba` で、範囲と残作業は[実装記録](low_noise_timing_reference_refactor_2026-10-20_ja.md)に記録した。
全12条件の実descriptor、本番の選択・計時実行は未実施である。
Labo batch 3を回収したmixed snapshot v7は516/768群・45,408/67,584行で、flagged 45,408・undefined 27,764・infrastructure failure 0となった。
snapshot SHA-256は `c4b38ad8c24b67913e5a2d6c2f85f311c3e1e27ad6df174c68fae338d033db2e`、全科学検証完了flagはfalseである。
Labo batch 4へ引継ぎ済みで、batch 5への既存waiterが同じ実PID 6360を観測している。
11:29 JSTの実qstatは監査265348がQ、生成265343がR・経過4時間32分58秒であり、待機中を含め最大2ノードを維持した。

2026-10-20 11:36 JST前後の追記として、C0T0/C0T1の実子environment候補を別プロセスで確認し、各98 source・137 native fileと元reportのsource/runtime bindingが一致した。
初回は旧bundleの新module不足で失敗し、元bundleを変更せず検証済み追加moduleの参照先を別配置に設定して通過した。
28ファイルのmanifest SHA-256は `75b0e0ab62718a4cb4e3cec0853b17e7088f03e168776ef3692429ed498ec096` で、raw reader実行や親descriptorの本番受理は未実施である。
DGX再割当てbatch 3の20群を回収し、mixed snapshot v8は536/768群・47,168/67,584行、flagged 47,168・undefined 28,856・infrastructure failure 0となった。
snapshot SHA-256は `1475792bb0720861db408998597e1ec04b7e5e9d3a6280a64d81c20299527786`、全科学検証完了flagはfalseである。
DGX batch 4の実PID 1365431が稼働中・terminal未作成、Labo batch 4も既存waiterが実PID 6360の稼働を観測した。
11:33 JSTの実qstatでは監査265348がQ、生成265343がR・経過4時間38分59秒であり、新しいqsubは行っていない。

2026-10-20 11:48 JST前後の追記として、C0T0/C0T1のentry候補を各25ファイルのmetadata・元authority・WSS marker・実qstatへ結んだ。
実C0T1のWSS監査と最終reportではsource配置先だけが異なり、それ以外の全フィールドは一致していた。
小仕様・失敗する受入の後に、既存のsource relocation検査を通過した元配置または現在配置の完全なmapだけを認める修正を加え、第三の配置や科学フィールドの変更は拒否した。
修正後はWindows/Linux各222件が成功し、実子environment候補も2条件で再確認した。
詳細と201ファイルのmanifest SHA-256 `d4e2187a82a300118e6be01e4354d213971cc4228a5dd5f33e7e94555432578b` を[実装記録](low_noise_timing_reference_refactor_2026-10-20_ja.md)に保存した。
本番raw reader、全12条件の選択、低ノイズ独立計時と新しいqsubは未実施である。

2026-10-20 12:18 JST前後の追記として、C2T0/T1/T2の元sealed snapshotと実qstatを再照合し、各77ファイルのentry候補を保存した。
親の元Python・core・科学moduleを保った93 sourceとldpc native binding 8ファイルのbootstrapも通過した。
初回の依存不足を含む32ファイルのmanifest SHA-256は `638c65605c0928d6b1d559198a8ad059afdf2392ff0b902035e1d51fc9386583` で、raw読取や数値再計算は実施していない。
完了済み5条件と未完了7条件の部分入力inventoryを保存し、全12条件の受理・資源確定・本番選択と区別した。
DGX再割当てbatch 4を回収したmixed snapshot v9は556/768群・48,928/67,584行、flagged 48,928・undefined 29,928・infrastructure failure 0だった。
snapshot SHA-256は `0eb4723e2b07fe98b0eb55684f49be02c6f3ba88dd46b148884272af357dcf4b` で、既存pipelineがbatch 5を起動した。
12:09 JSTの実qstatは監査265348がQ、生成265343がR・経過5時間13分5秒で、Labo batch 4も既存waiterが実PID 6360の稼働を観測した。

2026-10-20 12:32 JST前後の追記として、C0T0/C0T1の保存済み全67,584行・352設定・192 seedによる独立算術レビューを完了した。
各11,968項目の最大絶対差は1.734723475976807e-18と6.938893903907228e-18であり、分母からの除外は0だった。
隔離した配置拡張の受入・回帰はWindows 52 passed・1.38秒、Linux 52 passed・0.22秒で、既存算術6関数・classのAST一致も確認した。
41ファイルと別保存のrows 2個を再照合し、manifest SHA-256 `b59f08e74acbc10a4ec5c71a8235028914ed65db57ba8c932639ee0733fad27d` を[結果報告](low_recovered_arithmetic_review_result_2026-10-20_ja.md)に記録した。
全block長を含む長い16設定のreference区間との重なりはC0T0で172–186/192、C0T1で158–182/192であり、8設定の抜粋だけでは区間への感度を尽くさない。
算術の一致を混合・精度・名目被覆の保証にはせず、低ノイズの正式比較は5/12条件のままである。
12:30 JSTの実qstatは監査265348がQ、生成265343がR・経過5時間35分7秒で、新たなqsubは行っていない。

2026-10-20 12:35〜12:37 JSTに、稼働中のtile288 bit-flip生成job 265343の実qstat、execution intent、trace directoryのmarker数を読み取り専用で観測した。
同じintent SHA-256の61,440タスクに対し、約82秒間でmarker数が52,690から52,901へ211件増えた。
[観測と外挿](data_tile_validation_2026-10-17/low_c1t0_live_progress_projection_20261020_v1.json)には元2観測のhash、残り8,539件、短時間の生成速度をそのまま用いた13:32 JST前後というmarker到達予測を保存した。
失敗marker、task間の費用差、末尾の遅いtask、生成後の全成果物照合を含むため、この外挿をjob終了や科学検証完了の時刻とは扱わない。
実qstatはR・walltime 5時間41分8秒であり、再実行や新規投入は行っていない。

2026-10-20 12:42 JST前後に、完了済み5条件の固定長設定全80行を用いた[誤差法比較](low_long_uncertainty_comparison_result_2026-10-20_ja.md)を保存した。
初回検査は全条件を16 chain・保存60,000とする仮定を拒否し、C0の16 chain・保存60,000とC2の8 chain・保存12,000を明示する修正を行った。
修正後の受入は7 passed・0.62秒、実入力5条件の照合と全20方法群の集約は完了し、異なるnoise間の同一計算予算比較とは扱わない。
各condition・kernel・初期化の20組で点推定由来のbias/RMSEと診断件数は誤差法間で同一だが、referenceとの重なりと区間幅は変化する。
depolarizing p=.001ではblock長32の重なり108–123/192に対しcross_chainは174–181/192であり、両者とも診断未定義192/192、区間未取得0/192だった。
元source・受入・CSVなど9ファイルのmanifest SHA-256は `354554fc70c71bc68d3d4cc6ed8d40d684d94f480c9e244dcbf5debd70960838` で、保存sourceからの再実行でもCSV hashが一致した。
本文15表行と元集計も照合し、公開既定を変更せず、正式比較5/12条件と残り7条件・独立計時を維持した。

2026-10-20 12:45 JST前後に、DGX再割当てbatch 5の20群を既存pipelineが回収・受理し、batch 6の実PID 1430650の稼働を確認した。
全archiveを照合したmixed snapshot v10は576/768群・50,688/67,584行、flagged 50,688・undefined 31,008・infrastructure failure 0であり、未回収192群・16,896行を保持する。
snapshot SHA-256は `e202c49d5ecceb76c8cba3507394175636224cb9715b77faf9c86652ce60c0f3`、全科学検証完了flagはfalseである。
Labo batch 4の実PID 6360も稼働中で、クラスタは監査265348がQ、生成265343がR・経過5時間49分9秒だった。
新しいqsubは行わず、待機中を含め最大2ノードを維持した。

2026-10-20 12:52 JST前後に、5条件・80設定の[誤差法比較図](data_tile_validation_2026-10-17/low_long_uncertainty_plot_v2/uncertainty_comparison.png)をPNG・PDF・SVGで保存した。
図には条件別のchain数・保存数・burn-inと診断flag・未定義件数を示し、誤差法間の同じtraceの利用と、referenceとの重なりが精度・被覆・混合の保証ではないことを明示した。
全80点を保存CSVへ照合し、初回の脚注切れを修正したv2を目視確認した。
描画recordのSHA-256は `0de38626d2f4ae3a379202a0ca7397c1d87ad93fad7faaf5992bdd653578c810`、検証receiptは `436668ee1d2a382cba475e798d3e20cdf60e0909bd4c112ad8877677d24f9981` である。

2026-10-20 12:57 JST前後に、完了済み5条件の比較を再現する[補足ZIP](low_long_comparison_export_2026-10-20_ja.md)を作成した。
38ファイル・404,280 byte、SHA-256 `0c1c66e21a8ff343baa82b9a3e858380b515e30010245377dacd4419396ca6ba` であり、元レビュー・CSV・図・sourceを含む。
別directoryへ展開して同梱sourceを実行し、2つのCSVのhash、描画80点、ZIP内ローカルリンク11件を確認した。
補足は保存集計の記述的比較に限り、raw trace・seed別BAR row・native環境・残り7条件と独立計時を含む完全再計算bundleとは扱わない。
本体の公開候補を変更せず、GitHubへの添付・公開は未実施である。

2026-10-20 13:03 JST前後に、次のtile288後処理に備えて既存の凍結配列解析とdecoder構築を除いた変換関数を縮小fixtureで比較した。
tile72/288 × bit-flip/depolarizing × 低ノイズ3点について、成功・sampling失敗・zero anchorの36ケースがWindows optional環境で一致し、実測13.49秒だった。
変換後はdecoder factoryを例外に置き換え、元解析source hashの検査と既存の数値・ACF・flag・未定義位置の比較を維持した。
元full driver・parity入口・再割当てrunnerは固定されたtile72条件専用のままであり、tile288本番parity・実行・回収・最終readerへの接続は未実施である。
稼働sourceを変更せず、12ファイルのmanifest SHA-256 `f125036b5316a068291d6647796da7c85d738651b19aff3f65f6c8899b00507b` と実施範囲を[確認記録](portable_bar_tile288_readiness_spec_2026-10-20_ja.md)に保存した。

2026-10-20 13:15 JST前後に、元production・条件・root・固定照合群を明示する隔離parity入口を追加した。
Windows 49 passed・1.47秒、Linux 49 passed・0.68秒で、改変helper、入力混同、失敗記録の保持、既存出力の拒否を実CLIでも確認した。
17ファイルのmanifest SHA-256は `cd3aea416bf28dd35ab57d68b2c8938484d7f8e7f2797857de31ff3b004116a4`、入口sourceは `e182c6bb9b33243229ad3a374a8d53bbe1db542e09f3797eda556667e34b4bd9` である。
次のC1T0の群 `(1,0,0,0,0)` を元生成準備のproduction hashへ結び、未取得のarchive hashを埋めず、実reference・実parity・全群driverへの接続は未実施として保存した。
既存のC0T2 pipelineと固定sourceは変更せず、新しいqsubも行っていない。

2026-10-20 13:22 JST前後に、DGX再割当てbatch 6の20群を回収・受理し、batch 7の実PID 1480686の稼働を確認した。
mixed snapshot v11は596/768群・52,448/67,584行、flagged 52,448・undefined 32,092・infrastructure failure 0であり、未回収172群・15,136行を保持する。
snapshot SHA-256は `853b19c79d12257d85abfbba2ac7bb28f2ce9aede80029cd96966971ba7e3a2b`、全科学検証完了flagはfalseである。
13:20 JSTのC1T0生成の実qstatはR・経過6時間25分16秒で、61,440予定タスク中60,080件のmarkerを確認し、partition summaryは未作成だった。
新しい条件用の元クラスタreference作成は[小仕様](portable_bar_native_reference_spec_2026-10-20_ja.md)を保存し、専用worker・qsub接続・実計算は未実装・未実施として既存の投入順を維持した。
## 2026-10-20 13:37 JST：native reference workerの受入

次のtile288条件をPCへ分担する準備として、[native reference worker](portable_bar_native_reference_spec_2026-10-20_ja.md)を別directoryに実装した。
元loader・analyzerを呼び、全88設定の順序、診断とACF、失敗と未定義の保持、元入力とPBS証跡のhash、別領域へのarchive保存を確認する。
Windows 26 passed・2.53秒、Linux 26 passed・1.07秒で、実PBSや実入力での成功実行とは区別する。
sourceとred/greenログ、Linux実行記録、再現receiptを24ファイルのmanifestに保存した。
専用qsub接続と終端受理wrapper、実reference作成とPCとの実parityは未完了である。
公開候補と稼働中pipelineは変更していない。

13:36 JSTの実qstatで265343はR、生成traceの終了markerは61,440/61,440だった。
partition summaryは未作成であり、正常終端後にcollectorへ進む。
固定照合群 `(1,0,0,0,0)` の80 traceと共有anchorのmarkerも揃っているが、payloadの受理ではない。
265348は引き続きQで、待機を含め要求2ノード以内を維持している。

## 2026-10-20 13:49 JST：native referenceのqsub準備

[専用controller](portable_bar_native_reference_spec_2026-10-20_ja.md)を実装し、Windows 23 passed・7.06秒、Linux 23 passed・12.16秒を確認した。
投入記録のatomicな公開、待機を含む2ノード制限、曖昧なqsub応答でのlock保持、重複投入拒否、終端とarchiveの対応をfixtureで確認した。
実PBS上の成功計算・終端受理は未実施である。
既存C0T0の保存native referenceから88設定・2,980.7399085583165秒・peak RSS 1,551.15625 MiBを元exportのhashで照合し、C1T0の初回要求を1 CPU・32 GB・上限4時間とした。
元bundle・Python・source・入力・資源証拠を固定した実configとscriptを新しいjob rootへ作成し、preflightとbash構文確認を通した。
config SHA-256は `0e96cb5fbb4c8db9b37dcac9c20e26fa6b1e855361e0499d68d7d32fc582f20d` で、source・受入・資源・準備記録を35ファイルのmanifestに保存した。
実preflight時点は265343がR・265348がQで要求2ノードだったため、qsubは行っていない。
既存jobとcollector等の優先順を維持し、実referenceが受理された後に各PCの固定群parityへ進む。

## 2026-10-20 14:02 JST：616群の回収と新条件parityの再照合

DGX再割当てbatch 7の正常回収を確認し、[途中index v12](data_portable_bar_2026-10-19/mixed-collected-snapshot-20261020-v12.json)を616/768群・54,208行へ更新した。
未回収152群・13,376行を保持し、観測全54,208行の診断flagと33,164行の診断未定義を除外していない。
infrastructure failureは0であり、最終科学検証の完了flagはfalseである。
snapshot SHA-256は `e061c7dc3ec9d0fb3cafe020e87dbee899fc237e557cd000c72ef9ed663079ff` である。
既存pipelineが起動したDGX batch 8のPID 1496265と、Labo batch 4のPID 6360の稼働を実観測した。

[新条件の保存parity再照合](portable_bar_condition_batch_spec_2026-10-20_ja.md)はWindows 41 passed・5.46秒、Linux 41 passed・0.76秒だった。
12種類のcondition identity、全88設定、小さいACF、未定義と失敗を含むfixtureを用い、改変・欠落・別条件・runtime不一致を拒否した。
source・ログ・再現手順を18ファイルのmanifestに保存し、実C1T0の成功parityや本番全群driverとは区別した。
新条件のdriver・割当て・配置・回収・最終readerの接続は未完了である。
クラスタは265343がR・265348がQで、要求最大2ノードを維持し、新たなqsubは行っていない。

## 2026-10-20：新条件driverと割当て契約の受入

[新条件driver](portable_bar_condition_batch_spec_2026-10-20_ja.md)と全768群の割当て契約を隔離directoryへ追加した。
外部hashで固定した入力、実runtime、前batch終端、実processとlockを確認し、既存数値workerをspawnで起動して終了後にも保存parityを再照合する。
統合受入はWindows 112 passed・18.47秒、Linux 112 passed・3.70秒で、Windowsではfixture ZIPのmtime対応後の結合試験も1 passed・14.71秒だった。
実subprocessとspawn子workerで、合成したsampling・anchor失敗から全88設定の未取得行を保持することを確認した。
Windowsのvenv起動親processとpytestファイル名を別workerと誤認する問題、Linux fixture ZIPの古いmtimeによる失敗を検出・修正し、失敗時の証跡も保存した。
source・ログ・再現手順を[51ファイルのmanifest](data_tile_validation_2026-10-17/portable_condition_batch_driver_v1/manifest.json)へ保存し、SHA-256は `0f42a9d2df4263da38adaad1c7ef49e4f1e469d0e1d2ed4ca7c03d9ea9aa8fa5` である。
実C1T0の成功parity、実割当てplan、配置・回収・途中index・最終readerへの接続、本番全群計算は未実施である。
公開package・既存稼働driverは変更していない。
14:26 JSTの実qstatは265343がR・経過7時間31分、265348がQだった。
証跡保存時にもDGX PID 1496265とLabo PID 6360の稼働を確認し、既存pipelineへ任せて重複起動しなかった。

## 2026-10-20 14:35 JST前後：640群の回収と転送前入力検査

Labo batch 4の24群を正常回収し、[途中index v13](data_portable_bar_2026-10-19/mixed-collected-snapshot-20261020-v13.json)を640/768群・56,320行へ更新した。
未回収128群・11,264行、観測全56,320行の診断flagと34,476行の診断未定義を分母から除外していない。
infrastructure failureは0で、最終科学検証の完了flagはfalseを維持した。
snapshot SHA-256は `28197779bf9aea5860d80d629a020ed7667b5374880879cf6b165e8e3fe9f7f5` である。
既存引継ぎ処理が起動したLabo最終batch 5のPID 7544の稼働を確認し、実intentに結び付いた回収準備を完了した。
回収準備recordのSHA-256は `f9ea1987fac98728d9d2274cbd89646fa1b4ff4a7d8627e32cc01052bc0dd284` で、回収自体は実終端確認後に行う。

[新条件の入力転送前検査](portable_bar_condition_batch_spec_2026-10-20_ja.md)を追加し、外部pin付きの割当て・receipt・batch ZIP・固定reference ZIPと、全taskのmarker・payloadを照合する。
referenceと共通するtaskのbyte一致を含む追加26件と既存112件の統合受入は、Windows 138 passed・22.48秒、Linux 138 passed・4.43秒だった。
合成入力による転送前検査であり、実C1T0のarchive作成・転送・parityや科学的受理は未実施である。
sourceと実行ログは[25ファイルのmanifest](data_tile_validation_2026-10-17/portable_condition_input_transfer_v1/manifest.json)へ保存し、SHA-256は `40cb0570cb946e886cd15c429ef682da915418300024363f990c60f0f2d7e66d` である。
クラスタは265343がR・経過7時間39分、265348がQであり、最大2ノードの制約を維持して追加qsubを行っていない。

## 2026-10-20 14:43 JST前後：DGX引継ぎ復旧と660群の回収

DGXの旧controllerはbatch 8起動後の状態応答をJSONとして読み取れず、数値SSHの終了を待って停止していた。
旧controller PID 4108の不在、実batch 8のPID 1496265の終了とaccepted=trueの20群を再観測し、既存collectorで正常回収した。
旧応答のraw byteは保存されておらず、char 8192で読取りに失敗した原因までは確定していない。
[復旧記録](portable_bar_dgx_handoff_recovery_2026-10-20_ja.md)にsource pin・実終端・回収・再開の証跡を保存した。
状態観測だけを最大3回再試行するadapterの受入は5 passed・0.39秒で、元数値workerや割当てを変更していない。
再開controller PID 45340がbatch 9〜13を担当し、batch 9の実PID 1547853の稼働を確認した。
sourceと証跡の50ファイルmanifest SHA-256は `f49424897e960eb59fbe150650ef2fcd1467c436f863d82249c138fe2bbfdeee` である。

[途中index v14](data_portable_bar_2026-10-19/mixed-collected-snapshot-20261020-v14.json)は660/768群・58,080行となり、未回収108群・9,504行を分母に保持した。
観測全58,080行に診断flag、35,564行に診断未定義があり、infrastructure failureは0である。
最終科学検証の完了flagはfalseで、snapshot SHA-256は `0872b5cc4d14cdc318de96172f80f07236737af89bcc8487b27606fdef209803` である。
クラスタは265343がR・経過7時間47分、265348がQであり、追加qsubは行っていない。

## 2026-10-20 14:53 JST前後：tile288 sampling終端、collector投入と配置CLI

tile288 bit-flip p=.01のsampling265343は14:46:54 JSTにF・exit 0・run_count 1、walltime7時間52分17秒で終了した。
前段anchorとsamplingの正常終端を確認し、collectorのprepare・preflight・executeを一度ずつ実施した。
prepared SHA-256は `9ec6795d7b5dd3e7dd0920649ac0aefa2f2d18d128bb2cb0fc1b68e0f1e3c1f8` で、qsubによりjob265356を得た。
1ノード・1 CPU・32 GB・walltime上限2時間を要求し、実qstatでRを確認した。
C0T2のfull trace監査265348もRとなり、待機中を含む最大2ノードを維持した。
実終端と投入の証跡は[collector投入記録](low_c1t0_collector_dispatch_2026-10-20_ja.md)へ保存した。
collectorの終端受理とその後の科学評価は未実施であり、低ノイズ正式比較は5/12条件のままである。

[新条件の配置CLI](portable_bar_condition_batch_spec_2026-10-20_ja.md)は転送済み入力と固定sourceから新しい実行directoryを作り、最終pathのconfigを保存する。
実parity subprocessから配置CLI、配置したdriverとspawn workerへつなぐ合成失敗入力の結合試験を加え、全88設定の未取得行・診断flagを保持した。
配置拒否等10件と追加結合1件を含む統合受入は、Windows149 passed・36.41秒、Linux149 passed・9.00秒だった。
source・ログ・再現手順を[27ファイルのmanifest](data_tile_validation_2026-10-17/portable_condition_staging_v1/manifest.json)へ保存し、SHA-256は `392646d593f732e92fe0785795d42f230d56a4dcbb3d584dde502efbaefce7a0` である。
配置成功と起動前の全検査・科学的受理を区別し、実C1T0の転送・parity・全群実行は未実施である。

## 2026-10-20 15:08 JST前後：次条件のsampling開始と新collector

C0T2 full trace監査265348は14:55:16 JSTにF・exit 0・run_count 1で終了し、walltimeは8分20秒だった。
固定completion readerを一度だけ起動し、既存keepalive・900秒SSH観測で結果を待っている。
completion intentが作成済みであり、同じ操作を重複実行しない。
空いた枠で予定していたC1T1 anchorをqsub投入し、job265357は1分36秒で正常終了した。
続いてsample partition 0をqsub投入し、job265358のRを確認した。
要求は96 CPU・32 GB・walltime上限12時間30分で、同時にcollector265356がRのため最大2ノードを維持した。
投入記録と使用済み操作は[生成開始記録](low_c1t1_generation_dispatch_2026-10-20_ja.md)へ保存した。

[新条件collector](portable_bar_condition_batch_spec_2026-10-20_ja.md)は実config・intent・終端・予定群を固定し、元のsemantic validatorを再利用して全88設定と未取得・診断・ACF構造を検査する。
新しい終端binding等17件を加えた統合受入は、Windows166 passed・52.76秒、Linux166 passed・11.45秒だった。
実subprocessの結合fixtureで回収ZIPの全memberとhash、出力改変の拒否、context失敗の途中ファイル保持と検証済み0行を確認した。
source・ログ・再現手順を[30ファイルのmanifest](data_tile_validation_2026-10-17/portable_condition_collection_v1/manifest.json)へ保存し、SHA-256は `df45eb455fb92dd69ffd9c7ef417bb9c57f7baca7f687bcccea11a9576240ccd` である。
fixtureの成功は実C1T0の転送・parity・回収や数値校正の完了ではなく、実運用と全群index・最終readerの接続を継続する。

その後、C0T2 full trace監査のcompletion readerがaccepted=true・returncode 0で終了した。
receipt SHA-256は `fe900965d68d477b05a4aa9afbccd73aa5144f98c88e161fb89c68c6188d49d7`、remote completion SHA-256は `42ea16543e1498bb263856d84330a526c19f46b0a0be8786d8c6a88782d0b136` である。
768群・192 replicate・184,320 planned task、failed_sampling 0と12,349,440 redecoded checkpointを記録し、全measurement artifactと監査done markerを再hashした。
監査group payloadと現在の全raw traceの再hash、全物理状態の再復号をこの終端受理で行ったとは扱わず、最終PBS collectorでの検査条件を維持した。

## 2026-10-20 15:22 JST前後：680群の回収と転送先reader

DGX再割当てbatch 9の20群を正常回収し、[途中index v15](data_portable_bar_2026-10-19/mixed-collected-snapshot-20261020-v15.json)を680/768群・59,840行へ更新した。
未回収88群・7,744行、観測全59,840行の診断flagと36,628行の診断未定義を保持し、infrastructure failureは0だった。
最終科学検証の完了flagはfalseであり、snapshot SHA-256は `b7772a20e78e7f3e167d127835dd374dcca5c2fbfe12c96948fb4a0810024d44` である。
再開controllerが起動したDGX batch 10のPID 1597918とLabo最終batch 5のPID 7544の稼働を確認した。
[実process観測](data_portable_bar_2026-10-19/portable_live_20261020_v15.json)を保存し、回収と後続起動は既存controllerに任せている。

[新条件の回収ZIP reader](portable_bar_condition_batch_spec_2026-10-20_ja.md)は、独立parentとcollector pin、元plan・input manifest・native profile・transform、検証済みsampling recordとmarkerを使って保存結果を照合する。
追加13件と実subprocess fixtureを含む統合受入はWindows179 passed・59.40秒、Linux179 passed・11.62秒だった。
88未取得行の保持、sampling marker不一致の拒否、context失敗の検証済み0行を確認し、sourceとログを[33ファイルのmanifest](data_tile_validation_2026-10-17/portable_condition_archive_reader_v1/manifest.json)へ保存した。
manifest SHA-256は `c5e4945772705b4ceed780660c8f14e76ceafe9ea6e929997bbe54c242646d56` である。
実C1T0の読取、全群indexと最終readerへの統合、元環境trace監査と独立referenceの結合は未完了である。

15:35 JSTの追加確認では、qstat上のcollector265356とsampling265358はともにRであり、計2ノードを維持していた。
新条件の回収readerを全768群の途中indexへ接続し、元input ZIPの全memberとtask marker、保存recordのseed・prior・設定を照合する実装を追加した。
予定67,584行を固定し、未回収、基盤失敗、context失敗、sampling失敗、区間未取得、診断flagと未定義を保持する。
追加8件と結合試験を含む受入はWindows187 passed・65.66秒、Linux187 passed・13.28秒だった。
元の数値関数や稼働中driverは変更せず、実subprocess fixtureの正常回収88行とcontext失敗の観測0行を全予定群へ結合した。
source・ログ・再現手順を[34ファイルのmanifest](data_tile_validation_2026-10-17/portable_condition_cohort_index_v1/manifest.json)へ保存し、SHA-256は `c4d768c4c18501a9845ffa5bd08b8eaec1f0e9de2e7aa98fe676a95b940b9975` である。
このfixtureは全samplingを意図的失敗とした構成であり、正常traceの数値一致や実C1T0の校正とは扱わない。
実C1T0のreferenceと各PCのparity、全群割当て・起動、最終PBS readerへの接続を継続する。

15:39 JSTに、collector265356の正常終端・既存completion受理後にnative referenceを一度だけqsubする引継ぎをlocal PID46044で起動した。
事前の実reference preflightはreturncode 0・prepared_not_submitted、最初のcollector実観測はRであり、追加の計算jobはまだ投入していない。
共有lockとQを含む2要求ノード上限に従い、completion・投入の曖昧な応答では停止して再投入しない。
18件のWindows受入が0.40秒で成功し、controller・テスト・ログ・startup intentとpreflightを[9ファイルのmanifest](data_tile_validation_2026-10-17/native_reference_handoff_v1/manifest.json)へ保存した。
manifest SHA-256は `821a333cc44a49edc7b58f2e4da1d9a33fe5d04c86e85146b5e2ec23e3aa3867` であり、実reference成功やPC parity完了の証拠とは扱わない。
この引継ぎがcollector completionとreference submitを担当するため、実receiptを確認せず手動で重複実行しない。

15:44 JSTにC1T0の実割当てをDGX624群・Labo144群へ固定し、各kernel・初期化の192 seedを156対36に分けた。
DGX32 batch・Labo6 batchの全768群を既存validatorと直接列挙で照合し、重複・欠落がないことを確認した。
元C1T0のmanifest・platform profile・fixtureをread-only SSHで取得し、準備済みnative reference configの3ファイルのhashとproduction digestへ照合した。
割当てSHA-256は `9e2f52087a92f7bdf246a935c932b2901f80882fb86f35ffb5a3de344d44e57d` である。
直近C0T2の受理済みwall timeを配置の参考にし、C1T0やdecoderの速度比較とは扱わない。
source・実metadata・根拠・割当て・空registry・初期indexを[22ファイルのmanifest](data_tile_validation_2026-10-17/portable_condition_c1t0_assignment_v1/manifest.json)へ保存し、SHA-256は `f4bbd0b4a72c4336c60be8dd3ec3375d76e32fb706728949d22759fe4f909fa9` である。
初期indexは予定67,584行・観測0行・未回収768群であり、実reference・PC parity・入力exportと実起動は未完了である。

15:58 JSTまでにC1T0のDGX batch 0・20群とLabo batch 0・24群を実exportし、各PCの新規incoming directoryへ入力とcontrol計14ファイルを配置した。
元sampling job265343の正常終端・run_count 1・投入script、元sourceとmetadata、ZIP全member・task marker・割当てと転送後の全hashを照合した。
DGX入力50,082,015 bytes・4,977 member、Labo入力59,998,081 bytes・5,949 memberで、数値workerや実行configはまだ作成していない。
実reference比較・PC parity・runtime受理を未実施のまま保持し、sourceと証跡を[47ファイルのmanifest](data_tile_validation_2026-10-17/portable_condition_c1t0_initial_inputs_v1/manifest.json)へ保存した。
manifest SHA-256は `ec4bae61a69eedcb3c113aeb47d8f50788cb4ffec308f3f3116811c63ea1c4c9` である。

C0T2のDGX再割当てbatch 10の正常回収を既存pipelineが完了し、batch 11の実PID1612816の稼働を確認した。
Labo batch 5のPID7544も稼働しており、[観測v17](data_portable_bar_2026-10-19/portable_live_20261020_v17.json)へ保存した。
[途中index v16](data_portable_bar_2026-10-19/mixed-collected-snapshot-20261020-v16.json)は700/768群・61,600/67,584行、未回収68群・5,984行で、SHA-256は `8ab420fef29c858ed54a91fcba519ed1f2273f881fe7adf0330fdc0c01f61844` である。
観測全61,600行がflagged、37,724行がundefinedであり、未取得区間・基盤失敗は0だが科学検証完了flagはfalseのままである。
実qstatではcollector265356とsampling265358がともにRで、native referenceの引継ぎはcollector終了待ちだった。

16:09 JSTに、固定C0T2の最終joinを変更せず、全12条件を明示検査する `condition_final_join.py` を別directoryへ追加した。
元production/full audit/PBS/native environment/referenceの検査を維持し、provider sourceの開始前後の照合とcontext失敗の分母保持を追加した。
context失敗は88未取得行ずつ残し、基盤失敗と別に数え、元trace監査は両方で必須とする。
Windows54 passed・31.44秒、Linux54 passed・16.72秒で、I/O・provider・reference等を置き換えたfixture制御試験である。
source・派生手順・ログを[19ファイルのmanifest](data_tile_validation_2026-10-17/portable_condition_final_functions_v1/manifest.json)へ保存し、SHA-256は `152df1b0ed7360f4db6d5a276d330c36c8ed45323ab515a39c7b00face625f80` である。
実condition provider、CLI・qsub接続、実データのraw監査とreference結合は未完了であり、科学的な完了条件を縮小していない。

16:35 JSTまでに実condition providerを追加し、割当て・runtime・保存parity・前batchの連鎖・現在のrecord/marker・全768群の消費を照合するようにした。
関連235件はWindows66.37秒・Linux18.85秒で成功し、sourceと証跡を [37ファイルのmanifest](data_tile_validation_2026-10-17/portable_condition_provider_v1/manifest.json) へ保存した。
全群制御試験のarchive/parity I/Oは明示的なfixtureであり、別の実subprocess結合試験も合成失敗入力を用いるため、実C1T0の数値校正完了とは扱わない。
manifest SHA-256は `db8d1c35123780d9c6c3196e80e4f1d6a18941cec6118abc7b5fd152da9eac55` である。
条件別CLIからこのproviderと外側のnative最終監査を接続し、必須reference、実context hash拒否、PBS外拒否と引数受渡しの4件がWindows2.07秒・Linux0.51秒で成功した。
CLIの [41ファイルのmanifest](data_tile_validation_2026-10-17/portable_condition_final_cli_v1/manifest.json) のSHA-256は `b200161986ef18fb573cdc522945ad565eff9f7fabb1ceaae13ea05af2d98f98` である。
実native parity reference受理後のcontext作成、条件別qsub controllerと実全群の最終集計は未完了である。

16:42 JSTまでに条件別qsub controllerも別sourceへ接続し、元controllerの15関数のASTを保持してmetadata準備検査とCLIの呼出し先を変更した。
受理済みnative parity referenceの終端、全768群の割当て・全batch receipt/export、転送metadataと元sampling identityを準備検査へ追加した。
共有lock、待機を含む最大2ノード制限、曖昧応答時の予約保持、終端受理の関数は維持し、実context・configや本番jobは作成していない。
Windows45 passed・1 skipped・3.03秒、Linux46 passed・1.81秒で、Linuxだけの1件は実ファイル操作とqsub/qstat/数値readerを置換した接続試験である。
source・派生記録・ログを [24ファイルのmanifest](data_tile_validation_2026-10-17/portable_condition_final_qsub_v1/manifest.json) へ保存し、SHA-256は `94a601578cc45406286aa617378d9ce10bd5561c075f2c629b02c42f3a68bfda` である。

DGXの再割当てbatch 11の回収を受理し、[途中index v17](data_portable_bar_2026-10-19/mixed-collected-snapshot-20261020-v17.json)で720/768群・63,360/67,584行を照合した。
未回収48群・4,224行、flagged63,360行、undefined38,824行を保持し、科学検証完了flagはfalseである。
snapshot SHA-256は `a9f063277e54361cd5f87ce22ae48ea4443ab5b20790ceca89200a8b1214c21c` である。
[実process観測v18](data_portable_bar_2026-10-19/portable_live_20261020_v18.json)ではDGX batch 12のPID1671458とLabo batch 5のPID7544がともに稼働し、終端は未取得だった。
native reference引継ぎの最新成功観測ではcollector265356がRであり、重複してcompleteやqsubを呼び出していない。

16:53 JSTまでにcollector265356はwalltime 2時間00分33秒・Exit_status -29で終了した。
summaryはなく、途中tasks.jsonlとnative preflight、投入記録を保持し、[実PBS・stderr・途中ファイルhash](data_tile_validation_2026-10-17/c1t0_collector_timeout_20261020_v1.json)へ保存した。
自動引継ぎは正常終端条件を拒否して停止し、completion・reference qsubの双方を行っていない。
全群collectorの復旧は新たな残作業であり、部分回収を成功として扱わない。

単一群referenceの元契約と実configが全群collectorを入力に含まないことを確認し、正常終了済みanchor265342/sample265343に基づく独立実行へ順序を変更した。
失敗した引継ぎの停止と未投入、元source/config/script、実preflight、共有2ノード制限を確認し、16:55 JSTに [reference265360をqsub投入](data_tile_validation_2026-10-17/c1t0_reference_independent_dispatch_20261020_v1/receipt.json) してRを確認した。
全群collectorとtrace監査、独立referenceの最終結合は省略しない。
元のscientific sourceや実行中sampling sourceを変更せず、独立dispatchとnative回収・PC parity・初回batch配置の操作sourceを [14ファイルのmanifest](data_tile_validation_2026-10-17/portable_condition_c1t0_parity_operations_v1/manifest.json) へ保存した。
manifest SHA-256は `53544ecac1637417f64e097273f1e52eb12a9bcc74db77847be5fb403564c2ff` であり、後続3操作はsyntax確認のみで未実施、reference回収入口の実観測はR・completion未実施だった。

17:14 JSTまでに、collector時間切れに対応する [分離backend](collection_retry_spec_2026-10-20_ja.md) を小仕様・受入テスト・実装の順で追加した。
元sampling source/planとpartition検査を維持し、collectionの出力先と4時間の要求上限を分離し、新しいcollection証拠を同じ監査計算へ明示的に渡す。
合成metadataの12件がWindows13.95秒・Linux4.22秒で成功し、旧ファイル不変、全分母保持、別job/resource/sourceや欠落/重複taskの拒否を確認した。
[41ファイルのmanifest](data_tile_validation_2026-10-17/collection_retry_backend_v1/manifest.json)のSHA-256は `b6b1398731459c1a4e1294763b5d9330a146c1abb7a7c674513f5ca7fd94c792` である。
実旧失敗と途中成果物を固定するguard、retry config・qsub worker/controller、最終reportでのbackend選択と実データの復旧は未完了である。

DGX再割当てbatch 12の20群を受理し、[途中index v18](data_portable_bar_2026-10-19/mixed-collected-snapshot-20261020-v18.json)で740/768群・65,120/67,584行を照合した。
未回収28群・2,464行、flagged65,120行・undefined39,880行を保持し、全科学検証完了flagはfalseのままである。
snapshot SHA-256は `747091a4666e2d41342289ca067c3455cfdd6f8578e70f5732522a5671ca75ad` である。
[実process観測v19](data_portable_bar_2026-10-19/portable_live_20261020_v19.json)ではDGX最終batch 13のPID1685632とLabo最終batch 5のPID7544が稼働し、終端は未取得だった。
native reference265360の回収入口はRを確認してcompletion未実施で戻り、既存jobを重複起動していない。

17:15 JSTまでにnative reference265360はF・exit 0・run_count 1となり、専用controllerのcompleteとローカル回収を一度だけ実施した。
実walltime16分34秒・CPU16分24秒で、8,024,988 bytes・371 memberの全hash、元task markerとproduction、config・worker/controller completion・PBS終端を照合した。
[回収受理](data_tile_validation_2026-10-17/portable_condition_c1t0_native_reference_collected_v1/accepted.json) のSHA-256は `090ae150168777eddef377c6e1e2649c90382db2c96db0df65efe63d1941dd41` で、reference ZIPは `9001df2430e8a2603a54fabfc693276e973e9b9d0d00d6b2b32b0fa269de2d41`、export manifestは `fd8305e6c9353eec7e7e9973217ba0e1dbc0c7d308a7a25e7731019bd7b80903` である。
このcomplete・回収は使用済みとし、各PCの実parityや全群collector復旧の完了とは扱わない。

空いた枠に対してC1T1 sample partition 1の未使用preflightとexecuteを行い、qsubで265361を受け付けた。
17:18 JSTの実qstatでは265358がR・265361がQで、待機分を含む最大2ノードを維持した。
[追加sampling投入証跡](data_tile_validation_2026-10-17/low_c1t1_sampling1_dispatch_20261020_v1.json) のSHA-256は `edafec960a568327fe975ac099bd979229d9981622afc32a9901f17bb12ca424` である。
要求上限12時間30分をETAとして扱わず、全群collector復旧と最終集計は次の空き枠を要する。

## 17:39 JST：DGXの次条件開始とcollector復旧準備

DGXのC0T2再割当て最終batch13は実PID1685632の終了・terminal作成・既存pipelineによる回収まで確認した。
既存pipelineのforeground handleはexit 0となり、新たな回収を重複実行していない。
独立native reference265360を用いるC1T0のDGX full parityを一度だけ起動し、全88設定の値・診断・ACF比較は318.35秒でacceptedとなった。
保存値の再照合と5ファイルの回収・hash検査も通り、[parity受理](data_tile_validation_2026-10-17/portable_condition_c1t0_dgx_parity_dispatch_v1/accepted.json) を保存した。
実parity/runtimeと固定済み20群入力からbatch0を配置し、config SHA-256 `b29443a67b86c3cf789d96992174680d3c098b1756c35977cbdab6f310364893` で起動した。
17:39 JSTの [実プロセス観測](data_tile_validation_2026-10-17/c1t0_first_batch_live_20261020_v1.json) はPID1732128・20 worker・terminal未取得であり、全20群の完了を意味しない。
Laboの旧batch5はPID7544で実行中であり、終了とterminalを確認してから回収・C1T0 parity・配置・起動へ進む一度限りの引継ぎをlocal PID17396で開始した。
数値失敗や曖昧な実行応答を自動再試行せず、保存されたintent・logを確認する構成である。

失敗collectorの旧14ファイルと実qstat終端を検査するguard、および元submitの共有lock・最大2ノード・曖昧応答時の停止を保持する別worker/controllerを追加した。
Windowsはguard 16件とscheduler 12件、Linuxは統合28件が成功し、実元sampling・anchor・native bindingを確認するpreflightも通過した。
4時間上限の別collectorのqsubはまだ未実施であり、既存265358 R・265361 Qの2要求ノードから空きが出るまでlocal PID3092で監視する。
復旧context・source・scriptを外部固定し、空き枠の確認後にも共有lockの下で再検査する。
実再収集、native trace監査への接続、最終reportのretry backend選択は残り、低ノイズ正式完了数5/12は増えていない。

17:49 JSTまでにLabo旧batch5も終了し、一度限りの引継ぎによる24群の回収・転送・検査が成功した。
これでC0T2の全768群・67,584行が揃い、[snapshot v20](data_portable_bar_2026-10-19/mixed-collected-snapshot-20261020-v20.json) のpendingは0となった。
全行flag、診断未定義41,424行、区間未取得0、基盤失敗0を保持しており、全trace監査と独立referenceを結ぶ最終reportまでは正式完了に数えない。
Laboは次のC1T0 parityを開始し、DGX・Labo双方へbatch1の固定済み入力を先行配置した。
DGX batch1は20群・50,149,229 bytes・4,977 member、Labo batch1は24群・60,138,979 bytes・5,949 memberで、配置済み14ファイルの全hashを確認した。
batch1の配置は数値起動や完了の証拠ではない。
復旧controlと17:39 JSTまでの実運用証跡47ファイルを [保存manifest](data_tile_validation_2026-10-17/c1t0_recovery_progress_20261020_v1/manifest.json) へ保存し、SHA-256は `5241bc76032c75b02f5a688267acf68c64c9738d1651699bc4a57edc2686d610` である。

全群の最終contextは `output/portable_mixed_c0t2_distribution_v1` に作成し、SHA-256 `79f3aab5862d5bb4f36370140dde73a47317e640c82678414b9d6d204817a557` で130ファイルの転送を17:50 JSTに開始した。
配置先は `/home/user/workspace/mcmc4qec/20261020-portable-mixed-c0t2-inputs-v1`、記録先は `data_portable_bar_2026-10-19/mixed-c0t2-final-transfer-v1` である。
転送完了・最終config・最終report qsubはまだ受理しておらず、進行中の転送を重複実行しない。

## 18:27 JST：最終ジョブ設定の固定とPC後処理

C0T2の130ファイル・9,532,490,259 bytesの転送後hash照合が完了した。
最終configの初回準備では、venvのPython入口と実体を同じpathとする仮定で停止し、ジョブroot作成・qsub前に終了した。
実体を直接起動すると依存版が変わることを読み取り専用で確認し、元venvの入口・directory alias・実体・pyvenv.cfg・prefix・Python/package versionを明示的に結ぶ別wrapperを実装した。
元qsub wrapperを保持し、read_configとcomputeのPython検査だけを変更する構成で、共有lock・最大2ノード・曖昧応答時の停止は同じ関数本体を使用する。
Windows10 passed・1 skipped、Linux11 passedと実元venvでの検査が成功し、[実config](data_portable_bar_2026-10-19/mixed-c0t2-final-config-v2/accepted.json) のprepare/preflightを完了した。
config SHA-256は `4aa2210aafc1d0f25c987da488516f57f110bfe16413a2bf9a980999fbacf8b9`、sourceは156件、metadataは136件である。
local PID30804の監視は既存復旧collectorの投入後に空き枠を待つため、2つの監視から同時に枠を要求しない。
新wrapperへ固定した別report collectorもWindows/Linux各26件と実prepared configの読取確認を通過した。
実qsub、科学report完成、最終回収は未実施であり、低ノイズ正式完了数5/12は維持する。

DGXのC1T0 batch0/1を各20群・1,760行で回収し、host側の元input・parity・saved record検査と転送hash検査を通した。
batch0の最初の回収はPython隔離起動時のimport不足で止まり、旧出力先にparentだけが存在してexportがないことを実確認したうえで、別source・別出力先のv2入口で回収した。
ローカル独立検査も、現在のcheckoutの `__init__.py`・`decoders.py`・`submit_tile_seed_audit.py` がsampling時のソースと異なることを検出して停止した。
元ZIPのhashを照合して113ソースを隔離配置し、元の厳密なgateで [snapshot v2](data_tile_validation_2026-10-17/portable_condition_c1t0_snapshot_v2.json) を受理した。
検査済み20群・1,760行は全行flag、診断未定義772行、未回収748群であり、全条件の精度・混合を認定する結果ではない。
Laboの同一referenceに対する88設定parityも747.04秒で成功し、24 workerのbatch0を起動した。
18:27 JSTの実観測はDGX batch2 PID1784989・20 worker、Labo batch0 PID14832・24 workerで、両方ともlive・terminal未取得だった。
DGX batch3とLabo batch1の入力は先行配置済みで、数値起動は未実施である。

## 2026-10-20 18:49 JST：固定batchの逐次引継ぎ

DGX batch2の実terminal・PID終了を確認してv2入口で20群・1,760行を回収し、host上の検査と転送hash照合を通した。
DGX batch0〜2のhost回収は計60群となった。
batch0/1のローカル独立検査 [snapshot v3](data_tile_validation_2026-10-17/portable_condition_c1t0_snapshot_v3.json) は40/768群・3,520行・未回収728群、全行flag・診断未定義1,516行を保持して完了した。
batch2を含む独立検査は元source bindingを維持した `index_c1t0_collected_v1.py 4` で開始し、snapshot v4はこの記録時点で処理中である。

PCが手動操作待ちで空かないよう、[小仕様](portable_condition_serial_driver_spec_2026-10-20_ja.md)・受入・実装の順で既存入口を呼ぶ逐次driverを追加した。
Windowsのdriver受入は11 passed・0.67秒、既存Labo batch0の状態判定受入は7 passed・0.36秒だった。
科学計算や固定割当てを変えず、既存のexport・転送・stage・launch・collectionをforegroundで順番に実行する。
途中出力、既存の数値実行、source変更、入口の異常終了を検出した場合は停止し、自動再試行しない。
DGXはbatch3〜31のdriverをlocal実処理PID41548で起動し、batch3の実remote PID1792734の稼働を確認した。
Labo batch0は実remote PID14832で継続中であり、local実処理PID20712の別引継ぎが正常終端・元launcher受理を待ち、回収後にbatch1〜5のdriverを起動する。
元Labo launcherのlocal handleは引き続き維持し、同じbatchの二重実行は行っていない。
DGXの直近3 batchの実launch開始からSSH終了までは各約15分で、現在の1条件のPC後処理は転送・回収を含めて明朝を暫定目安とする。
これは現在のconditionの後処理見込みであり、クラスタ監査・残り条件・全科学検証の終了時刻ではない。

最終config、元Python binding、Windows/Linux受入、修正前の失敗記録、C0T2転送証跡を [73ファイルのmanifest](data_portable_bar_2026-10-19/mixed-final-readiness-20261020-v1/manifest.json) に保存した。
manifest SHA-256は `a24e9d4c910b47b55141da74c6bcb89199707aa415b796b1946826f77ade9c68` である。
クラスタは実監視のqstatで265358がR・265361がQの2要求ノードを維持し、復旧collectorとC0T2最終reportの追加qsubは引き続き未実施である。
正式完了数は5/12で、commit・push・公開操作は追加していない。
逐次driverとLabo引継ぎのsource・受入テスト・実intent・18:49 JSTの実PID観測を [25ファイルのmanifest](data_tile_validation_2026-10-17/c1t0_serial_execution_20261020_v1/manifest.json) に保存した。
manifest SHA-256は `c43b76fd5ca055b0abebe6404afa8fac84124c8df05b1a2b37dfba900741dbc7` で、保存時点ではDGX batch3とLabo batch0の実PIDがlive・terminal未取得だった。

## 2026-10-20 19:05 JST：復旧結果の監査入口と自動引継ぎ

元sampling時の113 sourceを使う [snapshot v4](data_tile_validation_2026-10-17/portable_condition_c1t0_snapshot_v4.json) が正常終了した。
60/768群・5,280行・未回収708群、全行flag・診断未定義2,440行を保持し、科学的な最終検証完了とはしていない。
DGXの逐次driverはbatch3の正常終了・回収とbatch4の転送・stage・launchまで自動で進んだ。
host回収は80群で、19:05 JSTの実remote観測ではDGX batch4 PID1799928がlive・terminal未取得だった。
Laboは既存batch0 PID14832がliveで、既存launcherと別の回収・逐次実行引継ぎを維持している。

復旧collectorから元環境trace監査への [明示接続](recovery_trace_execution_spec_2026-10-20_ja.md) を、小仕様・受入・実装の順で追加した。
旧復旧controlや元sampling/監査sourceは変更せず、復旧authority・qsub worker入口・ledgerを別namespaceで接続した。
監査のcheckpoint再復号とgroup計算、capacityの資源推定、共有lockと2ノード制限は元の処理を再利用する。
Windowsは分割実行で計45件、Linuxは統合45 passed・12.07秒の受入を通過した。
新configのhashは `c1fded776101ec8ff167d0652ceb431cc730d218655ef7222a4a49152d0ac898` である。
実元環境のconfig・sourceと旧265356の失敗guardを [読取確認](data_tile_validation_2026-10-17/recovery_trace_execution_native_v1/accepted.json) したが、復旧collectorの新正常終端authorityはまだ未取得である。
新監査のcapacity/full rootは未作成で、本番plan・preflight・qsub・監査・completeは未実施である。
最終BAR reportでの復旧backend選択と独立readerの接続も残っている。
既存投入監視は引き続き265358 R・265361 Qの2要求ノードを観測しており、追加qsubは行っていない。
新旧control・元監査source・受入ログ・native配置記録・snapshot v4は [44ファイルのmanifest](data_tile_validation_2026-10-17/recovery_trace_execution_progress_20261020_v1/manifest.json) に保存した。
manifest SHA-256は `c44b41aa5a26b400ba20f16367ae95d2c14e5cd51d686f37c746cabbc1a7d4b8` である。

## 2026-10-20 19:22 JST：最終readerの復旧backend選択

[最終reader/CLI](recovery_bar_final_reader_spec_2026-10-20_ja.md) に、配置済み復旧audit configを外部hashで固定して読む入口を追加した。
元report計算を変えず、復旧authorityと旧成果物の全file hashを最終input evidenceへ加え、reference照合中の変化も拒否する。
通常condition readerのmoduleやsource、動作中の復旧監査controlは変更していない。
Windows64 passed・34.42秒、Linux64 passed・17.24秒の受入と、実配置済みaudit configのbootstrap確認を通過した。
fixtureは全12条件の合成768群の分母とcontext失敗を保持するが、実trace/decoder/referenceの照合完了とは扱わない。
本番用のfinal qsub wrapper、全38 batchのcontext作成/転送、report回収bindingは未接続である。

DGXの自動driverはbatch4の20群・1,760行も正常回収し、host回収は100群となった。
batch5の入力export・転送・stageを終えてlaunchへ進んだ。
Labo batch0の実PID14832は19:18 JSTの観測でもlive・terminal未取得だった。
独立readerで完了した範囲は引き続きsnapshot v4の60群であり、host回収100群とは区別する。
クラスタは265358 R・265361 Qの2要求ノードを維持し、復旧collectorとC0T2最終reportの追加qsubはまだ行っていない。
最終reader source・受入・native bootstrap・PC進捗は [30ファイルのmanifest](data_tile_validation_2026-10-17/recovery_bar_final_reader_progress_20261020_v1/manifest.json) に保存した。
manifest SHA-256は `6ae12850564e0d158f944b0b0f41ea4affecfa54fd735cf77f17415d881b65c2` であり、19:24 JSTの実観測ではDGX batch5 PID1842936とLabo batch0 PID14832がlive・terminal未取得だった。

## 2026-10-20 19:37 JST追記：復旧collector投入と最終qsub受入

sampling前半265358は19:31:46 JSTにF・exit 0・run_count 1、walltime4時間24分28秒で正常終了し、後半265361がRへ移った。
既存監視が復旧collectorをqsubで一度だけ投入し、265362のRを確認した。
同時に要求中のノードは2であり、C0T2最終reportの監視は次の空き枠を待っている。
PC側はDGX batch0〜5の120群、Labo batch0の24群を回収し、host側保存値検査と転送hash検査を通過した。
ローカルの独立再検査はsnapshot v4の60群のままであり、回収144群をそのまま最終科学受理数としない。

復旧BAR最終readerへ接続するqsub wrapperを小仕様・受入テスト・実装の順で追加した。
元の共有lock・最大2ノード・一度限りの投入・曖昧応答保持を維持し、元venvと復旧authority、sampling入力・旧成果物・full監査terminal・reportのhashを照合する。
Windows30 passed・3 skipped・3.45秒、Linux33 passed・4.55秒で、実投入と科学readerをfixtureに置き換えた結合試験を含む。
本番final config・全38 batchのcontext生成/転送・実qsub・report回収bindingは未完了である。
詳細と失敗を含む受入範囲は [仕様と結果](recovery_bar_final_qsub_spec_2026-10-20_ja.md) に記録した。
source・ログ・19:39 JSTの実qstatとPCプロセス観測を [35ファイルのmanifest](data_tile_validation_2026-10-17/recovery_bar_final_qsub_progress_20261020_v1/manifest.json) に保存した。
manifest SHA-256は `df69403861cf01cace4d63913e212b9735330aca2794f7e22407dfd663b19a6f` であり、DGX batch6 PID1850435、Labo batch1 PID6556のliveを確認した。

## 2026-10-20 19:51 JST追記：共有保存物の回収とcontext作成

元batch0の固定recipeとstaging証跡に従い、DGX・Laboからparityとpredecessorを各7ファイル回収した。
転送前後・local保存後のbyteを照合し、計12,971,850 bytesを保存した。
元samplingソースを復元した環境で各88設定の保存parity・診断・ACFをnative referenceと照合し、最終providerの初回predecessor検査も通過した。
この実入力比較は3.86秒であり、BARや復号の新規計算は行っていない。

完全なindex・registryと共有保存物から最終providerのcontext・転送planを作る処理を追加した。
Windows50 passed・5.66秒、Linux50 passed・0.68秒で、失敗群・診断・未取得行の分母保持、欠落・重複・変更の拒否と合成context作成を検査した。
実snapshot v4の60群を使うと、未完了のため出力を作らず拒否した。
実全群index・本番context、転送処理の新条件への接続、最終qsubとreport回収は未完了である。
詳細と受入結果は [仕様](portable_condition_distribution_spec_2026-10-20_ja.md) に保存した。
19:51 JSTの実qstatはsampling265361と復旧collector265362がRで、2ノードを維持している。
旧Labo batch0のlauncher session17747はexit 0で終了確認し、batch1以降を扱うsession23921とDGXのsession39752は稼働を維持している。
source・受入・共有保存物・実入力照合と拒否記録・実プロセス観測は [49ファイルのmanifest](data_tile_validation_2026-10-17/condition_distribution_progress_20261020_v1/manifest.json) に保存した。
manifest SHA-256は `be037b70bf2f307ff64c5fed2657cd89128be4a5557feed1eb9de97a4ab30522` で、19:52 JSTの実観測でもDGX batch6 PID1850435とLabo batch1 PID6556がliveだった。

## 2026-10-20：条件別contextの転送接続

既存mixed転送処理の実装を変更せず、別namespaceで新condition planとcontextの検査へ接続した。
固定assignmentの全batch、receiptの分母、元export manifest、共有保存物とnative referenceの結び付けを検査する。
追加Windows22 passed・42.35秒、Linux統合72 passed・7.11秒で、実builderによる合成入力・SSH/scpを置き換えた転送・破損拒否・通信失敗時の予約保持と無再試行を確認した。
実全群indexとcontextがまだ揃っていないため、本番転送は未実施である。
DGX batch6も回収され、host側で検査・転送照合を終えた群はDGX140＋Labo24＝164群になった。
ローカル独立検査はsnapshot v4の60群のままであり、正式な低ノイズ比較の完了数は5/12条件から増えていない。
source・受入・回収増分・実qstat・両PCの実PID観測を [25ファイルのmanifest](data_tile_validation_2026-10-17/condition_transfer_progress_20261020_v1/manifest.json) に保存した。
manifest SHA-256は `ccbb41871dc3a5567f59fd8b1bf752bcab5a1aa90cc0a4793e5884df8fc933ce` で、19:59 JSTにDGX batch7 PID1858268とLabo batch1 PID6556のliveを確認した。

## 2026-10-20：復旧最終reportの回収接続と制御ファイル配置

元最終collectorを変更せず、C1T0・復旧wrapper・元venvを固定した別collectorを実装した。
configとsource全体をimport前に検査し、snapshot内で復旧authority・入力証跡・reader sourceも照合する。
Windows31 passed・8 skipped・3.01秒、Linux39 passed・1.57秒だった。
追加8件はimport gateと実qsub wrapperからcollectorへの接続であり、PBS・監査I/O・reportはfixtureに置き換えている。
既存の転送前後snapshot比較、失敗時の記録保持と無再試行も維持した。
本番用の新規directoryへ22制御ファイルを配置し、元venvからのimportとnative referenceの113ソース、75 import先を照合した。
最終config・preflight・qsub・report実行・本番回収は未実施である。
詳細は [回収仕様と結果](recovery_final_collection_spec_2026-10-20_ja.md) に記録した。
source・受入・本番制御ファイルの配置照合・実qstat・両PCの実PID観測を [51ファイルのmanifest](data_tile_validation_2026-10-17/recovery_final_collection_progress_20261020_v1/manifest.json) に保存した。
manifest SHA-256は `d4aa40677cb3467ea101fc3c2c4314ec1ab88d74ced5c82c67f1e6cbd546c341` で、20:10 JST前後にDGX batch7 PID1858268とLabo batch1 PID6556のliveを確認した。

## 2026-10-20：復旧監査とC0T2最終回収の自動引継ぎ

復旧collector265362の正常終端からcapacity/full監査へ進む引継ぎを、Windows30 passed・2.23秒と実control照合後にlocal PID47332で起動した。
監査qsubの前にはC0T2の既存最終投入監視を優先し、共有lockと待機中を含む最大2ノードを維持する。
C0T2の最終ジョブの正常終端から既存complete・既存collectorへ進む別引継ぎも、Windows13 passed・0.84秒の後にlocal PID34196で起動した。
後者はqsubを呼ばず、投入済みjobの固定ID・script・resource・正常終端を検査して13成果物を回収する。
いずれも変更操作は一度だけとし、曖昧な応答で同じ計算やcompleteを再試行しない。
実装・受入の範囲は [復旧監査引継ぎ](recovery_audit_handoff_spec_2026-10-20_ja.md) と [最終回収引継ぎ](portable_mixed_final_handoff_spec_2026-10-20_ja.md) に記録した。
20:24 JST前後の実qstatは265361と265362がRであり、両引継ぎの後段操作は未実施だった。
DGX batch7まで160群とLabo batch0の24群をhost側で回収済みだが、ローカル独立検査は60群、低ノイズ正式比較は5/12条件のままである。
両引継ぎのsource・受入結果・起動証跡・実qstat・DGX/Laboのlive観測を [49ファイルのmanifest](data_tile_validation_2026-10-17/automatic_handoffs_progress_20261020_v1/manifest.json) に保存した。
manifest SHA-256は `52eb9cd2617bd702374ea44ac554dbb649b7df03e71473362f9125c38cf5d7ab` である。

20:29 JSTに次のtile288 bit-flip p=.001のanchorについて、[実クラスタpreflight](low_remaining_generator_order_2026-10-20_ja.md)を実施した。
source・native・runtime・固定planの照合は成功したが、実応答はslot_available=falseのためqsubしていない。
当該preflightは使用済みとして記録し、既存のC0T2最終投入・復旧監査を優先する。

## 2026-10-20：未投入条件の初回collector資源枠

C1T0旧collectorの2時間walltime失敗を踏まえ、残る5条件の初回collectorに4時間枠を明示する隔離backendを追加した。
元sampling sourceと検査内容を維持し、collectorの保存先・資源を分け、旧試行のあるrootでの使用を拒否する。
Windows21 passed・11.57秒、Linux21 passed・2.40秒で、全失敗のfixtureも768 group・192 anchorを保持し、欠落・重複・source/resource不一致を拒否した。
実クラスタの5 planと初回collectionの候補状態も照合したが、scheduler・worker・authority・後続監査/最終readerとの接続は未完了である。
実装・検証範囲は [小仕様と受入](planned_collection_budget_spec_2026-10-20_ja.md) に記録し、source・ログ・実入力照合を [11ファイルのmanifest](data_tile_validation_2026-10-17/planned_collection_backend_sources_v1/manifest.json) に保存した。
manifest SHA-256は `8b030bb3add3bf952a4a87e2227dcd2f86c9d8fde4ca5173810e456027183682` である。
20:37 JSTまでにDGX batch8の20群を回収し、C1T0はhost側204/768群、ローカル独立検査60群である。
低ノイズ正式比較は5/12条件のままであり、新たなcollectorの本番実行や科学的受理は行っていない。

## 2026-10-20：初回4時間collectorの投入・worker接続

元qsub制御と共有lock・2ノード上限を維持し、planned_collection bindingを持つscheduler・workerを別sourceへ追加した。
初回worker結合試験は1 failed・17 passedで、元のPBS縮約がrun_countを保存しない問題を検出した。
新collectorのnamespaceでrun_countを保存する修正を行い、元samplingのterminal形式は維持した。
修正後の統合受入はWindows51 passed・18.66秒、Linux51 passed・5.69秒だった。
正常終端の封印から全task index照合までをfixtureで接続し、曖昧なqsub応答、失敗worker、再実行、欠落taskを拒否する。
本番用の5 configを別native配置で固定し、元acceptance manifestと全input、control、production/partition manifest、runtimeを照合した。
これは上流jobの正常終端を確認するpreflightや本番collector実行ではなく、authorityと後続監査・最終readerへの接続は未完了である。
source・失敗と成功のログ・native検証・5 configは [26ファイルのmanifest](data_tile_validation_2026-10-17/planned_collection_protocol_sources_v2/manifest.json) に保存した。
manifest SHA-256は `3b7b546a8600852cdf1f6ce695860e48c3ad4385b5f8af2886d7821771ec58c9` である。
20:47 JSTの実観測でDGX batch9のPID1908956とLabo batch1のPID6556はliveだった。
既存の復旧監査・C0T2投入と最終回収の3監視も実行中であり、今回新しいqsubは行っていない。

## 2026-10-20：初回4時間collectorからtrace監査への接続

初回collector用のauthority、監査/資源backend、qsub接続とworkerを別sourceへ追加した。
sealed terminalだけに依存せず、実qstat・worker開始/完了・元入力・全task indexを再照合し、既存C1T0の復旧authorityとは別の記録を保持する。
Windows統合51 passed・30.26秒と追加結合2 passed・3.76秒、Linux統合53 passed・12.61秒だった。
全失敗fixtureの768 group・192 anchorを保持し、completeからauthorityへ接続した後にtaskを欠落させて関連hashを更新しても拒否することを確認した。
元の監査計算・group処理・資源推定を維持し、qsub・共有lock・待機中を含む2ノード上限を適用する。
別native配置に5条件のconfigを固定し、元bundleと全input・collector config/control・plan/runtime・未使用の監査rootを読み取り照合した。
本番collectorの完了authority確認、監査plan・qsub・実行は未実施であり、最終BAR readerへの接続は未完了である。
詳細は [小仕様と受入](planned_trace_audit_spec_2026-10-20_ja.md)、source・ログ・native配置・実config・実機観測は [47ファイルのmanifest](data_tile_validation_2026-10-17/planned_trace_execution_sources_v1/manifest.json) に保存した。
manifest SHA-256は `56b2646e229089fde456560a5da524c7d931800042a8ef60da662d08512c4122` である。
21:02 JSTまでにLabo batch1の24群も回収・転送照合を確認し、DGX200群・Labo48群、計248/768群になった。
Labo batch1の転送receipt SHA-256は `2f202f6343ee640c2ddf6addbe0e899257e0672a2169b54efa7f1a57b2398dd9` であり、既存driverはbatch2のexportを進めている。
ローカル独立検査は60群、低ノイズ正式比較は5/12条件のままである。

## 2026-10-20：初回collector条件の最終reader・qsub・回収

初回4時間collectorを使うC1T1・C1T2・C3T0・C3T1・C3T2の最終BAR reader/CLIを、既存C1T0復旧処理とは別のsourceへ追加した。
planned_collection_authorityと全入力のhashをreportへ結び付け、元の全192 seed・768群・67,584行の集計とreference照合を維持する。
小仕様・受入・実装の順で進め、reader/CLIはWindows65 passed・26.02秒、Linux65 passed・12.04秒だった。
元schedulerの共有lock・Qを含む最大2ノード・一度限りのqsubを保つ接続は、Windows30 passed・3 skipped・3.97秒、Linux33 passed・4.19秒だった。
source・実装前の不足module検出・受入・5実configのbootstrapを [58ファイルのmanifest](data_tile_validation_2026-10-17/planned_bar_final_progress_20261020_v1/manifest.json) に保存した。
manifest SHA-256は `2f6f3b83c62fc4e2267fa3ba41f09ce3ed4522dbe4115af7d84a69072543d10a` である。

続いてcase/target_indexを外部指定する5条件用のreport回収を追加した。
13成果物の転送前後のhash、正常PBS終端・実行回数1・job/script/resource、authorityとreader source、条件と全行数を確認する。
Windows46 passed・8 skipped・3.21秒、Linux54 passed・1.47秒で、Windows未実施のPOSIX import/PBS結合8件はLinuxで実行した。
Linux結合は実wrapperのprepareからcompute/complete・回収snapshotまでを通すが、PBS応答と科学I/Oはfixtureに置き換えている。
本番用22 controlを別directoryへ固定し、元bundle manifestに基づく113ソース・75 import先と5実監査configを照合した。
source・ログ・実配置・実プロセス観測は [80ファイルのmanifest](data_tile_validation_2026-10-17/planned_final_collection_progress_20261020_v1/manifest.json) に保存し、SHA-256は `9bb11280e990ac9e29036305a536fe51dcd889db981041c31cac766d7f512b1d` である。
これら5条件の実collector authority/full監査・最終config・qsub・report回収は未実施であり、fixture成功を科学的受理と扱わない。

21:21 JSTまでにDGX batch10の20群も回収し、C1T0はhost側268/768群・ローカル独立検査60群となった。
DGX batch11のPID1960148とLabo batch2のPID19744はliveである。
復旧collector265362は21:20:36 JSTに正常終了し、walltimeは1時間48分17秒、Exit_status 0・run_count 1だった。
既存引継ぎがcompletion readerを一度だけ実行し、recovery_collected=true・scientific_cohort_accepted=falseを確認した。
続くcapacity監査のplan/preflightも成功したが、投入は空き枠待ちである。
空き枠の優先引継ぎによりC0T2最終集計を21:21:00 JSTにqsubで投入し、job265366のRを確認した。
sampling265361とfinal265366の2ノードを維持し、最終集計の完了・回収監視は既存driverへ任せて重複実行しない。
実qstatと投入/回収受理recordのhashは [観測記録](data_portable_bar_2026-10-19/mixed-c0t2-final-dispatch-observation-v1.json) に保存し、そのSHA-256は `c852ed7a28b279c802f52276124aa19a515cf2262d7b7c5e9e11ef4469419c92` である。
低ノイズ正式完了数は引き続き5/12条件であり、公開候補の変更・追加commit/push・公開操作は行っていない。

## 2026-10-20：C1T1生成から回収・監査への自動引継ぎ

固定したC1T1の3投入receiptと実PBS正常終端を要求する別driverを、小仕様・受入・実装の順で追加した。
Windows25 passed・1.08秒で、段階順序、先行監査待ち、実ノード数、結果不一致、応答不明の再実行拒否を確認した。
既存の一度限り実行・PBS終端判定はhash固定して再利用し、稼働中helperを変更していない。
実collector/audit configと元bundleを含む197ファイルのbootstrapは成功し、anchor265357とsampling前半265358はF・Exit_status 0・run_count 1、後半265361はRだった。
21:29 JSTまでにlocal PID13508でdriverを起動し、後半265361の実qstatを観測して待機している。
新driver source SHA-256は `d2c1e4a577780c5c2b02b265b51ced13be4792841c3d83656d7729b794aef4d9` である。
collector投入前には先行C1T0復旧full監査の受理記録と実PBS正常終端を確認し、実要求ノード数の観測と既存schedulerの共有lock・2ノード上限を維持する。
監視起動時点ではC1T1 collectorの本番preflight・qsub・監査は未実施であり、科学的受理はfalseのままである。
source・受入ログ・readiness・起動・実local processとPBS観測は [57ファイルのmanifest](data_tile_validation_2026-10-17/planned_c1t1_handoff_progress_20261020_v1/manifest.json) に保存した。
manifest SHA-256は `e7118b5ebc78d83bc018a34a4779e2f26a46fbb1735dd2f8280a35542aea3a59` であり、実観測時はsampling265361とC0T2 final265366の2ジョブがRだった。
今後のC1T1 collector・capacity/full監査はこのdriverが担当し、手動の重複実行を避ける。
低ノイズ正式完了数5/12、C1T0のhost側回収268/768群・ローカル独立検査60群を、この引継ぎの起動によって増やさない。

## 2026-10-20：次条件の生成preflightと5 native referenceの準備

C1T2のsample 0/1について未使用の実クラスタpreflightを一度ずつ並列に実施し、両方ともreturncode 0・ambiguous=false・qsub_executed=falseだった。
両応答でslot_available=falseを確認し、新しいqsubは行っていない。
anchor 0を含む3 preflightは使用済みとなり、3 executeはいずれも未使用である。
使用済み操作と既存引継ぎを優先する投入順を [生成順文書](low_remaining_generator_order_2026-10-20_ja.md) に追記した。

C1T1・C1T2・C3T0・C3T1・C3T2のnative single-group parity referenceを、既存worker/controllerを変更せず、別configとPBS scriptで準備した。
対象は各条件の事前固定groupと全88設定であり、独立MC referenceや全cohortの科学的受理とは区別する。
受理済みC1T0 referenceのZIP・record・marker・回収記録のhashを照合し、保存実測は978.7308733696118秒・715.29296875 MiBだった。
元job265360も実qstatでF・Exit_status 0・run_count 1と同じscript/resourceを再確認した。
初期資源は実測の4倍・rung数比・export余裕を根拠とし、既存と同じ4時間・32 GBを下限とした結果、全5条件が1ノード・1 CPU・32 GB・4時間となった。
別noise/targetの所要時間・必要memoryや同精度到達時間の保証ではない。
元113 source、固定生成planと実metadata、既存controlを照合して5件のq.prepare・q.submit(execute=False)が成功した。
各条件の実qsub・数値計算・raw入力の存在/整合性検査は未実施であり、準備完了を実reference成功と扱わない。
各job rootとconfig/scriptのhashは [reference準備記録](planned_native_reference_spec_2026-10-20_ja.md) と実accepted.jsonへ保存した。
source・資源根拠・実config/script・生成preflight・実機観測を [75ファイルのmanifest](data_tile_validation_2026-10-17/planned_next_conditions_readiness_20261020_v1/manifest.json) に保存し、SHA-256は `09c1fcafe304f940d6d5a912b34ac4e89bded0ce8555e263207a8dcd05db5fad` である。

21:42 JST前後の実観測ではDGX batch12のPID1967670、Labo batch2のPID19744がliveで、sampling265361とC0T2 final265366もRだった。
DGX batch11の回収を確認し、C1T0のhost側回収は288/768群、ローカル独立検査は60群である。
低ノイズの正式完了は引き続き5/12条件であり、新しい数値試験・追加commit/push・公開操作は行っていない。
<!-- planned-condition-assignment-20261020 -->

## 2026-10-20 21:51 JST：残る5条件のPC割当て

C1T1/C1T2/C3T0/C3T1/C3T2の全768群を、各stratumでDGX162 seed・Labo30 seedへ固定した。
直近の実C1T0 batch時間を外部hash付き回収証跡とZIP/completionから照合し、191通りの割当てを比較した。
各条件はDGX648群・33 batchとLabo120群・5 batchとなり、元クラスタのmetadata照合と既存contract・初期cohort indexの受入を通過した。
57ファイルの[保存manifest](data_tile_validation_2026-10-17/planned_condition_assignments_v1/manifest.json)と[仕様・結果](planned_condition_assignment_spec_2026-10-20_ja.md)へ記録した。
現在のC1T0割当ては変更せず、未来の5条件について数値処理やqsubを開始したわけではない。
5つの既存引継ぎ・PC driverのsessionは継続中で、実qstatではsampling265361・final265366の2ジョブがRだった。

## 2026-10-20 22:02 JST：C0T2完了と次条件の入力export

C0T2の最終集計265366は21:54:56 JSTにF・exit 0・run_count 1、walltime33分55秒で終了した。
既存handoffによる終端受入と13点の回収が完了し、reportの全67,584行・352設定・192 seedを確認した。
事前の長い設定を同じ集約処理で抽出し、[結果と適用限界](low_c0t2_recovered_result_2026-10-20_ja.md)を保存した。
全設定・全seedでflag・high R-hat・low ESSがあり、長い8設定の参照被覆件数は174〜180/192で、名目95%被覆を保証しない。
正式比較はtile72の6条件を完了し、全体で6/12条件となった。
元collectorの固定成果物は変更せず、集約scriptと元処理との差分、集約JSONを別保存した。

残る5条件の[入力export adapter](planned_input_export_spec_2026-10-20_ja.md)を別directoryへ作成した。
anchor 0とsample 0/1の3件すべての実投入receiptと実PBS終端を要求し、元raw exporterとarchive readerの検査を保持する。
実remote処理を合成PBSで実行する結合試験を含め、Windows/Linux各38件が成功した。
C1T1の実3投入receiptと事前固定したmetadataのローカル照合は成功したが、本番export・PC配置・parityは未実施である。
source・受入・再現手順・実観測を[51ファイルのmanifest](data_tile_validation_2026-10-17/planned_input_export_progress_20261020_v1/manifest.json)へ保存し、SHA-256は `63cce1b4d0c57f3ea66b25bcd4756f5a85193d8fbacef53fe3fa1f2722624625` である。
空いたクラスタ枠には既存recovery handoffがcapacity監査265367をqsubで投入し、sampling265361のRと監査265367のQで2要求ノードを維持した。
DGX batch13・Labo batch2の実PIDがliveであることを確認し、C0T2完了handoffのterminal session20616だけを回収した。
追加commit/push・公開操作は行っていない。

## 2026-10-20 22:09 JST：次条件のPC lifecycle

残る5条件について、固定割当てを認証してから動く6つのPC operator adapterを別directoryへ作成した。
配置、初回・後続stage、初回・後続launch、回収の条件名と保存先を切り替え、条件取り違えを副作用前に拒否する検査を加えた。
数値runner・共通stage/collectorと既存remote処理本文は維持した。
Windows32件・0.83秒、Linux32件・0.27秒の受入と、両環境で6 CLIの起動確認を完了した。
[44ファイルのsource・受入証跡](data_tile_validation_2026-10-17/planned_pc_lifecycle_acceptance_v1/manifest.json)と[実施範囲・再現手順](planned_pc_lifecycle_spec_2026-10-20_ja.md)を保存した。
初回native reference回収・条件間parity・serial driverへの新条件接続は未完了であり、この変更による実PC処理はまだ起動していない。
既存C1T0 driverはDGX batch12の回収後にbatch13へ進み、Labo・監査・C1T1引継ぎの各sessionも継続中と確認した。
クラスタはsampling265361がR、capacity監査265367がQで、最大2要求ノードを維持した。
低ノイズ正式比較は6/12条件で、公開候補の変更・追加commit/push・公開操作は行っていない。

## 2026-10-20 22:17 JST：次条件のnative reference回収

固定済み5条件のconfig・script・資源と、実qsub戻り値の外部hashを照合するreference collectorを別directoryへ追加した。
実PBSのowner・script・資源・F・exit 0・run_count 1を確認し、既存controllerのhashを検査してからcompleteを一度だけ呼ぶ。
元のarchive検査と転送後の同一性検査を維持し、非終端時は回収保存先を予約しない。
5条件の合成転送を含むWindows31件・0.66秒、Linux31件・0.13秒の受入とCLI起動確認を完了した。
結合試験ではPBS・転送・archive readerを置き換えており、本番payload・本番completeの受理ではない。
[24ファイルのsource・固定config・ログ](data_tile_validation_2026-10-17/planned_reference_transfer_acceptance_v1/manifest.json)と[実行手順](planned_reference_transfer_spec_2026-10-20_ja.md)を保存した。
5条件の実reference投入・回収と、PC初回parity・serial driverの新条件接続は未実施である。
22:17 JST前後の実qstatはsampling265361がR、capacity監査265367がQで、最大2要求ノードを維持していた。
公開候補の変更、追加commit/push、公開操作は行っていない。

## 2026-10-20 22:26 JST：PC初回parityと全batch driver

新条件のnative reference受理と、前条件の最終host batch回収を外部pin付きregistryで結ぶparity入口を実装した。
条件順はC1T0→C1T1→C1T2→C3T0→C3T1→C3T2に固定し、途中batch・別host・異常回収を拒否する。
既存のremote parityと保存結果の再検査本文を維持し、Windows25件・1.08秒、Linux25件・0.50秒を通過した。
[31ファイルの証跡](data_tile_validation_2026-10-17/planned_pc_parity_acceptance_v1/manifest.json)と[registry仕様](planned_pc_parity_spec_2026-10-20_ja.md)を保存した。

各hostの全割当てをexport→preposition→初回parity→stage→launch→collectへ接続するserial driverも追加した。
固定済み3受入のsource/input、実generator registry、native/前条件回収を照合し、既存の途中成果物や失敗操作を自動再試行しない。
Windows31件・0.58秒、Linux31件・0.21秒とCLI起動確認が成功し、[67ファイルのsource・ログ](data_tile_validation_2026-10-17/planned_pc_serial_acceptance_v1/manifest.json)と[起動手順](planned_pc_serial_spec_2026-10-20_ja.md)を保存した。
本番reference投入・回収、実parity registry作成、新driverの起動は未実施である。
旧C1T0 driverは変更せず、DGX batch13の回収からbatch14のlaunchへの進行を確認した。
既存4 sessionは継続中で、クラスタはsampling265361がR・capacity監査265367がQだった。
数値の正式比較は6/12条件のままであり、公開候補の変更・追加commit/push・公開操作は行っていない。
## 2026-10-20 22:41 JST：次条件への自動引継ぎ

C1T1のnative reference引継ぎをlocal PID46972で起動し、sampling265361の正常終端を待っている。
実referenceは未投入であることを確認し、既存controllerのpreflightと37 source・input bindingを照合した。
Windows/Linux各20件の受入sourceとログは[native引継ぎ記録](planned_native_handoff_spec_2026-10-20_ja.md)に保存した。
PC側は前条件の全host batch回収と新referenceの回収を待つ引継ぎをDGX用PID13260・Labo用PID19728で起動した。
Windows/Linux各19件の受入sourceとログは[PC引継ぎ記録](planned_pc_handoff_spec_2026-10-20_ja.md)に保存した。
既存の科学計算・配布候補・稼働中driverは変更せず、新条件のreference投入・PC parity・数値workerはまだ実行していない。
既存4 sessionと新しい3 sessionをpollし、継続を確認した。
DGXはbatch14回収を終えてbatch15のPID2025839、Laboはbatch2回収を終えてbatch3のPID20824がliveであり、正式完了数は引き続き6/12条件である。

## 2026-10-20 22:49 JST：C1T2生成の待機処理

次のtile288 bit-flip p=.001の[生成引継ぎ](planned_c1t2_generation_handoff_spec_2026-10-20_ja.md)をlocal PID44160で起動した。
Windows/Linux各14件の合成受入とCLI起動、実3preflight receipt・固定生成plan・先行driver sourceの照合を通過した。
C1T1 full監査とnative referenceの正常完了を優先し、その後anchorの正常終端を確認してsampling2分割を空き枠へ進める。
新しいqsubと数値計算はまだ実施しておらず、sampling265361がR、capacity監査265367がQの計2要求ノードを維持している。

## 2026-10-20 22:59 JST：C0T2の計時入力候補

C0T2最終reportの実venv wrapperに合わせ、計時readerのsnapshot依存1か所を別配置で修正した。
Windows/Linux各16件の受入を通過し、初回Linux配置でplatform fixtureが不足した失敗記録も保持した。
元configのsource・metadata・Python bindingを照合し、実子環境108 source・137 native binaryと157入力のmetadata候補を確認した。
元最終job265366の実測は2035秒・1,352,040,448 byteで、独立計時は未実施である。
同じWSS reference監査を参照する6候補・6未完了の部分inventoryへ更新した。
source・実証跡は[C0T2計時接続記録](low_timing_portable_venv_spec_2026-10-20_ja.md)に保存した。
DGX batch15の回収とbatch16のPID2033529のliveを確認し、現在条件のhost側回収は392/768群になった。
8 sessionの継続をpollで確認し、新規qsubは行っていない。

## 2026-10-20 23:09 JST：全回収後の独立検査・転送

C1T0の全38 batch回収後、既存index builderの未使用version 5、context作成と転送を一度ずつ実行する引継ぎをlocal PID40448で起動した。
初回の実入力照合は過去test harnessのhash差で予約前に停止し、失敗記録と旧受入sourceを保持した。
実装sourceのhash照合を維持し、test harnessと実行時sourceの範囲を分けた修正後はWindows/Linux各11件が成功した。
詳細と証跡は[引継ぎ記録](c1t0_collection_finalize_handoff_spec_2026-10-20_ja.md)に保存した。
両PCのserial driverはまだ未完了で、全群index・context・転送・最終qsubは未実施である。
9 sessionの継続をpollし、実qstatはsampling265361がR、capacity監査265367がQだった。

## 2026-10-20 23:15 JST：残るdepolarizing生成のpreflight

C3T0/T1/T2のanchor 0・sample 0/1、計9件の未使用preflightを条件ごとに3件ずつ並列で実行した。
全件が成功し、source・native binary・runtime・固定plan・PBS scriptと旧controllerの終端を照合した。
全件でslot_available=false・qsub_executed=falseであり、9 executeは未使用である。
使用済みpreflightを再実行せず、既存C1T2生成引継ぎと先行監査の投入順を維持する。
実sourceと応答を[52ファイルのmanifest](data_tile_validation_2026-10-17/c3_generator_preflights_v1/manifest.json)に保存した。
実qstatはsampling265361がR、capacity監査265367がQの計2要求ノードだった。
DGXのbatch16は計算を終えて回収へ進み、PCの2つの既存sessionの継続をpollで確認した。

## 2026-10-20 23:28 JST：tile72低ノイズ6条件の比較追補

[6条件・96設定の比較](low_long_six_comparison_result_2026-10-20_ja.md)を追加し、旧5条件の80設定を変更せず、回収済みC0T2 reportの長い16設定を加えた。
C0T2はreport抽出であり、今回保存BAR行の独立算術レビューを追加したとは扱わない。
受入9件、保存sourceによるCSVのbyte一致、旧80設定の値の保持、描画全96点の照合とPNGの目視確認を完了した。
6条件の24組のkernel・初期化について、誤差法間の点推定のbias/RMSEと混合診断の一致を確認した。
追加条件ではblock32のreference重なり143–154/192に対し、block1024は174–180/192、cross_chainは175–180/192だったが、全seedの診断flagは残る。
有限referenceとの重なりを真値の被覆保証とせず、公開既定を変更しない。
9つの既存sessionをpollし、DGX batch16の回収完了とbatch17への移行を確認した。
23:27 JSTの実process観測ではDGX batch17のPID2076332とLabo batch3のPID20824がliveだった。
host側回収はDGX340群・Labo72群の計412/768群であり、全群ローカル独立検査の完了数とは区別する。
正式完了数は6/12条件を維持し、新しいqsub・commit・push・公開操作は行っていない。

## 2026-10-20 23:37 JST：C1T0最終設定作成への引継ぎ

[最終設定作成処理](c1t0_final_preparation_spec_2026-10-20_ja.md)を別配置へ追加し、Windows/Linux各18件の受入、元クラスタvenv・135 reader source・復旧audit bootstrapの照合を通過した。
先行の全群回収・転送とfull監査が正常完了してから一度だけ設定を作る待機処理はWindows/Linux各6件を通過し、local PID34812で起動した。
この引継ぎは設定作成までを担当し、qsub・最終report実行・回収は行わない。
資源要求の初回上限は1 CPU・32 GB・12時間とし、先行C0T2最終集計の実測33分55秒・resident memory 1,320,352 KiBを根拠に保存する。
tile288の実時間は未計測であり、要求12時間をETAとは扱わない。
現時点では本番config・preflight・qsubも未実施で、先行2処理の完了を待っている。
既存9 sessionと新待機sessionをpollし、全10 sessionの継続を確認した。
DGX batch17の回収が終わってbatch18のexportへ進み、host側回収はDGX360群・Labo72群の計432/768群である。
実qstatはsampling265361がR、capacity監査265367がQの計2要求ノードであり、追加投入は行っていない。

## 2026-10-20 23:44 JST：C1T0最終qsubから回収への引継ぎ

[最終設定から投入・回収への引継ぎ](c1t0_final_execution_handoff_spec_2026-10-20_ja.md)を実装し、Windows/Linux各24件の受入と実復旧wrapperのbackend import・CLI起動を確認した。
設定作成の正常完了を待ち、固定preflightの再照合、最大2要求ノードの空き待ち、既存wrapperによるqsub、同じjob IDの正常終端確認、既存collectorによる回収を一度ずつ進める。
空きなし・qsub未実施を明示する厳密な応答以外は再投入せず、曖昧応答・例外を保存して停止する。
local PID21844で起動し、先行設定作成driverのPID34812とともに完了待ちである。
新しい最終qsub・report・回収はまだ未実施で、正式完了数は6/12条件を維持する。
既存10 sessionと新引継ぎをpollし、全11 sessionの継続を確認した。
DGXはbatch18のlaunchへ進み、host側回収は432/768群のままである。
実qstatはsampling265361がR、capacity監査265367がQで、要求は引き続き計2ノードだった。

## 2026-10-20 23:57 JST：C0T2独立算術とクラスタ終端

[C0T2の保存BAR行の独立算術レビュー](low_c0t2_arithmetic_review_result_2026-10-20_ja.md)を追加し、38 archive・768 group・全67,584行・352設定の11,968値がreportと最大差0で一致した。
既存図表の長い16設定の432値も最大差0だった。
初回のkernel mapping読取エラーは失敗記録を保持し、受入追加後に修正して新しい出力directoryへ実行した。
追加読取の受入10件と実データ処理161.312秒を記録し、source・失敗ログ・生の保存BAR行・結果・再現手順を保存した。
sampling・BAR・decoder・WSSの再実行ではなく、診断警告や名目被覆の限界を変更しない。

sampling265361は23:55:18にF・Exit_status 0・run_count 1、walltime 4時間23分31秒で終了した。
capacity監査265367は23:55:18に開始して23:56:09にF・Exit_status 0・run_count 1となり、walltimeは49秒だった。
既存復旧監査driverがcapacity completionを受理し、full-planへ進んだ。
C1T1のnative reference引継ぎはqsubで265368を投入し、23:56 JSTにRを確認した。
この時点で手動による重複投入は行っていない。
DGX batch18の回収を終えてbatch19のexportへ進み、C1T0のhost側回収は452/768群である。
11 sessionの継続をpollで確認し、正式完了数は6/12条件を維持した。

## 2026-10-21 00:20 JST：環境修正後の再開

C1T0 full-planのnative検査はthread環境の不一致で停止し、依存する4処理も旧errorを保持して停止した。
元のthread環境をPython起動前に設定した別driverにより、検査を緩和せずfull監査265369をqsubで投入した。
監査は00:11:21に正常終了し、terminalを受理済みである。
後続4処理を3本の新driverへ再接続し、Windowsで38・59・21件の制御・回帰テストが成功した。
C1T1 collector265370はqsubで投入されて実行中、C1T1 native reference265368は正常終了・回収・受理済みである。
C1T0最終処理はPC全回収待ち、C1T2生成はC1T1 full監査受理待ちである。
C1T0 host側回収は496/768群となり、正式完了は引き続き6/12条件である。
8 sessionの継続をpollで確認し、旧失敗sessionを再利用していない。
最新状態は [2026-10-21の状態文書](PROJECT_STATUS_2026-10-21_ja.md)に保存した。

## 2026-10-21 00:26 JST：空きノードでC3T0生成開始

C1T1 collectorが使用する1ノード以外の空き枠に、C3T0の既存anchorをqsubで投入した。
anchor265371は2分35秒で正常終了し、実terminalを検査して保存した。
同じ空き枠で固定済みsample partition 0をqsubで265372として投入し、Rを確認した。
既存C1T2待機を変更せず、C3T0のanchorとsampling前半を実行順だけ前倒しした。
2要求ノードを維持し、seed・計画・source・native検査は変更していない。
sample partition 1と後続分析は未完了であり、正式完了は6/12条件を維持する。

## 2026-10-21 00:34 JST：C1T2生成後の自動引継ぎ

C1T2の実generator registryを待って既存native reference driverを起動し、DGX・Laboを前条件から引き継ぐ親処理を追加した。
初版の受入record schema差は子起動前に検出し、失敗source・ログを保持したv2で修正した。
実ファイルのbindingsと実子process試験を含む23件、元driverの回帰20・19件が成功した。
PID22720で待機を開始し、子processは未起動である。
DGX batch20の回収が完了し、C1T0 host側回収は516/768群となった。
詳細は [引継ぎ仕様と実施結果](c1t2_downstream_launch_spec_2026-10-21_ja.md)を参照する。

## 2026-10-21 00:39 JST：C1T2収集・監査の引継ぎ

C1T2の実generator registryとsampling正常終端を待つcollector・capacity/full監査driverを追加した。
既存の数値workerと受理条件を維持し、新規13件と制御・環境・registry回帰64件がWindowsで成功した。
PID7312で生成registry待ちを開始し、collector・監査のqsubはまだ行っていない。
source・ログ・実行状態は [仕様と実施結果](c1t2_collection_audit_handoff_spec_2026-10-21_ja.md)へ保存した。

## 2026-10-21 00:46 JST：残り5条件の全回収後index

全5条件の固定assignment・native configと保存済み113 sourceの完全一致を確認し、元の独立cohort_indexを呼ぶ接続を追加した。
Windowsで追加10件と元indexの回帰8件に成功した。
C1T1のPID37216とC1T2のPID12872で両PC全回収待ちを開始した。
本番indexや転送はまだ行っておらず、科学的なcohort受理を宣言していない。
source・ログ・残る接続事項は [仕様と実施結果](planned_cohort_index_spec_2026-10-21_ja.md)に保存した。

## 2026-10-21 00:55 JST：残り5条件のshared入力と転送adapter

旧C1T0のsourceを変更せず、明示conditionを取るshared回収・保存replay検証・distributionとtransferへの接続を導出した。
元の7ファイル検査、全保存値照合、768群の全件分母・input hash検査を維持した。
Windowsで82件と導出・CLI確認5件が成功し、17ファイルのsource・差分・ログを保存した。
実shared回収・転送と自動待機は未実施であり、実結果の成功へ読み替えない。
DGX batch21の回収を終え、C1T0 host側回収は536/768群となった。
詳細は [仕様と受入結果](planned_condition_distribution_spec_2026-10-21_ja.md)を参照する。
