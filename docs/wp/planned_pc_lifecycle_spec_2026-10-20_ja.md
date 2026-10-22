# 残る条件のPC配置・実行・回収

対象は固定済みC1T1/C1T2/C3T0/C3T1/C3T2とする。
既存のC1T0用operator adapterから条件名と保存先を明示的に切り替える派生版を作り、数値runner・parity・stage・collectionの共通実装は変更しない。
各操作は固定manifestで認証した全群割当てを読み、host・batchと条件座標を照合する。
配置は新しいexport adapterのprepared inputを読み、元source・archive・task markerを再検査してから新規incoming directoryへコピーする。
初回stageは当該条件の実native referenceとPC parityの受理を必要とし、後続stageは同じ条件の直前batchの回収・正常終端を要求する。
launchとcollectでもstage受理記録の条件を明示して照合する。
実行中processの検出、runtime固定、共有lock、一度限りの保存先、失敗時の証跡保持を維持する。
この変更だけではnative referenceの投入・回収、初回parityの条件間引継ぎ、自動serial driverを完成したとは扱わない。
受入では5条件×2hostの固定割当て、未知条件、負または範囲外batch、条件取り違えを検査し、派生adapterのremote処理が既存版と一致することを別途確認する。
本番配置・launchは前段の実成果物が揃ってから行う。

## 2026-10-20の実施結果

`output/planned_pc_lifecycle_v1/` に `preposition.py`、`stage_first.py`、`stage_later.py`、`launch_first.py`、`launch_later.py`、`collect.py` を作成した。
既存6 adapterのhashを固定し、条件名・入力経路・選択条件の追加検査を行う派生手順と全置換記録を `derive.py`・`derivation.json` に保存した。
数値runner・stage・collectionの共通sourceと、各adapterのremote処理本文は変更していない。
固定5条件×2hostの割当て、範囲外batch、条件の取り違えによる副作用前の停止、remote処理本文の一致を検査し、Windows32件・0.83秒、Linux32件・0.27秒で成功した。
6 adapterの `--help` を両環境で実行し、importとCLIの起動も確認した。
試験用Linux配置は `/home/user/workspace/mcmc4qec/20261020-planned-pc-lifecycle-tests-v1` であり、本番PCへの配置ではない。
[source・ログ・固定割当てを含む44ファイルのmanifest](data_tile_validation_2026-10-17/planned_pc_lifecycle_acceptance_v1/manifest.json)のSHA-256は `597c13d3e806fda56374c0c596f80ae60bdc5eb27897e7c8d28da03e07e12d94` である。
この受入に当該5条件の実転送・実parity・数値起動・本番回収は含まれない。

初回の操作入口は、前段の実native reference回収と条件間parityの引継ぎを完了した後に以下を使用する。
native referenceの回収と初回parityの新条件対応はまだ未実装であり、現時点でこの列を通し実行しない。
各操作は別プロセスで一度だけ呼び、失敗またはSSH応答不明時は実PIDと保存成果物を確認し、自動再実行しない。

```powershell
& 'A:/dev/mcmc4qec/.venv-experimental-optional/Scripts/python.exe' -B output/planned_pc_lifecycle_v1/preposition.py dgx 0 --condition c1t1
# 当該条件のnative referenceと、このhostのparity受理が必要。
& 'A:/dev/mcmc4qec/.venv-experimental-optional/Scripts/python.exe' -B output/planned_pc_lifecycle_v1/stage_first.py dgx --condition c1t1
& 'A:/dev/mcmc4qec/.venv-experimental-optional/Scripts/python.exe' -B output/planned_pc_lifecycle_v1/launch_first.py dgx --condition c1t1
& 'A:/dev/mcmc4qec/.venv-experimental-optional/Scripts/python.exe' -B output/planned_pc_lifecycle_v1/collect.py dgx 0 --condition c1t1
```

後続batchでは入力export・prepositionの後に `stage_later.py HOST SEQUENCE --condition CONDITION` と `launch_later.py HOST SEQUENCE --condition CONDITION` を使う。
collectは初回と同じ入口でsequenceを明示する。
当該5条件のserial driverへの接続も未実施である。
