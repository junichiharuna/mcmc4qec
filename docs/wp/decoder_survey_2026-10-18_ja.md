# 基本decoderの調査と追加順

2026-10-18のユーザー依頼に基づき、tileに限定せずsurface・toric・Steane・HGP・BB・tileを対象に調べた。
既存のクラスタ校正は継続し、公開decoder API・稼働中bundle・計測条件は変更していない。
この調査は文献・導入済み実装・小規模probeを区別し、速度や論理エラー率の順位を未測定のまま断定しない。

## 基本候補

| decoder | 主な対象 | 方法と位置付け | 本リポジトリでの扱い |
|---|---|---|---|
| MWPM | surface、toric、graphlikeな誤り機構 | 検出点を重み付きmatchingで結ぶ基準手法 | PyMatching経由で既存対応 |
| BP＋OSD | 一般のbinary parity-check matrix、CSS QLDPC | BPの信頼度を用いた大域的な後処理 | 既存対応、比較基準 |
| Union-Find＋peeling | surface、toricなど点状syndromeを持つ符号 | syndrome clusterの成長・結合と局所復号 | 新規対応候補、graphlike制約を入口で検査 |
| BP＋LSD | 一般のCSS QLDPC、HGP、BB、tileなど | BPの信頼度で局所clusterを作り、局所的な線形系を解く | 最初の追加候補 |
| BeliefFind | 一般CSSではinversion版、graphlikeではpeeling版も候補 | BPが解けなかった場合にBP情報でUF clusterを成長させる | BP-LSDに続く追加候補 |
| 単独BP | 一般のbinary parity-check matrix | sum-product/min-sumによる反復、比較用の軽量baseline | 復号不能を表す契約を先に設計 |

