# 単一PBS移設後の親用投入wrapper案

## 範囲と現状

これはcase2 target0のcopy完了後に使う準備・一回投入手順の小仕様案であり、実装・実prepare・remote照合・qsubは未実施である。
新規候補は `output/submit_low_noise_staged_phase_once.py` と対応mock testsだけとし、科学module、control protocol、v11、staging-v1、control-v2、既存planは変更しない。
既存 `tile_low_noise_staging_control.py` の `prepare`、`pre_submit`、`compute`、`read_completion`、`prepare_audit_full`、`read_all`、`collect` をそのまま再利用する。
一つのwrapperが `analysis`、`trace-capacity`、`trace-full`、`collection` を扱い、一回のexecuteで一つのqsubだけを実行する。
phase/indexを選ぶ親CLIは orchestration のみであり、既存controlのphaseは `analysis` と `trace-audit` のまま維持する。
解析indexは固定partition manifestのindexに限り、trace二種とcollectionはindex省略のみを認める。
全192反復、全768群、予定設定、seed、失敗・区間未取得・診断未定義の分母を変更しない。

## 固定pathと未確定の証拠

`BASE=/home/user/workspace/mcmc4qec` とし、bundleは `BASE/20261018-tile-low-analysis-v11`、Pythonはその `venv/bin/python` を使う。
stagingは `BASE/20261018-tile-low-staging-v1/cluster_scripts/tile_low_noise_staging.py`、controlは `BASE/20261018-tile-low-staging-control-v2/cluster_scripts/tile_low_noise_staging_control.py` である。
control directoryのstaging symlinkは承認済みstaging-v1の実pathへ解決することを要求し、同bytes別pathへ差し替えて許可しない。
sourceは `BASE/20261018-tile-low-noise-v2/runs/production-2-0`、copy control rootは `BASE/20261018-tile-low-staging-control-v2/runs/copy-2-0-v1`、destinationは `bundle/runs/staged-production-2-0-v1` である。
analysis capacityは `BASE/20261018-tile-low-analysis-v3/runs/capacity-2-0` の265264であり、正式measured_profileと `low_analysis_capacity_case2_target0_pbs_stability_supplement_v2.json` を合わせて固定する。
trace capacity/fullの新root候補は `bundle/runs/staged-trace-capacity-2-0-v1` と `bundle/runs/staged-trace-full-2-0-v1`、collection制御root候補はcontrol-v2の `runs/collection-2-0-v1` とする。
新rootの存在を準備前に確認し、既存なら上書き・自動再生成せず停止する。
元samplingの265259はこの仕様読取時点では未完了として扱い、copyのjob ID・F0・elapsed・seal・実receiptのSHAはここで補わない。
元samplingとcopyの実F0終了後に、必要fieldだけのPBS記録、実script・submission intent/receipt・copy summary/sealのSHAと解決先、元plan/source/native/Python証拠を新規ローカルreadiness JSONへ保存し、親がそのファイルSHAを外部pinする。
PBS記録はjob_state、Exit_status、run_count、Submit_arguments、Resource_List、exec_host/exec_vnode、必要なresources_usedと時刻だけを保存し、Variable_Listは保存しない。
readinessには承認済み配置/受入証拠のSHA、全import originの実path/SHA、旧controller終端証拠、capacity profileとPBS stability supplementのSHAも含める。
copyの成功は `staging.read_staged_provenance(destination)` のmetadata readerで確認し、loginで `read_staged` や全raw走査を呼ばない。

## 準備する順序と既存API

1. コピー終端証拠を外部固定し、metadata-onlyのstaging provenanceを照合する。
2. `staging.plan_analysis(destination, analysis_capacity_root)` で新partition manifestとanalysis routing reservationを一度だけ作る。
3. 全partition indexについて `control.prepare(bundle,destination,'analysis',index=index)` を一度だけ呼び、実 `analysis-submissions/{index}/partition.sh` と `staging-control-plan.json` を保存する。
4. 独立trace capacity rootへ `staging.plan_trace_audit(destination,capacity_root,capacity=True,workers=8)` を呼び、`control.prepare(bundle,destination,'trace-audit',audit_root=capacity_root)` で実guarded scriptを作る。
5. capacity jobの実receiptとcontrol prepared SHAを親が固定し、F0後 `control.read_completion` でstatus successを確認してから `control.prepare_audit_full(full_root,destination,capacity_root,capacity_pins)` を呼ぶ。
6. `control.prepare(bundle,destination,'trace-audit',audit_root=full_root,capacity_root=capacity_root,capacity_pins=capacity_pins)` でfull用scriptを作る。
7. 全analysis partitionとfull trace auditのprepared/receipt pinsを固定し、`control.read_all` の全partition＋full audit censusを通してcollectionの新規準備へ進む。

capacityとanalysisはcopy成功後なら互いに独立だが、親だけが最大2nodeの空きと順序を決める。
analysisの基礎資源は保存済み正式profileの96 workers・96 CPUs・48 GiB・01:30:00であり、group分割とworker数をwrapperで書き換えない。
controlが呼ぶ既存 `staging.budget_resources` はcopy実測を使い `extra=max(1800,ceil((4*2*copy_elapsed_seconds+300)/1800)*1800)` を計算し、analysis/fullには基礎walltimeへ加える。
copy実測が未確定なので現時点で最終walltimeは確定しない。
trace capacityは既存8 workers・2反復・96 CPUs・340 GiB・24hの初期上限を使い、同headroomは24hの内側に予約し、追加予算が基礎上限を消費する場合は拒否する。
trace fullは既存controlのmetadata-only capacity completionと既存純関数resource_planからworkers/resourceを決め、loginから旧 `measured_capacity` のraw再走査を呼ばない。
これらは資源見積りであり完了時間の保証ではない。

