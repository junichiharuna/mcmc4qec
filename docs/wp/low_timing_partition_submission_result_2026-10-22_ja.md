# 分割workerの単発qsub投入と台帳待機：受入結果

[小仕様](low_timing_partition_submission_spec_2026-10-22_ja.md)に従い、runner v2と単発投入処理を実装した。
新しい数値計算・本番入力準備・実qsub投入を完了したものではない。
既存controller・投入済みjob・公開パッケージは変更していない。

runner v2は実PBSのR状態・script・資源・hostを確認してから、当該jobの台帳が保存されるまで最大30秒待つ。
欠落・書込途中のJSONだけを待ち、一致しない完全な台帳は直ちに拒否する。
同じjobの継続処理であり、timeoutを再投入許可として扱わない。
受入は33 testが成功し、[保存source](data_tile_validation_2026-10-17/low_timing_partition_runner_acceptance_v2/)からの再実行は33 passed・5.14秒だった。
受入manifestのSHA256は `b39a353b031a050ec1bfc77d4f1f218f3157a6fbc491326db2967c672de37ae0` である。
v1のsource・受入・クラスタbootstrap記録は保持し、v1の実環境確認をv2の実環境実行済み証拠として流用しない。

投入処理は準備receiptと全workerの固定成果物、source・入力・resolved pathを照合し、既存の共有lockをexclusiveに取得する。
同一ownerのQ・Hを含む非終端jobの要求node合計を数え、新規1nodeを加えて2以下の場合にだけ `qsub <script>` を呼ぶ。
qstat異常、不明な資源、旧coordinator稼働、他のlock所有者がある場合は投入しない。
intentを保存した後にもgateを確認し、timeout・非ゼロ終了・複数job ID・空応答・qsub中の固定入力変更は、応答と予約を残して自動再投入を防ぐ。
投入前の安全な停止や正常な台帳保存後だけ、自分が取得したlockを解放する。
CLIの既定はdry runで、実投入には `--execute` が必要である。

投入処理は実際の準備artifactを使い、schedulerとnative事前検査をdoubleに置き換えた35 testが13.56秒で成功した。
[保存source](data_tile_validation_2026-10-17/low_timing_partition_submission_acceptance_v1/)からの再実行も35 passed・15.14秒だった。
受入manifestのSHA256は `be8f58c3da70d3ecd4b131210fa5214c367a55ce1d3f251e39a73edee1857380` である。
初回のテストではsource変更の2項目が失敗し、環境とmanifestのsource closureを投入前後に直接照合する修正を加えた。
これらは投入制御の受入であり、実クラスタへの投入成功、全12条件の科学的受入、結合結果の正しさを認定するものではない。

実metadataは引き続き9/12条件で、分割経路を本番利用する判断は全12条件の資源評価後に行う。
実投入までには本番入力準備と経路の接続が必要であり、結合ジョブ・後続censusへの接続も未完了である。
独立計時・全体の計算効率評価・日本語最終報告は完了していない。
