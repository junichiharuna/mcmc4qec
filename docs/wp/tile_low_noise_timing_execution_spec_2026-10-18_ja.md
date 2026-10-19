# 低ノイズ独立計時の実行・資源・終端検証案（第3段階）

[独立計時仕様](tile_low_noise_independent_timing_spec_2026-10-18_ja.md) と [manifest・seed仕様](tile_low_noise_timing_manifest_seed_spec_2026-10-18_ja.md) を受ける、実装前の最小仕様案である。
本書の作成では実装、sampling、追加capacity、全数seed監査、qsubを行わない。
既存の選択規則・科学manifest・seed集合・旧sourceを変更せず、全24行を保持する。

## 実装境界と既存関数の再利用

追加はMC/BAR共通のrunner 1本とsubmitter 1本を基本とし、同じrunner内にtask、capacity判定、partition計画、保存済み実行の検証を置く。
submitterはprepare/dry-run/一回のqsubを扱い、専用の回収・資源・条件別helperを多数追加しない。
旧 `tile_bar_time_benchmark.run_task` と `tile_mc_time_benchmark.run_task` は旧stage・条件・96 replicate capacityに結合しているため、低ノイズmanifestへ差し替えて呼ばない。
科学計算には既存の `tile_study.build_problem`、`qec.direct_mc`、`qec.sample_faulty`、`tile_low_noise_study.logical_state`、`tile_study.compact`、`calibration.estimate_window`、`tile_bar_study.with_anchor_variance` を直接再利用する。
既存の `clock`、`check_metadata`、`platform_inputs`、`native_preflight`、`validate_platform`、artifact保存・読取り、`parallel_map` は契約が一致する部分で再利用し、旧plan/seed/resource builderは使わない。
第2段階の `validate_plans`、`tasks`、`task_seed`、registry、`complete_census_gate` が座標と科学manifestの唯一のauthorityであり、新runnerに座標式を再実装しない。
新driverのsource closureとexpected runtime/native/Pythonを実行envelopeへ固定し、旧bundleを更新しない。

MC main/capacityはstage160/161、BAR main/capacityはstage162/163である。
同じselected設定でもcase/target/epsilon identityごとに独立したtaskとする。
mainは192 replicate、capacityは各selected identity・各手法でreplicate 0/1の2 taskと2 workersである。
capacityはMCのfull N、BARのfull anchor・全rung/chain・burn+samples・指定解析を実行し、初期化や解析を省いたprofileへ置換しない。
capacityの全2 taskが正常に完了し、BARでは点・区間がavailableでなければmain資源を計算しない。
MCの観測失敗数0は固定N MCとしての正常結果であり、capacity失敗としない。

## estimator taskと保存契約

task identityは手法・cohort・case・target_index・epsilon_index・replicateと科学manifest digestに結合する。
partition IDや投入順をseedへ加えず、capacity標本をmainへ再利用しない。
各taskはdecoderを目標physical priorで一度構築し、BARのanchorと全rungに同じProblemを使用する。
depolarizingでは既存build_problemのjoint noiseと固定sector priorを維持し、rungごとにdecoderを作り直さない。
MCは科学manifestの正確な整数Nを1回のdirect_mcへ渡し、失敗数に応じた停止・試行の分割・seedの追加をしない。
BARはfresh anchor 16384 trialsを先頭rungで実行し、各chainをburn+samples、burn_in=0でsamplingして、burn後の全samplesを解析へ渡す。
棄却・lazy self-loopを除去せず、chain失敗、anchorの失敗数0、解析不能、区間未取得を分類して保持する。
logical_stateへ渡すindexは `replicate*initialization_stride+chain`、strideはcase0=16、他=8で、選択chain数に置き換えない。
local rungと元fine-ladder indexの対応、初期係数、初期状態、初期sector、有限log probability、failure supportを保存・検証する。
各rung/chainのseedと実metadata、compact weight/syndrome/sector、initial/final、chain_okを旧timing形式に沿って保存し、compact時の再decode費用を計時へ含める。
bootstrap seedはallocationを保存し、cross_chainでは `bootstrap_rng_consumed=false` とする。
logical_basisのinitialization seedもallocationを保存し、決定的係数の場合はRNG未消費を明示する。
失敗して到達しなかったpurposeは未消費のまま残し、新しい独立標本として数えない。
混合診断を独立計時で計算しない場合は `not_collected` とし、本校正の診断を転記して実測扱いしない。

