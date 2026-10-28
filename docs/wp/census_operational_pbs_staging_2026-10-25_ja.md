# census復旧の運用受入とPBS順序

実計測265678を保持した上で、運用上の本番割当は1 CPU・96 GiB・4時間とする方針である。
元式の16 GiB・45分候補とは区別し、metadata検証・親子RSS・実行余裕のための予算として扱う。
この予算は終了時刻の保証ではない。
元265675の失敗root、265678の計測原本、既存worker・merge・比較・handoffと科学入力は変更しない。

受入順序は独立pure fixture→凍結済みsourceによる実環境/config組立→native確認→root担当の本番起動である。
独立fixtureは既存shared physical gateで並列化できるが、未凍結sourceに依存するbuildを同時に開始しない。
このstaging担当は本番censusやcontrollerを起動せず、元jobを再投入しない。

resume controllerの25 fixtureは既存qsub 265679のF0証拠を利用し、重複実行していない。
別のcensus-only loaderについてqsub 265680で13 fixtureが0.017秒で成功した。
実qstatはF/0・run_count=1・walltime1秒で、要求は1 CPU・4 GiB・10分だった。
検査対象は新しい3つのeffective path、運用authority、outerの許可された変更だけを受理すること、旧root・相互包含・別科学path・元source mappingの書換えを拒否することである。
source/hashを前後で確認し、unittest subprocessには180秒のtimeoutを設定した。
実source/environment/bindingとの結合はこのpure fixtureの範囲外で、actual_binding_verified=falseを維持した。

小原本の取得先は `$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/pipeline-submissions/operational-census-loader-fixtures-v1/` である。
以下のhashはprivate原本bytesを指す。

| 原本 | SHA-256 |
|---|---|
| sources/recovery.py | `f4cb22ae8e3ac26d3606ec293dcdd3eb1ffdfa1613aedd1172f7a4ca2fb25408` |
| sources/test_recovery.py | `9c751a5de99604ea9d3622cc7255b08eb1652222fa7a51ecf42b91651857dc88` |
| accepted.json | `5765718e904a6fbcb045783952eb2d2084cfccf4f7f5ca0faae81444eb8b35ce` |
| terminal.json | `8a7c70827b306926967f45b4a934ce8e97c42ff290ba3308e1f18e9f50e2b533` |
| request.json | `822eb0a54ad79db3e521bf680bb3a4e8fc2cf41130cb7ca35f4fef6f7451f062` |

本稿記録時点で資源policyのpure fixtureと実環境組立/nativeはまだ未実施である。
fixture成功を全件seed census・統計的独立性・科学結果の検証へ読み替えない。

## 2026-10-25 10:02 JSTのfixture投入待ち

policyの28 fixture用sourceを凍結し、`pipeline-submissions/operational-census-policy-fixtures-v1` に固定requestとsourceを配置した。
既存physical admission gateは `waiting_for_capacity` を返し、`qsub_executed=false` で投入は行われていない。
新規の他ユーザーjob 265681・265682が既存allowedの両nodeをそれぞれ96 CPUで使用していることをfresh qstatで確認した。
要求walltimeは48時間だが、実際の空き時刻の予測とは扱わない。
投入未実施のstage、元の成功・失敗job、共有lockを保持し、容量不足を理由に資源gateを無効化したり別nodeへ無断で変更したりしない。
bindingの23 fixtureもsource凍結済みだが、stage作成・qsub・実行は未実施である。

| 凍結対象 | SHA-256 |
|---|---|
| policy.py | `cdabbcfc678957e4df4e4ec091d6c15aa1a872f7110d3dcb2960aca2bfdee459` |
| test_policy.py | `2ce226a93dc4af2d831e3d72a6b1ae7adb164507c3cb84a0c12db5ec5022a393` |
| policy fixture request | `6dad870069bdc2f12a250dec3577393e671c736ec037cad4a678c07cbfb46d34` |
| binding.py | `8db194a0e8e4cf8339893b277d40a0ea4f277de9f7facaf76d0e41f2b50d4028` |
| test_binding.py | `61ba83a54505f314ab9f2ac59d4fde900a06a75f4fed3ef19c0c2648652bb5b1` |

これらは原本bytesのhashであり、fixture成功や本番再開を表していない。

## 2026-10-25のfixture成功