MWPMの直接check-matrix接続では各列が1または2個の検出点を結ぶことが前提であり、任意のQLDPC行列をそのままmatching graphに変換できるわけではない。[PyMatching一次資料](https://pymatching.readthedocs.io/en/stable/)
BP-OSDは既存の量子LDPC比較基準として維持する。[BP-OSD論文](https://arxiv.org/abs/2005.07016)
通常のUFのほぼ線形時間という結果はtopological/graphlikeな設定のもので、一般LDPC用cluster-inversionに同じ計算量保証を付けない。[Delfosse–Nickerson](https://arxiv.org/abs/1709.06218)
一般LDPC向けUFは局所clusterの妥当性と線形系の解法を拡張した別の適用範囲を持つ。[一般化UF論文](https://arxiv.org/abs/2103.08049)
LSDは任意の量子LDPCを対象とする信頼度誘導の局所inversion法であり、OSDとの差は復号を局所clusterに分ける点にある。[LSD論文](https://arxiv.org/abs/2406.18655)
BeliefFindはBP後にUFを用いる構成で、`ldpc`はpeeling版とinversion版を区別して提供する。[実装の一次資料](https://software.roffe.eu/ldpc/quantum_decoder.html)
LSD論文の並列化可能性と現在のPython呼出しの並列動作は別であり、公式repositoryは現在のLSD実装がserialであると明記している。[公式repository](https://github.com/quantumgizmos/ldpc)

## 導入済みldpc 2.4.1のAPI

`BpLsdDecoder`、`BeliefFindDecoder`、`UnionFindDecoder`、`BpDecoder`、`BpOsdDecoder`は現在のoptional環境に存在し、これらの追加のための新しい外部ライブラリは不要である。
これはこの環境で確認した版の事実であり、`ldpc>=2.4,<3`の全版を受入済みとは扱わない。
BP-LSDはまず`lsd_method="lsd_0"`・`lsd_order=0`・`bits_per_step=1`を明示して接続し、高orderは局所解法の有効範囲・費用とともに別途検査する。
BPのschedule・最大反復数・min-sum係数・thread数も省略せず記録する。[BP-LSD API](https://software.roffe.eu/ldpc/ldpc/bplsd_decoder.html)
BeliefFindには`uf_method="inversion"`または`"peeling"`を明示する。
inversion版は一般parity-check matrixに使え、peeling版はpoint-like syndrome向けである。[BeliefFind API](https://software.roffe.eu/ldpc/ldpc/belief_find_decoder.html)

単独`UnionFindDecoder`は公式API文書と導入済みdocstringで`uf_method`をboolと記しているが、Windows 2.4.1の実際のconstructorはstrを要求し、True/Falseと引数省略がTypeErrorになった。[単独UF API](https://software.roffe.eu/ldpc/ldpc/union_find_decoder.html)
導入済み`.pyx`ではconstructor引数の型がstr、内部`.pxd`では保存先がC++ boolで、decode時にはこのboolでmatrix/peelingを分岐している。
非空文字列でinversion・空文字列でpeelingとなる回避方法を今回のprobeに限って検査したが、利用者向け公開APIとして推奨しない。
単独UFのfactoryを追加する前に、対応版の境界・回避方法の版限定検査または上流修正版を確定する。
この調査では依存ライブラリ本体を変更・更新していない。

## 小規模probeで確認した事実

`benchmarks/decoder_survey_probe.py` は7符号それぞれで、zero・2個のsingle error・p=.03から8個・p=.1から8個の計19状態を事前固定して使う。
bit-flipのX sectorのみで、全decoderのprior=.03、BP最大100反復、min-sum係数1、parallel schedule、1 threadを固定した。
OSD/LSDはorder0であり、本校正のOSD-CS order10と同一設定ではない。
同じobjectで再呼出し、呼出し順の反転、objectの新規構築を検査し、生状態・syndrome・補正列・環境・native binary hashを保存する。
19状態は混合目的のfixtureであり、失敗数をそのまま特定pの論理エラー率推定や性能順位にしない。

WindowsとLinuxで各37条件のAPI呼出しが完了した。
各環境内の上記有限probeでは、再呼出し・逆順・新規objectの補正列不一致はなかった。
BP-LSD、BeliefFind-inversion、互換文字列を使う単独UFでは、今回の入力に対するsyndrome不一致はなかった。
BP-LSDとBeliefFindは7符号、UF-peelingはtoric3/surface3のみで試した。
Hamming-HGPの列重みは最大4、BB72は3、tile72/288は最大3であり、これらに通常のpeeling型を適用する候補とはしない。

単独BPではtoric・Steane・HGP・BB・tileのprobeにsyndrome不一致があり、Steaneの1状態、tile72の2状態、tile288の4状態は論理bitだけを比較するとその不一致を見落とした。
これは現在の`DecoderAdapter`が補正をlogical mapへ写し、標準`Problem.is_faulty`がlogical mismatchだけを見るという契約に直結する問題である。
生のBP correctionをそのまま既存factoryと同じ形で包む実装は先に進めず、未復号syndromeもfailureに含める方法、または別名で明示した決定的fallbackを仕様化する。

同じsource・package version・入力でも、Windows/Linux間で補正列やlogical予測が異なる条件があった。
BP-LSDのtoric3では19入力中2入力のfailure labelが変わり、BeliefFind-inversionのHGPでは1入力のfailure labelが変わった。
補正列の違いだけではlogical failureの違いとは限らないため、両方を `comparison.json` に分けて記録した。
この結果から全入力に対する決定性、OS間同一性、低p精度や区間被覆を主張しない。
MCMC/BARの比較時は各decoderのbinary・実行環境・設定を固定し、各decoder自身の独立referenceを使う。

原データと再計算結果は [data_decoder_survey_2026-10-18](data_decoder_survey_2026-10-18/) にある。
`windows_artifacts.tar.gz` / `linux_artifacts.tar.gz` にraw配列と実行sourceを含め、`compare_probe.py` がarchive内hash・syndrome・failure count・同一入力を検査する。
最初に文書どおりのboolで失敗した記録とそのsourceも別に保存した。

## 追加実装の順序と受入

1. `bplsd_decoder`とX/Z sector合成を、既存の固定prior・明示correction出力・metadata契約に合わせて追加する。
2. `belief_find_decoder`をinversion既定で追加し、peeling指定時には列重みなどの適用条件を検査する。
3. 単独`union_find_decoder`をsurface/toricの比較用に追加し、上記2.4.1 binding問題への対応を公開引数から隠さず版情報とともに記録する。
4. 単独BPの復号不能契約を整え、必要なら小符号用のexact logical-coset MLを校正用baselineとして別途検討する。

public factoryはcorrectionの長さだけから意味を推測せず、H c=sを確認する契約を設計する。
不正補正を黙ってlogical成功と扱わず、fallbackを使う場合はdecoder名・failure集合が変わることを明示する。
depolarizingは物理I/X/Y/Zの相関を維持し、独立X/Z sector復号の近似とsector prior=2p/3を記録する。
受入は小符号全列挙、syndrome一致、X/Z mapping、同じsyndromeの反復・逆順・新規object、設定metadata、optional依存なしの動作を含める。
まずsurface/toricでMWPM対UF、Steane/HGP/BBでBP-OSD対BP-LSD対BeliefFindを比較する。
時間比較はdecode単体とMCMC全体を分け、MCMCが訪れるsyndrome分布・cache hit・混合時間も測る。
decoderの単体高速化だけからBARのtime-to-accuracy改善を推定しない。
本調査時点では新しいpublic decoder factoryは未実装である。
