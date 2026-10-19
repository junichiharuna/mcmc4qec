# 分割sampling条件の最終比較実行手順

対象は既定の残り9条件、case 0・1・3とtarget_index 0・1・2である。
本手順の実装・合成記録での受入は完了したが、2026-10-19 07:54時点で対象条件の本番assembly・final投入は未実施である。
科学的な設定と192 replicateの分母、凍結source・native環境は変更しない。
過去のC2用入口と実行記録は参照のみとし、再実行しない。

## 前提となる実記録

sampling collector、全BAR partition、BAR collector、trace capacity、full trace監査の完了受理を先に済ませる。
各入口と実行順は[data_tile_validation_2026-10-17/low_noise_pending_dispatch_ledger_v5_ja.md](data_tile_validation_2026-10-17/low_noise_pending_dispatch_ledger_v5_ja.md)を参照する。
未完了の記録や未取得のSHAをzeroなどの仮値で補わない。
次の共通引数を実記録から構成し、assemblyとfinal各phaseに同じ値を渡す。

| 引数 | 実記録の内容 |
| --- | --- |
| `--case` / `--target-index` | 同じ固定条件の座標 |
| `--collector-prepared-sha256` | sampling collectorのprepare response |
| `--capacity-directory` | 当該条件のanalysis capacity回収証拠ディレクトリ |
| `--capacity-binding-sha256` / `--capacity-profile-sha256` | 上記capacityのbindingとprofileのSHA |
| `--analysis-prepared-sha256` | 分割BAR解析のprepare response |
| `--bar-prepared-sha256` | BAR collectorのprepare response |
| `--trace-capacity-prepared-sha256` | trace capacityのprepare response |
| `--trace-full-prepared-sha256` | full trace監査のprepare response |

`output/`はgitignore対象であるため、再現時は保存archiveのmanifestを照合して必要sourceをリポジトリ直下の`output/`へ復元する。
回収入口まで含む保存先は`data_tile_validation_2026-10-17/partition_final_recovery_transport_v1/`で、外部証拠はmanifest指定の元ディレクトリへ復元する。
このarchiveは84 sourceを含み、manifestのSHA256は`024bb8fc40a775c59dde8d1532779047f7ee35162dd4a7a7002e9543a5419cbe`である。
archive内から直接CLIを実行しない。

## 実行順

以下の`$finalArgs`は上表の引数と実値から作るPowerShell配列であり、この文書では未取得値を埋めた実行可能例を作らない。
Pythonは`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe`を使用する。

```powershell
& $python output/assemble_low_partition_final_once.py @finalArgs
& $python output/invoke_low_partition_final_once.py prepare @finalArgs
& $python output/invoke_low_partition_final_once.py preflight @finalArgs
```

assemblyは両completionの実連鎖を再構成し、実PBSと現在のmetadataを照合してconfigを保存する。
prepareとpreflightは計算ジョブを投入しない。
preflight成功は空きノードの保証ではない。
待機中を含む既存要求node数を確認し、1node追加しても合計2以下となる時点で次を一度だけ実行する。

```powershell
& $python output/invoke_low_partition_final_once.py execute @finalArgs
```

既存final v3のsubmit処理が共有lockと最終node数を再確認し、qsubで投入する。
control SHAは実prepare responseから取得し、executeの脚本・manifest・resourceは実preflightと一致させる。
実jobがF・Exit_status 0・run_count 1となったことを確認してから、次を一度だけ実行する。

```powershell
& $python output/invoke_low_partition_final_once.py seal @finalArgs
```

sealは実executeのjob ID、現在のPBS、compute完了記録と保存reportを照合する。
seal受理後は、同じ実引数で次を一度だけ実行する。

```powershell
& $python output/recover_low_partition_final_once.py @finalArgs
```

回収入口はassemblyからsealまでの実記録を再構成し、remoteの14件の証拠と現在のPBSを照合する。
reportは別途scpで取得し、sealで固定されたSHAとbyte数を確認する。
保存先は`data_tile_validation_2026-10-17/low_partition_final_caseC_targetT_evidence_v1/`で、CとTは当該条件の番号である。
全検査成功後にだけ`collection.json`を作り、転送失敗時は途中ファイルと記録を保持する。
既存出力先へ再実行せず、失敗原因と保存証拠を確認する。
seal完了後も、report回収・数値レビュー・独立timingの候補選択と全入力検証は別工程として行う。
config生成やsealだけで低ノイズ研究全体の完了とは扱わない。

