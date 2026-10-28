# 成功候補を保持する混合manifestフロー仕様

v4実行先ではportable readerのPBS照会時刻を含む比較が失敗したため、全12条件を再計算せず、変更不要な5条件を保持する。
保持するindexは0、1、6、7、8であり、旧preparedと実ジョブ番号を変更しない。
置換するindexは2、3、4、5、9、10、11であり、明示的に修正したreader環境の新規ジョブだけを投入する。
PBS終端のjob内容はすべて検証し、照会時刻などの外側の属性だけをreaderの不変条件から除く。
科学計算、データ、選択基準、全12条件の分母は維持する。

## 制御

新しいcontrollerは12条件の実preparedを順序どおりに持ち、各workerの固有manifestを使用する。
保持する5件に投入ledgerがない場合は停止し、自動再投入しない。
保持する5件も、PBSの成功終了と元の証跡の検証前には成功結果と扱わない。
7件の置換は固定2物理ノードの容量ゲートと共有lockを通して`qsub`で投入する。
全12件が成功終了するまでmergeを開始しない。
mergeでは各workerの元のmanifest、prepared、job番号、結果を保持し、現在のmanifestへ見せかける書換えをしない。
独立計時と最終報告はmergeのseal確認後に同じクラスタ内で進める。

## 受入条件

- 保持5件と置換7件が重複なく0〜11を覆う。
- 保持したpreparedとjob番号の変更を拒否する。
- 保持ジョブのledger欠落時に`qsub`を呼ばない。
- workerごとのmanifestを使って配置、資源、terminalを確認する。
- 照会が不明のときにジョブを再投入しない。
- 途中までの計算やPBS起動成功を、数値処理の正常完了と扱わない。
- 全工程をクラスタで継続し、ローカル計算を行わない。

これまでの失敗ジョブ、未起動controller設定、単体・native受入の証跡は保存する。

## 受入記録

PBSジョブ265580で50テストが成功し、F/exit 0と空のPBS標準エラーログを確認した。
50件には、保持したジョブのledgerがない場合に実際のworker処理が投入関数へ進まない検査を含む。
PBSジョブ265585で実際の旧5件・新7件のpreparedを用いたshadow constructor確認が成功し、F/exit 0、walltime 1秒、空のPBS標準エラーログを確認した。
この確認ではcontrollerのtick、worker投入、科学計算、実controller起動を行っていない。
全12ジョブの完了、merge、独立計時、最終報告は別に検証する。
全12件の実投入ledgerと最新PBS状態の照合後に実controllerを起動し、SSH切断後の別接続で同じPID、起動時刻識別子、commandの一致と生存を確認した。
最初の巡回では12件の観測を保存し、保持index6・7のF/exit 0と元preparedに結合したterminalを回収した。
残る10件は処理中であり、worker結果の受理は後続mergeで別に検証する。
初回観測時のcontroller標準エラーとerror記録は空だった。
