# 分割集約後の独立計時待受の接続結果

分割経路のseed censusから独立計時の準備・実行へ接続する待受を追加した。
科学計画の準備本体、scheduler、remote transportは既存v2とbyte単位で同じであることを試験した。
全24組合せ・MC/BARの48行と、capacity各2反復・本計測各192反復を維持する。
通常経路が選ばれた場合は準備・qsubを行わず終了する。
対象がゼロの場合は既存のno-op処理で全行を保存する。
上流の失敗や矛盾するskip記録を拒否し、投入応答不明時に自動再投入しない既存処理を維持する。

Windowsの準備試験24件が1.13秒、実行試験26件が1.12秒で成功した。
Linuxでは科学計画準備の制御試験18件が0.11秒、scheduler10件が0.10秒、transport10件が0.06秒で成功した。
試験では科学処理とPBS応答の一部をfixtureで置き換えており、本番の独立計時は未実施である。
Linux記録は [accepted.json](data_tile_validation_2026-10-17/low_partition_independent_linux_v1/accepted.json) であり、SHA256は `60842628f2a29b460adff5447c44bab0052e997233a710f91ed8adefc7d36938` である。
sourceと受入記録は [accepted.json](data_tile_validation_2026-10-17/low_partition_independent_acceptance_v1/accepted.json) に保存し、SHA256は `036312516abe8d08d58af212f0ac6d5c36db4c1c861228534b812a2fca15ad19` である。

2026年10月23日06:11 JSTに準備待受PID19316と実行待受PID27136を起動し、対応するcommand lineと待機phaseを確認した。
準備は分割census、実行は計時入力の完成を待っている。
local journalはそれぞれ `low_partition_independent_preparation_v1` と `low_partition_independent_execution_v1` である。
remote configは `/home/user/workspace/mcmc4qec/20261023-low-partition-independent-inputs-v1`、制御rootは同階層の `20261023-low-partition-independent-controls-v1` とした。
通常経路の稼働中driverとjournalは変更していない。
新しい数値jobはまだ投入しておらず、本番投入時には既存のqsub・共有lock・最大2要求nodeの制御を使う。

最終報告の準備は既存コードが単一selectorのdescriptorを要求するため、分割mergeの受理証拠を直接検証する接続が残る。
分割結果を単一selectorの実行結果に見せかけず、検証経路を区別して接続する必要がある。
