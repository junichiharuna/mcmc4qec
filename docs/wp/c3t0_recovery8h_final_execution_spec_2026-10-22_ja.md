# C3T0復旧finalの実行と回収

最終準備の実accepted記録が作られるまでqsubを行わない。
元の一回限りの実行driverを別namespaceで使い、新しいjob root・準備記録・回収先と、明示的な単一thread環境を固定する。
旧準備・実行の失敗記録を残し、曖昧な投入応答は自動再試行しない。
空き枠待ちと実投入の共有lockを維持し、待機jobも含めて最大2ノードとする。
実qsub応答、固定script・1 CPU・32 GB・12時間の要求、実F・exit 0・run_count 1を確認してからcomplete・回収へ進む。

回収器は既存のC1T0復旧版を別ファイルに複製し、対象をcase 3・target 0・p=0.01に固定する。
67,584行・192 seed・352設定、監査authority、source、13成果物、転送前後のsnapshot一致は維持する。
case 1のbit-flip結果、別target・別pの結果は拒否する。
回収時のSSHにも単一threadとPYTHONHASHSEED=0を明示する。
POSIXのimport・metadata・転送試験はLinuxで実施するが、実C3T0 reportの回収完了とは区別する。
最終集計回収後の独立算術確認、計時candidate作成、all12集計への接続は別途必要である。
