# Tile code-capacity検証：事前計画

## 目的と固定条件

基準commitはd78377eで、tile72のbit-flipからtile288・depolarizingへ広げ、BP-OSDの再現性、MCMCの混合、BARのbias・区間被覆・計算効率を検証する。
既存の2026-10-17校正bundleと結果を変更せず、新しいbundle・seed namespaceで実行する。
RIMCは読み取り専用、計測投入はqsub、同時使用は最大2ノード、commit・pushは行わない。
公開kernel・sampling既定を変更せず、候補設定は明示した比較条件として扱う。

factoryはmake_tile_code(6,6)と(12,12)の開境界weight-6 presetとし、n/k=72/8と288/8、CSS可換性・完全なpaired logical basisを検査する。
288qubitsの距離12は文献値であり独立証明した距離下界にはしない。
bit-flipは独立X誤り、depolarizingは各qubitでI/X/Y/Zを確率1-p,p/3,p/3,p/3で生成し、syndrome測定は理想とする。
失敗は全logicalのうち1個以上に残余Pauliがあることとし、P_anyをkで割った値を1logicalあたりの失敗率とは呼ばない。
BP-OSDはmax_iter=100、min_sum、scaling=1、parallel schedule、osd_cs、order=10に固定する。
各target用のdecoderを構築し、bit-flipのpriorはtarget p、depolarizingの各sector priorは2p/3とする。
同じtargetのladder内ではdecoderを変更せず、X/Z sector別復号はdecoder側の近似として記録する。

## 第1段階：受入とPBS pilot

以下を実装前の受入条件とする。

1. tile72の全256個のsyndrome-zero X logical組合せに対し、zeroのみ成功、それ以外は失敗となり、公開Problem.is_faultyと残余logicalの直接計算が一致する。
2. bit-flip・depolarizingでBP-OSDの訂正がsyndrome式を満たし、残余logicalから計算したfailureが公開判定と一致する。
3. 同じsyndrome集合について反復・逆順・新decoder instanceでlogical predictionが一致する。
4. prior感度は同一物理誤りについて比較し、logical predictionの差・成功失敗の差・失敗総数の差を区別する。
5. 初期状態は独立rejection samplingまたは非自明なlogical operatorから作り、必ず正のnoise支持とfailureを検査する。
6. 既定Z/H=0.7/0.3と候補Z/H/stabilizer=0.6/0.3/0.1を比較し、lazy=0.05、k=2を共通にする。
7. 全棄却・lazyを保存し、weight、syndrome weight、各logical indicator、sector遷移、受理、時間、初期化試行数を記録する。
8. 候補の詳細釣合い・支持・非周期性は全列挙可能なCSS例で独立検査し、tileの全支持連結性の証明とは区別する。
9. manifest、source/package/backend hash、seed、行列、decoder設定を固定し、artifactはdata/meta両方のhashが一致する場合だけ再利用する。

pilotは4組（72/288×bit/depolarizing）×物理p=[0.1,0.05,0.03,0.01]×6 seedの96taskとする。
各taskのdirect MCは固定512試行、kernel2種×初期化2種のchainは各512step、burnなしとし、pilotを本校正のcohortへ混ぜない。
prior感度・再現性には各taskの最初の32個の同一誤りを使い、physical pとdecoder priorを区別して記録する。
初期化rejectionは最大20,000試行で打ち切り、失敗も保存し、別seedで置き換えない。
pilotの用途は正しさの受入・計算資源・referenceの必要試行数・低p初期化の実行可能性の確認であり、95%被覆の保証には使わない。
96workerを使い、先に短いlocal受入を通した後、専用配置先へqsubでpilotを投入する。
pilot実測から本校正の固定予算とPBS要求を決め、投入前に追加manifestへ記録する。

## 第2段階以降：校正と低ノイズへの拡張

