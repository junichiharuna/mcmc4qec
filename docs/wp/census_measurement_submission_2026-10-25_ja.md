# census資源計測のPBS投入

元prepare-role 265675はF1・run_count=1で、外側PBSの要求は1 CPU・96 GiB・4時間だった。
実qstatの使用量はwalltime 13分32秒・CPU time 13分24秒・mem 15,084,044 KiB・vmem 15,901,144 KiBだった。
停止理由の「2時間・4 GiB」は元census.resources()の内側の承認閾値であり、外側PBSの割当とは別である。
既存failed root・source・config・bundle・selection・worker・merge・比較結果を変更しない。

計測helperは元inspect_inputs→build_catalog→1,000件pilotを別のfresh processで実行し、測定値を保存してから元式の候補と元resources()の承認/拒否を別に記録する。
本census、科学manifest生成、科学計算の再実行、資源上限の承認は行わない。
入力再利用の実検証はPBS内の元inspect_inputsで行い、失敗rootを再利用可能と認定しない。
実計測の4時間は割当予算であり、予想終了時刻ではない。

## 受入と投入

qsub 265677で21 fixtureが0.067秒で成功し、実qstatはF/0・run_count=1だった。
fixture要求は1 CPU・4 GiB・10分で、fixture subprocessには180秒のtimeoutを設定した。
sourceの前後SHA、正確な件数、元gateの上限内・時間のみ超過・メモリのみ超過・両方超過、測定保存順、原入力変更、実PBS script/host/vnodeの拒否経路を確認した。
このfixtureでは実科学入力による測定は行っていない。

fixtureのF0/run1と原本sourceを確認後、別stageへ実計測qsub 265678を投入した。
要求は元外側PBSと同じ1 CPU・96 GiB・4時間で、既存shared physical gateのfresh censusとlockを通して投入した。
最大2物理ノード×96 CPUとnodeごとのメモリ管理上限を保持し、qsub再試行や独自のgate回避は加えていない。
元runtimeのPython実行path/SHA/PYTHONPATHをrequestへ固定し、scriptでは同じPYTHONPATHと単一thread設定を使う。
新results directoryはhelper自身が未存在であることを確認して作成する。
265678はF/0・run_count=1、walltime5分56秒・CPU5分55秒で完了した。
計測receiptのelapsed_secondsは355.3464013906196秒であり、PBSの秒単位のwalltimeとは記録の定義が異なる。

## 実計測結果

| 記録 | 実測値 |
|---|---:|
| 全予定件数 | 4,208,002 |
| pilotで検査した件数 | 1,000 |
| 未検査件数 | 4,207,002 |
| unexpected collisions | 0 |
| 意図的な共有entry | 17 |
| pilot.seconds | 0.054935259744524956秒 |
| pilot wall_seconds | 0.056612600572407246秒 |
| process lifetime peak RSS | 9,588.05859375 MiB |
| pilot SQLite bytes | 110,592 |
| 元式のmemory_gb候補 | 16 |
| 元式のwall_seconds候補 | 2,700（45分） |
| 元式のdisk_required_bytes候補 | 4,294,967,296 |

元式のpilot外挿は462.335365750961秒、既存baseline外挿は2396.5350828211185秒で、後者がpredicted_secondsとして採用された。
旧wall_seconds上限7200秒は超えず、memory_gb上限4だけを超えたため、元resources()は従来どおり拒否した。
候補生成に使う別namespaceの関数ではその上限require一行だけを除いたが、元関数は不変で別に呼び、拒否理由を保存した。
16 GiB・45分は元census-stream外挿の候補であり、本番投入の承認でもジョブ全体の予想終了時刻でもない。

