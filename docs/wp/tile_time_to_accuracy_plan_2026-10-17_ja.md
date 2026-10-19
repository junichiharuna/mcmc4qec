# Tileの同精度・計算時間比較

本校正のBAR結果を集計する前に、計算効率の比較指標を相対RMSE 20%と10%に固定する。
この指標は95%区間の相対半幅とは異なり、biasを除いた標準誤差だけの比較にも置き換えない。
直接MCの独立referenceを基準に、BARのbias・RMSE・未取得と区間被覆を別々に評価する。

固定N試行の独立Bernoulli MCでは推定量が不偏で、真の失敗確率Pに対する相対RMSEはsqrt((1-P)/(N P))である。
したがって目標εに必要な試行数はceil((1-P)/(P ε^2))となる。
Pには有限の独立MC referenceを使うため、reference点での値と、99.9%参考区間の両端に対応する必要試行数の範囲を保存する。
直接MCの比較用固定予算は、参考区間の下端から計算した値を64試行単位で切り上げる。
これはPが参考区間内にある場合の予算設定であり、Wilson参考区間を確実な真値範囲とは扱わない。
各条件は独立192 replicate、seed namespaceは既存と別のstage 121とし、観測失敗数による早期打切りやseedの置換をしない。
target p・decoder prior・OSD設定は既存の4caseと同じにする。
この比較用MC予算は生成時点では未実行であり、必要試行数の式だけから実測時間の優位性を主張しない。

生成済みの[固定予算](data_tile_validation_2026-10-17/direct_mc_precision_budget.json)は次のとおりで、数値は1 replicateあたりの試行数である。

| case | target p | 相対RMSE 20%用 | 相対RMSE 10%用 |
|---|---:|---:|---:|
| tile72-bit | .03 | 576 | 2,304 |
| tile288-bit | .05 | 896 | 3,392 |
| tile72-depolarizing | .03 | 832 | 3,264 |
| tile288-depolarizing | .05 | 8,576 | 34,112 |

4case×2精度×192 replicateの合計予算は10,358,784試行である。
目標式を有限binomial分布のMSEと照合し、referenceの端点・切上げを含む受入は7 passed・0.40秒だった。
追加MCと単独BARの実行driverは実装済みで、capacity測定・追加計時ジョブのqsub投入・実時間比較は未実施である。

直接MCのdriverは各replicateで符号・decoderを構築し、構築walltime、direct_mcのelapsed、task全体のwalltimeとprocess CPU時間を別々に保存する。
actual sampling p・RNG entropy・decoderを含むResult metadataをartifactに残し、保存seedと呼出し引数に一致することも検査する。
taskの計時はartifact書込みを除き、phase walltimeにはpoolの起動とartifact書込みを含める。
capacity用は各8条件に96 replicate、stage 122の独立seedを用い、本計測stage 121の192 replicateへ標本を混ぜない。
capacityでも1 replicateの試行数は本計測と同じとし、最も重い条件にも96taskを確保して全nodeの時間・memoryを測る。
容量測定は1ノード・96CPU・32GB・30分のqsubジョブとし、既存の固定予算referenceより小さい試行数で計時driver自体の資源を測る。
本計測の資源計画は、同じsource・条件の容量測定768taskが全成功した場合だけ生成する。
各taskのseed・固定試行数と実測時間・RSSを検査し、本計測への試行数比でphase時間を外挿して2倍と600秒の余裕を付け、30分単位で切り上げる。
memoryは96workerの最大RSSに1.5倍と8GBの余裕を付け、最低32GBとする。
要求が24時間または340GBを超える場合は投入せず、分割を再設計する。
投入直前に同じユーザーの稼働controllerと全未終了ジョブを確認し、controllerが存在する間や要求ノード数が2を超える場合は追加qsubを行わない。
qsub前に排他的なintentファイルを保存し、応答不明や失敗時は自動再試行しない。
容量測定と本計測のいずれも既存台帳・intentがあれば再投入を拒否し、dry-runではqsubとintent作成を行わない。
全taskを記録し、失敗taskを別seedで置き換えず、同じartifactはhashとidentityが一致した場合だけ読み直す。
小さい受入では、保存metadataと公開direct_mcの同seed再実行、固定条件・試行数・stage別seed、cache再読込みと失敗記録の保持を確認する。
driverと予算の受入は14 passed・2.38秒で、PBS外から本計測を開始しない検査も通った。
この検証は各caseの12試行などの小規模テストであり、固定予算の本計測やcapacity測定とは区別する。
qsub submitterを含めた受入はWindowsで21 passed・2.75秒、固定Linux環境で21 passed・1.69秒だった。
新しい不変bundle `20261017-tile-mc-timing-v1` に配置し、capacityと本計測のmanifestを固定して容量測定のdry-runを確認した。
実際のprocess表で既存controllerの稼働と要求2ノードを確認したため、追加qsubは行っていない。
capacityの実測、そこからの本計測資源計画、追加MC本計測は未実施である。

