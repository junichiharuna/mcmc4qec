# 低ノイズ selector 親入口の初版実装記録

2026-10-18時点のowner実装記録であり、独立レビューは依頼済み・未完了である。
新sourceは `cluster_scripts/submit_tile_low_noise_timing_selection.py` の1本だけで、既存科学source・既存bundle・import pathを変更していない。
正式input、親の正式受理receipt、正式資源decision、remote配置、qsubは未実施である。

## interfaceと実行範囲

`prepare(root, config_path, expected_sha256)` は外部固定configを読み、正式inputの全12complete、全12親受理receiptのentry digest、全16条件WSS audit成功、確定資源metadataを検査する。
親受理receiptは既存受理判断の集約を外部pinして受け取り、wrapperが自動で受理を捏造する処理は持たない。
資源decisionは全12final/collection・staged copy/hash費用の外部証拠、scope差、正数の基礎量・保守係数、親確定理由を必須とする。
1 CPU・1worker・1node、340GiB・24h以下、全体最大2nodeを検査し、resource未確定はprepare/executeできない。
資源decisionが持つ費用は親の確定判断であり、wrapperが全12raw実測を新たに行った、あるいは完走上界を証明したという意味ではない。

preparedは第4段階のexact execution descriptorに合わせた値だけを保持し、config pinと受理根拠・input/source/core/Python/nativeのpath/byte/identityは別control metadataへ保存する。
controlはfile byte SHA、preparedはcanonical object SHAをscript/親の実行引数に固定する。
標準libraryだけのbootstrapでsource/core/native/Python byteとactual import origin・既存aliasのresolve先を検査してから科学依存をimportする。

`submit(root, control_sha, execute=False)` は既定で未投入の準備情報だけを返す。
execute時は共通lockの所有token、controller、queuedを含む2node上限、現source/input/scriptを確認し、intent保存後に同じgateとregular file/path/identityを再確認してqsubを1回だけ呼ぶ。
intentとlockの同bytes symlink置換も拒否し、foreign lockは削除しない。
実stdout/stderrとjob IDを保存し、曖昧応答・例外はintentとlockを保持して自動再投入しない。

PBS scriptは `begin`、既存selector CLIのexact 1行、`finish` の順である。
begin/finishは実qsub receipt、PBS R・run_count=1・resource・script・host、固定thread/Python/runtime/native/sourceを確認する。
既存selectorの保存ACF/row検査・算術再集計・current raw hash・小native fixture probeをそのまま用い、BAR/ACF/traceの全科学解析を再実行する新経路は作らない。
finishは全24identity、各192分母、全候補、未選択/未達状態、speed_ratio=null、非保証flag、全12bindingを確認し、開始時入力とexecution identityの一致を保存する。
親 `seal` は実PBS F0/run_count=1・resource・script・hostを確認し、実 `tile_low_noise_timing_evaluation_report.selector_evidence` で7descriptorを受理する。
sealはmetadataと固定source/nativeの読取であり、raw traceの追加再走査は行わない。

## 軽量受入

小仕様の後に受入fileを作成し、module未実装の `ModuleNotFoundError` を確認してから実装した。
初期fixtureの全source closure反復が重いため、その試験を中断し、境界試験のclosureを明示的な縮小mockへ変更した。
最終owner受入は `tests/test_submit_tile_low_noise_timing_selection.py` の28件成功、43.78秒、skipなしである。
実行Pythonは `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe` である。
既存selector.runとchooseを縮小設定・各192標本の数値fixtureで実行し、実第4段階descriptor readerへ接続した。
raw reader、native input、PBS、resource費用、source closureの縮小部分はmockであり、正式768group・全raw audit・fresh native環境・Linux計測を行ったとは扱わない。
全24/192保持、全12completeと全16reference audit、未確定resource・source/native/Python改変、postintentのbytes/symlink/lock/script/input改変、2node/controller、曖昧qsub/timeout、compute後input/report/execution/native改変を検査した。

初版source SHA256は `494923339f04141cb2420ca5f248d4abca7d706621947660e7106924dcbca1b0` である。
受入file SHA256は `4432a9cd96c25a6b3de7e5b5c0f2cbf93e710a68962d4aff8fe85aeeec7380a4` である。
独立reviewで修正が生じた場合は初版の成功を修正版の成功へ読み替えず、追記する。

## 独立review指摘とv2修正

初版の独立受入は28件成功・41.70秒であったが、reviewerが3点を独立probeで実証した。
import_originsの非空subsetを許したため未列挙shadow moduleが拒否前に実行され、資源のfinal/collection pinは任意JSONを受理し、qsub例外のpartial stdout/stderrは保存されなかった。
初版のreview/probe証拠は別ファイルに保持し、初版を最終受理済みとは扱わない。

v2のimport前gateは全cluster moduleと全core Python fileを導出してorigin censusの完全一致を要求し、固定sourceのASTから推移的ローカル依存の欠落も検査する。
origin名はtop-level識別子に限定し、dotted find_specによるparent import副作用を避ける。
現Windowsの実closure90source・59originでmetadata gateと実source mapの一致を確認した。
この確認は既にimportされたprocessと明示的なexecutable native fixtureを使ったもので、正式native/PBS環境の受理ではない。

