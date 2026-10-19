# 低ノイズ独立計時の manifest・seed 接続案（第2段階）

[独立計時仕様](tile_low_noise_independent_timing_spec_2026-10-18_ja.md) の第2段階について、実装前の最小仕様と受入案を保存する。
本書だけでは stage の正式登録、manifest の作成、全数 seed 監査、sampling、qsub は行わない。
既存 frozen source と過去の監査証拠を変更しない。

## 参照した現行契約

`tile_study.seed` は master=2026101719 と固定 version=1 を先頭に置き、`SeedSequence([MASTER,1,*coordinates,purpose]).generate_state(1,dtype=uint64)` を整数 seed とする。
`tile_seed_audit.catalog` と現行 seed producer には stage 21、31–33、99、100、110、121、122、130、140、141、150–155 があり、旧 pilot は case を先頭座標とする別形である。
今回の source 検索では stage 160–163 の利用を認めなかったが、番号の未使用だけから出力 seed の無衝突を結論しない。
最新の正式な追加全数監査は job 265253、56 catalog namespace・3,963,562 entries、未検査 0、予期しない衝突 0、意図的共有 8,448 であり、stage 140/141 も列挙済みである。
一次保存証拠は `data_tile_validation_2026-10-17/bar_seed_census_evidence_v1/independent_verification.json` と同階層の正式 result/manifest/PBS/source である。
その独立照合 JSON の SHA256 は a480854ea51d32056f6baa72f0720e560481e63ab1681470d52fe4e51ace214d、正式 result の SHA256 は b61653309ca8e87ea315ab8dd46f05c1e4ad8e2a4fa642a67da6d590dcaa4116 である。
48 namespace・3,855,274 entries の先行監査へ戻して stage 140/141 を未列挙扱いにしない。
この最新監査にも本書の新 role は含まれていない。

## 固定 selection と manifest

selector の全 24 行を case=0..3、target_index=0..2、epsilon_index=0..1 の辞書順で保存する。
接続予定 API は selector の `identities()` と `report['rows']` であり、選択設定は `selected_condition`、有限 reference は `reference_interval`、校正分母は `calibration_replicates=192` から取得する。
selector の status/reason と全 candidates/classification_counts は選択証拠として保持し、後段の計画可否 `planning_status` と混同しない。
case は既存 CASES、target_index は (.01,.003,.001)、epsilon_index は (.2,.1) と固定対応し、表示用 float や selected 行内の連番を seed identity にしない。
同じ BAR 設定を選んだ epsilon 2 行も別 identity のまま保持する。
全校正・WSS の完了が未取得の selection_pending から実行用 manifest を作らず、完了した selector の immutable bytes/hash と正式 digest を外部 pin する。
reference の未取得・L=0・幅による ineligible・unmet は selector の正式 status/reason のまま行に保持し、これらの行から sampling task や seed allocation を生成しない。
不正 artifact、native/runtime/prior 不一致は ineligible ではなく validation failure とする。
selected 行だけに MC budget と BAR 設定を結び、変更済み selection を同じ stage の別 cohort として受け付けない。
将来の選択・reference・科学設定変更は新 version と新 stage 登録・再監査を要し、既存 manifest を書き換えない。

科学 manifest は role 別の 4 個とし、それぞれ全 24 行、selection digest、master/version、stage、replicate 範囲、計画 seed 件数を保存する。
MC/BAR と capacity/main に共通する identity・固定 decoder prior・reference interval とその証拠 pin・source closure・package/Python/native/thread 契約を結ぶ。
BAR 行には selected condition の kernel/init/chains/burn/samples/ladder/method/block、ordered rung values、各 rung の元 fine-ladder index、anchor_trials=16384、bootstrap_replicates=1000、cache と初期化規則を保存する。
低ノイズ校正 source の設定を検証して転記し、数値が異なる場合に既定で補完しない。
MC 行は reference interval [L,U]、epsilon、丸め前整数予算、丸め後予算、予算式 version を保存し、partial_estimate を計算入力に含めない。
四つの科学 manifest と registry の hash 集合を別の audit-input manifest に結び、科学 manifest 自体へ後発 census result hash を埋め込んで循環参照にしない。
実行 root と資源・replicate partition は別 envelope として科学 manifest を参照し、資源変更で seed 集合を変えない。
selected が 0 行でも 24 行と全 role の零予定件数を保存し、実行 root や空 qsub は作らない。

