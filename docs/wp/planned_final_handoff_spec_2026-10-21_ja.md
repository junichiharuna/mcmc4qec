# 最終転送・full監査から設定準備への引継ぎ

## 小仕様

現在稼働中のC1T1・C1T2について、条件別の全件転送driverとfull監査driverの開始intent・source・configを固定する。
両方の完了、同条件native referenceの受理、同一qsub jobのfull監査終端がそろった後に、受入済みの最終設定preparerを一度だけ呼ぶ。
native terminalのhashはnative driverの受理記録から取得し、転送先ファイルを検証するpreparerへ外部pinとして渡す。
先行処理の失敗、条件・path・hash・jobの不一致、既存操作intentを拒否する。
Python起動前の1 thread環境を維持し、リモート実行前後のsource照合とstdout・stderr・終了codeを保存する。
通信失敗や観測timeoutだけで同じ操作を再試行しない。
この親処理は設定作成と非投入preflightまでを行い、最終集計のqsubと回収は別の接続とする。

## 受入条件

転送・full監査・native referenceのいずれかが未完了なら操作しない。
誤った条件、転送receipt、native terminal pin、audit job、先行errorを拒否する。
実C1T1・C1T2の開始記録を読み取りだけで照合する。
リモート非zero終了は証拠を残し、同じprepare intentで再試行しない。
正常応答でも別config・job root・投入済み状態は拒否する。

## 実施結果

Windowsで19件・1.40秒のテストが成功した。
実C1T1・C1T2の開始intentと監査configを照合し、3つの先行処理の待機・証拠改変拒否・通信先非zero終了後の再試行拒否を確認した。
正常応答の試験はリモート実行を置き換えたfixtureであり、本番設定の作成成功を示さない。
親driverのLinuxテストは未実施であり、接続先preparerのWindows・Linux各43件の受入とは区別する。
source・red/greenログ・実行環境は [受入manifest](data_tile_validation_2026-10-17/planned_final_handoff_acceptance_v1/manifest.json) に保存した。
manifest SHA-256は `32ce0ad145669b6204b70cdc289ade556270ec72a3fa6dae80e9faa27f0b985a` である。
waiter SHA-256は `0c3fe62cda2993c6dc84c4ab2b658db72e1a9469d8bb1c36e9f1b0cb264f35cd` である。
01:19 JSTにC1T1のPID17424とC1T2のPID44648でlive sessionを確認した。
両方とも先行処理の完了待ちであり、本番prepareは未起動である。
設定作成後の最終集計qsubとreport回収の自動接続は残る。
