# 残る5条件のPC割当て

対象はC1T1/C1T2/C3T0/C3T1/C3T2とし、稼働中C1T0の割当ては変更しない。
各条件の全192 replicate × 2 kernel × 2初期化、計768群・67,584予定行を保持する。
固定済みnative reference configと元クラスタのmanifest・profile・fixtureの実byte一致を要求する。

処理時間の根拠には、外部hashで固定済みのC1T0 DGX batch9/10/11、Labo batch0/1の回収証跡と実completionを使う。
出力ZIP全体とcompletionのhash、accepted、群数を照合する。
各hostの平均batch時間を求め、DGX 20 worker・Labo 24 workerを維持する。
各kernel・初期化についてDGXへ先頭n replicate、Laboへ残る192−n replicateを割り当て、n=1〜191を列挙する。
最終の不完全batchも平均の完全batch時間を要する保守的モデルで、両hostの予測処理時間の最大値を最小化し、同値の場合は小さいnを採用する。
このモデルは転送・起動待ち・監査時間を含まず、別の物理誤り率・noiseでの速度や終了時刻の保証ではない。
割当ては科学結果によるseed選別や設定選択には使わない。

受入は既存のbatch contractによる全群の重複・欠落検査、各stratumのhost別同数、初期cohort indexの未回収768群・観測0行・予定67,584行の実検査とする。
元config、時間根拠、全候補の比較、割当て、初期index、使用sourceをhash付きで保存する。
これは配置計画の準備であり、入力export、native reference実行、PC parity、数値worker起動を受理した証拠とは扱わない。

## 実施結果

2026-10-20 21:51 JSTまでに、5条件すべての実native metadata照合と既存contract・cohort indexによる受入を完了した。
選択された割当ては各stratumでDGX162 replicate・Labo30 replicate、各条件全体でDGX648群・33 batch、Labo120群・5 batchとなった。
平均batch時間はDGX911.55秒、Labo5307.77秒で、モデル上の最大処理時間は30,081秒だった。
これは現在条件の実測から作った割当て比較値であり、新条件のETAとしては用いない。
5条件とも初期indexは未回収768群・観測0行・予定67,584行で、数値実行・qsubは行っていない。
生成script、時間根拠、191通りの候補、元configとmetadata、割当てと初期indexを[57ファイルのmanifest](data_tile_validation_2026-10-17/planned_condition_assignments_v1/manifest.json)に保存した。
manifest SHA-256は `6fc596b866739d40e5555e6a6da089459e6ba783b0504b0a37a87383589d3934` である。
再現scriptは同manifest内の `sources/output/planned_condition_assignment_v1/prepare.py` に保持し、既存保存先への上書きは拒否する。
今後の入力exportでは各条件のanchorとsampling partition 0/1すべての実PBS終端を検査し、C1T0の単一sampling job証跡は流用しない。
