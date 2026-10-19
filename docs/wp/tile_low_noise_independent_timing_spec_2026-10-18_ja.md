# 低ノイズ独立計時の最小仕様案

本書は既存 [低 p 計画](tile_low_noise_plan_2026-10-18_ja.md) の「同精度までの時間比較は独立計時 cohort で行う」を未完了の目標として具体化する。
実装前の提案だけを保存し、新 sampling・MC・BAR・WSS・qsub を実行しない。
main の stage121/140 計時が完了しても、本仕様の低ノイズ独立計時を完了扱いしない。
低ノイズの raw 全長 trace 費用、capacity 外挿、synthetic profile、短い window の長さ比例配分を独立計時として使わない。

## 条件と選択の順序

対象は tile72/288 × bit-flip/depolarizing × target=.01/.003/.001 × epsilon=.2/.1 の固定 24 行である。
各選択行には、本校正の全 192 replicate・全予定設定と同じ fixed decoder prior・native/runtime の独立 WSS reference を結ぶ。
本校正の sampling、anchor、BAR analysis、full trace audit、最終 collection、WSS reference 監査の終端が揃った後にだけ選択を固定する。
完了した subset や成功 seed だけから候補を先に選ばず、未完了の間は `selection_pending` と全 24 行を残す。
本校正と reference の完了証拠の外部 pin、source closure、予定設定、finite reference 区間を selection manifest に保存する。
既存 `tile_low_noise_summary` と `tile_weight_reference_comparison.assess_bounds` の全 cohort 検証・数値を使い、partial_estimate を真値点にしない。

reference 未取得、下端 L=0、または幅だけで目標不可能の場合は、計時候補を作らず ineligible を保存する。
正の reference 区間 [L,U] 全域で相対 RMSE<=epsilon が成立するための必要条件は `U*(1-epsilon) <= L*(1+epsilon)` である。
これは標本平均 mu に `U*(1-epsilon) <= mu <= L*(1+epsilon)` が必要なことから従い、標本分散があれば更に厳しくなる。
epsilon=.2/.1 はこの必要条件をそのまま使い、reference 幅による ineligible を精度が悪い BAR の実測値や decoder failure に読み替えない。
境界に等しい場合は width だけで拒否せず、全 cohort の実測 gate で判定する。
この early gate は精度判定を緩和するものではなく、既存の reference 全域 gate に合格できないことの明示である。
現在の tile288 低ノイズ reference のように幅だけで不可能な場合は、`ineligible_reference_width`・L/U・epsilon・必要条件の両辺を正式保存し、速度比は null とする。
native/runtime/prior不一致や不正 artifact は科学的 ineligible に変換せず、検証 failure として選択を停止する。

width gate を通る場合も、各設定の全 192 点取得と reference 区間全域での経験的相対 RMSE<=epsilon を要求する。
区間欠損・診断未定義・未収束 flag を分母から除かず、診断と被覆を eligibility の代用品にしない。
診断・被覆を選択 filter にしない場合は main と同様に独立評価候補だけを意味し、推奨設定とはしない。
候補順位は rung 数×chain 数×(burn+samples)、cross_chain、block 小、ZH、logical_basis、最後に canonical condition の固定順とする。
この順序は結果を読む前に本仕様で固定し、時間の最小化や良い seed の選択ではない。
eligible 候補がなければ `unmet_empirical_precision` と全設定の分類件数・欠損・diagnostics を保存する。
tile72 で候補が通った場合は新しい独立計時 cohort へ進めるが、符号サイズだけで通過を仮定しない。
tile288 も同じ gate を適用し、将来新しい reference に置換する場合は旧選択を上書きせず別仕様・別 manifest とする。

## 独立評価の最小計画

selected の各行で BAR と固定予算 direct MC をそれぞれ新規 192 replicate 実行する設計とする。
選択元の trace、anchor、seed、timing capacity、WSS draw を評価標本へ再利用しない。
同一 prior の epsilon 2 条件が同じ BAR 設定を選んでも、epsilon identity ごとに別の固定評価 cohort を使う。
BAR は選ばれた burn・samples・chains・ladder・kernel・initialization・uncertainty と既存 anchor trial 数を単独実行し、replicate ごとに fresh anchor を使う。
初期状態は既存 `logical_state` の bit/depolarizing と logical_basis/logical_combination の意味を維持し、低ノイズ計画の stride/index 規則と初期係数を明示保存する。
sampling の乱数だけを変えて初期 sector 分布が新たに検証されたとはしない。
新 driver は科学的な既存関数を再利用し、旧 main driver の manifest を低ノイズ値で書き換えたり旧 sampling の stage を流用したりしない。

direct MC の予算は WSS full interval の正の下端 L に対して `ceil((1-L)/(L*epsilon**2))` を 64 試行単位で切り上げる。
reference の partial point をこの式へ入れない。
この予算は真の確率がその有限区間内にある場合の固定 Bernoulli 母 RMSE についての条件付き計画であり、実 192 cohort の通過保証ではない。
試行数が大き過ぎる・resource が上限を超える場合は `execution_infeasible` と固定予算を保存し、試行数・seed・trace を縮めず、速度比を null にする。
観測失敗数に基づく早期打切り、成功 seed 置換、追加 replicate、結果を見た予算再設定はしない。