本校正は独立seed群を用い、reference・各replicateのMC anchor・MCMC・bootstrapに別のseed namespaceを使う。
直接MC referenceは固定試行数とし、pilotに基づく予算選択を本番前に固定する。
参考値自身の区間と標準誤差を保存し、有限MC referenceをexact truthとして扱わない。
被覆はreference区間全体を含む下側評価と、reference区間と交差する上側評価も報告し、reference不確実性が結論を曖昧にする場合は追加計測が必要と判断する。
bias・RMSEはreferenceの不確実性を併記し、同一referenceを使う多数条件を独立な真値検証として合算しない。
trace長、burn-in、chain数、ladder、誤差法は制御した対応比較とし、全seedを主分母に残す。
R-hat、IAT、ESS、未定義値、初期化・logical sectorへの依存を別々に報告し、良好な診断から既約性を推論しない。
少なくともtile72-bit、tile288-bit、tile72-depolarizing、tile288-depolarizingを扱い、直接MCで校正可能な領域と独立referenceのない低pを明確に区別する。
速度はCPU時間とwalltime、初期化・anchor・sampling・解析の内訳を保存し、同じ精度で比較できる条件だけtime-to-accuracyを報告する。
kernelの採用は被覆の点推定だけで決めず、bias・初期化依存・未取得・計算費用を合わせて判断する。
最終的に利用例、固定設定、適用限界、生データ・再現手順・環境・日本語報告・状態文書を整備する。

## Pilot完了後に固定する独立reference

pilot265196は終了コード0、96task全て成功、PBS walltime34秒だった。
各条件のdirect MCは6seed合計3,072試行で、tile72-bit p=.03は128失敗、tile288-bit p=.05は91失敗、tile72-depolarizing p=.03は93失敗、tile288-depolarizing p=.05は9失敗だった。
これら4条件を最初の被覆校正targetとして固定し、pilotの推定値はreferenceへ加算しない。
独立referenceは各chunk65,536試行とし、最初の3条件は96chunkずつ（各6,291,456試行）、tile288-depolarizingは960chunk（62,914,560試行）とする。
総試行数は81,788,928で、事前固定の試行数まで実行し、観測失敗数で打ち切らない。
各chunkは公開direct_mcをそのまま使い、seedはpilotとは別purposeとstageを持つ固定keyから生成する。
target decoderはtarget pに固定し、MC参考値の95%と99.9% Wilson区間を保存する。
pilotからの予測は最も重いchunkで約164秒、960chunkで約1,640秒、他3条件を含め約2,000秒であり、2倍の余裕を含めPBS walltime2時間・1ノード96CPU・32GBを要求する。
referenceジョブの結果を見てseed・target・予算を選び直さず、追加が必要なら独立の追補計画を残す。

## 本校正の科学設定（reference結果を見る前に固定）

各targetについて192 replicate、既定ZHと候補ZHS、独立rejection初期化とlogical初期化を比較する。
tile72-bitは最大16chain・各66,000保存、他の3条件は最大8chain・各18,000保存とする。
後処理は4chainと最大chain数、burn600/6,000、保存長600/6,000およびtile72-bitで60,000・他で12,000を比較する。
target .03のcoarse ladderは[.1,.07,.05,.03]、fineは[.1,.085,.07,.06,.05,.04,.03]とする。
target .05のcoarse ladderは[.1,.07,.05]、fineは[.1,.085,.07,.06,.05]とする。
ladder・window・chain数間は共通rungの同じ保存traceを使う対応比較である。
初期化・kernel間は独立sampling streamを使い、MC anchorだけをreplicateごとに共有する。
anchorは各case・replicateで独立16,384試行のdirect MCをp=.1で行い、そのcaseのtarget priorにdecoderを固定する。
anchorのlog分散には二項delta近似(1-phat)/(N*phat)を加え、anchor未取得・推定不能も主分母へ残す。
誤差法はcross-chainと円環block32/128、および保存長6,000以上でblock1024、bootstrap1,000回とし、点推定は共通のpooled BARとする。
depolarizingでも同じnoise率間のlog密度比は非I weightの関数となり、各非Iラベルの1/3は比で相殺されることを受入検査する。
保存traceは全stepのweight・syndrome weight・残余logical bitmaskとし、全保存状態のfailureを独立再復号してからcompact化する。
初期状態・最終状態・一定間隔の物理状態checkpoint、seed・runtime・model hash・受理・診断・時間を保存する。
全支持の連結性はこの観測から証明せず、連結性の未確定と実測のsector滞留を分けて報告する。
最長traceのcapacity smokeをreferenceとは別の1ノードで先に行い、実測後にsamplingと解析のPBS要求・分割を決める。
capacity smokeの標本は本校正へ流用しない。

## 集計と回収の受入条件

