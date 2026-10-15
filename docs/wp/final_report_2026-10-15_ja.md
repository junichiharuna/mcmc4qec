# 残課題への対応報告（2026-10-15）

## 到達点

ユーザーの依頼によりtoric高速化を優先し、混合・被覆の校正、物理回路の差分更新とH提案、非公開ヘルパーを含むstrict型検査を並列に進めた。
開始HEADは `35ed7f3`、版番号は0.1.0.dev5のままであり、以下は未コミットの開発差分である。
公開sampling既定、BARの既定誤差法、ライセンス、引用情報、公開状態は維持した。
commit・push・publishは実施していない。

| 項目 | 結果 | 残る限界 |
| --- | --- | --- |
| toric高速化 | d5/d7の最終2反復とも研究runner比2倍以内 | 固定環境・p・seedの短時間実測であり一般性能保証ではない |
| 混合・被覆 | block長だけを変える20seed×3群を実測し、exact被覆・IAT・ESS・R-hatを保存 | 95%被覆と混合改善は未達、広い符号・低p・長時間の校正は未実施 |
| 物理回路 | 既存効果tableの差分更新と明示location群のHを実装 | H単独は一般に可約、実符号での混合改善は未検証、stabilizerは非対応 |
| 型検査 | 新回路を含む26 sourceでmypy strict成功 | optional backendとJSON境界には明示的な動的型が残る |

## 高速化

混合CDFの事前構築、全密度総和を維持した重複support走査の削減、二値効果の直接XOR、failure集合外Z候補の逆分布正規化省略を実装した。
状態・受理・乱数消費と、公開proposeの順逆比を維持することを受入条件とした。
独立レビューでは極端supportの旧新2550 attempt、小状態全近傍の一般参照88 attempt、toric d3/d5/d7の旧新1800 attemptが一致した。

| 符号 | 変更前の研究runner時間比 | 最終時間比 | ライブラリ平均時間短縮 |
| --- | ---: | ---: | ---: |
| toric d5 | 2.603–2.605 | 1.873–1.915 | 25.5% |
| toric d7 | 2.506–2.549 | 1.925–1.941 | 22.6% |
| BB72 | 1.549–1.619 | 1.295–1.330 | 13.7% |

最終計測は他担当のCPU実験完了後、p=0.01、10000step、seed731、Z/H=0.7/0.3、k=2、1chain、lazy0の2反復である。
ライブラリ時間は結果と診断を含み、decoder構築は含まない。
詳細は [性能記録](../performance_ja.md)、[生データ](data_speed_2026-10-15/README.md)、[独立レビュー](speed_review_2026-10-15_ja.md) にある。

## 混合・被覆の校正

toric d3、固定unweighted MWPM、p=0.22、exact anchor、4chain×保存600、burn180、100 bootstrap反復を固定し、block長8/32/128をseed6100–6119で比較した。

| block長 | exact被覆 | 平均区間幅 |
| ---: | ---: | ---: |
| 8 | 12/20 | 0.049634 |
| 32 | 16/20 | 0.073329 |
| 128 | 16/20 | 0.076132 |

3群の同seed点推定と記録診断は一致し、block長だけを変えることで区間への影響を分離した。
全rung・全chainの最大IATのseed中央値は37.73、target ESS中央値は156.61/2400、split R-hat最大は1.07798だった。
block変更はsampling軌道の混合自体を改善せず、今回も名目95%被覆を保証できないため既定は変更しない。
計測は開始HEADのpackageで行い、統合後の高速化sourceによる再計測とは区別する。
全60行・事前計画・環境・exact再列挙cache・集計scriptは [校正記録](calibration_2026-10-15_ja.md) にある。

## 回路と型検査

回路専用stepは既存の物理fault効果tableとZ分布を再利用し、変更locationだけのsyndrome/observable差分を計算する。
Hは `KernelConfig.circuit_groups` で互いに素なlocation群を明示し、群内のchannelと順序付きfault alphabetの一致を要求する。
不可能な提案枝は自己遷移とし、非一様率・零support・共有failureのMH評価を維持する。
独自failureと派生型は一般経路へ戻し、正のlazyと連結性を区別して検証した。
回路の受入・独立レビューは [実装記録](circuit_2026-10-15_ja.md) と [レビュー](circuit_review_2026-10-15_ja.md) にある。

非公開ヘルパーを含む型注釈を追加し、既定設定・CI・型テストを `mypy --strict` に変更した。
全体のimport検査免除を外し、optional backend名前空間とldpcのimplicit re-exportだけに例外を限定した。
新規回路2moduleを統合後、26 source全体のstrict検査に成功した。
詳細は [型検査記録](typing_2026-10-15_ja.md) にある。

## 統合検証

研究照合env付きの全source suiteは394 passed、skipなし、188.05秒、file別合計時間最大22.238秒で、全suite300秒・各file60秒の制限内だった。
Windows notebookのzmq event-loop代替threadに関する環境warningが1件あり、失敗はなかった。
wheelはビルド成功し、既存の隔離core/optional環境へ依存を変更せず再installした。
core installed wheelは271 passed /76 skipped、78.84秒で、verify_wheel coreも成功した。
全26 Pythonファイルとtype markerがsourceに一致し、core実行例と文書コードを確認した。
optional installed wheelは389 passed /5 skipped、206.97秒で、Windows notebookのzmq環境warningが1件あった。
5skipは研究checkoutを指定しないlive照合であり、sourceでは実行済みである。
verify_wheel optionalも成功し、全20実行例・4quick notebook・文書コードを確認した。
全suite300秒、各file60秒の制限を3環境とも満たし、optionalのfile別最大は22.280秒だった。
実行ログ・package/wheel fingerprint・時間の集計は [検証データ](data_validation_2026-10-15/README.md) に保存した。
remote CIは未実施であり、pushを行っていないため今回の差分のremote成功は主張しない。
分担用の3worktreeは統合後source全suiteの成功を確認し、変更ファイル全54個とdiffの退避・SHA照合・削除対象絶対パスの確認後に削除した。
分担差分の退避先は `output/dev6/worktree_snapshots/` であり、最終変更はmainの未コミット差分として残っている。
handoffは既存byte prefixを維持して実施結果だけを追記し、研究runnerのhashは最終監査時も計測時と一致した。
研究側のpaper/main.texとpaper/refereeには別作業の変更が観測されたため、研究repo全体をcleanとは記録せず、本作業では一切変更していない。

## 次に残る課題

長いtrace・多数seed・別の実符号と低p領域での被覆校正、複数観測量による混合評価、回路Hの実符号での効果評価を残す。
今回のtoric速度達成を、他の設定や機器への性能保証とは扱わない。
PyPI等への公開、リポジトリの公開化、所属・DOI・release情報は引き続き所有者判断である。