## 新 role と座標

以下の番号は本仕様での予約提案であり、実装時に一つの versioned registry と authority source/hash に固定する。

| role | stage | replicate | capacity workers |
| --- | ---: | --- | ---: |
| low_timing.mc.benchmark | 160 | 0..191 | 該当なし |
| low_timing.mc.capacity | 161 | 0..1 | 2 |
| low_timing.bar.benchmark | 162 | 0..191 | 該当なし |
| low_timing.bar.capacity | 163 | 0..1 | 2 |

MC の entropy 座標は `(stage,case,target_index,epsilon_index,rep)`、purpose=0 とする。
BAR の entropy 座標は `(stage,case,target_index,epsilon_index,rep,kernel_id,init_id,rung,chain)` とする。
kernel_id は ZH=0/ZHS=1、init_id は logical_basis=0/logical_combination=1 に固定し、辞書の挿入順から推測しない。
BAR purpose は anchor=0、initialization=1、sampling=2、bootstrap=3 とする。
anchor と bootstrap の rung/chain は予約値 0/0、initialization と sampling は選択 ladder の local rung=0..R-1、chain=0..C-1 とし、purpose の違いで初段 chain と分離する。
anchor は各 estimator で新規に生成し、同じ prior の epsilon、replicate、capacity/main 間で共有しない。
bootstrap は一つの estimator に一つの RNG allocation とし、1000 bootstrap draw を別の seed entry に展開しない。
cross_chain にも固定 bootstrap allocation を記録して全数監査へ含めるが、実際に乱数を消費しない経路では `bootstrap_rng_consumed=false` を保存する。
同様に logical_basis の initialization allocation は監査へ含めるが、係数が決定的であることを記録する。
この allocation と RNG 消費の区別は故障による未到達段階にも適用し、未消費を追加独立標本として数えない。
role 別 seed generator と census adapter は同じ authoritative coordinate helper を使い、受入では手書きの期待座標との一致も確認する。
registry の番号だけでは旧 pilot のような可変長 entropy や uint64 衝突を排除できないため、新旧の全 entry を一つの census に通す。

初期状態は `tile_low_noise_study.logical_state` を再利用し、bit/depolarizing の基底順序を維持する。
`initialization_stride` は選択 chain 数ではなく元低ノイズ production の最大 chain 数（case0 は16、他は8）とし、index=`rep*initialization_stride+chain` を保存する。
logical_basis はその index と基底数の剰余で係数を定め、logical_combination は上記 initialization seed から非零係数を生成する。
各 rung の係数・物理初期状態・seed を記録し、失敗集合と有限 log probability を確認する。
新 seed が deterministic logical_basis の sector を本校正と異なるものにするとは主張しない。

## MC 予算と capacity の固定範囲

有効な interval は finite な 0<L<=U<=1 とし、epsilon は固定の 1/5 または 1/10 である。
`N0=ceil((1-L)/(L*epsilon**2))`、`N=64*ceil(N0/64)` を保存し、reference partial point、中点、観測失敗数を代入しない。
64 切上げと ceil は固定 JSON の L の十進表現を正確な有理数として処理し、巨大予算で浮動小数点の丸め落ちや整数 overflow を起こさない。
N=0 になる退化的な L=U=1 は本計時の正の試行数契約に合わないため、selector の status を変更せず後段 planning_status=`ineligible_degenerate_reference` で保持し、黙って 64 に増やさない。
大きい N は固定整数のまま残し、実行可能性は次段階の資源判定へ渡す。

