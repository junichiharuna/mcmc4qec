# WP-P 完了メモ：BAR 不確かさと論文手順の照合

## 小仕様と実装

`estimate_logical_error` の `uncertainty` は既定を `block_bootstrap` に固定し、`cross_chain` を追加した。
`cross_chain` は保存軌道と pooled BAR 点推定をそのまま使い、同じ chain 番号の隣接 BAR log ratio を組にして標本共分散を chain 数で割る。
この組により共有 rung を通じた比の相関を含め、anchor の独立 log 分散を従来どおり別に加える。
これは論文 `main.tex` 615–623 行の観測量平均に対する cross-chain 標準誤差を BAR に漸近的に適用したものであり、論文が full BAR の被覆を検証したと主張しない。
chain が 1 本なら `ValueError` とし、各 chain に双方向 overlap がないときは点推定を残して MCMC 区間を未定義にする。
既定引数、点推定、seed 系列、block bootstrap の計算経路は維持した。
`uncertainty_method` は既存の metadata に方法を記録し、cross-chain の比の共分散も metadata に保存する。

`benchmarks/bar_paper_protocol.py` は同一 seed の保存軌道を block と cross-chain で再利用できる設定を持ち、固定 cohort 2026–2045 の一部を invocation ごとに出力する。
`--samples` は固定 cut 群では cut 後の保存数を表し、paper 群では IAT cut 前の全 trace 歩数を表し、CSV に `total_steps` と各 chain の cut を残す。
paper 設定は研究 `src/postprocess.py` と `cluster_scripts/lowp_audit.py` に合わせ、各 chain ごとに最初の負の自己相関で打ち切る IAT を反復推定し、5·IAT の cut が非収束なら半 trace に落とす。
この反復 cut を `diagnostics.py` の `paper_burn_in_cut` に分離し、既存の初期正値ペア IAT とその API 挙動は変えなかった。
paper 設定は研究 runner に独立 lazy 抽選がないため `lazy=0` とし、現行既定の 4 chain 設定は `lazy=0.05` を維持する。
論文本文の各 chain の記述と研究の実験 runner は一致し、`postprocess.py` の 2D 入力だけにある共通中央値 cut はこの実験では使わない。
四条件の scaling と drift は未burnの checkpoint、multistart と dispersion は各 chain の burn 後を用いる。
toric d=3 の最小・最大論理基底状態は同一なので、論文どおりの multistart 判定は未判定とし、残る三条件の合格を `paper_vacuous_pass` に分離する。
`--aux-multistart` は異なる faulty な論理組合せから追加 chain を走らせ、その補助四条件を別の欄へ記録する。
BAR の ragged な burn 後標本は pooled BAR を解き、chain 単位の比の散らばりで区間を作るため、同数標本の API に対する漸近誤差近似を不等長 chain に延ばしたものである。
`--make-truth-cache` は同一問題の失敗重みヒストグラムを一度列挙し、符号行列と問題 metadata、パッケージ source、重み counts の SHA-256 を付けて保存する。
`--truth-cache` はその digest を検証し、各 p の exact 真値と exact anchor を重みヒストグラムから求める。
`cached_exact` は重みごとの確率質量の加重和から exact 条件付き重みも復元する。
低 p の `--anchor both` は MC と exact anchor に対して同じ rung 状態・cut・BAR 比・MCMC log 分散・収束診断を一度だけ計算して再利用し、anchor ごとの per-seed CSV と要約 CSV を別々に出す。
`--aggregate` は checked truth cache を必須とし、各 CSV の問題 digest と exact 真値を再計算して一致し、設定ごとに 2026–2045 が重複なく全件ある場合だけ cohort CSV を作る。
per-seed CSV、要約 CSV、標準出力には、診断は証明でないこと、有限 chain の BAR bias は区間外であること、toric の論文 multistart が未判定であること、不等長 cut の cross-chain 共分散が漸近近似であることを明記する。
`bar_sensitivity.py` の正式長さ比較も同じ checked cache から exact 真値と条件付き重みを復元し、20 seed の重複・欠落と provenance を検査してから集計する。
過去の `--truth-file` 入口は WP-M の既存実験用に残すが、dev5 の正式計測には使用しない。

## 実行済みの検証

