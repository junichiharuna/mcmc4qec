# WP-P 独立レビュー：実装段階

## 対象と判定

`f2799a1` からの WP-P 差分と、真値入力および集計の追補修正をレビューした。
実装段階では、後述の真値 CSV の検証不足が修正された後に残る重大な実装上の指摘はない。
WP-Q 統合後の main で取得する最終科学 CSV は未実施・未監査であり、被覆、bias、分散、論文手順の再現についての最終合格判定は保留する。

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

## 最終科学 CSV の再監査項目

Q と P の統合および版番号更新後の main の source digest に合う truth cache を使い、各構成の固定 seed 2026–2045 が重複も欠落もなく、真値・anchor 種別・chain 数・burn・lazy・長さ・誤差法・bootstrap反復数が計画と一致することを検査する。
同じ軌道の default block と default cross で点推定が一致し、区間幅と被覆だけの比較になっていることを検査する。
保存 600・2400・9600 の全20 seedの平均差、seed 間散らばり、対応する seed 間の差、seed 2026 の推移を併記し、`1/sqrt(N)` に似た推移を bias 不在の証明と扱わないことを検査する。
4構成と2領域および論文領域の MC と exact anchor の表に、被覆数、Wilson 区間、平均幅、平均点推定と exact の差、四条件の合否と未判定数が揃うことを検査する。
短い paper trace と不等長 cut を論文の 2,000,000 step の再現と呼ばず、20 seed の被覆差を設定の優劣や名目95%の保証と断定しないことを検査する。
