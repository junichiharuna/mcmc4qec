# 低ノイズ計時reader拡張：段階的な実装と検証

[reader接続仕様](low_noise_timing_reader_extension_spec_2026-10-20_ja.md)の最初の工程として、保存WSS参照の検査を別moduleへ分離した。
作業先は `output/low_timing_reader_extension_v1/cluster_scripts/` であり、公開候補、repository本体のselector、実行中driver、既存Linux配置は変更していない。
新しい回復readerとportable readerの接続自体はまだ実装していない。

元selectorの全16条件監査、対象conditionのartifact、native profile・prior、source対応、現存reference入力、最終report内の参照との照合を `tile_low_noise_timing_reference.read_reference` にまとめた。
helperを直接呼ぶ場合も、参照metadataとartifactの外部pinの存在・hash一致を検査する。
helperの返り値は参照側の情報だけであり、sampling・trace・最終reportの実行証拠を受理したことにはしない。
selector側の従来3経路はこの共通検査を呼び、既存の全row再集約・全PBS ledger照合を維持する。

テスト追加時の `ModuleNotFoundError` を保存してから実装した。
追加受入は15 passed・5.60秒、分離したselectorを実importした既存の選択・source対応試験は65 passed・16.02秒だった。
追加受入では全16条件監査の保持、prior・native・job・件数・marker・保存参照・外部pin・artifactの不一致、読取後の変更の拒否を検査した。
既存single・partitioned・stagedのmetadata fixtureは旧selectorと同じ選択結果・終端bindingになった。
raw readerとnative環境は既存試験の明示的なmockを用いる部分があり、実768群の監査や正式選択を実行したとは扱わない。
既存試験では有限reference区間、全192分母、欠測・未定義の保持、候補順位と24行の出力も確認した。

回帰試験前後で元selectorと新しい2 sourceのhash一致を確認した。
元selector SHA-256は `1e3aeea104a62443fd6c9545b1ef4441d5845ac0fb21230fe79447629343a4a8`、分離版は `43c51e017538d7de5946922403e20a270938d2cb49142152542bbde130559ddb`、参照helperは `e6096cb42791253c405d1539f2a39bb600cd812a3803b156cef8689c080ee7a8` である。
全import closureは保存時点の再現情報として記録し、全closureを試験前後に固定した証拠とは区別した。

source・派生手順・試験・初回失敗ログ・成功ログ・元sourceと既存fixtureの14ファイルを [保存manifest](data_tile_validation_2026-10-17/low_timing_reader_extension_reference_v1/manifest.json) にまとめた。
manifest SHA-256は `c7e185db68757e13c61239970dcaa82ed6031e11b6171521ba4935653f45ec25` である。
実行環境は同manifestのPython・package版と実行ファイルhashを参照する。
再現する場合は同じrepository配置で保存sourceを作業directoryへ復元し、次のコマンドを使う。
既存証拠を保持するため、回帰runnerは出力JSONが既に存在する場合は拒否し、新しい作業directoryで実行する。

```powershell
& 'A:/dev/mcmc4qec/.venv-experimental-optional/Scripts/python.exe' -m pytest output/low_timing_reader_extension_v1/test_reference_extension.py -q
& 'A:/dev/mcmc4qec/.venv-experimental-optional/Scripts/python.exe' -B output/low_timing_reader_extension_v1/run_selector_regression_v1.py
```

残作業は回復済み・portableのreader接続、経路ごとの実終端と資源根拠、selector親入口のsource/argv/import対応、後続計画・census・実行・stage4との接続、Linux受入と配置である。
今回の80件成功をその残作業の完了証拠にはしない。

## 共通report照合の追加

同じ隔離directoryに `tile_low_noise_timing_joined_report.reconcile_report` を追加した。
経路を明示してreaderの全rowと保存reportを比較し、既存 `compare_rows` を使って各科学フィールドを再集約・照合する。
現存sourceとreaderのinput hash・解決先を親Evidenceへ取り込み、再集約中と親処理終了時の変更を検出する。
回復履歴とportable cohortを相互に読み替えず、元reportの非保証flagも維持する。
この内部部品はPBS終端を確認しないため、返り値に `pbs_terminal_verified=false` と範囲を明記する。

