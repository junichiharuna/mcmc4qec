# C1T0最終集計の設定作成

稼働中の全38 batch回収・独立index・転送と、復旧full監査の両方が正常に完了してから最終設定を作成する。
既存の復旧reader・qsub wrapper・公開候補・稼働中driverは変更しない。
最終設定の作成処理を別配置に置き、入力receipt、source census、元venv、native reference、復旧authority、full監査の実PBS終端を照合する。
転送先contextの全metadataと、復旧監査plan・terminal・旧成果物の入力hashを設定に含める。
元のqsub wrapperによるread_config・prepare・execute=Falseのpreflightを使い、独自の簡略検査だけで投入可能とは判定しない。
actual contextまたはfull監査が未完了の場合、本番config・job directoryを作らない。
hash不一致・別条件・失敗終端・二重実行の場合は停止し、自動再試行しない。

資源要求は1 node・1 CPU・32 GB・12時間を初回上限とする。
根拠として、同種の最終readerを使ったC0T2の正常PBS終端265366、実測33分55秒・最大resident memory 1,320,352 KiBを保存する。
tile288の最終処理は未計測であるため、この実測を直接ETAへ換算しない。
32 GBは先行処理と同じ要求であり、12時間はより大きい符号と入力I/Oの未計測分を見込む保守的な上限で、所要時間の予測ではない。
上限超過時は実ジョブと失敗記録を確認してから再設計し、同じ予約へ再投入しない。

受入では、正常転送とfull監査の両方の必要性、別destination、失敗・複数回実行のPBS終端、metadata path逸脱、重複hashの矛盾を検査する。
本番前に元クラスタvenvでimportと固定source照合を行い、設定作成時には全入力を改めて照合する。
この設定作成自体はqsubを行わず、投入は既存wrapperの共有lockと最大2要求ノードの検査を通す。
metadataの準備成功をraw trace再監査・科学的受理・最終report完成とは扱わない。

全回収後の転送driverとfull監査driverの正常完了を待つlocal引継ぎを追加する。
どちらかが未完了なら待機し、error記録があれば停止して、既存処理を再起動しない。
両方が完了した時点でreceiptとfull監査の受理結果を固定し、上記の実metadata設定作成を一度だけ呼ぶ。
引継ぎ自体はqsub・最終reader・report回収を行わず、設定作成の成功または失敗を記録して終了する。

## 実装・検証と現在の状態

`output/c1t0_final_preparation_v1/preparation.py` を実装し、Windowsで18 passed・0.58秒、元クラスタvenvで18 passed・0.05秒だった。
クラスタ上の別配置 `20261020-c1t0-final-preparation-v1` で、元venv・135個の配置済みreader source・復旧auditのbootstrapを照合した。
これはimportとmetadata契約の検査であり、未完了のfull監査や全群contextを使って最終設定を作成した結果ではない。
[受入manifest](data_tile_validation_2026-10-17/c1t0_final_preparation_acceptance_v1/manifest.json)のSHA-256は `77d05e9f159655602bd5a387e5c4dec6bdd5432b53438281cee41b6fc8a60ef7` である。

`waiter.py` の受入はWindowsで6 passed・0.63秒、Linuxで6 passed・0.04秒だった。
実際の先行driver 2本とintent、元venv・配置済みcontrolの受理記録など10入力を照合し、両方の完了がまだ揃っていないことを確認した。
[待機処理の受入manifest](data_tile_validation_2026-10-17/c1t0_final_preparation_waiter_acceptance_v1/manifest.json)のSHA-256は `848b21b0197f13621b9504e8355e0754d95b6f459cb7f528e0d40104abd64003` である。
23:36 JSTにlocal PID34812で引継ぎを起動し、23:37 JSTのpollで継続中を確認した。
[開始intent](data_tile_validation_2026-10-17/c1t0_final_preparation_handoff_v1/intent.json)と同directoryのobservationsに待機状態を保存する。
sourceは起動時のhashに固定し、稼働中に変更しない。

本番final config作成・preflight・qsub・最終report生成・回収はまだ未実施である。
引継ぎが設定作成を終えた後も、qsubへの接続と最終report回収が必要である。
23:44 JSTまでに、後続の[qsub・正常終端確認・回収の引継ぎ](c1t0_final_execution_handoff_spec_2026-10-20_ja.md)を別driverとして実装・検証し、起動した。
この後続driverも現在は設定作成の正常完了待ちであり、本番投入・回収が完了したことを意味しない。
