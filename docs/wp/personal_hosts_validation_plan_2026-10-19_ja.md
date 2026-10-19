# 個人計算機を使う追加検証

ユーザーからlabo PCとDGX SparkへSSH接続して並列計算を実行し、利用可能な個人機の資源を使い切ってよいとの指示を受けた。
既存SSH設定の`dgx-ts`と`labo-ts`で接続を確認した。
DGXはaarch64 Linux・20論理CPU・約128GB、LaboPCはWindows 11・i9-12900・24論理CPU・64GBだった。
確認時点の負荷は低く、LaboPCのPythonプロセスはなかった。

公開準備を優先し、最初は固定済み915ファイルの公開候補とwheelを隔離ディレクトリへ転送し、各機の隔離venvでinstalled-wheelの全optionalテストを並列実行する。
LaboPCでは既存のuv管理Python 3.11.17を絶対パスで使い、DGXでは利用可能なPython 3.12.3を使う。
Python 3.12はパッケージと既存CIの対応対象であり、別環境として記録する。
グローバルPython環境、既存プロジェクト、RIMCは変更しない。
ZIPとwheelの固定SHA256を転送前後に照合し、ZIP内の絶対パス・親ディレクトリ参照・symlinkを拒否する。
sourceのhash一覧、wheel、Python、依存package、OS・architecture・CPU数、コマンド、終了コード、ログを保存する。

DGXは20 worker、LaboPCは24 workerを上限とし、各workerのBLAS等は1 threadに固定する。
全suiteは300秒の観測上限を設け、時間超過は失敗として記録し、当該runnerが起動したプロセス群だけを停止する。
テスト集合を減らして成功扱いにせず、skipと失敗を明記する。
既存の5分制約で完了しない場合は原因を調べる。

次に同じ固定decoder設定のplatform fixtureを照合し、ARM・Windows・クラスタLinuxでの差を検証する。
異なる実行環境のnative fingerprintを同一と扱わず、既存の事前固定クラスタcohortへ無条件に混ぜない。
継続する数値計算は環境別のreferenceとseed割当を固定してから実行する。
個人機の使用はクラスタのqsub・最大2要求nodeを置き換えるものではない。
今回の機能テストをBARのbias・被覆・計算効率の校正完了とは扱わない。
