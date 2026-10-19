# tile288 bit-flip：BAR保存summaryの暫定読取

主case1、物理誤り率・固定decoder priorともに0.05の保存summaryを確認した。
予定352設定が重複・欠落なく存在し、各設定の分母192、記録上768群・67,584行が一致した。
正式回収担当の完了通知後に読み、保存されたPBS F・exit 0、manifest・analysis context・referenceのhash結合、被覆率とWilson区間、bias/RMSEのreference範囲の算術を照合した。
これはsummaryから可能な検査であり、raw rowsは未回収で再集計しておらず、全analysis archiveの検証、full trace科学監査も未実施である。

全352設定で区間未取得0、記録された失敗0、点推定192/192だった。
全設定の全192 seedにflagがあり、low ESSも192/192である。
high R-hatは設定ごとに181〜192/192、診断未定義は0〜9/192で、未定義は設定×seed行の延べ381/67,584件だった。
同じtraceを再利用するため、この延べ件数は独立例の件数ではない。

以下は事前に固定したsamples=12,000、burn-in=6,000、8 chains、fine ladderに該当する全16設定であり、結果による選別をしていない。
pointは有限MC reference点を含む件数、entireはreferenceの99.9%区間全体を含む件数、possibleはその区間と交差する件数で、いずれも分母192である。
bias範囲の単位は10⁻⁴、RMSE範囲の単位は10⁻³であり、reference区間内で真値を動かした範囲を示す。
これらはbias/RMSE自体の信頼区間ではない。

| Kernel | 初期化 | 誤差法 | point /192 | entire /192 | possible /192 | bias範囲 ×10⁻⁴ | RMSE範囲 ×10⁻³ |
|---|---|---|---:|---:|---:|---:|---:|
| ZH | rejection | block 32 | 124 | 106 | 138 | -0.938〜3.461 | 1.388〜1.431 |
| ZH | rejection | block 128 | 162 | 154 | 170 | -0.938〜3.461 | 1.388〜1.431 |
| ZH | rejection | block 1024 | 178 | 171 | 182 | -0.938〜3.461 | 1.388〜1.431 |
| ZH | rejection | cross_chain | 176 | 173 | 182 | -0.938〜3.461 | 1.388〜1.431 |
| ZH | logical | block 32 | 116 | 105 | 129 | -3.106〜1.293 | 1.465〜1.498 |
| ZH | logical | block 128 | 157 | 148 | 163 | -3.106〜1.293 | 1.465〜1.498 |
| ZH | logical | block 1024 | 169 | 165 | 183 | -3.106〜1.293 | 1.465〜1.498 |
| ZH | logical | cross_chain | 169 | 164 | 173 | -3.106〜1.293 | 1.465〜1.498 |
| ZHS | rejection | block 32 | 123 | 102 | 134 | -4.191〜0.208 | 1.430〜1.490 |
| ZHS | rejection | block 128 | 166 | 157 | 171 | -4.191〜0.208 | 1.430〜1.490 |
| ZHS | rejection | block 1024 | 180 | 178 | 181 | -4.191〜0.208 | 1.430〜1.490 |
| ZHS | rejection | cross_chain | 177 | 172 | 182 | -4.191〜0.208 | 1.430〜1.490 |
| ZHS | logical | block 32 | 114 | 96 | 126 | -0.974〜3.425 | 1.442〜1.482 |
| ZHS | logical | block 128 | 162 | 154 | 170 | -0.974〜3.425 | 1.442〜1.482 |
| ZHS | logical | block 1024 | 182 | 179 | 187 | -0.974〜3.425 | 1.442〜1.482 |
| ZHS | logical | cross_chain | 178 | 172 | 182 | -0.974〜3.425 | 1.442〜1.482 |

この16設定の診断未定義は全て0/192だが、flag・low ESSは全て192/192である。
high R-hatも全て192/192であり、未定義がないことを混合良好とは解釈しない。
点推定のbias/RMSEは各kernel×初期化の4誤差法間で同一である。
block 1024とcross_chainのpoint被覆は169〜182/192（88.02〜94.79%）であり、短いblockのpoint被覆は114〜166/192だった。
設定ごとの診断flagsと有限referenceの不確かさを残し、この結果を名目95%被覆の保証や推奨設定の確定として扱わない。

独立MC referenceは182,133/6,291,456 = 0.028949260712、99.9%区間は[0.028730117258, 0.029170025515]である。
全352設定の機械読取原本は[production_bar_summary-1.json](production_bar_summary-1.json)、照合証拠と丸め前の16設定は[case1_bar_summary_read_v1.json](case1_bar_summary_read_v1.json)に残す。