追加受入は初回module未実装の失敗を保存してから行い、最終25 passed・4.00秒だった。
各192 seed・16設定・3,072行の縮小fixtureで実数値の再集約を行い、未定義診断・区間未取得・欠測点・portable infrastructure failureを保持した。
行欠落・重複・点推定変更・参照改変・source不足・読取後変更・途中で失敗するiterator・経路の混同を拒否した。
reader・native・PBSの本番検査はfixtureでは実行しておらず、実768群の妥当性を確認したとは扱わない。
本番readerの証拠フィールドをsourceで確認したが、その確認を実データ接続の代替にはしない。

6ファイルの [保存manifest](data_tile_validation_2026-10-17/low_timing_reader_extension_joined_v1/manifest.json) のSHA-256は `d9f64be60d45945382823ae7d4c7a35f3defdaa2e2b16f666bfe9d6fb5150347` である。
再現コマンドは `A:/dev/mcmc4qec/.venv-experimental-optional/Scripts/python.exe -m pytest output/low_timing_reader_extension_v1/test_joined_report.py -q` であり、環境は先行manifestと同じである。
source SHA-256は `60e796aa25c8bab34b312837a300970b652321f54654c0eb11b9abf928262fb0` である。
次に各経路の正式reader呼出し・PBS終端検証・親入口を接続する必要があり、この部品だけで正式設定選択を開始しない。

## 条件ごとの子プロセス分離

回復v1/v2のinventory sourceが異なることを確認したため、同名moduleのimport cacheを共有せず、固定Python・PYTHONPATHで条件ごとに子プロセスを使う実行部品を追加した。
`tile_low_noise_timing_process.start_reader` は親のPBS割当て内で実handleを返し、`finish_reader` はそのhandleが実際に終端した後にだけ終了code・出力・入力pinを確認する。
未終端、開始例外、非0終了、出力なし、入力変更では成功扱いせず、intent・PID・stdout/stderr・部分結果を保持する。
同じdirectoryへの再起動と完了receiptの上書きを拒否し、新たなqsubは行わない。
正常終了のreceiptも `scientific_validation_accepted=false` とし、科学readerの返り値を別途検証する必要を明示する。

初回のmodule未実装エラーを保存した後、Windowsは最終15 passed・1.28秒、クラスタLinuxは15 passed・2.93秒だった。
Linuxでのpytestプロセス起動を含む全所要時間は8.23秒であり、科学計算の性能計測ではない。
実際の短い子プロセスで同名moduleの2版が分離され、thread設定と親PBS IDが引き継がれることを確認した。
テスト中のPBS IDはfixtureであり、正式selector jobを投入したわけではない。
Linux検査は `/home/user/workspace/mcmc4qec/20261020-low-timing-reader-process-v1` に別配置し、sourceの検査前後のhash一致を確認した。
本番データ、既存driver、既存Linux sourceは変更していない。

12ファイルの [保存manifest](data_tile_validation_2026-10-17/low_timing_reader_process_v1/manifest.json) のSHA-256は `5f099dbaec4a4d13cf29ac287ffd473475670ec575af103cf4d0c97f2f01674d` である。
再現用のsource・test・別配置script・Linux実行script・ログ・Python hashを同manifestに保存した。
ローカルの再現コマンドは `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest output/low_timing_reader_extension_v1/test_reader_process.py -q` である。
別配置scriptは使用済みdirectoryとintentを保持する一度限りの入口であり、そのまま再実行しない。
科学readerの本体、実PBS証拠の完全な結合、selector親入口と後段の接続は引き続き未完了である。

## 回復済み全cohortの入口

