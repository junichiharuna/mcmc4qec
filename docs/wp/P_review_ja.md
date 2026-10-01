# WP-P 独立レビュー：実装と最終科学 CSV

## 対象と判定

`f2799a1` からの WP-P 差分と、真値入力および集計の追補修正をレビューした。
実装段階では、後述の真値 CSV の検証不足が修正された後に残る重大な実装上の指摘はない。
WP-Q 統合後の main で取得した保存長比較60行と被覆比較12 cohort・240行の数値監査は後述のとおり完了し、修正後の集計に未解決の算術上の指摘はない。
有限20 seedと短いpaper traceは名目95%被覆、収束、論文精度の再現を立証しないため、科学的保証の判定は行わない。

## 独立に照合した点

論文 `A:/dev/RIMC/paper/main.tex` の splitting 式と `src/splitting_pl.py` の BAR の向きは、`bennett_log_ratio` の log 比の定義と整合する。
論文の `eq:chain-se` は観測量の chain 平均に対する式であり、chain ごとに解く非線形 BAR 比への適用は大標本近似であることが実装の docstring と完了メモに明記されている。
`cross_chain` は隣接比を同じ chain 番号で組にした標本共分散を chain 数で割り、共有 rung の相関を保ったうえで独立 anchor の log 分散を加える。
pooled BAR の点推定と rung seed 系列は誤差法の選択前に決まり、既定の block bootstrap 経路は維持されている。
`src/postprocess.py` の 1D `burn_in(method="tau", c=5)` と `src/metrics.py` の最初の負の自己相関で打ち切る IAT に対し、`paper_burn_in_cut` は各 chain 個別の反復 cut と半 trace fallback を対応させている。
`cluster_scripts/lowp_audit.py` と `compare/convergence_flags.py` に照らし、scaling と drift は未burnの checkpoint、multistart と dispersion は各 chain の burn 後を使う修正版であることを確認した。
toric d=3 では論文式の最小・最大論理基底初期状態が同じであるため、正式な四条件合格を未判定とし、三条件のみの `paper_vacuous_pass` と補助の異なる faulty 初期状態による判定を区別している。
研究 production runner の独立 lazy 抽選なしに合わせた paper 群の `lazy=0` と、ライブラリ設定を保つ既定群の `lazy=0.05` は CSV に記録される。
paper 群の chain 別 cut 後の標本数は不等になり得るため、等長 chain の API の分散近似をそのまま延ばした区間であることを完了メモに明示している。
研究リポジトリの `git status --porcelain=v1` は出力なしであり、研究ファイルへの書き込みは確認されなかった。

## 指摘と対応

初版の `--truth-file` は region と利用者の宣言だけで真値を採用し、異なる問題の真値を被覆 CSV に混ぜられた。
WP-P 担当はこの入力経路を撤去し、fresh `exact()` または問題・source・count digest を照合する失敗重み cache に限定した。
初版の `--aggregate` は cohort の seed の重複と欠落を拒否したが、行ごとの exact 真値の一貫性を検証していなかった。
WP-P 担当は集計時に checked truth cache を必須とし、問題 digest、source digest、真値 source、再計算した exact 値と固定 20 seed の完全性を検証するよう修正した。
長さ比較の `bar_sensitivity.py` にも旧来の手動確認式 `--truth-file` が残っていたため、dev5 の正式計測ではこれを使わないよう指摘した。
WP-P 担当は同スクリプトに checked truth cache と固定20 seedの集計を追加し、exact 真値と条件付き重み、問題とsourceのdigestを検証するよう修正した。
当初の長さ比較集計では bootstrap 反復数が群の識別に含まれず、異なる設定の slice が混ざり得た。
WP-P 担当は各 seed のCSVと集計 key に反復数を加え、seed間標準偏差と平均biasの標準誤差、および有効区間数を要約に追加した。
MC と exact の両 anchor を比較する `--anchor both` は同じ条件付き軌道、BAR 比、MCMC log 分散を一度だけ計算し、anchor ごとに別の CSV を書く構成である。
paper 群の `--samples` は cut 前の全 trace 歩数、既定群では cut 後の保存数であるため、同じ値でも実計算量と有効標本数は等しくない。
WP-P 担当は `total_steps` と chain 別 cut を CSV に追加し、この違いを完了メモに明示した。
最終被覆CSVの集計ではPythonの未判定 `None` がCSV再読込時に空欄へ変わり、正式四条件の未判定数を0と誤集計する箇所を見つけた。
WP-P担当は `None`、空欄、文字列 `"None"` を同じ未判定として数える集計修正を加え、mainの `850fa0f` で統合した。
修正は集計のみでrawのsampling値を変えず、修正版aggregateの未判定数は全12 cohortでrawからの独立計数と一致した。

