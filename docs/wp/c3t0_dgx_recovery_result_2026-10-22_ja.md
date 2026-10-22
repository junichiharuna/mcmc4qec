# C3T0 DGX入力回収と後続処理の復旧

## 結果

2026-10-22 13:06 JST時点で、DGX batch8の解析を再開し、後続の集約・転送・最終解析・算術確認と計時候補作成への待機処理を再接続した。
C3T1のPC用待機処理も、両hostの復旧済みC3T0 serialを参照するよう再接続した。
稼働中だったnative reference controller、labo serial、クラスタjobは再起動していない。
低ノイズ正式完了は8/12条件、C3T0の独立照合済み回収は256/768群のままであり、復旧を科学的校正の完了とは扱わない。

## 原因と修正

旧DGX serialはbatch8の入力exportのSSH待機が約300秒で終了し、後続controllerも前段失敗を検知して停止した。
クラスタ側のexportはその直後に完成していた。
書き出しprocessと対象directoryを開いたprocessがないこと、archive全体hash、receipt、元入力とgenerator終端を確認し、完成済みarchiveだけを回収した。
元exporterの全member・metadata・assignment検証を維持し、54,345,888 bytes・4,977 member・20群のprepared_inputを得た。
archive SHA256は `a7002c50fec1cc01895afc2efc550687dc9bf48f1a0ce676a8586e42799baa12` である。
batch0〜7の41操作の完了記録とartifact hashを照合し、新serialの再利用記録に引き継いだ。
batch8のexportを再実行せず、preposition・stage・launchを進めた。
未実行batch9〜32には、SSH keepaliveを保ったままexportのローカル待機上限だけを外すadapterを使用する。
scp・qstatの期限、全検証、失敗時停止、33 batchの固定割当は維持する。
共有入力のcollect-dgx・collect-labo・verifyも既存の成功記録と入力を照合して再利用した。
旧source・停止記録・失敗logは保持し、稼働中sourceを変更していない。

## 検証と保存先

復旧仕様は[小仕様](c3t0_dgx_export_reconciliation_spec_2026-10-22_ja.md)に記録した。
各adapterを受入テスト作成後に実装し、完了済み操作の非再実行、異なるscopeや変更済み記録の拒否、未完了時の待機、前段失敗の伝播、全分母を維持する検査を実施した。

| 対象 | passed | 主な確認 |
| --- | ---: | --- |
| 完成済み入力回収 | 15 | 別batch拒否、元archive検証を保持、exportを呼ばない |
| DGX serial継続 | 16 | 41操作再利用、33 batch保持、変更済み旧記録拒否 |
| cohort index再接続 | 14 | 両hostの復旧serial、全768群・67,584行の契約 |
| distribution再接続 | 19 | 共有入力再利用、未完了indexでは転送しない |
| final preparation再接続 | 5 | 元preparerと検証を保持、未完了なら待機 |
| final execution再接続 | 5 | 元qsub経路・環境・collectorを保持、未準備なら投入しない |
| final downstream再接続 | 30 | 算術確認と候補検証を保持、両結果を要求 |
| C3T1 PC待機の再接続 | 7 | native計算の維持、両hostの前条件完了待ち |

合計111 passedで、最長のテストファイルは43.86秒だった。
実行環境は既存Windows Python 3.11で、`-B -m pytest <対象directory> -q -p no:cacheprovider` を用いた。
これらはcontroller復旧の検証であり、BARの被覆・混合・推定精度の追加検証ではない。
sourceとテストlogは `data_tile_validation_2026-10-17/c3t0_dgx_reconnection_acceptance_v1/` と `c3t1_pc_reconnection_acceptance_v2/` に保存した。
前者manifest SHA256は `c63e13e39354056b4c579a871ce924909b24761c276a4db36630138f2afed788`、後者は `c7205c9580a76a9bbebe233d4be58cb146f6da149e7d1a1a6b6ad93bc4e141fa` である。
実processとPBS観測は `data_tile_validation_2026-10-17/c3t0_dgx_reconnection_live_observation_20261022_v1.json`、SHA256は `2dd150193119123d1bdc3326d281297344c0dbd71c306892ae26963d854b106f` である。
保存済み実行先は排他的に作成するため、稼働中driverを再実行せず、再現時はテストと保存済み入力照合から始める。

## 稼働確認

DGX batch8の実PID355285とconfig SHA256 `b78261030043ea456e27881815d2beeb511a6b4993ad7b1bd7f08f7302eac9ba` の一致を確認した。
labo batch4の実PID21040も稼働中だった。
クラスタの265435（C1T2最終解析）と265438（C3T1 sample1）はR、各1node・合計2nodeだった。
復旧driverのlocal PIDはDGX serial49444、index45796、distribution40256、preparation16452、execution21172、downstream15392である。
C3T1のPC waiterはDGX5628・labo13536で、既存native controller10120を維持した。
今回の作業で手動qsub・qalter・qdel、commit・push・公開操作は行っていない。
