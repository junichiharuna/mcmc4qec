# 複数 sampling job を入力とする低ノイズ BAR と最終照合

本仕様は `tile_low_noise_sampling_partitions_proposal_2026-10-18_ja.md` の後続入口を具体化する。
既存の科学 module と凍結 bundle は変更せず、sampling task・stage 153・固定 decoder prior・全 192 replicate・全 768 group・全解析設定を維持する。
本番再計算と qsub は本受入に含めない。

## 入力契約

新 sampling module の `completed_partition_evidence(root,plan)` を明示的に呼び、mode が `partitioned_sampling` の完了証拠だけを受け付ける。
証拠には sample の全 task 数・failed 数・group_record_digests、anchors の全 task 数・failed 数・record_digests、全 partition の PBS receipts、native と source closure、root 相対の input_sha256 を含む。
metadata reader の再検証を現在の全 NPZ hash 再検証とは表現しない。
metadata の lexical path・解決先・hash を処理前後で照合し、root 外への解決、retarget、途中変更を拒否する。

## BAR の明示入口

`tile_low_noise_partitioned_analysis.py` は create_plan/read_plan/run_partition/collect/read_collection を提供する。
解析資源は既存 synthetic capacity の `measured_profile` と `validate_partitions` を再利用する。
analysis_context は元関数に新完了証拠全体を渡し、既存 validate_context/analyze_group/read_group/partition_evidence と整合させる。
新 wrapper は自分の source import closure と新 sampling reader の closure を結び、旧 singleton 完了 reader に戻らない。
既存 analysis-execution-intent.json に非 PBS routing reservation を排他作成し、既存 root の再実行・cache-return を禁止する。
run は PBS・固定単一 thread・実 native 検査を要求し、全選択 group の出力と入力 marker を検証して終端で metadata/source を再照合する。
collect は各 analysis partition の intent/native/summary に加え submission intent/ledger/script と正式 terminal F/exit0 を結び、完了後の全予定 group を保存する。
recorded sampling failure、未定義診断、未取得区間を分母から除かず、欠損 partition は完了 collection としない。
read_collection の iterator は全消費後に全 group 数・row 数・partition 証拠・metadata/source の終端一致を検証する。
新 submitter は qsub 一回、共有 lock、controller 非競合、queued を含む最大 2 nodes、資源一致、intent 後の曖昧応答では lock 保持を既存契約通り実装する。

## 最終照合と数値報告

`tile_low_noise_partitioned_collection.py` は新 BAR reader と新 `tile_low_noise_partitioned_trace_audit.read_plan(root,source)` を用いる。
旧 `Evidence` と `verify_group` による全 trace payload、analysis marker、失敗 task、checkpoint、anchor の結合を再利用する。
新 audit の read_terminal により実 submission と正式 F/exit0 を結び、全 sampling/analysis/audit の証拠を返す。
全 iterator を消費し、全 768 group と 192 anchor を照合し、終端で全記録 hash と source closure を再確認する。
独立 reference を使わない summary は既存 summarize_rows、bounded WSS 比較は既存 compare_rows を呼ぶ。
WSS 使用時は audit_saved_condition を一回呼び、同じ case/prior/runtime/native を照合し、partial interval を full point reference としない。
新 CLI の数値報告出力は入力 root 外に排他的に作成し、入力改変・source 改変時は成功結果を公開しない。
本入口が正式 receipt を検査する job は、入力 sampling の全 partition と collector、BAR の全解析 partition、および full trace audit である。
この BAR collect と最終 report 自身については実行時の PBS ID・hostname と source/input 証拠を記録するが、その job 自身の後から得られる正式終端 receipt はこの API 内では検証せず、上流 job の完了証拠と混同しない。
全物理状態の再 decode、anchor MC 再実行、精度・被覆保証は行わず、保存 audit の範囲を flags と警告に残す。

## 軽い受入

1. 新証拠で作成・読取が成功し、旧 singleton reader を呼ばず、mode/source/receipt/hash の変更を拒否する。
2. 全 768 group と 192 replicate を保持し、失敗・未定義・区間欠損が集計分母に残る。
3. iterator 終端の欠損・余剰・counter 不一致・入力/source 変更を拒否する。
4. 実保存 group の元 read_group/verify_group と新 wrapper の結合を少数 fixture で確認し、全 768 の contract fixture と分ける。
5. analysis terminal/receipt/native/script の不一致、missing partition、重複実行を拒否する。
6. mocked scheduler で qsub 一回・最大 2 nodes・controller・shared lock・曖昧応答・bundle/source/path 改変を確認する。
7. 新最終 reader が全 iterator を消費し、audit terminal と raw/marker の変更を拒否する。
8. summary/WSS CLI の純粋 helper 再利用、reference auditor 一回、partial flags、入力不変と排他出力を確認する。

各 test file は 60 秒以内とし、実 production の全走査・再計算は未実施と記録する。
