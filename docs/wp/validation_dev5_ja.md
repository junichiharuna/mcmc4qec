# dev5 検証記録

## Phase 0

2026-10-01に `git fetch origin` 後の main と origin/main がともに `9e1b28c1211bb4900e41f178ef8f0ddaaad78243` であることを確認した。
開始時の74 tracked fileとLICENSEの変更はユーザー承認を得て前提変更として取り込み、コミット `22a8e9c` に保存した。
既存の `docs/` 変更はユーザーホーム絶対パスの `%USERPROFILE%` への置換だけであることを、HEAD本文からの置換結果との全ファイル一致で確認した。
dev5依頼書は開始時点で未追跡だったため、作業計画とともに別コミットで保存する。
履歴文書の既存パス表記を前提変更として保存した後は、handoff既存本文に新たな変更を加えない。
研究repoのHEADは `69efcfcc86af3bf24ca977a098dab0f348601aff`、`git status --porcelain` は空だった。

全コマンドは指定Python3.11の絶対パス、またはそれで作成したvenvのPython絶対パスを使用した。
研究照合では `PYTHONDONTWRITEBYTECODE=1` と `RIMC_RESEARCH_ROOT` を設定した。
指定Pythonで `python -m pytest tests -q --junitxml=output/dev5/phase0_source.xml` は356 passed / 3 skipped、136.41秒だった。
skipはnotebookモジュール（nbformat/nbclient不在）とmypy依存テスト2件であり、この結果だけではnotebook・型検査成功を意味しない。
別の `python -m pytest tests/test_crossval_research.py -q --junitxml=output/dev5/phase0_crossval.xml` は20 passed、1.97秒だった。
研究照合のBARは保存済み合成traceの基準値との比較であり、研究BAR関数のlive呼び出しと混同しない。
live研究照合5件は全syndromeのdecoder比較である。

指定Pythonから `.venv-dev5-source` を `--system-site-packages` で作成し、nbclient0.11.0、nbformat5.11.1、build1.6.1、mypy2.3.1を追加した。
この環境はsource検証用であり、最終wheel検証用のcore/optional新規環境とは別とする。
全依存を含む基準実行のJUnitは `output/dev5/phase0_full.xml` に保存する。
同venvで `python -m pytest tests -q --junitxml=output/dev5/phase0_full.xml` は362 passed、151.22秒、skipなしで成功した。
Windowsのzmq/tornadoのselector threadへのfallback警告が1件あり、notebook4本と型検査も成功した。
dev4の358 passed / 5 skippedとの差は研究live照合5件を有効にしたことと、前提変更で固定絶対パスの旧保護テスト1件を除いたことに対応する。
同じ保護要件は環境変数で設定したrootを拒否するテストで確認した。

## 論文を読んで確認した区別

論文 `paper/main.tex` 269–281行のBARはFermi関数 `h(t)=1/(1+t)` を用い、同数標本ではC=Rの自己無撞着解を取る。
ライブラリの `bennett_log_ratio` は `sigmoid(delta-r+log(n_b/n_a))` と逆向きscoreの総和を等置し、同数標本ではこの式と一致する。
研究 `src/splitting_pl.py` のBAR関数はpymbarのwork差と `-Delta_f` を使い、別のone-sided reweighting関数とは区別する。
論文601–621行のproduction kernelはZ+H、K=50、5 IAT burn-in、chain平均間の標準誤差であり、研究runnerのAPI既定Z+PTとは異なる。
論文663–675行の収束規則は四条件であり、late driftとmultistartだけを合格させても四条件合格とは呼ばない。
論文987–1031行はmean-weight性能からBARの費用を見積もり、full estimatorのend-to-end費用は実測していないと述べる。
cross-chainのBAR区間は論文の平均標準誤差の考え方を応用するもので、論文がその被覆を検証したとは主張しない。

## 計測環境

CPUは `AMD Ryzen 5 3600 6-Core Processor`、OSはWindows、指定Pythonは3.11とする。
性能測定時に依存版と実際の設定・seedを改めて出力し、他の計測と重ねない。

## dev5 wheel用の環境準備

