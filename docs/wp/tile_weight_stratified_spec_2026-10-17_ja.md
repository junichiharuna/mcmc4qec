# Tileのweight-stratified reference：小仕様

2026-10-17のユーザー指示「必要ならweight stratified samplingも使って」に基づく追加候補である。
RIMCの `src/subset_sampling.py` と `cluster_scripts/subset_sampling_smoke.sh` を読み取り専用で参照した。
既存の直接MC reference・本校正のseedと予算・投入済みジョブは変更しない。
低noiseで直接MCが難しい場合の、MCMCと独立なreferenceを得るために用いる。

## 推定対象

decoder priorは各targetに固定し、同一priorのもとで f_w=P(failure | non-I weight=w) を測る。
異なるpriorで得たf_wを同じdecoderのreferenceとして再利用しない。
bit-flipではweight-wの位置集合を一様に選び、depolarizingではさらに各選択位置のX/Y/Zを独立・一様に選ぶ。
depolarizingのYは同一qubitのX/Z成分の両方に作用し、noiseを独立sectorへ置き換えない。
各重みの確率質量B_wはBinomial(n,p)で、P_L=sum(B_w*f_w)、条件付きweight平均はsum(w*B_w*f_w)/sum(B_w*f_w)である。
failure判定には本校正と同じProblem・decoderを用い、P_anyを推定する。

## 不確実性と予算

小さな重み層は全パターンを列挙し、大きな層は層内の独立MCとする。
Pauli層の全パターン数はC(n,w)*3^wであり、位置集合だけの列挙を完全列挙と呼ばない。
weight=0も実際に復号し、符号距離やBP-OSDへの未証明な訂正保証から低weight層を省略しない。
事前固定した層をすべて記録し、0失敗層を削除せず、0失敗のMC層をexact zeroと扱わない。
列挙層の区間は一点、MC層はClopper–Pearson区間を用い、MC層数でBonferroni配分して加重和の保守的区間を作る。
省略した重みのbinomial確率質量を、統計SEとは別の非負の打切り上限として区間上端に加える。
その上限が無視できない場合、打切り点推定を完全なP_Lとして扱わない。
pilotで予算配分を選ぶ場合はpilot標本を除き、独立seedの固定試行数による本番を新manifestに保存する。
referenceの区間が広ければ、低noiseの整合性を精度・95%被覆の保証へ格上げしない。

## 受入

全列挙できる小さいbinary/Pauli状態空間で、各層のパターン数・一意性・weight・全確率質量の正規化を確認する。
任意の有限failure集合について層別合成と直接全列挙の確率・条件付きweightが一致することを検査する。
層内MCの生成は位置の重複なし・Pauli label制約・固定seed再現性を確認する。
未観測層、重複層、不完全な列挙は拒否し、0失敗MCには正の区間上端を返すことを確認する。
小さいtileの公開failure判定と層内batch判定の一致を検査する。
クラスタはqsub・最大2ノードを維持し、smokeの時間・memory実測から本番予算を決める。
この仕様時点では層別の本番計測は未実施である。

## 資源・配分pilotの固定条件

4caseそれぞれについてdecoderのphysical priorを既存referenceのtarget、.01、.003、.001の4点に固定する。
weightは[0,1,2,3,4,5,6,7,8,10,12,16]、独立8replicate、weight=0は1パターン、それ以外は各512個の独立層内MCとする。
全1,536taskを新seed namespaceで実行し、前段のMCMC容量測定・本校正・直接MC referenceへ標本を混ぜない。
各taskの最初の16個までを公開Problem.is_faultyで再判定し、batch判定との一致を確認する。
このpilotは未計測weightを含むためP_L referenceとして使わず、予算配分と資源見積もりだけに使う。
実測後に全層を含む本番manifestを固定する。

## Pilotの回収・集計の受入

