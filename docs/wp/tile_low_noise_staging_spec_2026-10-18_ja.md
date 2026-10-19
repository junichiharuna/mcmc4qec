# single-PBS低ノイズ結果の検証付きcopy仕様

## 範囲と既存契約

旧sampling bundle・source・rootを変更せず、終了済みsingle-PBS productionの全保存artifactを新analysis bundle/runs配下の新規workspaceへbyte単位でcopyする。
移動・削除・再sampling・再復号・科学的再計算は行わない。
所有する新規ファイルは `cluster_scripts/tile_low_noise_staging.py`、`tests/test_tile_low_noise_staging.py`、本文書の3つとする。
元samplingが実行中の現時点ではworker実行とqsubを行わない。

既存 `tile_low_noise_analysis.read_production_plan` は保存manifestと現在のmake_planを比較し、root絶対パスの変更は要求しない。
`completed_phase_evidence` は両phaseの全task一覧・native証拠・実PBS job IDを結合するが、sampling submissionの絶対scriptパスをroot内へ変更する処理はない。
analysis submitterはanalysis rootをbundle/runs内へ制限するため、copy先をその制限に合わせる。
trace auditはsampling sourceとaudit rootの非包含を要求し、両者が同じbundleであることは要求しない。
最終 `read_audited_collection` は新audit側submission scriptをaudit root内へ制限するため、copy後のworkspaceを入力に新規auditを実行し、その実PBS/scriptを保存する。
旧samplingのreceipt・intent・native証拠・scriptに含まれる絶対パスやjob IDは書き換えず、そのまま元実行の証拠としてcopyする。
既存analysis・audit readerは追加staging証拠を自動消費しないため、新しいstaged readerでcopy由来のsealを検証し、既存readerの結果と併せて返す。

## 小API

`prepare(control_root, source_root, destination, analysis_bundle, binding)` は独立の新control rootへ固定planを作る。
bindingは元bundle・analysis bundleのaccepted source hash集合と元sampling job IDを明示し、sampling manifestの全scientific source hashを含める。
親が保存したmanifest・submission-intent・submission receipt・sampling scriptの独立hashを `input_sha256` として必須にする。
使用Python、現在のpackage/source集合、固定platform profileに一致するnative binary hashはprepare時に別のsoftware snapshotとして保存し、巨大raw一覧はprepare時に走査しない。
source・destination・controlは絶対パスでsymlinkを含まず互いに非包含とし、destinationはanalysis_bundle/runs配下の未作成rootへ固定する。
prepareは両phaseのcompleted evidence、元receiptとsubmission-intent、元PBS Fと実Submit_arguments、metadata一覧とhash、192 replicate・768 group・192 anchor・全sampling task数を結合する。
元PBSのrun_countが1であることと、両phaseのhostnameがexec_hostに含まれることを確認する。
元jobが非終端、summaryが欠落、task重複・欠落なら準備を拒否する。
PBS exit0と全phase成功は正常完了として区別して記録する。
非zero exitでも全taskの保存記録が揃い、summaryとartifactのrecorded failureが対応する場合は失敗を保持した完了として区別し、成功へ書き換えない。
失敗記録を除外して192/768の分母を縮めず、未記録taskをrecorded failureとして捏造しない。
両phaseが揃わない早期終了はstaging成功にせず、元証拠をそのまま残す。

`run(control_root)` はPBS内だけで実行し、新destinationを排他的に作る。
親投入のcontrol側契約は `stage.sh`、`submission-intent.json`、`submission.json` とし、command・plan_sha256・script_sha256・受理job_idを結合する。
workerは実PBSのSubmit_argumentsと実行中状態を確認し、copy後もreceipt/scriptの不変性を確認する。
開始intentをcontrol rootへ排他保存し、既存intent・seal・部分copyがある場合は再実行しない。
copy開始前にplan・metadata・実PBS状態・source/Python/nativeのhashを再確認する。
worker上で全raw marker/json/npzの期待task集合・identity・payload hashとsummaryのrecorded failureを照合する。
全source fileのhashとsizeを記録し、各copy先をexclusive binary writeで作り、全copy先のhashとsizeを照合する。
copy終了後に元の全file census/hash・metadata・source/Python/nativeを再照合し、copy先の全file census/hashも再確認する。
copy先は内容を書き換えない独立fileとし、symlink/hardlinkや未検証tree copyは使わない。
失敗時はcontrol intentと部分copyを残し、sealを書かず自動削除・自動再開しない。
成功時だけcontrol側summaryとcopy先staging sealを保存し、元絶対root、元script、元job/exit、元manifest、全file hash/size、copy実PBS、before/after一致、使用source/native/Pythonを結合する。

