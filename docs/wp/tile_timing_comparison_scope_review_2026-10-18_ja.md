# 独立計時比較の科学的範囲と追加仕様案

本レビューは BAR main の結果が未取得の時点で固定する。
既存の計時・精度判定 source、閾値、候補、seed、cohort は変更していない。
qsub、直接 MC の再実行、BAR 計算、raw payload の全走査は行っていない。
保存 MC summary のみの軽い再集計は [実行 script](data_tile_validation_2026-10-17/reassess_mc_timing_summary_v1.py)、[全 8 条件 JSON](data_tile_validation_2026-10-17/timing_mc_achieved_precision_v1.json)、[日本語短文](data_tile_validation_2026-10-17/timing_mc_achieved_precision_v1_ja.md) に保存した。

## 現行判定で正しく保持されること

`tile_timing_metrics.compare` は両手法の全 192 replicate の経験的相対 RMSE が、有限 reference 区間全域で epsilon 以下の場合だけ平均 task wall と平均 process CPU の比 MC/BAR を出す。
予定 epsilon や MC の予算式だけでは比を出さず、点推定欠損、reference_sensitive、empirical_above_target では比を null とする。
同関数は失敗 task の消費時間も含め、費用の欠測時には取得例だけの平均を全 cohort の平均としない。
`tile_precision_assessment.assess_condition` と `tile_summary.summarize_condition` は bias、RMSE、reference 点・全区間・交差の被覆を別々に計算し、失敗・区間欠損を 192 の分母から除かない。
区間のない点推定でも点が全件あれば RMSE gate を通り得るが、それは区間被覆の合格ではなく、現在の事前仕様どおりである。
この数学的 gate の変更は不要である。

実 MC は各条件 192 件、合計 1536 件が成功し、区間欠損は 0 件である。
そのうち within は 4 条件、above は 2 条件、reference_sensitive は 2 条件だった。
case0 の epsilon=.2、case3 の epsilon=.2 は above、case1 の epsilon=.2、case3 の epsilon=.1 は reference_sensitive である。
後者 4 条件は BAR が通過しても現行 gate の時間比を null とする。
現在は BAR main 未評価なので、全条件の実比較は未取得である。
追加 MC、事後の閾値変更、失敗条件の除外で値を通すことは本レビューの提案に含めない。

## 選択・評価・reference の独立性

候補は既存校正の 192 replicate で選び、選択後の BAR stage140 と MC stage121 の 192 replicate を評価に使う。
`tile_select_timing.POLICY` は全点取得と経験的相対 RMSE の上端だけを eligibility とし、診断・区間取得を選択 filter にしていない。
保存された全 8 候補は flagged=192、high_rhat=192、low_ess=192 であり、全候補の区間取得は 192 件でも reference 点被覆は 84.375%–90.104%だった。
これは独立計時のための固定候補であり、混合、名目95%被覆、推奨、最速の認定ではない。
選択順位は総提案 step 数と固定 tie-break であり、実時間の最小化ではない。
実際の候補は全て ZH・logical 初期化・cross_chain である。

MC 予算、BAR 候補選択、独立評価は同じ有限 direct-MC reference を参照する。
評価用乱数が新しくても、reference 誤差まで別の独立標本で再評価したことにはならない。
99.9% Wilson 区間は確実な真値集合ではなく、4 case・8 判定の同時保証でもない。
経験的 RMSE 範囲は reference 値を動かした範囲であり、192 replicate の母 RMSE 信頼区間ではない。
同じ epsilon 以下を両方が満たす場合も、両手法の達成 RMSE が厳密に等しいこと、最小必要時間へ達していること、母時間比がその値であることは示さない。
最終表は「固定 epsilon を経験的に満たす設定の task 費用比」とし、最適 time-to-accuracy curve や速度保証とは呼ばない。

seed は共通 master の SeedSequence 入力に stage を入れて生成し、MC benchmark=121、MC capacity=122、BAR benchmark=140、BAR capacity=141 を分離する。
reference は stage21、元校正 sampling は stage31、anchor は stage32、bootstrap は stage33 である。
[追加 BAR seed 全数監査](data_tile_validation_2026-10-17/bar_seed_census_evidence_v1/REPORT_ja.md) は計 56 namespace・3,963,562 件、未検査 0、予期しない衝突 0 を確認している。
既知の共有 8,448 件は校正 stage33 と synthetic resource bootstrap の意図共有であり、独立計時の評価標本とはしない。
有限 seed 非衝突は乱数 stream の数学的独立性の証明ではなく、実 task metadata の seed 一致検査も別に必要である。
logical 初期化の index は replicate と chain の決定的な配置を維持するため、新 seed は初期 logical sector の新たな無作為化や未検証 sector への一般化を意味しない。

