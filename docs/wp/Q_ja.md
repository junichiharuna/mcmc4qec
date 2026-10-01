# WP-Q 小仕様と作業記録

## 小仕様（実装前）

専用 step は既存の実型 gate と標準 failure に限り、公開 API と既定設定を変えない。
Z の近傍順、局所比の浮動小数演算、分布の最大値による安定化と総和、`rng.choice` の引数、逆向き proposal 比を維持する。
現状態の局所 log 比と正規化済み分布を保持し、単一座標変更の逆向き分布では変更座標の log 比だけを更新して全近傍の正規化を一度行う。
棄却では現状態の表を保持し、Z の受理では候補側の表を次の現状態の表として移し、他カーネルの移動受理では候補の表を再構築する。
候補状態の全密度は従来と同じ座標順と区間分割で全項を総和し、差分和に変えない。
decoder cache は miss 時に出力の二値性と一次元性を検証し、hit 時には独立コピーを返す。
専用 step は組み込み cache の検証済み予測を再検証せずに使うが、予測と observable の shape は毎回比較する。
受入試験は小 categorical 全状態・全近傍の提案分布と MH 確率、toric d=3 の同 seed の状態列・kernel/lazy/受理列・全 RNG 呼び出しと引数、cache の miss 検証・hit コピー・shape 安全性を確認する。

## 実装と検証

`faststep.py` は現状態の局所 log 比と正規化分布を保持し、Z の単一座標変更では該当箇所だけを置き換えて逆向き分布を作る。
開始時と非 Z 受理時にも表を更新するため、各 attempt の正規化は最大 1 回になる。
`decode_cache.py` は hit を 1 回の辞書検索で取得し、miss では一般 decoder 出力を検証し、実型が組み込み adapter の場合は adapter が行った検証を再実行しない。
専用 step は組み込み cache から返った検証済み予測を再検証せず、予測と observable の shape 比較を毎回行う。
候補の全密度は従来と同じ座標順と phenomenological の区間分割で総和し、RNG の呼び出し順と引数を維持する。
`bench_step.py` は `--quick`、`--seed`、`--out`、`--repeats` を受け付け、CSV を既定で一時ディレクトリに置き、研究 checkout 内の出力を拒否する。
研究 root を指定しない場合はライブラリ側だけを測り、指定時は研究 code を読み取り専用 import する。

`A:/dev/mcmc4qec/.venv-dev5-source/Scripts/python.exe -m pytest tests/test_faststep.py tests/test_adapters.py -q` は 42 passed、5.15 秒だった。
小 categorical 問題の全状態・全近傍で強制 `choice` による実際の Z 提案・順逆比・詳細釣合いと MH 確率、toric d=3 の各 step の状態・kernel/lazy/受理差分・RNG 引数と返値列、組み込み実型 gate、cache miss の不正出力拒否、cache hit のコピーと shape guard を検査した。
toric の `rng.choice` に渡す確率配列は計算経路の浮動小数差があるため、要素を絶対許容差 `1e-14` で比較し、RNG が消費した返値・呼び出し順・他の引数は一致を要求した。
追加の正規化回数検査は各カーネルの attempt ごとに最大 1 回を確認した。
`pymatching` を import 不可にした隔離実行では toric 試験が `1 skipped` となり、core 環境での optional 不在を扱えた。
研究 root 未指定の `bench_step.py --quick --seed 731 --out <作業tree内出力>` は 3 符号とも成功し、CSV には研究時間なしの行が出た。
研究 root 内を `--out` に指定した試験は変更前にエラーで終了し、研究 repo の `git status --short` は比較計測前後とも空だった。

正式比較は Windows 11 Pro build 22631、Python 3.11.9、AMD Ryzen 5 3600 6-Core Processor、NumPy 2.4.6、PyMatching 2.4.0、ldpc 2.4.1 で行った。
`$env:PYTHONDONTWRITEBYTECODE='1'; $env:RIMC_RESEARCH_ROOT=<研究repo>; A:/dev/mcmc4qec/.venv-dev5-source/Scripts/python.exe benchmarks/bench_step.py --steps 10000 --seed 731 --repeats 2 --out <一時出力>` は 14.44 秒で完了した。
型注釈修正後の最終コードで同じ seed と条件の 2 回を再実行し、14.81 秒で完了した。
最終の測定値は `docs/performance_ja.md` の表にあり、d5 の時間比は 2.722/2.713、d7 は 2.615/2.581、BB72 は 1.650/1.570 だった。
修正前の 2 回は d5 が 2.592/2.546、d7 が 2.468/2.469、BB72 が 1.604/1.553 で、短時間の計測ばらつきとして併記した。
toric の 2 倍目標は未達で、`--steps 1000 --profile` の原因探索では専用 attempt と提案生成、decoder cache/adapter が主な累積時間だった。
性能値は同一 seed の短時間反復であり、別環境の速度や混合精度を保証しない。

