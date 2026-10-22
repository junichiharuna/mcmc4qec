# 再割当て後の途中集計・転送・qsub制御の受入

2026-10-20に、固定した再割当てplanに従う途中index、全群限定の転送context生成、転送処理、最終評価用のqsub入口を追加した。
公開候補のpackage・配布物と既存の科学計算helperは変更していない。
再割当て264群の本番配置・起動・回収の自動制御はまだ未完了であり、今回の変更ではその計算を開始していない。

## 契約

[固定planの仕様](portable_bar_remaining_assignment_spec_2026-10-20_ja.md)に従い、全768群・192 seed・67,584行と、元担当・実際の実行先の両方を保存する。
DGXの元18 batch、Laboの元6 batch、DGXへの再割当て14 batchを合わせた38 batchについて、群の欠落・重複・担当先変更・plan hash変更を拒否する。
全群の終端が揃うまで転送contextの出力先を作らず、infrastructure failureも予定行数の分母に残す。
転送contextはschema 2とし、plan・baseline、両hostの完全parity記録、reference archive、各batchの出力・parent・receiptを個別のhashに結び付ける。
転送処理は既存の排他的な配置先作成、file census、送受信hash照合、曖昧な失敗時の再試行禁止を維持する。
新qsub入口は元環境の全群trace監査と全38 batchのmetadataを要求し、待機中を含む最大2ノード、共有投入lock、投入直前の再検査、実PBS IDと終端の検査を維持する。
これらは制御・metadataの検査であり、最終providerによる生配列、復号環境、PBS、sampling、独立referenceの監査を代替しない。

## 実行した検証

| 対象 | 結果 | 範囲 |
|---|---:|---|
| 混在index | 6 passed / 2.68秒 | 固定全群の割当てと既存snapshotの保護 |
| 転送context生成 | 18 passed / 33.61秒 | 全38 batch、失敗を含む分母、欠落・担当・hash不一致の拒否 |
| 転送 | 24 passed / 1.22秒 | byte転送、排他的配置、破損・部分転送・plan不一致の拒否 |
| qsub制御・Windows | 31 passed / 17.68秒 | metadata、上限2ノード、二重投入・曖昧な応答・終端不一致の拒否 |
| qsub制御・クラスタLinux | 31 passed / 12.98秒 | 同じテストを配置先で再実行、実qsubは呼ばない |

転送contextテストの初回は18件成功したが75.59秒で1ファイル60秒の上限を超えたため、そのログも保存した。
専用テストで確認済みの割当て導出をfixture内で何度も検証していた部分を一度にまとめ、metadata検査の内容を維持した再実行で33.61秒となった。
転送テストの初回は、planとbaseline追加後のSCP呼出し数の期待値が旧形式のままで2件失敗し、期待する転送数を直して24件成功した。
実際の392群の途中indexから全群用contextを作る試行は、`Full 768-group assigned inventory is not complete` で拒否され、出力先は作成されなかった。
mockによる転送とqsubの試験を、本番の全群転送・投入の成功とは扱わない。

## 回収済みの実データ

[途中index](data_portable_bar_2026-10-19/mixed-collected-snapshot-20261020-v1.json)は392群回収済み・376群未回収で、観測34,496行・未回収33,088行を合わせて予定67,584行の分母を保持する。
SHA-256は `08b7da33a422b53d030dad90963a5ca4b1200d3c6742ee4ba55e76672686f1f2` である。
観測34,496行はすべて診断flag付きで、21,144行に診断未定義があり、区間未取得とinfrastructure failureは0である。
診断flag・診断未定義を評価対象から除外しておらず、この途中indexは最終bias・RMSE・被覆の検証ではない。
Labo batch 2の24群の回収後にbatch 3が開始し、batch 3の回収準備とbatch 4への自動引継ぎ待機を設定した。

## 保存先と再現

helper・テスト・初回失敗を含むログ・固定plan・途中indexの58ファイルを [source保存先](data_portable_bar_2026-10-19/mixed_execution_controls_sources_v1/manifest.json) にまとめた。
manifest SHA-256は `3c92eede73d4a65a5d59f0081a72590ee05b713a8f1aef3972d69f626e1d6e86` である。
manifestに示すrepository headに各ファイルを相対パスどおり復元し、外部source hashを確認してから、`output/test_index_portable_mixed_collected_v1.py` と `output/test_portable_bar_mixed_{distribution,transfer,qsub}_v1.py` をpytestで実行する。
数値環境は既存の `src/` と `cluster_scripts/` を使用し、各テストの実行に新しい科学計算は必要ない。
クラスタ配置先は `/home/user/workspace/mcmc4qec/20261020-portable-mixed-controls-v1`、配置archive SHA-256は `481189463841d425f6bfb577cba62ca959c6bbb156f0569b312a6ef9a1a84751` である。
[配置receipt](data_portable_bar_2026-10-19/mixed-controls-stage-receipt-v1.json) と [Linuxテストログ](data_portable_bar_2026-10-19/mixed-controls-linux-qsub-tests-v1.log) を保存した。
本番全群の転送context・資源設定・qsub投入は未実施であり、今回の配置receiptも `qsub_executed=false` である。

## 継続する作業

再割当て264群の配置・本番config・直前batch終了後の起動・回収を接続し、既存DGX batch 17と重ならず最大20 workerで実行する。
全768群が揃った後に新contextで転送し、C0T2の元環境trace監査が成功してから最終評価をqsubで投入する。
2026-10-20 08:03 JSTの実qstatではC0T2回収265345とC1T0 sample0の265343はともにRであり、最大2ノードを維持している。
公開候補の準備と数値検証の完了を区別し、混合・名目95%被覆・低ノイズ精度の保証は追加していない。
