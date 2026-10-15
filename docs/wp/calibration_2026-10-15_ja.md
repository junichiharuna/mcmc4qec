# 実符号のblock長一要因校正（2026-10-15）

## 目的と設定

dev5で残った短いtraceの区間校正に対し、toric d=3のblock長だけを変える小規模比較を行う。
事前計画は [plan_ja.md](data_calibration_2026-10-15/plan_ja.md)、再実行コマンドと生データは [データ一覧](data_calibration_2026-10-15/README.md) に保存した。
公開既定・sampling・BARの実装は変更せず、既存benchmarkのCSVへtargetのESSとsplit R-hatを追加した。

| 項目 | 固定値 |
| --- | --- |
| 符号・ノイズ・decoder | toric d=3、bit-flip、固定unweighted MWPM |
| ladder | 0.30 / 0.26 / 0.22 |
| anchor | exact、独立MCのanchor分散を含めない |
| sampling | 4 chain、各保存600、burn180、Z/H=0.7/0.3、k=2、lazy0.05 |
| 初期化 | 公開既定のfailure条件付き棄却初期化 |
| seed | 6100–6119、各群同じ20個 |
| 変える要因 | circular block長8 / 32 / 128 |
| 誤差評価 | block bootstrap100反復 |

保存状態配列を流用する代わりに同じseedで公開APIを再実行し、block変更によるsamplingへの影響がないことを受入テストとcohortの対応比較で確認する設計とした。
bootstrap child seedも群間で共通だが、block長によって乱数の消費が異なるため、bootstrap drawを一対一に同一視しない。
3群の点推定・重み・IAT・ESS・R-hat・独立MC出力の対応一致を集計scriptで検証し、全状態列の保存・比較とは区別する。
独立MCはtargetで各1200試行の補助比較であり、BARのanchorには使わない。

## 再現性と受入検査

測定sourceは `35ed7f38ecae9de0a728730034f5602a2cca7e1f`、package SHA-256は `c13661d4d5004f37abb981281e0c37be92271665c90450014d3b2ae89b509ae6` であり、後続の高速化等を統合したsourceの測定とは区別する。
Python3.11.9、NumPy2.4.6、SciPy1.17.1、PyMatching2.4.0を使い、環境・事前計画hash・benchmark hashを保存した。
全262144状態を新しく列挙し、failure数196608のchecked cacheを作成した。
cacheから得たtarget exactは0.602662564701594、条件付き重みは4.530131731513127、anchor exactは0.7076851364881606である。
受入テスト `tests/test_bar_block_control.py` は1 passed /2.04秒で、小問題の3種類のblock長についてrung metadata・pooled BAR点推定・診断の一致を確認した。
全source suiteは統合担当が別に実行し、本担当では未実施である。
標準ライブラリだけの `recompute.py` を実行し、全60行のcohort完全性・固定設定・cache digest・exact値・区間算術と、全20seedでの3群の点推定と記録した診断の厳密一致を確認した。

## 実測結果

全60区間が得られ、各区間のbootstrap100反復すべてが成功した。
以下のWilson区間は20seedの被覆割合に対する区間であり、論理誤り率のBAR区間とは別である。

| block長 | exact被覆 | 被覆のWilson区間 | 平均BAR区間幅 | 全rung最大IATに対するblock比の最小値 | 実行秒 |
| ---: | ---: | --- | ---: | ---: | ---: |
| 8 | 12/20 | [0.387, 0.781] | 0.049634 | 0.1255 | 110.09 |
| 32 | 16/20 | [0.584, 0.919] | 0.073329 | 0.5019 | 103.79 |
| 128 | 16/20 | [0.584, 0.919] | 0.076132 | 2.0076 | 98.06 |

各invocationは2分以内、3群の合計sampling・bootstrap時間は311.93秒で、事前の全列挙時間はこの合計に含めない。
点推定平均は全群共通の0.607516703404、exactとの差は+0.004854138702、seed間SDは0.031649903979、平均のSEは0.007077133678だった。
平均偏差は約0.69SEであり、このcohortだけで有限標本biasの有無を判定しない。
対応seedの区間幅差の平均±SEは32−8で+0.023695±0.001661、128−8で+0.026498±0.002633、128−32で+0.002803±0.002433だった。
block32と128はblock8で外れた同じ4seedを追加で含み、両者の被覆集合は同じだった。
幅を増やしてもこの有限cohortは16/20にとどまり、block調整のみで名目95%被覆を達成したとは扱わない。
補助独立MCの被覆は19/20で、BARとの区間非交差はblock8で3/20、block32・128で0/20だった。

各seedの全rung・全chainにわたる最大IATの中央値は37.73で、block8はその有限標本相関時間より短かった。
targetの4chain合計ESSの中央値は156.61、最小値は91.93で、保存総数2400とは大きく異なった。
target split R-hatの20seed最大値は1.07798だった。
target条件付き重みのseed平均はexactより+0.0225974大きく、これらの診断と推定誤差を別々に記録した。
block128は全seedで記録した最大IATの2倍を超えたが、それだけで区間が校正されたとはいえない。

## 限界

block長の変更はsampling軌道の混合を改善せず、有限相関を区間へどの程度反映するかだけを変える。
IAT・ESS・split R-hatは重みという一つの観測量の有限標本診断であり、全状態空間の混合・収束・既約性・正しさの証明ではない。
20seedの被覆数は不確かで、95%被覆や設定の一般的優劣を保証しない。
block128では600/128=4.6875 block相当しかなく、block近似と100 bootstrap反復の有限変動が残る。
exact anchorはanchorのMC誤差による被覆への寄与を除くための実験条件であり、実用上常に利用できる方法ではない。
このp=0.22はdev4で使った領域で、論文の主なp≤0.1領域や別の実符号・ノイズへの一般化は未実施である。
研究精度での混合と被覆の校正、十分に長いtraceと多数seedでの確認は未達として残し、公開のblock選択やchain数の既定を変更しない。
