# 最終成果物の再現用保存計画

本書の初期closure表とflow pinは、並列merge導入前のv5構成を対象とした履歴である。
現行の保存対象はflow設定v8・front v6・並列merge v6・tail v3/設定v8であり、[v8 snapshot仕様](reproduction_snapshot_v8_spec_2026-10-25_ja.md)と[最終成果物監査](final_deliverable_audit_2026-10-24_ja.md)を参照する。
v5のprivate snapshot保存済みという事実を、現行v8の保存完了や最終成果物の完成へ読み替えない。

2026年10月25日に、[既存監査](final_deliverable_audit_2026-10-24_ja.md)、gitignore、対象fileの追跡状態、現行flow・worker準備・merge・tailの参照契約を確認した。
ローカルで数値計算やテストを実行していない。
実行中のsource・環境・manifest・jobを変更せず、commit・pushはしていない。

## 確認した不足

`output/` と `docs/wp/data_*/` はgitignoreされ、今回のtail受入directoryと算術照合directoryについて `git ls-files` は対象を返さなかった。
source hashがreceiptにあっても、対応するsource bytesを通常cloneから取得できることにはならない。
現行flow・merge・dispatch・reader修正・tail、元の科学helper、受入テスト、実入力manifestとseed仕様の一部はignored directoryまたはクラスタ上の固定bundleにのみ存在する。
大容量raw trace・anchor・index archiveについて、原本hashと所在はあっても、第三者向けの取得方法・利用条件・保持期限が揃っていない。
追跡対象への追加や公開配布先へのアップロードは未実施である。

## 保存する最小closure

| 層 | 起点と必要内容 | 保存先と判定 |
|---|---|---|
| 現行controller | 本番flow-config、worker-preparation、dispatch policy、flow/runtime/physical gate helperとその受入 | 小規模source archiveにbytesを保存し、元source pinと公開版pinを併記する。 |
| 全12条件 | front v5の7replacementとfront v4の5retainedの別manifest・prepared・script・job来歴、reader環境、全12条件の対応 | 元の来歴を維持し、重複・欠落がない対応表を保存する。 |
| 科学定義・入力 | 符号、noise、fixed decoder prior・native設定、failure、kernel、ladder、trace/burn-in/chain、誤差法、独立seedとselection規則 | 実際のsource closureと元の入力manifestから取得し、報告文から設定を推測して再生成しない。 |
| merge・tail | merge v4、tail v2、元6driver、census・独立計時・report環境、選択結果と必要helper | source_sha256・adapter_sha256・import_originsのbytesを照合し、動的importとentrypointの追加監査を行う。 |
| 完了証拠 | accepted/selection、seed census、独立計時入力と出力、全48行、report.json/report_ja.md、terminal/submission/journal | 本番完了後の受理済みpinを根拠に追加する。fixture成功を代用しない。 |
| raw・binary | trace、anchor、zip/npy等、大容量JSON、Python/native binary | 形式・サイズ・元hash・取得条件・管理者・保持期限を別indexへ保存し、今回再hashしたかを明示する。 |

初期計画時の本番flow-config SHA-256は `7c467ff93159574d9a98dd276df8431f2787b6577e83c2a3c9d6c15613ab86b1` で、当時の保存起点の候補である。
このpinの提示は、下流のmerge・独立計時・最終報告が完成したことを意味しない。
全closureの収集は未完了であり、最終proofを追加してから最終保存範囲を判定する。

## 保存toolの境界

[`archive.py`](../../tools/reproducibility/archive.py) は明示したroot pinからJSON内のpath/hash参照を辿り、小さいtext/sourceをhash照合する。
欠落・不正pin・相反するpin・root外・relative pathの基準不明・source変更・上限超過は問題として記録する。
大型JSONとbinaryは再読込せずexternal indexにし、その内部参照を未調査と表示する。
bare hash、動的import、source中のpath literalは自動閉包に含めず、実環境のimport_origins等と照合した追加seedを必要とする。
全参照は現行実行依存・上流の歴史的証拠・外部raw/native入力に区別してreviewし、旧Windows pathを黙って無視したり、存在する別fileへhashなしで付け替えたりしない。
歴史的参照の除外には、理由と代替証拠を固定した別仕様を必要とし、元のmetadataを変更しない。