資源decisionのfinal job IDは受理済みreport、collection job IDは固定collection summaryへ結合し、実terminalのF0とresources_used walltime/memを必須にした。
独立collection jobが無い場合はincluded_in_finalを明示して同一jobの二重計上を避け、staged copy実summary・実PBS・elapsedと追加hash pass proxyも結合する。
全12の実費用と追加hash予算より小さいwall基礎量、実RSSより小さいmemory基礎量は拒否する。
親による全12Evidence保持の追加見積りや政策上限を完走保証へ読み替えない。
qsub例外にはcommand・returncode・partial stdout/stderrを保存し、bytes応答はbase64で可逆保存する。

中間の単一file受入が69.07秒となったため、post-compute接続とreview回帰を別testfileに分けた。
最終v2 owner受入は主file23件成功・39.18秒、review file19件成功・45.68秒、計42件、skipなしである。
各testfile60秒以内へ戻した後の結果を最終owner受入とする。
source SHA256は `70554a13dca33f7ec12dab4e975dc0a1fd591193effac474661a8bb0b53b1173` である。
主受入file SHA256は `e155cbcb3fdb436691bb78f299635bbf2873149c7841023fd60ab928d269dcd2`、review受入file SHA256は `8c0cdd941422f59ac9a62c1ed6658d7960e5ebe75c60297e7c53fbd7c5732069` である。
v2を再freezeして独立差分reviewへ戻し、正式input・remote・qsubは引き続き未実施である。

## v2独立受入完了

独立reviewはSPW1〜3の解消を確認し、追加blocking findingなしで受理した。
独立試験は主file23件成功・35.57秒、review file19件成功・46.54秒、skipなしであり、source/testの終端SHAがfreezeと一致した。
実90source・59originのbootstrapも独立確認され、旧shadow probeはimport前拒否、空costは拒否、timeoutのstdoutと非UTF8 stderrはexact保持へ転じた。
独立証拠は `data_tile_validation_2026-10-17/low_noise_timing_selector_parent_independent_review_v2.json`、SHA256 `1d1032b22de0ddb0f3a20022b724383f8fe549c876979ac5eebb3c45c6db43d7` である。
実装と軽量受入は完了したが、production native環境、正式資源、正式input、remote配置、qsubは未実施である。

## Linux v2 配置と軽量受入

受理済みsource `70554a13dca33f7ec12dab4e975dc0a1fd591193effac474661a8bb0b53b1173` と2受入fileを変更せず、独立root `/home/user/workspace/mcmc4qec/20261018-tile-low-timing-selector-parent-v2` へ配置した。
既存source、Python、venv、Stage3/4起動設定は変更していない。
同wrapperをPBS scriptのbegin/finishでも実行する設計なのでWindows専用ではなく、Linux配置が必要である。
Python呼出pathは既存 `/home/user/workspace/mcmc4qec/20261018-tile-low-timing-stage2-v1/venv/bin/python` を維持した。
この専用processだけのPYTHONPATHには新wrapper、既存Stage4/census、既存Stage3/2/selector/control/staging/v11 sourceを順に指定し、従来Stage3/4のbase PYTHONPATHを変更していない。
全86 sourceと59 import origin、各pathの実解決先、既存selectorとexecutionのclosure、Python bytes、native binary集合とprofile/fixture bytesを開始前・終了後に照合した。
新配置はfresh native decoder probeではなく、受理済み環境のbinary/metadata一致の確認である。

Linuxの主fileは23件成功・pytest 24.07秒、review fileは19件成功・31.03秒、合計42件成功、skipなしであった。
subprocessを含む測定時間は各24.37秒・31.34秒で、各file60秒以内である。
独立した縮小fixtureで実selectorと第4段階descriptor接続を確認し、正式科学payloadや正式12入力を読み取っていない。
正式12入力、費用、資源は未確定であり、正式prepare、scheduler query、qsubは未実施である。
正式時には本bindingのsource/origin/Python/nativeと専用PYTHONPATHを外部固定し、確定したall12 acceptanceとresource decisionを与えたprepareから、submit直前・begin・finishの既存bootstrapを通す。
この軽量受入を正式資源受理や実PBS完了の証拠として流用しない。

初回Linux v1はpytest basetempの親directory作成漏れにより23件がfixture開始前にFileNotFoundErrorとなった。
初回rootと失敗証拠を保持し、配置helperのみを補正した別v2 rootで受入をやり直した。
v1失敗receipt SHA256 `3c08ead3661986e9b2c0604e1ef776f02ce0f7c474587d018a5b8d4e1c79ccf3` はv2の外部pinへ含めた。
v2 source bindingは `data_tile_validation_2026-10-17/low_noise_timing_selector_parent_source_binding_v2.json`、SHA256 `3440efa1eff29f297a534ea273bf7db44e5f50decf6d12cd9fe4f5c24b2102da` である。
前後snapshot、全actual originとresolved path、専用PYTHONPATH、既存base PYTHONPATH、runtime、各試験stdout/stderr、回収hashは同bindingと参照deployment証拠へ保存した。
