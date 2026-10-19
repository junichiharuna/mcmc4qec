# 主ノイズ正式計時報告の親用一回投入仕様案

承認済みの全4case報告requestを、一度だけqsubする親用入口を追加する。
本仕様の保存時点では実装・受入・正式request作成・実qsubは未実施であり、親の仕様確認後に受入テスト、実装、独立レビューへ進む。
科学module、既存の投入済みbundle、元MC/BAR root、reference・seed・閾値を変更しない。
全4caseの本計時と独立回収が揃う前に、欠けたpinや完了状態を補完しない。

## 所有範囲と既存契約

追加予定は `output/submit_final_timing_report_once.py` と `docs/wp/data_tile_validation_2026-10-17/test_submit_final_timing_report_once_v1.py` の2ファイルとする。
既存 `output/prepare_final_timing_report_v1.py` のSHA256 `ccc8ff5227b19ae982cc9ed8de403aed1d78239f2f45f9f0ce6b4478e39be0c9` を固定し、prepare/executeの契約をそのまま使う。
正式科学bundleは `20261018-tile-timing-report-v2`、accepted manifest SHA256は `867b18579f3e5b3975c9e8560787230477a1115c8305ba25c9ae25081a529942` のままとする。
配置・正式configの条件は [既存handoff](tile_timing_report_linux_handoff_2026-10-18_ja.md) を参照し、helperのprepareやcompute executeを親submit wrapper内で呼ばない。
実行対象は親が別途prepare・受理した単一のrequest rootと既存 `report.sh` に限定し、複数caseの自動loopやscheduler controllerを追加しない。
初期資源は既存readyと同じ1 node・1 CPU・16 GiB・2時間であり、完了時間の実測保証ではない。

`submit.own_active_jobs`、`submit_tile_capacity.requested_nodes`、`submit_tile_mc_time.live_controllers` の受理済みsourceを固定bundleから再利用する。
共有lockの場所と一度だけのqsub、intent後の最終検査、応答不明時の停止、所有一致時だけのcleanupは、既存のBAR親wrapperとsingle-PBS copy/source wrapperの契約を再利用する。
具体的な参照実装は `output/submit_bar_capacity_once.py`、`output/submit_low_noise_staging_copy_2_0_once.py` とする。
科学plan形式が異なる旧submitterのsubmit関数を流用したり、既存moduleをmonkeypatchしたりせず、共通のscheduler readerと固定request readerを用いる最小の親入口にする。

## 外部受理pinとmetadata gate

正式requestの受理証拠は別途親が固定したpath/SHA256から読み、wrapperが現在のremote bytesを読んで受理pinを自己生成しない。
受理対象はrequest root、`preparation.json`、`ready.json`、`config.json`、`plan.json`、`execution_driver.py`、`report.sh` と、準備時に固定したsource/Python/native入力・解決先・closureの集合である。
rootは受理された絶対pathそのものに限り、全入力cohortと交差せず、rootやmetadataのsymlink・途中の解決先変更を拒否する。
既存venvのPythonはlexical executable pathと解決先/binary hashを分けて保存し、実行pathをsystem Pythonへ置き換えない。
JSONはpinに照合した同一bytes snapshotをparseし、既知fileのbytesだけでなくsource censusの追加・欠落も検査する。
最適化Pythonではgateを省略しない明示例外を使い、既存helperをimportする経路ではその `sys.flags.optimize` 拒否も維持する。

project moduleのimport前にstdlibでrequest helperのSHA、accepted bundleのmanifest・全input/source census、Python、ready/driver/config/plan/scriptとplanの全metadata/source入力を検査する。
既存helperの `read_tracked_json`、`verify_bundle`、`verify_plan_inputs` とadapterの `sources`、`runtime`、`inputs` を再利用し、metadataの再構築結果を固定planと照合する。
MCとBARの4caseが全て `complete_candidate` であること、全8選択identityとreference・census・native/runtimeの結合を維持する。
`complete_candidate` は全payload照合済みを意味せず、NPZ読込・全task raw hash・decoder再実行・数値再計算はこのlogin-node入口では行わない。
親の受理済み回収proofと既存adapterが検査する保存inventoryの結合を保持し、本番の全payload照合はcompute上の既存 `report.run` に委ねる。

元MC/BARの5 jobについて保存済み正式receipt・execution/native・summary・terminalを既存 `execution_evidence` の契約で照合し、投入直前にはqstatの新しい終端snapshotを取得する。
新snapshotは受理済みjob ID、F、exit status、実script、resource、native hostとの一致を要求し、別jobやcapacityの正常終了で代替しない。
正常exit0と、全artifactを保存した記録済みtask failureに対応するexit1の区別は既存adapterに従い、kill・timeout・欠損をrecorded failureとして通さない。
新qstat snapshotは新しい投入証拠として保存し、元のaccepted terminalを上書きしない。
元結果の全payload検証の成功や科学的精度を、このmetadata gateから追加で主張しない。

## 投入順序と再投入禁止

既定CLIはlocal dry-runのみでSSHもqsubも行わない。
明示 `--preflight` はremote metadataとscheduler状態の読取だけ、`--execute` は親担当だけが使う一度の投入とする。
request未受理、pin未設定、localまたはremoteに既存intent/receipt/ledger/execution/outputがある場合は、自動resumeや新しいprefixへの逃避を行わず拒否する。
read-only preflightの記録はsubmissionの証拠と別prefixに保存し、正式投入の証拠を再利用しない。

