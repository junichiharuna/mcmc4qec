# DGXの全window後処理：batch 1の回収

DGX batch 1の20 group `(0,2,0,0,44..63)` は正常に終端し、自動controllerが生データを回収した。
回収時に入力・出力のhash、実際のexecution intent、source、環境、group集合、結果構造を検証した。
数値の再計算による一致検証を実施したという意味ではない。
全1760行、診断46560件、ACF46560配列があり、infrastructure failureと区間未取得は0だった。
診断flagは1760行すべてに存在し、未定義診断を含む行は1088行だった。
これらを集計の分母から除外しない。

producerが記録したbatch wall timeは2138.252605秒であり、同一条件でのクラスタとの速度比較ではない。
回収archiveのSHA256は`4c0e94f86d41cb9cbac75edc4d6d87ea013de20d061e6d97d85e3c9a6e8a0f7b`である。
生データは`data_portable_bar_2026-10-19/dgx-batch1-collection-v1/outputs.zip`に保存した。
構造・provenance検証の結果は同階層の`transfer-verification.json`、件数集計は`data_portable_bar_2026-10-19/dgx-batch1-collected-summary-v1.json`にある。

controller PID 40396は回収の検証後にDGX batch 2を起動し、local SSH PID 39216を保持している。
batch 2の実execution intentに結び付けた回収設定も作成し、`dgx-batch2-collection-preparation-v1.json`に保存した。
batch 2の回収自体は未実施である。
batch 3は必要な未予約入力がまだ揃っておらず、23:11 JST時点では予約も起動も行っていない。

batch 0と合わせて40 groupを回収したが、予定する全768 groupと全192 replicateの集約は未完了である。
sampling全体の終端、元環境でのtrace監査、独立referenceとの結合を完了していないため、bias・被覆の最終結果とは扱わない。
正式比較の完了数は4/12のままである。