`tile_low_noise_timing_recovered.load_complete` を追加し、既存report snapshot、元の `verify_prepared`、回復済みtrace reader、共通WSS検査、実数値再集約を順に接続した。
この入口は既存report controllerが扱う単一の回復partition・全768群に限定し、元の異常終了を保持してsampling・collector・trace監査・reference・reference監査・元解析・回復・最終reportの実PBS役割を結ぶ。
保存された失敗終端を成功へ読み替えず、読取中のPBS終端変更も拒否する。
実装は元のhelper版とimport位置を使用する前提であり、CLI側のsource/native bootstrapと親selectorへの接続はまだ行っていない。

追加受入は14 passed・4.93秒だった。
数値再集約と既存PBS ledger checkerは実コードを用い、縮小fixtureの8 jobが欠けず、元解析の非0終了が保持されることを確認した。
重いraw/native reader、report snapshot、WSS監査はこの接続試験では明示的なmockであり、本番終端受理や全768群の監査を完了したという意味ではない。
case・root・pin・final job・point estimate・native scopeの不一致、実行中のsampling、欠けたcollector、回復jobの失敗、読取中の終端変更を拒否した。

C0T1の実環境では `analysis_manifest.json` とfull trace監査の `manifest.json` を読み取り、`completed_phase_evidence` の完全一致を確認した。
実metadataはanchor 265317、sample 265319/265327、collector 265332を列挙し、fixtureのjob数を本番のjob数と混同しない。
この観測は約94 KB・102 KBのmetadataだけであり、trace payloadの走査やqsubは行っていない。
2ファイルのhashと観測script・stdout/stderrも保存した。

9ファイルの [保存manifest](data_tile_validation_2026-10-17/low_timing_recovered_entry_v1/manifest.json) のSHA-256は `a7659d29641d70fbd16c7dc0aca114ddd11f979aea4308d942a8dda6896299fe`、入口sourceのSHA-256は `55948ae30cd283da6abc2e17c4548a69cda1f43b137f41e847247ac266a7318d` である。
再現コマンドは `A:/dev/mcmc4qec/.venv-experimental-optional/Scripts/python.exe -m pytest output/low_timing_reader_extension_v1/test_recovered_entry.py -q` である。
本番readerの実行、portable側の対応入口、子プロセスCLIと親selectorへの接続、全経路のLinux受入は未完了である。

## Portable C0T2の入口と部品の統合受入

`tile_low_noise_timing_portable.load_complete` を追加し、固定final snapshotとconfig、既存のmixed provider、元環境trace reader、共通WSS検査、実数値再集約を接続した。
対象は既存providerが扱うC0T2に限定し、全768群・全192 seed・両PCの実行履歴を既存readerが確認する構成とした。
PC側の処理に架空のPBS jobを付けず、sampling・collector・trace監査・reference・reference監査・final reportのクラスタ上の実役割だけを照合する。
bindingのanalysisは `portable_mixed_context` と明示し、従来のクラスタanalysis manifestとは区別する。

単独受入は14 passed・5.11秒だった。
数値再集約とPBS ledger checkerは実コードを使い、archive/native reader・snapshot・WSS監査は明示的なmockで接続を試した。
case・target・root・pin・最終job・点推定・群数・native scopeの不一致、sampling実行中、監査・final jobの失敗、回復経路との混同を拒否した。
実C0T2のfinal reportはまだ無く、本番データをこの入口で読んだとは扱わない。

参照監査・共通照合・子プロセス・回復入口・portable入口の5受入fileをまとめ、83 passed・16.59秒を確認した。
6 sourceと5 testのhashを試験前後で比較し、全て一致した。
これは先行試験との重複を含む統合受入であり、独立に83件の科学実験を追加したわけではない。
保存した15ファイルの [manifest](data_tile_validation_2026-10-17/low_timing_portable_entry_v1/manifest.json) のSHA-256は `0e34070f3c704eddf669830b1adfef2883465912f78649185a32aec290f2e566` である。
portable入口のsource SHA-256は `cf57b0c047626c1eca955445adbbc350d535fbf8ca03a9d129cadd1c2fa1b9d4` である。
単独試験は `A:/dev/mcmc4qec/.venv-experimental-optional/Scripts/python.exe -m pytest output/low_timing_reader_extension_v1/test_portable_entry.py -q` で再現でき、統合受入の対象fileは保存JSONに列挙した。
子プロセス用CLI・source/native bootstrap・親selectorへの接続と資源根拠の対応、全経路Linux受入、本番実行は引き続き未完了である。

