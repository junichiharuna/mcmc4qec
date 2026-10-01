# WP-E 複数 chain の診断と収束判定

2026-09-30 に作業した。

## 実装

`diagnose` を一つまたは複数の `Result` に対応させ、chain 間標準誤差、各 chain の IAT と ESS、split R-hat、kernel ごとの採択数と採択率を追加した。
既存の平均 IAT、合計 ESS、`rhat`、`acceptance` の名前は維持した。
`evaluate_convergence` に論文 Setup と研究側 `compare/convergence_flags.py` の四条件を実装し、未判定を `None` として明示した。
IAT と chain 間散らばりの第四条件には独立 direct MC の条件付き分散を要求し、未提供の場合は `None` として四条件全体を合格にしない。
chain 内分散を使う研究論文の一次判定は、別の参考値 `within_chain_dispersion` に残した。
分母がゼロで観測差が正なら明示的に fail とし、差もゼロなら識別不能の `None` とする。
負の自己相関では IAT を 1 に切り上げず、正値であれば ESS が標本数を超えることも報告する。
`minimum_weight_coset_representative` は小 rank を全列挙し、大 rank を SciPy MILP で厳密最適化する。
`logical_representatives` は各論理基底行をそのスタビライザーコセット内だけで最小化する。
最小重み初期化、最大重み初期化、非零ランダム論理セクター初期化、指定した観測セクターの初期化を追加した。
独立基底の交差行列を GF(2) で解くので `lx[i]` が観測量 i だけを反転させるとは仮定しない。
公開 API と式の限界は `docs/convergence_ja.md` に記した。

## 実行した検証

`%USERPROFILE%/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_initial_states.py tests/test_convergence.py -q` は 12 passed、2.09 秒だった。
同じコマンドの再実行は 12 passed、0.51 秒だった。
`%USERPROFILE%/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests -q` は 168 passed、57.40 秒だった。
第1回レビュー対応後の同じ全 suite は 177 passed、192.47 秒で、全 suite 5 分以内の制約を満たした。
MILP の整数最適証明を強化した後の focused tests は 16 passed、1.29 秒だった。
二盆地テストの direct MC 参照分散を定常混合分布の理論値 6.5 に揃えた後の focused tests は 16 passed、1.92 秒だった。
小 CSS 符号の各コセットを全列挙して最小重みとセクター保存を確認し、rank 13 の MILP 経路も検証した。
rank 13 の非自明なランダム行列について 8192 個のコセット要素と MILP 解の重みを比較し、一致した。
既知の相関を持つ AR(1) では四条件がすべて pass し、持続的な chain 別オフセット、後半ドリフト、独立分散との不一致では対応する条件が fail した。
二盆地の玩具 Markov 連鎖は確率 `10^-6` で盆地を移り、異なる固定初期盆地から始めた群では他の三条件が pass しても multistart が fail することを確認した。
負の自己相関を持つ AR(1) では IAT が 1 未満で ESS が標本数を超えることを確認した。
`CSSCode(logical_basis="independent")` の実オブジェクトで非単位の交差行列と指定観測セクターの保存を確認した。
第1回レビューのゼロ分母、独立分散未提供、負相関 IAT、二盆地、実 CSSCode の指摘には実装と回帰テストで対応した。
MILP には相対 gap ゼロと整数目的の双対下界検査を追加し、近似解を最適解として返さないことを強化した。
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