## 一回投入の共通契約

CLI案は `--action prepare|dry-run|execute|completion --phase analysis|trace-capacity|trace-full|collection --index N --readiness PATH --readiness-sha256 SHA` とし、indexはanalysisだけで必須とする。
prepareは新規metadata/scriptだけ、dry-runは既存preparedを確認してbash -nと正確な一回executeコマンドを保存し、qsubを呼ばない。
executeはreadinessとprepared/scriptの外部SHAを要求し、準備を暗黙に行わない。
cluster moduleをimportする前にstdlibだけで外部pinした全source、Python/native、実import解決先を確認し、import後にも既存software snapshotとの一致を確認する。
既存共有lock `BASE/tile-low-noise-submission.lock` を排他取得し、終了済controller証拠とlive controller不在、queuedを含む現在の全requested nodes＋1が2以下であることを確認する。
control phaseは `control.pre_submit(plan,prepared_sha)` をintent作成前に実行し、exclusive `submission-intent.json` をprepared recordそのものとして保存する。
intent作成後は `pre_submit` が意図通り拒否するため再呼出しせず、既存 `control.checked(plan,prepared_sha)` とintent完全一致、execution/completionの不在、lock root/pid、PBS空き/controllerを再照合する。
actual argvはpreparedの `['qsub',actual_script]` だけに限定し、直前に実script hashとbash -nを再確認する。
qsubは一回、曖昧stdout・nonzero・timeout・中断ではlocal/remote intent、stdout/stderr、曖昧receiptとlockを保持し自動再実行しない。
成功応答後もlockの非symlink・root/pidと元intentを再照合し、他所有者へ変わったlockを削除しない。
成功receiptはprepared recordに実job_idだけを加えた形で `submission.json` に排他保存し、prepared SHAとreceipt SHAを別の親証拠へ固定する。
終端は `control.read_completion(plan,prepared_sha,receipt_sha)` でPBS F/exit、host/run_count、実script/resources、native/source、control完了markerを確認する。
全taskが揃うrecorded audit failureは既存statusのまま保存し、successへ変換せずfull計画や成功collectionへ進めない。

## collectionの最小補完

既存controlにはcollectionのCLI/script生成と出力publicationがないため、同じ親wrapperが専用PBS scriptを生成する。
これは新しいcontrol phaseの追加ではなく、既存 `control.collect` を呼ぶ外側の実行・保存手順である。
専用computeは実PBS job/receipt/resources/host/run_countとsoftware snapshotを始終照合し、`control.read_all` で全成功終端を確認後、`partitions.collect(destination)` を一度呼んで `destination/partition-collection/{rows.jsonl,summary.json}` を生成する。
続いて `control.collect(destination,full_audit_root,pins)` を呼び、返却されたsampling、全rows、audit/staging/control evidenceを専用rootへ排他保存する。
既存partition-collectionがある場合は自動再集計・上書きをせず停止し、途中生成物も削除しない。
control.collect内の全raw hash照合と監査結合はcomputeでのみ実行し、login completionは保存出力のhash/receipt/PBS終端だけを照合する。
外側のcollection完了証拠をcontrol-completion.jsonと偽装せず、`collection-completion.json` として入力pins・software・出力SHA・全192/768 census・wall/CPU/RSS・実PBS identityを結合する。
暫定collection資源候補は1CPU・32GiB・24hの明示的な初期上限とし、承認前に投入しない。
collectionはcontrol.collect内の追加監査走査を含むため、解析の4pass見積りをcollection全体の測定済予測として扱わない。
初回実行が計測となり、timeout/OOM/入力変更/後段失敗時は未完了の記録を残し、後続summaryやtiming selectorへ成功入力を渡さない。

## 実装前の受入要件

- 固定case2 target0、phase/index census、copy未完了・架空job/pin・異なる元planの拒否を確認する。
- source/import path/native/Pythonのpreimport改変、same bytes別path、prepared/script/resource変更を拒否する。
- prepareにraw readerを呼ばせないspyと、analysis/capacity/fullが既存APIへ正しくdispatchするfixtureを置く。
- capacityの2反復8 workersとfull192の受渡し、capacityのF0/status/pins不足と4pass予算超過の拒否を確認する。
- 共有lock、live controller、2node超過、intent後の直前変更、qsub一回、曖昧返値と成功直後lock所有変更を実既存helper接続で確認する。
- receipt完全一致、選択fieldのPBS F/exit/resources/host/run_count、前後入力改変、recorded failureと未完了を区別する。
- collectionはp.collect→control.collectの順、全分母・出力hash、途中失敗・既存出力拒否を軽量fixtureで確認し、本番rawは走査しない。
- 各testfile60秒以内、独立レビュー後にsourceをfreezeし、実終端後のreadiness固定・dry-run・親の一回投入を別工程として記録する。

本案では新wrapperのコードとテストは未作成であり、既存科学契約を変更する必要は確認されていない。
