# tile固定prior利用例の明示ladder受入

[小仕様](tile_example_target_cli_spec_2026-10-25_ja.md)、[契約テスト](../../tests/test_tile_fixed_prior_example_cli.py)、[利用例](../../examples/workflows/tile_capacity_fixed_prior.py)の順に変更した。
追加CLIは `--ladder P0,P1,...` のみで、末尾の物理確率を目標pとする。
省略時は既存size別ladder・目標・sampling予算・出力schemaを維持し、library API・公開既定・稼働中の本校正sourceは変更していない。
decoderはbit-flipでは目標p、depolarizingでは2p/3で1回構築し、anchor・独立MC・全BAR rungへ同じProblemを渡す。

## PBSで確認した範囲

共有2物理node gateを通してqsub265640へ投入し、F/0・walltime10秒を確認した。
新しい独立stageに例と受入testを置き、既存native package sourceのpinを実行前後で照合した。
このPCではPython実行・テスト・数値計算を行わず、小さいreceipt・stdout・stderrだけを回収した。

| 対象 | 結果 |
|---|---|
| CLI契約 | 23 passed、pytest表示0.16秒。size別省略値、明示末尾target、不正値・順序・点数の拒否、bit/depolarizingのprior・モデル・同一Problem共有を確認。 |
| 既存default tile workflow | 1 passed、pytest表示2.66秒。既存出力schemaとfixed decoder metadataを維持。 |
| tile72 bit-flip実CLI | exit0、2.229秒。目標0.025、prior0.025、fixed_failure、全rungのdecoder metadata一致。 |
| tile72 depolarizing実CLI | exit0、3.354秒。目標0.025、sector prior2×0.025/3、fixed_failure、全rungのdecoder metadata一致。 |

実CLIはいずれも `--quick --seed 7 --initialization logical --ladder .1,.07,.05,.03,.025` と各noise指定を使い、各60秒の上限内に終了した。
実nativeのtile288再実行や目標0.01の数値検証は今回行っておらず、両size・目標0.01の結線は契約テストの範囲である。
低ノイズのanchor失敗数・隣接rungのoverlap・混合は利用者が別途確認する必要があり、ここでの成功を精度・95%被覆・推奨設定の校正としない。
全12条件の正式selection・独立計時・最終reportは、このCLI受入とは別の未完了工程である。

## 保存と利用

原本stageはクラスタworkspace相対 `20261024-c3t2-index-relocation-v1/pipeline-submissions/tile-ladder-cli-acceptance-v1` である。
回収したprivate小証跡はlocal `output/tile-ladder-cli-acceptance-v1-evidence/` にあり、原本acceptedのSHA-256は `fffd74deb1afb34fa4e69e2a2ed7fb5c0f3dc7b28d85022b1790ba20d5c251a5` である。
[選択した受入証跡](tile_example_target_cli_acceptance_2026-10-25.json)には例・tests・native packageのsource pin、依存版、実行結果、元出力hashを保存した。
この小JSONはpathを相対化した選択記録で、記載の原本hashは置換前のprivate原本を指す。
大きいBAR結果やraw traceをローカルへ回収していない。

低pを指定する構文例は[examples README](../../examples/README.md)に追加した。
その目標0.01のladderは接続方法の説明であり、今回実行した目標0.025のsmokeや正式な低ノイズselectionと混同しない。
この変更と受入はv8時点の共有snapshotより後であり、そのarchiveへ収録済みとは扱わない。
commit・push・公開uploadは行っていない。