## 算術レビュー

review_low_final_arithmetic.pyとその受入テストは`data_tile_validation_2026-10-17/low_final_arithmetic_sources_v1/`に保存した。
manifest SHA256は`115c93c373f643b3b9f5827b16b33de95eb9426effc66c1cc2a10eb6e47fe73b`であり、照合して`output/`へ復元する。
回収済みreportの`audited_collection.evidence_sha256`が固定するproduction planと`partition-collection/rows.jsonl`を取得してから実行する。
この2ファイルの回収入口は`data_tile_validation_2026-10-17/low_review_input_sources_v1/`に保存した。
manifest SHA256は`052362bea3178969263b11a03da38b5e663bc2465985a0d47411599f505d9a20`であり、照合してsourceを`output/`へ復元する。
新規の回収先を指定して次を実行する。

```powershell
& $python output/recover_low_review_inputs.py --report $reportPath --report-sha256 $sealedReportSha --output $newInputDirectory
```

成功したcollection.jsonのfiles欄からremote pathを読み、localの`sampling.json`と`rows.jsonl`を次の算術レビューに渡す。
回収失敗時は途中ファイルとtransfer-receipt.jsonを確認し、同じ出力先への自動再実行はしない。
分割samplingでは同じsampling rootの`sampling_manifest.json`がproduction planであり、wrapperの`manifest.json`と混同しない。
report SHAはsealの実report SHAを指定し、remote pathはreportで実際に固定されたpathを指定する。
以下の変数は検証済み実値であり、未完了条件に仮のSHAを与えて実行しない。

```powershell
& $python output/review_low_final_arithmetic.py --report $reportPath --report-sha256 $sealedReportSha --plan $planPath --plan-remote-path $planRemotePath --rows $rowsPath --rows-remote-path $rowsRemotePath --output $newReviewDirectory
```

既存C2T2ではこの一般化した入口で実算術照合済みである。
plan・rowsの回収入口は実C2T2で確認済みだが、残り9条件の本番回収とレビューは未実施であり、回収処理で保存する14件のfinal証拠とは別に扱う。
算術レビューの成功を、独立referenceの真値保証・混合保証・名目95%被覆保証と解釈しない。

## 失敗時と解釈

全phaseはintent・生成script・stdout/stderr・receiptを保存し、既存記録を上書きしない。
通信失敗やqsub応答不明時に同じexecuteを再実行せず、実qstat・remote台帳・共有lock・local記録を照合して状況を確定する。
初回24時間は要求上限でありETAではない。
assemblyはrows・raw trace・WSS payloadを読まず、その検証はfinal computeが行う。
実行が完了しても混合の保証や名目95%被覆の保証にはならず、失敗・未定義・未取得を含む全192 replicateで結果を評価する。

## qsubの待機オプションについての確認

2026-10-19に実クラスタの`qsub --version`が`pbs_version = 20.0.0`を返すことを確認した。
PBSの`qsub -W block=true`は投入コマンドをjob終了まで待機させ、jobの終了コードを返す機能である。
仕様は[PBS公式User GuideのMaking qsub Wait Until Job Ends](https://2020.help.altair.com/2020.1/PBSProfessional/PBSUserGuide2020.1.1.pdf)に記載されている。
RIMCの`docs/superpowers/specs/2026-10-09-twelve-code-jobs-design.md`では、後続jobの開始を待たせる`qsub -W depend=afterany:JOBID`を使用しており、呼出し元を待機させるblockとは区別する。
今回の凍結済みsampling submitterはqsubを30秒、外側SSHを180秒で待ち、qsubが戻るまで共通投入lockを保持する。
そのままblockを追加するとtimeoutになり、lockも長時間保持して2本目の並行投入を妨げるため、追加していない。
submission ledgerとPBS Submit_argumentsも現在は固定scriptだけを許可しており、引数だけを差し替えると既存の完了検証と不一致になる。
block対応を行う場合は、投入受付・job ID保存・lock解放と長時間の完了待機を分離し、jobの非零終了を投入失敗と混同しない処理と、全記録検証の対応が必要である。
投入済みjobをblock付きqsubで再投入しない。
本調査では新規probe jobを投入しておらず、このクラスタでのblockの実動作は未検証である。
