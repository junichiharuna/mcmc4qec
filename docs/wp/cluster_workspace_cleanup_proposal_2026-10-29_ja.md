# クラスタ workspace の整理案（2026-10-29、削除は未実施）

本稿はクラスタの `~/workspace/mcmc4qec/` を 2026-10-29 に計測した結果と、残すもの・消してよいものの分類案である。
この時点で削除は何も行っていない。
削除は所有者の判断で行い、実行前に各候補の中身を再確認する。
計測は `du` の値（GiB、1 GiB = 1024 MiB）で、全一覧は手元の `ws_du_20261029.txt`（635 行）にある。
共有 filesystem は 50 TB 中 37 TB 使用（76%）で、この workspace は約 420 GiB である。

## 全体像

| 区分 | ディレクトリ数 | 容量（GiB） |
|---|---:|---:|
| 全体 | 635 | 約 420 |
| `20261018-tile-low-analysis-v11/runs/`（12 条件の校正 cohort の raw 実行） | 1（内部 12 run） | 223 |
| 2026-10-17〜19 の生産・校正・回復系 | 約 25 | 約 95 |
| portable BAR の DGX・ラボ PC batch（c0t2） | 38 | 約 10 |
| 独立計時（stage3-v2 の 49 root）と report 経路 | 4 | 約 9 |
| その他の小さな環境・config・補助（1 GiB 未満、うち 370 個は 50 MiB 未満） | 約 560 | 約 10 |

手元の `docs/wp/data_tile_validation_2026-10-17/` は 48 GB、`data_portable_bar_2026-10-19/` は 9.2 GB で、いずれも gitignore 済みである。

## 分類 A: 最終 report が pin しているもの（削除不可）

最終 report（`report.json`、SHA-256 `79d1357d…`）の `input_sha256`・`input_targets`（173,804 path）と `source_sha256` が参照する top-level ディレクトリは次の 26 個である。
これらは final report の再検証に必要で、1 ファイルでも変わると凍結 reader の照合に落ちる。

| ディレクトリ | pin 数 | 容量（GiB） | 役割 |
|---|---:|---:|---|
| `20261018-tile-weight-reference-v4` | 143,684 | 0.8 | WSS 参照（chunk census を含む） |
| `20261018-tile-low-timing-stage3-v2` | 29,214 | 5.4 | 独立計時 49 root の raw payload |
| `20261018-tile-low-timing-stage2-v1` | 280 | 小 | venv（report job の python）と script |
| `20261018-tile-low-analysis-v11` | 156 + source 76 | 223.0 | 校正 script 群と selection の出力（raw run は下記 B） |
| `20261018-tile-low-analysis-v7` | 132 | 小 | 参照 audit の raw report |
| `20261025-low-parallel-independent-controls-v9` | 98 | 小 | 独立計時の terminal 記録 |
| `20261018-tile-bar-seed-audit-v1` | 96 | 5.8 | seed 監査 |
| `20261024-c3t2-index-relocation-v1` | 36 | 7.7 | 実行 source root・journal・actions |
| `20261025-low-parallel-front-v6` | 30 | 7.0 | merged selection |
| `20261025-census-operational-bundle-v13` | 26 | 小 | census bundle |
| `20261022-low-timing-parent-environment-v4` | 14 + source 5 | 小 | 親環境 |
| `20261028-low-parallel-report-inputs-v10` | 4 | 小 | report 入力（prepared） |
| `20261028-finite-tail-report-environment-v2` | 2 + source 1 | 小 | delta 付き report 環境 |
| その他 13 個（staging-v1・staging-control-v2・timing-census-v1・stage4-v2・all-readers-v8・parent-environment-v1・census-config-v9/v13・tail-report-environment-v5・wall-runtime-v1・census-inputs-v3・partition-front-controls-v1・independent-timing-report-reference-v1） | 各 2〜4 | 合計 約 3 | script・config・環境 |

report job の root `20261023-low-partition-report-job-v1/runs/report-all24-relocation-v2`（result 1.85 GB）と別経路 `20261028-report-relocation-route-v1`（collected の写し 1.85 GB を含む 1.9 GiB）も A に含める。