## 先行gateと実行envelope

科学manifest・registry・selection bytes/hash・reference pinと、第2段階の旧56 namespace＋新4 namespaceの全数censusを結合する。
旧予定件数3,963,562に、新予定 `194*sum_i(3+2*R_i*C_i)` を加えた件数と、60 catalog namespace、意図的共有8448、未検査0、予期しない衝突0を照合する。
purpose別allocationとRNG消費を区別し、cross_chainやlogical_basisの未消費allocationをcensusから省かない。
上記件数は第2段階のauthoritative builderから再構築して一致を確認し、定数だけの一致を全数監査の代用にしない。
pure `complete_census_gate` の成功だけでは投入せず、正式censusのmanifest/source/result、execution intent、submission intent/receipt、実script、actual PBS F/exit0、前後input hashを別に検証する。
旧成功census、partial/pilot、別selection/source/registryの成功を流用しない。
新sourceの実行前検査はcensusで固定されたseed producer/source closureとの一致を必須とし、実行driver側の変更も別envelope/versionとして検査し直す。
科学manifestへ後発census resultを埋め込まず、後発の実行envelopeに全証拠とreplicate partition、資源、source、native/profile、script hashを記録する。
準備時のcurrent input検査は科学manifest・selection/registry/censusのmetadataと外部pinが対象で、巨大な過去校正rawの全再監査とは呼ばない。
正式selectorと本校正・WSS終端証拠の外部pinは維持し、意味の異なるsource変更やdecoder/native/prior不一致をscientific ineligibleへ変換しない。

各compute jobで同じbundle経由Pythonと固定single-thread環境を使い、import先・Python executable hash・package/native hashを照合してからnative_preflightを実行する。
prepareで使ったPythonとPBSで使うPythonの実行経路を一致させ、venvの実行ファイルだけのsymlinkで別依存へ落ちる構成を拒否する。
実PBS job ID、hostname、thread、seed、model/noise/decoder/failure hash、physical p、fixed prior、N・trace長・解析設定をtask記録と照合する。
終端でも現在のmanifest/registry/source/input/script/intent/nativeと全artifact marker/hashを照合する。
新rootを排他作成し、既存taskのresumeを新計時として認めず、再投入・不足seed置換を自動実行しない。
qsub直前は共有lock、controller不在、queuedを含む2 node上限を二度確認し、応答不明時はintentとlockを保持する。

## 容量測定と資源式

最初のcapacity requestはselected identity・手法ごとに1 node・2 CPU・2 workers・340 GiB・24時間という未測定の上限とする。
この上限は消費予測でも完了保証でもなく、capacity job間もqueuedを含む全体最大2 nodeを守る。
2 taskの並行結果だけから96 workersの競合、時間分布の裾、失敗確率を保証しない。
capacityがtimeout/OOMなら、完全な2 estimatorの測定を得られなかった事実とPBS費用を残す。
その場合に一部の成功taskだけでprofileを作らず、追加capacity replicate・新stage・短縮N/traceへ自動変更しない。

同一identity・同一手法の2 taskについて、以下の非負有限計時と正のRSSを測る。

- `t_j`：旧task scopeと同じ、構築から推定までのwall秒で、artifact書込みを除く。
- `u_j`：worker側でartifact保存完了まで含めたwall秒。
- `a_j=u_j-t_j`：保存とworker wrapperの追加費用で、純粋なdisk I/Oだけと呼ばない。
- `m_j`：workerのLinux process peak RSS MiB。
- `p`：controller process peak RSS MiB。
- `P`：pool起動・2 task実行・joinまでのphase wall秒。
- `s`：pool外のmetadata/native preflight/終端検証・科学要約保存のwall秒の和で、計時結果自身の最終書込みを除く。