すべて `A:/dev/mcmc4qec-wt/p` で Python 3.11 の `A:/dev/mcmc4qec/.venv-dev5-source/Scripts/python.exe` を使用した。
研究を参照する際は `RIMC_RESEARCH_ROOT=A:/dev/RIMC` と `PYTHONDONTWRITEBYTECODE=1` を設定し、研究側へ書き込まなかった。
研究側の `git status --porcelain=v1` は出力なしだった。
`python -m pytest tests/test_crossval_research.py -q` は 20 passed、2.13 秒で、凍結された研究 BAR 値 `-1.2130084485394683` とライブラリの Fermi 関数の値の一致を含む。
この照合は live pymbar を再計算するテストではない。
別に `PYTHONDONTWRITEBYTECODE=1` と `RIMC_RESEARCH_ROOT=A:/dev/RIMC` を設定し、読み取り専用 import した研究 `src/splitting_pl.py` の `estimate_pl_ladder_bar` と同じ合成 trace を live pymbar 4.0.3 で評価した。
研究の log ratio `-1.2130084485394683` とライブラリの `-1.213008448539711` の絶対差は `2.426947531830592e-13` だった。
`python -m pytest tests/test_bar_uncertainty.py tests/test_estimation.py -q` は anchor 分散の追加テスト前に 15 passed、8.09 秒だった。
追加後の `python -m pytest tests/test_bar_uncertainty.py -q` は 5 passed、5.62 秒だった。
反復 cut のテスト追加後の同じコマンドは 6 passed、4.94 秒だった。
現行差分の `python -m pytest tests/test_bar_uncertainty.py tests/test_estimation.py tests/test_crossval_research.py -q` は JSON 往復の追加 assert 前に 37 passed、10.57 秒だった。
JSON 往復の追加 assert 後の `python -m pytest tests/test_bar_uncertainty.py -q` は 6 passed、5.78 秒だった。
最終実装差分の `python -m pytest tests/test_bar_uncertainty.py tests/test_estimation.py tests/test_crossval_research.py -q` は 32 passed、5 skipped、9.26 秒だった。
合成 chain の既知の標準誤差と共有 rung の負の共分散、同 seed の点推定一致、1 chain と不正方法の拒否、10 seed の小問題の被覆の緩い回帰を確認した。
研究 `paper/main.tex` 261–282 行の Fermi 関数 `h(t)=1/(1+t)` と `bennett_log_ratio` の score の符号、`src/splitting_pl.py` の BAR の向きを照合した。
研究 `src/postprocess.py` の 1D `burn_in(method="tau",c=5)` と benchmark の `paper_burn_cut` を同じ seed 71 の長さ 250 の合成重み trace に適用し、cut 6 と cap `False` が一致した。
`python -m py_compile benchmarks/bar_paper_protocol.py benchmarks/bar_sensitivity.py src/mcmc4qec/estimation.py tests/test_bar_uncertainty.py` は成功した。
旧 protocol の `--quick --protocol paper50 --region paper --anchor exact --aux-multistart` は 199.98 秒で動作したが、旧共通 cut と burn 後 checkpoint を使うため最終表には使わない。
修正版の `--quick --protocol default_block --region dev4 --anchor mc --verify-api` は 88.62 秒で動作し、seed 2026 の benchmark と API の点推定、全隣接比、log 標準誤差、区間が許容差 `1e-12` 以内で一致した。
この短い実行の点推定 0.43237450 と区間幅 0.077939 は保存 80 の smoke であり、被覆を評価する数値として使わない。
Q 統合後の `--quick --protocol default_cross --region dev4 --anchor mc --truth-cache <cache> --verify-api` は 2.57 秒で、benchmark と API の点推定・比・標準誤差・区間が一致した。
同じ Q 統合後の paper 領域 `--quick --protocol default_cross --anchor both --aux-multistart --verify-api` は 4.26 秒で、MC と exact の両方が API と一致した。
同条件の `default_block` でも MC と exact の両方が API と一致し、4.0 秒以内に終わった。
その MC CSV と単独 `--anchor mc` の CSV は全列一致し、MC/exact 間では BAR 比、cut、scaling、drift、補助 multistart、dispersion が全て一致した。
paper50・paper 領域・全長 250・補助初期値有の seed 2026 でも、`--anchor both` の MC CSV は単独 MC と全列一致し、exact CSV は単独 exact とファイルの bytes が完全一致した。
同じ seed の MC/exact の BAR 比、cut、scaling、drift、補助 multistart、dispersion は一致し、両 anchor を同時に出す所要時間は 19.84 秒だった。
これらは seed 2026 の短い smoke であり、名目被覆の根拠ではない。
Q 統合後の `--make-truth-cache` は全 262144 状態を 36.2 秒で列挙し、失敗状態数 196608、問題 SHA-256 `16d53d251117bb3f52c9e7cff4aa63514d16409364f7d7b7e773977db84f974d`、counts SHA-256 `909d867052c997ee5d0445df5701dd6b8ff1295d61d497af64a36438195056af` を得た。
直接 `exact()` と cache の値は p=0.22 で `0.6026625647015839` と `0.602662564701594` の差 `1.01e-14`、p=0.03 で `0.02107475985928002` と `0.021074759859217335` の差 `6.27e-14` だった。
pilot の package source SHA-256 は `9a09dd24288f3d60bccdd8eef131d538b1357ba07842cb33f0fa81bf81548462` であり、dev5 version を組み込む最終 main の cache は再生成する。

