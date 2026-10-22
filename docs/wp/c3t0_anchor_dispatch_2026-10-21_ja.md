# tile288 depolarizingのanchorを空き枠で先行実行

## 投入前の判断

00:20 JST時点のクラスタ要求はC1T1 collector265370の1ノードで、もう1ノードが空いている。
C1T0 full監査とC1T1 native referenceは正常終了・受理済みである。
C1T2の既存待機処理はC1T1 full監査の受理を待ち、その生成ジョブはまだ投入していない。
計算資源を有効に使うユーザーの指示に基づき、独立したC3T0のanchor partition 0だけをこの枠で先行実行する。
先行preflight台帳に記録したC1T2優先の実行順から、今回のanchorだけを前倒しする判断である。
既存のC1T2待機処理とC1T1監査処理は変更せず、C3のsampleや他targetを自動投入する処理は追加しない。
この前倒しは事前固定された符号・ノイズ・decoder・seed・sampling設定・resourceを変更しない。
要求は1ノード・96 CPU・32 GB・walltime上限3時間であり、上限を予想終了時間とは扱わない。

## 使用する既存証拠と操作

preflight一覧のSHA-256は `3d5d0f0e77a5b2a54e7ad8c229e273b0826aea2c6a9ca37b9b9da21110892c02` である。
選択したpreflight receiptのSHA-256は `25706663c0f59b88f6297ad029863e86feeccf62b7ccf236264ba428431a684e` である。
既存submit wrapperのSHA-256は `1c916201a1c25e1d4d1578503174e48135af4593700b73eea7f860894660e8a6` である。
read-only確認で、未使用execute・正常preflight・script/resource/production manifestの一致を確認した。
実投入にも既存wrapperを使い、native環境・source・共有lock・Qを含む最大2要求ノード・qsub直前の再検査を維持する。
生成時と同じthread環境はwrapperに含まれている。
操作結果が不明または失敗した場合は、保存intent・receipt・実PBSを調べ、自動で再投入しない。
本書作成時点のqsubは未実施であり、結果を追記する。

## 実投入

既存wrapperのexecuteを一度だけ実行し、`265371.node-PRISM` としてqsubに受け付けられた。
receiptはreturncode=0・ambiguous=false・execute_requested=trueで、固定されたcommandとresourceに一致した。
00:22 JSTの実qstatでは265370と265371がともにRであり、要求は合計2ノードだった。
[実投入とPBS観測](data_tile_validation_2026-10-17/c3t0_anchor_dispatch_20261021_v1.json)のSHA-256は `64360eb8a6a9a03a5cb875e0ed91d80ddf958ac06482c4654ffd91462a2a04f5` である。
元wrapperが保存したintent・実行script・stdout・stderr・receiptは `data_tile_validation_2026-10-17/low_partition_3_0_anchors_0_submission_once_v1_*` にある。
このexecuteは使用済みであり、再実行しない。
00:23時点ではanchor実行中で、sample投入・anchor終端受理・科学的検証完了は未実施である。

## anchor正常終端とsampling前半の判断

anchor265371は00:24:32にF・Exit_status=0・run_count=1で終了し、実walltimeは2分35秒だった。
元のterminal validatorでscript・resource・owner・実job IDと正常終端を検査し、[終端記録](data_tile_validation_2026-10-17/c3t0_anchor_terminal_20261021_v1.json)に保存した。
終端記録のSHA-256は `f87a8f7f1470e6581ffedb456d0e63e16c593c4c901f4c78976e7d9ff24a7844` である。
この正常終了を受け、空き枠で同条件のsample partition 0を追加で進める判断とした。
先のanchorだけという投入範囲を、この1件のsampleへ拡張する。
もう1ノードでは既存の収集・監査を継続できるため、長い独立生成を早く開始して全体の待ち時間を減らす。
実行順だけの変更であり、元の事前固定された計画やseedは変更しない。
選択したsample preflight receiptのSHA-256は `e237d9677a9b89560f39125d071e6e5b9e822f553f94dd34f5fba0d432b34bc5` で、正常preflightと未使用executeを確認した。
要求は1ノード・96 CPU・32 GB・上限21時間30分であり、この上限はETAではない。
この追記時点ではsample qsubは未実施である。

## sample partition 0の実投入

既存wrapperがqsubで265372を投入し、receiptのreturncode=0・ambiguous=falseと固定command一致を確認した。
00:26 JSTの実qstatでは265370と265372がRで、合計2要求ノードだった。
[実投入とPBS観測](data_tile_validation_2026-10-17/c3t0_sample0_dispatch_20261021_v1.json)のSHA-256は `abfa46409c6e76fb8508979be75d363cd416bdb50c4ba439065c5e06c640831f` である。
元wrapperのintent・script・stdout・stderr・receiptは `data_tile_validation_2026-10-17/low_partition_3_0_sample_0_submission_once_v1_*` に保存した。
このexecuteは使用済みであり、再実行しない。
sample partition 1、collector、native reference、BAR、full監査、最終比較は未完了である。
