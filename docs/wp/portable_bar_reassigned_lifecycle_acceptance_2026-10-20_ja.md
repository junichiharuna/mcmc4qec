# DGXへの再割当て配置・起動・回収driver

2026-10-20に[小仕様](portable_bar_reassigned_deployment_spec_2026-10-20_ja.md)に従って、固定した264群・14 batchの配置、先行batch待機、実行config作成、起動、回収を接続した。
既存の元担当・全768群・全192 seed・数値関数・保存配列を変更していない。
公開候補のpackage・配布物は変更しておらず、この追加driverは進行中の数値検証用である。

## 実行前の検査と動作

配置の前に、保存済みの完全parity記録を全数値・flag・未定義位置まで再照合し、独立に固定したplan・baselineと元クラスタのexporter hashを確認する。
入力archiveは全memberのhash、production、群、geometry、元source・manifest・platform資料を確認してからDGXへ転送し、転送先でも全配置fileのhashを確認する。
入力配置の段階では数値計算を開始せず、先行batchの実終端と回収済みarchiveを確認してからexecution configを作る。
先行PIDが存在する間はcompletionが存在しても次を開始せず、PIDが消えてcompletionがないときも次を開始しない。
観測timeoutは同じ先行batchの再観測に戻し、再起動・再投入の根拠にはしない。
execution configとローカル投入intentを排他的に保存した後、DGX側でconfigを排他的に書き込み、runnerの実環境・先行終端・全入力検査が成功してからSSHで実行する。
runner自身の共有lockと固定先行batchの検査により、DGX上の数値workerは20以下に保つ。
実際のexecution intentに結び付けたcollection parentを作り、計算中に次batchの入力を配置して待ち時間を減らす。
現在batchの回収・照合を完了してから次へ進み、群の失敗を含む回収結果は保持して後続の起動を止める。
metadata・転送で失敗した場合も実行中の数値処理のSSH handleを保持して終了を待ち、曖昧な状態の再実行は行わない。

## 受入テスト

| 対象 | Windowsでの結果 |
|---|---:|
| 入力配置・archiveの同一性 | 15 passed / 3.55秒 |
| 先行batch・実行config・collection parent | 19 passed / 8.97秒 |
| 回収制御・失敗時の一度限りの予約 | 7 passed / 1.90秒 |
| driver・配置先行・回収後の順次実行 | 8 passed / 3.20秒 |

同じ49件をクラスタLinuxの新規配置先でも実行し、49 passed・6.48秒だった。
SSH、SCP、数値process起動はテストで模擬しており、この結果を14 batchの実計算完了とは扱わない。
archiveの実際の生配列・数値行検査は既存のreassigned payload・collection・混在providerの受入に加え、各実batchの回収時にも必須とする。
今回のテストと配置確認では新しいqsubジョブは投入していない。

## 実際の配置と待機driver

再割当てbatch 0と1の各20群、計40群をDGXへ配置し、転送前後のhash照合を完了した。
batch 0のprepared SHA-256は `a83ba5e21b38f3188eae898046cb360c9fcc99fdabf14280635f0cca7edd0e96`、入力archiveは294,483,776 byteでSHA-256は `0352f14c8f38e40b08fc0be6b6af6a0096e2e107c20d6bea5e50433fd6b987a8` である。
batch 1のprepared SHA-256は `b7774da9cd386aff7a83aeba84f830c78bb812ca804dec61424875f2c14dc470`、入力archiveは294,479,652 byteでSHA-256は `91d6997449b682b4803a560f331809d45409e89ac9e3fb498e690a334198f82e` である。
2026-10-20 08:18 JSTに `portable_bar_reassigned_pipeline_v1.py --first 0 --last 13` のdriverを開始し、ローカルPID 4108の生存を確認した。
controller記録のSHA-256は `a5993a933093ae5384ee45fdb15c28b370e7d73bd81dde84e42342c289149eac` である。
この起動は使用済みであり、同じcontrollerの再起動や別driverによる重複起動を行わない。
このdriverが既存DGX batch 17の回収準備と回収も担当するため、batch 17に対して別途手動のprepare・collectを並行実行しない。
開始時のDGX batch 17にはまだexecution intentがなく、driverは実remote観測に基づいてその開始・終了・回収を待っている。
直前の観測ではDGX batch 16のPID 1110511は生存中であり、既存batch 17への自動引継ぎも稼働している。
したがって、この記録時点では再割当て264群の数値計算は未開始である。
各batchの実行・終端・回収は `dgx-reassigned-N-*-v1.json` と観測JSONL、driverログに追記される。
全14 batch終了時のcontroller completionも、全768群のsampling・元環境trace監査・独立referenceを含む最終科学評価の代替にはしない。

## 保存先と再現

source・受入テスト・ログ・実配置のselection/prepared/export記録の55ファイルを [source保存先](data_portable_bar_2026-10-19/reassigned_lifecycle_sources_v1/manifest.json) に保存した。
manifest SHA-256は `7327e7ccd80367ab1c49a9adfd89ed280a3f9be2ce56a3d12191894f3e0d4442` である。
クラスタでの受入用配置先は `/home/user/workspace/mcmc4qec/20261020-portable-reassigned-lifecycle-v1`、配置archive SHA-256は `ae3122d44068b23456ae61d8055fcb46811047238a2e29c6a37489e2c3082f59` である。
[配置receipt](data_portable_bar_2026-10-19/reassigned-lifecycle-stage-receipt-v1.json) と [Linuxテストログ](data_portable_bar_2026-10-19/reassigned-lifecycle-linux-lifecycle-tests-v1.log) を保存した。
source manifestのrepository headと外部source hashを照合し、相対パスどおり復元して `test_portable_bar_reassigned_{deployment,control,collection_control,pipeline}_v1.py` をpytestで実行できる。
本番実行の再現では、固定plan・全保存配列・完全parity・元クラスタ環境の資料も必要であり、テストfixtureを実データとして使わない。
実行中driverのsourceは途中で変更せず、障害があれば実PID・実終端・既存intentを照合したうえで別版の復旧手順を作る。
