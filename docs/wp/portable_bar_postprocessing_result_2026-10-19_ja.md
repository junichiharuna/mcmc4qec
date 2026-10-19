# 追加PCへのBAR後処理の移植と初回投入

2026-10-19 22:01 JST時点で、DGX Sparkの20 workerとlabo PCの24 workerによるC0T2の全window後処理を開始した。
クラスタの265334（C0T1 BAR）と265338（C0T2 sampling）はともにR・run_count 1であり、要求node数は合計2のままである。
公開候補とは別のdriver・出力先で処理し、GPU専用コードは追加していない。

## 方法と受入

[小仕様](portable_bar_postprocessing_spec_2026-10-19_ja.md)に従い、元の解析source hashを固定して、decoder構築の代入だけを除き、符号の寸法をexport済みgeometryから供給した。
入力loaderも元sourceを固定し、同じ寸法置換と保存済みProblem metadataの供給によって、元のtask・prior・seed・config・payload検証を保持した。
元の数値処理、bootstrap seed、失敗判定、logical sectorを変更していない。
移植経路ではdecoder factoryを例外に置き換え、誤って再構築した場合に停止させる。
合成データの成功・失敗・anchor 0の一致、source/geometry拒否、元metadata・payload改変の拒否、割当の完全性、上書き拒否を含め、13テストが2.08秒で通った。

実traceの受入には、C0T0 group `(0,0,0,0,0)` の4 chain・burn-in 600・保存600の既存結果を使った。
両PCとローカルで、BAR 6行・診断128件・ACF 128配列が、離散値・flagsは完全一致、浮動小数点はrtol=1e-10・atol=1e-12、NaN/Noneの位置一致を満たした。
この検証用出力は本校正のcohortに追加しない。
受入は1 groupの短いwindowに対する移植確認であり、全設定の精度・被覆や全architectureの等価性を保証しない。

## 初回の本処理

元の全768 groupの順序を固定し、通番を44で割った余り0〜19をDGX、20〜43をlaboに割り当てる。
初回は完了markerがそろっていたgroup `(0,2,0,0,0)`〜`(0,2,0,0,43)` を対象とし、前半20 groupをDGX、後半24 groupをlaboに送った。
対象を診断値や推定値で選別していない。
全window・burn-in・chain数・ladder・bootstrap予算を元planのまま処理する。
全768 groupの予定集合と、今回の44 group以外も各実行intentに保存した。
各taskの既存の失敗と、後処理自体の失敗を残す。

DGXの親PIDは468606で、20 workerが各約99%のCPUを使っていることを確認した。
laboの親PIDは15892で、24 workerの生存とCPU時間の増加を確認した。
laboは最初のバックグラウンド起動で親プロセスが残らず、同driverのプロセスも出力directoryも存在しないことを照会した。
その観測を保存してから、別出力 `result-v2` へSSH接続を維持する方法で起動した。
最初の終了原因は特定しておらず、SSH接続終了に伴う終了の可能性を確定事実として扱わない。
現在のSSHはローカルPID 40784であり、曖昧な接続応答だけで計算を再投入しない。

DGXの実行先は `/home/other/workspace/mcmc4qec/20261019-experimental-platform-v2/portable-bar-full-batch0-v1/result` である。
laboの実行先は `D:/mcmc4qec_runs/20261019-experimental-platform-v1/portable-bar-full-batch0-v1/result-v2` である。
観測時点では両方とも完了groupは0であり、開始を完了と扱わない。

## データと再現

[実行証跡directory](data_portable_bar_2026-10-19/)に、両PCのparity受入、export hash、初回投入、起動し直す前の観測、PID・workerの実観測を保存した。
固定元source、plan、全raw payload、元環境profile、geometry、Problem metadata、全入力SHA256は、export archiveに含む。
parity入力archive SHA256は `139ae3e80fe394acd89ed6cd1fe64368f7b9bf6b90cbaa31d5c5dada1794b600` である。
DGX初回入力archive SHA256は `25e0a49db023f9becc16d2d84e4370e8d3a03722de17217e7c1429bb17fb2485` である。
labo初回入力archive SHA256は `16a0362902edde849ce9a54edc278b08364da6febdaf9ff728766e3f28716b53` である。
archiveの元はclusterの `/home/user/workspace/mcmc4qec/portable-bar-export-parity-v2/inputs.zip`、`portable-bar-c0t2-dgx-batch0-v1/inputs.zip`、`portable-bar-c0t2-labo-batch0-v1/inputs.zip` に残す。
ローカルにも同じarchiveを `output/portable_bar_parity_inputs_v2.zip`、`output/portable_bar_c0t2_dgx_batch0_v1.zip`、`output/portable_bar_c0t2_labo_batch0_v1.zip` として保持する。
source・再現コマンドの引数は `sources_v1/` と各launch recordに保存する。
同じ入力で新規の出力先を指定して `portable_bar_runner_v2.py` を実行すると短いwindowの受入を再現できる。
本処理は `portable_bar_full_v1.py` を使い、公開candidateのパッケージではなくarchive内の元sourceを読み込む。

## 未完了事項

初回44 groupの完了・hash確認と、残る724 groupの処理が必要である。
元samplingの全partition終端、全task census、元環境によるtrace audit、独立referenceとの結合を終えるまでは、移植結果は暫定後処理として扱う。
既存の固定runtimeやPBS実行記録を装ったmarkerは作らず、samplingと後処理の環境を分けて保存する。
正式な低ノイズ比較の完了数は引き続き4/12条件である。
今後のgroup集約で、両PCの結果と元環境の監査を結び付ける受入経路を実装する必要がある。
