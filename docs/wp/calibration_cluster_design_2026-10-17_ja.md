# 混合・BAR被覆校正のクラスタジョブ設計（2026-10-17）

## 状態と参照元

第1段階は全46,080 trace・64,512解析行の計算、監査、回収を完了した。
結果と残課題は [校正完了報告](calibration_results_2026-10-17_ja.md) に記載し、以下の実装前計画と区別する。

本書は実装前の設計を記録し、2026-10-17の追加依頼で実装とPBS投入まで進めた。
実装は `cluster_scripts/calibration.py` のsubcommandと `submit.py` に統合し、PBSスクリプトをrun単位で生成する。
smokeジョブ265188は成功し、第1段階の本番265189〜265194を `qsub` で投入した。
現在の状態と実行手順は [実装・投入報告](tile_cluster_report_2026-10-17_ja.md) と [driver README](../../cluster_scripts/README.md) を参照する。
以下の予定ファイル名と第9節は設計時点の記録であり、実際のコマンドはdriver READMEを優先する。
ライブラリの版番号、公開sampling設定、既定の誤差法は変更しない。
設計時のmcmc4qec HEADは `6f7528645ddf988ed8008bad5c81e321aa2aaaf8` である。
`A:/dev/RIMC` は読み取り専用で参照し、HEADは `e788c60319a6295db606a9a0f45867c84645b7d7`、参照開始時の作業ツリーはcleanだった。

参照した研究側のファイルは次のとおりである。

- `AGENTS.md` の Cluster / DESIGN PRINCIPLE。
- `docs/cluster_job_design_guide.md`。
- `docs/superpowers/specs/2026-10-09-twelve-code-jobs-design.md`。
- `cluster_scripts/diag_audit.py`、`diag_audit.sh`、`lowp_audit_2e6_gr.sh`。
- `cluster_scripts/dmc_speedup_topo_smoke.sh`。

研究側の最近の仕様を参考に、PBS `workq`、`select=1:ncpus=96`、flat pool 96 workers、メモリ340 GB以下、smoke先行を設計の基準とする。
研究側の最大4ノードという例よりも、今回のユーザー指定「最大2ノード」を優先し、全フェーズ合計で2ノード・192 CPUを上限とする。
大きいPBS配列を作らず、少数のfull-node job内でtaskを処理する。
設計時点ではリポジトリの記録のみを参照し、実投入前にSSH接続・PBSキュー・Python環境を確認した。
研究側の観測量平均の校正結果を、BARの絶対確率区間の被覆保証として転用しない。
研究側で使われる自動commit・push・通知は、本設計のジョブには入れない。

## 1. 問いを分ける

1. exactな失敗確率に対し、BARの名目95%区間がどの程度被覆するか。
2. 区間の過小評価と、初期化・有限長混合による点推定biasを切り分けられるか。
3. 長さ・burn-in・chain数の増加で、bias、分散、被覆、利用可能区間数がどう変わるか。
4. 複数論理量子ビットの符号で、重み平均だけでは見えない失敗sector間の滞留があるか。

block長を変えてもsamplingの混合は改善しない。
block長調整、sampling長、初期化、chain数を同時に変更して改善理由を混同しない。
観測量平均のMCSEと、BARの論理誤り率のSEを別の列に保存する。

## 2. 第1段階：exactで被覆を測れる固定cohort

| 項目 | 事前固定案 |
| --- | --- |
| 符号 | toric d=3（18 qubits）、surface d=3（13）、Steane（7） |
| ノイズ | 独立bit flip、実験全体で少なくとも1論理bitが失敗する確率 |
| decoder | toric/surfaceは固定unweighted MWPM、Steaneは固定prior 0.03のBP-OSD（min_sum、100 iterations、osd_cs、order 2） |
| 通常低p ladder | 0.10 / 0.07 / 0.05 / 0.03 |
| 希少領域 ladder | 0.03 / 0.01 / 0.003 / 0.001 / 0.0003 / 0.0001 |
| anchor / truth | 同じ固定decoder・failure定義の全列挙 |
| 独立反復 | 各条件192 replicate、ID 0..191 |
| 連鎖数 | 主解析4 chains/replicate/rung |
| 保存長の主比較 | 600 / 6000 / 60000（thin=1） |
| burn-in | 主解析600、追加の一要因比較6000 |
| 実行長 | chainごとに66000状態を保存し、上記windowを後処理で切り出す |
| kernel | Z/H=0.7/0.3、cluster_k=2、lazy=0.05 |
| 誤差法 | block bootstrapとcross_chainを同じtraceから評価 |
| block長 | 8 / 32 / 128、追加1024は6000/60000保存のみ |
| bootstrap回数 | 1000、samplingと独立した固定seed系列 |
| 初期化 | exact conditional stationary start と dispersed faulty start の2 arm |