## 実行した限定検証

`PYTHONDONTWRITEBYTECODE=1` と `RIMC_RESEARCH_ROOT=A:/dev/RIMC` を設定し、`A:/dev/mcmc4qec/.venv-dev5-source/Scripts/python.exe -m pytest tests/test_bar_uncertainty.py -q` は 6 passed、4.87 秒だった。
このテストには合成 chain の標準誤差と共有 rung の共分散、pooled 点推定の一致、MC anchor 分散、単一 chain と不正方法の拒否、小問題の10 seed被覆、反復 cut の確認が含まれる。
同じ環境と `PYTHONPATH=A:/dev/mcmc4qec-wt/p/src` で `bar_paper_protocol.py --quick --region paper --protocol default_block --anchor both --truth-cache output/bar_pilot_q/truth_weights.json --verify-api --out output/review_p_anchor_both` は3.55秒で成功した。
MC anchor の点推定は0.0205095980、exact anchor の点推定は0.0216027606であり、両方の公開API照合とCSVのBAR比、cut、収束列、lazy の一致を確認した。
最初の CLI 試行は `PYTHONPATH` がなく import 前に停止し、上記の環境を設定した再実行で解消した。
研究コードの live BAR 照合、全 suite、重い benchmark はこのレビュー担当では再実行していない。

## 条件付き初期化と bias の解釈

default 群の `initial_state=None` は各 chain の独立な bit-flip ノイズ標本を、固定された決定的 MWPM の failure が成立するまで繰り返して初期状態を作る。
ノイズの標本が正しい独立標本である限り、採用された初期状態は `ρ_p(x) 1_F(x) / P_p(F)` に従い、最大試行数以内で成功したことを条件としてもこの分布は変わらない。
カーネルがこの条件付き分布を不変に保つなら default 群は初期時点から分布上は定常であり、有限 seed の平均差を初期 burn-in 不足による過渡 bias と断定できない。
定常でも chain 内相関は有効標本数を減らして seed 間散らばりを大きくし、非線形 BAR 解と確率への変換には有限標本 bias が残り得る。
4 chain の cross-chain 分散推定や短い block bootstrap も不安定または過小になり得るため、点推定の偏りと区間幅の不足を別に評価する。
同じ seed の burn-in を変えて点推定が動くことは、定常 chain の異なる区間を見た場合にも起こる。
paper 群は決定的な論理基底状態から開始するため、default 群と異なり初期過渡が起こり得る。
保存長ごとの全 seed の平均と散らばりが揃っても、default 群の偏差の原因はこの一要因比較だけでは確定しない。

## 保存長比較60行の独立数値監査

main の `output/dev5/p_final/length/raw` の4個の実行 CSV、`aggregate/cohort_runs.csv` と `cohort_summary.csv`、および `length_derived.json` を読み取り専用で照合した。
raw の60行と集計の60行は全列一致し、保存長600・2400・9600の各群にseed 2026–2045が一度ずつ揃っている。
全行でdev4領域、固定burn180、4 chain、block長8、bootstrap30反復、ladder `0.3/0.26/0.22`、MC anchor1500試行、checked truth cache、およびsource凍結commit `05c70056e3cac6e9a92592daa6b186d86ceed773` が一致した。
同じseedの3長さでanchorと独立MCの全列が一致し、長さ以外の設定差を確認しなかった。
cacheの重みcountから真値を再計算し、anchor `0.7076851364881606`、target `0.602662564701594`、問題digestとpackage source digestの一致を確認した。
凍結commitから現mainまでの `src/mcmc4qec` に差分はなかった。

