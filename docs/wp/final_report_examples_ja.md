# dev3 実行例・notebook・README 最終報告

## 1. 到達点

WP-F〜Jを独立レビュー後にH → F → G → I → Jの順でmainへ統合し、版番号を`0.1.0.dev3`に揃えた。
既存6例を共通CLIに揃え、新規12例、実行済みnotebook4本、再生成スクリプト、英日READMEと実測付き一覧を追加した。
source全suiteは314 passed / 4 skippedで、公開API65名とZ/Hの公開既定は維持した。
core/optionalの別venvで全テスト・実行例・文書・notebookのwheel検証を完了し、mainへのpushとremote CI全4 jobの成功を確認した。
短い例の数値を収束・研究精度・論文図の再現の保証として扱わず、区間不一致と依存関係の制約を明記した。

## 2. WPごとの成果とレビュー

以下の`python`は指定Python 3.11、wheel検証ではそこから作成したvenvのPythonを指す。
各WPの独立検証と履歴は[F](F_ja.md)・[G](G_ja.md)・[H](H_ja.md)・[I](I_ja.md)・[J](J_ja.md)、レビューは対応する`*_review_ja.md`に記録した。

| WP | 作ったもの | 実行した検証（コマンドと結果） | 未実施 | レビューの指摘と対応 |
| --- | --- | --- | --- | --- |
| F | BB72、toric depolarising、phenomenological、Steaneの4例と既存6例のCLI改修 | `python -m pytest tests/test_examples_real.py -q`は11 passed、最終全suiteでも11件成功、10例の既定・quick実行成功 | 大規模sweep、研究図の再現 | BB72の診断文言を限定し、Steaneの被覆不足をそのまま記録、回路quickの時間超過はメインで修正して受入 |
| G | BAR曲線、条件付き重み、複数初期状態の診断、p依存decoderの4例 | 最終`python -m pytest tests -q`内で12件成功、4例の既定・quick実行成功 | 区間不一致の原因特定、長時間混合検証 | 初期セクター衝突を修正、独立MC分散を使用、BAR区間の未取得・非交差を警告、anchor再利用を明示して受入 |
| H | 符号・ノイズ・decoder・Stim DEMの4持ち込みテンプレート | `python -m pytest tests/test_examples_templates.py -q`は13 passed、最終全suiteでも13件成功、4例の既定・quick実行成功 | 利用者の任意の大符号や外部decoderの意味的正しさの保証 | MC値のExact誤表示を修正、ノイズ試料の幅・binary・support検査を追加、部分検査の限界を明示して受入 |
| I | 英語notebook4本、保存済み図、`regenerate.py` | 最終全suiteで4件成功、既定再生成34.989秒、各notebookの既定・quick実行成功 | 研究精度を確認する長いchain、全seedでの区間一致 | standalone化、三群の初期状態と診断をGに整合、既定BARの区間非交差も保存出力で警告して受入 |
| J | 英語READMEの拡充、日本語README、全例・notebook一覧 | 最終全suiteで`test_docs_manifest.py`の3件成功、リンク・全ファイル収載・英日Pythonブロックの完全一致を確認 | 未決定の公開・ライセンス・所属・DOIの確定 | 現行toricファクトリのcodes依存を英日で統一し、実測値をメインで補って受入 |

全18例は`--quick --seed INT --out DIR`、一時ディレクトリを既定とする出力、最終行の`SUMMARY` JSONに対応する。
研究リポジトリと環境変数で指定した研究rootへの出力を作成前に拒否し、意図的に壊したテンプレートも出力先作成前に停止する。
条件付きchainの頻度から絶対`P_L`を計算する例は作らず、BARでは固定decoderまたは明示的な近似モードと観測失敗のあるanchorを使う。
物理回路baselineは明示した`circuit_single=1`だけを使用する。

## 3. 全例とnotebookの実行時間

Windows、Python 3.11の壁時計実測で、各行は成功した既定・quick実行を記録する。
Fはdev3 installed wheel、G/Hは各WPのsource実行、Iは各WPの再生成記録に基づき、conditional_weightの最終設定はメインでwheelから再測定した。
seed、コマンド、計測条件は各WPの完了メモにあり、環境負荷やNumPy等の版による変動を認める。
`regenerate.py`は4本全体の別実行なので、個別notebookの時間合計とは一致しない。