SteaneのOSD orderは小さい検査行列のnullityを超えない2を明示し、公開既定を変更しない。
decoder priorはladder内で変えず、異なるfailure集合を密度比だけで接続しない。
通常低pと希少領域は別cohortとし、同じp=0.03があっても独立したsampling seedを割り当てる。
192回の95%被覆の二項標準誤差は約1.57 percentage pointsなので、この規模でも名目被覆の証明にはならない。
例えば183/192被覆のWilson区間はおよそ91.3–97.5%となり、点の被覆率だけで合否を決めない。

### 初期化による切り分け

全列挙のfailure状態集合を保存し、各rungのproduct-noise確率に比例して独立に初期状態を抽選するarmを設ける。
このarmでは初期分布biasを除去できるが、traceの自己相関や誤差推定の有限標本性は残る。
dispersed armは、failure状態集合の低重み・高重み側から、可能な限り異なる残余論理sectorを含む4状態を決定的に選ぶ。
state digest、重み、syndrome、decoder補正後の残余論理bitを記録し、選択規則を結果を見る前に固定する。
単にlogical basisの最小・最大重み行を選んで異なるstartだとみなさず、重複状態を検出する。
存在するsectorが4未満の場合はその事実を記録し、存在しないsectorを作らない。
全初期状態のfailure条件と各rungで正のsupportを検査する。
低pで公開既定の棄却初期化を使うと上限10000試行で失敗し得るため、主校正は明示startを使う研究設定とする。
公開既定の初期化の可用性はsmokeの別項目として測り、成功するまでseedを替えない。

### 同一traceの再利用

長さ・burn-in・block長・誤差法の比較は同じ保存trace上で行い、対応のある比較とする。
各replicateの各rungに4独立chainを割り当て、同じchain番号を隣接rungのcross-chain共分散計算で一貫して対応させる。
独立性の単位は192 replicateであり、chain、checkpoint、block長を独立な被覆試行として数えない。
chain数16の比較は、第1段階後の事前計画を別に切り、4chainの被覆結果を見て良いseedだけを延長しない。

## 3. 第2段階：大きい実符号とtile code

第1候補はtoric d=5、surface d=5、BB72であり、tileの構成受入後に小さいtile instanceと[[288,8,12]]系列を追加する。
全列挙不能な符号で独立MC推定値をexactと呼ばず、その推定誤差を保持する。
targetはまず0.01 / 0.001 / 0.0001を候補とし、別seedのpilotで隣接rungの重なりとanchorの失敗数を調べてからladderを固定する。
BP-OSDのpriorと全設定は各ladderで固定し、pごとに最適化するdecoder性能曲線は別実験とする。
MC anchorは各replicateで独立した固定試行数を使い、共有anchorの実現値によるcohort全体の相関を避ける。
必要ならexact anchor群との区別を明示したanchor誤差の一要因実験を第1段階にも追加する。
独立参照は固定予算の直接MC、または重み別層別samplingとし、成功数を見て停止した結果に固定試行数Wilson区間を当てない。
層別法では各重みの試行数、failure数、未列挙のbinomial tailの上界、decoder設定・行列digestを保存する。
RIMCの参照CSVは比較資料であり、decoder・matrix ordering・failure定義・打切りが一致するまで数値の正解として自動読込しない。
参照区間を[L,U]としたとき、BAR区間が[L,U]全体を含む回数と、[L,U]に交差する回数を別に出す。
これは参照精度に条件付けた包含・交差診断であり、exact被覆と同じ列名にしない。
極低pで独立参照が得られない場合は「混合診断のみ、被覆未評価」とする。

## 4. ジョブ分解と計算量

