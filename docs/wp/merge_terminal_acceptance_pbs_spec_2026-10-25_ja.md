# merge 終端受理を PBS 内へ隔離する契約

merge 結果と selection は大きな JSON になるため、常駐 controller から元の `execution_runner.accept_terminal` を直接呼ばない。
元関数と科学検証を変更せず、別の有限 PBS ジョブで一度だけ実行する。
受理ジョブの PBS ID と元 merge ジョブの PBS ID は分離し、元結果の由来を書き換えない。

## 実行境界

controller は 4 MiB 以下に制限した prepared・request・環境・ledger・accepted と receipt だけを読み、巨大な result・selection は parse も hash もしない。
元関数は PBS 内で canonical な `terminal.json`・`selection.json`・`accepted.json` を初回生成する。
既存ファイルがある場合は上書きせず停止し、部分生成後の失敗も保存して自動再試行しない。
専用の排他的 claim を merge root に一度作成し、同じ元 merge に対する wrapper の二重実行を防ぐ。
既存 controller との競合も、元関数の exclusive create と wrapper の事前検査により成功扱いにしない。

受理用 prepared は元 merge prepared・元 runner・環境・共有物理ノード policy・wrapper source を pin する。
元の成功状態を確認した上で、共有ロックと既存物理ノード上限判定を通して `qsub` する。
PBS 内から子ジョブを投入しない。
資源予算は 1 CPU・96 GiB・4 時間を明示する。
これは実測済みの必要量や終了予測ではなく、巨大 JSON の parse・copy に備えた保守的な予算であり、実結果サイズとピークメモリは未実測である。

## 小さな完了記録

PBS 内で元の受理を完了した後、元の accepted と各出力の hash・stat identity を小さな完了記録へ保存する。
controller は受理ジョブの F0、単一の投入・script・source・prepared identity、完了記録の bounded read を検証する。
元の accepted は bounded read と hash 照合で完了記録の値との一致を確認する。
巨大 artifact は PBS 内で確認した hash を引き継ぎ、controller では stat identity の不変性だけを確認する。
これを controller による巨大ファイルの独立再hashとは表現しない。
成功前、失敗、未知のジョブ状態、競合、partial output から下流を開始しない。
この変更は全条件の科学的受理を省略するものではなく、元の受理処理の実行場所を移すものである。

## 受入結果

wrapper の実装と独立レビューを完了し、PBS ジョブ 265621 で 27 件の小さな fixture テストが成功した。
ジョブは `F`・終了コード 0、walltime は 1 秒、テスト本体は 0.147 秒だった。
fixture は元 API を表す小さな pin 済み runner の呼出、canonical 出力、完了記録、controller による採用までを通した。
巨大 result・selection の controller-side open を禁止する trap、F0 でも完了記録が欠ける場合の拒否、元 merge ID と受理 ID の分離、部分失敗の保存、再投入防止、実ホスト・資源・intent の照合を含む。
本番の巨大 result に対する `accept_terminal` はまだ実行しておらず、そのピークメモリと処理時間は未実測である。
同じ wrapper の実 CLI と native bootstrap を使う追加の PBS preflight を、本番投入前に行う。
private 実装は `output/merge_terminal_acceptance_pbs_v1/` にある。

ジョブ 265623 では同じ wrapper の実 CLI を `-i --help` で開始し、その import 起点を保って元 runner・runtime・evidence と現在の環境を読み込み、native bootstrap と engine の manifest 検証を行った。
265623 は 4 秒で `F`・終了コード 0 となった。
過去に問題となった CLI ディレクトリによる import の競合は、この検証では検出されなかった。
実際の merge prepared はまだ生成されていないため、この前倒し検証は実 prepared に対する受入ではない。
仮の本番 prepared は作成せず、実 prepared ができた後の preflight を引き続き必要とする。
元の `accept_terminal` と巨大 result・selection の読み出しは実行していない。
識別子を除去した小さな証跡は [receipt.json](data/merge_terminal_acceptance_20261025/receipt.json) に保存した。
記録する SHA-256 は識別子除去前の private 原本を指し、公開用要約自体の hash ではない。

## v2 の追加契約

実 merge prepared ができた後の検査を人手の待機条件として残さないため、v2 では同じ受理 PBS ジョブ内で actual prepared の native preflight を先に行う。
prepared・元 runner・環境・manifest・source pin・PBS ID を結び付けた小さな preflight 記録を保存してから、排他的 claim と元 `accept_terminal` へ進む。
preflight が失敗した場合は claim・元終端記録・selection・accepted を生成せず、本受理を呼ばなかったことをエラー記録へ明記する。
preflight 自体は result・selection を開かず、元の initial・bootstrap・manifest validator を使用する。
controller は F0 だけでなく、同じ prepared と受理 PBS ID を持つ preflight 記録を照合してから採用する。
v1 とその受入証跡を保持し、この追加は別の `output/merge_terminal_acceptance_pbs_v2/` に実装する。
この節を追加した時点では v2 の PBS 受入は未実施である。

その後、v2 の 31 件の fixture はジョブ 265628 で成功し、`F`・終了コード 0、walltime 1 秒、テスト本体 0.184 秒だった。
v2 の同じ実 CLI による前倒し native 検証もジョブ 265629 で成功し、`F`・終了コード 0、walltime 4 秒だった。
この時点でも実 merge prepared は未生成であり、それに対する検証を実施済みとは扱わない。
実 prepared の検証は、生成後に同じ受理 PBS ジョブ内で自動実行する実装と fixture を確認した段階である。
v2 の識別子除去済み証跡は [receipt_v2.json](data/merge_terminal_acceptance_20261025/receipt_v2.json) に保存した。
