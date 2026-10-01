# WP-M 完了メモ：BAR 被覆と感度

## 小仕様と実装範囲

同一 `Problem` の fixed-failure BAR と独立 direct MC を exact 真値で比較し、seed を事前に固定した反復の被覆数、区間幅、非交差数を数えることを受入条件とした。
各感度実行は一つの要因だけを変え、10 分を超える sweep は分割することとした。
`benchmarks/bar_sensitivity.py` は toric d=3 の exact、BAR、MC、IAT、overlap、区間を seed ごとの CSV と要約 CSV に出力する。
`tests/test_bar_coverage.py` は 2 bit の列挙できる failure 問題で 10 seed の BAR 区間を exact と比べ、5/10 未満という極端な被覆低下だけを検知する軽い回帰テストである。
科学的数値と一要因感度、20 seed の各行、利用者向け指針は `docs/bar_sensitivity_ja.md` に保存した。
担当範囲の 4 ファイル以外と `src/` は変更していない。

## 実行した検証

全て `A:/dev/mcmc4qec-wt/m` で、`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe` を使用した。
`PYTHONPATH=src` を設定して `python examples/workflows/pl_curve.py --out <一時ディレクトリ>` を既定 seed 2026 で実行し、d=3、p=0.22 の BAR 0.5344713861、区間 [0.5055163266, 0.5650849390] と独立 MC 0.5991666667、区間 [0.5711650330, 0.6265354185] の非交差を再現した。
同じ問題の `exact` 全列挙は p=0.30、0.26、0.22、0.10 で順に 0.7076851365、0.6676781708、0.6026625647、0.2261084104 を返し、別の p=0.50 の全列挙は 0.75 を返した。
既定例の単発比較では真値を含むのは独立 MC の区間であり、BAR 区間は外れる。
`python benchmarks/bar_sensitivity.py --scenario baseline --seeds 20 --out <一時ディレクトリ>` は 349.11 秒で、BAR exact 被覆 13/20、独立 MC 20/20、区間非交差 2/20、平均 BAR 幅 0.06257 だった。
`--scenario` を `samples_short`、`samples_long`、`burn_zero`、`burn_long`、`block_tenth_iat`、`block_one_iat`、`block_four_iat`、`ladder_fine`、`ladder_coarse`、`initial_min`、`initial_random`、`initial_max`、`anchor_exact` にして各 `--seeds 8` を実行し、元の `baseline_summary.csv` の exact 値を `--truth-file` で再利用した。
`low_p` は `--seeds 8` で p=0.10 を改めて exact 列挙した。
既定 20 seed の実行が最長の 349.11 秒で、感度 8 seed の各 invocation は全て 186 秒以下だった。
`python -m pytest tests/test_bar_coverage.py -q` は 1 passed、5.97 秒だった。
`--out A:/dev/RIMC/wp_m_forbidden` はディレクトリ作成前に `ValueError: Refusing to write into the read-only RIMC repository` で停止した。
一時出力先の `baseline_summary.csv` を再利用した各数値は、初回 exact p=0.22 の 0.6026625647 と一致した。
現在の CLI は異なる問題の真値 CSV を自動識別しないため、再利用には `--trust-truth-file` の明示が必要である。
最初の感度実行はこの明示フラグを追加する前に行い、最終コードでの追加フラグは同じ入力 CSV の利用者による確認を要求する。

