# DGX batch 0の回収完了とbatch 1の開始

2026-10-19 22:38 JST時点で、DGXのC0T2 batch 0の20 groupを回収し、次の20 groupの実稼働を確認した。
これは全768 group中の20 groupの暫定後処理であり、条件全体の科学集約が完了したものではない。
正式な低ノイズ比較は引き続き4/12条件である。

## 回収した結果

対象は `(0,2,0,0,0)`〜`(0,2,0,0,19)` の固定20 groupである。
同じkernel・初期化のreplicate 0〜19に当たり、他の172 replicateや他のkernel・初期化の結果を代替しない。
全1760行、診断46560件と対応するACFを保持した。
infrastructure失敗は0 group、区間未取得は0行だった。
診断flagは1760行すべてにあり、1044行は未定義診断を含んだ。
これらは複数のwindow・chain数・ladder・誤差法を含む設定行の件数であり、1760回の独立試行を意味しない。
flagや未定義行を分母から除外しない。
この途中結果からbias・RMSE・被覆・推奨設定の結論は出さない。

元input archive、export manifest、固定source、全入力payloadとmetadata、全設定、出力marker、診断とACFの対応を、配置済みreaderで検証した。
親側へ転送後も全89 memberのhashと集合、親binding、reader hash、group censusを照合した。
転送の前後でremote archiveのhashが一致することも確認した。
source変換後の数値推定やACFをここで再計算したと主張せず、保存結果の構造・provenance・完全性の受理として記録する。
全sampling終端、元環境のtrace監査、独立referenceとの結合はまだ必要である。

## 生データと時間

親側のarchiveは `docs/wp/data_portable_bar_2026-10-19/dgx-collection-v1/outputs.zip` に保存した。
サイズは247250501 bytes、SHA256は `4be7eef5cb9639d3330de1b0b289b96f1c7260f37960156a71466ab1deaac7cd` である。
[transfer-verification.json](data_portable_bar_2026-10-19/dgx-collection-v1/transfer-verification.json) のSHA256は `f5ed26377a4c02410a74cfeccf81e85553f3b9fc31316cbf99114f31a12a516e` である。
元input archiveは [投入報告](portable_bar_postprocessing_result_2026-10-19_ja.md) の固定hashに対応し、remoteと親側の両方に残す。
archiveはraw解析JSON、数値ACF、marker、実行intent、source、親binding、reader、検証reportを含む。

producerが記録したbatch処理時間は2063.13秒で、groupごとの記録は1698.55〜2062.07秒だった。
この時間は入力の事前転送や初期展開を含む全工程の時間ではない。
本処理の実測として保存し、異なる条件のcluster jobとの速度順位には使わない。

## 自動引継ぎと次batch

controllerはbatch 0の終端、回収、親側の再検証を終えてからbatch 1を起動した。
batch 1の親PIDはDGX上の519556、接続を維持する親側SSH PIDは33224である。
20 workerがそれぞれ約99%のCPUを使い、予定20 groupを処理していることを実観測した。
batch 1のgroupは `(0,2,0,0,44)`〜`(0,2,0,0,63)` であり、batch 0との重複はない。
同じhostに2 batch分の数値workerを並べていない。
laboのbatch 0とclusterの2jobは別途継続する。

batch 1の回収準備は、起動済みの実行intentを読み、そのhash・runtime・source・group集合を親側へ固定してから行った。
配置したreaderはbatch 0と同一である。
後続batch用transportは、終端時と転送後にも固定した実行intent hashを確認する。
実gateを呼んだ時点では `terminal=false, collector_executed=false` であり、batch 1の回収は未実施である。
追加したtransportと関連する受入は13 passed・0.97秒だった。

後続batchの回収scriptは `output/collect_portable_bar_later_once_v1.py dgx 1` である。
起動済みのlabo batch 1について同じ準備を行う場合は `output/prepare_portable_bar_later_collection_v1.py labo 1` を使い、起動前のbatchへ実行済みのbindingを作らない。
controllerはbatch 0の回収とbatch 1の起動までを担当し、batch 1の回収はこの後続transportで行う。
全設定の校正・残る748 groupの処理・正式集約は引き続き未完了である。
