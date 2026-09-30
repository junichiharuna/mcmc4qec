# WP-E 複数 chain の診断と収束判定

2026-09-30 に作業した。

## 実装

`diagnose` を一つまたは複数の `Result` に対応させ、chain 間標準誤差、各 chain の IAT と ESS、split R-hat、kernel ごとの採択数と採択率を追加した。
既存の平均 IAT、合計 ESS、`rhat`、`acceptance` の名前は維持した。
`evaluate_convergence` に論文 Setup と研究側 `compare/convergence_flags.py` の四条件を実装し、未判定を `None` として明示した。
IAT と chain 間散らばりの比較には独立 direct MC の条件付き分散を渡せ、渡さない場合は chain 内分散を使う旨を warnings に残す。
`minimum_weight_coset_representative` は小 rank を全列挙し、大 rank を SciPy MILP で厳密最適化する。
`logical_representatives` は各論理基底行をそのスタビライザーコセット内だけで最小化する。
最小重み初期化、最大重み初期化、非零ランダム論理セクター初期化、指定した観測セクターの初期化を追加した。
独立基底の交差行列を GF(2) で解くので `lx[i]` が観測量 i だけを反転させるとは仮定しない。
公開 API と式の限界は `docs/convergence_ja.md` に記した。

## 実行した検証

`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_initial_states.py tests/test_convergence.py -q` は 12 passed、2.09 秒だった。
同じコマンドの再実行は 12 passed、0.51 秒だった。
`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests -q` は 168 passed、57.40 秒だった。
小 CSS 符号の各コセットを全列挙して最小重みとセクター保存を確認し、rank 13 の MILP 経路も検証した。
既知の相関を持つ AR(1) では四条件がすべて pass し、持続的な chain 別オフセット、後半ドリフト、二盆地の異なる初期値、独立分散との不一致では対応する条件が fail した。
`sample_faulty` に最小および最大重みの `(chains,n)` 初期状態を渡して metadata への記録も確認した。

## 未実施

研究論文の本計算データと全 entry の判定照合は未実施。
BB72 など大規模符号での MILP 完了時間測定は未実施。
installed wheel での検証は未実施。
診断良好によるエルゴード性の証明は行っていない。
研究リポジトリ `C:/dev/RIMC` の `git status --short` は空であり、変更はなかった。

## メインへの依頼

`__init__.py` に `evaluate_convergence`、`minimum_weight_coset_representative`、`logical_representatives`、`minimum_weight_initial_state`、`maximum_weight_initial_state`、`random_logical_sector_initial_state`、`observable_sector_initial_state` を公開名として追加してほしい。
`docs/api_en.md` へ各公開名を追加してほしい。
`sampling.py` の変更は不要であり、本 WP では編集していない。
