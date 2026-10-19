# 独立計時 stage3 の Linux 引継ぎ

runner と submitter の実装・独立レビュー・最小Linux配置を完了した。
科学sourceの最終SHA256は runner `d32c910b25058cc76f3d4d540c3b40801febd810f66b7e156b2b554be8ddc7cc`、submitter `e008f847fdf5b3074de944dcb9f55f2eb998868f0a9c0c2410781d9329ccd485` である。
独立レビューの全5指摘を解消し、`data_tile_validation_2026-10-17/low_noise_timing_stage3_independent_review_v3.json` に承認を保存した。
作者受入は70件・18.43秒、独立受入は第2版66件・17.81秒と最終submit境界10件・2.26秒で、各受入中のsource hash一致を確認した。

受理済みLinux rootは `/home/user/workspace/mcmc4qec/20261018-tile-low-timing-stage3-v2` である。
新source2本とその受入test2本だけを追加し、既存stage2、selector、control、staging、v11 coreとnative環境はコピー・変更していない。
Pythonは `/home/user/workspace/mcmc4qec/20261018-tile-low-timing-stage2-v1/venv/bin/python` を実呼出経路ごと維持する。
PYTHONPATHはstage3のcluster_scriptsを先頭に、stage2の受理済み順序をそのまま続ける。
正式な順序、実import、runtime、Python hash、test参照先は下記source bindingを使い、basenameから推測しない。

`data_tile_validation_2026-10-17/low_noise_timing_stage3_source_binding_v2.json` のSHA256は `97037539c1ec64b43df784adf316af075831fe8c3ba305e9a158cf9a07441297` である。
`import_closure_sha256` はresolved authorityの54件、`actual_source_sha256` と `import_origins` は実import経路を記録する。
既存 `tile_low_noise_staging.py` のcontrol-v2内aliasがstaging-v1へ解決する1件は、`import_aliases` に両経路を明記し、双方のbytesとresolve先を前後固定した。
同bytesでもpathを黙って置換せず、この差で停止したv1配置・失敗ログはそのまま保持した。

Linux受入はscience20件・2.32秒、gate50件・6.46秒で、skipなしだった。
54 moduleとshared/core/nativeは前後一致し、固定native profileとのstrict差分は0だった。
配置証拠 `data_tile_validation_2026-10-17/low_noise_timing_stage3_deployment_v2.json` のSHA256は `4b497a80f0d01b450b0fd5e6855cdc000580a22297cc318d5b10ef948255b406` である。
配置・検査の再現スクリプトは同data directoryの `deploy_low_noise_timing_stage3_v2.py`、archiveと全stdout/stderr・native実測・入力hashも保存している。

次の正式実行には、外部pinしたselector/scientific bundleと、bridgeが実行して受理した新60 namespace全数censusの12descriptorが必要である。
capacityはfull estimator2件・2 workersであり、main準備は外部summary/receipt pinと保存payload検証証拠をmetadata-onlyで受理する。
main計算開始時は実2payloadを再照合し、rawやmarkerの変更を新task前に拒否する。
qsubは親が担当し、1job1node・全体最大2node・曖昧投入の自動再試行禁止を維持する。
今回、正式selection、科学manifest、新全数census、capacity/main qsub、本番計時は行っていない。
小さい受入とnative一致は、96 workerへの資源外挿、低ノイズ精度、混合、名目被覆、速度比の保証ではない。