各条件のreplicate keyが事前固定集合と一致することを確認し、欠落・重複したファイルを完全なcohortとして集計しない。
保存済みのsampling失敗、区間未取得、診断未定義・閾値超過は削除せず、被覆の分母は全192 replicateとする。
推定値が取得できないreplicateを含む場合、全cohortのbias・RMSEは未定義とし、取得例だけの値は明示的に補助量として分離する。
reference点に対するbias・RMSEとともに、referenceの99.9%区間内でそれらが取り得る範囲を保存する。
各被覆率のWilson区間はreplicate数の有限性を示す記述量であり、多数条件の同時保証やreference不確実性を除いた保証とは扱わない。
回収archiveは展開せずstreamで全payloadのSHA-256を計算し、markerのidentity・manifest・task全集合・data/meta両hashを照合する。
この照合は転送完全性の検査であり、物理状態の科学的な再復号検査とは区別する。

解析の資源要求も本番前に測定する。
専用のsynthetic_analysis_capacity計画では、各caseの最大配列寸法・全window・全誤差法を持つ人工traceを24groupずつ作り、実際の解析関数を96workerで実行する。
人工traceは物理状態やMCMCの出力ではなく、科学的な推定・診断・被覆には使用しない。
本校正とは別の配置先・manifest・seedを使い、解析・入出力の時間とpeak RSSの測定だけに使う。

sampling本番はcaseごとに1ノード96workerのジョブに分け、容量測定の両端rungの平均時間の大きい方をkernel・初期化別に全rungへ外挿する。
walltime要求はその予測の2倍にanchor・起動分600秒を加えて時間単位で切り上げ、24時間を超える場合は投入せず追加分割する。
memory要求は容量測定の最大worker RSS×96の1.5倍に8GBを加え、32GB以上340GB以下とする。
投入順は予測時間の降順とし、実行中・待機中を含む自分の全ジョブの要求ノード数が合計2以下となる時だけqsubする。
各caseのMC anchorを192taskで先に実行し、その後sampling taskを実行する。
資源要求の外挿は完了時刻の保証ではなく、実行後の実測と併記する。

独立MCの条件付き平均weightは、各chunkの失敗数Kと失敗時weight合計Vからsum(V)/sum(K)を再集計する。
既存referenceには各試行のweight分散を保存していないため、その平均のMCSEは独立chunk間のV-mu*Kの標本分散を用いるdelta近似と明示する。
referenceの生ファイル・元のsummaryは変更せず、再集計・seed・モデル設定の照合結果を別の監査記録へ保存する。

条件付きweightの追加集計では、全解析groupのtarget rungにあるweight診断を読み、kernel・初期化・chain数・burn・保存長ごとの全replicateを保持する。
同じtarget traceを使うladder・BAR誤差法別の重複集計は行わない。
target chainのsampling失敗によって診断がない場合は欠測として残し、失敗記録なしでweight診断が欠落した場合は不完全な解析として拒否する。
全平均がそろう条件でのみreplicate平均の平均、referenceとの差、reference点に対するRMSE、独立replicate間の平均のSEを報告する。
欠測があればこれらの全cohort量は未定義とし、取得例だけの平均は明示的な補助量に分ける。
referenceのchunk delta SE、replicate間SEとその二乗和平方根による差のSEを保存し、母集団のbiasや収束の証明とは扱わない。
各replicateのIAT MCSE・cross-chain SE・R-hat・未定義診断・sector遷移も保存する。
これは観測量weightの比較で、BAR論理エラー率の誤差や区間被覆ではない。
入力の解析metadataはmarkerのidentityとJSON hashで照合し、参照しないACFのNPZや元traceの全件数値監査を実施したとは扱わない。
reference監査と元summaryのhash・条件付き平均の一致を検査し、追加集計を新しいartifactへ保存する。

この追加集計の受入は小仕様・未実装時の失敗・実装の順で進め、関連13件がWindowsで2.61秒、Linuxで1.42秒で通った。
短い実tile traceのtarget weight平均と、保存済み解析diagnosticから読む平均の一致も確認した。
受入のreference比較・欠測・改変は合成cohortによるもので、本校正の条件付き平均比較は未実施である。
不変bundle `20261018-tile-weight-comparison-v1` に配置し、hashと検証範囲を `data_tile_validation_2026-10-17/weight_comparison_deployment_v1.json` に保存した。
case別の全解析groupが完成した後、同じLinux環境で次を実行し、case 0〜3それぞれについて新規出力へ保存する。

