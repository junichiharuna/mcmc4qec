# flow v9 / finite outer の追加保存準備

これは採取前の範囲整理であり、flow v9の本番起動・snapshot作成・共有候補作成の完了記録ではない。
既存v8 private snapshotと共有候補は、その時点の歴史資料として変更しない。
最終bindingと切替証拠が確定した後、新しいrequest・stageで受入済み `tools/reproducibility/snapshot_v2.py` をPBS内から使用する。
snapshot library SHAは `053265218e64768d48e13871b47d9c6bb33bb659557122344b4c6b3300cdf35a` で、既存25 fixtureの受入はこのlibraryに対するものである。
新しい実request builderや実採取の成功を、その受入から推定しない。

## 既存の入口

`tools/reproducibility/collect_tile_v8_snapshot.py` の有限なsource/metadata収集と `snapshot_v2.snapshot(request, fresh_directory)` を再利用する。
v8 collector自体は固定v8の設定・source SHAを検査するため、v9のconfigをそのまま渡したり、原本定数を書き換えて上書きしたりしない。
別の薄いrequest builderで、旧v8 requestをhistorical baseline、新しい明示的入口をcurrent controlとして分類する。
旧requestのsources・metadata・bindings・envelope・externalを保持し、新しい宣言をpath単位で加え、同一pathの異なるSHAは拒否する。
旧sourceを新sourceに差し替える必要が生じた場合は、変更前bytesの別の実在保存先を証拠で固定するまで採取を進めない。

private v8 receiptは `$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/pipeline-submissions/reproduction-v8-finite-snapshot-v2/snapshot/receipt.json` で、SHAは `2e5068ac8385a74f6a281a48f9ec0e288777bf4ba4a2734323d2ea4c81b552ed` である。
これはprivate原本bytesのhashであり、識別子を除去した文書のhashではない。
旧共有候補のarchive・builder sidecar・補助source ZIPは変更せず、新flow保存の代わりとして扱わない。

## 最終bindingから保存する入口

| 区分 | 明示的に固定するもの | まだ確定していない点 |
|---|---|---|
| 新flow | 実flow source、launcher、config、native request/accepted/terminal、実launch intent/process/started | actual configと切替後のlaunch証拠 |
| 有限outer | 実7 source、assemble.py、assembly request/sources/deployment/qsub script・ledger・terminal、prepared receipt/config | 最終assemblyとactual native constructorの受入 |
| 有効tail | effective config/prepared receipt、loader、元base config、report IPC source・変換helper・report環境とnative受入 | outer configとの最終pin一致 |
| 共通PBS wrapper | 元job.py、derive_job.py、新実job.py、dynamic gate、capacity/dispatcher、fixture/native受入と実source | 最終outer source_pinsに同一pinが含まれること |
| 各family | census/independent/report plugin、dispatch、binding、census/report collection、元6 roleの実sourceと対応環境 | 実staging先と最終source closure |
| 後処理 | post_source、merge acceptanceのPBS分離helper、parallel merge関連の実source/contract/environment | flow helpersとの最終pin一致 |
| 切替 | 旧v8を停止した事実、新flowのimmutable launch、保持したworker/prepared/job対応 | 停止と新起動の実証跡 |
| 動的配置 | outerのknown-child authority形式、実際に作成済みのpolicy/census/intent/response/ledger | 採取時点で未生成なら欠落として記録 |

実outer configの `source_pins` はPython sourceだけでなくJSON authorityも含むため、拡張子・役割でsourceとmetadataへ分ける。
`adapter_sha256` の実7ファイル、`plugins`、`collections`、`job_module`、`dynamic_gate`、`dispatch`、`binding`、`post_source` を直接宣言と照合する。
`source_pins` の閉包に含まれないtransform/deploy/native probe/fixture sourceも、明示的な受入requestまたはassembly receiptに結び付けて追加する。
この一覧は実行された全sourceという主張ではなく、current source・validation source・historical sourceの役割を保持する。
source aliasは元のdeclared pathとcanonical targetを別々に記録し、同一bytesでも別pathを勝手に統合しない。

