# Tile低ノイズ検証の実行準備

本校正と並行して準備する次段階であり、この文書の条件ではsamplingもqsubも未実施である。
本校正のbundle・manifest・seedと、既に固定した層別reference v4の配分は変更しない。
最大2ノードを維持し、稼働中coordinatorと競合する手動投入は行わない。

## 対象と固定条件

対象はtile72/288のbit-flipとdepolarizingの4case、physical target p=.01/.003/.001の12条件とする。
各targetについて、そのtarget priorのBP-OSDをladder全体で共有し、異なるtargetのtraceやanchorを流用しない。
BP-OSDは本校正と同じmin-sum・scale1・parallel schedule・100 iteration・OSD-CS order10に固定する。
depolarizingのsector priorは2p/3とし、物理noiseは同一qubitのYを含むjoint Pauli noiseのままとする。
Linuxのnative binaryと再現fixtureを固定し、plan時とcompute node実行時の両方で照合する。

fine ladderの候補全集合は[.1,.085,.07,.06,.05,.04,.03,.02,.015,.01,.007,.005,.003,.002,.001]とする。
各targetより低いrungを除いて、そのtargetで終わるladderを構成する。
coarse ladderの候補全集合は[.1,.07,.05,.03,.015,.01,.005,.003,.001]とし、同じ規則で切り出す。
coarseはfineの部分集合なので、同一target・同一replicate内で同じtraceを用いてladder感度を比較する。
物理p=.1の独立MC anchorを各target・各replicateに16,384試行ずつ取り、層別referenceをBARのanchorに流用しない。
層別referenceは独立な比較対象に保ち、reference値を用いてBARの結果を合わせ込まない。

kernelは本校正のZHとZHSの2種類、lazy=.05、cache cap=200,000を維持する。
全192 replicateを事前固定し、capacity実行には別namespaceを用いて本番標本と混ぜない。
tile72-bitは最大16 chain・66,000 step、他caseは最大8 chain・18,000 stepを候補とする。
burn・保存長・chain数・block長・誤差法は本校正と同じ後処理水準を使い、都合のよい診断や区間だけを採用しない。
これは容量測定前の候補予算であり、容量測定で実行不可能と分かった場合は本番投入前に新manifestへ改訂し、旧案と理由を保存する。

## 初期化とseed

低pのrejection初期化は既存pilotで固定予算を使い切る例があり、次段階ではlogical basisと非零logical combinationの2初期化を事前に比較する。
logical basisはchain単位でindexを循環させ、depolarizingではX/Z basisが同一replicate内に含まれる割当てにする。
logical combinationは非零のlogical係数vectorを一様に選び、位相を無視したPauli積で状態を作る。
初期状態の公開failure判定・有限log density・syndrome・residual logical sectorを記録する。
選ばれた初期状態が失敗集合に入らなければ、そのtaskの初期化失敗を保存し、都合のよいsectorへの再抽選は行わない。
これらは条件付き定常分布からの初期化ではなく、burnと初期化感度の検証が必要な非定常初期化である。
bit-flipのlogical basisとdepolarizingのX/Z basisの割当て・非零係数分布は、全列挙できる小例と実tileの公開判定で先に受入を作る。

新しいseed stageは150=capacity sampling、151=本番sampling、152=本番anchor、153=本番bootstrap、154=capacity anchor、155=capacity解析に予約する。
seed入力はstage・case・target index・kernel index・初期化index・replicate・rung・chain・purposeを明示し、該当しない座標にも固定値を使う。
異なるtarget・初期化・kernelでsampling streamを共有しない。
同一条件のburn・保存長・chain数・ladder・誤差法比較では、予定どおり共通traceを切り出す。
投入前に既存namespaceとの重複検査を行い、seed・初期状態・sourceとmanifestのhashを保存する。

## 実装・投入の順序

専用driverのplanはcaseとtarget indexごとに独立したrootを作り、samplingとanchorの実行・記録を同じroot内の別phaseに分ける。
capacityでは各rung・kernel・初期化につき2 replicateを測定し、replicate 0/1にchain index 0/1を割り当てる。
capacityの保存step数は本番候補と同じとし、短いtraceの結果からcache飽和後の時間を推定しない。
本番では全192 replicate・全chainを測定する。
各taskはcase・target index・kernel・初期化・replicate・rung・chainの7座標を持ち、anchorではkernel・初期化・rung・chainを0に固定する。
samplingのpurpose 0は初期化、purpose 1は遷移乱数に使い、anchorはpurpose 0とする。
logical basisのPauli順序はX0,Z0,X1,Z1,…とし、同一replicateのchain群で両sectorを含める。
非零logical combinationはこのbasisの係数を整数1以上2^basis数未満から一様に選び、全係数と初期状態を保存する。
失敗を含め全taskに予告seed・physical p・decoder prior・stage・経過時間を保存する。
成功taskでは全保存状態の再判定、checkpoint、初期syndrome/sectorと完全なsampling metadataを保存する。
anchorにはdirect_mcのsampling p・RNG metadata・decoder metadataを保存するが、raw物理誤り列を保存した監査とは呼ばない。
CLI実行は96 worker・PBS_JOBID・単一thread環境を必須とし、source/runtime/plan/native入力を照合してからworkerを起動する。
phaseごとに排他的execution intentを保存し、既存task・summary・intentのあるphaseを自動再実行しない。
native preflightのplan証跡と各phaseの実行証跡は別のdirectoryに保存して上書きしない。
このdriverはqsub自体を呼ばず、最大2ノードと資源測定に基づくsubmitterは別に実装する。

