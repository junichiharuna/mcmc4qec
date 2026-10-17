# Tile codeの構成・decoder調査（2026-10-17）

## 対象と結論

ユーザーが指定した対象はSteffanほかの [Tile Codes: High-Efficiency Quantum Codes on a Lattice with Boundary, arXiv:2504.09171](https://arxiv.org/abs/2504.09171) である。
構成上はCSS符号なので、Hx・Hzと完全なLx・Lzを作れば、既存の `CSSCode`、bit/phase-flip model、depolarizing model、BP-OSD、条件付きMCMC、BARに接続できると判断する。
これは現在のAPIとの整合性に基づく実装方針であり、tile factoryを実装・実行した結果ではない。
最初の対応は開境界のweight-6系列と既存BP-OSDを推奨し、回路構築・Clifford deformation・directional tileは別の段階とする。

## 原論文から必要になる構成要素

原論文では格子の辺をqubitとし、局所的なX/Z stabilizerの形であるtileと、それを置くbulk・boundaryのlayoutを組み合わせる。
tileはB×Bの箱に収まり、T1の辺の除外規則と、T2の反転・水平垂直交換によるX/Z対応でbulkの可換性を得る。
境界ではtile supportを物理qubit集合へ制限するが、X/Z boundaryの重なりを壊さないanchor配置が必要である。
最後にXまたはZ検査から支持されないqubitと空になった検査を整理する。
したがって、既存BB factoryの周期shiftを非周期shiftへ単純置換しただけでは開境界の正しさを保証できない。
根拠は原論文の「Systematic construction of tile codes」、T1/T2、Figure 1である。
原論文が示す代表例はweight 6の[[288,8,12]]、weight 8の[[288,8,14]]と[[512,18,19]]であり、距離は著者らが整数計画法で確認した値である。
このライブラリがその距離下界を独立に検証したとは扱わない。
原論文本文にはdecoder性能比較や復号thresholdの評価は見当たらず、符号の `kd^2/n` の優位性を論理誤り率の優位性に読み替えない。
出典：[原論文本文・Table I](https://arxiv.org/html/2504.09171v1)。

## 多項式、行列、論理演算子

二つの辺の向きに対するsupportをGF(2) Laurent多項式の組(f,g)で表し、相手側は逆向きshiftを伴う交換から作る。
有限領域への制限ではX/Zのanchor範囲とqubitの座標原点を固定する必要がある。
後続の回路論文はweight-6の[[288,8,12]]系列について、正規化後の一例として `f=x+x^2+y^2`、`g=1+x^2*y+x^2*y^2` を与えている。
同論文の6×6格子はdistance 4の例であり、12×12における288qubits・8logical qubitsの系列との対応を検証候補にできる。
この表記は原論文の図から直接読んだ座標ではないため、採用時はX/Z交換、格子反転、qubit permutationを明示して図または別構築と照合する。
出典：[Bae–Park, Section II.1・Table I](https://arxiv.org/html/2607.05897v1#S2.SS1)。

初版のLx/Lz構築には、既存 `codes.py` のGF(2) nullspace・quotient basis処理を再利用できる。
少なくとも `Hx @ Hz.T = 0`、`Hz @ Lx.T = 0`、`Hx @ Lz.T = 0`、`k=n-rank(Hx)-rank(Hz)`、logical pairingのrank=kを検査する。
`CSSCode` のpaired basis契約を満たすようpairingを単位行列化するか、独立basisであることを明示する。
「Logical Operators and Derived Automorphisms of Tile Codes」は、条件付きで境界に支持を持つcanonical symplectic logical basisをcellular automatonで構成する方法を与えている。
初期実装にその全理論を必須とはせず、GF(2)構築の独立照合やboundary logicalの提供に使う候補とする。
出典：[Breuckmannほか, arXiv:2511.14589](https://arxiv.org/abs/2511.14589)。

## Decoderの選択

| 候補 | 現時点の位置付け | mcmc4qecとの接続 |
| --- | --- | --- |
| BP-OSD | 初版の基準decoder | 既存 `bposd_decoder` を使用可能な構成 |
| BP-LSD | 大規模化時の速度・精度比較候補 | ldpcのadapterを追加し、correction→logical mapを明示 |
| MWPF | hypergraph復号の比較候補 | 新しい依存・adapter・受入が必要 |
| PyMatching/MWPM | 一般のtileへそのまま適用する既定にはしない | 各検査行列の列重み≤2の場合だけ既存wrapperを許可 |

ldpcの公式文書はBP-OSDのsyndrome整合性とBP-LSDの局所行列反転を説明している。
BP-LSDは大きい行列で速度面の利点が期待できるが、tileでBP-OSDと同じ精度になるという保証ではない。
出典：[ldpc公式decoder文書](https://software.roffe.eu/ldpc/quantum_decoder.html)。

「Strictly Local Tile-Code Architectures on Two-Dimensional Planar Lattices」は、回路ノイズの特定条件でBP-OSD、BP-LSD、BP-UFD、MWPFを比較し、試した条件ではBP-OSDの論理誤り率が最も低かったと報告する。
その設定はmin-sum、scaling factor 0.5、max_iter=2000、OSD-CS order 7である。
これは特定の回路・距離・ノイズ・計算予算での比較なので、静的bit-flipへの最適設定として無検証に採用しない。
出典：[同論文 Appendix A/B](https://arxiv.org/html/2607.05897v1#A1)。

既存ライブラリのBP-OSD既定はmax_iter=100・min_sum・osd_cs・order 10であり、文献設定とは異なる。
構成受入では既存既定と文献設定の両方を明示的な選択肢として試し、小符号ではOSD orderがnullityを超えないよう検査する。
BARではdecoder prior・反復数・schedule・OSD設定をladder全体で固定する。
decoderをpごとに作り直す性能評価と、共通failure集合を必要とする通常BARを区別する。
脱分極ノイズは既存の相関したI/X/Y/Z samplingを維持し、sector別decoderを使う場合はdecoder側の近似として明示する。
`mwpm_decoder` は列重み>2を既に拒否するため、tile factoryを追加してもこの検査を緩めない。
PyMatchingの行列からgraphへの対応は [公式API](https://pymatching.readthedocs.io/en/stable/api.html#pymatching.Matching.from_check_matrix) を参照する。

## 実装資料の扱い

[JD0111phys/biased_noise_tile_code](https://github.com/JD0111phys/biased_noise_tile_code) に、開境界・周期境界の行列生成とbiased noise実験の実装が見つかった。
これは原論文著者の公式実装として確認できたものではなく、独立照合の候補である。
`tile_code_and_clifford_deformation/tile_code.py` は固定weight-6 offsetsと開境界anchorを明記している。
確認した実装では `B` 引数に対して境界の負offsetが-2,-1に固定されており、そのまま任意B対応だとみなせない。
また、未支持qubit除去はX/Zいずれかに支持されるもののunionを保持しており、原論文のX/Z両方の支持要件と一般には同じ処理ではない。
したがって、そのコードのコピーや出力を唯一の正解とせず、論文規則から独立実装し、可換性・rank・layoutの照合に使う。
コード再利用のlicense確認は未実施であり、今回は第三者コードを取り込んでいない。
出典：[確認した実装](https://github.com/JD0111phys/biased_noise_tile_code/blob/main/tile_code_and_clifford_deformation/tile_code.py)。

## 追加APIの案と受入順序

初版は `make_tile_code(l, m, *, preset="w6_288_8_12")` のように格子寸法と検証済みtileを指定する形を候補とする。
distanceを入力して任意の所望距離を保証するAPIにはせず、preset名の数値は文献の代表instanceの名称と説明する。
任意tile/任意layoutの汎用APIは、boundary規則が固まった後に別途追加する。
layout、辺の順序、anchor、pruning前後のqubit map、X/Z offsets、出典、文献距離と独立検証範囲をmanifestに残す。

1. 小仕様にedge座標・向き・X/Z anchor範囲・pruning・重複項のGF(2)処理を明記する。
2. B=2のsurface相当例で既存surface factoryとのrow space・logical spaceの一致を確認する。
3. 小さいweight-6 instanceでCSS可換性・rank・完全な論理basis・列重みを検査する。
4. 12×12の代表例でn=288・k=8・bulk weight 6と境界の縮退を確認する。
5. 小さい例で低重み列挙・syndrome復号・failure条件を確認し、288qubitsのdistance 12の独立証明は別作業とする。
6. X/Z両sector、既存BP-OSD、JSON provenance、strict型検査、wheelと英日文書を受入に含める。
7. static code-capacityでdirect MCと条件付きMCMC/BARの小規模照合を行う。
8. factoryとdecoderの受入後にクラスタpilotへ追加し、標本長やcohortを固定して本計測に進む。

MCMCのfailure判定は全logical bitの残余を用い、「全体で1個以上失敗」と「1logicalあたり」を混同しない。
一般に `P_any/k` を1logicalあたりの失敗確率とみなせないため、必要なら各logicalのindicatorを別に測る。
調査時点では未実装だったが、追加依頼により `make_tile_code` とBP-OSDの受入を実装した。
6×6の72 qubits・8 logical、12×12の288・8、最小3×3の13・3と距離2を確認した。
代表288qubitsの距離12は独立証明していない。
API、実行例、クラスタsmokeの検証結果は [実装・投入報告](tile_cluster_report_2026-10-17_ja.md) に記録する。

## 回路対応の境界

static tile codeだけからsyndrome抽出回路・gate順序・hook error・測定round数は決まらない。
回路noiseを評価するには、具体的なStim回路とdetector/observable定義を別に受け入れる。
BP-OSDを用いるDEM decodingと、PyMatching向けgraphlike DEMの制約も区別する。
2026年のdirectional tile研究はiSWAPを用いる動的な測定構成であり、今回指定された元のtile factoryとは別の対応範囲である。
出典：[Nearest-neighbour gates are all you need, arXiv:2606.19482](https://arxiv.org/abs/2606.19482)。

## 次の実装単位

先に小仕様・受入を固めたtile factory＋既存BP-OSD接続を実装し、クラスタ計測driverとは独立して検証する。
クラスタ計測の設計は [混合・被覆校正設計](calibration_cluster_design_2026-10-17_ja.md) にまとめた。
本調査の初稿ではtile行列の生成、decoder動作確認、距離検証、クラスタ実測は未実施だった。
続く実装ではstatic factory、X/ZのBP-OSD、最小例の全列挙、tile72/288のクラスタsmokeを確認し、tileの長traceによる本校正は後続段階として残す。
