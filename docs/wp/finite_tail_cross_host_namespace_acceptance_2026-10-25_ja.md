# 有限tailのhost間stat比較：修正と受入範囲

PBS側とlogin側で同じ共有homeのdevice番号が異なるため、保存stat全体の一致を要求する後続処理も停止する可能性を確認した。
元の科学設定、実merge、受入済み計算、元source/config/ledger/scriptは変更せず、新しいbinding・dispatch sourceと別configを作成した。
本記録はmetadata比較と実行入口の受入であり、後続の科学計算や最終reportが完了したという記録ではない。

## 対象と修正

旧dispatchのfinalizerは、PBSで封印したlock/carrierのstatをlogin側とdevice込みで比較していた。
旧bindingも、PBSで作ったsymlinkのlstat/target statをlogin側で丸ごと比較していた。
有限job wrapperのartifact比較にも同じ形があるが、現在のtail operationはそのartifacts集合を返さないため、今回の直接呼出経路では使われていない。
wrapper自体のsourceは変更していない。
outerのbounded read前後、relocation loaderのread前後、probe内の同process比較はdevice込みの厳密比較を維持した。

新しい共有namespace authorityは、loginのlocal XFS homeと、許可された2計算nodeのNFS home export、固定小sourceのhash・inode/size/time/mode、実PBSのF/0・run_count 1・script/hostを結ぶ。
観測したdevice番号はloginで2049、計算node Aで49、Bで46だった。
この対応が実mount観測と一致する場合だけhost間device差を扱い、inode・size・mtime_ns・ctime_ns・modeは一致を要求する。
同host比較、namespace外、未承認host、mount/export変更、symlinkの経路・readlink・target変更は従来どおり拒否する。
statは内容hashではなく、巨大carrierやnative binaryの再hashをloginで行ったとはしない。
元PBSのhashは、その観測時点のprovenanceとして保持する。

新dispatchはqsub停止境界でproducerの実job/hostをparent bindingへ結び、元intercepted receiptとcandidateに封印する。
sealまでのlock/intent/script所有権確認、source hash、親F/0、fresh gate、曖昧なqsub応答時の停止、元ledger形式を維持する。
aliasのproducer結合は、固定されたPBS worker→実parentとの一致→alias生成→completion/candidate封印→Coordinatorの受理という既存経路を引き継ぐ。
helper単体が任意のjob置換を検出するとは主張せず、強すぎたfixture doubleを実際のAPI境界へ合わせた。

## 実受入

| job・段階 | 実結果と範囲 |
|---|---|
| 265665 | F/0、74 tests。元wrapper31・observer30・namespace13と、node Bの小source/mount witness。 |
| 265666 | F/0、node Aの小source/mount witness。両nodeの終端証拠を固定してauthorityを組み立てた。 |
| 265670 | F/0、77 tests。dispatch31・alias36・既存Coordinator受取6・実job wrapper guard4。 |
| 265671 | F/0、別source/configの生成。outer変更はbinding・dispatch・source_pinsの3fieldだけ。 |
| 265674 | F/0・run_count 1・walltime7秒。probeの13 testsと、全6role×変換前後＋final-report constructorの13ケースに成功。 |
| 265674後のlogin確認 | 実際の新binding/dispatch/helperでscratch alias・lock・carrierをPBSからloginへ照合し、scratch lock解放まで成功。実qsubは禁止した。 |

先行265668/265669ではexact source変換の改行位置の取り違えを検出し、旧stageと部分生成物を残した。
元sourceの実1行に合わせて変換patternを修正し、fresh stageで受け入れた。
数値計算や科学的判定を変更する修正ではない。

constructorは、既存merge265660と受入265661、completion原本hash `c44b7cddc0b1bbefeab3a629ff932054a5d9c045301415cf41f38ccd7bce5946`、受入済observerの小proofに限ってMの既存を許容する。
旧failed Mの4metadataと、完成Mのprepared/accepted/terminal/submissionの4metadataをboundedなpin例外として区別し、巨大result/selection本体は開かなかった。
future tail出力先の未使用、旧設定の拒否、実source/import contextと4MiB read guardを維持した。

scratch往復は専用stage内の小source symlink、内容readを禁止したcarrier、専用lock/intent/scriptだけを使った。
実親PBSのF/0を確認した後、login側で実verify_aliases・check_candidate・finalizeを通した。
finalizeには偽runnerだけを渡し、返した架空job識別子とledgerはscratchに限定した。
元APIのscratch内部結果にある `qsub_executed=true` は偽runnerの結果であり、外側の受入記録は `actual_qsub_executed=false` と区別している。
本番出力の変更、実science qsub、carrier内容の読込は行っていない。
詳細は[alias側の受入記録](finite_tail_alias_namespace_2026-10-25_ja.md)と[独立レビュー](cross_host_artifact_stat_review_2026-10-25_ja.md)を参照する。

## 固定した取得起点

以下のパスは `$HOME/workspace/mcmc4qec` からの相対パスで、第三者のdownload URLではない。
記載hashは識別子置換前の原本を指し、この日本語文書のhashではない。

| 原本 | 相対パス | SHA-256 |
|---|---|---|
| tail config | `20261025-finite-tail-cross-host-v2/config.json` | `873a2c5cbde9693e7007b17a5b40ceac028ceb9533f78b428446489e133a6d3b` |
| namespace authority | `20261024-c3t2-index-relocation-v1/pipeline-state/shared-home-namespace-v1/authority.json` | `1db641382d82b9f6122a3607d44094771723cb63dd1c2a7ba3801312fd095465` |
| 受入ready | `20261024-c3t2-index-relocation-v1/pipeline-submissions/finite-tail-completed-merge-native-v1/ready.json` | `9db38edad846a9f1321a4a4f102d7b402662856716611e7505f26e9eb56c54b6` |
| constructor受入 | 同stageの `results/accepted.json` | `f12fcf6b575a894ad199c52d0b85f86305f9debaf869019da6eee4a7159b0063` |
| scratch往復受入 | 同stageの `namespace-roundtrip-scratch/observer-accepted.json` | `725562b9ff35dfc510c28db7160db4d75b10228ab1cb5c14da758106dfdbb476` |

constructorとreadyの小原本20件はlocal `output/finite_tail_completed_native_evidence_v1/`、scratchの小原本8件は `output/finite_tail_namespace_roundtrip_evidence_v1/` に回収した。
これらはraw科学データの再回収ではない。
元science childはunbound配置を取り得るが、namespace helperの呼出元はfinite aux PBSとloginである。
dynamic gateのhelper候補は元policyのA/Bのままで、science childの実nodeは2物理nodeの容量計算へ加わるだけでhelper候補へ昇格しない。
そのため今回、科学jobのscript/resourceを追加変更していない。
本番の再開判断はこの受入証拠を引き渡して別途行い、constructorやscratch成功を科学処理の完走として数えない。
