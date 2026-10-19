# 低ノイズ独立計時の実全数 seed census 接続案

本書は第2段階 primitive と第3段階の正式 census descriptor の間に残る実行入口だけを対象にする。
点検と仕様提案のみで、実装、正式 manifest 作成、全数 seed 再生成、remote 操作、qsub は行わない。

## 不足している入口の確認

既存 `submit_tile_seed_audit.prepare` は `tile_seed_audit.catalog` と既存 BAR timing manifest の組だけを扱う。
同 `run` は旧 `tile_seed_audit.py --full --max-seconds 1800` を呼び、追加引数は stage140/141 用の `--bar-timing-manifest` に限られる。
新 `tile_low_noise_timing_seed_audit.extend_catalog` の四 manifest を供給する引数・factory 接続はない。
旧 `completion.json` は manifest/result/PBS id/wall を保存するが、新 `tile_low_noise_timing_execution.formal_census` が必須とする実 native profile、hostname、execution hash、入力/source の前後 hash を揃えない。
従って既存 CLI の実行手順だけでは新60 namespaceの正式全数監査を完了できない。
既存 `tile_seed_audit.census` の SQLite 衝突検査 engine はそのまま再利用でき、seed 関数・座標・衝突判定の変更は不要である。

## 最小実装単位の提案

新 module は `cluster_scripts/tile_low_noise_timing_census.py` 一つとし、`plan`、`run`、`submit`、`seal` の入口をまとめる。
既存 frozen module、旧 census driver/submitter、旧全数結果、stage2/selector の配置先は変更しない。
科学的な plan/registry/seed generator は第2段階 API、scheduler の照会・共有 lock・一回投入は既存 helper を使い、新たな科学 namespace や stage は追加しない。
新 module とその受入・source closure を独立レビューと Linux 配置で固定した後に、正式 selection と科学 bundle が揃った時だけ運用 plan を作る。
plan の後の source 変更は旧 plan を更新せず拒否する。

## 入力と旧56 namespaceの再構築

authority は job265253 の元 root `/home/user/workspace/mcmc4qec/20261018-tile-bar-seed-audit-v1/runs/seed-census-bar` の正式 manifest/result/submission/script/PBS 終端・外部受入証拠である。
元全数集合は56 catalog namespace・3,963,562 entries、予期しない衝突0、意図的共有8,448、stream hash 89c16e9c9ebb47298c402b2f04b5b1f60fc4b28578987011b01d5a13fd239bb9 である。
正式 result bytes の SHA256 b61653309ca8e87ea315ab8dd46f05c1e4ad8e2a4fa642a67da6d590dcaa4116 を外部 pin の一つとし、件数の自己申告だけで baseline を受理しない。
旧 manifest に保存された data と8本の BAR main/capacity manifest のパス・順序をそのまま使い、同じ `audit.catalog(data,bar_timing_manifests=...)` で56 factoryを再構築する。
旧 seed を保存済み unique 件数で代用せず、これら factory から全3,963,562 entriesを再生成する。

旧 census の producer は旧 bar-seed-audit root、新 stage2/selector の実 import は v11 などの分離 root なので、絶対 source path の差を隠して旧 evidence の digest を流用しない。
保存証拠の read-only 比較では、旧 catalog の12 producerについて新 stage2 closureの同名moduleが全て同じSHA256だった。
運用時には外部固定した旧path→現pathの一対一対応表を作り、双方の現 bytes、旧source hash、実import解決先を計画時・run前後に検査する。
basename 一致だけで対応を認めず、旧12件と現在12件の集合が過不足なく一致し、同一 byte hash であることを必須とする。
旧保存 evidence と現在再構築 evidence は `source_sha256` の絶対path mapping以外を canonical 完全一致させる。
この検査には input_sha256、全56 plan digest、全件数、generated_candidate_plans、master、Python/NumPy、reservation の空集合も含む。
一致しなければ旧集合を再現した扱いにせず停止し、path正規化で値を補正しない。
旧 evidence は不変保存し、現在 evidence を別 digest で固定して、対応表と旧結果を結合した input manifest から `extend_catalog` に渡す。
この方法は巨大な entry stream の IPC や二重 module import を増やさず、実際に import する source と過去の producer bytes の同一性を明示する。

新入力は外部 pin 済みの正式 selector bytes、scientific bundle、registry digest、四 role manifest の canonical digest を揃える。
四 manifest が scientific bundle に内包される場合も各 digest を個別に記録し、別ファイルも渡された場合は内包値との完全一致を要求する。
`read_selection` と `validate_plans(bundle,expected_registry_digest=...)` を使い、24行と full candidate 集合、192評価分母、正下端MC予算、capacity2rep、stage160–163を再検査する。
selector の巨大 raw payload 全集合をこの seed 計画で再走査せず、正式 selector bytes と完了済み受入の外部 pin を境界にし、その範囲を記録する。
旧 result の checked_counts を外部 byte pin 後に読み、canonical object digest とともに `extend_catalog` へ渡す。
新旧あわせた catalog は60 namespaceで、planned_total=`3,963,562+194*sum_i(3+2*R_i*C_i)` と独立式で照合する。
selected=0 の四 role も零件として保持し、60 namespaceの定義を変更しない。
selected=0 かつ新allocation=0なら `not_required_no_allocations` を保存するno-op経路とし、pilot・全数census・新timing job・qsubを行わない。
旧56 namespaceの完了証拠と24行を保持し、60 namespaceの監査完了や新計時成功を主張しない。
selectedがあるが退化条件などでallocationが0となる場合はこのno-opへ自動変換せず、計画上の理由を確認して停止する。
第3段階はこのno-opを正式成功censusの代わりに受理せず、taskがないため実行せず、第4段階はineligible/unmetと費用未計測・速度比nullを保持する。

