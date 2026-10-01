# dev4 最終報告

## 1. 到達点

`0.1.0.dev4` に静的・phenomenological phase flip、物理回路のOBF/Z混合、同seed軌道を保つ専用step、公開型注釈と`py.typed`を統合した。
BARの既定例をexactと反復seedで調べ、block長とsample数を分けた感度評価と利用者向け説明を加えた。
source全358件、core wheel258件、optional wheel358件のテストとwheel実行例・notebookが成功し、remote CIの5jobも成功した。
toricでの研究runner比2倍以内、BARの名目95%被覆、一般問題の混合保証は達成したとは主張しない。
公開既定、ライセンス、公開先、著者の所属とDOIは変更していない。

## 2. WP別の結果

コマンドの`python`は指定Python3.11またはそこから作った検証venvの絶対パスを使用した。
詳細は各完了メモ、独立レビュー記録、[統合検証記録](validation_dev4_ja.md)にある。

| WP | 実装 | 実行した検証（コマンドと結果） | 未実施・制限 | レビューで出た指摘と対応 |
| --- | --- | --- | --- | --- |
| [K](K_ja.md) | `phase_flip_model()`、`errors="Z"`、phenomenological phase flip、X/Z比較例 | `pytest tests/test_phase_flip.py -q`:16 passed、8.98秒、研究Z側の全syndrome照合、独立32状態確認 | HGPの`2^58`と3×5 toricの`2^30` exactは予算外、X/Zの等号・不等号を一律に要求する仮説は反例あり | [独立レビュー](K_review_ja.md)は停止級指摘なし、誤った等号・不等号をテストに固定せず検証結果を記録 |
| [N](N_ja.md) | product/linear組み込み型限定の`faststep.py`、候補効果とdecode cacheを再利用 | `pytest tests/test_faststep.py -q`:15 passed、2.98秒、独立18構成153件と実MH閾値の確認 | toricの2倍目標は未達、独自model/noise/failureは参照経路 | log密度の集計順と実step/RNG試験を修正、[独立レビュー](N_review_ja.md)で承認 |
| [L](L_ja.md) | `single`/`zanella`/`circuit_single`混合、可変alphabetの確率行、新例とbenchmark | `pytest tests/test_circuit_kernels.py -q`:9 passed、28.48秒、N後rebaseの関連7file:59 passed、46.06秒 | 回路専用syndrome差分更新は任意項目として未実装、H/stabilizer非対応、短いchain区間はMCと非交差 | [レビュー](L_review_ja.md)の指摘を受けて成分別MH・failure棄却・lazy・固定乱数の実分岐を永続テスト化、benchmarkは共通初期状態へ修正 |
| [M](M_ja.md) | exact比較、20seed基準と8seed感度、被覆回帰試験、文書・notebook説明 | `pytest tests/test_bar_coverage.py tests/test_estimation.py -q`:12 passed、11.90秒、基準20seed349.11秒、各感度186秒以下 | 原因の一意な同定、研究精度の被覆校正、異なるminimum/maximum初期重みの比較は未達 | sample数と自動block長の交絡をblock8固定で再測定し、旧値も保存、[独立レビュー](M_review_ja.md)でCSV照合と別seed群を確認 |
| [O](O_ja.md) | 公開65名と返り値の公開メソッドの注釈、PEP561 marker、consumer型検査、CI | `mypy src/mcmc4qec`:24file成功、`pytest tests/test_typing.py -q`:3 passed、strict252errors/20file | strict全解消と外部ライブラリstub作成は対象外 | [レビュー](O_review_ja.md)でlist入出力、独自model/noiseの契約、診断のsequence/array入力、NumPy booleanを修正し、実行時ASTも監査 |

## 3. 数値

### K：同じ固定MWPMでのX/Z比較

| 符号・p | X exact `P_L` | Z exact `P_L` | X / Z exact 条件付き重み |
| --- | ---: | ---: | --- |
| toric d=3、0.13 | 0.33955890909632036 | 0.3398765182543714 | 3.574210998458394 / 3.574562479420181 |
| asymmetric toric 2×3、0.13 | 0.3829395240663858 | 0.3829395240663878 | 2.3395741332074724 / 2.3395741332074635 |

toric d=3の差は単なる丸め誤差ではなく、重み4の失敗状態数はX2403/Z2411、重み6はX14301/Z14293だった。
decoderの同率correctionの選択規則は候補であり、因果関係の確定は未実施である。
行列が非同一というだけでは集約誤り率の差は導けないため、依頼書の普遍的な等号・不等号は受入条件から外し、双対モデルの一致と実測を採用した。
小さい非self-dual repetition例ではX/Zの異なる解析値とexactが一致し、Z+Hの条件付き重みはexact2.125に対して2.13233、診断区間[2.11637,2.14830]だった。
新しい3×5例はquick1.76秒・既定5.01秒で、finite MCの差をsector差の証明とは扱わない。