BARの一次結果は全192 replicateで、未取得を含む被覆、reference不確実性を含むbias/RMSE、初期化依存と診断をそのまま報告する。
全cohortの推定値がそろわない条件は、取得例だけのRMSEで精度条件を通過したことにしない。
各精度水準について、既定と候補のどの設定が基準を満たすかを示し、満たす設定がなければ未達として記録する。
多数設定のうち観測値が良かったものを、独立に検証された最適設定や名目95%被覆の保証とは呼ばない。

既存の保存traceを短く切り出した結果に、長さ比を掛けた計算時間を実測値として割り当てない。
同精度の時間比較に使うBAR設定は、必要なburn・保存長・chain数・ladder・誤差法と独立anchorを含む単独実行として別manifestに固定し、実際の時間を測る。
必要なら既存校正での設定選択と、選択後の独立seedによる確認を分け、選択に用いた結果を独立確認の標本へ流用しない。
計時は初期化・符号/decoder構築・anchor・sampling・解析を分け、process CPU時間とworker elapsed、96CPUでのphase walltimeを区別する。
既存referenceやanchorのelapsed合計をCPU時間と呼ばない。
同じLinux環境・依存版・CPU/thread設定を使い、capacity実測後にqsubし、最大2ノードを維持する。
BP-OSDの環境間差が実状態で確認されたため、計時driverも既知のLinux native profileと再現状態をmanifestに固定する。
plan時に固定入力を保存し、run時には保存入力のdigestと実行環境のnative binary・再復号結果を照合してからworkerを開始する。
環境不一致では計測を開始せず、成功したpreflightの実測結果を保存し、その時間はsamplingのphase walltimeと分ける。
capacityと本計測で同じnative入力を要求し、入力改変・再復号不一致でworkerが開始されないことを受入で確認する。
既存の未投入v1 bundleは変更せず、更新版は別bundleに配置する。
native入力の改変・再復号不一致によるworker開始拒否と、成功時の証跡保存を加え、関連受入はWindowsで24 passed・9.34秒、Linuxで24 passed・1.75秒だった。
更新版を `20261017-tile-mc-timing-v2` に配置し、capacity・本計測のmanifest作成、login node上の実native preflight、capacityのdry-runを確認した。
今後の投入にはv2を使い、v1の未投入manifestは過去の準備記録として保持する。
compute node上のpreflightとcapacity・本計測の実測は未実施である。
稼働中のcontrollerと新規投入が競合しないよう、追加計測の投入はcontrollerの実process状態・既存キューと調整する。

低noiseでは直接MC referenceが得られない場合、独立なweight-stratified referenceの不確実性を含めて同じ基準を評価する。
独立referenceがない、または区間が広すぎる領域では、同精度の時間比を確定値として出さず、設定間整合性・計算費用・未達の理由を記録する。

## MC計時の新規実行と資源証跡の補足仕様（2026-10-18）