## 計画、pilot、資源

plan は immutable な新 runroot、catalog.json、manifest.json、入力元の外部 pin 集合を作り、既存 intent/output/symlink先の置換を拒否する。
manifest の必須項目は catalog_evidence_digest、runtime、input_sha256、source_sha256、native_input_digests、資源、Python binary/package binding とする。
input_sha256 は元baseline manifest/resultと全旧入力、source対応表、selector/scientific bundle、registryと四planの保存入力、固定profile/fixtureを含む。
source_sha256 は旧12 producer、新52module closure、新runnerとscheduler/import helperの実解決先を含み、元byteと現在byteを別pathで記録する。
plan/runのどちらでも、検証対象sourceをimportする前のstdlib-only byte pin gateを設ける。

新旧60 factoryの round-robin streamを最大1000 allocationだけpilotし、全予定件数を分母として時間・peak RSS・SQLite bytesを保存する。
pilotの部分集合はfull完走として扱わず、正式結果を先取りしない。
旧正式全数は1,504.881秒だった一方、旧pilot外挿は428秒だったため、新pilotの2倍外挿だけを完了予測にしない。
提案資源は1node・1CPU・2–4GiB、wallは `max(2*pilot_seconds*N/n_pilot,1.5*1504.881*N/3963562)+300` 秒を300秒単位に切り上げ、上限2時間とする。
これは実測旧規模と新pilotを併記した保守的な要求根拠であり、I/O条件や完了時間の保証ではない。
メモリ・空きdiskは旧 helper の実測式を再利用し、上限を超えると列挙数を減らさず停止する。
旧CLIの1800秒制限は使わず、既存 `census` 関数を新runのhard wall budget内で呼ぶ。
本番監査の上限が既存30分から延びる理由と、新上限は事前planへ明記する。
実資源式と係数は本仕様承認後に受入で固定し、結果を見てその場で伸ばさない。

## 一つの全数 census と完了証拠

run はPBS id・single-thread環境・実submission ledger/intent/script/resource・hostnameを照合し、実行意図をexclusive保存する。
run開始時に固定 native fixture を実測し、production profileとstrict比較した実profileを native.json の profile に保存し、manifest/PBS id/hostnameを付ける。
実行前に全plan/source/inputを照合し、元56 factoryと新4 factoryを `extend_catalog` で接続して `old.round_robin` から一つの `old.census` へ供給する。
新旧を別々のDBで検査して、旧seedとの衝突確認を省略しない。
正式 result.json は `census` が返した full dict自体を保存し、旧CLIの `{'full':...}` envelopeをそのまま第3段階へ渡さない。
完走、planned/checked/unchecked、role別件数、unique件数、意図共有8,448、予期しない衝突0、stream hashを `complete_census_gate` と独立式で照合する。
既知の calibration.bootstrap/synthetic.bootstrap 共有以外は許可を追加しない。
入力/sourceを再hashし、前後の絶対path→hash集合が等しい場合だけ completion.json の complete=true を保存する。
completion は manifest/PBS id/hostname、result_sha256、native_sha256、execution_sha256、input_sha256/source_sha256 と各 `_after`、wall/CPU/RSS、SQLite最大bytesを含む。
失敗・timeout・未完走・source変化では失敗結果と消費時間を保存し、成功completionを作らず自動再投入しない。

SQLiteは既存engine同様の一時重複検査DBであり、科学rawや再現に必須の保存対象とはしない。
通常の成功・例外では専用temporary directoryを閉じて削除し、予定入力・source・全件数・衝突例・stream hash・環境・実ログを残す。
PBS強制終了などで一時DBが残った場合はrunroot内の残留として明示し、実行中コピーや別rootを巻き込む掃除をせず、手動確認後のcleanup対象にする。
正式結果の再現は固定manifest/sourceから行う契約であり、削除済みSQLiteを保存済みと報告しない。

## 投入、終端seal、第3段階への接続