### L：詳細釣合いと共通初期状態での速度

独立レビューの64状態列挙では、成分別混合遷移の行和誤差は最大`2.22e-16`、詳細釣合い流量差は最大`1.09e-19`だった。
この例の失敗集合32状態は連結で自己ループがあり、一般回路への外挿はしない。

| surface d=3、p=0.02、150 step | step/s | 受理率 |
| --- | ---: | ---: |
| `circuit_single` | 176.95 | 0.0067 |
| Z | 52.63 | 0.6600 |
| Z0.7 / OBF0.3 | 63.23 | 0.6467 |

共通の失敗初期状態の探索6試行・0.056秒を表から除き、構成・provenance・診断を含む`sample_faulty`時間を計った。
surface d=3、p=0.03では独立300試行中108失敗の条件付き重みが12.093±0.556、Z+OBFの300保存・burn-in100が9.440±1.555、ESS7.674で区間は非交差だった。
短いchainの精度や混合を保証せず、条件付き標本から絶対`P_L`は推定しない。
新しい回路例はquick3.89秒・既定13.79秒で、PNG/CSVとCSV fallbackを確認した。

### M：exact被覆と一要因感度

toric d=3、p=0.22のexact真値は0.6026625647である。
seed2026のBAR区間[0.505516,0.565085]は真値を外し、独立MC区間[0.571165,0.626535]は含む。

| 条件 | BAR exact被覆 | 平均区間幅 |
| --- | ---: | ---: |
| 基準20seed | 13/20（Wilson 95% [0.433,0.819]） | 0.06257 |
| 基準の先頭8seed | 4/8 | 0.06321 |
| 保存200 / 1200、block8固定 | 6/8 / 7/8 | 0.08113 / 0.05299 |
| 参考：保存200 / 1200、自動block6 / 11 | 6/8 / 8/8 | 0.07677 / 0.05419 |
| burn-in0 / 600 | 7/8 / 7/8 | 0.06140 / 0.06542 |
| block3 / 27 / 107 | 4/8 / 7/8 / 7/8 | 0.04817 / 0.07616 / 0.08562 |
| ladder coarse / fine | 6/8 / 7/8 | 0.07103 / 0.05371 |
| 初期minimum / random / maximum | 6/8 / 5/8 / 6/8 | 0.06275 / 0.06294 / 0.06275 |
| exact anchor | 4/8 | 0.04991 |
| 低p=0.10へのladder | 8/8 | 0.02922 |

独立MCは基準20/20でexactを含み、BARとMCの区間非交差は2/20だった。
既定block8は最大chain重みIATのseed間中央値35.69より短く、blockを長くすると区間は広がるが、seed2026はblock107でも真値を含まなかった。
観測support欠落はなく、minimumとmaximum初期状態は同じ配列だったため異なる初期重みの効果は検証できていない。
8seedの広いWilson区間と低p ladder全体の変更を踏まえ、表を設定の最適性や原因の確定と解釈しない。

### N：研究runnerとの速度比較

| 10000 step、p=0.01、Z/H=0.7/0.3、lazy=0 | library秒 | research秒 | 比 |
| --- | ---: | ---: | ---: |
| toric d=5 | 1.546216 | 0.482388 | 3.21 |
| toric d=7 | 1.869962 | 0.755353 | 2.48 |
| BB72 | 2.867081 | 1.472265 | 1.95 |

独立再測定の比は3.11/2.96/1.79で、toric未達・BB72達成という判断と一致した。
短時間計測と軌道・負荷の差があるため、dev2の別時点測定から厳密な改善倍率は主張しない。
残るprofileと次の改善は[性能記録](../performance_ja.md)に記載した。

### O：型検査

`python -m mypy src/mcmc4qec`は24filesで成功し、`python -m pytest tests/test_typing.py -q`は3 passedだった。
初回に7件失敗したREADME型の利用例は、installed wheelを対象にしたmypyでも成功した。
strictは252 errors/20filesで、内訳はno-untyped-call139、no-untyped-def56、no-any-return27、type-arg16、attr-defined5、operator3、var-annotated2、arg-type/call-overload/index/type-var各1である。
公開APIの通常検査と非公開helperまでのstrict解消は区別し、strict完了とは主張しない。

## 4. 統合検証、wheel、CI