`read_staged(destination)` はsealと全copy file hashを再確認し、元絶対パスは由来情報として保持する。
このfull readerは最初のI/O前にPBS_JOBIDを要求し、login上で巨大rawを走査しない。
copy先sidecarだけでなく独立control rootのplan・summary・execution intentも一致させ、検証終端で全copy fileとsoftware snapshotを再確認する。
copy自身の実PBSがF/exit0であることと親投入receipt/scriptの一致を後続入口で必須とし、seal生成直後でまだRのcopyは後続処理へ渡さない。
analysisが作る新規出力は元copy censusと分離し、traces/anchorsや元metadataの追加・欠落・変更は許容しない。
copy元を再検証する場合はseal内の元absolute rootと比較し、現在のcopy先を元実行場所と偽装しない。
`read_staged_audited_collection(destination, audit_root)` はstaging seal検証の前後に既存audited readerを呼び、元sampling実行の由来と新analysis/audit実行の証拠を別項目として返す。

## loginとcomputeの入口

`read_staged_provenance` は固定seal・独立control・元metadata・source/native/Python・copy実PBS F/exit0だけを読み、`current_payloads_rehashed=False` を明示する軽量gateである。
`plan_analysis` と `plan_trace_audit` はこの軽量gateの前後で既存plan生成を呼ぶ。
`submit_analysis` と `submit_trace_audit` というPython関数名はscript準備専用であり、qsubを実行しない。
これらは既存checked_plan・resource・bundle_bindingを再利用し、新helperの `run-analysis` または `run-trace-audit` を実際に呼ぶPBSscriptと `staging-submission-plan.json` を保存する。
recordのcommand・script_sha256・submit_source_sha256は新helperが準備した実scriptを指し、旧runnerを直接投入したような記録は作らない。
親はこのrecordを用いて共有lock・controller不在・queued込み最大2node・排他intent・曖昧応答保持を満たす一回投入を行い、実job IDをsubmission receiptへ保存する。
compute入口は必ずfull readerを通ってから既存runnerを呼び、終了後にもfull readerを通す。
CLIは `verify-metadata`・`plan-analysis`・`plan-trace-audit`・`prepare-analysis-job`・`prepare-trace-audit-job` が軽量側、`run`・`verify`・`run-analysis`・`run-trace-audit` がPBS側である。
追加full hash検証の時間は既存synthetic分析profileに含まれず、既存資源上限による完了予測へ黙って含めない。
前後2回のfull readerがそれぞれ2回全rawをhashするため、追加4passを資源見積もりに明示する。
既存copy jobの実測totalを1pass時間のproxyとして再利用し、係数2とmetadata余裕300秒を加え、30分単位へ切り上げた追加予算を保存する。
copy totalは将来scan時間の厳密上限ではなく、負荷変動を含む完了保証として扱わない。
分析と実測full auditは追加予算を元要求へ加算し、合計24時間を超える場合は新allocationが必要としてscript準備を拒否する。
初回tracecapacityは測定前の24時間全job ceilingを維持し、その内側で追加I/O予算とbaselineに残す時間を明示予約する。
copy実測が欠落・非有限・非正の場合はsubmission-readyにしない。
scriptとrecordには同じ加算後または予約後の実要求を記録し、新しい測定ジョブは追加しない。
sealとplanは読み取ったbytesそのもののSHAを保存し、読取直後と検証終端の変更を拒否する。

## 受入

軽量fixtureで正常copy、recorded failureを含む全分母、元absolute receipt保持、非終端・不正exit・不足summary拒否を確認する。
rawの欠落・余分・重複task・marker不一致・payload変更・危険path・symlink・source/native/Python変更を拒否する。
copy途中の元変更、copy先変更、既存destination、既存intent、seal前の失敗、seal後の改変を拒否し、部分成果を保持する。
実APIとの境界でcopy後read_production_planとcompleted_phase_evidenceが元と一致し、既存analysis/audit readerに渡すmanifestとtask分母が変化しないことを確認する。
全raw走査と巨大copyはqsub内に限り、qsubは親だけが共通lock・controller不在・queued込み最大2nodeを確認して一回投入する。
資源値と所要時間は実測前の上限と実測を区別する。
copyの成功は混合・精度・被覆・decoder正しさの保証ではない。
