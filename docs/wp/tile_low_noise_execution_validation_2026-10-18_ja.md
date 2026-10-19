# 低ノイズ解析の分割・集計・checkpoint監査とseedジョブ

本記録は実行準備と軽量受入の記録であり、低ノイズの科学計測完了や名目95%被覆を示すものではない。
既存の解析・sampling・capacity driverを変更せず、別moduleを追加して接続した。
小仕様・受入テスト・実装の順で追加し、独立レビューを行った。

## 分割実行と全群回収

`tile_low_noise_analysis_partitions.py` は実測済み解析capacityの資源計画を再検証し、同一production manifestの全768群を重複なく分割する。
群内のrung・chain・設定は分割せず、既存の数値解析とbootstrap seedを共有する。
rootの排他的routing予約で旧全群runnerとの競合を防ぎ、partitionごとのPBS実行intent・native preflight・worker数・完了summaryを保存する。
collectionは全partition・groupの完了と解析JSON/NPZのchecksum、各設定行、入力markerを確認する。
欠落partitionは未完了として停止し、記録済みsampling失敗・診断未定義・区間未取得は全て分母に残す。
出力は`partition-collection/rows.jsonl`と`summary.json`である。
`read_collection`のiteratorを最後まで消費すると全行と最終件数・証拠の検証が完了する。
本番のpartition plan作成には実測capacityと本番samplingの完了が必要で、現時点では未実施である。
qsub投入管理と低ノイズ全数trace監査runnerは別工程である。

## 独立referenceのない設定比較

`tile_low_noise_summary.py` は検証済みcollectionを全件消費し、全設定について192 replicateの分母を保持する。
kernel・初期化・chain数・burn・window・ladder・誤差法の一要因比較を行う。
推定差はright-minus-left、log比はlog(right)-log(left)と出力にも明記する。
点推定または正の点推定が欠けた場合、全cohortの量は未定義とし、available-onlyの値を別欄へ保存する。
区間の非交差件数は比較可能な対の数と全replicate数を併記する。
独立referenceを設定しないため、bias・RMSE・被覆は報告せず、設定間の一致を精度や収束の保証として扱わない。
重み層別referenceとの比較は、既存の区間reference評価と実artifact監査へ別途接続する。

## 低ノイズtrace監査

`audit_tile_low_noise_traces.py` は7座標task、固定prior、実metadata・RNG、sampling設定、全compact配列の型・長さ・範囲、初期logical係数と状態、initial/final/checkpoint、提案・受理・移動の計数を確認する。
depolarizingはI/X/Y/Z=0/1/2/3の表現で、X/Z交互のbasisと非零logical combinationを再構成する。
保存された初期状態とcheckpointを同じdecoderで再復号し、sector・syndrome weight・weightと照合する。
保存していない各stepの物理状態、全乱数軌道、独立したdecoder実装の正しさを確認したとは扱わない。
純関数`audit_task`はnative未検証を明示し、artifact入口`audit_saved_task`は実native profile・source/runtime・manifest・payload hashを必須にする。
記録済み失敗は部分payloadの成功を主張せず保持する。
全数runnerと資源計測は未実装・未実施である。

## 全seed監査のqsub wrapper

`submit_tile_seed_audit.py` はproduction baselineのcore packageとsource/runtimeを固定する。
計画時の実1000件pilotで時間・RSS・SQLite file sizeを測り、全予定3,855,274件の計算時間とscratch容量を外挿する。
要求は1 CPU・2〜4 GiB・30分上限・1ノードとし、事前の外挿が上限を超える場合は投入しない。
queued込み最大2ノード、稼働coordinatorとの競合拒否、他の低ノイズsubmitterとの共有lock、intent保存後のqsub一回を要求する。
不明な投入応答ではintentとlockを保持する。
実行後は全数完了・予定件数一致・未確認件数ゼロ・想定外collisionゼロ・入力/source証拠一致を確認する。
選択済みBAR計時manifest待ちのstage140/141は未監査の予約として残し、全goalの名前空間を監査済みとはしない。
全数監査と実qsubは未実施である。

## 受入の範囲

Windowsの新4 fileは140 passed・12.32秒だった。
内訳はpartition 40件、summary 16件、seed submitter 22件、trace監査62件である。
core環境はoptional依存を持たず4 skipped・0.27秒、pytest終了コード5で、実行成功件数に含めない。
source hashと結果は`data_tile_validation_2026-10-17/low_analysis_extension_windows_acceptance_v1.json`に保存した。
partition・summaryの独立レビューでは分母と証拠検査、設定差の方向・欠落時の扱いを確認した。
seed wrapperの独立レビューでcore環境のcollection失敗を発見し、3依存のskip guardを追加して修正した。
checkpoint監査の独立レビューでは62件が成功し、native検証の入口と全状態再復号ではない適用範囲を確認した。
collectionからsummaryまでの結合受入は実ファイルと実readerを使うが、上流PBS実行証拠とgroup生成はfixtureであり、実際の192 cohortを測定したものではない。

## Linux配置と投入前確認

`20261018-tile-low-analysis-v4`へ旧core packageと既存3 driverを保持したまま追加moduleを配置し、新4 fileの140件が全て成功した。
各fileは60秒以内で、partition 1.07秒・summary 0.80秒・seed 0.43秒・trace監査7.02秒だった。
既存Linux native profileとも厳密一致し、旧profileの変更は行っていない。
archive SHA256は`416b655ed1507272ccabca7836678dd7e20589248a7ff519648844d5af4c7c86`である。
受入ログ・source照合は`data_tile_validation_2026-10-17/low_analysis_linux_acceptance_v4.txt`と`low_analysis_source_binding_v4.json`に保存した。

seed計画の実1000件pilotは0.04905秒で、想定外collision 0・意図的共有21を記録した。
予定3,855,274件中3,854,274件は未検査である。
全数時間のfactor2外挿は378.17秒、要求は1 CPU・2 GiB・30分・1ノード、必要scratchの予算は4 GiBとなった。
これは本計算の実測時間や終了保証ではない。
manifest digestは`1464f4c66b2da06129a727ae352f77927e4f85dc2fb64d2617b4f877be193fe1`、PBS script SHA256は`f9c5a036ee270f7245c730812de80ccbe8581b6a062a846edaa61b8cfc854e3e`である。
plan・dry-run・PBS構文確認の証拠は`low_analysis_seed_plan_validation_v4.json`、`low_analysis_seed_dry_run_v4.json`、`low_analysis_seed_script_v4.sh`に保存した。
capacity本計測と本番samplingが未完了のため、partitionの本番planは作成していない。

クラスタ上でseed投入のdry-runを再現するコマンドは次のとおりである。

```bash
cd /home/user/workspace/mcmc4qec/20261018-tile-low-analysis-v4
export PYTHONPATH="$PWD/src:$PWD/cluster_scripts"
venv/bin/python cluster_scripts/submit_tile_seed_audit.py submit \
  --bundle "$PWD" --root "$PWD/runs/seed-census"
```

実投入は同じコマンドへ`--execute`を加え、submitterがcontroller停止とqueued込み最大2ノードを確認してqsubを呼ぶ。
現時点の実qsub・全seed監査・低ノイズ本計算・全数trace監査は未実施である。
09:14:09 JSTに既存265209・265211が各1ノードで実行中、controller PID 3756042も稼働していることを再確認した。
case0は72,987/86,016、case2は15,624/43,008 trace markerで、観測証拠を`low_analysis_cluster_observation_v2.json`に保存した。
