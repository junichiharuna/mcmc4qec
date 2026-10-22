# 残る5条件のnative parity reference準備

## 範囲

C1T1・C1T2・C3T0・C3T1・C3T2について、既存のnative_reference.pyとreference_qsub.pyを変更せず、条件ごとのconfigとPBS scriptを準備する。
対象groupは事前固定したcase・target_index・kernel 0・initialization 0・replicate 0で、全88設定を元native環境で処理する。
このreferenceは両PCの保存値比較用であり、独立MCのreferenceや全768群の科学的受理とは区別する。
準備ではqsubも数値計算も行わず、元生成plan・metadata・113 sourceと既存controlをhashで固定する。
全条件の入力生成は未完了であり、config準備をraw traceの存在・完了・検証と扱わない。

## 資源

受理済みC1T0 native referenceの保存recordは全88設定でwall_seconds 978.7308733696118、peak_rss_mb 715.29296875だった。
record・marker・export manifestは回収済みZIPのhashから照合し、元job265360の実qstat正常終端も再確認する。
対象条件は同じtile288・8 chains・18,000 stepsで、rung数は10・13・15と異なる。
初期walltimeは保存recordの4倍にrung数比を掛け、読み込み・export用30分を加えて30分単位へ切り上げ、既存referenceと同じ4時間を下限にする。
memoryは保存peak RSSの4倍と8 GiBを加え、既存と同じ32 GiBを下限にする。
これは保守的な初期要求の決め方であり、別noise/targetの計算時間・必要memoryや同精度到達時間を保証しない。
単一referenceは1ノード・1 CPUで実行し、実投入時には既存controllerのqsub・共有lock・最大2要求ノードの制限を使う。

## 実行順

現在のC0T2最終集計、C1T0復旧監査とC1T1回収・監査の担当driverを維持する。
各referenceの実投入前に対象groupのanchor/trace生成と実PBS正常終端を確認し、担当driverと空き枠を調整する。
referenceの正常終端・全artifact回収と両PCでの88設定parityが通るまで、その条件のPC本処理を始めない。
今回のprepare/preflightはmetadataとscriptの検査であり、実行結果の校正ではない。

## 準備結果

5条件の実元metadataと既存controlを照合し、既存q.prepare・q.submit(execute=False)で全configとscriptを準備した。
全条件の要求は1ノード・1 CPU・32 GB・4時間となった。
元C1T0 referenceのjob265360は実qstatでF・Exit_status 0・run_count 1と同じscript/resourceを確認した。
113科学sourceと保存済みrecord/marker・元ZIP・回収記録のhashを照合し、既存worker/controllerと元configは変更していない。
新しい数値試験やqsubは行っておらず、各条件のraw入力生成・存在・整合性の確認は未実施である。

| 条件 | 準備済みjob root | config SHA-256 |
|---|---|---|
| C1T1 | `/home/user/workspace/mcmc4qec/20261020-native-reference-c1t1-v1` | `6b395539e2ada002edf255d600246768f7ccc5719653009f23a2ee8edac051cc` |
| C1T2 | `/home/user/workspace/mcmc4qec/20261020-native-reference-c1t2-v1` | `7b5f67d4e5f626116ccb485a77a5c4c06bf4c33c32cf598b2b37683a48f21fdb` |
| C3T0 | `/home/user/workspace/mcmc4qec/20261020-native-reference-c3t0-v1` | `33a16fb1b25a3e8bf58d275136dbfc571365a9f44dd3013616e6f86f179d1510` |
| C3T1 | `/home/user/workspace/mcmc4qec/20261020-native-reference-c3t1-v1` | `b621ee1c191af76b2bef5de87ca604b15e16c4d6559afa652938d4c25c7183de` |
| C3T2 | `/home/user/workspace/mcmc4qec/20261020-native-reference-c3t2-v1` | `998f502134b24a41c7101bb49fe0a6b5b3bdfa485ffc1e4c3ef3281ac1e439ad` |

実controllerは `/home/user/workspace/mcmc4qec/20261020-native-reference-controls-v1/output/portable_bar_native_reference_qsub_v1/reference_qsub.py`、SHA-256 `0d09cba776f68086ede0af9c33316a9a678bc6345bf16a4969d201cda3e1f5ad` である。
実行入口は元bundleの `venv/bin/python` とし、既存controllerのsubmit/completeと回収処理を使う。
準備の [accepted.json](data_tile_validation_2026-10-17/planned_native_reference_preparation_v1/accepted.json) はSHA-256 `29659148155787ebdae95452c1b661cb1cf97b5dccac75207cd50615d6d53966` である。
source・資源根拠・実config/script・事前検査の記録は [保存manifest](data_tile_validation_2026-10-17/planned_next_conditions_readiness_20261020_v1/manifest.json) に保存する。
