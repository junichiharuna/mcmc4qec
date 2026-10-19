# 低ノイズ独立計時の評価・日本語報告案（第4段階）

本書は実装前の小仕様であり、実装・受入実行・sampling・qsubを行った記録ではない。
[全体仕様](tile_low_noise_independent_timing_spec_2026-10-18_ja.md)、[第1段階の選択](tile_low_noise_timing_selection_spec_2026-10-18_ja.md)、[第2段階のmanifestとseed](tile_low_noise_timing_manifest_seed_spec_2026-10-18_ja.md)、[第3段階の実行と終端検証](tile_low_noise_timing_execution_spec_2026-10-18_ja.md) を受ける。
対象はcase 0..3、target index 0..2（p=.01/.003/.001）、epsilon index 0..1（.2/.1）の固定24行である。
候補・選択規則・閾値・reference・seed・MC予算・BAR設定を変更しない。
以下の第3段階API名は現在の実装に基づく接続案であり、実装開始時に受理済みfreezeの契約と照合する。

## 最小の実装境界

追加予定は `cluster_scripts/tile_low_noise_timing_evaluation_report.py` と対応する受入test fileの各1本である。
既存selector、plan builder、execution runner、数値helper、main報告adapter、旧bundle/sourceは変更しない。
main報告adapterは固定8行と旧manifestへ結合しているため、その `run` へ低ノイズ入力を渡さない。
同adapterの外部pin、入力状態snapshot、完了reader接続、公開前再照合、日本語renderの構成を再利用する。
pure数値評価には `tile_weight_reference_comparison.compare_condition` / `assess_bounds`、費用には `tile_timing_metrics.cost_summary` を再利用する。
WSS区間の中点やpartial estimateをmain用の点referenceへ渡して `tile_timing_metrics.compare` を呼ばない。
既存bounded helper内のlegacy bridgeを利用する場合も、中点依存量が破棄された公開結果だけを報告し、`reference_point=null` とする。

`prepare(config_path, expected_sha256, output_plan)` は外部pinと軽いmetadataを確認し、新しい固定報告planを排他的に作成する。
`run(plan_path, expected_sha256, output_root)` はPBS内で保存済み全taskの検証・評価を行い、全24行の `report.json` と日本語報告を新rootへ保存する。
`render(report_path, expected_sha256, output_path)` は固定reportから日本語表示だけを作り、raw再走査・再推定・再選択を行わない。
比較用jobの資源計画と親の一回投入wrapperは別工程とし、本仕様では新しいscheduler policyや自動qsubを実装しない。
全payload走査はPBS guard後に限定し、loginでのprepare/renderはmetadataだけを扱う。

## 入力と証拠の接続

configは受理済みselection、4種の科学manifest bundle、registry、正式seed census、固定WSS summary/auditと回収証拠、各capacity/main partitionの実行envelope・親receipt・実script・正式PBS終端証拠のpathと外部SHAを持つ。
external pinを今回読み取った値から自己承認せず、既存の受理済み回収・準備記録に結合する。
各24行のidentity、selection status、選択condition、full reference interval、MC整数N、rung/chain/burn/samples/anchor、seed allocationと消費区分は第2段階のbuilderをauthorityとする。
別のselection/source/registry/referenceへ差し替えたmanifestを、同じidentityという理由で統合しない。
正式censusは旧56と新4 namespaceの全予定allocation、未検査0、想定外衝突0、意図的共有の固定件数と実PBS終端を結ぶ既存gateを再利用する。
例外として全24行でselected=0かつ新allocation=0なら、[census bridge仕様](tile_low_noise_timing_census_bridge_spec_2026-10-18_ja.md) の `not_required_no_allocations` 証拠を結合し、新規censusの実行を要求しない。
この場合は全24行をnull比で報告し、旧56 namespaceの証拠と追加監査不要を区別して、60 namespace監査済みとは表示しない。
no-op証拠も科学bundle/registry/selectionの外部pinとbridgeの `read_plan` で検証し、selected行や新allocationがある入力へ流用しない。
bridgeの固定Python/PYTHONPATHを維持するため、別報告bundleからの接続は外部pinを起動前後に照合したread-only subprocessで `state_only(read_plan(root))` だけを呼び、30秒上限とする。
この検証はpilot/run/seal/submitを呼ばず、橋側の実行環境gateを緩めない。

