# 全12条件の並列復旧フロー仕様

旧worker 1が失敗終了したため、成功した旧workerを保持するv1案は採用しない。
旧ジョブと失敗証跡を保存したまま、新規12個の単一条件workerを固定2物理ノードへ6個ずつ割り当てる。
入力データと科学計算の定義を維持し、欠落した提出証跡の参照を、元のledger、script、PBS終端記録に照合した上で明示的に補う。
source、環境、提出証跡参照の許可された差分は版付きmerge policyで検証する。

## 実行制御

controllerは12個すべてのprepared入力を固定し、`qsub`のintent、応答、ledgerが一致するジョブだけを引き継ぐ。
ジョブ数を2に制限せず、固定2物理ノード、各96コアの資源制御に従う。
PBS照会の一時的失敗は不明として再照会し、自動再投入の根拠にしない。
12個すべてのF/exit 0を確認するまでmergeを投入しない。
mergeは他の所有者ジョブがない状態で単一ノードへ一度だけ投入する。
ジョブとcontrollerはクラスタで継続し、ローカルPCの接続に依存しない。
停止したcontrollerを再開するときは実ジョブとjournalの照合を必要とし、未確認の再投入は行わない。

## 後続工程

各workerの元のprepared、index、terminal、valuesを版付きmergeへ渡し、12条件・24選択行の欠落や重複を拒否する。
mergeのPBS終了と科学的selectionのsealを確認してから、版付きtail adapterで独立計時のseed census、計時、最終報告を進める。
JSONと日本語Markdownの最終報告を保存後に内容のSHA-256を照合する。
独立referenceのない領域では設定間整合性を精度・被覆の保証にしない。

## 受入条件

- 12個の新workerのindexを0〜11に固定する。
- 過去の失敗ジョブを成功した統合入力として扱わない。
- 既存投入を引き継ぐ場合もintent、qsub応答、ledger、prepared、scriptの一致を必須とする。
- 不明、pending、成功終了、失敗終了を区別する。
- workerの未完了中にmergeを作らない。
- 独立計時と報告の検証前に全工程の完了を宣言しない。
- ローカルではテストや計算ジョブを行わず、受入テストもPBSを使用する。

v1のコードと仕様は不採用となった設計の記録として保持する。

## 受入記録

PBSジョブ265531で制御とdetached launcherの30テストが成功し、F/exit 0を確認した。
v2実行先の全workerがimport origin照合で失敗したため、helperの配置を修正したv3実行先のprepared入力を採用する。
controllerのソースは265531で検証したものを維持する。
PBSジョブ265554で、v3の実際の12個のprepared入力、親環境、merge、tailの固定設定を読み込み、controllerの初期化と固定ファイル照合が成功した。
265554のF/exit 0と空の標準エラーログを確認した。
この受入は独立したshadow journalを使い、productionのcontroller、worker投入、merge、tailを実行していない。
実ジョブの完了、merge結果、独立計時と最終報告の検証は別に必要である。