| 保存長 | MC平均bias | MC seed間SD | MC平均SE | exact換算平均bias | exact換算seed間SD | exact被覆 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 600 | -0.011914 | 0.025610 | 0.005727 | -0.010479 | 0.024223 | 13/20 |
| 2400 | -0.001230 | 0.012282 | 0.002746 | +0.000274 | 0.011622 | 20/20 |
| 9600 | -0.003251 | 0.006966 | 0.001558 | -0.001737 | 0.007136 | 20/20 |

ここでexact換算値は各seedの `exact_anchor × BAR推定値 / MC_anchor` であり、新たなMCMC測定ではない。
各行から平均、標本SD、平均SE、log比、seed対応差、seed 2026の推移を再計算し、集計CSVとJSONに数値丸めの範囲で一致した。
対応seedのMC推定値の平均差は2400−600で `+0.010684`、9600−600で `+0.008663`、9600−2400で `−0.002022` であり、最後の差のSEは `0.002497` だった。
exact換算値の対応差は順に `+0.010753`、`+0.008741`、`−0.002012` であり、log比の対応差も `+0.018620`、`+0.015387`、`−0.003233` と再計算で一致した。
9600のexact換算平均biasは平均SEの約1.09倍であり、この20seedから持続する偏りは確定しない。
600のexact換算平均biasは約1.93 SEで、2400では約0.11 SEと符号も変わるため、長さに対して単調なbiasを推定する根拠も弱い。
seed間SDの減少は観測事実だが、有限長BARの非線形biasがゼロになったことや名目95%区間の校正を証明しない。
20/20被覆のWilson 95%区間の下端は約0.839であり、短いblock長による区間不足を棄却できない。

MC anchorのseed間平均は `0.705967`、標本SDは `0.009640` だった。
真のBAR比を固定して独立1500試行anchorの二項変動だけを伝播させた理論SDは約 `0.010001` であり、対応する正規近似95%幅は約 `0.03920` となる。
9600の平均区間幅 `0.04114` はこのanchor由来の幅に近く、幅だけからMCMC成分の校正を読み取れない。
9600のMC推定値の観測SD `0.006966` が理論anchor SDより小さいことは、20seedの標本SDに理論的な下限があることを意味しない。
9600のanchorとBAR比の標本相関は `−0.591`、標本共分散は `−5.747e−5` であり、MC点推定の標本分散はexact換算成分 `5.092e−5`、anchor成分 `6.810e−5`、共分散の2倍 `−7.050e−5` の和 `4.852e−5` と一致した。
この負の標本共分散は観測SDが理論anchor SDを下回る算術上の説明となるが、固定20seedの相関だけで母集団の独立性を確証も否定もできない。
コード上は `bar_sensitivity.py` が `spawn_seeds(seed, 4)` の別子seedをanchor、BAR、独立MCに渡し、`spawn_seeds` は NumPy `SeedSequence.spawn` を使う。
さらに `estimate_logical_error` はBAR用seedから各rungとbootstrap用の子系列を分けるため、anchorとBARの独立性は乱数分岐の設計上の仮定であり、標本相関をゼロに固定する主張ではない。

default群の初期状態は条件付き標的から採られるため、今回の平均差を追加burn不足と断定する根拠はない。
9600の持続biasが未確定である現段階では、固定burn対5 IAT cutや4・16・50 chainの追加感度測定を今回実施せず12 cohortの被覆監査へ進む判断は妥当と考える。
この判断は原因候補の除外や追加感度の科学的不要性を意味しない。
後続の被覆比較ではdev4のdefault blockが13/20、低pのexact anchor付きdefault blockが14/20、paper全群の各seedに半trace上限が見られたため、追加感度は将来の別計画の候補として残る。

## 被覆比較12 cohort・240行の独立数値監査