| 入力 | 再利用する検査・追加する報告接続 | 本段階で拡張しない主張 |
| --- | --- | --- |
| selectionと本校正 | 外部pin・正式selector終端・全24行・全候補情報を保持する | 旧single readerが未確認の全job資源/run_countを遡って認証しない |
| WSS | 正式16条件監査・回収証拠と対象12条件の保存summaryを結合し、既存 `compare_condition` でstrataからfull区間を照合する | 全物理状態の再decode、真値、乱数streamの数学的独立性を証明しない |
| 計時capacity | `execution.completed` と固定resource decisionを照合し、2 task・主実行と別seedの費用を保存する | capacity標本を192主標本へ混入しない |
| 計時main | 全partitionの `execution.completed` と実PBS/receipt/scriptを結合し、正確なreplicate集合を確認する | 成功taskだけでcohortを作り直さない |
| 本報告 | consumed inputs/source/runtimeの開始前・公開前照合と報告job情報を保存する | compute内から自身のPBS Fを主張しない |

完了partitionは現在の `tile_low_noise_timing_execution.completed(root, terminal, expected_manifest_sha256=...)` を再利用する。
同readerのtask JSON/NPZ/marker、seed/model/failure/prior、native/profile、actual script/argv、親receipt、resource、run_count、hostnameの照合を迂回しない。
保存済みPBS証拠は親による実qstat取得と外部pinへ結合し、報告時の観測範囲・取得時刻を記録する。
元jobの実PBS終端とcompute内のexecution_complete markerを別々に確認する。
第3段階では全taskの保存と検証が完了した記録済み科学的failureを含む実行はF/exit0で完了し得るため、F0を全task成功と読み替えない。
非zero終端・kill・欠落artifactを記録済み科学的failureだけの完了へ読み替えず、現行readerが受理しない実行はincompleteとして比を出さない。
capacityは正常完了に加えfailed=0かつunavailable=0を必要とし、recorded failureを費用・分母に残しても主実行資源を受理しない。

手法・identityごとのpartition集合は固定resource planの全範囲と一致し、disjoint unionがreplicate 0..191となることを検査する。
duplicate、範囲外、別role、capacity混入、別manifest、未選択行への実行割当を拒否する。
capacity resource infeasibleは既存decisionと理由をそのまま保存し、科学的な精度不適格と区別する。
各rootの未実施・実行中・中断は固定manifestと実在するintent/receipt/summary/PBS観測から分類し、operatorが結果のよい行だけをcompleteと指定できないようにする。
complete宣言の入力不一致、外部pin不足、source/nativeの不一致はvalidation failureであり、科学的ineligibleや通常incompleteへ丸めない。

source closureはfunction-local importを含む既存AST方式と実import解決先を用い、package/Python/runtime/nativeとともに固定する。
消費したmetadata、全完了task payload、marker、receipt、scriptはlexical path・resolved path・consumed bytesのSHAを記録し、公開直前に再照合する。
同じbytesへのsymlink付け替えや読取中の変更も拒否し、旧rootは変更しない。
metadata状態のsnapshot後にpendingからcompleteへ変化した場合も同じ報告へ取り込まず、新しい報告planを必要とする。
開始前または終端照合が失敗したときは成功reportを公開しない。
入力・出力の排他と出力解決先を検証した後のfull読取・終端失敗は `validation_failure.json` へ保存する。
それ以前のconfig/source/snapshot等のpreflight例外は安全な出力先が未確定のため、呼出側がstderr/logへ保存し、本adapterは不明な出力先へファイルを作らない。

## 全24行・全192 replicateと欠測の保持

### 正式selector実行descriptorの最小接続案

selectorの専用実wrapperは本仕様更新時点で未実施であり、全12入力の準備後に親の一回処理として作成する。
configの `selector_execution` はprepared/intent/submission/script/execution/completion/terminalの外部pinを持ち、report自体はconfigのselection pinを使う。
preparedはpurpose=`low_noise_timing_selector_execution`、入力pin、report絶対path、selector実argv、固定resource、selector source path/SHA、runtime、Python path/SHA、native bindingのpath/SHA集合を持つ。
submissionとintentは既存型のmanifest/command/script_sha256/resourceを持ち、submissionだけに実job_idを追加する。
executionはprepared digest、実job_id/hostname、input SHA、selector argv、source/runtime/Python/native bindingを保存する。
completionは同じ実行identityとreport SHA、終了時のsource/runtime/Python/native bindingを保存する。
readerはpreparedの実argvを既存selector CLIと照合し、固定scriptにその一回呼出しがあること、親receipt/script/実PBS F0/run_count1/resource/host、reportのinput_manifest_sha256とprepared input pinの一致を検査する。
native bindingは記録されたmetadata/binaryの固定を意味し、fresh native probeの実施や全物理状態の検証を追加で主張しない。
実wrapperがこのdescriptorを保存するまでは本番report prepareの必須入力が不足しており、pure数値fixtureの成功を正式selector終端へ代用しない。