MC計時runは既存task・summary・実行intentがあるrootを拒否し、worker開始前に排他的な実行intentを作る。
個別artifactの検査目的の再読込みは維持するが、容量測定と本計測のphase時間に再利用taskを混ぜない。
native preflightにはmanifest digest・hostname・PBS_JOBIDを保存し、runの実行intentと同じcompute実行に結び付ける。
資源見積もり前には固定budget・manifest・native入力・preflight hash・実行intentを照合する。
全768taskのidentityとJSON/NPZ payload hashを検査し、保存metadataを除いた各task recordがsummaryと一致することを要求する。
metadata自身のdigestとsampling p・RNG entropyも固定taskに照合する。
欠落・改変・summaryとの不一致・compute実行への結合欠落は、本計測の資源見積もりとqsubを拒否する。
受入は短い実MC artifact、合成された完全な容量cohort、入力改変と再実行の拒否を使い、実容量測定の成功とは扱わない。
既存の未投入v2と稼働中の本校正bundleは変更せず、更新版は別bundleに配置する。
実装前に受入5件の失敗を確認し、実装後はBAR計時との関連を含めWindowsで59 passed・22.99秒だった。
この時点では更新版のLinux配置・容量測定・本計測は未実施である。
その後、不変bundle `20261018-tile-mc-timing-v3` に配置し、Linuxで関連59 passed・9.40秒、login node上の実native preflight、capacityのdry-runを確認した。
今後のMC計時にはv3を使い、v1/v2の未投入manifestを過去の準備記録として保持する。
配置・manifest・検証範囲のhashは `data_tile_validation_2026-10-17/mc_timing_deployment_v3.json` に保存した。
計時ジョブのqsub、compute nodeでのpreflight、容量測定と本計測は引き続き未実施である。
coordinator終了と既存キューを実確認した後、次のcapacity投入を行い、終了後に検証済み容量artifactから本計測の資源要求を作る。

```bash
TILE_MC=/home/user/workspace/mcmc4qec/20261018-tile-mc-timing-v3
"$TILE_MC/venv/bin/python" "$TILE_MC/cluster_scripts/submit_tile_mc_time.py" --bundle "$TILE_MC" --root "$TILE_MC/runs/mc-capacity" --execute
# Run only after capacity has completed and its recorded job is terminal.
"$TILE_MC/venv/bin/python" "$TILE_MC/cluster_scripts/submit_tile_mc_time.py" --bundle "$TILE_MC" --root "$TILE_MC/runs/mc-benchmark" --capacity-root "$TILE_MC/runs/mc-capacity" --execute
```

## 単独BAR計時driverの小仕様（2026-10-18）

選択設定JSONは元のsampling manifestと選択根拠のartifact hash、全4case×2精度の8行を持ち、各行はselectedまたはunmetを明示する。
selectedの設定は元の校正grid内に限定し、未達条件を黙って省略しない。
このJSONは設定選択の入力であり、指定された設定が実際に精度を満たすことはdriverが保証しない。
実際の設定JSONは校正結果の全件集計・監査後に固定し、本稿の時点では未選択である。
本計時は独立192 replicate・seed stage 140、capacityは96 replicate・stage 141とし、anchor・初期化・sampling・bootstrapにも別purposeを割り当てる。
選択元の校正traceやanchorを再利用せず、各replicate内でも各条件の独立anchorを新しく16384試行で生成する。
符号・目標priorに固定したdecoderはreplicateで一度構築し、全rungで同じinstanceを使う。
depolarizingのlogical初期化indexは、選択chain数ではなく元の最大chain数×replicate＋chainとして、校正時のprefixと同じX/Z割当てを保つ。
各chainをburn＋保存長だけ実行し、棄却を含む全stepを残してから固定burnを除く。
保存分を独立に再復号してcompact配列へ変換し、全保存状態のfailureを確認する。
推定には既存校正と同じhistogram BAR、共有rungの共分散と独立anchor分散、選択された誤差法だけを用いる。
構築・anchor・初期化・sampling・compact検証・BAR解析のwallとCPU時間、task全体wall/CPU、peak RSSを別々に保存する。
compact検証の費用もtask全体に含め、公開APIだけの推定時間や理想化した最小時間とは呼ばない。
時間比には同じ精度の独立確認を通過した設定だけを使い、部分traceの長さ比による時間按分は行わない。
初期化やsamplingの失敗があっても残りの予定chainを記録し、replicateは未取得として分母に残す。
anchor 0失敗は確率ゼロと断定せず、BAR区間未取得として保存する。
再読み込みはhash一致のartifactだけに限り、再利用件数をphase summaryに残して新規実行時間と混同しない。
runはqsub・96 worker・1 threadとnative入力照合を必須とする。
受入は短い実tile traceでpublic samplerの同seed再現、保存metadataと固定prior、burn除去、anchorとBAR結果、失敗保持、stageの分離、設定改変拒否を確認する。
単独BARの資源計測・本計測・設定選択・同精度の時間比較は未実施である。
小仕様・未実装時の受入失敗・実装の順に進め、関連32件がWindowsで9.46秒で通った。
この受入は各caseで2chain・保存8stepなどの短い実行で、実際の比較設定の精度や計算時間を示さない。
不変bundle `20261018-tile-bar-timing-v1` に配置し、Linuxでも関連32件が7.57秒で通った。
同bundleのlogin nodeでnative profileを取得し、固定Linux profileとの一致を確認した。
実設定JSON・本計測manifest・資源計測・専用qsub submitter・独立精度確認は未完了で、計時ジョブは投入していない。
保存した選択根拠hash自体は精度の証明ではなく、実際の選択時には参照先の全cohort結果と照合する。
配置と検証のhashは `data_tile_validation_2026-10-17/bar_timing_deployment_v1.json` に保存した。