mainの `output/dev5/p_final/protocol/raw` と修正版 `aggregate` を読み取り専用で照合し、事前固定の4構成×dev4領域MCおよび低p領域MC/exactの全12 cohortにseed 2026–2045が一度ずつあることを確認した。
rawの240行とaggregateの240行は全列一致し、mainに保存された `docs/wp/data_dev5/protocol` の27ファイルもoutputの対応ファイルとSHA-256で一致した。
全パッケージPython sourceから再計算したSHA-256 `50f47ab86aadb8ddc25142c696ce6cfbce631a8cf8357cbbca8ca33d397f56d5` はcacheと環境記録に一致した。
失敗重みcountsのdigestと総失敗状態数196608を確認し、dev4のexact真値 `0.602662564701594` と低pの `0.021074759859217335` をcountsから再計算した。
各行のladder、anchor、chain数、cut前後の長さ、lazy、block長8、bootstrap30反復、anchor1500試行、問題digest、真値source、区間端、log標準誤差、被覆判定を固定計画と式に照らして確認した。
各cohortの平均点推定、平均bias、平均区間幅、Wilson 95%区間、診断AND、半trace cap数はrawからの独立計算が実行別summaryとaggregate summaryの対応列に一致した。
seed間SD、平均SE、chain別cut長とcap率も独立再計算が `protocol_derived.json` に一致した。

| 構成 | dev4 MC 被覆 | 低p MC 被覆 | 低p exact 被覆 |
| --- | ---: | ---: | ---: |
| default_block | 13/20 | 18/20 | 14/20 |
| default_cross | 18/20 | 18/20 | 15/20 |
| paper16 | 17/20 | 20/20 | 19/20 |
| paper50 | 19/20 | 19/20 | 19/20 |

dev4のdefault blockとcrossは全seedで点推定、BAR比、cut、診断列が一致し、平均区間幅は `0.062566` から `0.096984`、被覆は13/20から18/20へ変わった。
対応seedでは5件がblockのみ真値を外し、残る15件の被覆判定は一致した。
低pのdefault block/crossも各anchor内で点推定と診断列が一致し、MCの被覆は両方18/20、exactは14/20と15/20だった。
低pの同一軌道におけるMC/exactのBAR比、cut、診断列は4構成の全seedで一致し、anchorを替えると点推定と区間の双方が変わることを確認した。
MC/exactの被覆差は独立した反復実験の差ではなく対応したseedの差であり、exact anchorの一般的な被覆悪化を意味しない。

| 領域・paper構成 | cut後長の最小／中央値／最大 | 半trace上限のchain | 上限のあるseed |
| --- | --- | ---: | ---: |
| dev4・16 chain | 125／132／230 | 474/960 | 20/20 |
| dev4・50 chain | 125／125／233 | 1503/3000 | 20/20 |
| 低p・16 chain | 125／201／235 | 396/1280 | 20/20 |
| 低p・50 chain | 125／202／236 | 1217/4000 | 20/20 |

paper16/50の全seedでchain別cutは不等長であり、全seedに少なくとも1 chainの半trace上限があった。
各seedとrungでpaper16のcut列はpaper50の先頭16 chainと一致したが、CSVにない保存状態の全要素一致までは検査できない。
このraw250の不等長chainへ適用した `cross_chain` の区間は漸近近似であり、研究論文の各chain 2,000,000 stepの精度を再現したという解釈はできない。
default4対paper16/50はchain数に加えて初期値、lazy、cut、trace長も変わるため、被覆差をchain数だけに帰属できない。
paper16対paper50は同じ設定でchainを追加する限定的な対応比較だが、20seedの結果を一般の最適chain数へ広げられない。

正式四条件の全合格は全cohortで0であり、最小・最大の論理基底初期状態が同一のため、他の三条件が合格したseedは不合格でなく未判定として扱った。
未判定数はdev4のdefault二群で各4、paper16で11、paper50で18、低pのdefault二群で各3、paper16で12、paper50で19であり、低pの両anchorで同数だった。
異なるfaulty初期状態による補助四条件合格数は今回この三条件合格数と一致したが、論文どおりのmultistart判定や収束証明の代わりにはならない。
P担当の最終 `P_ja.md`、`bar_sensitivity_ja.md`、`paper_consistency_ja.md` は上記数値、対応比較、論文手順との差、有限20seedと正規近似の限界を区別して記述していた。
このレビューでは重いsamplingを再実行せず、固定CSVの算術とsource・研究資料の読取を独立に行った。
