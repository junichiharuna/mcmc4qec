# 低ノイズBAR解析・資源計測・seed監査の受入

本記録はv3までの受入時点を保存する。
後続のpartition実行・集計・checkpoint監査・全seedジョブの実装状況は[低ノイズ実行検証記録](tile_low_noise_execution_validation_2026-10-18_ja.md)を参照する。

本記録は解析と実行準備の受入であり、tileの低ノイズ領域での混合・精度・被覆を校正した結果ではない。
本番192 replicateの低ノイズ計測、合成データによる全寸法の資源計測、全seed照合は未実施である。

## 実装した範囲

`cluster_scripts/tile_low_noise_analysis.py` はtile72/288のbit-flip・depolarizingについて、保存された低ノイズtraceと独立anchorから既定の全window・burn・chain数・ladder・誤差法を解析する。
本番は2 kernel×2 initialization×192 replicateの768群を保持し、sampling失敗・anchor未取得・zero anchor・診断未定義・区間未取得を成功群だけの結果に置き換えない。
sampling用capacityの1 chainデータは本番BARの入力として拒否する。
fixed decoder prior、各rungの物理p、RNG、Problem、source/runtime、native profile、PBS実行証拠、artifact hashとphase summaryを照合する。
独立referenceをこの解析内では設定せず、重み層別samplingの部分和を真値として扱わない。

`cluster_scripts/tile_low_noise_analysis_capacity.py` は全chain数・全trace長を持つ人工配列で数値計算本体を測るための別driverである。
保存するのは費用と件数であり、人工配列から得た推定値を科学結果として保存しない。
資源CLIは全群の成功と全設定の出力件数を確認し、生artifact・native実行証拠が一致する場合だけ見積りを返す。
詳細とI/O・同時worker数の外挿に関する制約は[資源計測仕様](tile_low_noise_analysis_capacity_spec_2026-10-18_ja.md)に記す。
資源計画のpartitionは全768群を保持するが、本番driverのpartition実行への接続は未実装である。

`cluster_scripts/tile_seed_audit.py` は予定seedをSQLiteへ逐次登録し、同じseed入力の意図的共有と想定外の重複を分ける。
予定件数は3,855,274件で、low-noiseのstage150〜155を含む。
stage140/141は実際のBAR計時条件manifestが未作成のため、未監査の予約として残す。
全数を調べても乱数列の統計的独立性や実際のsampling metadataとの一致を証明するものではない。
現sourceの1000件pilotは`data_tile_validation_2026-10-17/seed_namespace_extended_pilot_v2.json`に保存し、想定外の衝突は0件、既存synthetic/main bootstrapの意図的共有は21件だった。
pilotの時間から全数は約428.7秒と外挿されたため、軽量ローカル作業には含めていない。

`cluster_scripts/submit_tile_low_noise_analysis_capacity.py` は合成解析capacity専用のqsub submitterである。
queued込み最大2ノード、稼働coordinatorとの競合拒否、他の低ノイズsubmitterと共通の排他lock、intent保存後のqsub一回を要求する。
timeout・非零終了・不明job IDではintentとlockを保持して自動再投入を防ぐ。
source・package・native入力・Python・scriptを直前まで照合し、8 workerでの初回要求は1ノード・96 CPU・340 GiB・24時間上限とする。

## 受入と独立レビュー

Windowsで解析27件・資源計測25件・seed監査10件、合計62件が31.13秒で成功した。
実際の小予算trace・anchorを用いた4case、失敗行保持、native/PBS結合、入力欠落・改変拒否、cache、数値例外、人工配列の数値core、資源式と全群保持を含む。
証拠とsource hashは`data_tile_validation_2026-10-17/low_analysis_windows_acceptance_v1.json`に保存した。
これらは全trace長・全192 replicateの科学計測ではない。