1. 上記初期化・seed・targetごとのladderを小仕様と受入で固定する。
2. targetを明示する専用driverを実装し、stage31/32を埋め込んだ既存production driverのplanだけを差し替える方法は使わない。
3. 失敗taskを含むcheckpoint・metadata・source/native環境の記録と、層別referenceのcase/prior照合を検査する。
4. 新bundleへ配置し、端のrungだけでなく各rung・kernel・初期化を含むcapacity jobをqsubで実測する。
5. 実測時間とmemoryからcase/target別の分割・walltimeを固定し、全体の予測node時間と実行順を保存する。
6. 既存coordinator終了とqueued/running要求ノード数を実観測し、排他的intentを保存してqsubする。

本番の途中でtrace長・seed数・ladderを変更せず、capacityで失敗した設定も記録する。
低pで大きなMH棄却率や未定義IATが出る可能性を、定常分布の正しさや連結性の証明と混同しない。
初期化の追加はproposal kernelを変更するものではなく、failure support全体の連結性を保証しない。

## 結果の評価

全replicateを分母に残し、初期化失敗・推定値未取得・区間未取得・診断未定義・未収束フラグを別々に集計する。
層別referenceが得られた条件では、`tile_weight_reference_comparison.compare_condition` でcase/priorと合成算術を照合して区間内のbias/RMSE範囲を評価する。
この関数はraw artifactやnative環境の監査を代替しないため、元のreference driverによる全chunk監査の結果とhashを結び付ける。
未評価尾部を含むreference区間が広い条件、reference下端0の条件、reference未取得の条件では、設定間整合性を精度・被覆保証として報告しない。
同精度までの時間比較は独立計時cohortで行い、この低p実行の終了時間や取得できたtaskだけの時間平均で代替しない。
本校正での精度達成を低pに外挿せず、この段階のcapacity未実施の間は低p本番やgoal全体の確定ETAを出さない。

## 容量測定と投入の追加受入仕様

1 jobは1 case/targetのanchor phaseとsampling phaseを順に実行し、いずれも96 workerを使う。
初回capacityは1ノード・96 CPU・340 GiB・24時間を上限として要求する。
これは未測定条件の初回上限であり、実消費量や終了時刻の予測ではない。
本番の資源は同じcase/target・source/runtime・step数・kernel・初期化を用いた、全capacity task成功の記録から決める。
capacityのnative証跡とexecution intentのmanifest・PBS job ID・hostnameを結び付け、全artifactのidentityとJSON/NPZ hash、予定seed・physical p・固定prior・metadataを照合する。
この投入前の検査は記録の同一性検査であり、全数値traceの再復号・混合監査ではない。

sampling時間の予測は、capacity phase時間×本番task数/capacity task数と、各kernel・初期化・rungの最大task時間×192 replicate×chain数の総和/96の大きい方とする。
anchor時間も同様に、capacity phase時間×192/2と最大anchor task時間×192/96の大きい方とする。
二つの予測時間を足した値の2倍に600秒を加え、要求walltimeを1800秒単位で切り上げる。
memoryは全capacity taskの最大RSS×96×1.5に8 GiBを加え、最低32 GiBとする。
24時間または340 GiBを超える場合は本番を投入せず、固定科学条件を維持したjob分割の設計を必要とする。
失敗task・欠落task・不正な時間やRSSを成功分だけで外挿しない。

qsub前にcoordinatorの実process不在と、待機を含む全要求ノード数を観測し、追加1ノード後に2ノードを超える場合は拒否する。
同じrootにsubmission intent・ledger・execution intent・task directory・summaryがあれば再投入を拒否する。
qsubは1回だけ呼び、先に排他的submission intentを保存する。
qsub応答不明・timeoutではintentを保持し、自動再投入しない。
同じdeployment親directoryを使う低p submitter間では共通の排他的lockも使い、観測とqsubの間の競合を防ぐ。
応答不明時は共通lockも保持し、queueとprocessを確認するまで別rootから投入しない。
受入は改変・欠落・source不一致・資源上限・coordinator稼働・2ノード使用中・intent先行・曖昧応答・並行lock拒否を含む。

## 2026-10-18の実装・受入

