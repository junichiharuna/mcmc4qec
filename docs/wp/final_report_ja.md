# 開発依頼書の最終報告（統合前の作成中）

## 1. 到達点

この文書は作成中であり、開発依頼の達成宣言ではない。
WP-A〜E の実装を作業枝で進め、B と E は担当範囲の独立レビューを通過した。
main は共通基盤、明示的な独立論理基底、公開契約と provenance を整備し、統合準備として version を `0.1.0.dev2` に更新した。
全 WP の main 統合、統合後の wheel 検証、push と remote CI は未完了である。
著者はユーザーが指定した `junichi haruna` で、公開化、publish、license の追加は行っていない。

## 2. WP ごとの実装・検証・レビュー

以下は各作業枝の記録であり、統合後の検証結果は第4節に別記する。
検証は指定 Python 3.11 を使用した。

| WP | 実装 | 実行した検証（コマンドと結果） | 未実施 | レビューの指摘と対応 |
| --- | --- | --- | --- | --- |
| A | 実符号ファクトリと MWPM/BP-OSD/sector wrapper、研究照合 | 担当3ファイルの pytest 66 passed、core-only 40 passed / 26 skipped；exact、MC、Z+H は第3節 | 最終変更後の全 suite と独立レビューの完了 | 正式第1回レビュー中；研究の非単位交差行列は明示 independent 指定で保持 |
| B | product ノイズの Z 高速経路、decoder cache、syndrome 差分 | `-m pytest tests -q` 169 passed、`tests/test_fastpath.py` 13 passed；列挙で q 最大差 1.11e-16、詳細釣合い差 0 | 研究速度の2倍以内 | cache の先行 uint8 cast を修正し、不正 decoder 出力の回帰試験を追加；profile による代替受入条件を確認 |
| C | 物理 location の排他 fault、Stim 効果の XOR、専用 MH と中点 logical idle | 初版の circuit 試験 13 passed、surface direct MC 比較を実施 | 第1回レビュー修正後の受入と第2回レビュー | 2ラウンド全 location の列挙、location 別分布、確率和検証を修正中 |
| D | README、API/tutorial、CI、CFF、追加例 | 枝の installed wheel 162 passed、CFF validate 成功、README/tutorial の実行 | 新公開名を含む統合後の全監査 | README の導入依存と BAR の状態数上限違反を修正し、公開 docstring 補完を main へ反映 |
| E | 複数 chain 診断、四条件、厳密な論理コセット最小化と初期化 | 第1修正後の全 suite 177 passed；最終 focused 16 passed、独立レビューでも16 passed | 統合後の全 suite と wheel | ゼロ分母、独立分散未指定、負相関 IAT、二盆地試験、MILP 最適性確認を修正し、第2回レビュー合格 |

## 3. 数値照合と性能

以下の値は WP-A/B の実測記録から転記したものであり、研究論文の図表再現や全領域の精度保証ではない。
詳細な条件と制約は統合後の `docs/crossval_research_ja.md` と `docs/performance_ja.md` に残す。

| WP-A 対象 | ライブラリ | 研究参照 | 比較と時間 |
| --- | --- | --- | --- |
| 符号12構成の hx/hz/lx/lz | shape と raw bytes の SHA256 | 研究ファクトリの同じ行列 | 全12構成一致；大きい符号の距離下界は独立証明していない |
| toric d=3、p=.01 exact P_L | 0.0020442815656133238 | 0.0020442815655904952 | 差約2.28e-14、ライブラリ44.19秒 |
| 同 exact E[w\|F] | 2.261042002778366 | 2.2610420028036122 | 差約2.52e-11 |
| toric d=5、p=.01 direct MC | 14/100000、P_L=.00014、Wilson [.0000834003,.0002350020] | CSV P_L=.0001419507468 | 参照値は区間内、21.95秒 |
| BB72、p=.01 direct MC | 166/100000、P_L=.00166、Wilson [.0014261085,.0019321771] | CSV P_L=.0018106462377 | 参照値は区間内、23.52秒 |
| toric d=5、p=.01 Z+H E[w\|F] | 3.77733、参考95%区間 [3.55680,3.99787]、ESS52.60 | CSV 3.784 | 参照値は区間内、15.21秒 |
| BB72、p=.01 Z+H E[w\|F] | 3.57433、参考95%区間 [3.38725,3.76142]、ESS65.56 | CSV 3.706 | 参照値は区間内、18.74秒 |
| 同一合成 trace の BAR log ratio | -1.213008448539711 | -1.2130084485394683 | 差約2.43e-13 |

Z+H は Z=.7、H=.3、k=2、1 chain、burn-in500、保存3000、lazy=.05 であり、参考区間は混合や被覆確率の証明ではない。
MC の条件付き平均は toric d=5 で4.0000、BB72で3.74699だったが、失敗数が少なく、比較の参考標準誤差には CSV の分散推定値を代入した。

WP-B のコマンドは `benchmarks/bench_step.py --steps 10000` で、双方 p=.01、Z=.7、H=.3、k=2、1 replica、ライブラリの lazy=0 とした。

| 符号 | ライブラリ秒 / step毎秒 | 研究秒 / step毎秒 | 時間比 |
| --- | --- | --- | ---: |
| toric d=5 | 3.950001 / 2531.6 | .221087 / 45231.0 | 17.87 |
| toric d=7 | 5.091820 / 1963.9 | .226044 / 44239.2 | 22.53 |
| BB72 | 4.521356 / 2211.7 | .700546 / 14274.6 | 6.45 |

研究時間の2倍以内は未達であり、依頼書が認める代替条件として profile による原因と次の手を記録した。
主因は候補評価での `Problem.state` と `categorical` の反復検証であり、時間にはライブラリの全状態保存と Result/診断も含まれる。
次は検証済み内部状態、受理時の syndrome/observable 更新、順逆局所確率表の再利用を検討する。

## 4. 統合後の tests、wheel、CI

未完了である。
main の直近の全 suite 実行は WP 統合前の `f5323c1` に対する164 passed、40.40秒であり、最終コードの成功とは扱わない。
最終検証用の `.venv-dev2-core` と `.venv-dev2-optional` は準備済みで、統合後の wheel 導入は未実施である。
全 WP merge 後の tests 件数と所要時間、wheel hash/import先、各例とREADME/tutorial、CFF、API監査、GitHub Actions の対象 commit と結果をここへ追記する。
main の push は未実施である。

## 5. 所有者の判断待ち事項

- license の選択、第三者権利確認と正式配布の条件。
- 公開先と repository の公開化、package publish の時期。
- Z .7 / H .3 / k=2 / 1 chain を正式な公開既定として確定するかどうか。
- phenomenological の境界と表現の公開既定を設けるかどうか。
- 著者名 `junichi haruna` は確定済みだが、所属、DOI、正式論文の引用情報は未確定。

## 6. 次の依頼候補

- 同一の出力条件による性能比較と、検証済み内部状態を使う高速化。
- 複数 chain による実符号の混合診断、BAR ladder と block 長への感度評価。
- 回路 baseline の範囲拡張と、物理配置を保った Z/H 提案の独立検証。
- 公開型注釈と py.typed の整備、正式な公開・引用・ライセンス判断。
