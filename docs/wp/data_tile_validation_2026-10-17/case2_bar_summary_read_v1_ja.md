# tile72 depolarizing：BAR保存summaryの暫定読取

主case2、物理誤り率・固定decoder priorともに0.03の保存summaryを確認した。
予定352設定が重複・欠落なく存在し、各設定の分母192、記録上768群・67,584行が一致した。
正式回収担当の完了通知後に読み、保存されたPBS F・exit 0、manifest・analysis context・referenceのhash結合、被覆率とWilson区間、bias/RMSEのreference範囲の算術を照合した。
これはsummaryから可能な検査であり、raw rowsは未回収で再集計しておらず、全analysis archiveの検証、full trace科学監査も未実施である。

全352設定で区間未取得0、記録された失敗0、点推定192/192だった。
診断flagは設定ごとに186〜192/192、high R-hatは126〜192/192、low ESSは170〜192/192である。
診断未定義は0〜164/192で、設定×seed行の延べ10,935/67,584件だった。
同じtraceを再利用するため、この延べ件数は独立例の件数ではない。

以下は事前に固定したsamples=12,000、burn-in=6,000、8 chains、fine ladderに該当する全16設定であり、結果による選別をしていない。
pointは有限MC reference点を含む件数、entireはreferenceの99.9%区間全体を含む件数、possibleはその区間と交差する件数で、いずれも分母192である。
bias範囲・RMSE範囲の単位はいずれも10⁻⁴であり、reference区間内で真値を動かした範囲を示す。
これらはbias/RMSE自体の信頼区間ではない。

| Kernel | 初期化 | 誤差法 | point /192 | entire /192 | possible /192 | bias範囲 ×10⁻⁴ | RMSE範囲 ×10⁻⁴ |
|---|---|---|---:|---:|---:|---:|---:|
| ZH | rejection | block 32 | 166 | 144 | 182 | -2.630〜1.858 | 5.730〜6.304 |
| ZH | rejection | block 128 | 178 | 164 | 187 | -2.630〜1.858 | 5.730〜6.304 |
| ZH | rejection | block 1024 | 180 | 168 | 187 | -2.630〜1.858 | 5.730〜6.304 |
| ZH | rejection | cross_chain | 177 | 166 | 186 | -2.630〜1.858 | 5.730〜6.304 |
| ZH | logical | block 32 | 166 | 148 | 177 | -2.620〜1.868 | 5.741〜6.311 |
| ZH | logical | block 128 | 175 | 162 | 187 | -2.620〜1.868 | 5.741〜6.311 |
| ZH | logical | block 1024 | 176 | 165 | 187 | -2.620〜1.868 | 5.741〜6.311 |
| ZH | logical | cross_chain | 177 | 161 | 184 | -2.620〜1.868 | 5.741〜6.311 |
| ZHS | rejection | block 32 | 153 | 124 | 175 | -2.824〜1.664 | 6.708〜7.278 |
| ZHS | rejection | block 128 | 174 | 152 | 186 | -2.824〜1.664 | 6.708〜7.278 |
| ZHS | rejection | block 1024 | 178 | 160 | 188 | -2.824〜1.664 | 6.708〜7.278 |
| ZHS | rejection | cross_chain | 172 | 156 | 183 | -2.824〜1.664 | 6.708〜7.278 |
| ZHS | logical | block 32 | 174 | 150 | 184 | -2.481〜2.007 | 5.342〜5.890 |
| ZHS | logical | block 128 | 185 | 172 | 190 | -2.481〜2.007 | 5.342〜5.890 |
| ZHS | logical | block 1024 | 186 | 176 | 192 | -2.481〜2.007 | 5.342〜5.890 |
| ZHS | logical | cross_chain | 178 | 167 | 188 | -2.481〜2.007 | 5.342〜5.890 |

この16設定の診断未定義は全て0/192だが、診断flagは多く残る。
下表は各kernel×初期化の4誤差法で共通する件数であり、未定義がないことを混合良好とは解釈しない。

| Kernel | 初期化 | flag /192 | high R-hat /192 | low ESS /192 |
|---|---|---:|---:|---:|
| ZH | rejection | 191 | 138 | 190 |
| ZH | logical | 190 | 132 | 190 |
| ZHS | rejection | 192 | 155 | 192 |
| ZHS | logical | 192 | 157 | 192 |

点推定のbias/RMSEは各kernel×初期化の4誤差法間で同一である。
block 1024とcross_chainのpoint被覆は172〜186/192（89.58〜96.88%）であり、短いblockのpoint被覆は153〜185/192だった。
一部のpoint被覆が95%を超えても、設定ごとの診断flagsと有限referenceの不確かさを残し、名目95%被覆の保証や推奨設定の確定として扱わない。

独立MC referenceは189,804/6,291,456 = 0.030168533325、99.9%区間は[0.029944944656, 0.030393739147]である。
全352設定の機械読取原本は[production_bar_summary-2.json](production_bar_summary-2.json)、照合証拠と丸め前の16設定は[case2_bar_summary_read_v1.json](case2_bar_summary_read_v1.json)に残す。