公開ZIPでは原本SHA-256と公開後SHA-256を分け、識別子置換の有無と理由を保存する。
metadata内に残す元pinは元bytesを指し、公開後の別bytesを本番で用いたと読み替えない。
公開側の内部照合はZIP全体の真正性の証明ではないため、ZIP hashとmanifest hashを独立した公開receiptに保存する。
実path・ユーザー名・ホスト名を含むprivate request・policy・inventoryは公開しない。
公開ファイルは置換後に再検査し、ZIP内の名前重複・危険な相対path・未掲載member・公開hashとedgeの不一致を拒否する。
このtoolは `execution_ready=false` と `scientific_reproduction_verified=false` を維持する。

## 任意workspaceで再利用する手順

まず公開archiveの外側hashと内部hashを検証し、新しい空のworkspaceへ展開する。
外部入力は利用条件に従って取得し、元hashを照合し、未取得を再現のblockerとして記録する。
記録したPython・依存packageを構築し、新しいnative binaryのhashを元のbinary記録と区別する。
公開path tokenをreviewして新workspaceへ対応付けるが、immutable validatorを無理に通す一括置換や、旧receiptの書換えは行わない。
新環境のimport_origins・resolved_sources・source hash・pythonpathを確定した後、reader環境、worker manifest、resource plan、flow/tail config、script、submissionの順に新しいpinを生成する。
歴史的なaccepted/PBS/job来歴を新環境の実行証拠に変換しない。
実CLIのimport origin、科学定義、入力選択、capacity、短いcanaryを新環境で受け入れてから本計算を行う。
クラスタではqsubを使い最大2物理nodeを守り、local環境には別途reviewしたlocal entrypointを用意する。
自動再配置・再pin runnerの大改修は今回未実装で、別仕様と受入が必要な提案として残す。
詳細は[tool利用手順](../../tools/reproducibility/README.md)に記録する。

## 受入状況

fixture 23件を用意し、原本・公開hash、参照漏れ、匿名化、raw index、変更検出、ZIP内部整合性を検査する。
PBS job 265593へphysical-node gateを通して1CPU・1GB・5分の上限で投入した。
23件すべて成功し、unittestは0.023秒、PBS walltimeは1秒、終了状態F・exit 0・run_count 1を確認した。
source pinの前後一致、qsub scriptとSubmit_argumentsの一致、許可された物理node上での実行も照合した。
識別子を除いた[受入receipt](reproduction_archive_fixture_acceptance_2026-10-25.json)に、原本source・request・terminal・submission・ログのhashを保存した。
receipt内の原本hashは識別子を含む非公開原本を指し、公開用receipt自体のhashではない。
これは小さいfixtureに対するtoolの受入であり、実際のsource closure収集・public archive作成・raw保存・科学計算の再現は未実施である。

その後、PBS job 265594で初回の実inventoryを収集し、5秒・exit 0で終了した。
2000 recordsのうちarchive対象722、blocked1178、external100となり、問題1179件を隠さず記録した。
問題の内訳は総byte上限1079、relative base未指定64、非canonical参照34、source symlink拒否1、file数上限1である。
33,554,406 bytesを元hash照合し、参照探索がblockedでも元bytes照合済みのmetadataを含む820 membersを非公開snapshotへ保存した。
直接指定したcurrent source参照318件中317件は照合・保存済みで、残る1件は消失ではなく、現環境が実際に使うstaging sourceのsymbolic linkだった。
34件の非canonical参照は、主としてnative bindingのvenv別名がproduction環境の実体へ解決することによる。
この初回collectorは条件を満たさない最初の参照でそのJSONの後続探索を止めるため、未調査の参照が残っている。
[`reproduction_inventory_partial_2026-10-25.json`](reproduction_inventory_partial_2026-10-25.json) に部分収集の証拠と限界を保存した。
初回の上限を単純に増やす方針にはせず、[明示scopeの次版仕様案](reproduction_snapshot_v2_spec_2026-10-25_ja.md)でsource・現行metadata・歴史的external参照を分ける。
次版は25fixtureの受入後に実行し、job 265599でflow v5に固定したsource1031参照とcurrent metadata75文書のprivate snapshotを保存した。
保存した原本artifactのhashは[次版receipt](reproduction_snapshot_v2_acceptance_2026-10-25.json)にあり、公開用ZIP・現行flow設定v8のsnapshot・final proofの追加・科学的再現は別の残工程である。
