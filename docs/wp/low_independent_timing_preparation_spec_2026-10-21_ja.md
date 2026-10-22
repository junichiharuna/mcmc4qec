# 低ノイズ独立計時の入力・capacity準備

## 固定仕様

新旧seed全数監査が正式に完了したdescriptorを既存execution.inputsで受理してから、独立計時の準備へ進む。
4 case・3 target・2精度目標の24行を、MCとBARの両方について残す。
元planで選択されなかった行や、計時予算を作れなかった行を除外しない。
eligibleな行だけ、既存runnerのprepareを使ってcapacity用の2 full estimatorを準備する。
capacityの2 replicateとbenchmarkの192 replicateは元のseed区分を維持し、capacityを評価データへ混ぜない。
元のtrace長、burn-in、chain数、ladder、誤差法、MC予算を変更しない。
mainの資源と分割はcapacityの実測後に既存resource_planで決め、準備段階で性能や完走を保証しない。
seed監査がno-opの場合は独立計時も未実行のno-opとし、正式監査のdescriptorを捏造しない。
本準備はqsubを行わず、容量測定の実行driverが共有lockと最大2ノード制約を維持して投入する。

## 受入

4 role・各24行の順序・件数・identityと、MC/BAR・capacity/benchmarkの選択状態の一致を確認する。
部分集合、重複、別精度目標、roleごとの選択違いを拒否する。
準備結果のtaskが指定identityのreplicate0・1だけであり、元capacity資源と一致することを確認する。
元configの科学bundle・selection・registry・census・native入力のpinを保持する。
全対象の準備に成功するまで完了receiptを作らず、失敗した出力rootを再利用しない。
mock境界の接続テストと、本番seed監査後の実準備を区別して保存する。

## 受入と待機開始

Windows18件・0.76秒、Linux18件・0.08秒で接続テストが成功した。
全48行の保持、4 role間の選択一致、capacityのreplicate0・1、benchmarkの192 replicate、既存capacity資源、no-opと元科学bundleの対応を確認した。
既存execution.inputs・prepare・read_plan・bundle_bindingは本受入ではmock境界であり、正式seed監査後の実資源測定の準備や実行ではない。
sourceと実行ログは `data_tile_validation_2026-10-17/low_independent_timing_preparation_acceptance_v1/` に保存した。
manifestのSHA-256は `085a323774f2ba31e661b8b0d8d0ada0469bfa7cd06fd2a3e1d169f9f4cfe1c3` で、保存した10ファイルを再照合した。
driverをsession72330で開始し、正式censusの完了を待っている。
capacity・mainの本番投入と実測、実測後の分割・集計への接続は残る。