## 子プロセスCLIとimport前の検査

`tile_low_noise_timing_reader_cli.py` を追加し、外部SHAで固定した入力、Python実体、全core source、明示したmoduleとlocal import、native binary census、実import先を科学importの前後で照合する。
親PID・host・PBSのRとrun_count 1・投入script・資源設定も読取前後で確認する。
返り値は当該条件の2 epsilon行、全352候補・各192 seed、監査binding、入力hashと解決先を保持し、全12条件の選択や独立計時の完了とは区別する。
変更やreader例外を未完了・科学的な不適格へ読み替えず、成功結果を保存しない。

bootstrap 25件と返り値処理19件は計44 passed・2.27秒で成功した。
実子プロセスを使った2件では同名readerの異なる配置を分離し、native変更による失敗のstderr・終了codeを保持した。
科学reader・PBS応答・native bytesは明示したfixtureであり、実科学監査や実PBSジョブの受入ではない。
初回統合ではWindows venvのpython.exeが中継プロセスを作り、即時の親PIDが一致しないため1 failed・128 passedとなった。
本番の親PID検査を緩めず、Windowsの実子プロセスfixtureをbase interpreterへ固定した後、全8受入fileで129 passed・20.53秒を確認した。
失敗時のlogとcompletionも削除せず保存した。
LinuxではCLI・実プロセス・bootstrapの4受入fileを実行し、最終のsource/testに対して61 passed・8.06秒を確認した。
qsub、sampling、decode、実trace読取は行っていない。

21ファイルの [保存manifest](data_tile_validation_2026-10-17/low_timing_reader_cli_v1/manifest.json) のSHA-256は `dc1880d4c56b5cd75b72de348c7ee3f14b4604191c76f24fc941d7b30eb4f450`、CLI sourceは `4fbf7e522e7c00b122aecabd7f1321f6233c513da5bcf2eedf84a00cd9b2bf9d` である。
親selectorによる返り値の受理、全12条件の実descriptor、計画・資源・stage4への接続、全科学readerのLinux受入、本番実行は未完了である。

## 親側の返り値受理と全部品のLinux受入

`tile_low_noise_timing_child_result.accept_reader` を追加し、親が実intent・handle・completion・stdout/stderr・結果hashを同じprocess specへ照合する。
実子PIDと現在の親PID/PBS、外部入力pin・entry・環境・2 epsilon行・全352候補と192 seedの分母を再確認し、子の全input hashと解決先を親Evidenceへ引き継ぐ。
既存のprocess completionは書き換えず、プロセス正常終了と単一条件の読取受理、全12条件の選択を区別する。
実子プロセスを使う16件は5.71秒で成功し、結果・入力・環境・PID・分母・artifactの不一致と、受理後のraw fixture変更を拒否した。
科学readerとPBS応答は引き続きfixtureである。

全9受入fileのWindows実行は145 passed・25.00秒だった。
Linux初回は配置対象から既存の `decoder_platform_linux.json` と `decoder_platform_fixture.json` が漏れ、68 failed・77 passedとなった。
不足したmetadataをhash付きで追加した別rootへ配置し、ソースや検査を緩めず再実行すると145 passed・27.61秒となった。
159配置fileのhashを実行前後に照合し、親受理部品を含む全受入を確認した。
これは既存のprofile/fixture metadataを参照する軽量試験であり、native probe・decode・sampling・実trace読取・qsubを実行したものではない。

