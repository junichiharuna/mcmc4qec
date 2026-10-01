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
