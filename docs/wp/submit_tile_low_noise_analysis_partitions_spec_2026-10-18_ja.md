# 低ノイズ本番BAR partitionのqsub投入

投入前にpartition driverの `read_plan` を呼び、実測capacity・本番manifest・sampling/native evidence・解析contextを再検査する。
partition indexを一つ指定し、固定資源計画の96 CPU・memory・walltime・worker数で1ノードを要求する。
worker数はdriverが固定planから読むため、PBS commandで上書きしない。
bundleのdriver・依存source・core package・Python executableのpathとhashを結び付ける。
rootは同bundleの `runs/` 配下に限定し、symlink escapeを拒否する。

submission intent・ledger・script・dry-runは `root/analysis-submissions/{index}/` に保存する。
driver専用の `analysis-partitions/{index}/` を投入時に作らず、既存execution evidenceや対象group artifactがあれば投入を拒否する。
実行は `qsub` を一度だけ呼び、全queued/running requestを含め同時最大2ノードとする。
稼働中のtile coordinatorがある間は投入しない。
既存低ノイズ投入と同じ `bundle.parent/tile-low-noise-submission.lock` を排他的に用いる。
lock取得後に全plan・source・Python・script・既存intentを再確認する。
qsub呼出し前にsubmission intentを保存し、timeout・異常終了・解釈不能responseではintentとlockを保持して自動再投入しない。
qsub成功時だけjob ID付きledgerを保存してlockを解除する。

受入ではqsubをmockし、dry-run、成功一回、queued node上限、coordinator、曖昧response、同partition重複、source/Python/script変化、path escapeを検査する。
実際のqsub・remote計算は受入では実施しない。

CLIは `python cluster_scripts/submit_tile_low_noise_analysis_partitions.py --bundle BUNDLE --root ROOT --partition INDEX` でdry-runを作成し、`--execute` を追加するとguardを再検査してqsubを呼ぶ。
2026-10-18のWindows Python 3.11受入は28件が11.80秒で成功し、symlink escapeの3ケースも実行して拒否を確認した。
Linux受入・実qsubはこの時点では未実施である。
