# sourceとmetadataを分ける保存scopeの小仕様案

初回inventoryの不足を隠さず保持したまま、歴史的metadataを無制限に再帰探索しない保存方式を追加する案である。
受入済み `tools/reproducibility/archive.py`、実行中のsource、元metadata、PBS証拠を変更しない。
次版を独立helperとして実装し、PBS job 265596で25件のfixtureを受け入れた。
実snapshotの作成と公開版作成は、このfixture受入とは別に判定する。

## authorityとscope

本番flow-configのSHA-256は `7c467ff93159574d9a98dd276df8431f2787b6577e83c2a3c9d6c15613ab86b1` である。
追加の封印authorityは `$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/output/cluster_postprocess_pipeline_v1/controller-envelope.json`、SHA-256 `25e2464484c67f9842fb9a68861bf70f85203e6db87e537491f13d20251c3b6a`、183371 bytesである。
このenvelopeの1223 entriesはPython729、JSON473、JSONL13、Markdown3、binary1、log4であり、全1223件をPython sourceと呼ばない。

| 区分 | 明示scope | 処理 |
|---|---|---|
| source bytes | 現行helper/environmentのsource_sha256等から固定した318参照と、envelope中のPython729参照 | 重複31を除いた1016参照を出発点に、pin一致・サイズ・source別名を検査してbytesを保存する。 |
| current metadata | flow、prepared-receipt、現行・retained manifest、resource-plan、policy、全12prepared、reader/parent/report環境、tail config/basis、immutable submission・完了済みterminal | 明示した有限listだけを保存し、全JSON参照をedge indexへ記録する。 |
| historical evidence | 旧prep・旧acceptance・旧manifest、envelope中のJSON/JSONL/log等でcurrent list外のもの | 元の宣言path・hash・役割・未収集理由をexternal indexへ残し、再帰収集を義務としない。 |
| raw/native | trace・anchor・binary・Python実行file・native moduleとそのlink | link名・resolved target・宣言hash・サイズを保存し、原本の再hashは行わない。 |
| future evidence | 全12merge、独立計時、最終reportの未完成proof | 未取得として明示し、完成後の別versionで追加する。 |

1016件は参照pathの和集合であり、物理fileの一意数や全動的importを閉じた証明ではない。
実requestを作る際には、実controllerの自己pin、workerの実runtime/evidence/values、dispatch capacity、merge validatorのbefore/after source参照など、元の1016件にない実依存15件を出典付きで追加し、1031参照になった。
1016という出発点の分母を書き換えず、補足15件を別listとして保存する。
import_origins・resolved_sourcesにある実際のimport先がsource tableまたはnative/external tableに対応することを別に照合する。
envelopeのcurrent外entryも全件を表に残し、選択的に存在自体を消さない。
宣言pinが同じpathについて相反する場合は停止し、どちらか一方を選ばない。

## symbolic linkの扱い

source linkは元の参照path、受入済み環境のresolved_sourcesが指定する実体path、期待SHA-256、実測resolve結果を対応付ける。
既存のstaging source linkはこの方式で保存し、current依存から落とさない。
実体が許可root外、非file、循環、想定外target、hash不一致ならsource保存は不受理とする。
実体bytesを保存しても、元pathを実体pathで書き換えた元receiptを作らず、別名対応表として残す。
Python/nativeのlinkはsource linkと別にexternalとして記録し、今回はbinary bytesを読まずhash検証済みとも書かない。

## traversal boundaryと不足の記録

各metadataは元bytesと元hashを保存し、その内容を改変して参照探索を通さない。
探索は明示scope内の各documentに対して一段だけ行い、current tableに含まれるedge以外は分類付きexternal edgeとする。
各edgeに元document pin、JSON pointer、宣言target文字列、宣言hash、分類、収集状態、理由、分かる範囲の所在を保存する。
relative targetはdocumentごとにreviewしたbaseがある場合だけ解決し、未知のbaseをcwdやdirectory名から推測しない。
不正pinや解決不能edgeが1件あっても、そのdocumentの他のedgeの記録を中断しない。
bare hashや動的pathなど自動参照として解釈できない箇所は、別の未分類一覧またはmanual review条件として残す。
source bytesの保存完了、明示current metadataの保存完了、historical closure、raw取得、科学的再現を別々に判定する。
scope内bytesが揃った場合でも、公開archive単体でexact replayできるとは扱わない。

## 必要な受入

元pin一致・相反pin拒否・元bytes不変更・source hash照合・期待targetに一致するsource link・link循環/別target/root外拒否をfixtureで検証する。
raw/nativeの内容を開こうとすると失敗するfixtureを用い、statと宣言hashの記録だけで終わることを確認する。
current scope外edgeが全件indexへ残ること、先頭に不正pinがあっても後続edgeを失わないこと、relative base未指定を明示することを検証する。
envelope全entryの分母保持、1016参照の出発点の一致、current metadataの過不足、source/environmentの別名対応を実metadataから検証する。
公開版の識別子除去と元/public hash区別は既存toolの受入を維持し、新たな形式を使う部分には追加受入を行う。
受入と実収集はqsub・physical-node gate・最大2nodeを使い、ローカルで数値処理しない。

## 実施記録

PBS job 265596は25 passed・0.023秒・walltime 1秒・F0で、source/native open禁止、同bytes別targetへのsource link変更、不正edgeの後続保持、scopeを跨いだ相反pinの拒否を確認した。
受入済みlibraryは `tools/reproducibility/snapshot_v2.py`、SHA-256 `053265218e64768d48e13871b47d9c6bb33bb659557122344b4c6b3300cdf35a` である。
最初の実収集job 265597は、封印済みsource `prepare_remote_v1.py` のサイズ2613873 bytesが2MiB/fileを超えたため、2秒・F1で安全に停止した。
有限scopeはsource1031件・metadata75件で、statによる合計はsource14475969 bytes・metadata4675602 bytesだった。
次のfresh stageではfile上限だけを4MiBへ変更し、合計32MiBとscopeを維持してjob 265599を投入した。
job 265599は5秒・F0で完了し、source1031参照・current metadata75文書・envelope1223参照を保存した。
one-hop edgeは19692件で、explicit scope内5876件とexternal13816件を区別して残した。
nativeとenvelope由来の項目も含むexternal indexは14420 recordsで、原本contentの再hashはしていない。
source/metadataの原本文字bytesは合計19151571で、private-source.zipは4794453 bytes、private-metadata.zipは772213 bytesだった。
source aliasは1件で、元path・受入済みresolved target・期待hashの前後一致を確認した。
生成されたZIP・index・member表のhashをreceiptと再照合し、[公開用の小さい証拠](reproduction_snapshot_v2_acceptance_2026-10-25.json)と[25fixtureのログ](reproduction_snapshot_v2_fixture_2026-10-25.txt)を保存した。
実収集に使用したcollector sourceは [`collect_tile_v5_snapshot.py`](../../tools/reproducibility/collect_tile_v5_snapshot.py) に同一bytesで保存し、SHA-256は `c8d20d83a94c21c7425ea1bc0bc5bd604667316de9105abe0607e09ee7f5048d` である。
元のlibrary、初回collector、失敗証拠、実行中の科学sourceは変更していない。
このsnapshotは固定したflow v5の資料であり、後続の復旧flow v6の最新sourceを保存済みとは扱わない。
全歴史依存のclosure、未取得final proof、rawの永続保存、公開ZIPの匿名化と配布、科学的再現は完了扱いにしない。
