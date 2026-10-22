# 最終回収から独立算術レビューへの接続

C1T0・C1T1・C1T2・C3T0・C3T1・C3T2を対象とする。
既存の最終実行・回収・metadata候補・計時driverは変更しない。
正常回収のcompleted記録、receipt、report、入力転送の完了記録とtransfer planを結び付ける。
最終実行にerror記録がある場合は、その条件の独立レビューを実行しない。
未完了や書込途中のcompleted JSONは待機し、完成した記録の矛盾は失敗として保存する。
入力のcondition・remote root・job ID・report hash・receipt hash・transfer plan hashが一致しなければ拒否する。
実行直前に既存のcandidate組立helperを用い、元snapshot validatorで回収成果物の整合を再確認する。
helper・reader・算術sourceは受入済みhashで固定する。

各条件の新規出力先に一度だけ実行要求を保存してからreaderを呼び、stdout・stderr・return codeと出力manifestを保存する。
入力とsourceを前後で再照合し、失敗や中断の後に同じ出力先を自動再使用しない。
ある条件の失敗を他条件の成功に置き換えず、他の正常な条件の処理は継続する。
sampling、復号、BAR、bootstrap、独立計時、qsubは実行しない。
この独立算術レビューは追加照合であり、既存の数値検証pipelineを停止させる依存関係にはしない。
実データ未回収時の受入は模擬回収と模擬childによる接続試験であり、本番レビューの成功とは区別する。

## 受入と起動

未実装によるimport失敗を記録してから実装し、Windows Python 3.11で22テストが1.23秒で成功した。
6条件のpath対応、未回収・書込途中・元実行失敗、report・receipt・転送planの改変、異なるremote root・job・receipt path、失敗時の一度だけの呼出し、成功childのreport pin・condition・出力manifestを検査した。
元snapshot validatorと実算術childの実行は接続テストでは模擬化している。
算術reader自体の全67,584行を使う別の合成受入は先に完了しているが、どちらも本番回収データの照合ではない。
実source 7ファイルのpinが一致し、6条件すべてのreadinessがpendingであることを確認した。
source・仕様・ログ・環境は `data_tile_validation_2026-10-17/planned_arithmetic_handoff_acceptance_v1/` に保存した。
`accepted.json` のSHA256は `72b10564b109975dda0fc83f83821eb448b970b8d85b49ba14b8c27b980dba19`、実行sourceのSHA256は `07f909c61fc4950b3fb6b09a1ed13c49e67717f9d9548806ee454531e2b8fa5f` である。
待機処理をPID27868・session76495で開始し、06:46 JSTに実handleの継続を確認した。
記録先は `data_tile_validation_2026-10-17/planned_arithmetic_handoff_v1/` である。
本番の独立算術レビューは未実施であり、新規qsubも行っていない。