## 有限referenceに対する相対精度の集計仕様（2026-10-18）

同精度の比較指標は、全固定replicateの点推定値x_iに対する経験的相対RMSE sqrt(mean((x_i/P-1)^2))とする。
reference点での値と、reference区間[L,U]内のPに対応する最小・最大を区別する。
相対RMSEの区間内最小点は、mean(x_i)>0ならmean(x_i^2)/mean(x_i)を[L,U]へ切り詰めた値である。
これは絶対RMSEの最小点mean(x_i)とは異なり、絶対RMSEの区間をreference点で割る操作では代用しない。
最大値は区間の両端で評価し、全推定値が0ならP>0に対する相対RMSEは1である。
小さい確率でも二乗のunderflowを避けるため、最小点の計算は最大推定値でscaleを合わせ、相対残差の二乗和はhypotで評価する。
全点が取得でき、reference区間全域で経験的相対RMSEが閾値以下ならempirical_within_target、全域で閾値を超えるならempirical_above_target、端点や内部で判定が変わるならreference_sensitiveとする。
点推定値が未取得のreplicateを除いた値で合格にはせず、incomplete_pointsとして残す。
reference下端が0なら相対誤差を全域で定義できないためreference_zero_boundaryとし、合格にしない。
数値範囲を超えて有限値で表せない場合も判定不能として保存する。
区間未取得や診断未定義は従来の固定分母で別々に数え、点推定の精度と区間被覆を混同しない。
これらは有限cohort上の経験的比較であり、replicate標本変動を含む母RMSEの信頼区間や名目95%被覆の保証ではない。
集計CLIは元のsampling/analysis/reference/summary/raw rowsのhash結合、全条件と全replicateの完全性、保存済み絶対誤差集計との一致を確認する。
既存の固定BAR解析sourceは変更せず、追加の報告artifactを別ファイルに作る。
受入は内部最小点、端点最大、scale不変性、未取得・重複・0下端、実artifact形式の再集計とhash不一致の拒否を確認する。
小仕様・未実装時の受入失敗・実装の順に進め、関連26件がWindowsで0.85秒で通った。
既存のsourceと保存済みBAR集計を変更する処理ではなく、検証済み全cohortから別の相対精度artifactを生成する。
本校正の実データへの適用と設定の選択は未実施である。
新bundle `20261018-tile-precision-assessment-v1` に配置し、Linuxでも関連26件が0.19秒で通った。
配備hashと検証範囲は `data_tile_validation_2026-10-17/precision_assessment_deployment_v1.json` に保存した。

## 単独BAR計時のcase別投入仕様（2026-10-18）