各行はidentity、selection status、planning/resource status、MC/BAR別execution status、精度判定、clock別比とnull理由を別欄に持つ。
全行の比較目標は `planned_replicates=192` とし、未選択・資源不適格で実際のtask割当が0の行は `allocated_tasks=0` を併記する。
未割当192件を実際に失敗した192 taskとは表示しない。
selected行では全192 task identityを保持し、ok/failed/unavailable/not_started/interruptedと未検証・不明を区別する。
ineligible、selection_pending、capacity_failed/unavailable、execution_infeasible各理由、未投入・未終端・未完了も行を消さず、比をnullとする。
記録済みfailure、点なし、区間なし、全chain完了の有無、取得済み費用と欠測を保存する。
incomplete partitionのraw全監査を新設しないため、その未検証部分の点・区間・失敗数はunknownとし、0や成功数へ補完しない。
既に完了検証できたpartitionの件数や費用は検証済み部分として別欄へ保存できるが、192全体の平均・精度gate・時間比には使わない。

## WSS full区間による有限標本評価

WSSの対象case/prior、planned/available trials、chunk failure、confidence level/method、full [L,U]、partial estimate、omitted_mass_upperを保存する。
partial estimateと切捨てtail上界は補助情報であり、完全な論理誤り率の点referenceとしない。
availableなfull区間は既存weight synthesisとの一致を確認し、幅やtailを都合に合わせて短縮しない。
同じfull [L,U]をMCとBARの両評価へ渡す。

各完了cohortを `assess_bounds(..., replicates=192, interval=[L,U], thresholds=(epsilon,))` へ正規化して渡す。
出力にはbias_reference_range、rmse_reference_range、relative_bias_reference_range、relative_rmse_reference_rangeと既存precision classificationを残す。
既存helperのreference_unavailable、reference_zero_boundary、incomplete_points、reference_sensitive、empirical_above_target、numerical_range等を独自のwithinへ変換しない。
全192点がない場合はfull-cohort bias/RMSEを未定義とし、取得点だけの量を全体の精度と呼ばない。
区間被覆はfull reference interval全体を含むentireと、一部でも交わるpossibleの件数・192分母の率・既存Wilson95区間を保存する。
区間未取得は分母に残し、entire/possibleのどちらにも成功として数えない。
entire/possibleは未知の真値が[L,U]にある場合の経験的被覆範囲であり、95%名目被覆の達成証明ではない。
独立BARのmixing診断はnot_collected、MCはnot_applicableとし、校正診断を転記しない。
既存helper用のBAR flagged/undefined保守的placeholderを用いる場合は未観測placeholderと明示し、R-hat/ESSが不良だった実測件数として表示しない。

## 費用と比の条件

主比は固定192 taskの `mean(MC)/mean(BAR)` とし、paired ratioの平均を用いない。
MCとBARの両方が全192点を持ち、full reference interval全域で指定epsilonのempirical_within_targetを満たす場合だけ候補とする。
さらに比較するclockの全192費用が両手法で取得され、有限・非負かつBAR平均が正である場合だけ、そのclockの比を出す。
wallとCPUは独立に判定し、一方の欠測で他方を補完しない。
点精度gateと区間被覆は別であり、区間のみ未取得ならその件数を残し、点・費用の要件を独立に判定する。
MCのavailableは点・trialの正常取得を示すため、available=trueかつinterval=nullも192点のcohortへ保持し、区間未取得として別に数える。
gate不成立、未完了、費用欠測、ゼロ分母、数値範囲外では比をnullと理由付きで保存する。

