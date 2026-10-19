# case2 T1/T2を既存staging/controlへ接続する最小入口仕様案

これは仕様案だけであり、新source・正式authority/readiness・remote rootは作成しない。
既存T0入口、staging-v1、control-v2、analysis-v11、sampling-v2は変更しない。
T0のcollectionおよびfinal reportの実受理は本検討時点では未解決であり、入口の軽量受入成功から本番完了を推定しない。

## 対象と固定する科学契約

対象はcase=2、target_index∈{1,2}の既定single-PBS samplingである。
現行CASESと保存manifestではcase2はsize6・depolarizingであり、別caseへ一般化しない。
sampling manifest、seed、目標prior固定decoder、kernel、initialization、全192rep、全768group、192anchor、全chain/step/ladder/uncertainty設定を変更しない。
既存保存manifestから読める予定数は次の通りで、実完了数とは区別する。

|target_index|目標p|fine rungs|chain/group/rung|sample task数|trace監査capacityのtask数|
|---|---:|---:|---:|---:|---:|
|1|0.003|13|8|79,872|832|
|2|0.001|15|8|92,160|960|

両対象ともstep18,000、anchor192件、anchor各16,384trialである。
trace監査capacityは本samplingのrep0/1×2kernel×2initの8groupであり、元sampling capacityの単一chainを代用しない。
記録済みfailed task、区間未取得、未定義診断を除外して分母を小さくしない。
現T0入口の正常終端gateを維持し、未終端・欠落・不一致・未対応の非正常終端は未完了として証拠を保持し、成功receiptを生成しない。

## 再利用する既存core

`tile_low_noise_staging.inspect_source/prepare/run/read_staged_provenance` は渡されたsampling planと独立bindingから対象を検証し、case2T0専用の数値処理を持たない。
`tile_low_noise_staging_control.prepare/checked/pre_submit/compute/read_completion`、`prepare_audit_full/read_all/collect` をそのまま使う。
BAR計画・実行・collectionは既存analysis_partitions、監査は既存trace_audit_run/resources、最終raw結合は既存audited_collectionを使う。
analysis partition数は各targetの正式measured_profileから取得し、T0の1partitionを固定値にしない。
全partitionの一意なprepared/receipt/PBS completionをcollectionへ要求する既存read_all契約を維持する。
samplingがmulti-PBSになっていた場合は本入口でsingle-PBS receiptへ偽装せず、既存の別multi-PBS経路の設計対象とする。

## T0から差し替えるauthority

|分類|T1/T2で必要な正式証拠と差し替え|維持する条件|
|---|---|---|
|sampling|対象production-{case}-{target}のmanifest・prepare・script・submission intent/receipt・両phase summary/native・選択field付き終端PBS|同じcase/target、固定source/runtime、全予定task、sample/anchorsが同じ実PBS job|
|analysis capacity|対象capacity-2-{target}のmanifest、全8group実測、measured_profile、PBS安定性補足、実script/receipt/native|対象production manifestへの一致、全192を維持する資源/partition、T0 profile/job265264を流用しない|
|source/runtime|既存承認済みdeploymentのsource/import/native/Python pins、元bundleのwheelと実installed package origin|現在sourceを自己受理せず、28py census・7driver・wheel・元plan.sources値を期待hashと照合|
|copy|対象専用fresh control root・destination・copy実script/receipt・F0・seal・経過時間|T0 copy job/summaryを流用せず、実copyの計測からI/O予算を決める|
|trace監査|対象専用capacity/full root、各prepared/receipt/native/summary/PBS|同じ対象の8group実測からfull192資源を決める|
|入口記録|case/targetを含むlocal invocation名、readiness identity、全phase pins、入口source SHA|T0のlocal evidenceと衝突させず、target間のreceipt交換を拒否|

実sampling job ID、analysis capacity job ID、profile/PBS/readiness/receiptのSHAは、各実終端証拠が揃ってから独立確認して固定する。
本仕様にはfuture hash、仮job ID、架空copy elapsed、架空の成功authority JSONを置かない。
同じimmutable source deploymentを使う限りsource期待hashを再発行する必要はないが、target別manifest/script/receiptと実解決先への結合は毎回検査する。
元sampling packageはlow-noise-v2/srcへ推測置換せず、承認済みwheel配置とvenv alias→production-v1の実解決先を使う。
local証拠Pathとremote POSIX pathを分離し、Windows親CLIで/home/...を正しく扱う。

## 入口の最小構成