capacity は selected identity ごと・MC/BAR ごとに先頭 2 replicate、2 workers を新結果を見る前に固定する。
最大 24 selected でも capacity は各手法 48 estimator、計 96 estimator であり、既存の条件ごと 96 replicate 計時を機械的に繰り返さない。
MC は full N、BAR は full anchor・全 R rung・全 C chain・burn+samples・全解析設定を一つの estimator task で実行し、trace/chain/trial を短縮しない。
2 task の並行によって最小限の同時使用メモリを測るが、2 replicate から裾の時間や失敗確率を保証しない。
96 workers の I/O/メモリ競合はこの capacity では測れないため、並列度を増やした資源外挿は未検証の見積りとして明示し、実測保証とは扱わない。
main は最大 2 ノードの範囲で各ノードの 96 CPU を活用する方針を維持し、capacity の 2 workers を main の並列度上限にはしない。
後続 resource planner は実測 task wall/process CPU、worker ごとの memory と pool の余裕、保守係数、artifact I/O と job phase の費用を使い、340 GiB・24h の上限内で worker 数と replicate partition を決める。
96 workers へ増やした場合の競合や memory の変動が保守係数で保証されるとはせず、要求根拠と未検証部分を保存する。
具体的な資源式・係数・分割規則は第3段階の実装前仕様で固定し、そのためだけの追加 capacity や新 stage を第2段階では要求しない。
主 cohort は全 192 replicate 固定とし、replicate 単位 partition を許すが、disjoint union が 0..191 と一致し、失敗・未取得とその費用を分母に残す。
capacity が timeout/failed/unavailable なら、部分結果の費用を成功 full estimator の profile として使わず、未計測または execution_infeasible を保持する。
資源上限は 1 node・96 CPU・340 GiB・24h、queued を含む最大 2 nodes とし、1 estimator でも入らなければ予算を削らず停止する。

## census 接続と投入 gate

selected identity 数を S、各 selected 行 i の rung/chain 数を R_i/C_i とすると、新 MC allocation は main=192S、capacity=2S である。
新 BAR allocation は main=`192*sum_i(2+2*R_i*C_i)`、capacity=`2*sum_i(2+2*R_i*C_i)` である。
従って追加全予定件数は `194*sum_i(3+2*R_i*C_i)`、既存集合が変わらない場合の全予定件数は `3,963,562+追加件数` となる。
新 logical seed role は MC 2 個と BAR 4 purpose×2 cohort の 8 個、合計 10 個であり、既存報告の 56 catalog namespace という plan 単位の数え方と混同しない。
新 adapter の catalog namespace は role ごと四つの manifest 単位に固定し、零件も明示するため新旧合計は 60 catalog namespace とする。
role/purpose 別件数、row 別件数、manifest/source/registry hash、master/version、全順序を census 計画へ保存する。
既存 56 namespace を生成した固定 source と全旧 manifest を保持し、新 adapter がその stream と新 stream を連結して既存 census engine へ渡す。
旧 result の unique 件数だけとの比較や新 entry 同士だけの監査で、新旧の出力 seed 衝突検査を代用しない。
既存 stage33 の calibration.bootstrap/synthetic.bootstrap の同一 entropy 8,448 件だけを従来どおり意図的共有とし、新 role 間の同一 entropy は許可しない。
期待件数・完走・予期しない衝突0・意図共有の予定件数・入力前後 hash のすべてを照合し、hash input が異なる過去の census 成功で通過させない。
既存 engine の bounded pilot は計画の一部確認にすぎず、partial/timeout/未列挙 role を full としない。
最新全数監査は約25分であり、次の全数 census は local の軽い受入へ含めず、別の許可された qsub 手順と資源で実行する。
全 manifest と registry/source が固定され、この追加全数監査の正式 F/exit0 と result が結合する前は、新 capacity も qsub 不可とする。
全数 seed 非衝突は乱数 stream の数学的独立性、実行記録の seed 一致、科学的精度や被覆の証明ではない。

