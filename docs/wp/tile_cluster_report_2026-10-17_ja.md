# Tile対応・クラスタ実装と投入記録（2026-10-17）

本書は実装・投入時の記録を含む。
その後、全sampling・解析・監査ジョブが終了コード0で完了し、46,080 trace・64,512解析行を回収・検証した。
被覆と混合の結論、Steaneの既定Z/Hの可約性、追加計測の判断は [校正完了報告](calibration_results_2026-10-17_ja.md) を参照する。

`make_tile_code`、既存BP-OSDへの接続、校正driverを実装し、PBSの `qsub` でsmokeと第1段階の本校正を投入した。
版番号0.1.0.dev5と公開sampling既定は維持し、commit・pushはしていない。
変更前HEADは `6f7528645ddf988ed8008bad5c81e321aa2aaaf8` である。
`A:/dev/RIMC` は投入手順の読み取り専用参照とし、終了前の `git status --short` も空だった。

## 実装

`make_tile_code(l,m,preset="w6_288_8_12")` は開境界のweight-6 tile族を生成する。
可換性、rank、完全な論理basis、paired logical条件を検査し、6×6でn=72,k=8、12×12でn=288,k=8を確認した。
3×3は境界pruningによりn=13,k=3となり、両sectorの距離2を全列挙で確認した。
288qubitsの文献上の距離12の下界は独立証明していない。
X/Z両sectorのBP-OSDで72個全ての単一qubit誤りを復号し、通常のMWPMは次数3以上の列を拒否することを確認した。
追加APIはNumPyだけで構成でき、復号と `examples/tile_bposd.py` にはoptional依存を使う。
static CSS対応であり、tileの物理syndrome抽出回路は追加していない。

`cluster_scripts/calibration.py` はmanifest、96分割exact bank、sampling、compact trace解析、集計、smokeをsubcommandにまとめる。
`submit.py` はdry-runを既定とし、明示実行時に `qsub` を呼び、各job IDを即座に台帳へ保存する。
samplingの整数seed keyはtask順序・worker数から独立し、既定のZ/H=0.7/0.3、k=2、lazy=0.05を使う。
stationary初期化は全列挙failure bankの正確な条件付き分布から引き、dispersed初期化は重みと残余logical sectorを分散させる。
全ての棄却・lazy stepを残し、weight、syndrome weight、残余logical bitmaskを保存する。
artifactのmanifest・identity・SHA-256が一致する場合だけ再利用し、不完全なchainは同じseedで最初からやり直す。
記録済みのsampling失敗はseedを置き換えず、区間未取得として分母に残す。
同一rungのbootstrap drawを隣接BAR edgeで共有し、独立bit-flipに限ってweight度数からBennett方程式を解く。
解析にはIAT、ESS、raw split R-hat、重み・syndrome weight・logical bit・Bennett寄与の数値ACFを保存する。

## クラスタ実測と投入

配置先は `/home/user/workspace/mcmc4qec/20261017-tile-calibration-v1` で、専用venvを作った。
Pythonは3.11.9、主要依存はNumPy2.4.6、PyMatching2.4.0、ldpc2.4.1、bposd2.1に固定した。
全依存は `data_calibration_2026-10-17/cluster_environment.lock.txt` に記録した。
配置archiveのSHA-256は `482b3bfdb4100aacc014c880f7f6dc85ad649fb0f7d31dad202fa0b877cdc9b1` で、展開前にリモートで照合した。
配置時のfile hashと変更元commitは `cluster_bundle.json` に保存した。
その後のローカル変更は文書、実行例のsummary出力、受入検査の追加であり、稼働中のdriverとwheelを上書きしていない。

| Job ID（末尾は全て `.node-PRISM`） | 役割 | 依存 | ノード・CPU・メモリ | 上限時間 |
|---|---|---|---|---|
| 265188 | smoke | なし | 1・96・128GB | 30分 |
| 265189 | exact bank | なし、smoke完了後投入 | 1・96・32GB | 30分 |
| 265190 | sampling shard0 | 265189成功 | 1・96・32GB | 30分 |
| 265191 | sampling shard1 | 265189成功 | 1・96・32GB | 30分 |
| 265192 | sampling shard2 | 265190成功 | 1・96・32GB | 30分 |
| 265193 | sampling shard3 | 265191成功 | 1・96・32GB | 30分 |
| 265194 | 解析・集計 | 265192と265193成功 | 1・96・46GB | 19時間 |

