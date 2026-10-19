# Low-noise sampling capacity 全12条件の完了確認

全12条件が PBS F・exit 0 で終了し、sample 1,216件と anchor 24件の保存 artifact を検証した。
各条件の全 artifact はクラスタ側で marker/hash、seed、固定 prior、config、metadata、source・Python・native binary、PBS・実行 intent を照合し、回収した metadata の全 hash をローカルでも照合した。
元の資源計画式による単一 PBS 本計算の受理可否を以下に示す。

| 符号・noise | p | job | capacity PBS wall | sample/anchor | full要求時間 | full要求GB | 元gate |
|---|---:|---:|---:|---:|---:|---:|---|
| tile72 bit | 0.01 | 265235 | 00:00:48 | 80/2 | 31:30:00 | 32 | 24h上限超過・分割が必要 |
| tile72 bit | 0.003 | 265242 | 00:00:49 | 104/2 | 31:30:00 | 32 | 24h上限超過・分割が必要 |
| tile72 bit | 0.001 | 265243 | 00:00:53 | 120/2 | 35:30:00 | 32 | 24h上限超過・分割が必要 |
| tile288 bit | 0.01 | 265244 | 00:01:31 | 80/2 | 26:00:00 | 32 | 24h上限超過・分割が必要 |
| tile288 bit | 0.003 | 265245 | 00:01:32 | 104/2 | 26:30:00 | 32 | 24h上限超過・分割が必要 |
| tile288 bit | 0.001 | 265246 | 00:01:34 | 120/2 | 27:00:00 | 32 | 24h上限超過・分割が必要 |
| tile72 depolarizing | 0.01 | 265247 | 00:00:37 | 80/2 | 09:30:00 | 32 | 受理 |
| tile72 depolarizing | 0.003 | 265248 | 00:00:38 | 104/2 | 10:00:00 | 32 | 受理 |
| tile72 depolarizing | 0.001 | 265249 | 00:00:40 | 120/2 | 11:00:00 | 32 | 受理 |
| tile288 depolarizing | 0.01 | 265250 | 00:02:28 | 80/2 | 44:30:00 | 32 | 24h上限超過・分割が必要 |
| tile288 depolarizing | 0.003 | 265251 | 00:02:29 | 104/2 | 45:00:00 | 32 | 24h上限超過・分割が必要 |
| tile288 depolarizing | 0.001 | 265252 | 00:02:35 | 120/2 | 47:00:00 | 32 | 24h上限超過・分割が必要 |

単一 PBS の元 gate は 3条件を受理し、9条件を資源上限で拒否した。
上限拒否は元 measured_capacity の payload/native 検査より先に生じるため、全 artifact の独立検査を先に実行している。
資源外挿は完了時間の保証ではなく、capacity のサンプルは本計算の推定に混ぜない。
再復号、混合、収束、bias、被覆、精度の検証結果としては扱わない。
raw payload はクラスタ側で保持し、ここでは metadata と検証済み hash の回収を記録する。

機械可読な条件別証拠と全入力 hash は `low_sampling_capacity_all12_summary_v1.json` に保存する。