新しい親用3入口をcase2・target1/2だけに限定して設ける案とする。
役割はcopy一回、phase一回、readiness initial/extendの既存3区分を維持し、汎用workflow engineや新collectorは作らない。
targetごとに一つの外部SHA付きauthorityファイルを親が確認して固定し、3入口は同じauthority identityを要求する。
authorityは対象、許可済みbundle/root集合、元samplingの独立pins、対象analysis capacityの独立pins、承認済みsource/software pinsと元receiptを保持する。
authorityの対象選択はtarget1/2の列挙だけを許し、任意case・任意remote root・実行code文字列を設定として受け取らない。
authorityファイルから読み取った現在source hashを正解へ格上げせず、既存deployment evidenceの外部pinと連結してからimportする。
新しい操作記録は辞書をcanonicalな順序でserializeし、別PYTHONHASHSEED processでも同一programになるようにする。
T0のv3 builderが持つ旧7driver順序の限定対応は既存T0証拠向けに残し、新入口の任意dict順許容へ拡張しない。
旧入口をexecしてglobal値だけ差し替える方式や、旧source SHAのままtargetを変更する動的patchは使わない。
新入口自身のsourceとimport closureは新deployment evidenceへpinし、旧immutable bundleのsourceを上書きしない。

root候補は既存規約に従うcopy-2-{target}-v1、staged-production-2-{target}-v1、staged-trace-capacity/full-2-{target}-v1、collection-2-{target}-v1とするが、実採用前に別作業の占有がないことを親がread-only確認する。
analysis/trace rootはanalysis bundle/runs配下、copy/collection rootはcontrol bundle/runs配下の既存containment制約を満たす。
copy8GiB24h、trace-capacity96CPU340GiB24h、collection1CPU32GiB24hは既存の初回上限として維持し、完了予測にしない。
BARとfull trace auditのworkers/memory/walltimeは対象別capacityだけから決め、copy由来headroomも対象自身の実時間から再計算する。
上限超過時は停止して既存partition設計との接続を別途確認し、目標prior・192分母・task集合を削らない。

## 実行順と未解決範囲

対象のsampling/analysis-capacity実終端確認→target authority固定→copy prepare/qsub→copyF0/seal→R0→analysis全partitionとtrace-capacity→trace-full→全analysis/full-audit F0→collectionの順を維持する。
独立computeの並行実行は出力rootを分離し、readinessだけは一本の系列へ直列更新する。
各phaseのexecute成功receiptは、その実invocationが参照したpriorへ追加してから次のprepareへ進め、別branchの無条件mergeをしない。
qsubは親だけが共有lock、controller終了、queued含む最大2node、intent fsync後の直前gate、lock所有、実script/source/native/PBSを再検査して一回だけ行う。
曖昧応答・既存intent・partial rootの自動再投入をしない。
collectionの実compute fileは受理済み新phase入口自身のbytesを排他配置したparent-wrapper.pyであり、新しい科学collectorを用意しない。
そのsource SHA、実inputs SHAと--collection-compute argvをPBS scriptに結合する既存contractを維持する。
T0 collection/finalreportの実受理が未解決の間はT1/T2についても下流完了・推奨設定・被覆保証を宣言しない。
finalreport/WSS/reference/selectorへの正式接続には対象別collection terminal/input pinsと全体cohort/reference gateの別受理が必要であり、本入口仕様の完了と混同しない。

## 受入項目

1. target1/2それぞれの実manifest形状の軽量fixtureで、13/15rung・全192rep/768group/192anchorと対象priorを維持し、target0・target間混入・case変更を拒否する。
2. source bundleのsrc不在とinstalled package配置、28py追加/欠落/変更、7driver/wheel不一致、同bytes別解決先、Windows親CLIの実POSIX形状を検査する。
3. 対象別capacityの取り違え、PBS未終端、script/receipt/native/manifest mismatch、T0 profile流用を拒否し、異なるpartition数でも全予定group集合が一度ずつ残ることを検査する。
4. 実copy値未取得時はR0を作らず、実F0/seal/経過時間からのみ初期readinessとI/O予算を作る。
5. 旧T0入口と全既存evidenceのhash不変、target間local invocation/root/lockの衝突拒否、最大2node/曖昧応答/所有権変化の一回qsub受入を行う。
6. 独立PYTHONHASHSEED processでprogramが一致し、source値/code/duplicate key/target/prior/任意dict順変更を拒否する。
7. 既存generic coreへのprepare/checked/receipt/compute契約をbounded fixtureで結び、raw走査はPBS compute以外から到達不能とする。
8. failed task/未定義診断/区間未取得を全分母に残し、missing artifactは記録済みfailureに読み替えず未完了として停止する。
9. collectionの全partition＋full-audit terminal pins、実parent-wrapper/inputs/scriptのcompute前検査とoutput hashの保存直後/終端照合を検査する。
10. 各test file60秒以内の軽量受入と独立レビュー後にfreezeし、実配置/PBS/source/native照合と実ジョブ受理は別段階で記録する。
