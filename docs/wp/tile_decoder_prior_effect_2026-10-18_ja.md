# Tile decoder prior変更のpaired pilot解析

## 小仕様

完了したpilotの全96task・3072物理誤りを再利用し、符号・noise・physical p・alternative priorの全64比較を報告する。
これは追加のdecoder実行や新しいMC標本ではなく、固定済み同一誤り上のpaired集計である。
baseline失敗数A、alternative失敗数B、判定不一致数D、標本数Nから、成功→失敗は(D+B-A)/2、失敗→成功は(D+A-B)/2、両方失敗は(A+B-D)/2、両方成功はN-(A+B+D)/2として復元する。
整数性、非負性、全セル合計、logical prediction不一致数がfailure判定不一致数以上であることを検査する。
失敗率差(B-A)/Nと、判定境界が変わった誤りの質量D/Nを別々に報告する。
paired差の標準誤差はD_i∈{-1,0,1}の不偏標本分散から求め、独立な2つのbinomial標本の差として計算しない。
同じ状態について複数priorを比べた比較間の独立性は仮定しない。
全64比較の成功→失敗、失敗→成功、不一致の計192個の周辺binomial確率に対し、Clopper–Pearson区間へBonferroniのalpha/192を割り当てる。
成功→失敗と失敗→成功の区間差から失敗率差の範囲を作る。
このfamilyは記録された全比較で固定し、表に例を抜き出してもfamilyを縮めない。
95%は、この固定family内でiid物理誤りと固定decoderを仮定した同時信頼水準であり、BAR区間の被覆や任意prior・任意環境での再現性を保証しない。
不一致0件でも、未観測状態を含むfailure集合の同一性とは扱わない。
入力manifest・生pilot summary・既存compact countsとproducer sourceのhashを照合してから派生JSONを保存する。
受入はpairedセル復元、周辺数の不整合拒否、差の標準誤差、0件時の正の上限、familyの増加による保守化、有限multinomial列挙を用いる。
小仕様・未実装時の受入失敗・実装の順で進め、関連18件がWindowsで1.96秒で通った。

## 全pilot記録から得た結果

元の全96taskとcompact countsのhash・集計値を照合し、64比較を `data_tile_validation_2026-10-17/pilot_prior_effects.json` に保存した。
以下はphysical p=0.1で、physical decoder priorを0.1から0.0001へ変更した場合の同一192誤りである。
depolarizingの各sector priorはphysical priorの2/3である。
差はalternative失敗率−baseline失敗率とし、百分率点で表示する。

| 符号・noise | 成功→失敗 | 失敗→成功 | 判定が変化 | 失敗率差 | 失敗率差の同時信頼範囲 |
|---|---:|---:|---:|---:|---:|
| tile72 bit-flip | 0 | 0 | 0/192 | 0.00 | [-4.55, 4.55] |
| tile72 depolarizing | 1 | 0 | 1/192 | +0.52 | [-4.55, 5.81] |
| tile288 bit-flip | 16 | 7 | 23/192（11.98%） | +4.69 | [-8.47, 17.35] |
| tile288 depolarizing | 7 | 8 | 15/192（7.81%） | -0.52 | [-11.52, 10.53] |

表の信頼範囲は、表に抜粋した4比較だけでなく全64比較・192周辺区間をfamilyとする95% Bonferroni範囲で、有限pilotでは広い。
tile288 bit-flipのpaired差の標準誤差は2.48百分率点、depolarizingは2.02百分率点だった。
depolarizingの失敗総数55→54だけを見ると差は小さいが、15状態で判定が入れ替わっており、失敗集合の変化は相殺されている。
logical predictionの不一致数は、それぞれ106/192と39/192で、成功・失敗が入れ替わる数とは別である。

同じphysical p=0.1でpriorを0.1から0.03へ変えた比較では、tile72の両noiseとtile288 bit-flipは判定不一致0/192、tile288 depolarizingは1/192だった。
0/192の同時信頼上限は4.55%であり、未観測状態まで失敗集合が同一という根拠にはしない。
これらは各physical pにおけるpairedなdecoder比較で、可変priorのBAR biasや低noiseでの相対誤差を測定した結果ではない。
BAR ladderと独立referenceには目標priorのdecoderを固定する方針を維持する。
本pilotのalternative priorには0.05が含まれないため、tile288の本校正目標prior=0.05に対する全rungの感度測定とは扱わない。

## 再現と検証

Linuxでも関連18件が0.98秒で通り、同じ実pilotの全64比較を再生成した。
Windows/Linux間で整数countとpoint効果量は一致し、信頼区間の丸め差は比較時の絶対1e-14・相対1e-12の許容内だった。
両方とも同じLinux pilot記録を後処理した結果であり、Windows/Linuxのdecoder出力が一致することを意味しない。
新しいdecoder実行や追加qsubは行っていない。
配置先は `/home/user/workspace/mcmc4qec/20261018-tile-prior-effect-v1`、bundle SHA-256は `f028f192d4c3302f8cf203e7a0b4201538053c99984cfefa8e618240a2a20cfd` である。
元の集計、Linux再生成、hash、数値差分は `pilot_prior_effects.json`、`pilot_prior_effects_linux.json`、`prior_effect_validation.json` に保存した。

```powershell
$env:PYTHONPATH='src'
& "$env:USERPROFILE/AppData/Local/Programs/Python/Python311/python.exe" cluster_scripts/tile_prior_effect.py --manifest docs/wp/data_tile_validation_2026-10-17/pilot_manifest.json --summary docs/wp/data_tile_validation_2026-10-17/pilot_summary.json --counts docs/wp/data_tile_validation_2026-10-17/pilot_decoder_counts.json --output output/pilot_prior_effects_reproduced.json
```
