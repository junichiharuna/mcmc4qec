# 完了した 3 条件の限定的な事前検査

2026-10-25 に、index 6・7・8 の完了済みジョブ 265571・265572・265573 が保存した値について、後段の全 12 条件の受理とは別に、入力形式の不整合を早期に見つける限定検査を行った。
検査ジョブ 265595 は `qsub` で投入し、2 CPU・4 GB・10 分の上限を指定した。
実際には 10 秒で `F`・終了コード 0 となった。

元の prepared・manifest・環境・実行コードの pin をそのまま使用し、変更していない `engine.validate` と `engine.check_rows` を PBS 内で呼び出した。
3 条件とも、順序を含む座標、各条件 2 行の epsilon、352 設定の候補 census、192 replicate の固定分母が既存 validator を通った。
元の values の hash、実行開始・完了記録、保存済み終端記録と新しい `qstat` の成功状態も照合した。
この範囲では形状またはメタデータの不一致を検出しなかった。

検査中に hash を確認したのは source・環境・metadata・保存値の計 263 ファイルである。
値が参照する全入力ファイル約 73.8 万件・約 42.7 GB は走査せず、`e.accept_worker` も呼び出していない。
科学値の算術の完全な再検証、科学計算の再実行、全 12 条件の merge、worker の完全受理は行っていない。
receipt でも `worker_envelope_accepted`・`full_worker_acceptance_performed`・`scientific_value_arithmetic_revalidated`・`all12_merge_performed`・`production_selection_validated` をすべて false とした。
この検査は後段本来の全入力 hash 照合と完全受理を代替せず、bias・被覆や科学的精度の保証でもない。

元の完了記録・values・実行中の他ジョブには書き込んでいない。
probe と配置コードは private `output/completed_worker_shape_probe_v1/`、投入・終端・結果の原本は private `output/completed_worker_shape_acceptance_v1/` に保存した。
