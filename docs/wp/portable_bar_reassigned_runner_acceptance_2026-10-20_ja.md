# 未予約群をDGXで後処理するrunnerの受入記録

## 実装した範囲

[分担変更の小仕様](portable_bar_remaining_assignment_spec_2026-10-20_ja.md)と[固定planの受入](portable_bar_remaining_assignment_acceptance_2026-10-20_ja.md)に続き、再割当てbatchを実行するrunnerを追加した。
既存の `portable_bar_full_v1.initialize` と `portable_bar_full_v1.process_group` を直接使用し、数値関数とdecoderを呼ばない配列解析の実装は変更していない。
既存のfull driver・array adapter・archive readerのSHA-256をrunner内で固定し、実行configに異なるsource hashを記録しても受け入れない。
実行config自体にも独立したSHA-256を要求し、分担plan、baseline、入力archive、全数値設定、実際のhostname・Python・OS・依存版、既存の完全parity検査の証明記録を結び付ける。
隔離モード `python -I` で起動するCLIと、20 worker・spawn方式の実行を備える。

先行batchのintent・completionのhash、実host・runtime、全群の終端状態と行数を確認し、実PIDが終了するまで新しいworkerを起動しない。
最初の再割当てbatchの先行対象は既存DGX batch 17とし、それ以降は直前の再割当てbatchとする。
再割当てbatch同士の重複起動を防ぐ排他ディレクトリを設け、異常終了時は出力と排他記録を残して照合を必要とする。
既存出力を上書きせず、workerの例外をinfrastructure failureとして全群の分母に残す。
実行先はDGXとして記録し、元のLabo担当だったことは固定planに保存する。

## 検証結果と限界

受入テストを先に作り、未実装によるimport失敗を確認した後に実装した。
最終29テストは6.57秒で成功した。
入力・担当・worker数・source・runtime・thread設定・先行batch証拠の変更の拒否、排他制御、失敗群の保持、実行intentと結果の対応を確認した。
実行制御テストのworker poolと解析結果には合成入力・代替関数を使用しており、新runnerで本番BAR計算を再現した検査ではない。
保存済みparityの証明記録の確認も、配置時と最終集約時に行う生データの独立照合を置き換えない。

DGX実機の新規検査ディレクトリ `20261020-portable-reassigned-runner-check-v1` に7 sourceを配置し、転送前後のhashを照合した。
実機のPython 3.11.17・Linux aarch64で `-I ... --help` が成功し、読み込んだ初期化関数と解析関数が既存full driverの関数と同一であることを確認した。
この実機検査はimportとCLIのみであり、数値処理を起動していない。
実機の記録は [DGX検査receipt](data_portable_bar_2026-10-19/dgx-reassigned-runner-check-receipt-v1.json) に保存し、SHA-256は `3a42d9a69398e464a755c3fe680841a5fd15ba0e011fbbf86842acdcc883cb05` である。

## 保存物と残作業

[source・テスト・ログの保存先](data_portable_bar_2026-10-19/remaining_assignment_runner_sources_v1/)には、固定plan・baseline・既存parity検査記録も含めた。
[manifest](data_portable_bar_2026-10-19/remaining_assignment_runner_sources_v1/manifest.json)のSHA-256は `dfb8ed71e5d572ce62ba4b0e6ab93b926aac82cc5daa80db72597c3796e6f6de` である。
ローカルの受入テストは次のコマンドで実行した。

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
& 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe' -B -m pytest output/test_portable_bar_reassigned_runner_v1.py -q
```

新runnerの本番config生成・入力配置・起動制御・回収・旧新artifactの混合集約・最終provider接続は未完了である。
既存のcollectorとproviderは固定owner規則を用いるため、そのままでは再割当て結果を受け入れない。
これらの対応と検証を完了するまで、再割当て264群の本計算は開始しない。
既存経路の計算・回収、元環境のsampling・trace監査・独立reference照合は継続する。
