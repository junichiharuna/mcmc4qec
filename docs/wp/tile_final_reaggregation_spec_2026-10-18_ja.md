# 主校正の最終再集計実行仕様

科学処理は凍結済みの `tile_audited_results`、`tile_comparisons`、`tile_precision_assessment`、`tile_weight_comparison`、`tile_initialization_strata` を変更せず再利用する。
case ごとに全 192 replicate を対象とし、adapter、比較、精度評価、重み比較、depolarizing の場合のみ初期化層別の順で別プロセスを逐次実行する。
混合一覧は後続の別 phase とし、この runner の依存に含めない。

`prepare(root, production_root, audit_root, case, evidence, completion_receipt, receipts=None)` は新規 root に manifest を排他作成する。
evidence は adapter の sampling_verification、analysis_verification、anchor_verification、anchor_audit、reference_verification、reference_audit の 6 JSON を指す。
completion_receipt は元 sampling、analysis、full trace audit の submission ledger に対応する 3 job の qstat JSON（Jobs mapping、F、Exit_status=0）である。
job_state、Exit_status、Submit_arguments、資源など必要な field のみを抽出した記録を受理し、qstat の全 field は要求しない。
submitter が保存する直前 qstat 記録も必要な field に制限し、Variable_List など無関係な環境情報を保存・表示しない。
追加の回収 receipt は任意の名前とパスの mapping で固定する。
入力 JSON、receipt、生成 manifest、context、元 ledger、full audit summary/native evidence、凍結数値 module を含む source closure、runtime、Python 実体 hash を結ぶ。
prepare/read_plan は全 payload を走査せず、full audit の 768 group、失敗 0、192 replicate と固定 production context を確認する。
実 payload と全 raw rows の確認は adapter の全件処理に委ね、subset で代用しない。

run は qsub、単一 thread、実 submission ledger と PBS_JOBID の一致、排他 execution intent を要求する。
既存の execution intent、phase 成果物、summary があれば再実行しない。
各 subprocess は開始時と終了時の入力/source binding、出力 hash、wall、CPU、Linux peak RSS、return code を保存する。
最初の失敗で後続を停止し、予定全 phase に failed / not_run_dependency を記録して非 zero で終える。
正常に保存された結果だけを成功とし、子プロセス終了時の report 欠落、改変、入力変化も失敗として残す。
開始後の source/入力変化と終端 binding failure があっても summary に既存 outcome を保存する。
PBS による強制 kill では終端 summary を保証できないため、開始 intent と phase の逐次記録を保持し、未完了を成功扱いせず自動再実行しない。

submitter は新 bundle/runs 下の独立 root に固定 script を置き、共有 tile-low-noise-submission.lock を取得して controller 不在と queued 込み最大 2 nodes を確認する。
qsub は一度だけ呼び、曖昧な応答・例外では intent と lock を保持する。
実行直前に upstream jobs の F/exit0、source/package/executable/input/script hash を再確認する。
資源は 1 node、1 CPU、32 GiB、2 時間で固定し、測定済み予測や完了保証ではなく初回上限と明示する。
正常な全件実行そのものが資源実測となる。
受入は軽量 fixture と mocked subprocess/qsub で行い、元科学 module の重い計算を繰り返さない。

この処理は現在の成果物と監査証拠の整合性・保存 BAR 算術・全分母の再集計を確認する。
歴史的 consumed hash、bootstrap の再実行、全物理状態の再復号、名目 95% 被覆保証を追加しない。
既存 bundle、venv、production root、科学 module、既存成果物を変更しない。