| Job | 内容 | 資源案 | 完了条件 |
| --- | --- | --- | --- |
| C0 | 全経路smoke、resume、時間・RSS測定 | 96 CPU / 128 GB / 30分 | chainごとの一致、出力完全性、再開で重複0 |
| C1 | 3符号のexact reference bank作成 | 96 CPU / 128 GB / 30分を初期上限 | 分割全列挙の集合一致、checksum、公共exact APIとの一致 |
| C2 | 第1段階の全chainを4 shardで生成 | 各96 CPU / 128 GB、walltimeはC0実測から確定 | manifestにある全chainのcommit markerとdigest一致 |
| C3 | window・BAR・誤差・診断・cohort集計 | 96 CPU / 128 GB、C0実測から確定 | 全replicate、全要求区間の状態を記録 |
| C4 | 大きい符号のpilotと独立参照 | 96 CPU / 256 GB以下、pilot後に確定 | 設定・資源見積もりの固定、参照の不確実性表示 |
| C5 | 大きい符号の本計測 | C4で条件を確定した後に設計確定 | 別の固定manifestで全条件を回収 |

第1段階のchain数は3符号×(4+6)rungs×2初期化×192replicate×4chain = 46080である。
samplingは46080×66000 = 3041280000 stepsであり、exact列挙・decoder構築・診断・bootstrapは別費用として計上する。
各chainの公開API呼出しは `SamplingConfig(chains=1, samples=66000, burn_in=0, thin=1, ...)` とし、burn-inは保存列の後処理で一度だけ除く。
解析単位は(code, ladder, init, replicate)の2304組である。
各組で6 windows（3保存長×2 burn）と、bootstrapの18設定＋1024-blockの4設定＋cross_chainの6設定を評価するため、targetの推定行は合計64512となる。
未取得区間も行として残し、補助的なrung別・chain別診断は別テーブルに保存する。
1 workerの単位は(code, ladder, init, replicate, rung, chain)とし、worker内で追加のPoolを起動しない。
4 shardはreplicate IDのmod 4で分け、各11520 tasksを同じ構成で持たせる。
4 shardを同時投入可能な実行状態にせず、2本の依存チェーン（shard 0→2、shard 1→3）として最大2本ずつ実行する。
第2段階や解析jobも同じ2ノード枠に含め、別キャンペーンという理由で上限を超えない。
各shardは単一flat Pool(96)、長いと予測されたtaskから `imap_unordered(chunksize=1)` で処理する。
全task数は96の倍数だが実測時間は異なるため、末尾まで厳密に96稼働する保証はなく、最長残存taskと実測pool利用率を報告する。
残りtaskを詰めるためにseedの統計設計を変えない。
BLAS/OpenMP/MKL/NumExprのthread数を各1に固定し、96 worker×内部threadの過剰並列を避ける。

### Smokeとwalltimeの決め方

C0は独立したpilot seed領域で各符号・rung・initの1000/10000 stepsを測り、最低96独立taskを作る。
各taskの初期化、sampling、decoder構築、診断、書込時間を分け、wall time・CPU time・ピークRSSを保存する。
1000から10000への傾きと固定費で66000を外挿し、cacheの飽和前後とFFT・bootstrap費用を別に見る。
予測task時間を96 workerにlongest-firstで割り当てたmakespanと、sum(task time)/96・max(task time)を併記する。
各本番walltimeは初期方針として予測makespanの2倍＋書込余裕とし、24時間を超える場合はtask集合をさらに分割する。
RIMCのs/stepは参考値であり、mcmc4qecのクラスタ実測として流用しない。
ローカル予備計測もクラスタwalltimeの確定根拠にはしない。

### メモリと保存容量

現行 `sample_faulty` は[chain,saved,n]のuint8全状態列を保持し、研究runnerの `record_trace=False` 相当の公開optionはない。
本番workerは1 chain / 1 rungだけを実行し、状態列は観測量を作った直後に解放する。
第1段階の最大状態列は66000×18 bytes = 1.188 MB/workerである。
残余論理sector計算のdecoder呼出しも計測対象とし、同じ固定decoderで計算する。
decode cacheは `cache_cap=200000, cache_policy="lru"` とし、entry数とピークRSSを両方記録する。
entry capはbyte上限ではないので、memory要求をentry数だけから確定しない。
保存は重みuint16、syndrome重みuint16、残余論理sector uint32を基本にし、k>32では固定幅のbit-packed表現を使う。
第1段階の3系列は非圧縮で約24.33 GB、重みだけなら約6.08 GBであり、I/O容量を先に確保する。
圧縮率を容量保証に使わず、状態の全dumpは受入検査用の代表traceに限定する。
BB・tileはn×N、decoder cache、NumPy一時配列、FFT領域を加算し、96 worker合計と親processを含めてRSSを見積もる。
例として288qubits×200000保存は57.6 MB/worker、2000000保存は576 MB/workerであり、後者を128 GBで無条件に投入しない。
最初の大符号pilotは20000保存、本番上限候補は200000とし、2000000への延長は別計画にする。

