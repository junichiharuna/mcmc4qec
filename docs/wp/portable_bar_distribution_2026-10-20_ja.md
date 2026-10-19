# 最終contextと転送一覧の作成手順

全768群が揃った後に使う `output/portable_bar_distribution_v1.py` を追加した。
公開候補と実行中の数値driver、配置済みの最終providerは変更していない。

## 入力と検証

固定した全cohort indexのpathとSHA-256、出力先を指定する。
全768群・67584予定行・固定host割当を確認し、infrastructure failureを含めて全群が終端していることを要求する。
各groupがindexに記録したarchiveへ結び付くことと、選択した全batchに欠落・重複がないことを確認する。
両hostの全設定移植照合の受入記録と、記録された全入力hashを確認する。
元ファイルのpath・SHA-256・サイズと転送先相対pathを一覧にし、作成前後の入力変更を拒否する。
contextと転送一覧の作成だけを行い、転送やqsubは実行しない。
転送後は配置済みproviderが全archive・保存値・元native trace監査・独立referenceを改めて検証する。

## 検証結果

全分母の保持、host・group・計数の不整合、相対path、入力変更、metadata作成のfixtureを含む13テストが1.24秒で成功した。
全metadataを使う正例はfixtureであり、実cohort全体の受入とは扱わない。
現在の実データ80群のindexを渡すと、全768群が未完了であるため拒否し、出力directoryを作らないことを確認した。
結果は [途中indexの拒否記録](data_portable_bar_2026-10-19/distribution-partial-inventory-rejection-v1.json) に保存した。
この確認で科学計算やデータ転送は実行していない。

## 再現

受入テストは `.venv-experimental-optional/Scripts/python.exe -m pytest output/test_portable_bar_distribution_v1.py -q` で実行した。
全群と両hostの移植照合が揃った後の入口は以下の通りである。
引数の値は固定した実ファイルに置き換える必要があり、この最終context作成はまだ実施していない。

```text
python output/portable_bar_distribution_v1.py
  --inventory <complete-inventory.json>
  --inventory-sha256 <fixed SHA-256>
  --output <new directory under output/>
```

出力は `context.json` と `transfer-plan.json` であり、context自体のSHA-256も保存する。
既存の出力へ上書きせず、失敗した出力があれば証拠を確認してから扱う。
source、テスト、REDから成功までのログは `data_portable_bar_2026-10-19/distribution_sources_v1/` にhash付きで保存した。
