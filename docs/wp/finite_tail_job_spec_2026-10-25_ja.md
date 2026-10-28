# 有限 tail PBS envelope

実装は新 `output/finite_tail_job_v1/job.py` とし、既存 wrapper、科学 source、環境、実行中の job を変更しない。
prepare / submit / observe は軽量 controller の処理であり、operation.perform は PBS worker 内だけで実行する。
全 JSON / source / payload / receipt の読取と出力を 4 MiB に制限する。
巨大 artifact の読取と hash は PBS 内に限定し、observe は保存した pin と stat fingerprint を照合する。
stat の一致を内容 hash の再検証とは呼ばない。

## 入力と source

`prepare(payload_pin, *, operation_pin, source_pins, policy_pin, directory, resource)` は prepared pin を返す。
payload の `runtime` は厳密な `{python_path, pythonpath, cwd}` とする。
Python 実体は outer で読込・hash せず、実行時の絶対 Python path と PYTHONPATH を確認し、native の詳細検証は operation の元 bootstrap に委譲する。
`source_pins` は名前から小 source pin への辞書で、auxiliary / dispatcher / capacity は accepted helper の hash に固定する。
capacity pin は共有 physical policy の pin と一致させる。
operation、payload、policy、全 source、wrapper 自身を実行前後で照合する。
script は select と walltime を順番通り一度だけ指定し、許可された二物理ノードの一つ、1〜96 CPU、1〜340 GiB、24時間以内とする。
prepare は別の canonical 新規ディレクトリを作成し、既存 prepared の完全一致時だけ読取による再利用を認める。

## 投入と実 PBS binding

submit は accepted `physical_aux_submission_v1` を呼び、共有 physical gate と既存 lock の契約をそのまま用いる。
PBS 内から submit を呼ぶことを拒否し、親 job が子 job の資源を占有したまま投入しない。
既存 ledger は intent / response / script / policy / resource と結び付けて採用する。
intent または response だけがある曖昧状態では再投入しない。
worker は actual PBS job ID、所有者、Submit_arguments、select / walltime、CPU / memory / node数、単一 exec_vnode、run_count=1、exec_host と実 hostname を検査する。
開始・終了時点の actual qstat を保存し、処理中は R のままであることを要求する。
`parent_binding` は厳密な `{job_id, owner, script, resource:{select,walltime}, hostname}` とし、実観測から作る。
script は原本 script の pin である。
context には parent_binding、evidence_directory、prepared、payload_pin、source_pins を渡す。
`MCMC4QEC_CLUSTER_TRANSPORT` は起動時に unset とし、operation が必要な経路を明示的に設定する。
Python は `-B` で実行し、固定 source ディレクトリへ pycache を生成しない。

## 結果と観測

operation は小 dict を返し、大結果は PBS 内 artifact として保存する。
optional artifacts は名前から `{path,sha256}` または `{path,sha256,stat}` への辞書であり、PBS 内で内容と前後 stat を検証する。
completion には result、sealed artifacts、開始・終了の PBS pin、source pins、prepared pin、parent_binding を保存する。
Deferred 結果が dispatch_candidate を持つ場合、`deep_submission_validation_complete is True` を要求し、completion top-level に同じ値を記録する。
dispatch_candidate は候補 JSON の pin であり、本体の purpose、parent_binding、deep 検証完了、実 qsub 未実施を bounded read で確認する。
その値は本物の qsub 成功や子計算完了を意味しない。
dispatch_candidate がない通常結果は top-level の deep_submission_validation_complete を False とする。
self と children の ru_maxrss は別々に KiB 単位で保存し、合算を peak memory と呼ばない。
observe は pending / failed / accepted の小結果を返し、F / Exit_status=0 / run_count=1 と completion 全 binding が一致した場合だけ accepted とする。
受理時の terminal qstat 原本を一度だけ保存し、後続観測では保存済み原本の同じ実行 identity と F0 を再確認する。
元実行の error 記録、非零終端、不完全 completion、変更された source / receipt / artifact は受理しない。
失敗時も既存出力を残し、自動再試行しない。

## 受入

固定小 operation を使い、prepare→実 ledger fixture→worker→terminal observe の全 envelope を実行する。
actual PBS fixture の owner / script / resource / allocation / host / run count の改変を拒否する。
outer の artifact open を禁止する trap、4 MiB 超過、source の作用中の変更、曖昧投入、偽 Deferred flag、再実行を検査する。
resource や Python の native 検証を stub する fixture は本番完走の証拠ではない。
テストは qsub で実施し、ローカルでは実行しない。
作成時点では受入未実施である。
