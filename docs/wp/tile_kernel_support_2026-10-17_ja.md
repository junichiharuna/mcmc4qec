# Tileのfailure支持・kernelと混合診断の区別

対象は固定済みのtile72/288、bit-flip/depolarizing、target priorに固定したBP-OSDと標準の残余logical failureである。
全失敗支持の連結性、長時間での混合、BARの名目95%被覆は、この記録時点では確立していない。
構成行列と代数的な確認結果は [structure_audit](data_tile_validation_2026-10-17/structure_audit/summary.json) に、各caseの行列は同じdirectoryのNPZに保存した。

## 符号・failureの前提

factoryは開境界weight-6 presetで、tile72はrank(Hx)=rank(Hz)=32、tile288はそれぞれ140、いずれもk=8だった。
X/Z検査の最大列重みは3、行重みの集合は{2,3,4,6}であり、一般の列重み2以下を前提とする既存MWPM接続へそのまま渡す設定ではない。
paired logical basisの積Lx Lz^Tは単位行列で、検査とlogicalの可換性はfactory受入に加えて監査行列にも保存した。
この計算はtile72/288の距離下界の独立証明ではない。

物理状態をbinary vector xに変換し、syndromeをH·x、logical observableをL·xと書く。
ここでHとLはmodelの線形mapを表す記号で、CSS検査行列の名前Hx・Hzとは区別する。
bit-flipでは入力次元はn、depolarizingではX/Z成分を並べた2nである。
Pauli labelはI=0、X=1、Y=2、Z=3で、YはX/Zの両成分を持ち、labelのXORは位相を無視したPauli積に対応する。
固定decoder Dに対する残余logicalはr(x)=L·x XOR D(H·x)、標準の失敗集合はF={x:r(x)≠0}である。
これは「1個以上のlogicalが失敗」の確率であり、P_any/kを1logicalあたりの失敗確率とは呼ばない。

## Stabilizerがつなぐ範囲

Sをphysical stabilizer generatorのbinary行列、AをHとLを縦に連結した行列とする。
今回の4caseではA S^T=0に加えて、rank(S)=入力次元-rank(A)が成り立った。

| case | binary入力次元 | rank(A) | rank(S)=nullity(A) |
|---|---:|---:|---:|
| tile72-bit | 72 | 40 | 32 |
| tile288-bit | 288 | 148 | 140 |
| tile72-depolarizing | 144 | 80 | 64 |
| tile288-depolarizing | 576 | 296 | 280 |

同じsyndromeとlogical observableを持つ二状態の差はker(A)に属し、このrank一致からker(A)=rowspace(S)である。
したがって、二状態は有限個のgeneratorを順番に掛けることで結べ、その途中でも両mapは変わらない。
固定された決定的なsyndrome-only decoderでは、同じsyndromeでのlogical observableの一致は残余logicalの一致と同値である。
よってstabilizer移動は、同じsyndrome・残余logicalを持つ集合（fiber）の中をつなぐ。
0<p<1のproduct noiseは全物理状態に正の質量を持ち、stabilizerの混合確率も正なので、各generatorの提案とMH受理は正の確率を持つ。
ただしstabilizer移動だけではsyndromeも残余logicalも変わらず、異なるfiber間をつなぐ役割はZ/Hに残る。
Z/H/Sの和を使った全failure支持の連結性は、上のrank一致だけからは従わない。
BP-OSDの決定性はこの議論の前提であり、有限の反復・順序変更・再構築probeを全入力上の決定性証明へ読み替えない。
任意のcustom failureについてstabilizer不変性を仮定することもできない。

## 詳細釣合い・非周期性と連結性

固定failure集合上の目標分布はπ_p(x)∝ν_p(x)1_F(x)である。
各kernelの提案確率をq_j、固定混合比をa_jとすると、異なる状態間の受理後fluxは(1-lazy)Σ_j a_j min{π_p(x)q_j(x,y),π_p(y)q_j(y,x)}となり、xとyの交換で不変である。
この性質は提案比とfailure gateを正しく適用した場合の詳細釣合いであり、supportの連結性を仮定しない。
Zの近傍は単一座標のcategory変更で、逆向き提案比には正規化定数も入る。
Hは非Iの物理weightを保存し、提案不能なbranchや同一labelへの再選択もself-loopとして残る。
Sは自己逆なgeneratorの一様選択で、重複generatorがあっても順逆確率は同じだが、weightが変わるのでnoise密度比によるMH受理は必要である。
共通lazy=.05により各状態のself-loopが少なくとも.05あるため周期性は除かれるが、異なる閉成分の間を移動できることにはならない。

既存の [Steane全列挙](data_calibration_2026-10-17/results/steane_components.json) では、prior=.03・OSD order=2のfailure支持64状態が既定Z/Hで56状態と8状態に分かれた。
同じ有限例ではZ/H/S=.6/.3/.1が一成分になり、両混合で詳細釣合い・定常性とlazy self-loopを数値照合した。
これはZ/Hの一般的な既約性を否定する反例と、候補Sの有限例での効果であり、OSD order=10のtileに対する連結性や混合時間の証明ではない。

## 初期状態と実測で確認すること

本校正ではrejection初期化とlogical-basis初期化、ZHとZHSを比べる。
logical初期化はphysical logical basisを使い、これらは最小重みのlogicalとは限らない。
例えばtile72のX basisの重みは[11,13,7,6,5,5,5,5]、tile288では[24,41,12,20,18,15,18,15]だった。
depolarizingのbasisはXの8行にZの8行を続け、初期化indexはreplicate×最大chain数+chainである。
最大8chainのため、偶数replicateはX basis、奇数replicateはZ basisから開始し、4chain比較では各basisの先頭4行を使う。
これは各replicateの中でX/Z初期状態を交互に混ぜた設計ではない。
元の192 replicateを主分母に維持し、偶数・奇数の96 replicateずつも層別集計して、初期化依存が平均で隠れないか確認する。
本校正のsource・seed・初期状態の設定は変更しない。

weight・syndrome weight・各残余logical bit・Bennett寄与のIAT/ESS/R-hat、sector遷移、異なる初期化間の平均・推定値差を別々に評価する。
診断が良好でも、未訪問成分の存在や全支持での収束を排除できない。
直接MCの独立referenceがある領域では条件付きweightとP_anyの両方を比較し、BARのbias・RMSE・被覆は未取得を含む固定cohortで確認する。
referenceのない低noiseでは、設定間の一致だけから精度や被覆を保証しない。

監査の受入は4 passed・2.23秒で、公開modelとbinary mapの一致、全generatorによるmap不変性、上表のrank一致を検査した。
本監査は軽量な行列計算としてローカルで実行し、既存のPBSジョブやcontroller bundleは変更していない。
