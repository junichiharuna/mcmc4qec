# 低ノイズtrace監査の資源外挿

capacityは完成productionの最初2 replicate、8 groupを8 workerで監査した結果だけを利用する。
fullは同じproduction・source・native入力・完成sampling証拠の768 groupであり、purpose・replicate数・worker数以外の違いを許可しない。
監査failed・context_error・input_changes・欠落groupを含むcapacityは拒否する。
sampling failedを含む監査は科学的には分母に保持すべきだが、再復号を省略して所要時間の下界となり得るため、full要求の資源profileとしては拒否する。

最大worker RSSをM MiBとして、worker数をmin(96,floor((340−8)×1024/(1.5M)))で選ぶ。
要求memoryはceil(1.5×workers×M/1024+8) GiB、最低32 GiBとする。
1 workerも収まらない場合は拒否する。
capacity最大group時間をT、group処理後の全入力再hash等を含むphase時間をPとする。
予測時間はT×ceil(768/workers)+96×max(P−T,0)とする。
後半はcapacityの8 groupからfullの768 groupへphase余剰時間を保守的に外挿する項である。
要求walltimeは予測の2倍に600秒を加え、1800秒単位に切り上げる。
24時間または340 GiBを超える場合は拒否し、partition設計を別工程に残す。
CPU総量は768×最大group CPU時間を別に記録し、経過時間と混同しない。
96 workerの同時I/O競合はcapacityの8 workerでは未測定であり、2倍係数は完了保証ではない。

純粋関数resource_planはfull_planのworker数を外挿式に使わず、選択したworker数を返す。
呼出側は返却worker数で新規full planを事前作成し、submitterが一致を確認する。
初回capacity_resourcesは8 worker・1ノード・96 CPU・340 GiB・24時間という未測定上限を返す。

measured_capacity(root,source,full_plan)はrunner.read_planを再利用し、native probe・PBS intent・native証跡・summary hashを結合する。
全measurementとaudit artifactのmarker・identity・JSON/NPZ hashを検証し、全予定task・再復号checkpoint数・失敗数・raw reduced record検査済み状態を確認する。
元traceの全入力hashを再照合してから資源値を返す。
このreaderはsource traceの数値監査を繰り返す関数ではなく、固定sourceで実施された監査証拠の再検証である。

prepare_full(root,source,capacity_root)はworker数1の仮full planをメモリ内で作り、measured_capacityを通して選択worker数を得る。
capacityが不適格なら新規rootを作らない。
最初の外挿はworker選択だけに使い、選択worker数のfull planを再構成してmeasured_capacityを再実行する。
最終resourceのfull_manifestと保存full planのdigest、および両worker数の一致を確認して返す。
固定sourceとcapacity summaryを保存直前にも照合し、選択worker数でrunner.prepareを呼んで新しいfull manifestだけを作成する。
既存full manifestのworker数を書き換えず、source変化や書込み失敗で部分rootが残った場合も自動再利用・削除を行わない。
CLIは`python cluster_scripts/tile_low_noise_trace_audit_resources.py plan-full --root NEW_ROOT --source-root SOURCE --capacity-root CAPACITY`とし、manifest digestと選択資源を表示する。