## 時間・環境の比較範囲

MC の保存 job は node011 の 96 workers、全 8 条件を一つの pool で実行し、phase wall=226.897983454 秒、task CPU 合計=21183.545013858 秒だった。
PBS wall=230 秒、PBS cput=21265 秒であり、worker task 時計と job 時計の scope が違うため同一値を要求しない。
MC は重い条件を先に並べ、BAR は case 別の選択条件を task 順で実行する。
したがって pool の占有、負荷、最後の少数 worker の区間が異なり、phase wall を条件数や task 数で按分した speedup は作らない。
task wall は OS 待ちや同時実行負荷の影響を受け、process CPU も CPU 世代・周波数・cache・NUMA から自由ではない。
現在の native profile は platform、machine、native binary、Python、依存版、thread 設定と有限 decoder probe を検査するが、CPU model・frequency・affinity・NUMA・当時の負荷を検証していない。
hostname が違うだけで decoder が違うとは限らず、同じ native profile だけで性能条件が等しいとも保証しない。
今後の BAR の hostname・PBS allocation・native hash と MC を併記し、未記録の性能条件は unknown として、実観測された未補正費用比の scope を明示する。
同一 hardware を新たに証明できないことを理由に既存 MC を事後再実行する提案はしない。

BAR task 時計には構築、独立 anchor、初期化、sampling、compact の再 decode、BAR 解析を含み、artifact 書込みを含まない。
MC task 時計には構築と direct MC を含み、artifact 書込みを含まない。
native preflight は phase 計時の外、pool 起動と artifact 書込みは phase 内である。
これはこのライブラリと保存方式の費用比較であり、診断を含む別 pipeline、別 decoder、bootstrap を省く別 estimator の時間へ外挿しない。

## main と低ノイズの評価範囲

現在の固定 direct-MC 計時予算と BAR stage140 の候補は、main の tile72 の p*=.03、tile288 の p*=.05 の bit-flip/depolarizing、計 4 case × 2 epsilon だけを対象にする。
`tile_bar_time_benchmark.make_plan` は main の校正 grid を参照し、低ノイズの target=.01/.003/.001 をこの計時に含めない。
低ノイズの科学計画は [低 p 計画](tile_low_noise_plan_2026-10-18_ja.md) に別途あり、同精度時間は独立計時 cohort で測り、低 p production の終了時間で代替しないと既に明記されている。
低ノイズの独立計時 cohort を作る固定 manifest・比較実行は、今回確認した main 計時入口からは得られず、現時点の評価範囲外である。

低ノイズの保存 raw record から得られるものは、全長 chain の wall/CPU、構築・初期化・sampling・compact の wall、独立 anchor の全費用、各 sampling/analysis job の phase wall と資源である。
`tile_low_noise_analysis` の各解析 row は `sampling_seconds_full_traces`、`initialization_seconds`、`anchor_seconds`、`estimation_seconds` を保存する。
前者は選択した rung/chain の全長 trace の費用であり、短い window や小さい burn を単独実行した費用ではない。
同じ全長 trace と anchor を複数 window・ladder・誤差法で再利用するので、row ごとの費用を全設定に足したり trace 長比で短い独立計時へ換算したりしない。
`estimation_seconds` はその row の推定計算であり、共有診断・I/O・初期化などを含む全 pipeline 時間ではない。
capacity 外挿や synthetic analysis profile は allocation 用であり、科学的 time-to-accuracy の実測には使わない。
これらから報告できるのは実行全体と全長 task の費用・設定整合性であり、現状の保存値だけでは低ノイズの同精度速度比を評価できない。

