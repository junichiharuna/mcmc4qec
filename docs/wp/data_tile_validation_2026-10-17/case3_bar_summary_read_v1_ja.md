# tile288 depolarizing：BAR保存summaryの暫定読取

主case3、物理誤り率・固定decoder priorともに0.05の保存summaryを確認した。
予定352設定が重複・欠落なく存在し、各設定の分母192、記録上768群・67,584行が一致した。
保存された完了証拠はPBS F・exit 0で、manifest・analysis context・referenceのhash結合、被覆率とWilson区間、bias/RMSEのreference範囲の算術を照合した。
これはsummaryから可能な検査であり、raw rowsの再集計、全analysis archiveの検証、full trace科学監査は未実施である。

全352設定で区間未取得0、記録された失敗0、点推定192/192だった。
全設定の全192 seedにflagがあり、high R-hatとlow ESSもそれぞれ192/192である。
診断未定義は設定ごとに0〜192件、設定×seed行の延べ19,162/67,584件で、同じtraceを再利用するため独立例の件数ではない。

以下は事前に固定したsamples=12,000、burn-in=6,000、8 chains、fine ladderに該当する全16設定であり、結果による選別をしていない。
pointは有限MC reference点を含む件数、entireはreferenceの99.9%区間全体を含む件数、possibleはその区間と交差する件数で、いずれも分母192である。
bias範囲の単位は10⁻⁵、RMSE範囲の単位は10⁻⁴であり、reference区間内で真値を動かした範囲を示す。
これらはbias/RMSE自体の信頼区間ではない。

| Kernel | 初期化 | 誤差法 | point /192 | entire /192 | possible /192 | bias範囲 ×10⁻⁵ | RMSE範囲 ×10⁻⁴ |
|---|---|---|---:|---:|---:|---:|---:|
| ZH | rejection | block 32 | 114 | 104 | 125 | -1.058〜3.443 | 2.124〜2.152 |
| ZH | rejection | block 128 | 160 | 147 | 164 | -1.058〜3.443 | 2.124〜2.152 |
| ZH | rejection | block 1024 | 177 | 174 | 179 | -1.058〜3.443 | 2.124〜2.152 |
| ZH | rejection | cross_chain | 178 | 174 | 180 | -1.058〜3.443 | 2.124〜2.152 |
| ZH | logical | block 32 | 97 | 85 | 115 | -2.286〜2.214 | 2.106〜2.118 |
| ZH | logical | block 128 | 149 | 137 | 160 | -2.286〜2.214 | 2.106〜2.118 |
| ZH | logical | block 1024 | 177 | 176 | 178 | -2.286〜2.214 | 2.106〜2.118 |
| ZH | logical | cross_chain | 177 | 174 | 182 | -2.286〜2.214 | 2.106〜2.118 |
| ZHS | rejection | block 32 | 102 | 92 | 115 | -2.738〜1.762 | 2.226〜2.243 |
| ZHS | rejection | block 128 | 143 | 138 | 149 | -2.738〜1.762 | 2.226〜2.243 |
| ZHS | rejection | block 1024 | 176 | 170 | 178 | -2.738〜1.762 | 2.226〜2.243 |
| ZHS | rejection | cross_chain | 175 | 173 | 179 | -2.738〜1.762 | 2.226〜2.243 |
| ZHS | logical | block 32 | 98 | 85 | 116 | 1.024〜5.524 | 2.240〜2.305 |
| ZHS | logical | block 128 | 146 | 138 | 155 | 1.024〜5.524 | 2.240〜2.305 |
| ZHS | logical | block 1024 | 176 | 173 | 180 | 1.024〜5.524 | 2.240〜2.305 |
| ZHS | logical | cross_chain | 177 | 175 | 183 | 1.024〜5.524 | 2.240〜2.305 |

この16設定でもflag・high R-hat・low ESSは全て192/192である。
診断未定義はZH/rejectionが3/192、ZH/logicalが0/192、ZHS/rejectionが1/192、ZHS/logicalが0/192で、各誤差法で同じだった。
点推定のbias/RMSEは各kernel×初期化の4誤差法間で同一である。
block 1024とcross_chainのpoint被覆は175〜178/192（91.15〜92.71%）であり、短いblockのpoint被覆は97〜160/192だった。
設定ごとの診断flagsと有限referenceの不確かさを残し、この結果を名目95%被覆の保証や推奨設定の確定として扱わない。

独立MC referenceは185,628/62,914,560 = 0.00295047760010、99.9%区間は[0.00292806236751, 0.00297306391663]である。
全352設定の機械読取原本は[production_bar_summary-3.json](production_bar_summary-3.json)、照合証拠と丸め前の16設定は[case3_bar_summary_read_v1.json](case3_bar_summary_read_v1.json)に残す。