計時ジョブは1caseずつ分割し、全8条件の選択・未達記録と元のcondition indexを保持する。
分割でseedやreplicate番号を変更せず、capacityは96、本計時は192 replicateのままとする。
初回capacityは96 workerの最大trace・bootstrapを含み得るため、MC用の30分・32 GiBを流用せず、1ノード・96 CPU・340 GiB・24時間を暫定上限として要求する。
これは未測定の資源予算であり、完了時間や必要memoryの実測値ではない。
capacityと本計時は別root・別seed stageとし、本計時の資源要求は完全なcapacity artifactとcompute nodeのnative証跡を確認してから決める。
計測phaseの2倍と条件ごとの最大task時間に192/96を掛けた作業量の大きい方を予測値とし、さらに安全係数2と600秒を加え、1800秒単位に切り上げる。
memoryは最大worker RSS×96×1.5に8 GiBを加え、最低32 GiBとする。
24時間または340 GiBを超える場合は投入を拒否し、追加分割を別途設計する。
欠落・失敗・区間未取得・再利用を含むcapacityは不完全な資源測定として拒否し、成功例だけに絞った外挿を行わない。
これはcapacityの結果を変更する規則ではなく、元の失敗・未取得記録は保持する。
実投入前にはcoordinatorの実process不在と、待機中を含む要求ノード数が追加後2以下であることを検査する。
qsub前に排他的intentを保存し、timeoutや不明な応答でも自動再投入しない。
runも排他的execution intentを作り、中断後のキャッシュ混入を新規phase計測と扱わない。
受入ではcase分割のseed保存、実測資源の外挿、artifact・native証跡の改変拒否、controller・2ノード制約、qsub応答不明時の再試行拒否を確認する。

小仕様・未実装時の受入失敗・実装の順に進め、関連42件がWindowsで12.47秒、Linuxで8.49秒で通った。
資源外挿・投入の受入は合成capacityと模擬qsubであり、実資源測定ではない。
samplerの関連受入は短い実tile traceを使う。
新しい不変bundle `20261018-tile-bar-timing-v2` に配置し、login nodeのnative profile照合も通った。
最初の手動probeはthread環境変数の明示を省いてguardに拒否され、4変数を1に固定したprobeでは一致した。
両profileのcanonical差はthread環境変数だけで、今回の手動probe間ではdecoder出力の差はなかった。
qsub scriptは4変数を固定し、compute nodeで同じguardを通る必要がある。
実際の設定選択・計時manifest・capacity・本計時のqsubは未実施である。
配置・受入・native照合のhashは `data_tile_validation_2026-10-17/bar_timing_deployment_v2.json` にある。

校正の全cohortを監査・集計して選択設定を保存した後、次の手順をcase 0〜3に適用する。
以下の `SELECTED_SETTINGS` は実際の選択根拠に結び付くJSONであり、受入fixtureを使用しない。
両精度とも未達のcaseは計時ジョブを作らず、全8行の選択結果に未達を残す。
その場合も比較処理の入力として本計時側のmanifestだけはplanで保存し、capacity planとqsubを省略する。
`--execute` のsubmitterが内部でqsubを呼び、coordinatorと要求ノード数を検査する。

```bash
TILE_BUNDLE=/home/user/workspace/mcmc4qec/20261018-tile-timing-comparison-v1
TILE_CASE=0
TILE_CAP="$TILE_BUNDLE/runs/capacity-$TILE_CASE"
TILE_MAIN="$TILE_BUNDLE/runs/benchmark-$TILE_CASE"
"$TILE_BUNDLE/venv/bin/python" "$TILE_BUNDLE/cluster_scripts/tile_bar_time_benchmark.py" plan --root "$TILE_CAP" --settings "$SELECTED_SETTINGS" --capacity --case "$TILE_CASE"
"$TILE_BUNDLE/venv/bin/python" "$TILE_BUNDLE/cluster_scripts/tile_bar_time_benchmark.py" plan --root "$TILE_MAIN" --settings "$SELECTED_SETTINGS" --case "$TILE_CASE"
"$TILE_BUNDLE/venv/bin/python" "$TILE_BUNDLE/cluster_scripts/submit_tile_bar_time.py" --bundle "$TILE_BUNDLE" --root "$TILE_CAP" --execute
```

capacityのPBS終了と完全なsummary・artifactを確認してから、本計時を投入する。

```bash
"$TILE_BUNDLE/venv/bin/python" "$TILE_BUNDLE/cluster_scripts/submit_tile_bar_time.py" --bundle "$TILE_BUNDLE" --root "$TILE_MAIN" --capacity-root "$TILE_CAP" --execute
```

失敗・中断・応答不明時は既存のintentとPBS状態を確認し、同じrootへの再投入で新規計測を装わない。

