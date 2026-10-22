# 次条件のPC serial driver

各hostについて、固定した1条件の全batchを一度ずつ実行する。
開始前に実generator投入registry、新条件のnative reference受理、前条件の最終host batch回収を検査する。
初回batchはexport → preposition → parity → stage → launch → collect、後続batchはparityを再実行せず同じ順序で進める。
初回parity・配置・起動・回収の各adapterに検査を委譲し、driver自身は数値処理を変更しない。
検証済みexport/prepositionの先行準備は次のadapterによる独立検査付きで再利用する。
それ以外の既存保存先や不完全な先行準備、曖昧なSSH応答、失敗した操作は自動再試行しない。
失敗時は現在のbatch・操作・ログ・handleを保持して停止し、実process状態を確認してから別途復旧する。
本driverはqsubせず、native referenceの投入・回収とregistry作成は別操作とする。
各PCの条件順はparity引継ぎの固定順に従い、稼働中のC1T0 driverは変更しない。

## 実施結果と起動

`output/planned_pc_serial_v1/driver.py` に実装し、入力export・PC lifecycle・parityの3受入記録とそれらが参照するsource/inputのhashを開始前に照合する。
新条件の元generator registryと、前条件の最終batch・native referenceのparity registryも開始前に検査する。
各操作のintent、ログ、受理記録のhashを保存し、完了後も科学検証完了とは記録しない。
全33 DGX batch・全5 Labo batchの予定、初回のみのparity、失敗時の停止、既存保存先の拒否、各adapterの引数を検査した。
Windows31件・0.58秒、Linux31件・0.21秒の受入とCLI起動確認が成功した。
数値workerやネットワークを実行しないdriver試験であり、当該5条件の実本番運転を受理した証拠ではない。
[67ファイルのsource・受入・依存記録](data_tile_validation_2026-10-17/planned_pc_serial_acceptance_v1/manifest.json)のmanifest SHA-256は `d761f0743df60067afe84b654e0e3b56566a699a81458a7d80e9a840aea89c9c` である。

実generator全3件の正常終端、新条件native referenceの回収、前条件の当該host最終batch回収が揃った後に、以下の実値を指定する。
generator registryは [入力export](planned_input_export_spec_2026-10-20_ja.md)、parity registryは [初回parity引継ぎ](planned_pc_parity_spec_2026-10-20_ja.md)の形式を使う。

```powershell
& 'A:/dev/mcmc4qec/.venv-experimental-optional/Scripts/python.exe' -B output/planned_pc_serial_v1/driver.py dgx --condition c1t1 --generators GENERATOR_REGISTRY_JSON --generators-sha256 GENERATOR_REGISTRY_SHA256 --parity PARITY_REGISTRY_JSON --parity-sha256 PARITY_REGISTRY_SHA256
```

当該5条件のdriverはまだ起動していない。
クラスタ側のnative reference投入・回収と実registry作成、現在条件からの自動起動待ち合わせは別途残る。
