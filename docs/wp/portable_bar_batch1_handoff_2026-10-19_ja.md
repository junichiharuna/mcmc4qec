# 次の44 groupの配置と自動引継ぎ

2026-10-19 22:25 JST時点で、C0T2のbatch 1を両PCへ配置し、batch 0からの引継ぎcontrollerを起動した。
実計算は引き続きbatch 0のDGX 20 worker・labo 24 workerであり、batch 1はまだ起動していない。
clusterの265334と265338もR・run_count 1で、要求node数は合計2のままである。

## 入力と処理条件

samplingの完了markerがそろった92 groupを観測し、そのうち事前の固定順序で次に当たる44 groupを取り出した。
batch 1は `(0,2,0,0,44)`〜`(0,2,0,0,63)` をDGX、`(0,2,0,0,64)`〜`(0,2,0,0,87)` をlaboへ割り当てる。
元の入力metadataと全payloadを確認してからexportし、各PCへ転送後にarchive・driverのhashを照合した。
数値sourceはbatch 0と同一で、全window・chain数・burn-in・ladder・bootstrap条件を変更していない。
groupを推定値・診断値で選別していない。

DGXの入力archive SHA256は `beafbd345b8560ca0356a2341755cd1f37b23bb44d8d367f3c5951f879a6d0e8` である。
laboの入力archive SHA256は `45aa2b988267e704b50190c657de3b66702cb2652b0b5473ad1ebdf8d21175d1` である。
cluster上の原本は `/home/user/workspace/mcmc4qec/portable-bar-c0t2-dgx-batch1-v1/inputs.zip` と `portable-bar-c0t2-labo-batch1-v1/inputs.zip` に残す。
各PCの配置先は既存のplatform root以下の `portable-bar-full-batch1-v1` である。
親側にも `output/portable_bar_c0t2_dgx_batch1_v1.zip` と `output/portable_bar_c0t2_labo_batch1_v1.zip` を保持する。

## 引継ぎの条件と稼働状態

[小仕様](portable_bar_handoff_spec_2026-10-19_ja.md)に従い、hostごとに「batch 0の終端 → 結果回収 → 親側archive再検証 → batch 1起動」の順で進める。
そのため、同じhostへ2 batch分の数値workerを重複して起動しない。
記録済みsampling失敗は保持し、infrastructure失敗のあるbatchやprovenance不一致の場合は次へ自動的に進めない。
通信timeoutは未確認として同じ元processを再照会し、元processが消えて終端記録もない場合はartifactを調べるためcontrollerを停止する。
collectorの応答が曖昧な場合も、自動的な二重実行をしない。

controllerのローカルPIDは34240で、Windowsのprocess一覧でも生存を確認した。
両hostのcontroller予約と最新観測を `*-handoff-controller-v1.json`、`*-handoff-observations-v1.jsonl` に保存する。
最新の観測では、DGXの親PID 468606とlaboの親PID 15892がともに生存し、batch completionは未作成だった。
batch 1の起動intentも未作成であり、計算開始を主張しない。

controllerが生存している間は、別の親側processからbatch 0のcollectorやbatch 1のlauncherを重ねて実行しない。
controllerのscriptは `output/portable_bar_handoff_v1.py`、実行tool sessionは55176である。
laboの現在のbatch 0を支えるSSHは、引き続きローカルPID 40784・tool session 40998である。
既存の計算や接続を停止・再起動していない。
batch 1もSSH接続を維持する方式で実行し、起動した場合に `*-batch1-handle-v1.json` へ新しいSSH PIDを記録する。

## 検証と残作業

引継ぎを含む関連6 test fileは51 passed・3.31秒だった。
終端前、転送未検証、失敗batch、host/hashの不一致、既存起動intent、次groupのすり替え、元process欠落を扱う受入を含む。
この時点では正常な全window batchから次batchへ進む実データ経路は未実行であり、実際の終端・回収時に確認する必要がある。
小仕様・source・テスト・実行ログは [証跡directory](data_portable_bar_2026-10-19/) の `handoff_sources_v1` に保存する。
`*-batch1-prepared-v1.json` は配置完了の記録であり、計算完了の証拠ではない。

配置した累計88 group以外に680 groupが残る。
batch 1以降の結果回収、残るgroupの処理、全sampling終端・trace監査・referenceとの正式集約は未完了である。
正式な低ノイズ比較は4/12条件のまま、公開候補も据え置く。