`cluster_scripts/tile_low_noise_study.py` に専用plan・sampling・anchor driverを実装した。
関連36件はWindowsで5.06秒、Linuxで2.86秒で成功した。
4caseの8保存stepの実tile計測で、同じtarget prior=.001のままphysical p=.1と.001を測定し、Problem hashの一致・保存状態のfailure・初期logical係数とsyndrome/sector・seed metadataを確認した。
小binary空間で全非零logical係数を列挙し、PauliのX/Z basisの交互配置と積がYになることも確認した。
失敗taskの保持、native照合前のworker起動禁止、同じphaseの再実行拒否、metadata改変の検出は受入で確認し、phase制御の受入は模擬worker・probeを用いた。
これらは短い実行と制御の検査であり、本番の混合・被覆・計算量の実測ではない。

不変bundle `/home/user/workspace/mcmc4qec/20261018-tile-low-noise-v1` に配置し、転送archiveと収録fileのhashを照合した。
tile72-bit・target .01のcapacity planを `runs/capacity-0-0` に作成し、80 sampling task・2 anchor taskを固定した。
login nodeでのnative preflightは保存済みLinux profileと一致し、証跡をplan専用directoryに保存した。
このplanのmanifest digestは `cbfeef6a78d9cb10f12a9e61605d55dbfdccdf3d437b7898ac98d92b5fc2ab4f` である。
記録は `data_tile_validation_2026-10-17/low_noise_deployment_v1.json` と対応するmanifest・native証跡・Linux受入logにある。
低p用submitter・qsub容量測定・本番・全seed namespaceとの重複照合・専用BAR解析の接続は未実施である。
低p driverの追加により、既存production driverや稼働中bundleを変更していない。

planの再現コマンドは以下で、新しい空のrootを指定する。
sample/anchors subcommandはPBS環境でのみ実行でき、login nodeからの直接長時間計測には使わない。

```bash
TILE_LOW=/home/user/workspace/mcmc4qec/20261018-tile-low-noise-v1
"$TILE_LOW/venv/bin/python" "$TILE_LOW/cluster_scripts/tile_low_noise_study.py" plan --root "$TILE_LOW/runs/capacity-0-0-reproduction" --case 0 --target-index 0 --capacity
```

## 投入処理の実装とdry-run

`submit_tile_low_noise.py` にcapacityのqsub script生成と、本番の資源外挿・capacity記録照合を追加した。
関連53件はWindowsで12.39秒、Linuxで6.14秒で成功した。
小予算の実tile taskから作ったartifactを使い、summary・固定prior・sampling p・seed・実行証跡との結合と改変拒否を検査した。
資源予測・compute node証跡・qsubの成否は受入fixtureを使ったもので、実capacityの資源測定とは区別する。

新bundle `20261018-tile-low-noise-v2` に配置し、同じ科学manifestのcapacity planとlogin native preflightを再作成した。
tile72-bit・target .01のqsub dry-runは1ノード・96 CPU・340 GiB・24時間上限で、anchor2 taskの後にsampling80 taskを実行するscriptを保存した。
この24時間は初回の要求上限で、終了まで24時間かかるという予測ではない。
今後の低p投入にはv2を用い、v1を変更しない。
保存した `data_tile_validation_2026-10-17/low_noise_deployment_v2.json` はbundle・source・plan・native証跡・dry-runとscriptのhashを結び付ける。
現時点では本校正coordinatorと2ノードが稼働しており、低pの実qsubは行っていない。
低p本番の資源見積もりは実capacity完了後に行い、全seed重複検査・専用BAR解析・本番計測も未実施である。

```bash
TILE_LOW=/home/user/workspace/mcmc4qec/20261018-tile-low-noise-v2
"$TILE_LOW/venv/bin/python" "$TILE_LOW/cluster_scripts/submit_tile_low_noise.py" --bundle "$TILE_LOW" --root "$TILE_LOW/runs/capacity-0-0"
```

実投入時だけ `--execute` を加え、submitterがcoordinator不在・要求ノード数・既存intent・共通lockを検査してqsubを1回呼ぶ。
応答不明時に残るintentや共通lockは自動削除せず、記録とPBSの実状態を先に確認する。

## 全12条件のcapacity準備

2026-10-18にsampling用v2と合成BAR解析用v3の残り11条件ずつを別担当で準備し、各全12条件のplan・native preflight・dry-run・PBS脚本構文確認を完了した。
samplingは`20261018-tile-low-noise-v2/runs/capacity-{case}-{target}`、合成解析は`20261018-tile-low-analysis-v3/runs/capacity-{case}-{target}`を使う。
caseは0〜3、targetは0〜2で、既定の4符号/noise条件とp=.01/.003/.001に対応する。
既存samplingのcapacity-0-0、解析のcapacity-0-2と、固定bundle・source・Python環境は前後hashが一致した。
sampling全12計画の予定数はsampling 1,216 task・anchor 24 taskであり、実行済み件数ではない。
解析は各8群の合成データを使う計測計画で、科学的な精度検証には用いない。
記録は[低ノイズsampling準備](data_tile_validation_2026-10-17/low_sampling_capacity_preparation_v1.json)と[低ノイズ解析準備](data_tile_validation_2026-10-17/low_analysis_capacity_remaining_preparation_v1.json)にある。
全12条件のcapacity計算・本番計算・qsubは未実施である。
既存controllerの終了後もqueuedを含む最大2ノードを守り、計画数に応じて一括投入しない。