```bash
TILE_WEIGHT=/home/user/workspace/mcmc4qec/20261018-tile-weight-comparison-v1
TILE_RESULTS=/home/user/workspace/mcmc4qec/20261017-tile-production-v1/runs/production
"$TILE_WEIGHT/venv/bin/python" "$TILE_WEIGHT/cluster_scripts/tile_weight_comparison.py" --root "$TILE_RESULTS" --case 0 --reference-audit "$TILE_WEIGHT/docs/wp/data_tile_validation_2026-10-17/reference_audit.json" --output "$TILE_WEIGHT/runs/weight-comparison-0.json"
```

解析本番の資源要求は、人工配列容量測定の各caseの平均解析時間×768group/96workerの2倍に600秒を加え、時間単位で切り上げる。
memoryは最大worker RSS×96の1.5倍に8GBを加え、32GB以上340GB以下とする。
24時間または340GBを超える場合はそのまま投入せず、追加分割を設計する。
samplingのPBS終了を確認し、sampling・anchorの事前固定task集合が全件記録されてからcase単位の解析を投入する。
全件記録された失敗は解析から除外せず、失敗に起因する区間未取得を含めて集計する。

## 対応比較の集計仕様

解析済みの全条件・全192 replicateを検査した後、kernel・初期化・chain数・burn・保存長・ladder・誤差法を一要因ずつ変えた条件対を集計する。
条件対は事前設定の全水準から機械的に作り、結果の良い組合せだけを選ばない。
同じreplicateのMC anchorと、共有されるtraceを保った対応差として扱い、kernel・初期化のsampling stream自体は独立であることを明記する。
差の向きは右条件から左条件を引いた値に統一する。
推定値差・対数比・二乗誤差差は全replicateで算出できる場合だけ主結果とし、取得分だけの値は明示した補助量にする。
二乗誤差差は共通referenceに対して計算し、referenceの99.9%区間内で取り得る範囲も保存する。
被覆差では区間未取得を非被覆として全replicateを残し、両方被覆・右だけ被覆・左だけ被覆・両方非被覆のcountを保存する。
reference点・区間全体包含・区間との交差の三つを別々に集計し、後二つの差を真の被覆差の信頼区間とは呼ばない。
対応差の標本分散から計算する標準誤差はreplicate間変動の記述量で、多重比較補正済みの検定や精度保証として扱わない。
未収束・未定義・閾値超過・sampling失敗を条件対から除外しない。
この集計は新しいsamplingやbootstrapを行わず、投入済み計画・source・標本を変更しない。
受入では共有変動が相殺される差、既知の二乗誤差差とreference範囲、区間未取得、推定値未取得、重複・欠落・一要因条件対の完全性を検査する。

## 長時間計測の投入継続

固定済みのsampling4条件と対応する解析4条件に限り、軽量controllerが60秒間隔でPBSの実状態を確認して既存submitterを呼び出す。
待機・実行中の自分の全ジョブを含め要求ノード数が2未満のときだけ、1件ずつqsubする。
未投入samplingは既定順3/0/1/2で優先し、その後は完了を確認できたcaseの解析を資源予測時間の降順で投入する。
解析前の全sampling・anchor記録の確認と、完全に記録された失敗を残す既存規則は維持する。
source・manifest・資源計画をhashで固定し、controllerはsampling条件・seed・予算・artifactを変更しない。
投入の直前に意図を永続記録し、qsub結果と台帳を照合した後に受領記録を残す。
投入処理中のエラーや受領記録の欠落では自動再試行をせず、既存ジョブと台帳を人が確認できる状態で停止する。
qstatの一時的な観測エラーでは新規投入せず、同じjob IDを再観測する。
controller自身は二重起動を拒否し、最大72時間で終了するが、既存ジョブは取り消さない。
常駐するのは待機と状態確認だけの軽量processで、sampling・解析はすべてqsubされたcompute nodeで行う。
controllerの終了を研究検証全体の完了とは扱わず、回収・監査・比較・層別本計測・最終報告は別に行う。

## Stabilizer移動の代数的な確認