親のlocal側ではinvocation intent、送信するsource、stdout、stderr、receiptを排他作成し、任意の一つが既存なら同じ一回投入を拒否する。
remoteでは `/home/user/workspace/mcmc4qec/tile-low-noise-submission.lock` を排他取得し、request root・PID・所有tokenと作成bytes hashを保存する。
既存lockやdangling symlinkを拒否し、取得失敗時に他所有者のlockを削除しない。
固定controllerのfinished証拠とprocess記録を外部pinに結び、その旧PIDが残っていないこと、およびlive controllerがいないことを確認する。
queuedを含む全自分のactive jobのselectを既存関数で数え、今回の1 nodeを足して2以下でなければ投入しない。
node数やcontroller状態が不明な場合はゼロ扱いで補完しない。

lock取得後にmetadata/source/runtime/native/script・元5 job終端・root freshnessを再確認し、実qsub commandを `['qsub', '<request>/report.sh']` に固定する。
`submission_intent.json` を排他保存してfsyncした直後に、同じmetadata/source/解決先/closure、controller、node数、scriptとintent、lock所有をもう一度照合する。
intentは既存preparationのmanifest/resource/command/script hashを保持し、ready/preparation/wrapper pin、投入時の終端snapshot、scheduler snapshotの証拠を追加できる。
`submission.json` はこのintentと完全に同じ内容へjob_idだけを追加し、既存compute wrapperの比較を変えない。
既存 `report.sh` を再生成せず、`bash -n` と固定hashの両方で検査する。

最終gate後にだけqsubを一度呼び、再試行callbackや別scriptへのfallbackを設けない。
return code 0と単一の正式job ID形式が同時に得られた場合にのみ成功候補とし、stdout/stderr/return code/commandを排他receiptへ保存する。
timeout・非zero・空/不正stdout・通信例外は受理状態不明としてlockと全intentを保持し、再qsubせず親が既存jobを調べる。
成功応答後もintent/script/input snapshotとlock所有を照合し、同じintentからledgerを排他保存し終えるまで投入成否を確定しない。
qsub受理後のmetadata変化、receipt/ledger保存失敗、所有変更も曖昧状態として証拠を残し、二度目のqsubを行わない。
失敗時のcleanupはqsub未呼出しと確定できる場合、または成功ledger保存済みの場合に限り、非symlink・所有token/PID/root・作成bytes hashが全て一致するlockだけを削除する。
intent作成後に最終gateが失敗してもintentを消さず、そのrequestの自動再実行を拒否する。

localのSSH失敗や応答消失もremote投入なしとは断定せず、local receiptを曖昧状態にして手動照合へ戻る。
local側の成功判定はjob IDだけでなく、返ったledger全体が外部固定requestから期待したintentと一致することを要求する。
報告job自身のF/exit、実資源、execution/completion、生成reportと日本語表は親の終端回収で別途照合し、submit成功を報告処理完了と扱わない。

## 軽量fixture受入案

本番requestを作らず、小さい合成metadataとmock scheduler/SSH/qsubを使い、1file60秒以内・全体5分以内に収める。

1. 固定requestを一度だけ投入し、実command・資源・intent/ledgerのjob_id以外の一致・所有lock cleanupを確認する。
2. 既定dry-runでremote/qsubが0回、preflightでqsubとremote入力書込が0回であることを確認する。
3. pin欠落、template、未完了case、case/epsilon不足、capacity取り違え、PBS終端/script/resource不一致を拒否する。
4. preimport gateでhelper/source/Python改変、source追加、metadataのpath変更・symlinkを拒否し、project importへ到達しないことを確認する。
5. 各外部pinとparseが同一bytes snapshotに対応し、`-O` または明示gateを無効化して通過できないことを確認する。
6. local/remoteの既存intent・ledger・execution・output、既存lockとdangling symlinkでqsubしないことを確認する。
7. queuedを含む2 node稼働、controller非finished・PID残存・live controller、scheduler取得失敗を拒否する。
8. intent保存直後のsource/plan/script/解決先/closure/intent改変とnode増加・controller開始・lock所有変更を検出し、qsubが0回のままであることを確認する。
9. qsub非zero・timeout・空/不正/複数job ID・SSH応答消失を曖昧として保持し、再試行が0回であることを確認する。
10. qsub成功後の所有変更・metadata変化・receipt/ledger保存失敗で他所有者lockを消さず、成功を報告しないことを確認する。
11. qsub前に発生した失敗でも取得していないlockや変更されたlockを削除せず、作成済みintentを保持することを確認する。
12. 合成requestに既存prepare helperのreaderと実adapter metadata入口を接続する小fixtureを置き、全raw readerとdecoderが呼ばれていないことを確認する。

受入成功は投入制御の検証であり、本番の元payload監査、精度評価、実PBSの正常終端を証明しない。
仕様承認後も本物request/pinの生成と実qsubは親の別作業として残す。

## v2のpath検査修正

初回受理source `072d2359c7596524211f5f562d161f59ecf0ac91c2dfe102e89858fd5aae3a0f` の証拠は履歴として保持する。
runbook確認時、Windowsの `Path('/home/...').is_absolute()` がfalseとなり、実remote rootをlocal CLIで誤拒否することを確認した。
remoteのroot・bundle所属・controller file所属だけを `PurePosixPath` で解釈し、local acceptanceファイルと出力証拠は従来のWindows `Path` で扱う。
実 `/home/...` 型の合成schemaをWindowsの一時local証拠から読み込む受入、relative path・traversal・別prefix・Windows drive形式の拒否を先に追加する。
qsub、lock、科学入力、request helperの契約は変更せず、最小修正と独立差分レビュー後の新SHAを受理対象にする。
この修正中も本物request/pin作成・remote・qsubは行わない。