2026-10-01に指定Python3.11から `--system-site-packages` を付けずに `.venv-dev5-core` と `.venv-dev5-optional` を新規作成した。
coreにはpytest9.1.1とmypy2.3.1を導入し、mcmc4qecとoptional依存の不在を確認した。
optionalにはpyprojectのdependenciesとtest/matching/bposd/codes/stim/plot/notebooks extras、およびmypyを導入した。
optionalの主要版はNumPy2.4.6、PyMatching2.4.0、ldpc2.4.1、bposd2.1、Stim1.16.0、matplotlib3.11.2、nbclient0.11.0、nbformat5.11.1、ipykernel7.4.0である。
両環境の `pip check` は `No broken requirements found.` で成功し、optional環境もmcmc4qecはまだ導入されていない。
この準備はwheel検証の成功を意味せず、最終dev5 wheelを導入した後に全pytestとverify_wheelを実施する。

## WP-P 手順照合で検出した修正点

読み取り専用の補助担当が、論文の記述だけでなく研究 `cluster_scripts/lowp_audit.py` と `compare/convergence_flags.py` の呼び出しを照合した。
研究の実行は各chainに対する1Dの5 IAT cutであり、`src/postprocess.py` が2D入力時に採る共通median cutとは区別する（`lowp_audit.py` 267–277行）。
反復はcut=0から最大5回で、現在のtailから得たIATの5倍を切り上げ、半traceの上限に制限し、cut不変で収束とする。
5回で収束しない場合は半traceへfallbackする。
四条件のscalingとlate driftには未burnの全traceのN/4、N/2、N checkpointを用い、multistartとdispersionには5 IAT後の値を用いる（`lowp_audit.py` 234–251、619–625行、`convergence_flags.py` 715–754行）。
dispersionのWはburn後の各chain分散の算術平均、IATと残存Nはchain間中央値を使う（`lowp_audit.py` 294–324行、`convergence_flags.py` 660–684行）。
toricの論理basisのshort/longは同じ状態になるため論文のmultistart条件は実質的な比較を提供せず、異なる論理組合せからの補助比較と区別する。
Pの初回pilotは共通cutとburn後のS/Dを用いて199.98秒で完了したが、この旧手順の値は最終の科学表に採用しない。
P担当へ各chain別cutと四条件の修正を依頼し、修正版の最終測定をQ統合後mainで行う。

## remote 接続の確認

2026-10-01に `gh repo view --json nameWithOwner,isPrivate,defaultBranchRef` で対象は `junichiharuna/mcmc4qec`、private、既定branchはmainであることを確認した。
この時点の最新Actions run `36850587053` は開始時の `9e1b28c` に対する成功であり、dev5のCI成功とは扱わない。

## Q統合後のsource検証

2026-10-01、main `8d00cf8` で `PYTHONDONTWRITEBYTECODE=1` と `RIMC_RESEARCH_ROOT` を指定し、`.venv-dev5-source/Scripts/python.exe -m pytest tests -q --junitxml=output/dev5/q_merged.xml` を実行した。
366 passed、153.24秒で、失敗とskipはなかった。
基準362 passed /151.22秒から4件増え、時間増分は2.02秒だった。
警告1件は既知のWindows zmq event-loop対応である。
Qの独立レビューは `Q_review_ja.md` にあり、136近傍の逆向き分布全再計算との一致、詳細釣合い、関連45件、CSV6行の数値を確認済みである。
JUnitのfile別合計最大は `tests.test_circuit_kernels` の25.583秒で、各file60秒以内だった。

## P統合とdev5 source凍結

Pの実装レビューは `0804e4a` で確定し、最終科学CSVの監査は後続として残した。
mainへ `82c003a` でmergeし、`05c7005` でpyprojectとResultの版を0.1.0.dev5へ揃えた。
研究envと `PYTHONDONTWRITEBYTECODE=1` を設定した `.venv-dev5-source/Scripts/python.exe -m pytest tests -q --junitxml=output/dev5/p_merged.xml` は372 passed /156.56秒、skipなしだった。
基準から10件増え、時間増分は5.34秒で、file別最大はcircuit kernelsの26.652秒だった。
警告1件は既知のWindows zmq対応であり、全suite300秒・増分60秒・各file60秒の制限を満たした。
このsourceを最終科学計測の実装として固定し、版変更により失効する旧truth cacheは使い回さず、mainで新規列挙する。
`python -m build --wheel` は成功し、`dist/mcmc4qec-0.1.0.dev5-py3-none-any.whl` を新規core/optional venvの両方へinstallした。
installed wheelの全pytestとverify_wheelは、この時点ではまだ未実施である。
