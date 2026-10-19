# tile72 depolarizing・p*=.001の低ノイズ比較

目標priorへ固定したBP-OSDをladder全体で用いた全352設定・各192 seed・67,584行を、同じdecoder条件のWSS参照と比較した。
最終比較265315はF/exit0/run_count1・47分24秒で終了し、正式sealと14ファイル127,333,574 bytesの回収を完了した。
別の標準ライブラリによる集計で全設定の10,208 scalarを照合し、最大絶対差は2.141×10^-16未満であった。
終了前に作成した診断件数CSVとも、全352設定のflag・undefined・high R-hat・low ESS・区間未取得の1,760項目が一致した。
これは保存行の算術照合であり、新たな復号・BAR・bootstrap・raw trace検証ではない。

WSS参照の99.9%区間は[1.2363283244099694×10^-5, 1.236433253008209×10^-5]である。
層別Clopper–Pearson区間をBonferroniで合成し、未計測重量の確率質量上限8.042060035047471×10^-17を加えた区間で、厳密な真値ではない。
部分和1.2363806643416953×10^-5を完全な点referenceとして扱わない。
以下のbias・RMSE範囲は参照確率がこの区間内を動くときの経験的範囲であり、母RMSEの信頼区間ではない。

8 chain・burn-in 6,000・保存長12,000・fine ladderを固定した比較を示す。
被覆欄は「BAR区間がWSS区間全体を含むseed数／WSS区間と交差するseed数」で、どちらも分母は192である。

| kernel | 初期化 | 相対bias範囲 | 相対RMSE範囲 | block1024 被覆 | cross-chain 被覆 | 診断未定義seed |
|---|---|---:|---:|---:|---:|---:|
| ZH | logical_basis | +0.241〜+0.250% | 4.393〜4.394% | 174 / 174 | 174 / 174 | 192 / 192 |
| ZH | logical_combination | −0.255〜−0.246% | 4.336〜4.336% | 173 / 173 | 179 / 179 | 192 / 192 |
| ZHS | logical_basis | −0.0109〜−0.0024% | 4.857〜4.857% | 173 / 173 | 181 / 181 | 192 / 192 |
| ZHS | logical_combination | +0.0227〜+0.0312% | 4.493〜4.494% | 174 / 174 | 178 / 178 | 192 / 192 |

全352設定で点推定と区間を全192 seedで取得し、失敗task・区間未取得は0だった。
一方、全352設定で全192 seedにhigh-Rhat・low-ESSの集約flagが残り、未定義診断を含むseedは190〜192だった。
上表の固定sliceでは、全192 seedに未定義診断が含まれた。
これは観測量・rung等を集約したseed単位のflagであり、各chainの全診断が未定義という意味ではない。
診断未定義・警告を分母から除かず、区間取得と混合確認を区別する。

ZH・logical_basisのblock32では全体包含・交差とも121/192、block128では150/192、block1024とcross-chainでは174/192であり、誤差評価法による差が残る。
block1024・cross-chainの経験的被覆が高くても、名目95%被覆・収束・低ノイズ全域での精度は保証しない。
Sを加える設定が、この固定sliceで一様にRMSEや被覆を改善したとはいえない。
[trace長比較図](../figures_low_case2_target2_v1/caption_ja.md)では、同じ8 chain・burn6,000・fine・cross-chainで保存長600・6,000・12,000を比較した。
相対RMSEは約15.40〜18.00%から約5.98〜6.78%、約4.34〜4.86%へ下がったが、全設定の全seedに診断flagと未定義診断が残った。
同じchainの保存窓の比較であり、独立な差の有意性検定ではない。
p*=.01・.003との比較では目標固定decoder priorも異なり、同じfailure集合のままpだけを変えた比較ではない。
低ノイズ正式比較は12条件中3条件まで完了し、独立計時と最終推奨設定は未確定である。

全設定は`all_settings.csv`、固定sliceは`fixed_long_slice.csv`、入力hashと照合結果は`review.json`に保存した。
再現scriptは`../review_low_final_case2_target2_v1.py`で、Python 3.11を用いる。
既存出力を上書きしないため、再実行は別の空の`OUT`へ変更し、その差分を保存する。
元report SHAは`14f6fd9c4b9319c0c372b615d0797b78dc5cf74487f6490e08a80229e5f1d2ab`、算術照合JSON SHAは`e3be5afb78dac787a1b4e998f6cc5c51f77b5623e29f5e70be72980186928c11`である。
回収記録SHAは`4b9f4e5457298043061604ef36f5aa16691ad4bccee392dff6b1437bd53747b5`で、回収したreportを全raw trace archiveとは扱わない。