source・metadata・失敗時と成功時のlogを含む174ファイルの [保存manifest](data_tile_validation_2026-10-17/low_timing_all_readers_v1/manifest.json) のSHA-256は `afdad91e65a91ffbf8cf196c2927a6c070c7d6e005671c102c1f5ec9b66875a5`、親受理部品のsourceは `cc3e0bb64d90f31b2c67efb9f8cfaea6f6f201a0bad92c2d9dbb61121b4cfe80` である。
Linuxの試験rootは `/home/user/workspace/mcmc4qec/20261020-low-timing-all-readers-v2` で、公開候補や実行中のpipelineとは分離している。
正式selectorへの子プロセス起動・受理の組込み、全12条件の実descriptor、計画・資源・stage4への接続、実回復v1/v2とportableの本番配置・読取は未完了である。

## 隔離selectorからの逐次起動と受理

隔離copyのselectorへ新2経路のdispatchを追加し、`tile_low_noise_timing_isolated` が固定templateを検査して、子入力JSONの排他保存・実handleの待機・正常transportの確認・親側の返り値受理を逐次行う。
待機timeoutは同じhandleの観測として扱い、再起動しない。
全12条件が揃わなければ24行をpendingとし、完成を宣言した新経路のmetadata/templateだけを検査して子を起動しない。
実科学入力rootが宣言rootに含まれることも確認し、子の作業先を科学入力から分離する。

旧3経路とsource bindingの回帰は65 passed・15.93秒で成功した。
その後、input rootの申告漏れを拒否する受入と、投入scriptのhashが入力manifestへ循環しない受入を追加した。
templateでは親scriptのパスと資源を固定し、script hashは親wrapperのbegin/finishによる実submission検証の内側で子入力へ記録する設計とした。
これにより、入力hashを含む親scriptを先に作れない循環を避け、外側のwrapper検証は引き続き必須とする。
現versionの追加2 fileは22 passed・7.98秒、全11受入fileはWindows 167 passed・31.91秒、Linux 167 passed・33.60秒だった。
Linuxでは162配置fileの実行前後hashを照合した。
科学reader・PBS応答・子の待機境界に明示的なfixture/mockを使い、実運用のtrace読取や新しいqsubを実行したとは扱わない。

191ファイルの [保存manifest](data_tile_validation_2026-10-17/low_timing_selector_dispatch_v1/manifest.json) のSHA-256は `cdf456f6ef0ac5c0bd4fe0a06c21caae332d12d326a3bbd350240327f2b7a6ba` である。
隔離起動部品のsource SHA-256は `a45d0630f6137b0b35c96802e3151c8f3c3ab82c06fcc51459bff1ce5bf8aab8`、隔離selectorは `2a5849e729439352ca6795d57660fa1c4fad651f3aa164c01261991d72d6769d` である。
回帰65件の後に追加した2つのtemplate検査を混同しないよう、各段階のsource pin・配置script・失敗する受入logも保存した。

残る親側の接続点は、既存 `submit_tile_low_noise_timing_selection.validate_config` の3 reader限定と、`confirmed_resource` が通常のterminal receipt・partition collection summaryを前提にする部分である。
回復済みとportableの実最終job・履歴をその固有schemaで結び、実測に基づく資源根拠、親scriptの実行時hash、子templateの資源を整合させる必要がある。
さらに全12条件の実descriptor、後段planとstage4の実source/argv接続、本番配置・読取が未完了である。
公開候補と実行中のpipelineのsourceは変更していない。

## 親の最終job metadataと実C0T1の照合

`tile_low_noise_timing_final_metadata.read_final_metadata` を追加した。
回復済みreportのprepared・guard・qsub receipt・internal completion・parent completionと、portable reportのconfig・qsub response・execution・completion・terminalを、それぞれ元のschemaのまま照合する。
外部pin済みreport bytes・script・同じ最終job・run_count 1・正常終端へ結び、実 `resources_used.walltime` と `resources_used.mem` を返す。
要求資源を実測値へ読み替えず、実測欠落・無効値やmetadata改変を拒否する。
子によるraw/native/WSS/archive検査を省略する部品ではない。

