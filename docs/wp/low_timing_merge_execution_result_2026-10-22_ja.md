# 分割結合jobの実行と正常終了受理：実装結果

[小仕様](low_timing_merge_execution_spec_2026-10-22_ja.md)に従い、PBS内の結合実行と正常終了後の受理を `output/low_timing_merge_execution_v1/` に実装した。
実行中の結合結果は正式な計時入力とせず、qsub応答・台帳・script・開始時と終了前のPBS状態・F/exit 0・source・結果hashを照合してから選択候補を受理する。
受理時には大規模rawを再走査せず、結合job内で検証した固定snapshotと出力byteを対象とする。
将来のrawファイル不変性、独立計時の実施、精度、名目95%被覆は保証しない。

実行予算は1 CPU・32 GB・1 node・24時間であり、実測した終了予測ではない。
未終了・異常終了・run_count不一致・host/script不一致・qsub複数ID・結果や完了記録の変更・source変更を拒否する。
観測timeoutは未完了や再投入の根拠にせず、既存の実行記録があれば再実行を拒否する。

22 testは15.13秒、記録付き実行では14.41秒で成功した。
PBSとnative bootstrapと実行フロー中の科学処理はdoubleで検証し、別の統合testでは実combine・設定選択・計時planを小さな人工入力で接続した。
統合testでは24選択行・12 bindingを保持し、既存の計時planを生成できることと、元の未昇格結果を変更しないことを確認した。
初回の統合testはplanの最上位に存在しないfieldを参照して失敗したため、実schemaのselection内のfieldと投入未承認状態を検査するようテストを修正した。
科学的な選択規則は変更していない。

source・テストログ・依存sourceのhashは [low_timing_merge_execution_acceptance_v1](data_tile_validation_2026-10-17/low_timing_merge_execution_acceptance_v1/) に保存した。
accepted.jsonのSHA256は `6f0c08992f3e063d480d16be57e1371b9a8c190611d8d8ec73e852e54ce2f974` である。
テストは元workspaceのsourceを使い、同一byteのsourceを受入資料へ保存した。

本番用request・preparedの作成、共有lock付きqsub投入処理との接続、実クラスタbootstrap、全12条件での結合、後続censusへの接続は未実施である。
この実装結果だけで分割経路全体を実行可能・完了と扱わない。
