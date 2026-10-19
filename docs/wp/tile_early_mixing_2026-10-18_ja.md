# tile288完了traceの早期混合診断

本番計画を変更せず、事前固定したcase1/3、kernel0/1、初期化0/1、replicate0/1の全16 groupsを調べた。
物理pは両caseとも0.05、decoderは目標priorに固定し、最終rungの8 chains・burn6000・保存12000を用いた。
各設定2 replicateだけの早期診断であり、192 replicateの本校正を代替しない。

| 対象 | 観測量群 | flag数 | 未定義数 | group内最大R-hatの範囲 | group内最小chain ESSの範囲 |
|---|---:|---:|---:|---:|---:|
| tile288 bit-flip | 80 | 25 | 0 | 1.00889–1.03568 | 7.97–56.35 |
| tile288 depolarizing | 144 | 144 | 0 | 1.04577–1.17164 | 4.95–15.12 |

flagは既存基準のR-hat > 1.01、いずれかのchain ESS < 100、または診断未定義のいずれかである。
depolarizingでは全144観測量群がR-hatとESSの両方でflagとなり、ZH・ZHSのどちらについても、この部分集合で十分な混合を確認できたとはいえない。
この結果は非収束の証明でも、2 replicateからのkernel間の統計的優劣判定でもない。
bit-flipの条件付きweight平均は20.20798–20.71692、IAT MCSEは0.12466–0.25307だった。
depolarizingの条件付きweight平均は20.63701–21.34097、IAT MCSEは0.16873–0.28686だった。
これらのMCSEは条件付きweight平均の誤差であり、BARの論理誤り率の誤差ではない。
各chainのsector遷移数・unique sector数、全logical bitを含むIAT・ESS・R-hat・数値ACFを生記録に残した。

128 traceすべてでartifact identity/hash・固定source/runtime・native profile・metadata・全compact配列の検査に成功し、入力エラーは0件だった。
initial128状態とcheckpoint2432状態の再復号が保存値に一致した。
これは全物理traceの再復号やRNG軌道の再現ではない。
全16群の監査・診断本体は合計21.91秒で、各SSH commandは約4.4–5.3秒だった。
pilotの2倍外挿は56.09秒でbatch上限45秒を超えたため、診断値ではなく事前の費用規則に従って1群ずつ実行した。
実qsub・reference比較・BAR推定・被覆校正・本番設定やseedの変更は行っていない。

事前計画は [tile_early_mixing_plan_2026-10-18_ja.md](tile_early_mixing_plan_2026-10-18_ja.md)、集計は [early_mixing_summary_v1.json](data_tile_validation_2026-10-17/early_mixing_summary_v1.json)、全groupの生診断は [early_mixing_group_records_v1.json](data_tile_validation_2026-10-17/early_mixing_group_records_v1.json) に保存した。
計画とnative環境、入力hash、各commandの実行時間は同階層の `early_mixing_*_v1` 証拠に保存した。
回収archiveのSHA256は `97423e604a5cdd7f80bd458c61ee195d0c311dd3c4d4332d231633c9194add42` である。
集計は同階層の `summarize_early_mixing_v1.py` で生archiveから検証でき、既存出力は上書きしない。