縮小受入はWindows 26 passed・2.24秒、Linux 26 passed・0.10秒だった。
その後、C0T1の元report rootを読み取り専用で照合し、job 265341の実qstatとも一致することを確認した。
元report SHA-256 `db0fbd9ea104bf55c5f5a84d29f5cf291e4312a47061f567fa4de156d537bcb2` を維持し、実測walltimeは3071秒、peak memoryは2,049,712,128 byte（約1.909 GiB）だった。
要求メモリ251 GiBを実使用メモリとして扱わない。
今回の実metadata観測は3.57秒で、reportのstreaming hashと保存metadataを確認し、trace読取・decode・数値再計算・qsubは行っていない。

16ファイルの [保存manifest](data_tile_validation_2026-10-17/low_timing_parent_final_metadata_v1/manifest.json) のSHA-256は `c0771be6c717b338170149a3522e81f40091fe8267822eed16f40331c8076b99`、metadata reader sourceは `4b64e5225d188ce5fd4213d0e756001e588cd24a2ce5f11098fe868818f97095` である。
portableの本番最終reportはまだ無く、その実記録での照合は未実施である。
外側wrapperの `validate_config`・`confirmed_resource` への組込みは次の作業であり、元の公開wrapperは変更していない。
組込み時はこのmetadata readerもimport前のsource/origin censusへ含め、wrapper自身のlocal import closureを実ファイルから照合する。
新経路の最終readerが行うcollection読取を元の最終jobの計時へ結び、架空のpartition collection jobやsummaryへ変換しない。

## 親wrapper接続と実環境bootstrap：11:30 JST追記

隔離版の親wrapperに新経路のmetadata・資源計上・子templateの接続を実装した。
全12条件と16参照の既存検査を維持し、352設定・67,584行・192 seedの範囲と、精度・被覆を認定していないことを照合する。
追加受入はWindows 212 passed・62.22秒、Linux 212 passed・48.81秒で成功した。
既存の親・selector・source bindingの回帰はWindows 120 passed・77.38秒、Linux 120 passed・67.55秒で成功し、各fileの最大時間は26.51秒と25.77秒だった。
最終実装のhashが両回帰試験時の固定sourceと一致することも保存時に確認した。
fixtureの実prepare、begin、finish、sealを通してstage4 descriptorの受理まで確認したが、qsub応答と科学読取は縮小fixtureであり、本番の全計時planを実行した証拠ではない。
最初のlifecycle試験ではfixtureが古いselector moduleを保持していたため失敗し、そのlogを残してfixtureの参照だけを修正した。
source・argvの検査は緩めていない。

別途、新しいPythonプロセスで実97 source・137 native fileのbyteとimport originを照合し、Windows 2.545秒、Linux 2.242秒で通過した。
この実環境検査はraw trace・decoder出力・PBS実行の再検証を含まない。
205ファイルの[保存manifest](data_tile_validation_2026-10-17/low_timing_parent_wrapper_extension_v1/manifest.json)のSHA-256は `8de7cfbe6ba4e54f29db8de097294eff877ed68c0294fb5871c4449f499e7aba` である。
隔離親wrapperのSHA-256は `27b5645790b9c62780265db5bcc7874ba62c70605811811d42d5c73cb4e349c3`、隔離起動部品は `117d339648dbb04993595bfef349c5556e18248f7f460835ee203d6426768f43` である。
公開候補・元のcluster_scripts・稼働中pipelineは変更していない。
全12条件の実descriptor・実測資源決定・本番選択のprepare/qsub・独立計時は未実施である。

## 完了済みC0T0/C0T1の実子環境候補

元の保存preparedと回収receiptに基づき、C0T0/C0T1それぞれの実helper rootを使う別プロセスで、元reportのsource/runtime bindingと新readerのbootstrapを照合した。
両条件とも98 source・137 native fileを固定し、bootstrapと元bindingの照合は2.275秒・2.268秒で通過した。
最初の配置では旧bundleに `tile_reference_source_binding` が無く、両条件ともimport時に失敗した。
その失敗を保存し、別の新directoryで、Linux受入済み配置から追加3 moduleだけを解決する参照先を設定して再確認した。
元のsourceと実行中bundleは変更していない。
補足したmoduleは `tile_reference_source_binding`・`tile_low_noise_staging`・`tile_low_noise_staging_control` であり、受入済みarchiveのhashとも照合した。

