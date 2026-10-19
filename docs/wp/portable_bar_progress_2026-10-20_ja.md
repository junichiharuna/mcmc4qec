# Portable BAR：全設定照合と最終集計の準備

2026-10-20 00:04 JST 時点の追記であり、固定した公開候補 `47ef1b6` の変更ではない。

## DGXの全設定照合

事前指定したC0T0 group `(0,0,0,0,0)` について、4／16 chain、burn 600／6000、保存600／6000／60000、coarse／fine ladder、block 32／128／1024とcross-chainを含む88設定を比較した。
保存済みの元環境の結果に対し、88行・1536診断・1536 ACF配列が既定のrtol=1e-10・atol=1e-12で一致し、離散flagと未定義位置も一致した。
decoder factoryの呼出しは0回であり、後処理だけの照合である。
DGXの実行時間は923.23秒で、同時負荷を制御した速度benchmarkとは扱わない。
回収前後のremote hashと転送後のhashを検証し、保存値をローカルで再比較した。
ローカルでは推定計算を再実行していない。
証拠は [照合結果](data_portable_bar_2026-10-19/dgx-full-parity-terminal-v1.json) と [回収後の比較](data_portable_bar_2026-10-19/dgx-full-parity-collection-v1/verification.json) に保存した。
これは1群の後処理検証であり、C0T2の科学cohortへ追加せず、bias・被覆や全入力での一致の保証とは扱わない。
Labo側の全設定照合は、remote PID 15784の生存とCPU使用を確認しており、完了は未確認である。

## 実cohortの回収

DGX batch 2の20群を追加回収し、batch 0～2の3 archiveを再検証した。
固定された全768群・67584行に対し、回収済みは60群・5280行、未回収は708群・62304行である。
回収済みのflagged行は5280、診断未定義行は3192、区間未取得とinfrastructure failureは0であり、flagや未定義を理由に除外していない。
診断とACF配列は各139680件である。
これらの数は複数設定を含む行数であり、独立seed数として扱わない。
証拠は [60群の途中index](data_portable_bar_2026-10-19/first60-cohort-inventory-v1.json) に保存した。
batch 3はremote PID 589620で実行中であり、次のbatch 4は固定host割当を守った20群の入力配置とhash照合が完了した。
batch 4のcontrollerはbatch 3の実PIDと終端を確認してから回収・起動するため、同一hostの本計算を重複起動しない。
Labo batch 0はremote PID 15892で実行中であり、まだ回収済みとして数えていない。

## 最終集計の実装と残作業

全768群・192 anchorの監査を結合する制御処理と、PBS環境で排他的に最終レポートを書く処理を実装した。
成功groupとinfrastructure failureを区別し、失敗groupの88設定も未取得行として分母に残す。
参照条件・native profile・raw reference監査の取り違え、入力やsourceの変更、入力directory内への出力、既存出力への上書き、非PBS環境を拒否する。
全体制御の9件とレポート境界の22件を合わせた31テストが15.15秒で成功した。
全体制御テストはI/Oを置き換えたfixtureであり、実cohortの監査を済ませたという意味ではない。
実artifactのgroup結合は別の11テストで検証している。
実archiveから全cohortを供給し、hostごとの全設定照合を必須にするproviderは未実装である。
全sampling、元native環境のtrace監査、独立referenceとの最終結合も未完了であり、名目95%被覆や母集団RMSEを保証しない。

## 再現

追加テストは `python -m pytest output/test_portable_bar_final_join_v1.py output/test_portable_bar_final_report_v1.py -q` で実行した。
使用環境は `.venv-experimental-optional/Scripts/python.exe` である。
回収後の検証scriptと追加テスト・ログは `data_portable_bar_2026-10-19/final_join_sources_v1/` にhash付きで保存した。
scriptの相対importを保つには、保存したファイルを元の `output/` 配下へ配置し、既存のarchive・cluster scriptと同じ環境で実行する。
回収・途中indexのscriptは排他的出力を持つため、既存の保存先へ再実行しない。