依存には全てPBS `afterok`を使い、4 shardを2本のチェーンへ分けるため、本作業の同時使用は最大2ノードとなる。
smokeは終了コード0、PBS walltime71秒、driver計測69.66秒だった。
480本×10,000stepの全条件sampling、checksum再開、worker1/2による8本の短いfresh実行のcompact trace一致、24groupの解析と336行集計を確認した。
さらにtile72の1,000stepを48本、tile288の200stepを48本実行し、保存状態のfailureとResult JSON往復を確認した。
tile smokeのtask時間中央値は72qubitsで1.63秒、288qubitsで2.00秒であり、文献の研究精度を再現する長さではない。
長さ60,000・bootstrap1,000の容量計測は96taskを使い、短traceの反復を計算負荷の測定だけに用い、科学集計には混ぜていない。
実測からのsampling shard予測は各873.27秒で、2倍を上に丸めて30分の要求とした。
解析は全28条件を最も高価なwindow相当として保守的に見積もり、予測33,535.47秒の2倍を上に丸めて19時間の要求とした。
これらは予測と資源要求であり、本番の実測完了時間ではない。
exact bankジョブ265189も終了コード0、walltime6秒で完了した。
投入時点ではsamplingと解析の最終成果は未回収だったが、現在は上記の校正完了報告に全件検証と本番被覆率を保存した。

## 検証

- 小仕様→受入テストの失敗確認→実装の順で進めた。
- Tileとdriverの受入は27 passed、4.49秒だった。
- weighted BAR、共有rung共分散、円環block末尾切断を既存のBennett・cross-chain・block index実装と数値照合した。
- Steaneの全128状態でbankのfailure判定を公開 `Problem.is_faulty` と比較し、3個のpで公開 `exact` と一致した。
- クラスタbankのp=0.03はtoric3で0.021074759859217335、surface3で0.01938581216207451、Steaneで0.016418097822239994となり、先の公開API予備計測と丸め誤差内で一致した。
- strict mypyは28 source fileで成功した。
- source全suiteは520 passed・5 skipped・230.84秒で、追加例を索引へ記載する前に走った文書index検査1件が失敗した。
- 例の索引とsummary出力を追加した後、関連する文書・tile例の検査は7 passedとなった。
- installed core wheelのtile・型関連は17 passed・2 skipped、9.18秒だった。
- 最小tileの距離assert追加後もinstalled coreのtile検査は14 passed・2 skipped、0.46秒だった。
- installed optional wheelのtile・driver・型・tile例は31 passed、18.25秒だった。
- core/optional両方の `verify_wheel.py` が成功し、28 source一致、21例の対応範囲、公開文書コード、optionalの4 quick notebookを確認した。
- tileのquick例はinstalled optionalで1.27秒だった。

source全suiteのskip5件は研究環境を使う照合であり、今回はremote CIを実行していない。
Windows notebookには既知のzmq event-loop warningが1件あった。
検証成功と診断値は混合・エルゴード性・名目95%被覆の証明ではない。

## 続行と回収

`ssh cluster 'qstat -u user'` で監視する。
実行手順と中断時の扱いは [cluster_scripts/README.md](../../cluster_scripts/README.md) に記載した。
`runs/production/coverage_rows.csv` と `summary.json`、全group artifactの完全性を監査ジョブ265195で確認し、全archiveをローカルへ回収した。
今回の本校正はtoric3・surface3・Steane、2 ladder、2初期化、192 replicate・各4chain、全46,080 task・30.41億step・64,512解析行である。
tileを含む大きい符号の長trace校正は、第1段階の結果と独立referenceの予算を確認する後続段階とする。
計測完了後も公開既定を維持し、短いtile smokeを低ノイズの精度保証として扱わない。
