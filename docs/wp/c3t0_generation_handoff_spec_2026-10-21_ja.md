# C3T0の既存生成jobから未投入partitionへの引継ぎ

## 小仕様・実行順

使用済みanchor265371とsample前半265372のreceipt・script・stdout・stderrを固定し、再投入しない。
未使用のsample partition 1だけを投入候補とする。
C1T2の全3 generatorの投入記録とregistry完成を待ち、そちらの未投入generatorを追い越さない。
C3T0 anchorの実PBS正常終端と、sample前半の実PBS identity・資源・実行回数を再確認する。
sample前半は実行中でも独立partitionの後半を投入できるが、既知の異常終了は拒否する。
投入前にQを含む要求ノード数を観測し、元wrapperの共有lockと投入直前の再検査を使って最大2ノードを維持する。
3件の実receiptを同条件registryへまとめ、後続のnative reference・collectorが実終端を検査できるようにする。
registry完成は全samplingの終了や科学的受理を意味しない。
保存済みpreflightの「未使用execute」は作成時点の記録として保持し、現状の投入済みjobを上書きしない。
通信失敗・観測timeout・曖昧なqsub結果は同一操作の再実行理由としない。

## 受入条件

既存2件の実receiptと固定preflightを照合し、別phase・script・job ID・出力の改変を拒否する。
新規submitがsample partition 1だけに制限されることを確認する。
C1T2のregistryが未完成なら新規qsubを呼ばない。
実行中の正しいjobと正常終端を区別し、異常終端・再実行・別所有者・別資源を拒否する。
後続registryは元の独立validatorで検査し、元helper・計画・seedを変更しない。

## 実施結果

Windowsで追加20件・0.84秒、元registryの回帰26件・0.61秒が成功した。
実2 receiptと出力を照合し、source・job・条件の一致を起動前に確認した。
新しいsubmit入口はsample partition 1だけを受け付け、実行中のjobと正常終端の扱いを区別する。
元の観測・slot待機・PBS terminal検査をそのまま継承している。
新driverのLinux単独テスト、本番sample partition 1投入、本番registry完成は未実施である。
source・red/greenログ・環境は [受入manifest](data_tile_validation_2026-10-17/c3t0_generation_handoff_acceptance_v1/manifest.json) に保存した。
manifest SHA-256は `48ef15da1e6836c14154a52c4765dfe9d57caadc941e0480833e6c467fdc8a50` である。
driver SHA-256は `116e869e78944981e253fb769cca3220b9a4d27d0fe96c92376366ef53925d01` である。
01:32 JSTにPID17484のlive sessionを確認し、C1T2 generator投入完了待ちで、新しいqsubはまだ実行していない。
実qstatで既存sample265372はRを確認した。
