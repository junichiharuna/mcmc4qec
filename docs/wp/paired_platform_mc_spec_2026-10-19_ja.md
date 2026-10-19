# 個人機間のBP-OSD判定比較：固定予算仕様

既知の単一状態の環境差がcode-capacityでどの程度現れるかを調べる。
同じ固定wheelを使うDGX Spark/Linux aarch64とLabo/Windows x86-64で、同じ独立誤り状態列を復号する。
GPUとMCMCは使わず、速度benchmarkを目的としない。
既存クラスタcohortへ結果を追加しない。

tile72/288 × bit-flip/depolarizingの4 caseで、mainのp=(0.03,0.05,0.03,0.05)と各caseの低p=(0.01,0.003,0.001)を合わせた16条件とする。
各条件16 chunk × 4096 iid試行、65536試行を固定し、1環境につき1048576試行を行う。
結果を見て試行数を増減しない。
各chunk内で目標pに固定したBP-OSDを一度作り、max_iter=100・min_sum・scaling=1・parallel・osd_cs・order=10を維持する。
depolarizingはjoint Pauliをsampleし、各sectorのdecoder priorを2p/3にする。
既存tile_study.build_problemとnoise.sampleを使い、相関Pauliを独立sectorノイズへ置き換えない。

両PC共通のnamespace `mcmc4qec-personal-paired-platform-20261019-v1` と条件番号・chunk番号のcanonical JSONをSHA256にし、256bit整数をPCG64へ渡す。
256 seedの重複と64bit範囲との非交差を事前確認する。
これは保存済みの64bit seedと同一整数を使わない確認であり、擬似乱数列の数学的独立性の証明ではない。
物理状態、logical sector、failure labelを各chunkに保存し、両環境で物理状態が全て一致する場合のみ対比較する。
default failureはobserved XOR predictedのいずれかが非zeroであることとし、独自predicateは拒否する。
各chunkの先頭・末尾でProblem.is_faultyとの照合を行い、不一致は失敗として記録する。
この限定照合を全状態での決定性の保証として扱わない。

環境ごとの失敗数、failure判定不一致数、logical sector不一致数、片側だけ失敗した数を報告する。
各条件の6個の二項count（両環境の失敗・failure不一致・sector不一致・両方向の片側失敗）に対し、16条件を合わせた96個のClopper–Pearson区間をBonferroni補正したfamily 95%として計算する。
LER差の区間は両方向の片側失敗率の区間を差し引き、pairingを保持する。
独立試行・固定されたdecoderを前提とする区間であり、有限seedや限定的な決定性検査だけで前提を証明しない。
零失敗、未完了chunk、例外、診断不一致を隠さず、未完了条件に正式な区間を付けない。
低pで失敗数不足となる可能性を許容し、これを既存WSS referenceの代替とは扱わない。

小規模受入ではseed固定、default failureとsector対応、joint Pauli状態の保持、異なる状態列・欠測・重複chunkの拒否、零countの区間、対比較の向きと区間を確認する。
科学処理の実行前に仕様・受入テスト・実装を揃える。
source・wheel・package・native binary・plan・seed・raw成果物のhashと環境を保存し、同じ出力先への暗黙の再実行を拒否する。
