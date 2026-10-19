# DGX batch 5の準備と引継ぎ

2026-10-20 00:34 JST時点の記録である。
完了入力が揃う前の予約は行わず、固定host割当の20群が揃ってからDGX batch 5を準備した。
対象はC0T2 group `(0,2,1,0,20..31)` と `(0,2,1,0,56..63)` であり、推定値や診断結果を選択に使用していない。
入力archiveは278687079 byte・14577 memberで、SHA-256は `5c4aed914c542c540370d12a9445c4ac52c898536f030c72ddaa6879a5b4f65c` である。
export manifestのSHA-256は `25ddafa3382c55f920a0a243aa63c87639bb7a6f941b291c0e912f0a22ddb3b3` であり、元sampling・固定group・sourceの照合とDGXへの配置を完了した。
batch 5の本計算はまだ起動していない。

local controller PID 39216が、実行中のbatch 4のremote PID 643186を確認し、終端・回収・archive検証を経てbatch 5を起動する。
batch 4の回収準備ではexecution intentを `a95b585691a0f76c5b0d53a7621bcbc6dbb76f48aad3500def281ff7cb65f922` に固定している。
同一hostの本計算を重複起動せず、既存のhandoffを再実行しない。

[予約集合の検証](data_portable_bar_2026-10-19/batch5-preparation-verification-v1.json)では、DGX 120群・Labo 96群、計216群に重複がなかった。
未予約は552群であり、予約数と回収済み80群は区別する。
全768群の監査・reference比較は未完了である。

旧DGX batch 2・3を保持していた終了済みのterminal sessionは正常終了を回収した。
その後batch 5用の引継ぎcontrollerを追加したため、現在のbackground terminalは計算接続3本と回収・後続起動待ち2本である。
クラスタのqsub jobは既存2本を維持し、今回の配置・引継ぎによる追加投入はない。