| ファイル | 既定（秒） | quick（秒） |
| --- | ---: | ---: |
| `examples/bit_flip.py` | 2.549 | 0.292 |
| `examples/three_noise.py` | 4.340 | 1.158 |
| `examples/bar_ladder.py` | 0.503 | 0.348 |
| `examples/toric_pymatching.py` | 1.008 | 0.680 |
| `examples/stim_dem.py` | 0.476 | 0.225 |
| `examples/circuit_baseline.py` | 3.908 | 1.441 |
| `examples/bb72_bposd.py` | 1.951 | 0.712 |
| `examples/toric_depolarizing.py` | 1.521 | 0.708 |
| `examples/phenomenological_toric.py` | 0.952 | 0.644 |
| `examples/steane_exact.py` | 2.354 | 0.516 |
| `examples/workflows/pl_curve.py` | 19.370 | 3.610 |
| `examples/workflows/conditional_weight.py` | 16.790 | 3.926 |
| `examples/workflows/convergence_check.py` | 1.450 | 1.010 |
| `examples/workflows/p_dependent_decoder.py` | 1.720 | 0.780 |
| `examples/templates/byo_css_bitflip.py` | 0.599 | 0.269 |
| `examples/templates/byo_noise.py` | 0.313 | 0.190 |
| `examples/templates/byo_decoder.py` | 0.310 | 0.184 |
| `examples/templates/byo_stim_dem.py` | 0.780 | 0.596 |
| `notebooks/01_quickstart.ipynb` | 5.890 | 4.930 |
| `notebooks/02_pl_curve_with_bar.ipynb` | 37.680 | 6.530 |
| `notebooks/03_conditional_sampling_and_diagnostics.ipynb` | 7.560 | 4.120 |
| `notebooks/04_bring_your_own.ipynb` | 4.890 | 2.580 |
| `notebooks/regenerate.py`（4本全体） | 34.989 | 20.180 |

各例は既定120秒・quick10秒、各notebookは既定180秒・quick60秒以内だった。
保存notebookは最大49,242 bytesで、PNGは各1枚、出力のない状態からの再生成も検証した。
Windows Systemログのスリープと一致した中断・timeout試行は合格や通常実測に含めていない。

## 4. 統合テスト、wheel、CI

Phase 0のmainとorigin/mainは`8cbc0b1c4eef64519cc6320b3ddd5565876d168e`で一致し、指定依頼書とAGENTS.mdを含むcleanな状態だった。
メインが共有ファイルを管理し、5 WPは個別worktreeで並列実装し、別担当がレビューした。
各merge後の`python -m pytest tests -q`は次のとおりだった。

| 段階 | 結果 | 秒 |
| --- | --- | ---: |
| Phase 0 | 268 passed / 4 skipped | 46.08 |
| H統合後 | 284 passed / 4 skipped | 69.79 |
| F統合後 | 295 passed / 4 skipped | 98.44 |
| G統合後 | 314 passed / 4 skipped | 138.40 |
| I統合後 | 318 passed / 4 skipped | 151.79 |
| J統合後 | 321 passed / 4 skipped、追加テストの時間予算超過 | 265.15 |
| 重複seed整理・quick縮小後の最終source | 314 passed / 4 skipped | 231.28 |
| 最終core installed wheel | 231 passed / 61 skipped | 113.04 |
| 最終optional installed wheel | 314 passed / 4 skipped | 225.23 |

最終sourceの追加5ファイル合計は84.876秒、最大はworkflowの32.055秒であり、90秒・60秒・全suite300秒の予算内だった。
optional wheelでも追加5ファイル合計83.405秒、ファイル別最大31.542秒で時間予算内だった。
初期セクター衝突は9 seedで検査済みで、常設回帰試験を代表する2 seedへ整理したため最終件数が7件減った。
既存テストにも時間変動があるため、Phase 0との差をそのまま追加テストの費用とは解釈しない。
同じoptional wheel環境で新規5ファイルを`--ignore=tests/<ファイル名>.py`で除いた比較実行は271 passed / 4 skipped、140.96秒だった。
最終全suite225.23秒との差は84.27秒で、計測用親processを含む壁時計も226.285秒と141.927秒の差84.358秒となり、90秒の増分予算内だった。
この比較対象にはversionと回路の小規模修正の受入試験も含み、新規5ファイルの寄与を同時期の環境で比較している。
notebook実行でWindowsのZeroMQが補助selector threadを使う警告が1件出たが、実行は成功した。