flow担当から受領した予定sourceは `output/low_parallel_flow_v8/flow.py` SHA `58ada8dedaf393d01f501a9615ee7e920146c6596989b20c1b0f67b47a21e138` とlauncher SHA `2f79f7ec4b7b082f19ea155de3503f5852960df88ab9dbf379db8abae841700b` である。
directory名のv8と新actual journalのv9を区別し、名前から実行versionを推定しない。
担当者によるfixture 265626の84件F0報告は、actual config・native受入・実launch証拠の代わりにはしない。
追加sourceの候補位置は `output/reproduction_snapshot_v9_preparation/inventory-plan.json` に列挙したが、folder名を辿る無制限収集ではなく、最終config・request・receipt内の実pinを入口に選択する。
新flowの `helpers.terminal_acceptance` は `output/merge_terminal_acceptance_pbs_v2/acceptance.py` を指す予定で、旧v8 snapshotには存在しない追加の直接依存として保存対象にする。
最終outer候補は `$HOME/workspace/mcmc4qec/20261025-finite-tail-outer-v9/`、有効tail候補は同workspaceの `20261025-low-parallel-tail-config-v9/`、report環境候補は `20261025-finite-tail-report-environment-v1/` である。
実runtime候補の `output/finite_tail_runtime_v1/` と開発用pluginフォルダーを区別し、実行先のbytesと変換・配置元の由来を両方保存する。

## 読み込み境界と実行条件

ローカルでは小sourceと明示した小JSONだけを扱い、snapshot生成・圧縮・内容hash・実verifyはqsub内で行う。
raw/nativeの内容を開かず、既存宣言hashを外部referenceとして保存する。
巨大なmerge-result、values、accepted scientific rows、raw index全体、増加中のjournal/ログをJSONという理由だけで読み込まない。
外部referenceにはbytes_collected=false・original_hash_verified=falseを保持し、必要なら宣言済みstat/sealのみ記録する。
state-latestや可変ログの代わりに、採取時点の小さいPBS observationを新規保存し、時点観測とterminal成功証拠を区別する。
各source/metadataは4 MiB、総textは既存32 MiBの上限から始め、超過時に黙って対象を落としたり上限を拡大したりしない。
既存v8の件数を期待する値として新snapshotに流用せず、固定した実requestから新しいexpected countを作る。

採取helperの資源案は1 CPU・2 GiB・10分で、投入時の実物理配置に応じて受入済みdynamic gateまたは既存fixed gateを使う。
最大2物理ノードを超えないことをfresh censusで確認し、全ノード級childが2件稼働中なら待機する。
policy directory、collector jobstage、snapshot directoryは別の新規directoryとする。
collector/deployer/source pin・request・元authority・qsub証拠を保存し、snapshot後に生成したaccepted/terminalは別sidecar metadataとして固定する。
execution_ready・full_dependency_closure_complete・final_proofs_complete・scientific_reproduction_verified・publicly_distributableはfalseを維持する。
公開upload・commitは行わず、新snapshotから共有候補を作る場合も別stage・別policy・別identifier reviewを必要とする。

実採取に進む残作業は、最終flow/outer bindingの受領、実configとsource閉包の照合、切替後launch証拠の固定、有限request builderとその受入、shared gateによるqsub採取である。

## 切替後に確定した採取仕様

最終flow configはSHA `5b44a838edcf35f9d02d119c323530ef17bab880aeb8c29e74ff3fe81c4748ed`、outer configは `f4dc8a4b9ff57cbe2c1f6e8867fd2d31b4b1b6c09be57a812c353681a7cbf114` として担当者から受領した。
新launch startedは `ff09c182ad53930668b8cd2a1d2a157b3ec459795702ced6b3ee9cc8386189ef`、processは `2f670a0d080b822ad7c7c81210e29af0b0fbf9a36a0b9aa4cfdfcab2144ebb5c`、旧stop証拠は `fa52d841b85f4c97e6e80fe51943ffb4d1ae71885aabcd11dc741227ee06b26a` に固定して採取時に照合する。
これらはprivate原本hashであり、本文から実識別子を除去している。
新builderは `output/reproduction_snapshot_v9_preparation/` にあり、baselineをcopyして明示したsource/metadataだけを追加する。
source衝突、metadata hash、可変state拒否、未指定JSON参照の未読、source alias、4 MiB上限、external内容open禁止の7fixtureをPBS内で先に実行し、成功後だけ実採取へ進む。
fixture受入と実採取成功のreceiptは分け、同じジョブで後半が失敗しても前半の成功を実snapshot成功とは呼ばない。
native flow・outer assembly・outer constructorの既存jobについては採取時のqstatを保存し、F0/run_count=1を照合する。
十二workerの観測は時点情報のみで、scientific resultのaccepted判定やhashをこのcollectorでは行わない。
