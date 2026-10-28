# 親sourceのalias照合修正の独立レビュー

全12workerの正常終端後に停止したmerge request準備について、metadata・sourceの読取だけで原因と修正範囲を確認した。
このレビューではローカル試験・科学計算・ジョブ投入・worker原本の変更を行っていない。

## 原因の独立確認

クラスタ上の親環境原本SHA-256は `8e069c1137ccad9415edf3b5d296184e326722cc2a514d0b67ce76b52abd7a6f`、front-v5 manifest原本は `d3386369d998069a428504d828f40d8dacf44b868ee164711ceeabb1f5125c53` だった。
manifestの53 sourceと親環境の93 sourceを比較し、直接のpathキーで一致しない項目は `tile_low_noise_staging.py` の1件だけだった。
親の宣言aliasは `$HOME/workspace/mcmc4qec/20261018-tile-low-staging-control-v2/cluster_scripts/tile_low_noise_staging.py` である。
承認済みresolved targetとmanifestのpathは、ともに `$HOME/workspace/mcmc4qec/20261018-tile-low-staging-v1/cluster_scripts/tile_low_noise_staging.py` だった。
両宣言のSHA-256は `d2595162fb7e9fe02ca2a89d292cece30e86a545f8a06dc8b0d6cb142f9ac9ea` で一致し、実symlinkのresolve結果も同じtargetであることを確認した。
この原本hashは識別子を置換する前のクラスタ原本を指す。

## 修正の境界

`output/low_parallel_recovery_merge_v7/contract.py` の差分はpure helper追加と従来の包含照合1箇所の置換だけである。
直接の宣言pathがある場合はそのhash一致を必須とし、誤った直接hashを別aliasで迂回しない。
直接キーがない場合だけ、親環境の明示されたresolved targetがmanifest pathと完全一致し、対応する全宣言hashが一致することを要求する。
同じhashだけを持つ別path、欠落したresolved宣言、矛盾したaliasは受理しない。
既存の `proof.track` による宣言path・hash・承認targetの検査は比較の前に残っている。
baseline/effective source map、各workerの元manifest・条件・source・job世代に対する検査も変更されていない。
`merge.py`・`build.py`・`control.py` はv6との実SHA比較で同一bytesだった。
`integration.py` はこの限定差分を元の固定sourceから再生成する規則だけを追加し、元workerや数値結果のpinを書き換えない。

静的レビュー時のcontract SHA-256は `61b253e08953a9319fec71ca2057f87b49805e8ef74dea5ad54ac4d912f60670`、integrationは `aaee82b38690db798c8de73a7a398a8abc1781b6910797c57591d06a8e5c9766` である。
静的レビューでblockingとなる指摘は残っていない。

## 実行確認の範囲

PBS受入265647はF/exit 0・run count 1で、25試験が18.63秒、PBS walltimeは20秒だった。
修正の16例と従来の統合9例が実行され、元の24行比較・worker受入・hash phase・allocation guardの受入を含む。
取得したreceiptが列挙する12個の証跡ファイルを独立にhash照合し、全て記録値と一致した。
`sources.json` のcontract・integration・追加試験sourceのpinは、静的レビュー対象と一致した。
この試験はsynthetic fixtureであり、実production入力を使用していない。
受入原本SHA-256は `65354f96017a33eb898919667e3371464ad18333432810bc752efe7c15a0f739`、source mapは `72a9117634881d17bdf139ff020380b25c87dd743db01d80a57df91b1158bdc5` である。
原本は `output/low_parallel_recovery_merge_v7/parent-alias-merge-tests-v1-evidence/` に保存され、これらのhashは公開用に書き換えたJSONのhashではない。

元の失敗箇所を含むactual requestのnative準備確認265648はF/exit 0・run count 1で、PBS walltimeは10秒、CPU timeは9秒だった。
取得receiptが列挙する17個の証跡ファイルを独立にhash照合し、全て記録値と一致した。
実行されたprobeのSHA-256 `43707e19e2c9e43bfe524489760261336c7d29ab2231b6913340e9cc460d8841` は事前に読んだsourceと一致した。
元のfailure/config/requestを固定し、元12workerのterminal・submission・script・indexを確認した上で、実builder・新contract.inspect_request・元control.prepare/preflight・実execution CLIのinitial・native bootstrap・engine.validateを通す経路だった。
新requestは元requestからrecovery policyへの参照だけを変更したことを検査し、元parent環境とmanifestを維持している。
受入原本は `42f7da2047b5d2e23b6564c05f43e414056b454e877fcea5b44f37bc67212c33`、実終端原本は `5d4f268ad09239411fe63cec0a00f6a02e92e2ec0c2710f18a2d8c0e9bd03c98` である。
小原本は `output/low_parallel_recovery_merge_v7/parent-alias-merge-native-v1-evidence/` に保存されている。
実CLIの `-i --help` に伴う `SystemExit: 0` の表示はあるが、その後のnative結果1件と正常終了が必要条件になっており、失敗を成功として読み替えていない。
workerのvalues・raw trace・本番mergeは実行対象外で、深いworker受入と科学的検証の完了はfalseのままである。

この限定されたalias修正と実request準備経路について、独立レビューのblocking指摘はない。
pure helperだけの成功をactual request準備や科学的なmergeの完了とは扱わない。
本番merge・全条件比較・独立計時・最終報告の完了を、このsource修正の受入から主張しない。