本番配分の入力には、固定manifestの全taskを含むpilotだけを使う。
artifactのidentityとpayload hashを照合し、各taskのcase・prior・weight・seed・Problem metadataを検査する。
成功taskは保存した状態からweight・alphabet・試行数・失敗数を再計算し、宣言したseedで層内乱数を再生成して状態配列と照合する。
同一case・prior・weightの中で同じ状態に相反するfailure判定があれば、決定性の不整合として集計を拒否する。
この検査は保存したfailure判定の整合性であり、別実装によるdecoderの正しさの検証とは区別する。
失敗taskは明示して残し、その層の本番配分準備済みフラグを偽にする。
全task成功かつ検査成功の場合だけ、配分用の層別count・層内失敗率・経過時間・memory・全列挙パターン数を出力する。
層内の二項区間は探索用の各層95%区間として記録し、多層・多priorの同時区間や論理エラー率区間として扱わない。
計時は構築・公開API照合・保存前検査を含むtask時間で、純粋なdecode速度とは呼ばない。
重複・欠落・seed変更・prior変更・count変更・状態変更を拒否し、失敗taskを成功分母から消さない受入を先に用意する。

## 本番の固定予算chunkと合成

本番の条件ごとにcase・physical decoder prior・0から連続するweight層・各層のenum/MCと固定試行数を指定する。
enum層の試行数は全パターン数に一致させ、0失敗を見て途中終了しない。
chunkは最大4,096試行の半開区間に分割し、enumでは全パターンのrank区間、MCでは固定試行予算内の位置を表す。
MCは新seed stage 130を用い、pilot stage 110や既存reference・MCMC・計時MCの標本を混ぜない。
各chunkにraw state・failure mask・固定prior・seed・Problem hash・公開APIとの照合数・CPU/wall時間を保存する。
合成時は各chunkのidentity・固定試行数・seed・raw state・mask・weight・alphabetを照合し、乱数または列挙区間からraw stateを再生成する。
欠落や重複は記録された失敗とは区別して拒否し、失敗chunkがあればその条件のreference区間と点推定を未取得にする。
全chunkが成功した場合だけ層別countを合成し、Clopper–Pearson/Bonferroniと未評価tail上限を維持する。
plannerはpilot監査とnative profileのdigestを記録するが、digest文字列を受け取ること自体をpilot成功の検証やqsub許可とは扱わない。
実際の本番予算選択、pilot監査実体との照合、native preflight、資源計画と投入はpilot完了後の別段階で行う。
上記のchunk生成・保存・raw照合・条件別合成を `cluster_scripts/tile_weight_reference.py` に実装し、既存の層別primitiveと合わせて14 passed・16.15秒を確認した。
受入はtile72/288のbit/depolarizingの小予算、weight 1の完全列挙分割、欠落・重複・改変の拒否、失敗chunkの保持と再試行しないことを含む。
これは本番の固定予算やreference値を生成した結果ではなく、実データの本番計測・resource測定・qsub投入は未実施である。

## 実行driverの入力と実行条件

実行driverは固定pilot manifestと監査JSONを読み、全1,536task・192層の成功、raw再生成済み、metadata確認済み、RSS取得済み、source hashと全層のcount整合性を検査する。
配分JSONは監査とnative profileのdigestを指定し、pilotと同じ4case×4priorの16条件を過不足なく含める。
予算は別途判断して固定し、この入力検査で目標精度を達成したとは扱わない。
plan時とrun時にnative profileと再現状態を照合し、入力5ファイルのcanonical digest、実行driverとprimitiveのsource/runtimeを固定する。
runはPBS_JOBID・96worker・単一thread環境を必須とし、全chunkを処理してから条件別にraw検査と合成を行う。
条件別合成は最大16個の独立処理であり、そのphaseのwalltimeをsampling phaseとは分けて残す。
失敗chunkがあっても全条件の未取得を記録してsummaryを保存し、seedの交換や自動再試行を行わない。
このdriver自体はqsubを呼ばず、実測に基づくresource計画と最大2ノードを守るsubmitterは別途用意する。
`tile_weight_reference_driver.py` にplan/runを実装し、chunk処理との関連受入は20 passed・21.99秒だった。
driverの入力検査と実行順序の受入では合成したpilot監査fixtureと模擬workerを用い、chunk処理の受入では実際の小予算tileデータを用いた。
この受入を、未完了の実pilotが成功した証拠や本番referenceの取得と扱わない。
driverを独立した `20261017-tile-weight-reference-v1` bundleへ配置し、Linuxで層別primitiveを含む27 passed・6.66秒を確認した。
固定production venvを使ったlogin node上のnative preflightも成功し、出力を保存した。
compute node上のpreflight、本番配分JSONの作成、資源測定とqsub投入は未実施である。