| 対象 | pytest結果 | 秒 |
| --- | --- | ---: |
| 基準source（notebook込み） | 314 passed / 4 skipped | 166.23 |
| K統合後 | 330 passed / 5 skipped | 149.98 |
| N統合後 | 345 passed / 5 skipped | 122.42 |
| L統合後 | 354 passed / 5 skipped | 144.72 |
| M統合後 | 355 passed / 5 skipped | 148.14 |
| O統合・dev4版情報後source | 358 passed / 5 skipped | 146.28 |
| 新規core wheel環境 | 258 passed / 71 skipped | 56.23 |
| 新規optional wheel環境 | 358 passed / 5 skipped | 142.24 |
| optional wheelと研究live照合 | 5 passed / 15 deselected | 1.00 |

source全suiteのコマンドは`python -m pytest tests -q`、wheelは`python -m pytest --override-ini pythonpath= tests -q`で、JUnit記録の位置とvenvは検証記録にある。
sourceとoptionalの通常全suiteの5skipは研究checkout未指定の照合で、上のlive実行で別途通した。
`python -I docs/wp/verify_wheel.py core|optional`でcore7例・文書5ブロック、optional20例・notebook4本・文書7ブロックが成功した。
sourceとの24 Python file一致、空py.typed、版0.1.0.dev4、metadataのREADME一致、site-packagesからのimport、coreでのoptional依存不在も確認した。

最終sourceの146.28秒は基準166.23秒より19.95秒短く、追加5file合計37.117秒、全file最大25.186秒だった。
optional wheelの追加5file合計は35.413秒、最大24.675秒だった。
これらの実測では各file60秒・全suite増分60秒・全体300秒を満たし、別負荷での時間保証とは扱わない。

optional installed wheelで`python -I notebooks/regenerate.py`を実行し、既定notebook4本を再生成した。
各実行時間は3.04/12.05/3.53/2.49秒、合計21.11秒で、これはprocess全体ではなくnotebook実行の和である。
quick再生成のprocess全体は11.29秒で、20本のquick例の最大は4.38秒だった。

検証済みmain `c1c6fb919c3bb3cb7a89a2b4e2fae5fb060f80a4`をpushし、[Actions run 36798208073](https://github.com/junichiharuna/mcmc4qec/actions/runs/36798208073)の5job成功を確認した。

| remote CI（Ubuntu） | 結果 | pytest秒 |
| --- | --- | ---: |
| core wheel Python3.11 | 258 passed / 71 skipped、例と文書も成功 | 23.83 |
| core wheel Python3.12 | 258 passed / 71 skipped、例と文書も成功 | 46.28 |
| optional wheel Python3.11 | 356 passed / 7 skipped、20例とnotebookも成功 | 118.59 |
| optional wheel Python3.12 | 356 passed / 7 skipped、20例とnotebookも成功 | 119.21 |
| typing Python3.11 | 通常mypy24files成功、型テスト3 passed | 0.59 |

remote optionalのローカルとの差2件はmypy不在による型テストのskipで、独立typing jobでは両検査を含めて成功した。
この報告と完了記録の文書だけを後続コミットに追加し、source・wheel対象の内容は上のCI対象と同一である。

5worktreeのclean状態、`git cherry main wp/<k|n|l|m|o>`が空であること、各branchがmainの祖先であることを確認した。
削除先の解決済み絶対パスが`A:/dev/mcmc4qec-wt`直下の対象5個であることを確認し、worktreeと`wp/k`〜`wp/o`を削除した。
研究repoはHEAD`69efcfcc86af3bf24ca977a098dab0f348601aff`のままcleanで、handoff既存本文のprefix一致、CITATION不変、LICENSE非追加も確認した。
研究repoには書き込まず、公開化・publish・著者情報の確定も行っていない。

## 5. 不具合と扱い

新しいphenomenological phase flipで確率行を4値として構築する不具合を受入テストで再現し、binaryデータは2値にする最小修正を行った。
Nの初回実装ではphenomenological log密度の集計順序と実stepの試験不足を修正し、同seedの軌道とRNG消費を再検証した。
Lの集約提案MHだけのテスト、Mのsample数とblock長の交絡、Oの狭すぎる入力注釈は、レビューと再測定で修正した。
BARの式やbootstrap実装に最小修正を要する誤りは今回特定せず、`estimation.py`の推定処理は変更していない。
区間の非交差と低い探索的被覆は記録し、seed調整で隠していない。

## 6. 所有者判断と次の候補

ライセンス、公開先、著者の所属・DOI等は所有者判断のままとした。
BARの既定block長・標本数への指針の反映は、追加の被覆校正を踏まえて所有者が判断する。
回路cluster exchangeはlocationのgroup化、alphabet長の違い、順逆提案確率を定めた小仕様から始める必要がある。
次の候補はtoricの速度差の残り、BAR scoreと経路間移動を含む混合評価、実際に異なる初期重みの感度、回路の効果差分更新、非公開ヘルパーまで含めたstrict型検査である。
診断が良くても収束・エルゴード性・正しさの証明にはならず、この制約は維持する。