## 分類 B: pin されていないが一次証拠として残すもの

- `20261018-tile-low-analysis-v11/runs/`（223 GiB）: 12 条件 × 352 設定 × 192 seed の校正 cohort の raw 実行（`partitioned-full-*`・`staged-production-*`、各 11〜32 GiB）。selection と比較表はここから作られ、最終 report は selection の値だけを pin する。raw を消すと校正の再検証ができなくなる。全 raw の保存・公開は別判断と文書に書いてあるので、少なくとも公開判断まで残す。
- `20261017-tile-production-v1`（28 GiB）・`20261017-tile-calibration-v1`（5.5 GiB）・`20261017-tile-reference-v1`（0.8 GiB）: 主 4 条件の生産・校正・参照。
- `20261018-tile-low-noise-v2`（12.9 GiB）: 低ノイズの初期実行。後続の v11 に置き換わったかは要確認。

## 分類 C: 削除候補（所有者の確認後）

| 候補 | 容量（GiB） | 理由 | 確認事項 |
|---|---:|---|---|
| `20261019-tile-low-bar-recovery-c0t1-v1`、`20261019-tile-low-bar-recovery-v2`、`20261018-v2-tile-case{0,1,2,3}-analysis-recovery`、`20261018-v2-tile-case{0,2}-recovery`、`20261018-tile-case1-recovery-v1`、`20261018-tile-recovery-v1`、`20261018-v1-tile-weight-reference-recovery` | 約 40 | 10/18〜19 の回復作業の中間物。結果は v11 と weight-reference-v4 に統合された | 各 README・receipt が手元の `docs/wp` にあるか、v11 への取り込みが文書化されているか |
| `20261020-portable-mixed-c0t2-inputs-v1`、`20261021-portable-planned-c{1,3}t{0,1,2}-inputs-v1`、`20261020-portable-condition-c1t0-inputs-v1` | 約 40 | DGX・ラボ PC 向け portable 実行の入力束（c3t2 の index 移設で役目を終えた） | c3t2 の index 移設（`20261024-c3t2-index-relocation-v1`）に必要な入力が含まれていないか |
| `portable-bar-c0t2-{dgx,labo}-batch*`、`portable-bar-c0t2-dgx-reassigned-*`（38 個） | 約 10 | portable BAR の batch 結果。手元の `docs/wp/data_portable_bar_2026-10-19/` に 9.2 GB の写し（batch ごとの dispatch・launch・observation・verification 記録を含む）がある | 手元の写しと件数・hash の一致（未照合） |
| `20261025-low-parallel-front-v4`、`-v5` | 2.8 | merge の失敗版。v6 が受理済み | 失敗記録として文書から参照されていないか（参照されていれば小さい journal だけ残す） |
| `20261017-tile-weight-pilot-v1/v2`、`20261017-tile-study-v1`、`20261017-tile-capacity-v1`、`20261017-tile-analysis-capacity-v1` | 約 2 | 10/17 の試行・容量計測 | 文書からの参照 |
| home 直下の補助 script（`cluster_status*.sh`、`cluster_watch*.sh`、`route_watch*.sh`、`audit_roots_check.py` ほか）、`JH.o185349.*` | 0 | 今回の監視・診断用の使い捨て。`JH.o*` は 2025-09 の PBS 出力 | なし（手元の scratchpad に同じものがある） |

C を全部消しても約 95 GiB で、全体の 4 分の 1 弱である。
容量圧力はないので、急いで消す理由はない。

## 進め方の案

1. まず home 直下の補助 script と `JH.o*` を消す（内容はこの session の監視用で、手元に写しがある）。
2. portable BAR の 38 batch について、手元の写しと照合してから消す。
3. 回復系と portable 入力束は、各 README・receipt への参照を `docs/wp` で grep し、参照されていない raw だけを消す。
4. B の 223 GiB は公開判断（全 raw の保存・公開をどうするか）が決まるまで残す。
5. 消す前に候補ごとに `du` と `ls` を取り、削除した一覧を本稿に追記する。
