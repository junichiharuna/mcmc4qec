# C0T0 BAR時間切れとv2再開

元job 265324.node-PRISMは実行上限6時間を超えてF・Exit_status -29・run_count 1・walltime 06:01:29で終了した。
最後の実行中marker観測は672/768件であり、payloadの検証済み件数ではない。
v1 prepareは実PBS stderrの `=>> ` 接頭辞を拒否し、投入には進まなかった。
失敗したprepareのintent・script・stdout・stderr・receiptを保持している。

## 修正と確認

[小仕様](low_bar_pbs_prefix_fix_2026-10-19_ja.md)に従い、v2 inventoryの終了メッセージに限り、接頭辞なし又は正確な `=>> ` を許可した。
既存の23件と追加8件を合わせた31テストが3.81秒で成功した。
修正前は接頭辞ありの受入テストが失敗することを確認した。
変更はinventoryの正規表現1箇所で、他の7 helperはv1とbyte単位で一致する。
v2の投入制御4テストは2.71秒で成功した。
投入制御テストではPBS照会とqsubをmockし、実計算の成功として扱わない。

v2配置は `/home/user/workspace/mcmc4qec/20261019-tile-low-bar-recovery-v2` で、旧v1配置と元データを変更していない。
Linuxで8 helperのcompile・import・hash・元環境との対応を確認し、配置receiptを受理した。
deployment.json SHA256は233a74a024da1771699d6c32d80ba22dd00c35e5b5698262b0674d0487bfde7dである。
元のF/timeout記録を照合したprepareと、空き枠・controller不在を確認したpreflightも受理した。
prepared.json SHA256は7b10c914f724285233f3e47cd046247abe3471e1e9afd8273da05dbf7f82b2c5である。

## 実投入

`output/control_low_bar_recovery_v2.py execute` でqsubを1回行い、265331.node-PRISMの投入receiptを受理した。
要求は1 node・96 CPU・96 worker・226 GB・walltime 12時間で、12時間は完了予測ではない。
投入直後のPBS状態はQで、sampling 265327.node-PRISMはRだった。
待機中を含めて合計2ノードの要求である。
復旧計算は正常な保存groupを検査して再利用し、未完成groupだけを同じ計画・seedで計算する。
再利用件数と未完成件数は復旧job内の検査で確定させ、marker数だけでは受理しない。

## 残作業

実復旧jobの開始・正常終了・completion受理・最終比較・回収は、この文書作成時点では未完了である。
v1のcompletion/report transportをそのままv2へ流用せず、v2配置とhelper hashへ明示的に結び付けた経路を用意する。
正式な低ノイズ比較は引き続き3/12条件で、再開投入を科学的な検証完了には数えない。
公開候補のcommit・push・remote CI・Releaseは未実施である。
