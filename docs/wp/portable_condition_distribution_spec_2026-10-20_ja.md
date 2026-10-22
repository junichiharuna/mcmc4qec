# 条件別PC結果の最終集計入力

固定assignmentの全768群・全batchを最終providerのcontextへ束ねる。
未回収batchがあれば完成したcontextとして出力せず、context失敗・基盤失敗を成功群だけの分母へ変換しない。
元sampling、入力export manifest、出力archive・receipt・parent、hostごとのruntime・source・transform・parity、初回predecessorを明示する。
この入力作成は保存物の結び付けであり、全raw trace・native監査・独立referenceの最終検証を置き換えない。

## 先行する共有保存物の回収

実batch0のstaging recipeとaccepted記録、実saved parity受理記録を外部hashで固定する。
各hostからparityの5ファイルと初回predecessorのintent・completionの2ファイルを読み取り専用で取得する。
remoteで読取前・読取後のhashを既存recipeと照合し、localでも転送payloadと保存後のbyteを再照合する。
取得対象・出力名は固定し、未知member・重複target・hash不一致・転送途中の変更を拒否する。
既存directoryへの上書きや自動再試行は行わず、保存に失敗した場合は記録を残す。
本番のdecoder・BAR・bootstrapを再実行せず、新しいqsubやPC workerも起動しない。

## 後続のcontext作成

外部pin付きregistryのbatch一覧をassignment全体と照合し、完全な終端一覧に限って転送planを作成する。
parity・predecessorは上の回収物を使い、input manifestは元export ZIPのbyteを保持する。
転送先では全ファイルのhashとcensusを検査してからtransfer receiptを作成する。
最終providerは保存parity、各batchの結び付けと失敗区分を再検査し、元環境の最終readerがraw trace・監査・referenceと結合する。

## 19:51 JSTまでの実装と実入力確認

`output/condition_distribution_v1/` に共有保存物の回収と転送planの作成を実装した。
転送planは外部hash付きの完全なindex・registry・shared replayを要求し、全群・全batch・失敗区分・未取得行・診断件数を照合する。
export manifestは元ZIPからbyteを保持して取り出し、最終providerの既存context schemaに合わせて保存する。
元indexと最終provider、計算中のdriverやcollectorは変更していない。

回収部分の18件、全分母と転送先検査27件、ファイル単位の合成context作成・不正入力拒否5件を合わせ、Windows50 passed・5.66秒、Linux50 passed・0.68秒だった。
結合fixtureは保存値を持たない合成metadataであり、本番providerによる全群の受理を示さない。
Linuxのsource・ログは [native受入](data_tile_validation_2026-10-17/condition_distribution_native_v1/accepted.json) に保存した。

本番の共有保存物はDGXから7ファイル・6,477,168 bytes、Laboから7ファイル・6,494,682 bytesを回収し、転送前後とlocal保存後のhashが一致した。
元sampling時の113ソースを復元した環境で、両hostの保存parityを各88設定・診断・ACFについて元native referenceと比較し、一致した。
これは保存値の比較であり、新しい復号・BAR・bootstrap計算は行っていない。
初回predecessorも最終providerの既存検査関数を直接使って照合した。
実入力の比較は3.86秒で、[結果](data_tile_validation_2026-10-17/portable_condition_c1t0_shared_inputs_local_replay_v1.json) のSHA-256は `473cc9a4c0fd8dea782891ce7f700a356fbf7becc5cde595101705ebb2c8bce2` である。

実snapshot v4の60/768群・未回収708群を渡すと、完全なbatch一覧ではないためcontextを出力せず拒否した。
この [実入力での拒否記録](data_tile_validation_2026-10-17/portable_condition_c1t0_distribution_partial_v1/receipt.json) は未完了を成功扱いしないことの確認である。
実全群indexとcontextの作成、転送処理の新条件への接続、本番転送・最終qsub・report回収は未完了である。

## 再現と本番への接続

source・受入・共有保存物と実入力照合は [保存manifest](data_tile_validation_2026-10-17/condition_distribution_progress_20261020_v1/manifest.json) にある。
fixtureは `python -B -m pytest output/condition_distribution_v1/test_shared_inputs.py output/condition_distribution_v1/test_distribution.py output/condition_distribution_v1/test_prepare.py -q` で実行する。
Windowsの実行Pythonは `.venv-experimental-optional/Scripts/python.exe` の絶対パスを使った。
共有保存物の回収・実入力比較・partial拒否・native配置・archiveのv1操作は使用済みであり、同じ保存先に再実行しない。
本番では全batch回収後の完全なregistryと独立indexを外部hashで固定し、partial検査用とは別のrecipeを作成する。
入口は `distribution.py --recipe <新しいrecipe> --recipe-sha256 <固定hash> --output <未使用directory>` である。
入力作成の成功だけでは実転送・qsub・科学受理を意味せず、未接続の転送処理と最終監査は別途完了させる。

## 新条件の転送接続

既存mixed転送処理のremote directory作成・scp・全member照合・一度限りのlocal記録・失敗時の無再試行はそのまま使う。
別namespaceのwrapperで新しい転送planとcontextの検査に差し替え、元moduleを変更しない。
contextの全入力census、assignment、全batch、export manifest、receiptの分母、両hostの共有保存物とnative referenceの結び付けを検査する。
科学的受理は引き続き最終provider・元環境監査・reference結合に残す。
転送先は既存と同じクラスタworkspace直下の未使用directoryに限る。

`output/condition_distribution_v1/transfer.py` に転送接続を実装した。
元moduleの変更なしと、execute・remote_apply・転送先制約のbytecode一致を確認した。
新contextの検査、実builderで作った合成planの転送、転送中の破損、通信失敗時の予約保持・無再試行を含む追加22件がWindowsで42.35秒で通過した。
Linuxでは既存50件と合わせた72件が7.11秒で通過し、[sourceとログ](data_tile_validation_2026-10-17/condition_transfer_native_v1/accepted.json) を保存した。
SSH・scpは結合fixtureで置き換えており、本番の全群転送は未実施である。
本番入口は `transfer.py --plan <固定したtransfer-plan.json> --plan-sha256 <外部hash> --destination <クラスタworkspace直下の未使用directory> --record-dir <未使用local記録先> --execute` である。
外部hashを固定した完全なcontextが作成された後に限って実行し、失敗時は同じ記録先や転送先へ自動再試行しない。
