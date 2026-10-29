# 校正 cohort の再生成に必要なセットアップの記録（2026-10-29）

所有者の決定（2026-10-29）により、低ノイズ校正 cohort の raw trace と解析 payload（クラスタ `20261018-tile-low-analysis-v11/runs/*/{traces,analysis}/`、約 212 GiB ≈ 227 GB、写しなし）は保持しない。
代わりに、同じ run をいつでも再生成できるように、セットアップ（manifest・投入 script・pin された source・環境・seed）を残す。
本稿はその一覧と、再生成の手順、削除したものの記録である。
最終 report（`report.json`、SHA-256 `79d1357d…`）はこれらの raw trace を 1 つも pin していないので、削除は最終 report の再検証に影響しない（pin 一覧 86,902 path のうち `…-v11/runs/` 配下は 0）。

## 残すもの（run ごと）

12 run（`partitioned-full-{0,1,3}-{0,1,2}-v1` と `staged-production-2-{0,1,2}-v1`）のそれぞれで、`traces/` と `analysis/` 以外のファイルをその場に残し、提供用 bundle（クラスタの staging、Zenodo などの公開 record は作らない）（group D、63,942 ファイル、2.7 GiB）にも写した。

| ファイル・ディレクトリ | 役割 |
|---|---|
| `manifest.json` | 再生成の全パラメタ: `master_seed`、`chain_counts`、`burns`、`blocks`、`bootstrap_replicates`、`checkpoint_stride`、`kernels`、`decoder`、`initializations`、`stages`、`anchor_trials`、`replicates`、`condition`・`case`・`target_index`、`required_threads`、`runtime`、`sources`（script の sha）、`native_input_digests` |
| `platform_profile.json`、`platform_fixture.json` | native decoder 環境の fixture と profile（decoder の失敗 label は環境依存なので、再生成時に一致を確認する） |
| `sample-execution-intent.json`、`anchors-execution-intent.json`、`analysis-execution-intent.json` | 実行時の intent（PBS job、host、manifest digest） |
| `submission.json`、`submission-intent.json`、`low-noise.sh`（staged-production） | 実際に投入した PBS script と台帳 |
| `sampling-submissions/`、`sampling-partitions/`、`sampling-collection/`、`sampling-collection-submission/`（partitioned-full） | 分割投入の script・台帳・回収記録 |
| `anchors/`（576 ファイル）、`anchors-summary.json`、`sample-summary.json`、`partition-collection/` | anchor と sampling の集計 |
| `analysis_manifest.json`、`partition_analysis_manifest.json`、`analysis-parent-prepared.json`、`analysis-submissions/`、`analysis-partitions/`、`preflight-plan/` | 解析段の計画と台帳（解析結果本体 `analysis/` は削除対象） |

## 残すもの（環境と source）

| 場所 | 内容 |
|---|---|
| `20261018-tile-low-analysis-v11/cluster_scripts/`（86 ファイル） | 校正・解析・投入の script 一式（`submit_tile_low_noise_sampling_partitions.py`、`submit_tile_low_noise_partitioned_analysis.py`、`audit_tile_low_noise_traces.py` など）。最終 report の `source_sha256` に 76 本が pin されている |
| `20261018-tile-low-noise-v2/`（12.9 GiB） | staged-production 3 run を最初に走らせた環境（`cluster_scripts/tile_low_noise_study.py`、venv、`runs/production-2-*`）。残す |
| venv（v11、python 3.11.9） | `numpy==2.4.6`、`scipy==1.17.1`、`ldpc==2.4.1`、`PyMatching==2.4.0`、`mcmc4qec==0.1.0.dev5`（wheel sha256 `f321f735…`、`20261017-tile-production-v1/dist/`） |
| `20261018-tile-weight-reference-v4/`、`20261018-tile-low-analysis-v7/runs/weight-reference-audit/` | WSS 参照と監査（pin 済み、データセットに含む） |
| `20261025-low-parallel-front-v6/merge-parallel-v2/` | 受理済み selection（校正の評価結果 352 設定 × 24 行、pin 済み、データセットに含む） |

