# 独立計時の投入・監視

## 契約

準備済みの全48行を読み、対象条件のcapacityを既存submitterからqsubする。
既存submitterの共有lock、実scheduler再照会、待機中を含む最大2ノード制約を維持する。
1ジョブへの投入試行は1回とし、不明応答や投入時競合では自動再投入しない。
観察時の通信障害は同じjob IDへの再照会で扱い、ジョブ終了と見なさない。
capacity終端は固定済み後処理helperへ渡し、準備できたmain partitionを同じ投入キューへ追加する。
replicate0〜191の分割、2件のcapacityとの区別、科学的な設定は元planを維持する。
非ゼロ終端と資源計画不能も全48行に残し、mainを実行していない条件は192件の未実行を保持する。
mainの終端回収はPBS・manifest・submissionの証拠を保存する段階であり、raw payloadの最終科学検証は後続のPBS集計で行う。
対象0件のno-opは投入せず、その状態を保存する。
全ジョブの終端回収が終わっても、独立計時の精度・被覆・計算効率の検証完了とは扱わない。

## 受入

全48行の保持、対象capacityだけの投入、最大2要求ノード、同じjob IDの再観察、投入試行の重複禁止を確認する。
capacityがreadyとなった場合のみmainを追加し、重複・欠落したreplicate分割は拒否する。
capacity非ゼロ終了とmain非ゼロ終了を成功測定へ置き換えない。
元wrapperとPBSを模擬化した接続テストと、本番投入・計時を区別して保存する。

## 受入と待機開始

Windows20件・0.84秒、Linux20件・0.09秒で接続テストが成功した。
固定済みcapacity後処理helperを実際に読み込み、計時不能時にmainを作らない経路も確認した。
科学的な読み取り・PBS境界はmock化しており、本番capacity・mainの実行証拠ではない。
source・試験ログは `data_tile_validation_2026-10-17/low_independent_timing_execution_acceptance_v1/` に保存した。
manifestのSHA-256は `14a2ff762054fb46a76b9692d9de0c7ce262e5e34902dee215e4a7993fdb4c63` で、保存した14ファイルを再照合した。
待機driverをsession39834で開始し、正式な独立計時入力の準備完了を待っている。
本番投入・計時と、raw payloadを検証する最終集計への接続は残る。