実際の最終reportが使うinventoryは、C0T0の `20261019-tile-low-bar-recovery-v2/helpers` とC0T1の `20261019-tile-low-bar-recovery-c0t1-v1/helpers` にある。
今回の両ファイルはともにSHA-256 `4156d55c93d80502f6ded4233e41d6ccb0cee2974570b7c2cefe868abb95f016` であり、directory名のv1/v2から内容の版を推測しない。
絶対pathの異なる元source bindingは別々に保持した。
C0T0のenvironment SHA-256は `ed272c244eddb6bb0ed1bc3825d090e90c2a8611a29950de99c08af2702c5e11`、C0T1は `c4225d469fa655fe76632b1522e67c69178d344dc59a0edbf7f6c6d2a53c4152` である。
28ファイルの[保存manifest](data_tile_validation_2026-10-17/low_timing_actual_recovered_environments_v1/manifest.json)のSHA-256は `75b0e0ab62718a4cb4e3cec0853b17e7088f03e168776ef3692429ed498ec096` である。
これらは実子environmentの候補であり、raw reader実行、decoder挙動再検証、全12条件の親descriptor・資源決定・qsubは未実施である。

## 実entry候補とreferenceの配置先差：11:48 JST追記

C0T0/C0T1について、元の回復authorityの相対pinを元sampling rootへ解決し、WSS監査のdone markerからcondition payloadのpinを取得した。
各25ファイルのmetadataを照合し、元reportの最終jobを実qstatで再確認した上でentry候補を保存した。
C0T0の最終job 265333は実測1747秒・1,586,446,336 byte、C0T1の265341は3071秒・2,049,712,128 byteだった。
親script/resourceと子directoryは未決定であり、これらを本番parent inputとして受理したとは扱わない。
この段階の10ファイルの[保存manifest](data_tile_validation_2026-10-17/low_timing_actual_recovered_entries_v1/manifest.json)のSHA-256は `35cdfd8ff66ef548c4b4cd21ea6f3c1152960702a58129f71a153667606002c9` である。

続く実C0T1の照合で、最終reportの `reference_audit` とWSS監査conditionのreportは `source_sha256` の絶対配置先だけが異なり、それ以外の全フィールドのcanonical digestは一致すると確認した。
前者はlow-analysis-v11、後者はlow-analysis-v7であり、従来の完全一致検査はこの実データを拒否する。
小仕様を追記して追加受入を先に実行し、2 failed・8 passedを確認してから、両配置の実byte検査を通過した完全なsource mapに限って受理するよう共通readerを修正した。
第三の配置、hash改変、欠けたsource、数値・入力・scopeの相違は拒否する。
元の保存recordは変更せず、照合済み最終reportの表現と元監査recordを返り値で別々に保持する。

関連受入64件が16.44秒で成功し、統合はWindows 222 passed・66.88秒、Linux 222 passed・49.81秒だった。
実source/native bootstrapも修正後に再確認し、各98 source・137 native fileの2条件が通過した。
修正後environmentのSHA-256はC0T0が `2c555b0873d9e19bc5a43a243e68b6c0e0ecf8eb9ccc6ae586b3aa558545ed4e`、C0T1が `bf25d06d0c4efd182e682aea2bea2155ad2bec153685388421772f6cdd62efe4` である。
今後のentry候補は、旧environmentへの参照を保持した履歴から、この修正後environmentへ明示的に更新した候補を使う。
候補・実データの相違観測・失敗する受入・Linux配置sourceを含む201ファイルの[保存manifest](data_tile_validation_2026-10-17/low_timing_reference_report_relocation_v1/manifest.json)のSHA-256は `d4e2187a82a300118e6be01e4354d213971cc4228a5dd5f33e7e94555432578b` である。
共通reference readerのSHA-256は `8780ff025d84e61b42a42466ccbd393a10f2f5102e327248951cacf330b7afd9` である。
元reportの数値再計算、raw referenceの再監査、本番raw reader・選択・独立計時は今回実行していない。