## dev5 最終計測

計測前に [固定計画](data_dev5/measurement_plan.json) の全条件と seed 2026–2045 を確定し、main の `0.1.0.dev5`、sampling source commit `05c7005`、package source SHA-256 `50f47ab86aadb8ddc25142c696ce6cfbce631a8cf8357cbbca8ca33d397f56d5` で実行した。
最終 truth cache の問題 digest と全失敗重み counts は Q 統合後 pilot と完全一致し、source/version の digest だけが変わった。
長さ比較の60行は各保存長20 seed と cache provenance を集計で検証し、9600 は事前固定の10 seedずつを483.03秒と469.46秒で実行した。
9600の全20 seedは合計約953秒であり、全体が600秒以内だったという意味ではない。

| 保存数/chain | MC anchor BAR 平均 bias | seed 間 SD | 平均の SE | BAR exact 被覆 | seed 2026 点推定 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 600 | −0.011914 | 0.025610 | 0.005727 | 13/20 | 0.534471 |
| 2400 | −0.001230 | 0.012282 | 0.002746 | 20/20 | 0.590558 |
| 9600 | −0.003251 | 0.006966 | 0.001558 | 20/20 | 0.593408 |

同 seed の点推定差の20本平均と SE は2400−600が `+0.010684 ± 0.004678`、9600−600が `+0.008663 ± 0.005146`、9600−2400が `−0.002022 ± 0.002497` だった。
同じCSVのBAR比を exact anchorへ再換算した補助平均 bias は順に `−0.010479`、`+0.000274`、`−0.001737` で、9600の残差は平均の約1.09 SEだった。
9600のMC anchor点推定の平均残差は約2.09 SEだが、20 seedの標本ではanchor値とBAR比の相関が `−0.59118` となり、観測SDが単純なanchor分散目安より小さい。
これを真の負相関や持続的biasの証明とせず、追加burn・chain感度は今回の事前計画では発動しなかった。
既定初期化はこの固定decoder問題で失敗条件付きtargetからの棄却標本なので、default群の長さ差を初期過渡と断定しない。
全行、集計、派生値と再計算コードは [長さデータ](data_dev5/length/aggregate/cohort_runs.csv) と [派生JSON](data_dev5/length/length_derived.json) に保存した。

被覆比較はdev4 ladder `[0.30,0.26,0.22]` と低p ladder `[0.10,0.07,0.05,0.03]` の各4構成を固定し、低pでは両anchorを同軌道から出して8回のsamplingから12 cohortを作った。
4 chainはcut後600、paper16/50はcut前raw250、全構成に異なるfaulty startの補助診断を付けた。
8 invocationの20 seed実測はdev4で `91.42/82.24/97.96/271.11` 秒、低pで `124.71/111.20/138.86/409.82` 秒となり、いずれも600秒以内だった。
修正済みaggregateは12 cohort×20 seedの240行を検証し、同点推定のblock/cross、MC/exactのBAR比・cut・診断の一致を [派生解析](data_dev5/protocol/protocol_derived.json) で照合した。
16 chainと50 chainはSeedSequence設計上先頭16 chainを共有し、CSVに残る全seed・rungの先頭16本のcut列が一致したが、保存状態列の全要素をCSVから再照合したとは主張しない。
未判定のPython `None` はCSVで空欄になるため、集計は両表現を同じ未判定として扱う修正をbenchmark commit `850fa0f` で統合した。
この修正は集計だけであり、sampling sourceとraw数値は変えていない。
全12 cohortの被覆数、Wilson区間、平均bias、seed間SD/SE、平均幅と四条件は [BAR感度の最終表](../bar_sensitivity_ja.md) に示す。
paper16/50のraw250は論文の各chain 2,000,000 stepから大幅に短く、全4群で20/20 seedに半trace capがあり、この計測を論文精度の再現や収束の証明とは扱わない。

## 統合状態と所有者判断

`docs/api_en.md` には既定block bootstrapと追加cross-chainの契約、共有rung共分散と独立anchor分散、2 chain下限と少数chain正規近似の制約をmainが反映した。
README、`examples/workflows/pl_curve.py`、notebook 02の短い実行と被覆に関する説明はmainが更新し、既定notebook再生成とwheelのcore/optional検証を完了した。
公開既定の誤差法、chain数、保存長を自動変更する提案はせず、20 seedの有限精度と費用を示して所有者判断に残す。
default4とpaper16/50の間ではchain数以外に初期状態、lazy、burn、trace長も同時に変わるため、結果差の単独原因を指定できない。
paper16とpaper50の間は同じraw250・開始・lazy・cut規則でchain数だけを増やす限定的な感度比較だが、20 seedから一般化しない。
診断と被覆探索は混合・エルゴード性・BARの正しさや名目95%被覆を保証しない。
PyPI公開、研究repo変更、pushは行っていない。