## 独立計時cohortの比較集計仕様（2026-10-18）

MCと単独BARの各固定cohortを全replicateで集計し、失敗・区間未取得を分母から除外しない。
各手法について有限reference区間内の経験的相対RMSEを既存の精度集計で再計算する。
両手法がreference区間全域で指定の精度を満たす場合だけ、全taskの平均wall時間と平均process CPU時間の比MC/BARをそれぞれ報告する。
比が1より大きい場合はその費用指標でBARの方が小さいことを表し、母RMSEや母時間比の保証とはしない。
失敗taskの消費時間も含め、時間の欠測があれば全cohortの平均と対応する時間比を未取得とし、取得例だけの平均は補助量として区別する。
taskのwall・CPU・構築・anchor・sampling・compact検証・解析を区別し、phase walltimeを条件別task数で按分しない。
単独BAR計時driverは混合診断を保存していないため、診断未取得を明示し、本校正の診断を独立計時の診断として代用しない。
MCではchain混合診断は非適用とし、BARで未取得の診断を良好と扱わない。
この集計は検証済みartifactから読み込んだrecordsを引数に取る数学的な後処理であり、単独ではmanifest・native環境・元traceの監査を済ませたことにしない。
受入では平均の比と個別比の平均の区別、精度未達・失敗・診断未取得・時間欠測の保持、負値や重複replicateの拒否、実MC recordの入力を確認する。
`cluster_scripts/tile_timing_metrics.py` の `assess` と `compare` にこの後処理を実装し、未実装時の受入失敗を確認した後、関連32件がWindowsで1.73秒で通った。
この時点ではLinux検証、実計時artifactの監査・接続、同精度の実時間比は未実施である。
その後、不変bundle `20261018-tile-timing-metrics-v1` に配置し、Linuxで関連32 passed・0.47秒を確認した。
配置と検証範囲は `data_tile_validation_2026-10-17/timing_metrics_deployment_v1.json` に保存した。
このmoduleは集計の中核であり、実計時artifactを読み込んで監査するadapterと、実結果への適用は引き続き未完了である。

### 計時artifactからの接続仕様

接続処理はcapacityを拒否し、MCはstage 121・192 replicate、BARはstage 140・case別192 replicateの固定manifestと元budget/settingsを再構築して照合する。
native入力とcompute preflightのhash、manifest・PBS_JOBIDと実行intentの一致を確認し、全予定taskのidentity・JSON/NPZ hash・summaryとの一致を検査する。
MCの実sampling p・RNG・固定trial数とmodel hash、BARのanchor/chain seed・sampling p・model hashを独立reference監査のmodel hashに照合する。
失敗taskは分母に残し、成功taskのみを抜き出したsummaryや再利用taskを拒否する。
reference summaryのhashを監査記録に結び付け、MC予算のreference値・区間、両手法のtarget priorと照合する。
BAR設定の未達条件も出力し、その条件に計時taskが存在する場合は拒否する。
phase walltimeは元job全体の値として保存し、case/精度別に按分した比は作らない。
この接続はpayload完全性と記録metadataの検査であり、保存中間状態の全再復号、選択元校正の再解析、native環境の新しい実probeを実施したとは扱わない。
受入は完全な合成192 replicate artifactと改変・欠落・異なるseedの拒否を用い、実校正や独立計時の成功とは区別する。
現在のMC v3と同じnative証跡形式で新規BAR manifestを作るため、今後のBAR計時は接続処理を含む新bundleで準備し、旧v2は変更しない。
`tile_timing_comparison.py` に接続を実装し、未実装時の受入失敗を確認した後、関連36件がWindowsで28.04秒で通った。
最初の完全fixtureは80.45秒を要したが、合成modelのhash結合と実MC metadataの検査を分け、最終の同testは25.51秒となった。
これはartifact形式と記録の整合性の検査であり、実計時や実際の速度優位を示す結果ではない。
その後、不変bundle `20261018-tile-timing-comparison-v1` に配置し、Linuxで36 passed・2.74秒、同testは2.11秒だった。
既存MC v3のcapacity・benchmark両manifestが、このbundleのdriverによる再構築と一致することも確認した。
BARの計時は今後このbundleで新規planを作り、旧bar-timing-v2のsourceや既存ジョブは変更しない。
配置・source hash・検証範囲は `data_tile_validation_2026-10-17/timing_comparison_deployment_v1.json` に保存した。
実計時artifactへの適用と比較ジョブの資源測定・qsubは未実施である。
全payloadを読む比較CLIはPBS内でのみ実行し、容量と短い計測から資源要求を決めたqsub jobの内部で、caseごとに次を呼び出す。
ジョブの投入時は既存controller・全要求ノードを確認し、最大2ノードを維持する。

