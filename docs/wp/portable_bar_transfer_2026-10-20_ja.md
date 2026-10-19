# 最終cohortの転送処理

全768群のcontextと転送一覧を生成した後に使う `output/portable_bar_transfer_v1.py` を追加した。
[小仕様](portable_bar_transfer_spec_2026-10-20_ja.md)と受入テストを先に追加し、実装前のimport失敗を記録してから実装した。
最終実行は21 passed・0.68秒で、入力変更、hash・サイズ不一致、余分・欠落ファイル、既存出力、path脱出、通信失敗時の記録保持を確認した。
一連の転送試験では同じremote Python処理を一時directoryで実行し、正常なbyte転送と転送途中の破損を確認した。
これはlocal fixtureによる試験で、実クラスタへの全cohort転送は未実施である。

全群の固定planが揃った後は以下の入口を用いる。
値は実際に固定したpathとSHA-256へ置き換える必要がある。

```text
python output/portable_bar_transfer_v1.py --plan <transfer-plan.json> --plan-sha256 <SHA-256> --destination /home/user/workspace/mcmc4qec/<new-name> --record-dir <new-local-record-directory> --execute
```

全元ファイルと準備時の証拠hashを転送前後に確認する。
remoteでは新規directoryへ配置し、全memberのhash・サイズ・集合を照合した後に `transfer-complete.json` を排他的に保存する。
localには開始intent、成功時のreceipt、失敗時のfailureを保存する。
失敗した場合は途中出力を保持し、同じ出力先へ自動再投入しない。
この入口はqsubを呼ばず、転送成功を科学的受入とは扱わない。
最終qsubの投入手順はportable用CLIと元native環境を明示して接続する必要があり、従来のPBS解析専用wrapperへそのまま置き換えられるとは扱わない。

source・受入テスト・REDと成功ログは [転送処理の保存資料](data_portable_bar_2026-10-19/transfer_sources_v1/manifest.json) にhash付きで保存した。
保存manifestのSHA-256は `1b78738c84faaba46db610812e792a1acce46e06765bfa12bbd025915e2041f4` である。
公開候補のパッケージと配布物は変更していない。
