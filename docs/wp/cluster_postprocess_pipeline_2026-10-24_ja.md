# 低ノイズ後処理のクラスタ移設記録

2026-10-24 10:39 JST時点で、残る後処理をクラスタだけで継続するcontrollerを配置・起動した。
このPCからの転送は完了し、計算・待受のためにPCを起動し続ける必要はなくなった。
既存の科学設定・seed・failure定義・分母・受入条件は維持した。
移設の接続・起動確認と、全工程の完走・科学的結論の検証は区別する。

## 接続した工程

| 工程 | 実行方法と状態 |
|---|---|
| 全38バッチの索引 | qsub `265505.node-PRISM`、1ノード8CPU32GB、10:42:56 JSTに正常終了、25分10秒 |
| 全入力のhash照合・最終reader用配置 | qsub `265506.node-PRISM`、1ノード1CPU32GB、3分55秒で正常終了、receipt/context hash照合済み |
| C3T2条件別最終集約 | source135件・metadata383件の準備検証後、qsub `265507.node-PRISM`が11:02:46 JSTに実行開始、1ノード1CPU32GB |
| 保存値の算術照合・12番目の候補metadata | 新しいPBS stageから既存の2処理を実行、1ノード2CPU32GB |
| 全12条件比較 | 全12候補と実測資源規則を再検証し、分割worker・mergeを元のflowからqsub |
| 独立seed census・独立計時 | 既存の6段階driverの前半を順に接続、必要な計算をqsub |
| 日本語最終報告 | 既存report jobをqsubし、JSON・日本語報告の実体とhashを確認してcontroller完了を記録 |

軽い待受・metadata準備・PBS照会はクラスタ上の独立した制御プロセスで行う。
重い処理はPBS allocation内で行い、共有lockと待機・保留を含む要求ノード数の上限2を維持する。
全12条件の比較入力が揃う前に部分集合で正式比較へ進まない。
独立計時対象が事前規則でゼロとなる場合も、既存の対象なし記録と全method行を保持する。
失敗したreport jobを最終報告成功と判定せず、`report_completed`と回収した2ファイルのhashを要求する。
名目被覆やpopulation RMSEの保証はこの運用確認から導かない。

## 確認済み範囲

Windowsでtransport・パス移設・候補census・resource failure・制御停止・子プロセス継承を検査した。
最終版のクラスタ受入は13テスト成功だった。
controllerのsource・入力1,223件のhashをクラスタ上で照合した。
6本の後段driverを実環境でimportし、固定metadata/sourceのpinと未実行の保存先を確認した。
final execution・downstream factoryの既存source検証、算術照合と候補準備の新保存先への接続も確認した。
本番全工程の端から端までの実行確認は、計算が未完了のため未実施である。

ローカル待受10本はPID・開始時刻・commandを照合し、journalに投入や後処理の実行記録がないことを確認して停止した。
旧journal・入力・解析結果は削除していない。
残るWindows Python2本はarxiv MCP serverであり、mcmc4qecの計算・待受Pythonは残っていないことを確認した。
クラスタcontrollerの最終起動PIDは4045000で、別SSH接続からcommand一致・生存・親PID1を確認した。
最初の起動は親ディレクトリ未作成でプロセス生成前に失敗し、未起動を照合してから修正した。
最初に起動した待受は後続mutation前に停止・保存し、失敗した前段と最終報告の判定を追加した最終版へ置き換えた。
これらで索引・配置のPBSジョブは再投入していない。

## 保存先と再起動後の確認

実装・source envelope・受入結果・停止と起動の証跡は`output/cluster_postprocess_pipeline_v1/`に保存した。
クラスタ側にも同じsource packageとcontroller envelopeがあり、後続の正常進行にこのPCのファイルは不要である。
運用パスを含むため、このディレクトリをそのまま公開配布物へ追加しない。
Python 3.11の絶対パスで次を実行すると、読取り専用でcontrollerと既存ジョブを照合できる。

```powershell
& "$env:USERPROFILE/AppData/Local/Programs/Python/Python311/python.exe" -B output/cluster_postprocess_pipeline_v1/observe_controller.py
```

`--compact`を付けると全証跡の保存を維持したまま、表示を段階・実プロセス・既存ジョブへ絞る。
投入応答の保存前に実ジョブが存在する場合も見落とさないよう、投入journalに加えて所有者の現在のPBSジョブ一覧を照会する。
`final_progress`にはC3T2最終集約の実行・完了・失敗記録、結果ファイルの有無とサイズ、readerのstdout・stderrの末尾各4 KiBも表示する。
今回確認した実行記録とreaderログには途中処理件数がなく、ログが空であることを停止・成功・進捗率の根拠にはしない。

クラスタ内の起点は`controller-launched.json`のcommandに記録され、状態はその起点の`pipeline-state/`に保存される。
`pipeline-state/controller/`の段階別開始・完了と`error.json`、各段階のstdout・stderrを確認する。
全条件比較flowは専用の`execution/`、計時と報告はクラスタへ移設したdataディレクトリに元の形式の記録を保存する。
controllerの`completed.json`は最終報告の成功・回収・hash一致まで確認した後にのみ作る。
通信timeoutやcontroller停止だけを理由に投入scriptを再実行しない。
失敗時は同じジョブID・投入intent・PBS終端・既存出力を照合し、既存の実行を保存してから復旧方法を決める。
このPC上の旧待受10本と、以前停止した索引・後続5本・到達不能な通常経路6本は再起動しない。
