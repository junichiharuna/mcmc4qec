# 残り5条件の全PC回収後index

## 小仕様

C1T1・C1T2・C3T0・C3T1・C3T2の事前固定assignmentを用い、両PCのserial完了と全割当batchの転送検査を待つ。
全38 batch・768群がそろうまでindexを開始せず、任意のbatchを飛ばさない。
prepared input、転送検査、assignmentのconditionとbatchを照合し、archive・receipt・parent・input archiveをhash付きregistryへ保存する。
元の独立cohort_index.pyを変更せず、保存済みの元source bundleを指定した別processで呼ぶ。
5条件それぞれのnative reference configに固定された113 sourceは、保存済みbundleの113 sourceと完全一致することを実行前に要求する。
既存検証器が入力archiveに対するsourceの一致、全保存BAR行、分母、失敗・未定義・区間未取得・診断警告を検証する。
新しいsampling・BAR・bootstrap・decoder計算は行わない。
最終snapshotには768群・67,584予定行・pending 0・全batchの一致を要求する。
科学的なcohort受理と収束・被覆の保証は宣言せず、最終集計・full監査との結合は後続で行う。
出力と起動intentは排他作成し、途中失敗を自動再試行しない。
旧C1T0の実行sourceや稼働中driverは変更しない。

## 受入条件

固定assignmentと全5条件のsource census一致を実ファイルで検査する。
未完了host、異なるcondition/host、未検証転送、異なるbatch、欠落batchを拒否する。
一部がそろった状態を全件完了へ読み替えず、既存snapshotを上書きしない。
元のindex検証器による失敗と診断を保持する分母処理の回帰テストを実施する。

## 実施結果

全5条件の固定assignmentは各38 batch・768群であり、native configの113 sourceと保存済み元bundleの113 sourceの完全一致を実ファイルで確認した。
Windows Python 3.11で追加10 passed・0.84秒、元index検証器の回帰8 passed・0.90秒だった。
未完了host、異なるcondition/host、異なる転送batch、未検証転送、欠落batch、partial snapshotの拒否を確認した。
元のindex検証器と数値計算sourceは変更していない。
新しい接続用driverのLinux試験と、5条件の本番全archive走査は未実施である。
[sourceと受入ログ](data_tile_validation_2026-10-17/planned_cohort_index_acceptance_v1/manifest.json)のmanifest SHA-256は `b4addc2db3b6c3857166dffb6dd191469e225e8818816351254666ed70b3df2b` である。
実行sourceのSHA-256は `dbe29cfa48282628ecdc5f2f2b8b9949f6acf1e380d62a7ca0ec979c78180607` で、稼働中に変更しない。

C1T1はlocal PID37216、C1T2はlocal PID12872で起動し、00:46 JSTに両sessionの継続をpollで確認した。
実行記録は `data_tile_validation_2026-10-17/planned_cohort_c1t1_index_v1/` と `planned_cohort_c1t2_index_v1/` に保存する。
両者とも両PC全回収待ちであり、本番index作成・転送・最終report結合は未実施である。
新driverは残りC3の3条件にも同じ明示引数で対応するが、その待機processはまだ起動していない。
shared parity・predecessor入力の回収と再検証、転送recipe、最終reportへの接続は別途必要である。