## 実行環境の証跡保存

環境照合の成否だけでなく、実際のprobe結果・hostname・PBS_JOBID・照合時間・manifest digestを保存する。
plan時とrun時の証跡は別ファイルとし、run時は入力とmanifestの整合性およびnative照合が通ってからworkerを開始する。
chunk summaryと最終summaryはrun証跡のhashを記録し、環境照合の時間をsampling時間へ混ぜない。
受入では両段階の証跡、worker開始前の保存、環境不一致での開始拒否、失敗chunkを含むsummaryとの対応を確認する。
証跡保存を実装し、関連受入はWindowsで27 passed・17.24秒、Linuxで27 passed・6.87秒だった。
更新版を `20261017-tile-weight-reference-v2` に配置し、固定production venvを使うlogin node上の実probe一致も確認した。
実行順序の受入は模擬probe・workerを用い、実pilotに基づくplan/runやcompute node上の証跡取得は未実施である。
今後の本番準備にはv2を使い、v1は変更せず保持する。

## 本番資源見積もりと投入の受入

submitterはplan済みの入力5ファイルからcontextを再構成し、manifestとの一致とpilot監査の完全性を確認する。
各chunkの時間は同じcase・prior・weightのpilot task最大時間にmax(1, chunk試行数 / pilot task試行数)を掛けて見積もる。
pilotにない正のweightは同じcase・priorの正の測定weightのうち最大の見積もりを使い、該当weightを結果に記録する。
96workerへの長いtask順の割当てでsampling時間を見積もり、条件内chunk時間の合計の最大値を16条件並列の合成用予備時間とする。
合成の実測値ではないため、これを性能測定や時間上限の保証として扱わない。
要求walltimeはsampling見積もりと合成用予備時間の和の2倍に600秒を加え、1800秒単位で切り上げる。
memoryはpilotの最大worker RSSに最大chunkのraw状態・maskの4コピー分を加え、96worker分の1.5倍と8 GiBの余裕を要求し、最低32 GiBとする。
24時間または340 GiBを超える計画は拒否し、計画の分割・再設計を必要とする。
この見積もりは新weightやenumの実測ではなく、予算の精度保証でもない。
投入直前に実プロセスからcoordinator不在とqueued/runningを含む既存要求ノード数を確認し、1ノード追加後も最大2ノードを守る。
qsub前に排他的なintentを保存し、応答不明・timeoutを含め自動再投入せず、同一rootのintentまたはledgerがあれば拒否する。
受入では固定入力の改変、未完了pilot、見積もりの上限、未知weightの扱い、qsub前のintent、投入競合とtimeout後の再投入拒否を確認する。
`submit_tile_weight_reference.py` を追加し、関連受入はWindowsで39 passed・10.43秒だった。
資源見積もりと投入の受入には合成pilot監査・模擬qsubを用い、実pilotからの見積もりやジョブ投入は未実施である。
その後、新しい `20261018-tile-weight-reference-v3` へ配置し、Linuxで39 passed・7.24秒を確認した。
固定production venvを使うlogin node上の実native probeも保存済みprofileと一致した。
今後の本番準備と投入にはv3を使い、v1/v2と稼働中のbundleは変更しない。
実pilotに基づくplan・資源要求、compute node上のpreflight、本番qsubは未実施である。

