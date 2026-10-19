# tile72 depolarizing・p*=.01の低ノイズ比較

固定BP-OSD priorで実行した全352設定・各192 seed・計67,584行を保存済みWSS参照と比較した。
最終比較job265299はF/exit0/run_count1・30分40秒で終了し、正式sealと14ファイル86,595,446 bytesの回収を完了した。
別の標準ライブラリだけの再集計で全設定の10,208 scalarを照合し、最大絶対差は2.18×10^-16未満であった。
この照合は保存行の算術に関するもので、新たなdecoder実行・BAR・bootstrap・raw trace検証ではない。

WSS参照の99.9%区間は[0.0019476637418754938, 0.0019557995175693153]である。
各MC重量層のClopper–Pearson区間をBonferroniで合成し、未計測重量の確率質量上限を加えた区間であり、厳密な真値ではない。
部分和0.0019517234202748154を完全な点referenceとして扱わない。
以下のbias・RMSE範囲は参照確率がこの区間内を動くときの経験的範囲で、母RMSEの信頼区間ではない。

8 chain・burn-in 6,000・保存長12,000・fine ladderを固定した比較を示す。
表中の被覆は「BAR区間がWSS区間全体を含むseed数／WSS区間と交差するseed数」であり、どちらも分母は192である。

| kernel | 初期化 | 相対bias範囲 | 相対RMSE範囲 | block1024 被覆 | cross-chain 被覆 |
|---|---|---:|---:|---:|---:|
| ZH | logical_basis | +0.082〜+0.500% | 3.087〜3.139% | 168 / 171 | 166 / 171 |
| ZH | logical_combination | −0.385〜+0.031% | 2.663〜2.682% | 180 / 183 | 174 / 182 |
| ZHS | logical_basis | −0.371〜+0.046% | 2.828〜2.843% | 180 / 183 | 177 / 182 |
| ZHS | logical_combination | −0.146〜+0.271% | 2.867〜2.889% | 179 / 184 | 177 / 179 |

この16設定では点推定と区間を全192 seedで取得したが、全設定の全192 seedにhigh-Rhat・low-ESSの警告が残り、診断未定義は0であった。
警告の有無と被覆・経験的RMSEを混同せず、名目95%被覆や収束を保証しない。
ZH・logical_basisのblock32では全体包含134/192・交差145/192、block128では155/192・165/192であり、誤差評価法による差も残る。
この固定sliceでblockを長くすることやSを加えることが全符号・全領域で改善するとは結論しない。
[trace長比較図](../figures_low_case2_target0_v1/caption_ja.md)では、同じ8 chain・burn6,000・fine ladder・cross-chain条件で保存長600・6,000・12,000のRMSE範囲と参照区間包含・交差を示す。
同じchainの窓を比較した図であり、点間の差の独立な有意性検定や設定推奨を与えない。
低ノイズ12条件のうち正式比較が完了したのはこの1条件であり、独立計時と最終推奨設定は未確定である。

全設定は`all_settings.csv`、上記の固定sliceは`fixed_long_slice.csv`、入力hashと数値照合結果は`review.json`に保存した。
再現はPython 3.11で`docs/wp/data_tile_validation_2026-10-17/review_low_final_case2_target0_v1.py`を実行する。
出力先は既存結果を上書きしないため、再実行時は別の空の出力先を指定するようscriptの`OUT`を変更し、その変更を記録する。
元reportのhashは`af5a324a8aedbdf5d38f56f8f58b5a6ba55311cacf0d81d718d6ac8fb131fa8f`、算術照合JSONのhashは`cbf23d260f590d63f4eaf78119a347f376590e5ffc34819783b77390d9bb47fa`である。
