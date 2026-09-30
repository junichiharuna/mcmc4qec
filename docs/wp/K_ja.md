# WP-K 静的 phase flip 完了メモ

## 1. 小さい仕様と実装

Z 誤りの状態は qubit ごとの binary support とし、`CSSCode.phase_flip_model()` は `hx` を syndrome、`lx` を observable、`hz` を stabilizer 行として使う。
`IndependentBitFlip(code.n)` は X と Z の binary product 分布を共通に表す。
`mwpm_decoder(code, errors="Z")` と `bposd_decoder(code, p, errors="Z")` は `hx` から物理 Z correction を求め、`lx` で論理予測を返す。
`errors="X"` は従来の `hz` と `lz`、識別子、既定値を維持する。
phenomenological phase flip は各 round の Z data fault と X check measurement fault を持ち、data fault と measurement fault はいずれも二値とする。
高速 Zanella の局所確率行は phase flip data fault に Bernoulli の 2 列を使い、参照密度からの提案分布と同一 seed 軌道が一致する。
条件付き chain は絶対論理誤り率を推定しない。

変更した担当ファイルは `src/mcmc4qec/core.py`、`decoders.py`、`models.py`、`noise_categorical.py`、`tests/test_phase_flip.py`、`tests/test_crossval_research.py`、`examples/phase_flip_asymmetric.py`、`docs/tutorial_en.md` である。
`src/mcmc4qec/fastpath.py` の必要な1行修正は担当外としてメインに依頼し、メインの commit `23bd178` をこの作業枝へ `3609478` として取り込んだ。

## 2. 受入テストと実測

`tests/test_phase_flip.py` は双対符号との行列・全状態一致、非 self-dual な Hamming HGP と BB72 の行列選択、小符号の exact、Z 側復号器、phenomenological 正規化と全32状態の高速 Zanella 等価性、同一 seed 軌道、Z sector 初期状態、Z+H 条件付き重み、CLI、無効値を検査する。
Z+H の重み比較は、Zanella が動かせない偶奇固定の例を避けて双対 repetition 符号を使った。
seed 724、p=0.3、3000 retained states では exact `E[w|faulty]=2.125`、chain 平均 `2.1323333333333334`、IAT `1.7332322073639115`、ESS `1730.8702130355211`、分散と ESS による参考95%区間 `[2.11636692, 2.14829974]` だった。
この区間は推定 IAT と正規近似に依存し、1回の被覆は収束・エルゴード性・正しさを証明しない。
`RIMC_RESEARCH_ROOT=A:\dev\RIMC` と `PYTHONDONTWRITEBYTECODE=1` を指定した研究比較では、toric d3 の実現可能な X-check syndrome 全256件で、`mwpm_decoder(errors="Z")` と読み取り専用の `RESEARCH/src/css_code.py` の Z 側論理予測が一致した。

| 実行 | 結果 | 所要時間 |
| --- | --- | ---: |
| `python -m pytest tests/test_phase_flip.py -q --tb=short` | 16 passed | 10.68秒 |
| `python -m pytest tests/test_phase_flip.py tests/test_crossval_research.py tests/test_decoders.py tests/test_noise_models.py tests/test_fastpath.py tests/test_initial_states.py tests/test_public_api.py -q --tb=short` | 116 passed | 28.09秒 |
| `python -m pytest tests/test_crossval_research.py -q --tb=short` | 20 passed | 1.94秒 |
| `python examples/phase_flip_asymmetric.py --quick --seed 20261001` | 成功、CSV・PNG・summary.json・SUMMARY出力 | 1.76秒 |
| `python examples/phase_flip_asymmetric.py --seed 20261001` | 成功、CSV・PNG・summary.json・SUMMARY出力 | 5.01秒 |

ここで `python` はすべて `C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe` の絶対パスを使用し、研究比較の2コマンドには PowerShell の `$env:RIMC_RESEARCH_ROOT='A:\dev\RIMC'` と `$env:PYTHONDONTWRITEBYTECODE='1'` を設定し、例の source 実行時は `PYTHONPATH=src` を設定した。
例の quick は250 independent trials、既定は3000 independent trials を各 sector で実施する。
quick の `P_L(X)=0.312` と `P_L(Z)=0.364`、既定の `P_L(X)=0.364` と `P_L(Z)=0.37566666666666665` は有限標本値で、両方とも95% Wilson区間が重なる。
3×5の状態数は `2^30=1,073,741,824` なので例では exact を実行せず、`exact_available=false` と記録する。