計時 role は少なくとも low_timing.mc.benchmark/capacity と low_timing.bar.benchmark/capacity に分ける。
BAR 内で anchor、初期化、sampling、bootstrap の purpose を分離し、case/target/epsilon/replicate/rung/chain の全入力座標を固定する。
整数 stage 番号は本書ではまだ割り当てず、実装時に registry と既存全 namespace を確認して固定 manifest に登録する。
これらの新 role は既存 56 namespace の全数監査対象外である。
新 main/capacity manifest と固定選択集合を既存全計画へ追加した次の全数 seed census が成功する前は、capacity を含む新 sampling を投入しない。
有限非衝突と予定件数を保存しても乱数 stream の数学的独立性は保証せず、実記録の seed/model/native 一致を別途検証する。

## 資源・保存費用・比較

同じ frozen Linux package/native と single-thread 条件を使い、各 selected 設定の full-dimensional capacity を別 seed で測ってから資源を決める。
capacity の未知の実行時間を短い trace の線形外挿だけで確定しない。
既存 1 node 上限の 96CPU・340GiB・24h と、queued を含む最大 2 nodes、shared lock、controller 非競合、qsub 一回、曖昧応答時の停止を維持する。
必要な partition は replicate 単位とし、一つの estimator の anchor・全 rung/chain を同じ測定 task に含める。
partition の disjoint union は元 192 replicate と完全一致させ、追加計時の分割を新しい科学標本としない。
本仕様で partition 実装まで行うかは資源設計時に固定し、1 replicate でも上限を超える場合は実行不能で停止する。

task ごとに wall/process CPU、構築、anchor、初期化、sampling、compact、解析を保存する。
artifact 書込み、native preflight、pool/job phase、PBS 経過時間は別 scope とする。
全予定 task の failed/unavailable と消費費用を残し、完了した job だけの平均を全 cohort の平均にしない。
比較時は同一 WSS interval に対する実評価 cohort の相対 bias/RMSE 範囲と区間 entire/possible 被覆を既存 bounded helper で再計算する。
reference point の RMSE・被覆は作らず、MC/BAR とも全域で目標を満たして費用が全件ある clock だけに平均費用比を出す。
設定整合性、狭い自称区間、partial WSS、reference幅不明から precision 達成や速度優位を補完しない。
BAR 混合診断を計時で取らない場合は not_collected とし、本校正の診断を独立計時の測定値として代用しない。
host/CPU/thread/native/並列度が一致した範囲と unknown を示し、未補正の実 task 費用比として報告する。
母精度、母時間比、名目被覆、最速設定、独立 reference のない領域への外挿は保証しない。

## 提案する実装単位

第一段階は新しい selector と保存 report だけとし、24 行の pending/ineligible/unmet/selected と source/input/reference pin を扱う。
第二段階で selected 行に対する新 manifest/seed role/budget builder と census adapter を追加する。
第三段階で独立 MC/BAR timing driver、capacity/resource、qsub submitter、完全 artifact/terminal/native verifier を追加する。
第四段階で bounded reference 用の独立評価・費用報告 adapter を追加する。
既存 main timing の point-reference 比較 helper をそのまま WSS midpoint で呼ばず、bounded helper と同じ定義を使う。
新 seed registry、全数監査、資源、source closure、全後続 verifier が揃う前に新 job を投入しない。
本提案の保存時点では全段階が未実装・未計測であり、goal の低ノイズ同精度時間は未完了である。

## 軽い受入案

1. 全 24 identity、各設定の全 192 分母と pending 状態を保持し、本校正未完了・native不一致・reference不一致から選択しない。
2. 幅だけで不可能な [L,U]、等号境界、L=0、reference未取得を列挙可能な数値 fixture で区別し、ineligible でも行と比 null が残る。
3. 幅が狭くても欠損点・実測 RMSE 不通過なら selected にせず、全候補の deterministic ranking と設定順序不変性を確認する。
4. partial_estimate を変更しても full interval による MC budget を変えず、interval変更時は別 pin として拒否し、64単位切上げを確認する。
5. metadata上の比例配分・window長比・shared anchor 二重計上を独立 task timing として受け付けない。
6. 新 seed role/番号が未登録・未監査なら capacity/main とも投入不可とし、既存 census 成功だけでは通過しない。
7. 小さい実 code fixture で fixed prior、初期係数、fresh anchor、全 trace、seed purpose、直列/並列順の同じ科学出力を確認する。
8. 192 replicate の分割 union、failure/unavailable保持、formal terminal/native/source binding、二重投入・既存 output・2 node・controller・曖昧qsubを mocked scheduler で確認する。
9. bounded reference と同じ範囲全域の実評価 gate を使い、MC未達またはreference_sensitiveなら BAR が通っても比 null とする。
10. 同精度未評価、実行不能、reference幅による識別不能を、費用未計測・BAR精度未達と混同せず日本語報告へ残す。

全て 1 test file 60 秒以内の小 fixture とし、本番 sampling や全 seed census は local 受入へ含めない。
仕様・受入案を親へ提示した後に実装範囲を確定する。
