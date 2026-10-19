# 回収archiveからのgroup読取り：小仕様

全cohort providerの構成要素として、既存の転送検証を再利用しつつ、保存artifactを再読取りするreaderを追加する。
公開候補と稼働中の計算driverは変更しない。

1. 親が固定したreceipt・parent binding・collector sourceに対してarchive全memberを検証する。
2. 保存したexecution intent、終端summary、collection reportのhash・runtime・source・production manifest・group集合を相互に照合する。
3. source変換の記録とsampling native profileを固定した入力に照合する。
   profileの生ファイルのSHA-256と、planが持つcanonical JSONのdigestは別々に検証する。
4. archive内のsource payloadもparentのsource hashに一致させる。
5. 成功groupはcompletion・JSON・NPZ・markerの4ファイルを持ち、hashとidentityが一致し、未知groupを含まないことを要求する。
6. 読取り時にもmember hashを照合し、NPZはpickleを許さず読み込む。
7. 元samplingのrecord・anchorを呼出し側から渡し、既存の`validate_group`で全設定行、sampling failure、診断、ACF、summaryの計数を再検証する。
8. infrastructure failureの部分出力は成功として読まず、失敗理由を保持する。
9. 最後にarchive全体のhashが変化していないことを確認する。
10. このreader単独では全768群の完了、host割当、全設定の移植照合、native trace監査、独立reference結合を証明しない。

受入テストは実producerの小さいfixtureで成功・sampling failure・anchor failure・infrastructure failureを扱い、payload、source、runtime、intent、marker、設定行、診断の改変を拒否する。
改変テストでは外側のarchive hashを更新しても内側の不整合を検出することを確認する。
実cohortへの適用は元sampling recordを伴う検証として実施し、単なる保存済みreportの再表示と区別する。