運用上限は固定hostではなく最大2物理nodeであるため、fixtureだけを空きCPUのある別nodeへ移した。
新policyは `$HOME/workspace/mcmc4qec/20261025-census-fixture-node-policy-v1/policy.json` とし、元policyは保持した。
差分はallowed nodeの1つと、それに対応するplacementsのみで、capacity source・shared lock・dispatcher・上限は不変である。
新policyのSHA-256は `6c39576a3ba39fbe1b7afe1994180079f6d05b8749611b0eeb7b27f159d2a850`、移行記録は `412822f82e4b7fad2c3193bea8cf83bed8e02706c900eeeaf7b462a1efec532c` である。
元の未投入policy fixture v1 stageを保持し、fresh v2 stageをqsubで投入した。
各投入時に既存gateが2回のfresh censusを行い、当方の使用は同じ1 node内で1 CPU、次いで最大2 CPU・8 GiBと判定した。
後者は先行265685のRからEへの移行も予約量へ含めて受理し、当方の他node上のactive jobはなかった。

| 検証 | PBS job | 終端 | fixture数・実測 | accepted SHA-256 |
|---|---|---|---|---|
| 資源policyとcontrol閉包 | 265685 | F/0・run_count=1・wall2秒 | 28件・0.642秒 | `67f422b04c1470b0d4e1a49969640b3e778a48f8c0c4a6c379060707c1e47f32` |
| census専用環境・準備bridge | 265686 | F/0・run_count=1・wall1秒 | 23件・0.005秒 | `fc59cd5b7e655b733f73786532e3b24e9f73bfd92f9759a6834e6ab53fd556f9` |

原本は先述のrelocation root下 `pipeline-submissions/operational-census-policy-fixtures-v2/` と `operational-census-binding-fixtures-v1/` に保持した。
固定sourceの前後hash、実Submit_arguments、job ID、run_count、期待件数を照合し、小証跡をlocal `output/operational_census_acceptance_v1/` に保存した。
binding証跡の初回転送はJSONが途中で切れたため同じ終端jobを再照会して取得し、再投入はしていない。
実環境/configの組立・実constructorとの接続・全件census・本番controller再開は、このfixture成功には含まれない。
実環境組立も新policyでqsub投入する準備を進めるが、旧本番policyとcross-host namespaceの設定は変更していない。

## 専用環境の組立と後続制御の追加受入

実環境組立265687は同じfixture nodeの1 CPU・4 GiB・10分枠へqsub投入し、F/0・run_count=1・wall4秒・CPU4秒で終了した。
新bundleのsource・environment・config・basisを構築し、実wrapperのbootstrap/scienceとcensusのimport origin・preimportを検証した。
`built.json` は `$HOME/workspace/mcmc4qec/20261025-census-operational-bundle-v13/control/built.json`、SHA-256は `be4b8a29ba202bb3328fa9a184cf3ed7fcdab53d04088169955cb3e60dec16cb` である。
PBS終端のSHA-256は `4f51b6c117506c85234a79d26969c1fe7f4355ddb57021b674155f5c5feed144`、requestは `962a6aeaba93b87ca58712a6e3e7e6080f4bd41603389f160db2797d3433ce21` である。
元科学bundleを変更せず、その巨大payloadを読まない組立であり、`census_prepared=false`・`full_census_executed=false`・`controller_started=false` を保持する。

外側のoperation差分19 fixtureは265688でF/0・run_count=1、0.110秒で成功した。
accepted原本は `pipeline-submissions/operational-census-outer-fixtures-v1/accepted.json`、SHA-256は `a261991a0e477a8f26f504dde865c7965de36b964691f9d59d550a530ef7a7e3` である。
tail-only controllerの27 fixtureは265689でF/0・run_count=1・wall1秒で成功した。
accepted原本は `pipeline-submissions/operational-census-resume-fixtures-v2/accepted.json`、SHA-256は `c450d8195b50c74ded202194ceacb1ffe80f1f69c372241bf65ef54e36c9f0f8` である。
これらの実行に既存worker・mergeの再計算や本番controller起動は含まれない。
node移行のnamespace witnessと更新recoveryを結合する受入は別途必要である。

新helper nodeのnamespace witnessは265690でF/0・run_count=1・wall1秒となった。
元witness workerとnamespace sourceをそのまま使い、同じ小source sentinelと共有mount情報を新node上で照合した。
原本stageは `pipeline-submissions/census-active-node-witness-v1/` である。
acceptedは `d0da86310e2fc2b6b23d8eb24c1f8bf417b51c11a10e4a88bd45e8cbe98e4d1b`、witnessは `34279769a027a4a0670e1bbd8c36181d62e4ba7d36197fc07ba5ce1e419f58e1`、PBS終端は `6897f94484683b0f376ec4698751e4161743ce618c4566ec936220966aff1fea` である。
実job ID・run_count・Submit_arguments・requestとwitnessのhash結合を確認したが、新authorityと本番adapterへの統合受入は別工程である。