phase定義を固定し、`u_j>=t_j>0`、`P>=max(u_j)>0`、`a_j>=0`、`s>=0`を要求し、bool・欠損・非有限・負の値を拒否する。
CPUは同じscope別に有限非負値を保存するが、walltimeの代入値やCPU数で割った代用値にしない。
workerの実測は `t=max(t_j)`、`a=max(a_j)`、`m=max(m_j)` とし、pool追加費用は `h=P-max(u_j)` とする。
親・子のRSSを別に保存し、PBS memの0/未取得から消費0を推論しない。

mainは各jobに96 CPUを要求し、実worker数は最大96の範囲でメモリから決める。
W workersの要求メモリGiBを `M(W)=max(32,ceil(2*W*m/1024 + 1.5*p/1024 + 8))` とする。
worker係数2、controller係数1.5、固定8 GiB、最小32 GiBは本仕様で固定する保守係数であり、確率的な上限保証ではない。
`M(W)<=340` を満たす最大整数W∈[1,96]を選び、一つも無ければ `execution_infeasible_memory_policy` とする。
メモリ制約でW<96となる場合は割当96 CPUと実workersを別々に表示し、未使用CPUを隠さない。

n replicateの1 partitionに対し実workersを `w=min(W,n)` とし、見積り秒を `T(n,w)=ceil(n/w)*t + n*a + h + s` とする。
artifact保存追加費用は並列に完全に隠れると仮定せず、n倍を加える保守的なモデルとする。
要求wall秒は `Q(n,w)=max(1800,1800*ceil((2*T(n,w)+600)/1800))` とする。
時間係数2、600秒の余裕、30分単位切上げを固定し、2 workerから96 workerへの競合増を実測済みとは扱わない。
mainの要求メモリは `M(w)`、各jobの上限は340 GiB・24時間、最大2 nodeである。

## partitionと実行不能の決定

同identity・手法のreplicate 0..191を、科学manifestとは別の実行partitionへ分ける。
上記Wを固定し、`Q(n,min(W,n))<=86400` を満たす最大n∈[1,192]を選び、0からn件ずつの連続範囲で分割する。
最後の余りだけ少ないtask数とし、各partitionの要求資源を実task数から計算する。
unionがちょうど0..191、pairwise disjoint、空partitionなしを検証し、partition ID・size・worker数をseedへ加えない。
一つのestimatorのanchor・全rung/chain・解析を分割しない。
`Q(1,1)>86400` なら `execution_infeasible_wall_policy` とし、予算や安全係数を結果に応じて下げない。
これは本資源方針で実行不可という分類であり、estimatorの真の最短実行時間が24時間超という証明ではない。

MCの巨大Nは第2段階の正確な整数としてそのまま保持し、float化・clamp・round down・部分実行で小さくしない。
実際に使うAPI/保存形式の検証済み整数上限や必要配列の確定byte数を超える場合だけ、capacity前に具体的制約付きの `execution_infeasible_input_limit` を保存できる。
根拠のない最大Nを新設したり、旧MCの短い実測を本capacity完了と読み替えたりしない。
入力を扱えてもfull N capacityが24時間/OOM上限で終わった場合は、固定Nと `execution_infeasible_capacity_envelope`、原因、実費用を保存し、mainを投入しない。
通常のdecoder/task例外や区間未取得は `capacity_failed` / `capacity_unavailable` とし、物理的な実行不能やreference精度不可能と混同しない。
未実施・validation failure・失敗・実行不能のどの場合も全24行のselector statusを保持し、後段planning/execution statusと速度比nullを追加する。
selectedが0件なら空task集合を保存し、空のcapacity/main jobを投入しない。

資源式の小さい数値例を以下に固定する。

