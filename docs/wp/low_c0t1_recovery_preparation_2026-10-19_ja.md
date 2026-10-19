# C0T1の時間上限に備えた準備

BAR解析265334の観測では、768 group中96 groupの完了markerがあり、最初の完了時刻は2026-10-19 20:58〜21:00 JSTだった。
jobはRで継続しており、要求walltimeは7時間30分である。
groupごとの所要時間が同一とは限らず、この観測だけから完了時刻やtimeoutを断定しない。

上限に達した場合に既存groupを保持して続行できるよう、C0T0で使用した8個の復旧helperをbyte変更なくC0T1専用の新規ディレクトリへ配置した。
remote rootは`/home/user/workspace/mcmc4qec/20261019-tile-low-bar-recovery-c0t1-v1`である。
deployment SHA256は`baf843b96b3740e4354903d63f1486d9114f8b23115e19ca153db8df7970c013`である。
元のaccepted submission、source、manifest、runtime、native helperのhashを照合した。
既存C0T0の成果物・旧helper・実行中のC0T1 sourceは変更していない。

deployment transportは元v2から対象job・condition・root・origin hash・保存先だけの6置換で生成し、逆置換によるsource一致を確認した。
controlも対象とhashだけを変更し、元のguardと処理を維持した。
受入4件は3.25秒で通過し、実行中originのprepare拒否、prepare/preflight/単発qsubの手順、変更されたauthorityの拒否、queuedを含む2-node制限を確認した。
実環境ではobserveだけを行い、265334がR・run_count 1、復旧launch/resultsが存在しないこと、要求node合計2を確認した。
この準備ではqsubを実行していない。

## 条件付きの後続手順

265334が正常終了した場合は[通常の完了受理・集約手順](low_c0t1_trace_completion_2026-10-19_ja.md)を使う。
失敗終端が確認された場合だけ、`output/control_low_bar_recovery_c0t1_v1.py prepare`へ進む。
prepareは実PBS終端と固定入力を再照合し、既存の完全なgroup・未完了group・損傷や曖昧な出力を区別する。
その実inventoryと資源計画を確認してから、空き枠を検査するpreflight、executeの順に一度ずつ進める。
実行中のjobの再投入や、既存groupを無条件に削除して最初からやり直す処理は行わない。
復旧jobが必要となった場合の完了受理と最終report transportは、その実際のprepared/submission記録に結び直す必要があり、今回まだ作成していない。

originは`low_bar_recovery_parent_input_0_1_0_v1.json`、deployment証拠は`low_bar_recovery_c0t1_deployment_v1_*`、control生成根拠は`low_bar_recovery_c0t1_control_sources_v1.json`に保存した。
全て`docs/wp/data_tile_validation_2026-10-17/`配下にある。
