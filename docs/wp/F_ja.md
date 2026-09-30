# WP-F 実符号の実行例と既存例のCLI統一

## 実装

`examples/bb72_bposd.py`、`examples/toric_depolarizing.py`、`examples/phenomenological_toric.py`、`examples/steane_exact.py` を追加した。
既存の直下6例に `--quick`、`--seed INT`、`--out DIR`、最後の `SUMMARY <json>` と `summary.json` を追加し、元の推定対象を維持した。
全例の既定出力先は `tempfile.gettempdir()/mcmc4qec/<script-stem>` で、`Path.resolve()` 後に `C:/dev/RIMC`、`A:/dev/RIMC` および `RIMC_RESEARCH_ROOT`、`RESEARCH_ROOT` 配下を拒否する。
各例は `--seed` から `spawn_seeds` で乱数を分岐し、Stimのreplay seedもそこから作る。
数値を出力する全例は絶対失敗率 `P_L` と条件付き期待値を区別し、条件付きchainの頻度から `P_L` を推定しない。

BB72例は評価確率と一致する固定 prior 0.08 で BP-OSD を一度だけ構築し、両者の一致を出力する。
depolarising例はI/X/Y/Zの同時カテゴリから標本を引き、X/Z独立sectorの合成はデコーダー選択であることをコメントと出力に残し、chain標本のX/Y/Z個数を示す。
phenomenological例はclean初期境界、perfect最終測定、round-majorのsyndrome差分を用い、公開 `PhenomenologicalModel` の各単一fault座標から全時空間check列と最終論理observable列を組み立てる。
`HistoryDecoder(layout='round_major_flat')` が全ラウンドを `matching_from_check_matrix` に渡し、表示する `P_L` はTラウンド全実験の確率である。
Steane例は7ビット全状態から各syndromeの最小重み訂正と決定的tie-breakを求め、同じデコーダーでexact、direct MC、exact anchor付きBARを全3 rungで比較する。
BARの区間は混合とblock長を仮定し、診断が収束、エルゴード性、正しさの証明にならないことを出力に記した。
既存の物理回路例はZ/H/stabilizerを選ばず、`KernelConfig(circuit_single=1, single=0, zanella=0, cluster=0, stabilizer=0)` を明示した。

既存6例のSUMMARY key集合はbit_flipが `exact, pl, pl_interval, ew_exact, ew_chain`、three_noiseが `cases`、bar_ladderが `ladder, bar, intervals, exact` である。
残りはtoric_pymatchingが `code, p, pl, pl_interval, ew_direct, ew_chain`、stim_demが `mechanisms, exact, pl, pl_interval`、circuit_baselineが `locations, detectors, pl, pl_interval` である。
既存のREADMEとtutorialのコードブロックはスクリプト本体をimportしていないため、CLI追加による変更はない。

## 実測と検証

主記録は指定Python 3.11から作成されたdev3 optional wheel用venvの `C:/dev/mcmc4qec/.venv-dev3-optional/Scripts/python.exe -I examples/<stem>.py --out C:/Temp/mcmc4qec-f-wheel-primary/<stem>/default` と、同じコマンドに `--quick` を加えて出力先をquickにした実行である。
全例でCLI既定seed `20260930` を使い、bit_flipは `18`、bar_ladderは `73`、toric_pymatchingは `11`、stim_demは `41`、circuit_baselineは `2026` を使った。
下表はPowerShell `Diagnostics.Stopwatch` の実測経過時間であり、全例がdev3 installed wheelを`-I`で読み、連続実行中には他WPの作業負荷も存在した。

| 例 | 既定秒 | quick秒 | 結果 |
| --- | ---: | ---: | --- |
| bit_flip.py | 2.549 | 0.292 | 両方exit 0 |
| three_noise.py | 4.340 | 1.158 | 両方exit 0 |
| bar_ladder.py | 0.503 | 0.348 | 両方exit 0 |
| toric_pymatching.py | 1.008 | 0.680 | 両方exit 0 |
| stim_dem.py | 0.476 | 0.225 | 両方exit 0 |
| circuit_baseline.py | 3.908 | 1.441 | 両方exit 0、mainのdev3回路構築修正を使用 |
| bb72_bposd.py | 1.951 | 0.712 | 両方exit 0 |
| toric_depolarizing.py | 1.521 | 0.708 | 両方exit 0 |
| phenomenological_toric.py | 0.952 | 0.644 | 両方exit 0 |
| steane_exact.py | 2.354 | 0.516 | 両方exit 0、BAR区間のexact被覆は既定2/3、quick1/3 |

Steaneの被覆は有限標本とseedに依存するので全seedの保証ではなく、各rungの真偽と合計を例が表示する。
探索時の `--seed 2` ではSteaneのBAR区間は既定・quickとも3/3でexactを含んだが、この結果を主記録の代わりにはしない。

`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_examples_real.py -q` は11 passed、15.27秒だった。
このテストは10例を `sys.executable` の子processでquick実行し、pytestがimportした同じ `mcmc4qec` の親ディレクトリを子processの `PYTHONPATH` に設定して、終了値、最終SUMMARY key集合、保存JSONを確認する。
追加の拒否試験は環境指定の研究root配下を `--out` にした場合に失敗し、出力先が作られないことを確認する。
全suite、installed wheel、CIはこのWPで未実施であり、統合担当が検証する。

## 10秒上限の未解決点と共有依頼

WP-F着手時のsourceでは `circuit_baseline.py --quick` は80試行でも12.431秒で、d=3のsurface論理idle構築単体は10.88秒だった。
公開 `surface_logical_idle_problem` は奇数distance 3以上しか受けないため、quickでdistanceを下げずに既存の物理的意味を維持した。
`cProfile` では同構築11.62秒中 `CircuitFaultModel.__init__` が11.06秒で、2588回の `simulate_state` に伴う `stim.Circuit.append` 402801回が8.96秒を占めた。
メインには `src/mcmc4qec/circuit/model.py` の非noise連続命令区間をキャッシュして回路再構築を短縮する小さい修正案と、既存回路試験・全単一faultのH/L列一致による受入案を共有した。
メインが `aae4b0c` でsrcの構築経路を修正し、dev3 optional wheelで再測定したquickは1.441秒だった。
本WPではsrcを編集しておらず、主記録の全10例がquick10秒と既定120秒の上限内で動いた。
