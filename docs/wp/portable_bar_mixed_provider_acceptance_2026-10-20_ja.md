# 再割当てarchiveの読み取りと最終providerの受入記録

## 実装範囲

[回収・混合集計](portable_bar_reassigned_collection_acceptance_2026-10-20_ja.md)に続き、再割当てarchiveを読むpayload readerと、旧新経路の全768群を扱うproviderを追加した。
payload readerはarchive内のplan・baseline・config・実行intent・実行先・collector sourceを、外部から固定した分担planと照合する。
独立したplanのhashを最後まで保持し、archiveやplanの途中変更を拒否する。
数値行、marker、診断、ACFを読む既存のメソッドはASTが同一であることを確認した。

新providerは両ホストの保存済み完全parityを生データから再照合する既存の処理を使用する。
元環境のsampling metadataを各群のreaderへ渡すメソッドも既存providerからそのまま継承する。
旧24 batchと再割当て14 batchの全38 batchを固定planに結び付け、実際の前batchの終端hashと新batchのconfigが一致することを確認する。
全群の一意性と分母を保持し、すべての群が読み出されるまで `finish` を成功させない。
providerのprovenanceには分担planとbaselineのhashを残す。

最終report入口は既存版のprovider importだけを新providerへ変更した版を作成した。
元環境のsampling・PBS・native trace監査と独立reference照合の処理は変更していない。
新providerだけで科学的な最終検証が完了したとは扱わない。

## 確認結果

payload reader、provider、最終reportの各受入テストを先に作り、未実装による失敗を保存した後に実装した。
新旧payload検査37件は6.51秒で成功した。
再割当てarchiveのfixtureには本番manifest・環境情報と合成した20群のinfrastructure failureを用い、全失敗群の保持と証拠改変の拒否を確認した。
本番metadataはDGX batch 17の入力archiveからhash照合付きで取り出した2ファイルであり、元archive SHA-256は `6fa64c7534507a6aeac090f3e612ecea33fb8a3d2156f6b7e6d0a429c3a33ed2` である。
これは本番の数値結果を新readerで再現した試験ではなく、成功した数値行の読み取りは既存の小さいfixtureと変更していない検査メソッドで確認している。

providerの制御検査15件は30.04秒で成功した。
このテストではarchive readerとparity検査を代替関数に置き換え、全群数・担当・source・前batchとの結び付け・未回収・重複・path逸脱の拒否を確認した。
実archiveのI/Oとparityの生データ照合の検査は別であり、この制御検査を本番の全群照合とは扱わない。
新しい最終監査・report入口の32テストは13.93秒で成功した。
本番の最終reportジョブは未実施である。

## 保存と実機確認

[source・テスト・fixture・ログ](data_portable_bar_2026-10-19/mixed_provider_sources_v1/)の51ファイルを保存し、元のsourceとのbyte hash一致を確認した。
[manifest](data_portable_bar_2026-10-19/mixed_provider_sources_v1/manifest.json)のSHA-256は `6432d594c0e9d561494f29d70fbbfc630c8f6c7ac0ffb1ff0896fac38a1fef74` である。
各ファイルの元の相対位置と基になるcheckoutのcommit、外部のcluster helperのhashをmanifestに記録した。
再現にはそのcheckoutの `src/` と `cluster_scripts/` を使い、保存したhelperとfixtureを記録された `output/` の位置へ復元する。

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
& 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe' -B -m pytest output/test_portable_bar_reassigned_payload_v1.py output/test_portable_bar_payload_v1.py -q
& 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe' -B -m pytest output/test_portable_bar_mixed_provider_v1.py -q
& 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe' -B -m pytest output/test_portable_bar_mixed_final_join_v1.py output/test_portable_bar_mixed_final_report_v1.py -q
```

クラスタの新規ディレクトリ `20261020-portable-mixed-final-provider-v1` にsourceを配置し、転送hash・import・CLI・数値関数のAST変換を確認した。
配置archive SHA-256は `306fa9c4140f4b4548270b391dcca2c265021199ce977a86c3e65595793a87b7` で、CLIとimportはいずれもreturncode 0だった。
記録は [Linux配置receipt](data_portable_bar_2026-10-19/mixed-final-provider-stage-receipt-v1.json) に保存した。
この実機確認は科学計算を起動せず、qsubも実行していない。

## 残る作業

新しい転送contextの生成・転送・qsub入口の接続、および再割当て本番configの生成・配置・起動と回収の自動制御が残る。
再割当て264群の本計算と本番の混合集約は未実施である。
公開候補のsourceと配布物は変更していない。
