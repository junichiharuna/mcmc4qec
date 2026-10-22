# 計時の後段を親環境v4へ接続する

## 問題

親準備とcensus準備はv4環境を使うが、待機中のcensus実行・独立計時入力準備・独立計時実行の3 driverはv2環境を固定していた。
census実行の `control.context` は準備receiptの環境hashとlocal環境hashの一致を要求するため、このままではv4の正常な準備結果を受け付けない。
独立計時実行にも同じ固定hashの比較がある。
まだ各処理は入力待機中であり、新しい計算や投入を行ったという意味ではない。

## 変更範囲

旧sourceを保持して別版v2のdriverを作成し、親環境path/hashを受入済みv4へ固定する。
既存の出力先と後段が読む完了契約は保ち、旧intentとobservationsを保存して版別の引継ぎmarker・intent・observationsを追加する。
科学計算、seed、48 method行、no-opの扱い、capacityとmainの順序、資源上限、qsub・共有lock・最大2node、投入応答不明時の再試行禁止を変更しない。
selector実行は準備receiptから環境を受け取るため、古い検証時環境を理由に稼働sourceを書き換えない。
reportは独立した検証済み環境を持つため、環境名だけを理由に置き換えない。

## 受入

先に実環境の不一致を再現し、新しい3 driverがv4を固定するテストを用意する。
既存の失敗・no-op・曖昧応答・正常完了・2node制御の受入を維持する。
引継ぎの改変・重複・着手済み出力を拒否し、待機中に計算を始めないことを確認する。
WindowsとクラスタLinuxで小規模の制御テストを実行し、native環境のbootstrapと科学moduleの対応を確認する。
切替直前に旧PID・実command・生成時刻・source不変・計算子processなし・待機出力のみを確認し、旧履歴を保存する。
切替後は新processの実生存と待機状態、旧履歴のhash不変を確認する。
この受入を本censusや独立計時の完了とは扱わない。

## 最終報告環境の追加確認

報告環境v1は独立計時の記録済みPYTHONPATHを保存するため、親環境v2のPYTHONPATHを固定していた。
独立計時の `current_runtime` はPYTHONPATHの完全一致も要求するので、新しいv4で計時した結果を旧報告環境で受け入れることはできない。
検査を緩めず、既存の報告readerだけを上書きするimport構成をv4親環境に重ねた別環境v2を作成する。
報告reader・計時コード・選択規則・reference・native binaryを変更せず、実クラスタで元の計時runtime snapshotを受け入れることを確認する。
報告準備と報告jobの待機係の切替は、この環境受入と新sourceのテスト後に行い、旧環境と旧履歴を保存する。
