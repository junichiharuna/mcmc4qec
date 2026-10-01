# WP-Q 独立レビュー

2026-10-01に `wp/q` の `638932f` を基点 `f2799a1` と比較した。
結論は承認で、重大度高・中の要修正指摘はない。
toric d=5とd=7の研究runner比2倍以内という目標は未達だが、WP-Qメモと公開文書はいずれも未達を明記している。
全suite、wheel、remote CIはこのレビューでは未実施であり、main統合後の受入判定に残る。

## 確認した範囲と方法

`AGENTS.md`、`docs/dev_request_2026-10-01_bar_speed.md` 全体、`docs/wp/Q_ja.md`、`docs/performance_ja.md`、基点からの6ファイルの差分、参照経路の `sampling.py`・`kernels.py`・`fastpath.py`、adapterの出力契約を確認した。
小仕様は `Q_ja.md` にあり、現状態のZ局所表、逆向き候補の1座標更新、棄却時の保持、受理時の移動、密度総和の維持、cacheのmiss検証とhitコピーを明記している。
小仕様と実装は同じ1コミットで履歴化されているため、小仕様の作成が実装より先だった時刻まではgit履歴から独立に確認できない。

`PYTHONDONTWRITEBYTECODE=1` とQの `src` を指定した独立の一時プローブで、bit-flip、Pauli、phenomenological、および p=0・p=1・一部の座標だけが決定的な境界を調べた。
支持内状態からの136近傍について、近傍順、逆向き分布の全再計算との差、順逆確率、および正の順逆確率を持つ辺の詳細釣合いを確認し、逆分布の最大絶対差は0だった。
支持外候補では逆向き表が `None` になり、支持外の全密度は受理前に `-inf` になる経路を確認した。
Zの候補サイトだけを更新する処理と非Z移動後の再構築をコード上で追い、棄却・lazy・非移動では現表が維持されることを確認した。
正規化は開始時に1回、Z提案時に逆表で最大1回、非Z移動受理時に新状態で最大1回という分岐であり、各attemptで最大1回だった。
候補の全密度総和の順序とphenomenologicalの区間分割は基点から変わっていない。

同seedの状態・受理・lazy・kernel列およびRNG呼出し順を直接捕捉する追加テストを確認した。
toric d=3ではprefix 1〜24で各stepの受理差分と状態、`rng.choice` の確率配列以外の引数のshape・dtype・bytesと返値を比較し、確率配列は絶対許容差 `1e-14` で比較する設計だった。
小categorical全状態・全近傍のForcedChoice試験は実際の提案、順逆比、MH確率、詳細釣合いを参照経路と比較していた。
独立プローブはこれらと異なり逆表の増分更新を全再計算と照合した。

`CachedDecoder` はmissで一般decoderの二値・一次元検証を行い、実型が組み込み `DecoderAdapter` または `PyMatchingAdapter` の場合だけ、そのadapter内の検証結果を使う。
hitはshape・dtype・bytesを含むkeyで検索して独立コピーを返し、専用stepは予測とobservableのshapeを毎回比較する。
ユーザー派生decoder、派生model/noise、独自failureは実型gateにより検証省略または専用stepの対象から外れる。
外部からcacheの公開 `lookup` や組み込みadapterインスタンスの `predict` メソッドを直接改変する操作は、この検証済み出力の前提外である。

## 実行結果

`A:/dev/mcmc4qec/.venv-dev5-source/Scripts/python.exe -m pytest tests/test_faststep.py tests/test_adapters.py tests/test_typing.py -q` は45 passed、5.96秒だった。
`output/review_q_probe.py` の独立列挙は136近傍を検査し、逆表の最大絶対差は0だった。
研究rootを指定せず `benchmarks/bench_step.py --quick --seed 17 --out output/review-quick` を実行し、3符号各100stepでexit 0、CSVの研究側欄は空だった。
`RIMC_RESEARCH_ROOT=A:/dev/RIMC` で `--out A:/dev/RIMC/review-should-not-exist` を指定するとexit 1で拒否され、対象ディレクトリは作られず、研究repoの `git status --short` は空だった。
`git diff --check f2799a1..638932f` はexit 0だった。

`output/bench-step-dev5-final/results.csv` は seed 731、各10000step、3符号×2回の6行を持ち、秒数からstep/sと時間比を再計算して全行一致した。
d=5はライブラリ8385.968/8553.383、研究22824.880/23202.201 step/s、時間比2.721794/2.712634だった。
d=7はライブラリ7322.041/7604.633、研究19148.801/19628.854 step/s、時間比2.615227/2.581170だった。
BB72はライブラリ4825.529/4931.680、研究7962.432/7741.654 step/s、時間比1.650064/1.569780だった。
`docs/performance_ja.md`、`docs/wp/Q_ja.md` の最終測定値と、mainの `README.md`・`README_ja.md` の表はこのCSVを記載精度へ丸めた値と一致した。
`output/bench-step-profile.txt` の1000step profileは、d=5/d=7で全体0.186/0.208秒、`FastStepper.attempt` 累積0.153/0.164秒、`propose` 0.062/0.060秒、`CachedDecoder.predict` 0.033/0.047秒、adapter `predict` 0.028/0.041秒だった。
BB72の全体0.323秒とadapter `predict` 累積0.153秒も性能記録と一致した。
累積profileの値は呼出し関係で重複し、正式な速度比較の表ではない。

## 残る確認

Qの最終型修正後の全suiteはWP担当メモでは未実施であり、このレビューも軽量検証に留めた。
wheel隔離環境とremote CI、研究runnerの10000step再計測は未実施である。
レビューは記録済みCSVの計算と公開表の照合を行ったもので、計測条件や速度の再現性を新たに保証しない。
toricの2倍目標は継続課題として残す。