## 3. 依頼書の X/Z 等号・不等号に対する検証

依頼書の「toric d3 で X と Z の exact `P_L` と条件付き重みが一致し、asymmetric toric と Hamming HGP で一致しない」は、少なくとも現行の PyMatching MWPM と研究行列順序では受入条件にできない。
public `exact` で p=0.13 の toric d3 を各 `2^18=262,144` 状態列挙すると、X の `P_L=0.33955890909632036`、`E[w|faulty]=3.574210998458394`、Z の `P_L=0.3398765182543714`、`E[w|faulty]=3.574562479420181` だった。
実測時間は X が100.99秒、Zが97.06秒だったため、この列挙は1ファイル60秒制限の pytest に入れなかった。
別のベクトル化全列挙は X の `P_L=0.33955890909626174`、Z の `P_L=0.339876518254405` と public `exact` に浮動小数誤差内で一致した。
toric d3 の失敗状態数は重み4で X 2403件・Z 2411件、重み6で X 14301件・Z 14293件であり、差は単なる丸め誤差ではない。
同率 correction の決定規則が原因の候補だが、列置換の全自動同型と tie-break の因果検証は未実施なので確定とはしない。
asymmetric toric 2×3 の public `exact` は p=0.13 で X `P_L=0.3829395240663858` と Z `P_L=0.3829395240663878`、X `E=2.3395741332074724` と Z `E=2.3395741332074635` で、`2^12=4096` 全状態で一致した。
対応するベクトル化全列挙も双方 `P_L=0.3829395240663862` と `E=2.339574133207471` だった。
行列は `hx != hz`、`lx != lz` であるが、この非同一性から集約した誤り率の差は導けない。
Hamming HGP は `n=58` で `2^58=288,230,376,151,711,744` 状態、asymmetric 3×5 は `n=30` で `2^30=1,073,741,824` 状態となり、公開 `exact` の上限 `1,048,576` を超える。
Hamming HGP と BB72 では `hx != hz` と `lx != lz`、phase model と双対 bit model の syndrome・observable・stabilizer 行の一致を検査したが、集約した exact `P_L` の比較は未実施である。
非 self-dual の違いを明確に示す core の3 qubit repetition 例では p=0.13 で X `P_L=3p²-2p³`、Z `P_L=3p(1-p)²+p³` と exact が一致し、両 sector は異なる。

## 4. 統合時にメインへ依頼すること

`README.md` と `README_ja.md` の対応表に `Static CSS phase-flip | Supported | Optional | PyMatching/BP-OSD via errors="Z"; hx/lx` 相当の行を追加する。
`docs/api_en.md` で `CSSCode.phase_flip_model()`、`mwpm_decoder(code, *, errors="X")`、`bposd_decoder(code, p, *, errors="X", **kw)`、`PhenomenologicalModel(data_noise="phase_flip")` と `initial_states(..., sector="z")` を記載する。
`examples/README.md` に `examples/phase_flip_asymmetric.py` の行を加え、extras を `codes,matching`、目的を3×5のX/Z direct MC比較、実測を quick 1.76秒・既定5.01秒、読み方を「Wilson区間と `exact_available=false`、差の断定不可」とする。
`docs/wp/verify_wheel.py` の optional 例マニフェストに `phase_flip_asymmetric.py` と `code p pl_bit_flip pl_phase_flip interval_bit_flip interval_phase_flip exact_available` を加え、CIのoptional quick例に含める。
`__init__.py` に追加すべき top-level 名はなく、既存の `CSSCode`、`PhenomenologicalModel`、decoder サブモジュールの公開契約を拡張した。
`tests/test_docs_manifest.py` は共有担当が統合後の例数とREADME行を確認する。
WP-K 内で全 suite、installed wheel、remote CI、3×5 exact、Hamming HGP exact は未実施であり、全 suite 以降は統合担当が行う。
