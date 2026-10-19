# tile72 depolarizing・p*=.003の低ノイズ比較

目標priorへ固定したBP-OSDをladder全体で用いた全352設定・各192 seed・67,584行を、同じdecoder条件のWSS参照と比較した。
最終比較265308はF/exit0/run_count1・42分19秒で終了し、正式sealと14ファイル110,996,144 bytesの回収を完了した。
別の標準ライブラリによる集計で全設定の10,208 scalarを照合し、最大絶対差は2.12×10^-16未満であった。
これは保存行の算術照合であり、新たな復号・BAR・bootstrap・raw trace検証ではない。

WSS参照の99.9%区間は[0.00012577791425118524, 0.0001258614602556782]である。
層別Clopper–Pearson区間をBonferroniで合成し、未計測重量の確率質量上限4.52645895147584×10^-16を加えた区間で、厳密な真値ではない。
部分和0.00012581958790074308を完全な点referenceとして扱わない。
以下のbias・RMSE範囲は参照確率がこの区間内を動くときの経験的範囲であり、母RMSEの信頼区間ではない。

8 chain・burn-in 6,000・保存長12,000・fine ladderを固定した比較を示す。
被覆欄は「BAR区間がWSS区間全体を含むseed数／WSS区間と交差するseed数」で、どちらも分母は192である。

| kernel | 初期化 | 相対bias範囲 | 相対RMSE範囲 | block1024 被覆 | cross-chain 被覆 | 診断未定義seed |
|---|---|---:|---:|---:|---:|---:|
| ZH | logical_basis | +0.325〜+0.392% | 3.464〜3.474% | 180 / 181 | 179 / 179 | 145 / 192 |
| ZH | logical_combination | +0.143〜+0.210% | 3.808〜3.814% | 172 / 175 | 176 / 176 | 139 / 192 |
| ZHS | logical_basis | −0.004〜+0.062% | 4.019〜4.022% | 172 / 172 | 169 / 170 | 152 / 192 |
| ZHS | logical_combination | +0.028〜+0.095% | 3.995〜3.999% | 173 / 174 | 173 / 177 | 151 / 192 |

この固定sliceの16設定では、点推定と区間を全192 seedで取得した。
一方で全設定の全192 seedにhigh-Rhat・low-ESSの集約flagが残り、診断未定義も139〜152 seedだった。
これらは観測量・rung等を集約したseed単位のflagであり、各chainの全診断が未定義という意味ではない。
診断未定義・警告を分母から除かず、区間取得と混合確認を区別する。

ZH・logical_basisのblock32では全体包含134/192・交差137/192、block128では163/192・163/192であり、誤差評価法による差が残る。
block1024やcross-chainの値が高くても、名目95%被覆・収束・低ノイズ全域での精度は保証しない。
Sを加える設定が、この固定sliceで一様にRMSEや被覆を改善したとはいえない。
[trace長比較図](../figures_low_case2_target1_v1/caption_ja.md)には同じ8 chain・burn6,000・fine・cross-chainで保存長600・6,000・12,000を比較し、RMSE低下と一様には改善しない参照区間包含・交差を示した。
同じchainの保存窓の比較であり、独立な差の有意性検定ではない。
p*=.01との比較では物理誤り率だけでなく目標固定decoder priorも異なり、同じfailure集合のままpだけを変えた比較ではない。
低ノイズ正式比較は12条件中2条件まで完了し、独立計時と最終推奨設定は未確定である。

全設定は`all_settings.csv`、固定sliceは`fixed_long_slice.csv`、入力hashと照合結果は`review.json`に保存した。
再現scriptは`../review_low_final_case2_target1_v1.py`で、Python 3.11を用いる。
既存出力を上書きしないため、再実行は別の空の`OUT`へ変更し、その差分を保存する。
元report SHAは`20a0b9feda08bc488454ecc03af6b38a554fcf2fc30f433632a4aa4f5b445685`、算術照合JSON SHAは`21b4c92d53c7598e9feaa0a81ad18190aefeff573a32d9804824fa971c51257a`である。
回収記録SHAは`9e93f1b3895f9cfba293e202861e4be2c51a988841c8122846093ac5daedb704`で、回収したreportを全raw trace archiveとは扱わない。