wheelは`.venv-dev3-optional/Scripts/python.exe -m build --wheel`で作成し、新規の`.venv-dev3-core`と`.venv-dev3-optional`へ導入した。
coreはoptional依存なし、optionalは`matching,bposd,codes,stim,plot,notebooks`の全6 extrasを使用する。
全suiteは各venvの`python -I -m pytest --override-ini pythonpath= tests -q`、補足検証は`python -I docs/wp/verify_wheel.py core|optional`で実行した。
wheelのSHA256は`69d9488c7dfe3c91a7497db1fc954bbb05379ec0f70d294a3fa669a02bdd2156`である。
sourceとwheelのPython 23ファイルのbytes一致、site-packagesからのimport、配布・runtimeのdev3一致、metadata内READMEの一致を確認した。
英語READMEとtutorialのPythonブロックを実行し、日本語版は完全一致試験で確認した。
coreの補足検証は7例と文書4ブロックが成功し、全体13.90秒だった。
optionalの補足検証は全18例・notebook4本・文書6ブロックが成功し、全体71.02秒だった。
全18例にprocess単位10秒の上限を適用し、notebookの再生成は21.73秒、各notebookは4.60・6.90・5.47・3.66秒だった。
main `7afd3ac3ef60ca62ec3c174516fe179054901ad7`をorigin/mainだけにpushし、[Actions run 36694827034](https://github.com/junichiharuna/mcmc4qec/actions/runs/36694827034)の全4 jobが成功した。

| Ubuntu CI job | 結果 | pytest秒 | 実行例・文書・notebook |
| --- | --- | ---: | --- |
| core / Python 3.11 | 231 passed / 61 skipped | 57.60 | 7例・文書4ブロック成功 |
| core / Python 3.12 | 231 passed / 61 skipped | 35.79 | 7例・文書4ブロック成功 |
| optional / Python 3.11 | 314 passed / 4 skipped | 79.11 | 18例・文書6ブロック・notebook4本成功 |
| optional / Python 3.12 | 314 passed / 4 skipped | 77.61 | 18例・文書6ブロック・notebook4本成功 |

CIでも23 Pythonファイルのsource一致を確認し、各例の10秒上限、notebook再生成、READMEとtutorialの実行まで成功した。
`git cherry main wp/<x>`が空、mainの祖先であること、各worktreeのclean状態を確認してから、f〜jの絶対パスが`C:/dev/mcmc4qec-wt`配下であることを検査し、`git worktree remove`と`git branch -d`で整理した。
削除前の枝HEADはF `3acc0c9`、G `5e3829c`、H `d8ffabf`、I `8081496`、J `e758e72`であり、成果とレビュー記録はmainの履歴に保持されている。
リポジトリはprivateのままで、残るworktreeは`C:/dev/mcmc4qec`のmainだけである。

## 5. ライブラリの問題と扱い

### 修正したもの

配布版だけdev3にするとResult provenanceを含む実行時版番号がdev2のままになるため、一致テストの失敗を先に確認して`results.py`の定数1行を更新した。
回路例のquickが12.43秒で上限を超え、profileでは2588個の単一fault効果を作る際の理想回路の命令別再構築が主因だった。
メイン向けの小規模修正の例外に従い理想区間を再利用し、重複target・2 qubit・選択locationの80配置を比較する受入テストを先に追加した。
修正前後のsurface d=3のH/L全2588列は一致し、構築時間は9.61秒から0.92秒へ短縮、回路関連22テストも成功した。
公開API、fault順序、物理分布、failure定義、カーネル既定は変えていない。

### 現在の依存と数値上の制約

現行`make_toric_code`はldpcとbposdを必要とするため、依頼書マニフェストと一覧の該当行に`codes`を追加した。
PyMatching 2.4自身が`matplotlib.cbook`を読み込むため、matching workflowをmatplotlibパッケージ全体なしで動かす条件は満たせない。
検証したのは描画用`pyplot`のImportError時に数値CSVを保持してPNGを省く経路であり、README両言語にもこの制約を書いた。
phenomenological例は既存公開APIで時空間matchingを構築できたため、追加APIやマニフェストからの削除は不要だった。
SteaneのCLI既定seedにおけるBAR区間のexact被覆は記録した実行で既定2/3、quick1/3で、全rungの真偽を出力している。
探索時の別seedで3/3になった結果を主結果に置き換えず、区間やseedの調整で被覆を作っていない。
BAR曲線とnotebook 02は既定設定でもd=3、p=0.22で独立direct MCの区間と非交差となり、原因は未特定である。
anchor点は同じMCを再利用することを表示し、他の独立確認点と区別した。
この非交差を警告として残し、現状の短いchainが十分に混合したと解釈しない。
ノイズの密度正規化検査だけではsamplerの分布一致は証明できず、テンプレートの部分検査だけで持ち込み要素の全契約を保証しない。

## 6. 所有者判断と次の依頼候補

著者名はユーザー指定の`junichi haruna`であり、所属・DOI・ライセンス選択・公開化・PyPI publishは所有者判断として残した。
研究リポジトリ`C:/dev/RIMC`は`69efcfcc86af3bf24ca977a098dab0f348601aff`のcleanな状態を保持し、ファイル変更やrunner既定変更をしていない。
次の研究検証候補は区間非交差の原因調査、chain長・初期状態・ladder・block長の感度評価と反復seedによる被覆の評価である。
長いsweepやクラスタジョブは今回未実施であり、診断の合格を収束・エルゴード性・正しさの証明として扱わない。
dev2からの研究runnerとの速度差、回路baseline拡張、型注釈と`py.typed`も次の候補として残る。
