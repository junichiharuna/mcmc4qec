# BAR独立計時の準備 v1

全4caseの最終監査済み集計から、既存の固定選択規則で20%・10%の候補を選択した。
新しい結果依存の選択規則、診断によるreplicate除外、seed置換は追加していない。
全8条件が候補ありとなり、全てZH・logical初期化・cross_chain・burn 600である。
候補は独立確認の対象であり、推奨設定、母RMSE、名目95%被覆、速度優位の認定ではない。

| case | 目標 | chain | ladder | 保存長 | step/rep | 経験的rRMSE上端 | 点reference被覆/192 | 診断flag/192 |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| 0 | 20% | 4 | coarse | 600 | 19200 | 0.133898 | 162/192 | 192/192 |
| 0 | 10% | 4 | fine | 600 | 33600 | 0.092229 | 165/192 | 192/192 |
| 1 | 20% | 4 | coarse | 6000 | 79200 | 0.120485 | 172/192 | 192/192 |
| 1 | 10% | 4 | fine | 6000 | 132000 | 0.089701 | 171/192 | 192/192 |
| 2 | 20% | 4 | coarse | 600 | 19200 | 0.145160 | 170/192 | 192/192 |
| 2 | 10% | 8 | fine | 600 | 67200 | 0.080930 | 171/192 | 192/192 |
| 3 | 20% | 4 | coarse | 6000 | 79200 | 0.175618 | 168/192 | 192/192 |
| 3 | 10% | 4 | fine | 12000 | 252000 | 0.092164 | 173/192 | 192/192 |

被覆と診断は固定分母のまま保存し、候補選択の点推定精度と区別する。
参考区間全域の経験的相対RMSEを使っているが、その区間を真値の確実な範囲や母RMSEの信頼区間とは扱わない。

`bar_timing_selected_settings_v1.json` のSHA256は `47c0d2c624c5ec56478bf4c5bd47179651a893b2cce424c759f168e1009bd02c` である。
`bar_timing_selection_inputs_v1.json` は独立回収検証済みの4つのrecovery proof hashを外部pinとして固定する。
接続adapterは全member・source・input・PBS・final phaseを照合し、保存precision metricsとaudited report全352条件の一致を確認して既存chooseを使った。
親による独立レビューはblocking findingなしで、受入は13 passed・16.26秒だった。
元のraw rowsの再集計、BAR bootstrap再計算、fresh native probe、全状態の再復号は行っていない。

`bar_timing_plans_v1/` にLinux凍結環境で生成した4caseのcapacity/main manifestを保存した。
元の `20261018-tile-timing-comparison-v1` は読み取り専用で参照し、source・既存成果物を変更していない。
capacityはstage141・96replicate、mainはstage140・192replicateで、各caseの2条件を元のcondition indexのまま保持する。
capacity全768task、本計時全1536taskで、両stageの標本は混ぜない。
初回capacityの既定上限はcaseごとに1ノード・96CPU・340GiB・24時間であり、実測予測ではない。
mainの要求資源は完全なcapacity artifactとnative証拠に基づく既存measured_capacityが受理した場合だけ決定する。

追加seedはstage141が36,096、stage140が72,192、合計108,288件である。
既存全数監査3,855,274件とのunionは3,963,562件になる。
旧SQLite集合DBは削除済みで、保存stream hashから追加seedとのmembershipを照合できないため、unionの全数監査を新しいqsubジョブで行う必要がある。
stage番号の違いから理論的な非衝突を仮定しない。
新seed接続はmanifest/settingsのhash、全case・全stageの過不足、元index、run時CLI転送を検証し、受入36 passed・4.19秒だった。
全数監査とBAR計時のqsubは親agentだけが行い、この準備処理は投入していない。
MC本計時は完了しているが、BARの独立精度確認と独立計時が揃うまで同精度の速度優位は未評価である。

新bundle `20261018-tile-bar-seed-audit-v1` への配備とLinux受入36 passed・0.83秒が完了した。
旧v4から科学sourceをbyte単位で継承し、承認したseed submitter/testと新bundle専用の受入helper/indexだけを差し替えた。
8本のplanは新bundleの `runs/capacity-{0..3}` と `runs/benchmark-{0..3}` に配置し、既存make_planによる再構築一致を確認した。
`runs/seed-census-bar` のprepareとdry-run、PBS構文検査は成功した。
監査予定3,963,562件のうちpilotで1,000件を検査し、予期しない衝突0件・未検査3,962,562件である。
要求資源は1ノード・1 CPU・2 GiB・30分で、既存のshared lock、controller不在、queuedを含む最大2ノード制限を通して親がqsubする。
pilot外挿428.08秒は、旧全数実測約1,475秒より短いため完了予測や保証として扱わない。
配備証拠は `bar_seed_audit_deployment_v1/preparation.json`、独立したローカルarchive/input/output照合は同階層の `independent_preparation_verification.json` に保存した。
この記録時点で追加全数censusとBAR capacity/mainのqsubは未実施である。

その後、親が追加全数censusを265253としてqsubし、PBS25分14秒で正常終了した。
56 namespace・3,963,562件の全数監査、未検査0件・予期しない衝突0件とsource/input/runtime/PBSの結合を確認した。
詳細は `bar_seed_census_evidence_v1/REPORT_ja.md` と同階層の独立検証JSONに保存した。
BAR capacity case0の読み取り専用preflightも成功し、親へ投入用wrapperを引き渡した。
