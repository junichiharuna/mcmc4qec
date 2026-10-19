# batch 2の配置と完了入力からの後続処理

2026-10-19 22:54 JST時点で、DGXの20 groupとlaboの24 groupをbatch 2として配置し、hashを確認した。
数値計算はまだ起動していない。
DGXではbatch 1を観測する引継ぎcontrollerを追加し、laboではbatch 1の起動・実行intentの確認を待つ。

## samplingの生成順への対応

sampling partitionの設定を読み、partition 0は全kernel・初期化のreplicate 0〜95、partition 1は96〜191を生成することを確認した。
後続の連番seedを待つだけでは、完成済みの別初期化のtraceを使えずPCが空くため、[完了入力から選ぶ仕様](portable_bar_available_input_scheduling_2026-10-19_ja.md)を追加した。
元の全768 groupとhost割当、group identity、seed、解析条件は維持する。
未予約の完了入力を元のgroup順に並べて選び、数値結果や診断値を選択に使わない。
まだ生成されていないreplicate 96〜191も予定集合に残る。

DGXのbatch 2は、初期化0のreplicate 88〜95、初期化1の0〜3および28〜35で、すべてkernel 0・case 0・target 2である。
laboのbatch 2は、同じkernel・case・targetの初期化1のreplicate 4〜27である。
DGXでは必要数に満たなかった2回の観測で予約を作らず、133 groupの完了入力を観測した時点で20 groupを選んだ。
laboは130 groupの完了入力を観測した時点で24 groupを選んだ。
選択時の全ready集合と、既存予約のhashを `*-batch2-selection-v1.json` に保存した。
各hostのbatch 0・1・2を照合し、合計132 groupに重複がないことを確認した。
残る636 groupも元の予定に保持する。

## 配置と稼働

DGX入力archive SHA256は `e7ae8b8d59981f5aa1edef4107591c28e02bc5af4b9cafa3f456f20ef0e54d9b`、laboは `78460428108c73b8d75347569243810a884c1e858e0336e4c0edae08215358c2` である。
cluster原本、親側 `output/portable_bar_c0t2_*_batch2_v1.zip`、各PCの `portable-bar-full-batch2-v1/inputs.zip` を保持した。
数値driverはbatch 0・1と同一で、metadata・全payloadを元のloaderで確認してexportした。

DGXの新しいcontrollerはローカルPID 40396、tool session 56827である。
元のcontroller PID 34240は、引き続きlaboのbatch 0から1への引継ぎと、batch 1のSSH接続を担当する。
両者は異なる引継ぎを担当し、同じcollectorや起動を重ねて行わない。
新controllerはDGXのbatch 1の親PID 519556の生存を確認し、終端を待っている。
batch 1の終端・回収・転送後の検証・実行intent hash確認がそろった後だけ、batch 2を起動する。
元process消失、未確認のcollector実行、source/hash不一致がある場合は自動再投入しない。

laboのbatch 1はこの観測時点では未起動のため、batch 2のcontrollerも起動していない。
labo batch 1の実稼働を確認した後、`prepare_portable_bar_later_collection_v1.py labo 1` で前batchの回収bindingを作り、`portable_bar_later_handoff_v1.py labo 2` で同じ引継ぎを行う。
配置済みのbatch 2をもう一度選択・exportしない。

## 検証と再現

関連9 test fileは63 passed・4.76秒だった。
全groupの割当、初期化境界をまたぐ元順序、既存batchとの重複、同じbatchのrecord不一致、入力不足時の未予約、先行batchの実行binding欠落、未確認collectorの再実行拒否を含む。
実際のbatch 2の計算・回収は未実施であり、テスト成功を実計算の完了とみなさない。

後続batchの入力準備には `output/stage_available_portable_batch_v1.py HOST BATCH` を使う。
既存予約があるbatchは拒否し、入力不足なら予約せず戻る。
このscriptは数値processを起動せず、別の引継ぎcontrollerが先行batchの検証後に起動する。
script・テスト・ログ・小仕様は [証跡directory](data_portable_bar_2026-10-19/) の `available_input_sources_v1` に保存する。
公開候補は変更しておらず、正式な低ノイズ比較は4/12条件のままである。
