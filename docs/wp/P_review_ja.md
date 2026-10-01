# WP-P 独立レビュー：実装段階

## 対象と判定

`f2799a1` からの WP-P 差分と、真値入力および集計の追補修正をレビューした。
実装段階では、後述の真値 CSV の検証不足が修正された後に残る重大な実装上の指摘はない。
WP-Q 統合後の main で取得した保存長比較60行は後述のとおり独立監査したが、12 cohort の被覆 CSV は未監査であり、被覆と論文手順の再現についての最終合格判定は保留する。

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
この判断は原因候補の除外や追加感度の科学的不要性を意味せず、後続の被覆・診断で系統的な異常が出れば測定前に条件を固定して再検討する。

## 残る最終科学 CSV の再監査項目

Q と P の統合および版番号更新後の main の source digest に合う truth cache を使い、各構成の固定 seed 2026–2045 が重複も欠落もなく、真値・anchor 種別・chain 数・burn・lazy・長さ・誤差法・bootstrap反復数が計画と一致することを検査する。
同じ軌道の default block と default cross で点推定が一致し、区間幅と被覆だけの比較になっていることを検査する。
保存 600・2400・9600 の全20 seedの数値監査は上記のとおり完了したが、後続文書でも `1/sqrt(N)` に似た推移を bias 不在の証明と扱わないことを検査する。
4構成と2領域および論文領域の MC と exact anchor の表に、被覆数、Wilson 区間、平均幅、平均点推定と exact の差、四条件の合否と未判定数が揃うことを検査する。
短い paper trace と不等長 cut を論文の 2,000,000 step の再現と呼ばず、20 seed の被覆差を設定の優劣や名目95%の保証と断定しないことを検査する。