独立レビューでは資源summaryだけで全設定実行を確認しない点が指摘され、`measured_profile`のartifact照合と全設定件数検査を追加した。
人工配列で測らないchecksum照合・NPZ入力・ACF/JSON出力、および8 workerから最大96 workerへの外挿は未測定範囲として仕様へ明示した。
別の独立レビューではBARの共有rung bootstrap、cross-chain共分散、独立anchor分散、depolarizingの重みによる密度比、全予定行保持を確認し、blocking findingはなかった。
関連する既存統計・BAR・新解析の42件は24.82秒で成功した。
詳細釣合い・既約性や収束の証明をこの実装レビューから主張しない。
submitterの独立レビューではblocking findingはなく、qsubをmockする23件が7.55秒で成功した。
core環境で追加testのoptional依存欠落によるcollection失敗を実証し、今回の4 test fileにldpc・bposd・pymatchingのskip guardを追加した。
coreで4 skipped・0.33秒を確認し、全skipのpytest終了コード5をテスト失敗や実行成功件数として数えない。
skip guardとsubmitterを統合したWindows最終4 fileは85 passed・35.91秒で、source hashを`data_tile_validation_2026-10-17/low_analysis_windows_acceptance_v2.json`に保存した。

## 実行環境の固定

追加decoderを含む最新packageでのLinux軽量受入は62件成功したが、既存の科学計測用native preflightはpackage hashの差により拒否された。
native binaryと固定fixtureの応答は一致しても、環境全体の一致を代用しない。
既存profileを更新して検査を通すことはせず、科学計測と同じ既存wheelのpackageを隔離srcへ配置したv2 bundleで再検証した。
実証は`data_tile_validation_2026-10-17/low_analysis_native_comparison_v1.json`に保存した。
v2ではLinux受入62件が成功し、既存Linux profileとの厳密preflightも全項目一致した。
tile72-bit・target .001・15 rungの合成capacity planとplan preflightを生成し、8群・8 workerの予定を保存した。
v2 archive SHA256は`0f65b8f5fe7d61921bfa15b47a792c738127b684a87f948fefb0c3cd477c2cff`である。
受入・環境比較・plan証拠は`data_tile_validation_2026-10-17/low_analysis_linux_acceptance_v2.txt`、`low_analysis_native_comparison_v2.json`、`low_analysis_capacity_plan_validation_v2_case0_target2.json`にある。
稼働中のproduction/coordinator bundleやvenvは変更しない。

クラスタ実行はqsubを使い、queuedを含む最大2ノードを維持する。
稼働coordinatorと追加submitterを競合させない。
低ノイズ本番解析の最終利用手順は、資源実測・必要なpartition実装・完全trace監査への接続後に確定する。

## v3の配置と再現手順

submitterを加えた`20261018-tile-low-analysis-v3`でLinux最終85件が成功し、各test fileは60秒以内だった。
既存profileとの厳密preflight、tile72-bit・target .001のcapacity plan、新submitterのdry-runと`bash -n`も成功した。
旧core 29ファイルと既存3 driverはv2とbyte一致で、最新packageへの暗黙の切替はない。
v3 archive SHA256は`5a1861baef1fe943d57238c18b90c2a47205bd85ba492323d690cdc84a6ec995`、PBS script SHA256は`39a121c517e051b9b0bfba5b48b52bea1e77f1960724ad0693f5d1a0c771036b`である。
manifest digestは`802a1de95b641ed429b6f886c5e0ecf29165455d1a186cca547b33fde847e548`でv2から変わらない。
証拠は`data_tile_validation_2026-10-17/low_analysis_linux_acceptance_v3.txt`、`low_analysis_source_binding_v3.json`、`low_analysis_capacity_plan_validation_v3_case0_target2.json`、`low_analysis_capacity_dry_run_v3_case0_target2.json`に保存した。
archive内文書は配置時点のsnapshotであり、後から追記したローカル検証記録と実行sourceのhashは区別する。

クラスタ上のdry-run再現コマンドは次のとおりである。

```bash
cd /home/user/workspace/mcmc4qec/20261018-tile-low-analysis-v3
export PYTHONPATH="$PWD/src:$PWD/cluster_scripts"
venv/bin/python cluster_scripts/submit_tile_low_noise_analysis_capacity.py \
  --bundle "$PWD" --root "$PWD/runs/capacity-0-2"
```

実投入時は同じコマンドへ`--execute`を加え、submitterがcoordinator停止・queued込み2ノード以内・source一致を確認してqsubを一度呼ぶ。
この実投入は未実施であり、稼働coordinatorのある現在はguardで拒否される。
実測完了後は同じ環境で`tile_low_noise_analysis_capacity.py resources --root runs/capacity-0-2`を実行し、全artifactとnative証拠に結合した資源計画を得る。
dry-runの24時間は初回要求上限であり、実測時間や完了予測として引用しない。