## 5. 乱数、状態保存、再開、集計

task seedは(master seed, schema version, code ID, ladder ID, init ID, replicate, rung, chain, purpose)から `SeedSequence` で生成する。
Pythonの組込み `hash()`、worker番号、投入順序、完了順序をseedに使わない。
purposeをinitialization / sampling / bootstrap / anchor / independent referenceに分ける。
長さ・block長・誤差法はsampling keyに含めず、同一traceの後処理とする。
exact bankは行列、decoder実装・設定・依存版、failure、source digestで照合し、過去のcacheのsource確認を無効化しない。
同一syndromeを繰り返してdecoder出力が一致することもsmokeで確認する。

runごとに固定manifest.json、environment.json、package wheelのSHA256、driverのSHA256、source HEADと差分digestを保存する。
各taskは自分専用の一時ファイルへ書き、flush・close後のatomic renameでdataを確定してから、checksum付きの完了JSONを最後に置く。
summary CSVの行や `.done` の個数だけで完了と判定しない。
resumeはmanifestとtask keyと全artifactのchecksumが一致したtaskだけをskipする。
途中で停止したchainは同じseedで最初から再実行し、別の `sample_faulty` 呼出しをつないで同一chainの続きとみなさない。
一時ファイルは未完了として扱い、既存の成功結果は無条件削除しない。
例外・初期化不能・overlap不足・interval unavailableを状態として保存し、都合の良いseedへの差替えをしない。
完了していないcohortを完了扱いにせず、partial集計は明示した別出力にする。

### BARの後処理

独立同率bit flipでは隣接密度のlog比は `w*log(q/p) + (n-w)*log((1-q)/(1-p))` なので、BARには重みtraceが十分である。
この圧縮は一般の相関ノイズやlocationごとに異なる率へは適用しない。
bootstrapでは同じrungのresamplingを左右の隣接edgeに共有し、rung共有共分散を保持する。
cross_chainはchain番号ごとのedge vectorの共分散をchain数で割り、公開実装と同じpooled BAR点推定とanchor分散を使う。
長trace×1000 bootstrapの費用は無視できないため、bit-flipの重み別度数と円環blockの累積度数による実装を候補とする。
末尾の短いblock、棄却による反復状態、chain内の順序、同じrungを共有する乱数を変えない。
最適化前後を公開APIおよび `bar_paper_protocol.py` の参照経路と照合してから本番へ使う。

## 6. 判定と出力

各replicateにpoint estimate、log estimate、SE、区間端、truth、covered、interval available、overlap、bootstrap成功数、warningsを保存する。
各chain/windowにweight、syndrome weight、残余論理sector各bitの平均・分散・IAT・ESS、sector遷移数を保存する。
split R-hatは同じwindowの4chainをまとめて観測量ごとに計算する。
現行APIの受理集計はchain全体の値として保存し、状態変化率からwindow別のMH受理率を推測しない。
constant traceのIAT/R-hatは未判定として扱い、良好な値に置換しない。
BARの各edgeのBennett寄与系列も重みから計算して診断し、重みだけのIATで区間の正しさを判定しない。
cohortには被覆数/192とWilson区間、区間取得率、取得済み区間だけの条件付き被覆、bias、RMSE、empirical SD、mean estimated SE、区間幅を出す。
未取得区間を除いた分母だけで良好な被覆を報告せず、運用上のcovered-and-available/192も必ず示す。
長さや初期化間のbias差・区間幅差・被覆indicator差はreplicate IDを揃えた対応比較とし、差の不確実性も示す。
全条件の結果を保存して報告し、block長を本番被覆の良さだけで選んだ「最適値」の名目被覆を同じcohortで主張しない。
設定を選ぶ場合は別のvalidation cohortを事前に追加する。

## 7. 配置と実装予定インターフェース

独立した配置先 `/home/user/workspace/mcmc4qec` を候補とし、RIMCの作業ディレクトリ・環境・結果CSVを変更しない。
計算環境の正確なパスとquotaは投入前に確認する。
wheelと固定依存lockとdriverを同じbundleにし、クラスタ `py311` から作った専用venvで動作させる。
ジョブ開始時にpackage/driver/manifestのdigestを検査し、実行中に `git pull` や依存更新をしない。

