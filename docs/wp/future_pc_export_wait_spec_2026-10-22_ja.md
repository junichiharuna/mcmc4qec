# 未開始C3T1/C3T2のPC入力export待機を修正する

## 根拠と範囲

C3T0 laboの初回exportはlocalの300秒待機で停止した一方、remote export自体は正常終了していた。
その復旧ではremote結果を確認して再利用し、以後のC3T0 labo exportを完了まで待つ別helperを受け入れた。
未開始C3T1/C3T2のPC経路には元の300秒待機が残っている。
同じ待機切れを防ぐため、この2条件のDGX・laboの将来のexportだけに同じ修正を適用する。
実行中のC1T2とC3T0のsource・process・科学設定・出力先は変更しない。

## 契約

変更はlocal SSH subprocessのexport完了待機を300秒から無期限へ変更することと、その新helperへの明示的な接続に限る。
SSH接続timeout、keepalive、remote generator終端検証、source/input hash、固定群割当、archive構成検証、転送検証、preflight、失敗時の記録と再試行禁止を維持する。
scpの既存timeoutや科学計算の予算は変更しない。
明示的なC3T1/C3T2・DGX/labo・固定範囲内のbatchのみを受け入れる。
元のexport、serial、handoff、launcherを保存し、旧sourceと新sourceの両方をintentへ固定する。
新serialの出力と完了契約は既存の後段が読むものを維持する。
C3T1 laboのC3T0復旧serialへの接続も維持する。
native referenceの起動・generatorの順序・qsub・最大2nodeの制約を変更しない。

## 受入と稼働切替

先にscope、待機式以外のsource保持、export以外のargv保持、元の失敗時停止・再試行禁止、C3T1 laboの先行root保持をテストする。
registryやnative referenceがない状態ではPC処理を始めないことを確認する。
launcherの切替はregistry未取得・children空・実子processなし・旧source不変・旧PIDとcommandと生成時刻一致の場合だけに限定する。
旧intentと観測履歴を保持し、未着手のlauncherだけを停止して新しい保存先のlauncherへ引き継ぐ。
新processの実生存と待機状態を確認する。
まだ存在しないC3T1/C3T2の本export結果、native parity、全PC回収はこの小規模受入で完了とは扱わない。
