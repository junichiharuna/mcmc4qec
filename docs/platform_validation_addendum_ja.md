# BP-OSD環境差の追加検証

experimental版のsource snapshot固定後に、DGX SparkとLabo PCで同じ物理誤り状態1048576対を比較した。
packageや既定設定は変更していない。
tile72/288・bit-flip/depolarizingの16条件を各65536試行で調べ、両環境とも256 chunkが欠測なく完了した。
全状態配列の一致を確認してから対比較した。

| 条件 | failure判定不一致 / 65536 | 不一致率 |
| --- | ---: | ---: |
| tile72・bit-flip・p=0.03 | 1066 | 1.6266% |
| tile288・bit-flip・p=0.05 | 961 | 1.4664% |
| tile72・depolarizing・p=0.03 | 1002 | 1.5289% |
| tile288・depolarizing・p=0.05 | 9 | 0.0137% |

両方向に片方だけ失敗する状態があるため、判定不一致率と論理誤り率の差は異なる量である。
今回の論理誤り率の差の区間は全16条件で0を含み、両環境の率やfailure集合が等しいことを証明しない。
区間は96個の二項区間をBonferroni補正したfamily 95%であり、iid試行と環境内で固定されたdecoderを前提とする。
限定checkpointでの再確認だけでは決定性を証明しない。
低ノイズの零失敗条件は精密なreferenceとして扱わない。

Python・依存version・package source hashは一致するが、OS・CPU architecture・native binaryは異なり、原因は未分離である。
BARのladderとreferenceではdecoder設定・目標prior・native環境を固定し、今回の結果を既存クラスタcohortへ無条件に合算しない。
この比較をGPU性能、クラスタとの速度比較、MCMC混合、BAR被覆の検証とは扱わない。

詳細は[日本語報告](wp/paired_platform_mc_result_2026-10-19_ja.md)、[事前仕様](wp/paired_platform_mc_spec_2026-10-19_ja.md)、[全条件の集計](wp/data_paired_platform_mc_2026-10-19/comparison_v1.json)に保存した。
追加検証ZIPにはこの実験の物理状態・sector・failure label・環境・driver・解析スクリプトを含む。
tile研究全体の全raw dataを含むものではない。