## 実pilotの回収と監査

2026-10-18、pilot 265201は終了コード0・PBS walltime13秒で完了した。
全1,536 artifactを回収・hash照合し、生成元Linux環境で全721,024試行・192層のraw乱数再生成、metadata・failure count・同一状態のlabel整合性を監査した。
失敗taskは0でRSSも全層取得でき、本番driverの `validate_pilot` が実監査JSONを受理した。
最大worker RSSは89.5625 MiB、最大task時間は2.301052秒だった。
これは配分・資源測定用pilotの完了であり、独立した本番予算・打切りweight・reference値は未取得である。
監査は保存済みfailure labelの内部整合性で、全標本を別decoder実装で再復号したものではない。

## Pilot後に固定する独立本番配分

監査済みpilotだけを入力とする決定的plannerを追加し、本番標本・BARの点推定や診断を配分に使わない。
全16条件について、未評価binomial尾部が1e-14以下になる最小weightまでを連続して評価する。
1層の全パターン数が4,000,000以下なら全列挙し、それ以外は独立層内MCとする。
この閾値ではtile72-bitはweight4まで、tile288-bitとtile72-depolarizingはweight3まで、tile288-depolarizingはweight2までを全列挙する。
MC配分の設計値にはpilotの平滑化率(failures+0.5)/(trials+1)を使い、未測定weightには分散設計値1/4を使う。
平滑化率は予算決定用であり、本番推定値・信頼区間に擬似countを加えない。
費用c_wは同じ層のpilot最大task時間をtask試行数で割った値とし、未測定の正weightは同じcase/priorの正weight中の最大値を使う。
各条件のMC設計作業量T=3,600 worker秒を、N_w=T*B_w*sqrt(v_w/c_w)/sum(B_j*sqrt(v_j*c_j))で配分する。
各MC層は最低4,096試行・最大4,194,304試行とし、4,096単位に切り上げる。
最低予算・上限・丸めとenum費用により総時間はTと一致しないため、別途submitterで全chunkの時間とmemoryを見積もる。
これらは独立した本番を始めるための固定予算であり、特定の相対精度・被覆や低noise referenceの有用な区間幅を保証しない。
1e-14の絶対尾部上限が推定対象に比べ大きければ、その領域の精度保証を行わない。
plannerはsource・policy・pilot audit・native profileのdigest、全層のmode/N、未測定層、尾部、丸め後費用を保存する。
受入では小状態空間での全列挙判定と尾部最小性、Neyman配分の比、0失敗と未測定層の正予算、丸め・上限、全16条件、入力改変拒否と再現性を確認する。

配分plannerの関連受入はWindowsで30 passed・2.94秒、Linuxで30 passed・1.11秒だった。
実pilotから固定した配分は全16条件・97,857,608試行・23,938 chunkで、Linuxで同一JSONをbyte単位で再現した。
全列挙・MCの境界は上記閾値のままとし、noise別の試行結果による早期終了・seed交換を行わない。
打切りweightはtile72のp=.03/.01/.003/.001で20/14/10/8、tile288のp=.05/.01/.003/.001で50/23/15/11となった。
全条件の尾部上限は1e-14以下であるが、tile288の低noiseではpilotで0失敗の層が多く、relative precisionの保証にはならない。
新bundle `20261018-tile-weight-reference-v4` で実pilotを使うplanとnative照合を実行し、固定manifest・環境証跡・qsub dry-runを保存した。
要求は1ノード・96 CPU・32 GiB・4時間30分で、sampling外挿652.49秒と未実測の合成用予備6,848.92秒を含む安全係数付きの見積もりである。
今後の層別本番はこのv4計画を使い、既存coordinator稼働中には競合するqsubを行わない。
本番qsub・compute node preflight・reference値の取得は未実施である。
