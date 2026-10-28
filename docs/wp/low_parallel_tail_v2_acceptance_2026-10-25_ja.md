# 全12条件の後続処理の受入

`output/low_parallel_tail_v2` の受入テスト17件は、qsub 265528 で成功し、PBS の F・終了値0を確認した。
親環境と報告環境の実 bootstrap、および census の実 source closure は、qsub 265530 で成功し、F・終了値0を確認した。
265530 の経過時間は8秒であり、trace 読み取り・再計算・独立計時は実行していない。
両ジョブの記録と17件のログは [parallel_tail_acceptance_v2](data_tile_validation_2026-10-17/parallel_tail_acceptance_v2/accepted.json) に保存した。
公開用記録ではホームパスを `$HOME` に置換し、PBS サーバー接尾辞を除去した。
記録した SHA-256 は置換前の原本を指し、公開用 JSON 自体の hash とは区別する。

実行設定は `$HOME/workspace/mcmc4qec/20261025-low-parallel-tail-v2/tail-config.json` に保存し、SHA-256 は `a5deb2b4f69f990b0a1772c28ac83a6e760903af330d9074f00a87248415e752` である。
元 driver と helper の31ファイルは既存 controller envelope に照合し、adapter の8ファイルは成功済み受入の source pin に照合した。
元 merge 検証器・科学的選択規則・独立計時の内容を変更せず、承認済みの isolated 配置検証の差分を census と報告環境へ引き継ぐ。
新しい待受はクラスタ内に置き、元の qsub と最大2ノード制御を維持する。

この時点では後続処理を起動していない。
全12 worker の正しい割当と比較結果を versioned merge が受理した後に、新しい handoff から census・独立計時・最終報告へ進む。
受入テストと環境検証の成功は、科学計算の完了、名目被覆、低ノイズ精度の保証を意味しない。