```bash
TILE_COMPARE=/home/user/workspace/mcmc4qec/20261018-tile-timing-comparison-v1
TILE_MC=/home/user/workspace/mcmc4qec/20261018-tile-mc-timing-v3
TILE_PRODUCTION=/home/user/workspace/mcmc4qec/20261017-tile-production-v1/runs/production
TILE_CASE=0
"$TILE_COMPARE/venv/bin/python" "$TILE_COMPARE/cluster_scripts/tile_timing_comparison.py" --mc-root "$TILE_MC/runs/mc-benchmark" --bar-root "$TILE_COMPARE/runs/benchmark-$TILE_CASE" --reference-path "$TILE_PRODUCTION/reference_summary.json" --audit-path "$TILE_COMPARE/docs/wp/data_tile_validation_2026-10-17/reference_audit.json" --case "$TILE_CASE" --output "$TILE_COMPARE/runs/comparison-$TILE_CASE.json"
```

## 独立計時候補を選ぶ固定規則（本校正解析前）

候補選択では全4caseの元manifest・reference・解析context・raw rows・summaryのhash結合を照合し、全条件・全192 replicateから相対精度を再集計する。
目標20%・10%ごとに、全点が取得でき、reference区間全域で経験的相対RMSEが目標以下の設定だけを候補とする。
未収束・診断未定義・区間未取得をreplicateから除かず、これらの件数と被覆も選択結果へ保存する。
これは点推定精度に基づく独立確認候補であり、診断・被覆を含む推奨設定の認定ではない。
候補中でrung数×chain数×(burn＋保存長)が最小の設定を選ぶ。
このstep数は実測時間でも速度の予測値でもなく、同数stepでもkernel・初期化・解析費用が異なるため最速設定とは呼ばない。
同数stepならcross_chain、blockが小さい順、ZH、logical初期化、最後にconditionのcanonical JSON順で決める。
精度値の僅差や良かったseedを順位付けに使わない。
通過候補がなければunmetとし、条件ごとの分類件数を全8行に残す。
保存する選択根拠には入力ファイルhash・再集計digest・固定規則・選択処理source hashを含める。
数値trace・anchor・referenceの監査と初期化依存の評価は別途必要であり、この候補生成器のhash照合だけで完了と扱わない。
実際の計時投入はそれらの監査後に行い、選択後の独立192 replicateで精度を再確認してから時間比較を報告する。
受入では未取得例の保持、reference境界、候補なし、順位の順序不変性、全条件完全性、設定と選択根拠の結合を確認する。

小仕様・未実装時の受入失敗・実装の順に進め、関連30件がWindowsで2.14秒、Linuxで0.99秒で通った。
受入は合成全cohortと小gridの保存済みraw rowsを使い、実校正から設定を選択した結果ではない。
不変bundle `20261018-tile-selection-v1` に配置し、hashと検証範囲は `data_tile_validation_2026-10-17/timing_selection_deployment_v1.json` に保存した。
全4caseの本解析と監査後に、固定Linux環境で次を実行して新規候補JSONを作る。
既存の候補JSONがある場合は上書きを拒否する。

```bash
TILE_SELECTION=/home/user/workspace/mcmc4qec/20261018-tile-selection-v1
TILE_RESULTS=/home/user/workspace/mcmc4qec/20261017-tile-production-v1/runs/production
"$TILE_SELECTION/venv/bin/python" "$TILE_SELECTION/cluster_scripts/tile_select_timing.py" --root "$TILE_RESULTS" --output "$TILE_SELECTION/runs/selected_settings.json"
```

実cohortへの適用・選択設定の生成・選択後の独立確認は未実施である。