| 条件 | BAR exact 被覆 | 平均 BAR 区間幅 | 非交差 |
| --- | ---: | ---: | ---: |
| 基準 20 seed | 13/20 | 0.06257 | 2/20 |
| 基準の先頭 8 seed | 4/8 | 0.06321 | 2/8 |
| 保存 200 / 1200 | 6/8 / 8/8 | 0.07677 / 0.05419 | 2/8 / 0/8 |
| burn-in 0 / 600 | 7/8 / 7/8 | 0.06140 / 0.06542 | 0/8 / 0/8 |
| block 3 / 27 / 107 | 4/8 / 7/8 / 7/8 | 0.04817 / 0.07616 / 0.08562 | 2/8 / 1/8 / 1/8 |
| ladder coarse / fine | 6/8 / 7/8 | 0.07103 / 0.05371 | 0/8 / 1/8 |
| 初期 minimum / random / maximum | 6/8 / 5/8 / 6/8 | 0.06275 / 0.06294 / 0.06275 | 1/8 / 0/8 / 1/8 |
| exact anchor | 4/8 | 0.04991 | 2/8 |
| p=0.10 の低 p ladder | 8/8 | 0.02922 | 0/8 |

基準の block 8 は最大 chain 重み IAT の seed 間中央値 35.69 より短い。
同じ chain に対する block 3/27/107 の変更で区間は広がるが、非交差だった seed 2026 は block 107 でも exact 真値を含まなかった。
exact anchor に替えても先頭 8 seed の BAR 被覆と非交差数は変わらず、今回の MC anchor 誤差を主因とする根拠はない。
既定 20 seed の交差 support 有限率は全て 1、最小 BAR overlap は 0.4661–0.4898 で、観測 support 欠落はない。
seed 2026 は保存 1200 または burn-in 600 で点推定が真値に近づき、短い chain の分布差に感度があった。
ただし 8 seed の Wilson 区間は広く、block 不足と混合不足の寄与を確定的に分離できない。
minimum と maximum の初期状態は同じ配列で、8 seed の CSV は scenario 名以外完全一致したため、異なる初期重みの効果はこの符号では検証できなかった。
重み trace の IAT、区間被覆、初期状態比較はいずれも収束、エルゴード性、正しさの証明ではない。

## ライブラリの誤りの判定と残る作業

今回の証拠では BAR の式や block bootstrap 実装に最小修正を要する誤りは特定しなかった。
seed 2026 の block 増大後も残る点推定の差は、短い条件付き chain の有限標本・混合の候補を示すが、1 seed の調整結果だけで原因を断定しない。
`src/mcmc4qec/estimation.py` の変更案と回帰テスト案は現時点ではない。
大符号、より低い p、長い chain の多数 seed、BAR score 自体の IAT と経路間移動、研究精度での 95% 被覆校正は未実施である。
今回の基準 20 seed の Wilson 区間は BAR [0.433, 0.819] と広く、設定の最適値を保証しない。

## メインへの依頼

`examples/workflows/pl_curve.py` の冒頭説明と最後の説明に、既定 d=3、p=0.22 の exact 真値 0.6026625647、seed 2026 で BAR 区間だけが真値を外すこと、20 seed で BAR 13/20・独立 MC 20/20 の探索結果を `docs/bar_sensitivity_ja.md` へリンクして追記してほしい。
同じ説明で、既定 block 8 は観測した重み IAT 中央値 35.69 より短く、block を延ばすと区間は広がるが seed 2026 の点推定差は残ると明記してほしい。
`notebooks/02_pl_curve_with_bar.ipynb` の markdown cell 3 に、今回の範囲の既定最小 overlap が約 0.48 であり今回の非交差は support 欠落の証拠ではない旨を加えてほしい。
同 notebook の markdown cell 5 に、上記 exact 比較、20 seed の探索的被覆、block と chain 長の感度、短い実行を研究精度の保証にしない旨を加え、`notebooks/regenerate.py` で出力を再生成してほしい。
`examples/README.md` の benchmark 行案は「`benchmarks/bar_sensitivity.py`｜toric d=3 の BAR/direct MC 被覆と一要因感度｜`codes,matching`｜baseline 20 seed 349.11 秒、各感度 8 seed は 186 秒以下｜CSV の exact 被覆、区間幅、IAT、overlap を読む」である。
公開 API の追加、README の機能表、CI の新 job は不要であり、既定 block 長を変更するかは所有者判断とする。
メインでの統合後全 suite、installed wheel、notebook 再生成、remote CI はこの WP では未実施である。
