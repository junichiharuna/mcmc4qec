# tile72 bit-flip：BAR保存summaryの暫定読取

主case0、物理誤り率・固定decoder priorともに0.03の保存summaryを確認した。
予定352設定が重複・欠落なく存在し、各設定の分母192、記録上768群・67,584行が一致した。
正式回収担当の完了通知後に読み、保存されたPBS F・exit 0、manifest・analysis context・referenceのhash結合、被覆率とWilson区間、bias/RMSEのreference範囲の算術を照合した。
これはsummaryから可能な検査であり、raw rowsは未回収で再集計しておらず、全analysis archiveの検証、full trace科学監査も未実施である。

全352設定で区間未取得0、記録された失敗0、点推定192/192だった。
診断flag・high R-hat・low ESSはいずれも設定ごとに0〜192/192である。
診断未定義は0〜1/192で、設定×seed行の延べ12/67,584件だった。
flagは延べ41,436/67,584件であり、同じtraceを再利用するため、この延べ件数は独立例の件数ではない。

以下は事前に固定したsamples=60,000、burn-in=6,000、16 chains、fine ladderに該当する全16設定であり、結果による選別をしていない。
case0の最大窓・chain数は他3caseの12,000・8と異なる。
pointは有限MC reference点を含む件数、entireはreferenceの99.9%区間全体を含む件数、possibleはその区間と交差する件数で、いずれも分母192である。
bias範囲・RMSE範囲の単位はいずれも10⁻⁴であり、reference区間内で真値を動かした範囲を示す。
これらはbias/RMSE自体の信頼区間ではない。

| Kernel | 初期化 | 誤差法 | point /192 | entire /192 | possible /192 | bias範囲 ×10⁻⁴ | RMSE範囲 ×10⁻⁴ |
|---|---|---|---:|---:|---:|---:|---:|
| ZH | rejection | block 32 | 183 | 132 | 190 | -2.927〜2.393 | 3.451〜4.525 |
| ZH | rejection | block 128 | 185 | 144 | 190 | -2.927〜2.393 | 3.451〜4.525 |
| ZH | rejection | block 1024 | 185 | 148 | 190 | -2.927〜2.393 | 3.451〜4.525 |
| ZH | rejection | cross_chain | 186 | 148 | 190 | -2.927〜2.393 | 3.451〜4.525 |
| ZH | logical | block 32 | 180 | 132 | 190 | -2.865〜2.456 | 3.548〜4.560 |
| ZH | logical | block 128 | 183 | 141 | 190 | -2.865〜2.456 | 3.548〜4.560 |
| ZH | logical | block 1024 | 184 | 145 | 190 | -2.865〜2.456 | 3.548〜4.560 |
| ZH | logical | cross_chain | 181 | 148 | 190 | -2.865〜2.456 | 3.548〜4.560 |
| ZHS | rejection | block 32 | 182 | 134 | 188 | -3.014〜2.306 | 3.526〜4.639 |
| ZHS | rejection | block 128 | 184 | 146 | 189 | -3.014〜2.306 | 3.526〜4.639 |
| ZHS | rejection | block 1024 | 185 | 149 | 190 | -3.014〜2.306 | 3.526〜4.639 |
| ZHS | rejection | cross_chain | 184 | 150 | 188 | -3.014〜2.306 | 3.526〜4.639 |
| ZHS | logical | block 32 | 183 | 132 | 191 | -2.840〜2.480 | 3.530〜4.531 |
| ZHS | logical | block 128 | 184 | 142 | 191 | -2.840〜2.480 | 3.530〜4.531 |
| ZHS | logical | block 1024 | 184 | 146 | 191 | -2.840〜2.480 | 3.530〜4.531 |
| ZHS | logical | cross_chain | 185 | 144 | 191 | -2.840〜2.480 | 3.530〜4.531 |

この16設定の診断未定義・flag・high R-hat・low ESSは全て0/192だった。
診断flagがないことは、収束・既約性や推定の正しさの証明ではない。
点推定のbias/RMSEは各kernel×初期化の4誤差法間で同一である。
point被覆は180〜186/192（93.75〜96.88%）だが、entireは132〜150/192、possibleは188〜191/192で、有限referenceの幅によって被覆の読取りが変わる。
point被覆が95%近傍であっても、これを真値に対する名目95%被覆の保証や推奨設定の確定として扱わない。

独立MC referenceは270,328/6,291,456 = 0.042967478434、99.9%区間は[0.042702238639, 0.043234291329]である。
全352設定の機械読取原本は[production_bar_summary-0.json](production_bar_summary-0.json)、照合証拠と丸め前の16設定は[case0_bar_summary_read_v1.json](case0_bar_summary_read_v1.json)に残す。