## 第2段階の軽い受入案

1. 24 identity の順序・重複・欠落、非 selected 行の保持と零 task、同設定でも epsilon 別 identity を確認する。
2. pending や不正 evidence から実行 manifest を作らず、native/prior 不一致を ineligible に変換しない。
3. L=.01、epsilon=.1 で N0=9900/N=9920、epsilon=.2 で N0=2475/N=2496 を確認し、partial_estimate の変更だけで予算が変わらないことを確認する。
4. ceil 境界、64 境界、極小 L、非 finite、bool、不正区間、L=1 退化例を小さな有理数 fixture で検証する。
5. 手書き期待座標と authoritative helper、case/target/epsilon/rep/purpose/main-capacity 間の区別、logical stride と selected rung mapping を確認する。
6. S=1、R=2、C=4 の fixture で MC 194、BAR 3492、追加計3686 allocation と purpose 別件数を検証し、S=0 の四 manifest を零件として保持する。
7. 旧 catalog namespace と新 role の区別、実行 seed helper との一致、同一 entropy 別 role と意図しない uint64 衝突を小 stream の注入で拒否する。
8. 既存意図共有だけ許可し、同じ新 stage の別 selection/version、既存 stage 再登録、未知 purpose、途中変更 source/manifest を拒否する。
9. 古い全数成功、partial census、新 subset のみ成功、件数不足、registry 未列挙では capacity/main の gate を通さない。
10. capacity が 2 replicate/2 workers かつ full estimator dimension、main が192で、partition が同じ seed 集合を分割するだけであることを確認する。

ここまでの受入は計画と seed の小 fixture のみとし、sampling driver、native 実測、全数 census、submitter の実装・実行は後段の別仕様で扱う。

## 第2段階 primitive の実装境界

新 `tile_low_noise_timing_plan.py` は `read_selection(path,expected_sha256)`、`mc_budget(interval,epsilon_index)`、`make_plans(selection,selection_sha256=...)`、`validate_plans(bundle,expected_registry_digest=...)`、`tasks(plan)`、`seed_coordinates(plan,task,rung,chain,purpose)`、`task_seed(...)` を提供する。
make_plans は四 manifest と selection に結合した registry を返す純 builder であり、ファイルを保存しない。
selection は正式 selector envelope、全24行、全12 calibration binding、current source と一致する production plan、full candidate 集合と同じ再選択結果を検査する。
read_selection は外部 pin と単一 byte snapshot、source closure を検査するが、巨大な input_sha256 の raw payload を再走査しない。
この読取範囲を明記し、正式 selector の外部受入 pin を信頼境界として、後段の正式 terminal/PBS verifier を代用しない。
新 `tile_low_noise_timing_seed_audit.py` は `entries(plan)`、`planned_counts(plan)`、`extend_catalog(legacy_factories,legacy_evidence,bundle,baseline_evidence_sha256=...)` と `complete_census_gate(result,evidence,expected_evidence_sha256=...)` を提供する。
extend_catalog には旧正式全数 result とその canonical object digest（baseline_result/baseline_result_sha256）、外部固定 expected_registry_digest も必須とする。
これら object digest は元 JSON ファイルの byte SHA256 と別であり、後段の保存入口は元 bytes の外部 pin を先に検証する。
旧 catalog の plan 単位件数から purpose 別件数を推測せず、旧全数 result の checked_counts へ結び、正式結果を自己申告値へ置き換えない。
extend_catalog は旧56 namespace・3,963,562件の固定 evidence digest と全 factory key を要求し、新四 manifest の別 namespace と source/input pin を結合する。
complete_census_gate は予定件数・完走・衝突・意図共有と固定 evidence の純数値整合だけを検証し、正式 qsub/PBS/native/実行前後入力照合は第3段階の runner/submitter が別に必須とする。
primitive の成功値を単独で投入許可として使えないよう、その scope を返却値と docstring に記録する。