低ノイズ WSS は未評価 weight tail を含む区間 reference として `tile_weight_reference_comparison.assess_bounds` を通し、partial_estimate を full point としない。
保存済み `weight_reference_summary_v1.json` の例では、tile288-bit の p=.01 の区間は約 [3.34e-8,1.04e-5]、tile288-depolarizing の p=.003 では約 [7.96e-20,8.72e-7] である。
この数値は保存区間の読取りであり、今回 WSS の全 raw 監査や再合成をした結果ではない。
一般に正の区間 [L,U] 全域で相対 RMSE<=epsilon を満たすには、少なくとも標本平均について U(1-epsilon)<=L(1+epsilon) が必要である。
現在の tile288 の低ノイズ区間は 10%・20%についてその必要条件さえ満たさないほど広く、設定間の一致でこの reference の識別力不足を補うことはできない。
reference 下端0・区間過大・reference欠落では、それぞれの理由を保ち、単に「BAR が遅い」「BAR が正確」などと解釈しない。
新しい reference や低ノイズ計時をこのレビューで追加せず、最終報告は main の独立計時結果と、低ノイズの費用記録・reference付き整合性評価・同精度時間未評価を分けて示す。
低ノイズの同精度計算時間まで検証完了したとは扱わない。

## 実比較前に補う最小仕様案

既存 `tile_timing_metrics` の数式と gate は変更せず、新しい薄い報告 adapter または実行証拠 wrapper だけで次の境界を追加する。

1. 入力として固定された selected settings hash と選択根拠、MC/BAR benchmark manifest、reference summary/audit、seed census 証拠を外部 pin で指定する。
`tile_bar_time_benchmark.make_plan` は候補 grid と hash 形式を検査するが、比較入口自身は選択 provenance の回収 pin を再検証しないため、受理済み実候補との結合を明示する。
2. 全 8 条件を必ず出し、選択校正の診断・bias/RMSE/被覆と独立評価の同じ量を異なる欄に保存する。
BAR の独立計時は mixing diagnostics を収集していないため、評価欄は not_collected とする。
`tile_timing_metrics.assess` は現在内部入力として BAR の flagged/undefined を全件 True にするので、その 192 を「実測された診断 failure 192 件」と表示せず、not_collected を表の一次状態にする。
この表示 adapter の追加は既存計時 source や判定を変えずに行える。
3. 比は既存 gate と全費用取得の両方を通った clock だけに出し、above/reference_sensitive/incomplete_points/費用欠損では null と理由・両手法の全精度量を残す。
BAR 未完了、条件未選択、計算失敗と診断未取得を互いに区別し、取得例だけで全体を合格にしない。
4. `load_cohort` の現在の metadata/hash 検査に、受理済み submission/script/正式 PBS F/exit/native/実 hostname/資源証拠の結合を外側で加える。
現在の比較 source は native と execution ID を検査するが、正式 terminal、submission script、resource allocation まで自分で検証していない。
入力の解決先と source closure、JSON/NPZ payload の終端不変を検査した範囲も明示する。
現在の `load_cohort` は各 payload を読取時に検証し、終端では marker 等を再hashするが、既に読んだ全 JSON/NPZ payload の再hashまでは行わない。
5. 数値依存の `tile_precision_assessment`・`tile_summary`・`tile_reference` を含む source closure を開始前と公開前に照合する。
現在の比較出力の直接 source 欄は比較 adapter と timing metrics のみであり、全数値依存の終端同一性をその欄だけから検証できない。
6. task CPU/wall、各 task phase、job phase、PBS wall、host/resource/native を別欄にし、性能環境の一致を確認した範囲と unknown を保存する。
CPU と wall を混ぜず、phase 比・最速設定・母精度・名目被覆保証を作らない。

## 最小の追加受入案

固定 8 条件を模した短い JSON fixture で、MC が above/reference_sensitive、BAR が within でも比が null のままであることを検査する。
全点取得だが区間未取得の行、失敗点、費用欠損、BAR 未実施を別々に与え、192 分母・理由・利用可能量が保存されることを確認する。
選択側 flagged=192 と評価側 not_collected を与えても、独立評価の実測診断 failure と混ぜないことを確認する。
同じ reference を共有する選択/評価を許容しつつ、その依存と有限 reference の scope が消えないことを確認する。
selected settings pin、source helper、native hash、job ID、terminal、script、resource、payload、解決先の改変を拒否し、source/input の終端変更では結果を公開しない。
host が異なる場合に同一 CPU だと推測せず、未補正 task 費用比と性能環境 unknown を併記し、job phase の按分値を作らないことを確認する。
母 RMSE や時間比の信頼区間を新たに作る bootstrap、追加 MC、別 seed、閾値変更、再選択は追加要件に含めない。
実装へ進む前に親へ本案を提示し、現在はレビューと保存 summary の演算だけを完了した状態である。