phaseのelapsed_secondsは入力検証198.97510783653706秒、catalog構築147.90589841920882秒、pilot phase0.05686745047569275秒、最後の入力再検証8.366575142368674秒だった。
これらmetadata検証・catalog構築などの費用は、元式のcensus-stream外挿には含まれない。
RSSはこのfresh standalone processの累積peakで、phase間の差分を各phase固有のpeakと解釈しない。
旧bridgeの最大使用量をそのまま再現した実験でもない。
SQLiteは元census_streamと同じ一時領域で処理され、計測後には保持されない。
collision 0はpilot1000件に対する結果で、全件の一意性・統計的独立性・実行済sampling metadataの保証ではない。
全件census・科学manifest作成は未実施で、production_authorized=falseを維持した。
独立レビュー担当も主receipt4件とphase4件のremote原本hash・accepted内pin結合を照合し、予定件数・16 GiB/45分候補・memoryのみの拒否・全件未実施の区別に不整合を認めなかった。
45分をそのまま全PBS予算やETAと扱わない点も独立確認した。

## 小原本の取得先

共通rootは `$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/` である。
fixtureは `pipeline-submissions/census-resource-measurement-fixtures-v1/`、実計測は `pipeline-submissions/census-resource-measurement-actual-v1/` に保存する。
元入力authorityは `output/census_partial_reuse_review_v1/measurement-inputs.json` で、SHA-256は `1c900b0e89cb1434feda5f833ff3bed26999595903623c8c0cd0bc6afd05ce0a` である。
実requestはこのauthorityのconfig/census source/failure evidence/runtimeを変更せず、実行stage・helper・submission・resourceだけを追加する。
以下のSHA-256は識別子を含むprivate原本bytesを指し、この文書のhashではない。

| 原本 | SHA-256 |
|---|---|
| helper measure.py | `a12b7d1a50e12e25e523f2f770deb8d50d49be35c42b32c38d2f09ed616b9b0c` |
| test_measure.py | `17367e7cf4686c934459770471ac83850aa33c60af2d6d5db679b4901a358bd4` |
| fixture accepted.json | `d787a4ce9eb65da4ca1777dae6ab81d054ee7027c6af041c12e3d4ac71305166` |
| fixture terminal.json | `89bc52125469c86e3156ea274cf9d5001d6ff22fc782bb1226c3fb4012d9089f` |
| actual request.json | `86a2500a216f0a3bf65671b0a04f99addbabab3a6d9f5dda1480625fa2adac82` |
| actual submission.json | `a128cda0457cabd18de41a4a4360e2f42fe06b757666d94432a0a16901b60a0f` |
| actual fixture-authority.json | `761142f3f5907657ea5ac495b128942b65404ee37ab3a5d43c0a85d63edc1812` |
| actual job.sh | `8048f077c32d080bfdc1a2f1d9abbcd40eecb2e498a08b819e57377ef3a4abd4` |
| actual terminal.json | `ffe18d4cf9243cdee7d64c1d7d9219f453fe5320568d846c1bd5698733697b99` |
| results/accepted.json | `8a34035f7edb05d86e80face6d62edbbd5063a1baad059fb70176a041335b29a` |
| results/pilot-measurement.json | `6067e097cfe5e15cc3fb4b56b1a83bd8381148cfffaf9c4721f8a7991debf3c4` |
| results/resource-proposal.json | `eb2316d076bec1458ddc1596349b9cdf1556c50f75d02180b6a89c4d37bb54d5` |
| results/legacy-decision.json | `a587daba51a731cc087d852a202a4fa698c39da937887f62092437c4ba91026f` |

staging sourceは同rootの `output/census_measurement_submission_v1/`、実helperはfixture stageの `sources/measure.py` に固定した。
stage.pyのSHAは `47d10d78effeee14e891380fc9ab6d2287510d5eac11feb672d498eab41c3c2e`、fixture_worker.pyは `ea09c5ed20bec5fe23c6b4afa6b11113a5671f57bf3bec5a1f702b2b4b0c86b8` である。
元census source SHA `7e45d49b1955444e257852ea82a76933941f0e5620890701fbaa903770821692`、元census-config SHA `7fafc8ebb8cdd340485bfd0ba0d72b5c464393663f86591f6903bf4c4dfe724e` は維持した。
deploymentでは小metadata/sourceだけを扱い、巨大bundle・selection・rawのローカル/login読込やhashは行っていない。
小測定原本とterminalだけを回収し、この計測作業から本censusを投入していない。