`PYTHONPATH=<Q作業tree>/src` を指定し、`--seed 7 --out <Q作業tree>/output/...` で専用経路に関係する例 6 本を既定と `--quick` の双方で逐次実行し、全 12 実行が exit 0 と `SUMMARY` 出力を返した。
下表は今回の PowerShell Stopwatch による process 全体の秒数であり、旧表との厳密な速度倍率とは扱わない。

| 例 | 既定秒 | quick秒 | dev4既定秒 | dev4 quick秒 |
| --- | ---: | ---: | ---: | ---: |
| `toric_pymatching.py` | 2.120 | 1.378 | 1.008 | 0.680 |
| `bb72_bposd.py` | 2.969 | 1.092 | 1.951 | 0.712 |
| `toric_depolarizing.py` | 2.268 | 1.091 | 1.521 | 0.708 |
| `phenomenological_toric.py` | 1.792 | 1.095 | 0.952 | 0.644 |
| `bar_ladder.py` | 0.626 | 0.452 | 0.503 | 0.348 |
| `workflows/conditional_weight.py` | 4.985 | 1.842 | 16.790 | 3.926 |

`examples/README.md` の対応する 6 行の時間欄はこの実測値へ差し替える案で、他の例は今回未測定なので旧値と注記を残す。

## メインへの共有文書案

`README.md` の Performance 節案を以下に示す。

> ## Performance
>
> The dedicated step path applies to exact built-in linear model/product-noise pairs with the standard logical failure predicate; custom subclasses or failure predicates use the general path.
> On Windows 11 Pro, Python 3.11.9, and an AMD Ryzen 5 3600, at p=0.01 with 10,000 Z/H steps, the library measured 8.4–8.6k steps/s for toric d=5, 7.3–7.6k for toric d=7, and 4.8–4.9k for BB72 (two runs each).
> The research RIMC runner measured 22.8–23.2k, 19.1–19.6k, and 7.7–8.0k steps/s under the matched setup; the library took 2.71–2.72x, 2.58–2.62x, and 1.57–1.65x as long, respectively.
> This comparison includes library result construction and diagnostics, so it is a reference workload comparison rather than a pure kernel timing.
> Run `python benchmarks/bench_step.py --steps 10000 --repeats 2` with `RIMC_RESEARCH_ROOT` set to a read-only research checkout; without that variable, it reports library timings only.
> Timings vary with hardware and load and do not establish mixing or estimate accuracy.

`README_ja.md` の性能節案を以下に示す。

> ## 性能
>
> 専用 step は組み込みの線形モデルと積ノイズの実型の組み合わせで標準 failure を使う場合に適用し、独自派生型や failure predicate では汎用経路を使う。
> Windows 11 Pro、Python 3.11.9、AMD Ryzen 5 3600 で p=0.01、Z/H を 10000 step 実行した 2 回の実測は、toric d=5 で 8.4～8.6 千 step/s、d=7 で 7.3～7.6 千 step/s、BB72 で 4.8～4.9 千 step/s だった。
> 同条件の研究 RIMC runner は順に 22.8～23.2 千、19.1～19.6 千、7.7～8.0 千 step/s で、ライブラリの所要時間は順に 2.71～2.72 倍、2.58～2.62 倍、1.57～1.65 倍だった。
> この比較にはライブラリ側の結果と診断の作成が含まれるため、カーネル単体の所要時間ではない。
> `RIMC_RESEARCH_ROOT` に読み取り専用の研究 checkout を設定し、`python benchmarks/bench_step.py --steps 10000 --repeats 2` で比較できる。
> 研究 checkout がない環境ではライブラリ側だけを測り、速度は環境負荷で変動し、混合や推定精度を保証しない。

## 残件と未実施

`A:/dev/mcmc4qec/.venv-dev5-source/Scripts/python.exe -m pytest tests -q` は 359 passed / 5 skipped / 2 failed、162.55 秒で、失敗はこの変更に伴う mypy 型推論だけだった。
`cast` と `next_site` 注釈を直し、`A:/dev/mcmc4qec/.venv-dev5-source/Scripts/python.exe -m pytest tests/test_typing.py tests/test_faststep.py tests/test_adapters.py -q` は 45 passed、6.55 秒だった。
全 suite の再実行、wheel と remote CI はメイン統合後の検証事項として未実施である。
メインには README 両言語への性能節、`examples/README.md` の測定した 6 行、統合後の全 suite・wheel・CI の反映を依頼する。
