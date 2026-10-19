# 主校正 4 case の最終再集計概要

4 case の全 192 replicate・768 group を凍結 runner で再集計し、PBS の F / exit 0 と全 phase・入力・source・出力 hash を確認した。
case0/1/2/3 の job はそれぞれ 265241/265236/265240/265238 である。
全 case に 352 条件の BAR 集計、1680 対比、352 条件の精度評価、48 条件の重み比較があり、depolarizing の 2 case には 352 条件の初期化層別もある。
4 case のすべての 352 条件で点推定と区間は 192/192 取得できたが、診断未定義や診断 flag は別に保持されている。

以下は結果に応じて最良設定を選ばず、最大予定 chain・burn-in 6000・最長保存 trace・fine ladder に固定した記述的比較である。
ZH/rejection を表示例に使い、全 kernel・初期化・誤差法の値は同名 JSON に保存した。
この設定は公開既定の 1 chain とは異なる。

| code / noise | 物理 p | chain / 保存数 | MC reference | 相対 bias | 相対 RMSE | block32 被覆 | block1024 被覆 | cross_chain 被覆 | 診断 flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tile72 bit-flip | 0.03 | 16 / 60000 | 0.0429675 | −0.060% | 0.805% | 183/192 | 185/192 | 186/192 | 0/192 |
| tile288 bit-flip | 0.05 | 8 / 12000 | 0.0289493 | +0.439% | 4.815% | 124/192 | 178/192 | 176/192 | 192/192 |
| tile72 depolarizing | 0.03 | 8 / 12000 | 0.0301685 | −0.125% | 1.903% | 166/192 | 180/192 | 177/192 | 191/192 |
| tile288 depolarizing | 0.05 | 8 / 12000 | 0.00295048 | +0.407% | 7.211% | 114/192 | 177/192 | 178/192 | 192/192 |

被覆は有限 direct-MC reference の点推定を含む 95% 区間の数であり、真値に対する名目被覆の保証ではない。
reference の試行数は最初の 3 case が各 6291456、tile288 depolarizing が 62914560 である。
reference 自体の 99.9% 区間全体を含む数と交差する数、被覆の記述的 Wilson 区間も JSON に残した。
例えば tile72 bit-flip の cross_chain は reference 点では 186/192 だが、reference 区間全体を含む数は 148/192、交差する数は 190/192 であり、reference の有限精度を無視できない。

tile288 の短い block32 では区間の被覆不足が明瞭で、block1024 や cross_chain では改善するが、全 192 replicate に診断 flag が残る。
tile72 bit-flip の長い設定では今回の診断 flag が 0 になったが、これも混合・既約性・収束の証明ではない。
同じ固定切り口で ZH/ZHS と rejection/logical をすべて含めた相対 RMSE 範囲は、case0/1/2/3 の順に 0.805–0.827%、4.815–5.071%、1.772–2.231%、7.138–7.665% である。
この結果から stabilizer 混合 ZHS の一律な優位は示せない。

全 352 条件の有限 reference 区間全体に対する経験的相対 RMSE 10% 以内の分類は、順に 322、188、283、60 条件であった。
reference の範囲で 10% 境界をまたぐ条件は順に 0、8、0、12 である。
20% 以内は 352、256、352、240 条件で、case3 の 4 条件は reference に敏感な境界であった。
これらの条件は同じ trace を共有するため独立の 352 試行ではなく、母集団 RMSE の信頼保証でもない。

target rung の条件付き重み平均も保存した direct-MC reference と比較した。
固定切り口の平均差は概ね差の標準誤差の数倍以内だが、これは BAR 全 rung の混合診断を代替しない。
実際に tile72 depolarizing の target 重み診断 flag は 0–1/192 でも、BAR の全 rung 診断 flag は 190–192/192 である。
depolarizing の X/Z logical 初期化層別は各 96 replicate を残し、全 192 replicate の primary summary を再現した。
例えば tile288 depolarizing・ZHS logical の相対 bias は X 側 +2.099%、Z 側 +0.125% だが、補助的な層別比較だけで一般的な初期化効果や有意差を断定しない。

同じ精度に達する実時間の優劣は今回の再集計だけでは確定せず、固定 MC/BAR timing の測定との接続が必要である。
低ノイズと重み層別 reference の検証はこの主校正 4 case の概要とは別である。
fresh native probe、bootstrap 再実行、全 trajectory replay、全物理状態再復号、歴史的 consumed hash の証明は追加していない。
元 full audit の native 証拠を継承し、今回の回収は保存済み成果物の照合だけを実施した。

再現 script は summarize_final_reaggregation_four_cases_v1.py、数値・全入力 SHA256 は final_reaggregation_four_case_scientific_summary_v1.json に保存した。
概要 script の初回は strata の平坦な condition field を入れ子と仮定して停止したが、正式形式に修正後、約 2.3 秒で全 case の保存済み report を集約した。
科学計算や cluster job の再実行は行っていない。
