# 親source alias修正後のcontroller再開レビュー

`output/low_parallel_flow_v9` の変更を、元のflow v8 sourceと比較した。
このsource版が新しいcontroller v10設定を使って再開する構成であり、既存workerやtailのsource版を変更するものではない。
レビューではローカル試験・科学計算・本番起動を実施していない。

`migration_delta` は新設定を旧設定へ復元して完全一致を要求する。
許される変更は承認済みmerge contractとintegrationの2pin、predecessor、controller journal、merge request root、および明示migration記録だけである。
科学入力、worker preparation、元jobとsource、物理node policy、merge出力先、acceptance先、tail runner/configは同一に保たれる。

`migration_record` は旧エラーの内容・partial request/policy・順序付き12件のfinished記録・元terminal descriptor pinを結ぶ。
旧controllerが停止したことはPIDとstart ticksで確認し、PIDの再利用を区別する。
merge・acceptance・旧v9名のhandoff・tail journal・tail job rootが未作成である場合だけ、今後の出力先として継承する。
旧requestの途中結果は保存し、新request rootを使用する。
handoffには新flow設定とmigrationのpinを追加し、旧v9名の未作成pathを新controllerが使用した来歴を残す。

worker採用では元job IDを必須とし、terminal descriptorの再生成を除去して既存pinとの一致だけを認める。
`require_new_submission` は常に例外となるため、新workerの投入は許可されない。
元のledger・script・prepared・manifest・環境の検査は維持されている。
handoffの科学的な成功条件、selection、独立計時・被覆保証に関するfalseの扱いは変更されない。

native確認用の追加処理はPBS内で元12terminalを採用し、merge/requestの出力先2箇所だけをshadowに投影してprepareまで実行する。
worker submit・merge submit・terminal recaptureを禁止し、元worker valuesのopenを拒否する。
終了時に元configへ戻し、productionのjournal・merge・requestが未作成のままであることを確認する。
この確認は科学的なmergeやworker値の深い受入を実行した証拠ではない。

静的レビュー対象flowのSHA-256は `0b65f945ff58924dcf621a3a512a2708e4a8943191b20189425779740ebaab8e`、build_configは `12cd10846c7b934570478f75f492cf51d5fee49d0987e251b2bec6cf5a50d564` である。
静的レビューでblockingとなる指摘は残っていない。
以下は、その後に確認したPBS受入結果である。

265649はF0・run_count 1・walltime 1秒で、元tailのhandoff受理2件を加えた18件が0.020秒で成功した。
265650はF0・run_count 1・walltime 21秒で、実migrationを伴うconstructor、既存12terminalの採用、shadow出力先でのprepare_mergeが成功した。
両accepted原本のSHA-256、fixtureの4source全件、新config・migration・実flowのpinをクラスタ原本と独立照合した。
native workerのSHA-256は `1e0be64a8fd0c50b5237fdb277716f21d83b1466072b9f03aacf38a9943dcdac` で、レビューしたローカルsourceとも一致した。
テスト実行は担当者のqsubで行われ、本レビューではローカルテストを実行していない。

| 原本 | SHA-256 |
|---|---|
| 265649 accepted.json | `aad6fd2b73b553863e786d8c60c994583d8e2219b56bd340dc480d9c05353016` |
| 265650 accepted.json | `314132344cbf8be0178297b45d00d728908e680d6045a46ebf6d2adaf2020243` |
| actual v10 flow-config.json | `1263c2ed2264a19c69b0a29c692cf9277fb402d1d94f578364b73b94ab1046da` |
| migration.json | `ef9fa0b43c8913c2c5e1a51cd16f7ede81437d939b52d86fef7a30860549b726` |

取得済みの小証跡は `output/low_parallel_flow_v9/fixture-acceptance.json` と `native-acceptance.json` に保存されている。
上表のhashは、取得時の再直列化JSONではなくクラスタ上のaccepted原本・config原本・migration原本を指す。
本番の科学merge、worker valuesの深い受入、独立計時、最終報告はこの受入の実行範囲に含まれない。
この範囲で、移行実装と実入口の受入にblockingとなる指摘は残っていない。
