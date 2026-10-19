# Portable BAR：最終cohort providerの統合

公開候補 `47ef1b6` と実行中の計算driverを変更せず、最終集計用のproviderと移植照合gateを追加した。
対象はC0T2の全768群・192 seedであり、途中の部分集合を正式なbias・被覆の集計へ渡さない。

## 実装

`output/portable_bar_provider_v1.py` は、独立に固定した `context.json` のSHA-256を受け取り、全archive・parent binding・receipt・両hostの移植照合artifactを照合する。
全入力はroot内の相対pathとhashで登録し、入力directory外への参照、sourceやruntimeの差替え、同一groupの重複、未回収groupを拒否する。
元sampling recordとanchorは現在のsampling rootから読み取り、実artifactで検証済みのpayload readerへ渡す。
providerが読むsampling rootとnative trace監査の対象rootが同一であることも要求する。
解析処理が失敗した群も全88設定を分母に残し、未取得の推定値や診断を作らない。
providerと各helperのsource hashを最終レポートの入力検証へ加えた。

`output/portable_bar_parity_gate_v1.py` は、成功flagだけでなく、元reference archive全memberと回収したJSON・NPZを読み、保存値を再比較する。
実行環境、source、入力archive、変換規則、intent、marker、全設定の計数、rtol=1e-10・atol=1e-12、離散flag・未定義位置の一致を要求する。
推定計算やdecoderの再実行は行わない。
このgateをDGXの実保存artifactに適用し、88行・1536診断・1536 ACF配列の比較に成功した。
結果は [DGXの最終provider用照合](data_portable_bar_2026-10-19/dgx-final-provider-replay-gate-v1.json) に保存した。

## 受入テスト

移植照合gateと全設定referenceのテストは33 passed / 1.25秒だった。
provider・native監査の全体制御・最終レポート境界の統合テストは44 passed / 14.88秒だった。
全768群が解析処理の失敗となるfixtureでも、768群・67584予定行を保持し、全群を読まずに完了扱いにすることを拒否した。
現在のsampling record・anchorの引渡し、同一群の二重消費、両hostの照合必須、固定host割当、入力hashの変更も検証した。
全cohortの制御テストではarchive I/Oをfixtureへ置き換えており、実cohort全体の検証完了を示さない。
実archiveのpayload読取りは別途DGX batch 2の20群・1760行で確認済みである。

## 実行入口と残作業

`output/portable_bar_final_join_v1.py` に以下の引数を持つCLIを追加し、help表示を確認した。

```text
--sampling-root
--audit-root
--portable-root
--portable-context-sha256
--reference-root
--output
```

CLIは独立referenceを必須とし、実処理は元native環境のPBS job内でのみ実行する。
クラスタ実行は既存のqsub手順と最大2ノードの制限に従う。
全768群の回収、Laboの全設定照合・回収、全samplingの完了証拠、元native環境のtrace監査が未完了である。
したがって、最終contextの固定、元環境への配置、最終qsub投入と正式なreference比較は未実施である。
この実装・テストの成功を、母集団RMSEや名目95%被覆の保証とは扱わない。

## 保存先

実装、依存するportable helper、受入テスト、実測scriptとログは `data_portable_bar_2026-10-19/provider_sources_v1/` にhash付きで保存した。
原本とsource hashを一致させた研究実行bundleの `cluster_scripts/` とパッケージsourceを併用する必要がある。
公開候補のwheelにこれらの実験専用scriptを追加したという意味ではない。