| t / a / (h+s) 秒 | worker m / controller p MiB | 決定 |
|---|---|---|
| 60 / 1 / 15 | 256 / 128 | W=96、M=57 GiB、192件を1 partition、T=327秒、要求30分 |
| 30000 / 1 / 15 | 256 / 128 | 最大n=96、96件×2 partition、各T=30111秒、要求17時間 |
| 43000 / 1 / 15 | 256 / 128 | 1件でもQ=88200秒のためwall policyで実行不能 |
| 60 / 1 / 15 | 4000 / 128 | W=42、M=337 GiB、192件を1 partition、T=507秒、要求30分 |

## 失敗分母・費用・終端

各予定taskはok/failed/unavailable/not_started/interruptedを区別して保持し、成功taskだけへ192の分母を縮めない。
hard killでtaskの最終計時が無い場合はunknownとし、保存済みtask費用の合計を下限、PBS/phase費用を別scopeとして残す。
失敗後に完了taskだけを平均して全cohortの平均時間とせず、必要な費用が192件揃わないclockの比はnullにする。
task wall/process CPU、構築・anchor・初期化・sampling・compact・解析、artifact追加費用、native、pool/job phase、PBS elapsed/requested CPU時間を分ける。
capacityとmain、MCとBAR、同じ設定のepsilon2条件を別費用として保持し、旧trace/anchor費用を長さ比で割当てない。
partition結果は全partitionのF/exit0・script・intent・native・current source/input・全artifactと全192 identityが揃った場合にだけcompleteとする。
task failureがある完全な記録と、missing artifactなどによる検証failureを区別する。
全予定taskの有効な終端記録が揃ったjobは、記録済み科学task failureがあってもexecution_completeとして終了でき、全estimate取得とは別flagにする。
capacity resource gateはそこからさらにfailed=0・unavailable=0を要求し、正常終了だけでは通さない。
manifest/source/native/実metadata不一致やartifact欠損はvalidation failureで非零終了とし、科学task failureの通常記録へ変換しない。
native/source/seed/model/priorの不一致は実験結果の失敗率へ混ぜず、validation failureとして比較を停止する。
同精度のbounded評価と費用比は第4段階が行い、本runnerだけではprecision達成、名目被覆、速度優位、推奨設定を認定しない。

## 軽量受入案

1. 第2段階の手書き座標fixtureと実task seedが一致し、main/capacity・epsilon・purpose・partitionをまたぐallocation件数が変わらないことを確認する。
2. 小さいbit/depolarizing fixtureで固定prior、joint noise、fresh anchor、local rung対応、stride、初期係数、全棄却を含む保存長、bootstrap未消費を検証する。
3. 直列/並列の小taskで科学出力とseed/model metadataが一致し、計時値・hostだけは一致を要求しない。
4. 2rep capacityのfull dimension、MC full N、BAR fresh anchor・解析・compactを確認し、部分task・cached artifact・availableでないcapacityから資源計画を作れないことを確認する。
5. 表の4例、340 GiBと24時間の境界、bool/NaN/欠損/負計時、u<t・P<max(u)、RSS0をpure fixtureで検証する。
6. 最大nの決定がdeterministicで、192 identityのdisjoint union、余りpartition、1 estimator非分割、worker数変更によるseed不変を確認する。
7. 巨大整数Nの保存とinfeasible、capacity timeout/OOM、decoder例外、unavailable、unknown費用を区別し、Nや192を削らないことを確認する。
8. 旧/partial census、別selection/registry/source、件数不足、偽PBS/native、異なるPython経路、途中input変更を注入してcapacity/main双方のgate拒否を確認する。
9. mocked schedulerで全体2 node、queued、controller、shared lock、二重投入、曖昧qsub、既存出力を検証する。
10. 全24行保持、hard kill時のunknown費用、task失敗の分母、未取得artifactと記録済み失敗の区別、全partition終端不足による不完了を検証する。

受入は1 file 60秒以内の小fixtureだけとし、本番N/trace・全数censusをlocalテストへ含めない。
資源式と例を親レビューし、第2段階の確定API・registry・件数に整合させた後に実装範囲を決める。
表の4例の整数切上げ・最大workers・最大partition数は軽量なPython算術で確認したが、新driverの実装・受入・実測は未実施である。