組み込みCSS modelのsyndrome map Hとlogical-observable map Lを、物理状態のbinary成分の単位basisから再構成する。
bit-flipはn成分、depolarizingはX/Zの2n成分とし、I/X/Y/Z labelは位相を無視したPauli積に対応するbinary表現へ変換する。
stabilizer generator行列SについてH S^T=0、L S^T=0、rank(S)=入力次元-rank([H;L])を確認する。
これにより、同じsyndrome・同じlogical observableを持つ状態の差の空間がSのrow spaceと一致することを確認する。
固定された決定的なsyndrome-only decoderと標準の残余logical failureでは、stabilizer移動が同じsyndrome・残余logicalのfiber内をつなぐ。
0<p<1のproduct noiseと正のstabilizer混合確率のもとでは、各generator移動のMH受理率は正なので、このfiber内の連結性が従う。
異なるfiber間の連結性、BP-OSD実装の全入力上の決定性、混合時間や名目区間被覆は、このrank確認からは従わない。
任意のcustom failureやpごとに変わるdecoderへ、この議論を無条件には拡張しない。
受入には既知rankの4case、Pauli表現の線形mapと公開modelの一致、stabilizerによるmap不変性を用いる。

depolarizing本校正のlogical初期化は、sourceのindex規則replicate×8+chainによって偶数replicateがX basis、奇数replicateがZ basisとなる。
本校正の結果を集計する前に、主結果の全192 replicateに加え、偶数・奇数を各96 replicateとした初期化別の補助集計を追加する。
層別でも失敗・未取得・未定義を分母から除外せず、元の科学manifest・sampling・seedは変更しない。
このsource上の規則は結果の良否による選別ではなく、初期化依存の相殺を見落とさないための区分である。
補助集計は解析の全条件と全replicateを検査し、元の全192 replicateのsummaryを再現してから出力する。
元のreplicate IDを保存したまま各層の統計計算用の連番へ写し、seedやsamplingを変更しない。
rejection条件にも同じ偶奇の補助表を用意するが、これをX/Z basisからの初期化とは呼ばず、seed区分の対照として扱う。

完了したMC anchor phaseはMCMC本体と分離して回収できるが、固定case・全192 replicateのartifactを照合してから集計する。
anchorのseed・予算・Problem hashとcountから再計算した推定値・Wilson区間を確認し、全anchorの合算は監査用に限る。
各replicateの独立anchorを合算値で置き換えず、0失敗や失敗taskも残す。
anchor artifactは物理誤り列とdirect_mcの全metadataを保持していないため、物理pとRNG呼出しは固定source・manifestに基づく確認であり、保存済み生状態からの独立再計数とは呼ばない。
# 本校正データの回収検査（追加仕様）

本校正はcaseごとに回収し、sampling archiveには固定manifest、全trace、全replicateのanchorを含める。
期待するtask集合は固定manifestのcase・kernel・初期化・replicate・rung・chainから生成し、成功・失敗statusによって間引かない。
analysis archiveには固定sampling manifest、analysis manifest、独立reference summaryと全groupの解析artifactを含める。
analysis manifestのsampling digestとreference summaryのhashを検査し、別計測の解析が混ざることを拒否する。
どちらも全artifactのidentity、JSON/NPZのhash、marker集合、欠落・重複を検査する。
これは転送と計測同一性の検査であり、数値trace・checkpointの再復号や科学的な妥当性の監査は別に行う。
受入では小さな完全archiveと欠落・別case・別analysis manifestを検査し、実際のsampling task生成関数とも期待集合を照合する。
数値監査では全taskの失敗記録を残し、成功traceの保存長・整数dtype・weight/syndrome/sectorの値域・記録seed・固定Problem/configを照合する。
全checkpointの位置と最終状態を検査し、初期状態とcheckpointを固定priorのdecoderおよび公開failure判定で再復号する。
checkpointのweight・syndrome weight・residual logical sectorがcompact traceの同じ位置と一致することを確認する。
logical初期化は元replicate・chain番号のbasis選択と照合する。
rejection初期化は失敗支持と記録attempt数の範囲を検査し、再度最大20,000回のrejectionを実行して初期乱数を再生成したとは主張しない。
保存されていない中間の物理状態やMCMC軌道全体の乱数を再生したとは主張せず、checkpoint間は保存compact値の構造検査にとどまることを記録する。
全件数値監査は復号を伴うためqsub・96workerで実施し、localの受入は小さいtraceに限定する。
環境間のdecoder判定差が実測されたため、全件監査の前に生成元Linux profileとnative binary・環境情報・再現状態の判定を照合し、不一致なら監査を開始しない。