## staged 3条件と親実環境の準備：12:18 JST追記

C2T0/T1/T2の既存14ファイル回収記録を起点に、既存のsealed snapshot readerで元reportと実qstatを再照合した。
元のfinal configに含まれるstaging control pinを維持し、各77ファイルのentry候補を作成した。
最初の配置は旧環境に `tile_reference_source_binding` が無いため失敗し、失敗を保存した上で別配置から受入済みの同moduleを追加参照して通過した。
親の元Python・core・科学moduleのimport位置を保持し、新しいselectorへの置換を明示した。
親bootstrapは93 sourceと、元configのldpc native binding 8ファイルを照合して成功した。
この8ファイルはldpcの共有libraryであり、子environmentで確認したnumpy/scipy等を含む137ファイルの全体censusとは区別する。
親environmentのSHA-256は `2c202f2fb6213c488bf52ed4d95eabdfa2a8f7a4867ed20e9eafe5dea61779ea` である。

| 条件 | 最終jobの実walltime | 実peak memory（byte） | 元copy jobの実walltime |
|---|---:|---:|---:|
| C2T0 | 1840秒 | 1,531,842,560 | 771秒 |
| C2T1 | 2539秒 | 1,508,003,840 | 950秒 |
| C2T2 | 2844秒 | 1,854,623,744 | 1173秒 |

今回の保存collection summaryは最終reader内の読取に対応しており、資源候補では同じ最終jobの費用を二重計上しない。
copy jobのwalltimeと、copy summaryの経過時間は別フィールドで保存した。
これらを要求walltime、計時対象のsampling費用、全12条件の確定資源予算へ読み替えない。
32ファイルの[保存manifest](data_tile_validation_2026-10-17/low_timing_actual_staged_entries_v1/manifest.json)のSHA-256は `638c65605c0928d6b1d559198a8ad059afdf2392ff0b902035e1d51fc9386583` である。

完了済み5条件と未完了7条件を[部分入力inventory](data_tile_validation_2026-10-17/low_timing_partial_input_inventory_20261020_v1.json)に固定した。
5候補すべてが同じWSS reference root・監査summaryのpinを参照することを確認した。
既知5条件の最終jobの実walltime合計は12,041秒だが、追加hash、copy再検査、残り7条件、待ち行列を含まないため、全体ETAや確定資源とは扱わない。
inventory SHA-256は `9541a9df2326f98629fceac72f7b3f2e0d2a5ae591802bd61eda1a74d4b21855`、再現builderとinventoryの[保存manifest](data_tile_validation_2026-10-17/low_timing_partial_input_inventory_sources_v1/manifest.json)は `e23423e0f52d8e9ae3caff67539114cb76a78fc7e1a7d2d13b73b5fa104f527c` である。
部分inventoryはselector inputやaccepted-all-twelve記録ではなく、本番raw reader・全12条件の選択・独立計時・qsubは未実施である。

## C0T2追加：22:59 JST

C0T2の実最終reportは元venvを明示する新wrapperで作られていたため、計時readerのsnapshot依存をその実回収moduleへ接続する別配置を用意した。
変更は1つのimportに限定し、Windows/Linux各16件の受入と、実元config・source・runtimeのbootstrapを通過した。
実子環境は108 source・137 native binary、実metadata候補は157入力である。
最終job265366の実walltimeは2035秒、実peak memoryは1,352,040,448 byteであり、独立計時の結果ではない。
詳細と失敗を含む配置履歴は[C0T2の接続記録](low_timing_portable_venv_spec_2026-10-20_ja.md)に保存した。
同じWSS reference監査summaryを参照する6候補・6未完了の[部分inventory v2](data_tile_validation_2026-10-17/low_timing_partial_input_inventory_20261020_v2.json)へ更新した。
全12条件のselector input・parent資源決定と、本番raw reader・独立計時は未実施である。