seed は `manifest.json` の `master_seed` と `calibration.py` / `tile_low_noise_timing_plan.py` の seed 導出（`plans.seed_coordinates`）で決まり、trace を保存しなくても同じ乱数列を再現できる。

提供用 bundle（クラスタの staging、Zenodo などの公開 record は作らない） には、上の環境と source を group E（`E_regeneration_environment`、2,293 ファイル）として追加した: `20261018-tile-low-noise-v2/` の `cluster_scripts/` と traces・analysis・venv を除く 20 MiB 以下の記録、`20261018-tile-low-analysis-v11/cluster_scripts/` の全 86 ファイル、`0.1.0.dev5` の wheel、両 venv の `pip freeze`（`ENVIRONMENT-tile-low-analysis-v11.txt`、`ENVIRONMENT-tile-low-noise-v2.txt`）。
識別子の置換後に grep で漏れがないことを確認した。

## 再生成の手順

1. 同じ wheel と同じ pin の venv を作る（上の版）。native decoder（BP-OSD、`ldpc==2.4.1`）は Linux の同じ環境で動かし、`platform_profile.json` と `platform_fixture.json` の一致を `probe_tile_decoder_platform.py` で確認する。
2. staged-production の run は `low-noise.sh` の 2 段（`tile_low_noise_study.py anchors` → `sample`、96 worker）を同じ root 構成で qsub する。
3. partitioned-full の run は `submit_tile_low_noise_sampling_partitions.py` で `sampling-partitions/` と同じ分割を投入し、`sampling-collection-submission/` の手順で回収する。
4. 解析は `submit_tile_low_noise_partitioned_analysis.py`（`analysis_manifest.json`・`partition_analysis_manifest.json` に従う）で再実行し、`sample-summary.json`・`anchors-summary.json`・`partition-collection/` の値と照合する。
5. 既存の集計と一致すれば、受理済み selection の値（`merge-parallel-v2/selection.json`）へ同じ経路でつながる。

所要時間の目安は、元の実行記録（`submission.json` と PBS 台帳）にある walltime で、1 run あたり 96 CPU で数時間から十数時間である。

## 削除したもの

削除前に各 run の `traces/` と `analysis/` について全ファイルの size と path の一覧（`archive-20261029/v11-runs-<run>-<dir>.files.tsv`）を取った。
sha256 は取っていない（提供先がなく、再生成で照合するため）。
削除したものと容量は下表のとおり（削除時の一覧から、ファイル数と GiB）。
`partitioned-full` の 7 run には `analysis/` がなく（解析は別 root の partition 解析で行われ、その記録は残している）、traces だけを削除した。

| run | traces（ファイル数 / GiB） | analysis（ファイル数 / GiB） |
|---|---:|---:|
| partitioned-full-0-0-v1 | 368,640 / 10.80 | 2,016 / 6.15 |
| partitioned-full-0-1-v1 | 479,232 / 12.19 | 1,887 / 7.50 |
| partitioned-full-0-2-v1 | 552,960 / 12.85 | なし |
| partitioned-full-1-0-v1 | 184,320 / 11.62 | なし |
| partitioned-full-1-1-v1 | 239,616 / 14.83 | なし |
| partitioned-full-1-2-v1 | 276,480 / 16.94 | なし |
| partitioned-full-3-0-v1 | 184,320 / 21.34 | なし |
| partitioned-full-3-1-v1 | 239,616 / 27.54 | なし |
| partitioned-full-3-2-v1 | 276,480 / 31.64 | なし |
| staged-production-2-0-v1 | 184,320 / 3.03 | 2,304 / 7.32 |
| staged-production-2-1-v1 | 239,616 / 3.72 | 2,304 / 9.36 |
| staged-production-2-2-v1 | 276,480 / 4.14 | 2,304 / 10.57 |

合計は traces 約 170.6 GiB・analysis 約 40.9 GiB（約 211.6 GiB ≈ 227 GB）で、2026-10-29 19:52〜19:59 JST に削除した。
`20261018-tile-low-analysis-v11/runs/` に残っているのは 3.5 GiB（manifest・集計・台帳）である。