submit は共通 `tile-low-noise-submission.lock`、controller不在、queuedを含む最大2ノード、直前の再照会、fresh input/output、qsub一回という既存運用を維持する。
submission-intentを先に保存し、timeoutや不明応答はintent/lockを保持して自動再投入しない。
軽量sealはqstatによるF/exit0/run_count=1、実script/resource/hostnameを照合し、保存completion・native・全input/sourceの現在hashを検査する。
必要PBS fieldsだけをterminal.jsonへ保存し、失敗jobを成功descriptorへ変換しない。
sealが作るdescriptorは現 `formal_census` の12要素 `manifest,catalog,result,completion,submission,intent,execution,native,profile,fixture,script,terminal` に合わせ、それぞれ元fileの絶対pathとbyte SHA256を持つ。
native_input_digests のキーは profile/fixture、runtime は t.runtime() 完全一致、resource は cpus/workers/memory_gb/wall_seconds/walltime/requested_nodes/max_nodes を含め、workers=1 とする。
新completionのschemaはそのreaderが要求するfieldに合わせ、旧265253completionだけを補完して新jobの証拠に見せない。
sealの最終受入で実 `formal_census(descriptor,scientific_bundle,proof)` を呼び、全要素を消費して入力の前後固定を確認する。
このdescriptorが正式に揃うまでは第3段階capacity/mainを投入しない。
全数seed非衝突は乱数streamの数学的独立性や実samplingの正しさの証明ではない。

## 小さい受入案

1. 旧CLIは新4manifestを扱わないこと、旧completionはformal_census契約を満たさないことをfixtureで確認する。
2. 旧/現producer対応の同一bytesと別pathを区別し、未知path、hash違い、抜け、重複、source以外のcatalog差を拒否する。
3. 56旧factoryと新4factoryが一つのstream/DBへ渡り、旧新間の強制衝突を検出し、意図共有の許可が増えないことを小streamで確認する。
4. full予定件数、零件role、partial/timeout/未列挙/registry違いを検査し、旧全数成功だけで新gateが開かないことを確認する。
5. native/PBS/hostname/source/input前後変更とresult hash違いを拒否し、成功と失敗のSQLite削除、強制中断時の残留表示を小fixtureで確認する。
6. mocked schedulerで最大2ノード、controller、共通lock、intent後一回投入、不明応答保持、F/run_count/script/resource違いを確認する。
7. 実保存された小catalog/result/completion fixtureを12descriptorで実 `formal_census` に接続し、1要素改変と旧envelope形の結果を拒否する。

受入は1file60秒以内とし、旧3,963,562entriesや新全数の実走査は含めない。
この仕様段階では実装・配置・qsub・pilotも未実施である。

## 実装時の固定 API と受入範囲

単一 module `tile_low_noise_timing_census.py` の公開入口は `prepare(root,config_path,expected_sha256)`、`read_plan(root)`、`submit(root,execute=False)`、`run(root)`、`seal(root)` とする。
CLI は `plan --root --config --config-sha256`、`submit --root [--execute]`、`run --root`、`seal --root` とし、内部 `_work` は実PBS id/ledger/script契約を満たす子process専用とする。
run は保存したwall上限から180秒を残して子processを打ち切り、失敗記録と残留SQLite一覧を保存して自動retryしない。
config は schema=1、purpose=low_noise_timing_census_input とし、selection/scientific_bundle/baseline_manifest/baseline_result/baseline_verification/profile/fixture は `{path,sha256}` の元byte descriptorで渡す。
加えて registry_digest、source_relocation、実sourceの絶対path→SHA256であるsource_sha256、core全Pythonファイルのcore_sha256、python_path/python_sha256/pythonpath、新runner配置のbundleを固定する。
baselineの三descriptorは本文の旧正式manifest/resultと独立検証の既知SHAに一致させ、source対応表は旧catalog全producerを一対一で網羅する。
config自体も元byteの外部SHAを要求し、stdlib-only preimport gateの後でcluster moduleを読み込む。
read_plan は科学bundle/selection/registry、原始証拠、source/core/実Python/import pathを再検査するが、旧全entryの再生成は実runのbuild_catalogで行う。
no-op manifest は status、selected_rows=0、new_allocations=0、scientific_bundle_digest、registry_digest、selection_sha256、baseline_result_sha256、baseline_verified_namespaces=56、new_namespaces_audited=false、formal_census_descriptor=nullを持つ。
read_planで受理したno-opのrun/submit/sealはその状態だけを返し、正式成功census descriptorを生成しない。

小さい統合受入では旧engineに実3 allocationを投入し、fixture上の既知共有を1件として、保存result/completion/native identity/SQLite cleanupから実formal_census readerまで接続する。
この統合の旧catalog再構築、科学bundle全検証、native実probeとPBS応答は境界stubであり、本番3,963,562entryの再生成やnative実測を実施した扱いにしない。
runtimeとresourceの値の検査、source対応表の両path再hash、元byte pinのimport前拒否、qsub二重実行拒否・直前controller/2node制約、入力変化と公開直前result変化の拒否は別の小受入で確認する。
submission-intentはflush/fsyncしてから固定入力・script・controller・最大2ノード・lock所有を再照合し、その後だけqsubを一回呼ぶ。
共通lockはroot/pid/nonceの取得時bytesとfile identityを投入前後に照合し、所有を失ったlockを削除しない。
応答後の所有喪失は成功receiptにせずqsub応答・intentを保存し、投入結果の確認を要する状態として保持する。
