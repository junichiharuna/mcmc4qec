# 開発依頼書の最終報告

## 1. 到達点

WP-A〜E を指定順で main に統合し、65個の公開 API と version `0.1.0.dev2` を整えた。
統合後の全 suite は268件成功、最終 installed wheel は core208件・optional268件成功し、実行例と文書例も検証した。
研究照合、物理回路 baseline、複数 chain 診断を実装し、独立レビューでの指摘に対応した。
研究速度の2倍以内は未達で、profile と改善案による代替受入条件を満たしたが、混合や収束の証明は主張しない。
著者はユーザーが指定した `junichi haruna` で、公開化、publish、license の追加は行っていない。

## 2. WP ごとの実装・検証・レビュー

以下は各 WP の記録であり、統合後の最終検証結果は第4節に別記する。
検証は指定 Python 3.11 を使用した。

| WP | 実装 | 実行した検証（コマンドと結果） | 未実施 | レビューの指摘と対応 |
| --- | --- | --- | --- | --- |
| A | 実符号ファクトリと MWPM/BP-OSD/sector wrapper、研究照合 | `pytest tests/test_crossval_research.py -q` を研究path指定で19 passed、4decoder各256症候群で不一致0；exact、MC、Z+H は第3節 | 大符号の距離下界の独立証明、元数値照合の生Result保存 | 直接研究import試験と数値表再現helper、研究への出力拒否を補い第2回受入；非単位交差行列は明示 independent 指定で保持 |
| B | product ノイズの Z 高速経路、decoder cache、syndrome 差分 | `-m pytest tests -q` 169 passed、`tests/test_fastpath.py` 13 passed；列挙で q 最大差 1.11e-16、詳細釣合い差 0 | 研究速度の2倍以内 | cache の先行 uint8 cast を修正し、不正 decoder 出力の回帰試験を追加；profile による代替受入条件を確認 |
| C | 物理 location の排他 fault、Stim 効果の XOR、専用 MH と中点 logical idle | `pytest tests/test_circuit_model.py tests/test_circuit_pipeline.py tests/test_circuit_proposal.py tests/test_circuit_surface.py -q` 20 passed、全6位置4096配置のexact、surface比較 | d>3の統計照合、論文図表再現、回路Z/H/stabilizer | 全位置列挙、location別分布、確率和、確率付きM/MPP拒否、重複target識別を修正し第2回受入 |
| D | README、API/tutorial、CI、CFF、追加例 | `test_public_api.py` で65名突合、CFF validate成功、最終wheel208/268件、全6例・README2例・tutorial4例成功 | py.typedは提案のみで型監査後へ延期 | 導入依存、BAR状態数上限、同じ条件付き量の比較、全公開引数・例外を補完；最終レビュー記録参照 |
| E | 複数 chain 診断、四条件、厳密な論理コセット最小化と初期化 | `pytest tests/test_convergence.py tests/test_initial_states.py -q` 16 passed、独立レビューでも16 passed | 実符号の長時間・多chain混合評価 | ゼロ分母、独立分散未指定、負相関IAT、二盆地、MILP最適性を修正し第2回受入；core統合試験でMILPのoptional skipを補完 |

## 3. 数値照合と性能

以下の値は WP-A/B の実測記録から転記したものであり、研究論文の図表再現や全領域の精度保証ではない。
詳細な条件と制約は統合後の `docs/crossval_research_ja.md` と `docs/performance_ja.md` に残す。
元の exact・10万MC・3000標本Z+H の生Resultは保存されておらず、担当の実測記録と再現helper `docs/wp/A_reproduce.py` を根拠とする。
独立レビューではdecoder比較とhelperの短い実行を確認し、この長い数値表全体の再計算は行っていない。

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

回路baselineでは repetition d=3 の2ラウンド全4096配置と PyMatching の exact P_L は `0.02515682853`、Stim直接20,000試行では `0.0255` だった。
surface d=3・6ラウンド・p=.01 の物理配置700試行は `74/700=.105714`、Wilson区間 `[.085049,.130683]` で、Stim直接5000試行の `.0884` を含んだ。
これらは物理配置と中点observableの小規模検証であり、論文図表の再現や全回路への等価性を主張しない。

## 4. 統合後の tests、wheel、CI

再現コマンド、依存version、ファイル別時間、初回core失敗と修正の記録は [validation_dev2_ja.md](validation_dev2_ja.md) にまとめた。

| 検証 | 結果 | 秒 |
| --- | --- | ---: |
| 全WP統合後 source `python -m pytest tests -q` | 268 passed / 4 skipped | 76.01 |
| 最終 wheel、coreのみ、`python -I -m pytest --override-ini pythonpath= tests -q` | 208 passed / 43 skipped | 41.23 |
| 最終 wheel、optionalあり、同コマンド | 268 passed / 4 skipped | 81.52 |
| coreの実行例・文書例 | 3 examples、README1例、tutorial3例がexit 0 | 各60秒以内 |
| optionalの実行例・文書例 | 全6 examples、README2例、tutorial4例がexit 0 | 各60秒以内 |
| CFF / API | schema1.2.0 validate成功、65名掲載・import・docstringを確認 | — |

4 skipは環境変数指定時だけ実行する研究decoder直接比較で、独立レビューでは別途成功している。
coreのskipはoptional依存と研究checkoutの不在によるもので、MILP用SciPyのskip指定漏れ2件を統合時に修正した。
最終 wheel は `mcmc4qec-0.1.0.dev2-py3-none-any.whl`、SHA256 `e4d443a860a182786d3377cc068f713428771630fde9615cf7efbdb493581664` である。
二つの新規venvのsite-packagesからimportし、packageの23 Pythonファイルがsourceとbyte一致することを確認した。
main の `a47a141433fb97ccd9a44e597f8604352999df0a` を origin/main へpushし、[GitHub Actions](https://github.com/junichiharuna/mcmc4qec/actions/runs/36675225072) の全4job成功を確認した。
Python 3.11 / 3.12 のcoreは各208 passed / 43 skipped、optionalは各268 passed / 4 skippedで、CIの実行例もすべて成功した。
このCI結果を記録する後続commitは文書のみの変更であり、package・tests・workflowは検証対象から変更していない。

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