node移行helperの18 fixtureは265691でF/0・run_count=1・wall1秒、0.003秒で成功した。
原本stageは `pipeline-submissions/operational-census-migration-fixtures-v1/`、acceptedのSHA-256は `6f7fa12594487f7710ee23843a8e015750aa8b07ca17d6ed37e9fa0bb1863a87`、終端は `923c3c18142968aa3ef77637520f6bf35b610ec70f1e85bd04682d3781b897de` である。
受理済みhelper sourceは `d9c169fd0ac927687b9f83a47ecdcd4fbf7bd010d6d2ce915c968bf761887aa6` で固定した。
新namespace authorityと本番用policyの実組立・接続は、このpure fixtureとは別に検証する。

node移行を含む更新recoveryの27 fixtureは265692でF/0・run_count=1・wall1秒、0.022秒で成功した。
原本stageは `pipeline-submissions/operational-census-recovery-fixtures-v2/`、acceptedは `a5803301c260c97ff5fb0d85946f4eee7768a0243557262bdedaacf9e1d0f3e0`、終端は `d4082f9ecf208becdc8a65a9014ec0dbac5c1a6bc7d5426dd485fd72560a7f38` である。
recovery source `8decef0c3bf07cb217c144871cde2bdab807ba62b8e78de98b5b239df8fce61b` と、実組立/nativeを含む計5 sourceの固定hashを前後照合した。
fixture成功と実入力を結合したconstructor検証を区別し、後者は引き続き未実施である。

node移行の実組立265693はF/0・run_count=1となり、`$HOME/workspace/mcmc4qec/20261025-census-active-node-v13/` に新authority・policy・sourceを保存した。
`prepared.json` のSHA-256は `6e6b4b103a7f3d3c5361559bfd0faea5a3d7b8974fc0ad945d20ebd88c9b45fb`、`authority.json` は `9a543e1442bc4aea22ffef5764c8b837128aacdfa186d418d72960b7ed575769` である。
終端原本は `pipeline-submissions/census-active-node-build-v1/terminal.json`、SHA-256は `18f2bad2bea52aa8e5829e25d037106bceb3b44d117937c19342448e0fcf544a` である。
生成したauthorityの後続recoveryへの結合と実constructorの受入は、引き続き別工程として実施する。

起動前readiness helperの14 fixtureは265694でF/0・run_count=1、0.003秒で成功した。
原本stageは `pipeline-submissions/operational-census-readiness-fixtures-v1/`、acceptedは `0d52b47b24edd69cc8e4f531f52ab78b91d1c2983707bbc88b54852f4c65ad19`、終端は `831f555652f562eaad2a05dee94337fcc3effc653daa56cad02719319afbe2da` である。
実native受理を読む起動前確認はこのfixtureの後に行い、fixture成功だけで本番起動可能とは扱わない。

外側operationの実生成265696はF/0・run_count=1・wall1秒で終了した。
19 fixtureで受理したhelperを使い、元outerの7 sourceを新rootへ構築して原文との差分を再照合した。
新rootは `$HOME/workspace/mcmc4qec/20261025-census-outer-operation-v13/`、authorityは `a710d553bf803a3a6c8f4ab29268deb146e5d780773b7a06b6b0e7afaf0c5438`、acceptedは `3ad8e7f8a3ffd1413ac7d5677e3304c53f4d401d5b50ca7af539942739be0c46` である。
終端は `pipeline-submissions/operational-census-outer-materialize-v1/terminal.json`、SHA-256は `c09a42de106e3fbf8818372f71b9f75eb7d7b8486397a8f83acd320b0b4292db` である。
runtimeと元sourceを維持し、変更はcensus実行roleが専用environmentを参照する箇所だけである。
これをrecovery担当へ渡し、実設定組立とnative constructor検証は同担当が続けて実行する。

readinessの保存先が本番rootの祖先・子孫になる指定を拒否する追加検査を入れ、旧14 fixtureの原本を保持したまま新15 fixtureを265697で検証した。
265697はF/0・run_count=1で、原本stageは `pipeline-submissions/operational-census-readiness-fixtures-v2/` である。
新sourceは `254c3de9a506ba42c51201844b37a91559143b0f582d33387cfdda15d709bfdc`、acceptedは `76b6ee51ed58d751d83956469e9a90198f0e5cf8931303c1ec0b87776168549d`、終端は `55607b6cbbd6003f7753a90008dd0b3c3a0f1959ac3c79fee0bf923ebb659abe` である。
本番controllerの起動と科学処理は、この一連の受入ではまだ行っていない。