主表示は既存task wallとprocess CPUであり、両者がartifact書込みを含まない範囲であることを明示する。
第3段階summaryにあるinclusive wall/CPUは、task payloadとouter fieldsを結合する既存reader経由で検証し、artifact費用を含む別の補助比として同じgateを適用できる。
payload JSONにinclusive費用が無いことを0とせず、summary内の対応taskとmarkerの結合を必須とする。
failed taskの費用も全費用集計に含め、取得例だけの平均はavailable_onlyと表示する。
未完了jobの取得済み費用和は観測された下限として保存できるが、全192の平均や完全なjob費用にしない。
construction、anchor、initialization、sampling、compact、analysis、artifact込みworker、pool、outside_pool、PBS wall/cputを区別する。
pool/phase/PBS時間をtask数や条件数で按分せず、主task比へ足し合わせない。
capacity全2 task・capacity job費用、selection/seed census/監査・報告処理費用は主192の比とは別表とし、未取得はunknownとする。
capacity由来の資源見積もりと実行時の実資源・実時間を併記し、見積もりを実測費用へ置き換えない。
partition数、workers、host、実node/CPU/memory、thread/native/packageを保存し、CPU model/frequency/affinity/NUMA/負荷の未記録値はunknownとする。
同一native profileを同一性能の証拠とせず、partition境界とhost差による未補正費用比較の限界を明示する。

## 日本語報告と適用限界

日本語表は全24行の選択、実行、点/区間数、bounded相対RMSE、entire/possible被覆、CPU比、wall比、null理由を省略せず示す。
全数値、全cohort状態、reference/tail、費用内訳、入力hash・環境・実行証拠への参照は機械可読JSONに保存する。
本文では有限WSS referenceを選択・MC予算・評価へ共用したことを明記し、評価referenceが選択から独立とは呼ばない。
referenceの各confidence levelは全条件同時保証ではなく、独立評価seedのcensusも乱数streamの数学的独立性を証明しない。
独立mixing診断未取得、有限native probe、未補正host/partition差、失敗・欠測、capacity別費用を限界として列挙する。
時間比は記録環境で経験的精度gateを満たした固定設定の記述量であり、最速設定・最小time-to-accuracy・母RMSE・母時間比・名目被覆の保証ではない。
本報告のcompute完了と正式回収完了を分け、報告job自身のF/exit・親receipt・script・resourceの確定は外部回収証拠に残す。
既存timing completed readerは保存BAR chainのinitial/final状態を検査・再復号するため、全体を「物理状態の再復号なし」とは表示しない。
全trace状態の再復号は行わず、BARの保存checkpoint検証とWSSのcurrent payload hash照合を別scopeとして記録する。

## 実装前の軽量受入案

1. 全24 identityと各192目標分母を小fixtureで確認し、未選択のallocated=0、未完了unknown、recorded failureを混同しない。
2. WSS full区間とtailを既存synthesisへ結び、中点・partial estimateによるgateの誤通過を拒否する。
3. 正の区間、L=0、referenceなし、width等号、全点欠落/1点欠落、reference_sensitive、above、withinを既存bounded helperと照合する。
4. entire/possible/区間欠測の192分母を確認し、点取得済み・区間のみ欠測のprecision gateを被覆と区別する。
5. 両者withinの場合だけclock別に比を出し、CPUのみ欠測、wallのみ欠測、BAR平均0、非有限費用、mean of ratiosとの差を確認する。
6. failureの費用保持、inclusive summaryとpayload/markerの不一致拒否、capacity費用の分離、pool按分なしを確認する。
7. 192のpartition完全被覆、重複・欠落・範囲外・別identity/role・capacity混入・未選択行taskを検査する。
8. 第3段階の実 `completed` readerへ小artifact fixtureを渡し、F0かつrecorded failureは分母に残り、非zero/kill/欠落と外部pin・script・resource・run_count・host不一致は成功完了にならないことを確認する。
9. MC/BARの科学manifest・seed・prior・選択/reference/censusの差替えを拒否し、ineligibleへ変換しない。
10. payload/marker/summary/source/receiptの途中変更、同bytesへのpath retarget、snapshot後の状態変化で成功reportが公開されないことを確認する。
11. 未取得mixing診断と保守的placeholder、host情報unknown、有限reference共用、容量と本番の費用を日本語renderで区別する。
12. PBS guardが全payload I/O前に働くこと、fresh output、外部SHA必須、AST source closure、renderのraw再走査なしを確認する。

各test fileは60秒以内とし、数値fixtureと小artifactによる実reader受入、metadata境界mockの証拠範囲を分けて記録する。
本番rawの全走査、追加capacity、sampling、候補再選択、閾値調整、比のbootstrap区間、新しいqsub実行は軽量受入へ含めない。
本書の保存時点では上記受入と本番評価は未実施であり、親レビュー後に小受入から実装へ進む。
