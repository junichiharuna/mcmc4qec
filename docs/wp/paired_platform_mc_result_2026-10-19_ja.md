# DGX SparkとLabo PCのBP-OSD判定比較

同じ物理誤り状態を両PCで復号し、16条件・各65536試行、合計1048576対を比較した。
全ての物理状態が両環境で一致することを生配列で確認した。
各環境256 chunkが完了し、例外・欠測・限定checkpointのfailure照合不一致は0だった。
11件の受入テストを通した固定driverで実行し、試行数を結果に応じて変更していない。
事前仕様は[固定予算仕様](paired_platform_mc_spec_2026-10-19_ja.md)、生データと環境は[data directory](data_paired_platform_mc_2026-10-19/)に保存した。

## 結果

失敗数はDGX / Laboの順であり、不一致は同じ状態に対するfailure booleanの不一致数である。
sector不一致はlogical residual vectorが異なる状態数であり、両環境でfailure trueとなる場合も含む。

| 符号 | noise | p | DGX失敗数 | Labo失敗数 | failure不一致 | sector不一致 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| tile72 | bit | 0.03 | 2815 | 2839 | 1066 | 1330 |
| tile72 | bit | 0.01 | 179 | 176 | 97 | 106 |
| tile72 | bit | 0.003 | 7 | 8 | 5 | 5 |
| tile72 | bit | 0.001 | 0 | 0 | 0 | 0 |
| tile288 | bit | 0.05 | 1941 | 1988 | 961 | 1713 |
| tile288 | bit | 0.01 | 0 | 0 | 0 | 0 |
| tile288 | bit | 0.003 | 0 | 0 | 0 | 0 |
| tile288 | bit | 0.001 | 0 | 0 | 0 | 0 |
| tile72 | depolarizing | 0.03 | 1992 | 1976 | 1002 | 1141 |
| tile72 | depolarizing | 0.01 | 117 | 117 | 80 | 81 |
| tile72 | depolarizing | 0.003 | 5 | 7 | 4 | 4 |
| tile72 | depolarizing | 0.001 | 0 | 0 | 0 | 0 |
| tile288 | depolarizing | 0.05 | 194 | 195 | 9 | 14 |
| tile288 | depolarizing | 0.01 | 0 | 0 | 0 | 0 |
| tile288 | depolarizing | 0.003 | 0 | 0 | 0 | 0 |
| tile288 | depolarizing | 0.001 | 0 | 0 | 0 | 0 |

主な4条件のfailure不一致率は次の通りである。

| 条件 | 不一致率 | LER差 DGX−Labo（percentage point） | 差の区間（percentage point） |
| --- | ---: | ---: | ---: |
| tile72 / bit / p=0.03 | 1.6266% | -0.03662 | [-0.28176, +0.20853] |
| tile288 / bit / p=0.05 | 1.4664% | -0.07172 | [-0.30459, +0.16119] |
| tile72 / depolarizing / p=0.03 | 1.5289% | +0.02441 | [-0.21338, +0.26220] |
| tile288 / depolarizing / p=0.05 | 0.0137% | -0.00153 | [-0.02746, +0.02443] |

失敗判定が異なる状態は、片方だけ失敗する方向が両方あるため、不一致率とLER差は異なる量である。
今回のLER差の区間は16条件全てで0を含み、両環境のLERが等しいことを証明したものではない。
区間は各条件6個・全16条件の96個の二項countに対するClopper–Pearson区間をBonferroni補正したfamily 95%である。
LER差の区間は、DGXだけ失敗した率とLaboだけ失敗した率の区間を差し引いて構成した。
iid試行と環境内で固定されたdecoderを前提とし、限定checkpointだけで決定性を証明したとは扱わない。
不一致0件の条件でも率が0とは言えず、今回の補正済み区間の上限は約0.01259%である。
低pの多くの条件は両環境とも零失敗であり、直接MCで十分な失敗数を得た校正とは扱わない。

## 解釈と利用上の制約

単一fixtureに限らず、今回のiid sampleでも環境間で失敗と判定される状態集合が異なることを確認した。
Python 3.11.17、numpy 2.4.6、ldpc 2.4.1、pymatching 2.4.0、bposd 2.1とpackage source hashは両環境で一致する。
OS、CPU architecture、native binaryは異なり、原因はこの比較では分離していない。
各chunkにfresh decoderを作り、chunk内で目標priorを固定した。
depolarizingではjoint Pauliをsampleし、sector decoderのpriorを2p/3にした。
BARの同一ladderに異なる環境のdecoderを混在させたり、今回の個人機結果を既存クラスタのreferenceへ無条件に合算したりしない。
環境を変えて計算を分担する場合は、その環境に対応するreferenceとfailure定義の検証を維持する。
この比較はMCMCの混合・BARのbiasや被覆を校正したものではない。
GPUは使用しておらず、速度benchmarkとして追加実行したものでもない。
記録した所要時間は処理の追跡用であり、クラスタとの性能比較や同精度到達時間の結論には用いない。

## 再現と保存物

[集計JSON](data_paired_platform_mc_2026-10-19/comparison_v1.json)に16条件全てのcount・区間・入力証拠を保存した。
[集計スクリプト](data_paired_platform_mc_2026-10-19/compare_v1.py)は両環境の全515成果物のhash・サイズ、plan、seed、全状態配列、sectorとfailureの対応を照合する。
[source manifest](data_paired_platform_mc_2026-10-19/sources_v1/manifest.json)に固定driver、受入テスト、red/greenログ、事前仕様を保存した。
driverのrunは既存出力先を拒否するため、再計算時は新規ディレクトリを使い、既存結果を上書きしない。
同じ固定wheelと依存versionの環境で、driverへ `--source <展開した候補source> --output <新規出力先> --workers <CPU worker数>` を渡す。
本driverは個人機の固定環境用であり、任意versionでの再現を自動保証するものではない。
今回の計算ではDGX20 worker、Labo24 workerを用いた。
公開候補915ファイルと固定配布物の外側に保存した追加証拠であり、公開候補のcommit・push・releaseは別工程として残る。
