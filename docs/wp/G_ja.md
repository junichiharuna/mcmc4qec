# WP-G 完了メモ

## 作成したもの

`examples/workflows/pl_curve.py` は固定 MWPM デコーダーで toric d=3,5 の BAR 曲線を作り、最大 p の direct MC を anchor として観測失敗数を表示し、残りの 2 rung に独立 direct MC 確認点を置く。
表と図の anchor 点はその同じ MC anchor を再利用しており、独立な照合ではなく、CSV と SUMMARY の `mc_role` に `anchor_reuse` と記録する。
両区間の交差真偽を各行の CSV、標準出力、SUMMARY の `checks` 内に残し、非交差では原因未特定として調査を促す警告を出す。
`--quick` は実行経路の確認用であり、研究精度を保証しないことを表示する。
通常の ladder は `[0.30, 0.26, 0.22]` で、CSV と matplotlib Agg の PNG に BAR と direct MC の両区間を保存する。
最終設定の `SamplingConfig` は 4 chain、quick 40 samples と 12 burn-in、既定 600 samples と 180 burn-in で、MC anchor は quick 200・既定 1500 試行、他の確認点は quick 180・既定 1200 試行とする。
`--demo-overlap` は共通 failure 集合を持つ説明用 1 bit 問題の端点 `[0,1]` を実際の `estimate_logical_error` に渡し、排他的 support による `OverlapError` を捕捉する。
toric の内点 `0<p<1` は full support なので、単に p の刻みを粗くしただけで厳密な zero support が生じたとは説明しない。
`examples/workflows/conditional_weight.py` は toric d=5 の複数 p で独立 direct MC と Z+H 条件付き chain の `E[w|faulty]` を CSV と PNG に比較し、chain 頻度が絶対 `P_L` を与えない理由を出力する。
`examples/workflows/convergence_check.py` は asymmetric toric (3,5) で最小・無作為論理セクター・最大の異なる初期状態を使い、各群 2 chain の trace と独立 direct MC の条件付き重み分散を使って 4 条件を表示する。
この例は最小群と他の 2 群をそれぞれ比較し、各群の ESS と split R-hat、および診断が収束・エルゴード性・正しさの証明にならない警告を表示する。
無作為セクターが最小または最大と衝突した場合は `--seed` から派生した別 seed で選び直し、64 回衝突した場合は残る論理セクターを明示構築し、3 初期状態の相違を必ず検査する。
`examples/workflows/p_dependent_decoder.py` は BB72 に固定 p の BP-OSD を 1 回だけ作る standard ladder と明示的な `p_dependent_decoder_approx` を並べ、後者の区間に decoder 変更の bias が含まれないことを表示する。
4 例とも `--quick`、`--seed`、`--out`、tempfile 配下の既定出力、最後の `SUMMARY` JSON、seed から派生した RNG、出力先 resolve 後の `C:/dev/RIMC`、`A:/dev/RIMC`、`RIMC_RESEARCH_ROOT`、`RESEARCH_ROOT` 配下拒否を実装した。
`tests/test_examples_workflows.py` は subprocess による quick 実行、SUMMARY キー、CSV/PNG、描画不能時の CSV、overlap 実演、研究リポジトリ出力拒否を確認する。

## 実行した検証

Python は `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe` を使用した。
source 実行では `PYTHONPATH=src` を指定し、例の本体には source path 挿入を入れていない。
`python -m pytest tests/test_examples_workflows.py -q` は 18 passed、38.91 秒だった。
衝突が起きた seed `0,1,2,3,4,5,7,8,9` について、出力された 3 初期論理セクターが互いに異なることを性質として検査した。
区間が `None` のときに未判定と明示警告する追加テスト `python -m pytest tests/test_examples_workflows.py::test_missing_bar_interval_is_reported -q` は 1 passed、0.52 秒だった。
各例を `python examples/workflows/<名前>.py --quick --seed 2026 --out output/wp_g_quick_<名前>` と既定設定の `python examples/workflows/<名前>.py --seed 2026 --out output/wp_g_default_<名前>` で個別実行し、終了コード 0 とした。

| 例 | quick 実測 | 既定実測 |
| --- | ---: | ---: |
| `pl_curve.py` | 3.61 秒 | 19.37 秒 |
| `conditional_weight.py` | 1.80 秒 | 5.78 秒 |
| `convergence_check.py` | 1.01 秒 | 1.45 秒 |
| `p_dependent_decoder.py` | 0.78 秒 | 1.72 秒 |

quick の `pl_curve.py --demo-overlap` は `OverlapError from estimate_logical_error on disjoint endpoint supports p=0 and p=1` を表示して終了コード 0 だった。
既定設定の `pl_curve.csv` では d=3 の p=0.26 で BAR 区間 `[0.6008, 0.6520]` と direct MC 区間 `[0.6488, 0.7017]` が重なり、d=5 の p=0.22 で BAR 区間 `[0.5975, 0.6996]` と direct MC 区間 `[0.6726, 0.7244]` が重なった。
これは有限実行の相互照合であり、正しさや十分な混合の証明ではない。
既定設定の d=3、p=0.22 では BAR と direct MC の区間が交差しなかったため、警告を表示した。
quick の seed 2026 では d=5 の p=0.26 と p=0.22 で BAR 区間と direct MC 区間が交差せず、各行に `WARNING` を表示した。
この差の原因は特定しておらず、混合不足や有限標本変動などを調べる必要がある。
描画不能テストでは `sitecustomize.py` で `matplotlib.pyplot` の import に `ImportError` を起こし、両プロット例の CSV が残り PNG を省く出力を確認した。
PyMatching 自身が `matplotlib.cbook` を import するため、matplotlib パッケージ全体を隠した環境での実行は確認できず、描画層が無い場合だけを確認した。
研究リポジトリの拒否テストは `C:/dev/RIMC/mcmc4qec_example_forbidden` を出力先に指定し、書き込み前に拒否されたことを確認した。
環境変数 `RIMC_RESEARCH_ROOT` と `RESEARCH_ROOT` に指定したルートも、出力先を作る前に拒否した。

## 未実施とメインへの依頼

全 suite、installed wheel、CI、別 OS の実行は WP-G では未実施であり、メインの統合検証に委ねる。
toric ファクトリは現在 `ldpc` と `bposd` が必要なので、3 本の toric workflow の extras は `matching,codes` としてマニフェストと README を訂正してほしい。
両プロット例には追加予定の `plot` extras が必要であり、未導入でも CSV を保存する。
この WP では `src/` の変更、研究リポジトリの変更、論文図表の再現の主張はしていない。

## 計算予算調整の履歴

前の 4 chain 設定は quick 250 samples と 80 burn-in、既定 1000 samples と 300 burn-in で、pl_curve の実測は quick 5.47 秒、既定 23.60 秒だった。
他作業の並列実行中には quick subprocess がテスト側の 30 秒制限に達したが、同時負荷を除いた最終設定の単独実行は上記の 3.61 秒と 19.37 秒だった。