実装予定ファイルは以下のとおりである。

| ファイル | 責務 |
| --- | --- |
| `cluster_scripts/calibration_plan.py` | 固定manifestの生成、task数・重複・seed key検査 |
| `cluster_scripts/calibration_truth.py` | 分割全列挙、reference bankとsource照合 |
| `cluster_scripts/calibration_run.py` | flat Pool、1chain/1rung task、atomic保存、resume |
| `cluster_scripts/calibration_analyze.py` | compact traceからBAR・誤差・多観測量・完全性検査 |
| `cluster_scripts/calibration_smoke.sh` | PBS smoke、再開検査、時間・RSS測定 |
| `cluster_scripts/calibration_sample.sh` | manifestで指定したshardのみ実行 |
| `cluster_scripts/calibration_analysis.sh` | sampling成果物の完全性を確認して後処理 |
| `cluster_scripts/calibration_submit.py` | dry-runを既定とし、資源確定後に最大2ノードで依存関係を構成 |

実装後の順序は、ローカル小例受入→bundle配置→C0→C1→C2の4 shard→C3→独立レビューとする。
C0は小さいon-the-fly exactを使用できるようにし、まだ作っていないC1 bankに依存させない。
C1の長い全列挙はprefixまたは整数index範囲を96以上のtaskに分け、重複・欠落がないことを検査する。
Steaneだけの小規模準備やmergeの短い直列部分まで96稼働したと主張せず、その時間を報告する。
データ依存にはPBS `afterok`を使い、同時ノード数の制限だけに `afterany` を使う場合も入力完全性をdriver側で検査する。
PBSの出力先ディレクトリはqsub前に作り、配列indexやshard番号とmanifestの件数を一致させる。
ジョブコメントにはWHAT / WALLTIME / SATURATION / MEMORY / RESUME / REFERENCEを記載する。
smoke合格後、見積もりの長いshardを2本の依存チェーンへ均等に割り当て、同時最大2ノードを超えない。
同じ構成の4 shardなら2波となり、samplingの理想的なwall timeは総core時間/192で、実際には各チェーンのmakespanとI/Oを加算する。
成果物は別runディレクトリからchecksum付きで回収し、結果のcommit・pushはユーザー依頼時に行う。

## 8. 実装の受入条件

- 192 replicate・各4chain・全rungのtask keyが一意で、4 shardの和集合が全manifestと一致する。
- 投入計画の依存グラフから、smoke・truth・sampling・analysis・延長を含めた最大同時ノード数が2以下であることを検査する。
- worker数1/2、task順序、再投入の有無でseed・状態・BAR結果が変わらない。
- 全列挙bankの重み別failure数、truth、conditional weightが公開 `exact` と一致する。
- stationary startの全有限状態確率が条件付き分布に一致し、dispersed startがfailureかつ正supportである。
- 小問題でcompact traceのBAR点推定・共分散・SE・区間・未取得判定が公開APIと一致する。
- bootstrapで共有rungを独立に引き直す誤実装を検出する検査を含める。
- 中断・途中ファイル・破損checksum・誤manifest・重複task・欠落seed・失敗taskを検出する。
- mergeは全期待keyとartifactを検査し、不完全な本番summaryを成功として出さない。
- 科学的な受入は小仕様→受入テスト→実装の順とし、benchmark本体をpytestから実行しない。

## 9. 設計時点の確認範囲

今回は設計とローカルの軽量API予備計測までとし、cluster smoke、長trace本計測、192 replicate校正は未実施である。
ローカルの予備計測は `data_calibration_2026-10-17/pilot.py` と同ディレクトリの出力に記録する。
予備計測は各符号1seedであり、被覆率を評価する標本には含めない。
surface d=3とSteaneの公開API実行・JSON往復・source/seed照合は成功し、完全な結果JSONを保存した。
toric d=3は全列挙279.85秒・BAR10.16秒で要約を出力したが、3符号をまとめた予備processを約5分の上限で停止したため完全な結果JSONは残っていない。
この中断とstdout要約を `pilot_interrupted.json` に記録し、toricの完全な予備artifactは未取得とする。
これは並行負荷のあるローカル実行であり、速度比較・クラスタwalltime・被覆率の根拠には使わない。
tile codeの構成・decoder調査と受入案は [別紙](tile_codes_survey_2026-10-17_ja.md) に記載する。
