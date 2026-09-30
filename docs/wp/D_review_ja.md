# WP-D 第1回独立レビュー

## 対象と判定

`401f5c6` の公開文書・CI・citation 差分と `docs/wp/D_ja.md` を `docs/dev_request_2026-09-30.md` §4 の WP-D 受入条件に照合した。
README の実行不能箇所は `efcabc4` で修正され、コードファクトリ用の `codes` extra は `a37af33` で D 枝にも入った。
全公開 docstring の契約統一は統合後の再監査が必要であり、この時点では WP-D 全体の完了とは判定しない。

## 独立に確認した結果

README 冒頭は機能を3行で説明し、toric d=5 と PyMatching の Python 例は空行を含めても20行以内だった。
README は BAR ladder、ノイズ・カーネル・decoder の対応表、診断と近似 BAR の制約をこの順に掲載し、`P_L` を実験全体の確率として説明している。
`docs/tutorial_en.md` は独自 CSS 行列、正規化した独自ノイズ、物理補正を返す decoder の3つのコードブロックを備え、担当者の wheel 環境で3件とも終了コード0と記録されている。
現行 `mcmc4qec.__all__` の35名を実行時に取得して `docs/api_en.md` と突き合わせ、記載漏れは0名だった。
`.venv-cff/Scripts/cffconvert.exe --validate` を再実行し、schema version 1.2.0 に対する成功と終了コード0を確認した。
`.venv-wheel/Scripts/python.exe -I -m pytest --override-ini pythonpath= tests -q` を再実行し、別 venv の installed wheel で162 passed、39.27秒を確認した。
同じ wheel venv で `examples/bar_ladder.py` と `examples/toric_pymatching.py` を再実行し、BAR の最終推定値0.02844と exact 0.02800、toric の direct MC `P_L=0.2325` と条件付き平均重み6.730を確認した。
CI 定義は core と optional の両 job を Python 3.11・3.12 の行列で走らせ、`pytest --override-ini pythonpath=` により source-path 指定を外している。
core job は optional 依存の不在を検査し、optional job は PyMatching、ldpc、bposd、Stim と両追加例を含む。
`CITATION.cff` は所有者が指定した `junichi haruna` を著者とし、未確定の DOI、公開日、license、公開 URL を含まない。

## 指摘と対応

重大度高：当初の `README.md:6` は `[matching]` だけを案内したが、`make_toric_code(5)` は `ldpc` と `bposd` を必要とし、クリーンな環境で toric 例が実行できなかった。
`efcabc4` は README を `[codes,matching]` に修正し、`a37af33` は `codes` extra に `ldpc` と `bposd` を定義した。
重大度高：当初の `README.md` の BAR ブロックは直前の toric `problem` を再利用し、`exact(problem, 0.4)` が50 qubit の状態数上限で `ValueError: exact state count exceeds max_states` になった。
`efcabc4` は3-bit の `Problem` を BAR ブロック内で定義し、`cluster_k=1` を明示した。
重大度中：当初の `docs/wp/D_ja.md:29-30` は docstring が存在しない12名だけをメインへの補完依頼とし、引数・返り値・例外・確率単位が不足する既存の短い docstring を含めていなかった。
担当者は `D_ja.md` に未達を明記し、`docs/wp/D_docstrings.patch` に adapters、adapter_composition、noise_categorical、models、estimation の補完案を保存した。
この patch は D 枝で `git apply --check docs/wp/D_docstrings.patch` に成功したが、全公開名に対する統合後の契約監査の代わりにはならない。

## 統合後に残る確認

A/B/C/E と WP-D を main に統合した後、新しい公開名も含めて `__all__` と API 文書を再照合し、全公開 docstring の引数・返り値・例外・確率単位を確認する。
統合後の wheel を新しい別 venv に入れて tests、README の2コードブロック、全 examples を再実行する。
Python 3.12 の手元実行と remote CI の成功は未確認であり、remote CI は許可された push 後に結果を確認する。

## 第2回最終レビュー：main 統合版

対象は A→B→E→D→C を統合した main `4330c3f` と、文書・公開契約の補完を含む `5d2e793` までの変更である。
当初の2件の README 実行不具合と docstring 補完漏れは統合版で解消し、WP-D の静的受入条件は満たしたと判定する。
README 冒頭3行は用途を説明し、15行の toric d=5 例は direct MC の絶対 `P_L` とともに direct MC・Z+H の同じ条件付き平均重みを示す。
README は続けて独立実行できる3-bit BAR ladder、対応表、診断と近似 BAR の制約を掲載し、確率をモデル化した実験全体の量として説明する。
`docs/tutorial_en.md` の独自符号・ノイズ・物理補正 decoder の各例は独立実行でき、異なる qubit rate の説明も3種類の scales と一致する。
公開名65件を実行時の `mcmc4qec.__all__` と `docs/api_en.md` で突き合わせ、漏れ0件を確認した。
指定 Python 3.11 で `python -m pytest tests/test_public_api.py -q` を独立実行し、1 passed を確認した。
公開 callable には docstring があり、引数・返り値・主要例外・確率または物理量の単位を読み合わせ、指摘した設定・sampling・回路 helper の契約記述は `dcffdf8`、`29900f3`、`5d2e793` で補完された。
`CITATION.cff` はユーザー指定の `junichi haruna` と version `0.1.0.dev2` を記載し、中央実行の `cffconvert --validate` は schema 1.2.0 に成功した。
`pyproject.toml` の version、Python 3.11/3.12 classifiers、keywords、既存 private repository に対応する URLs、`codes` extra を確認した。
CI 定義は Python 3.11/3.12 と core/optional の4 job で installed wheel tests を実施し、`--override-ini pythonpath=` でソース指定を外す。
core job は optional 4依存の不在を検査し、optional job は PyMatching、ldpc、bposd、Stim と全追加例を実行する。

中央実行の最終 wheel `mcmc4qec-0.1.0.dev2-py3-none-any.whl` の SHA256 は `e4d443a860a182786d3377cc068f713428771630fde9615cf7efbdb493581664` である。
最終 installed wheel tests は core venv が208 passed・43 skipped・41.23秒、optional venv が268 passed・4 skipped・81.52秒で、ログは `output/wheel_core_final.log` と `output/wheel_optional_final.log` にある。
最終 `docs/wp/verify_wheel.py` 実行ログは両 venv で site-packages の import、version、23 Python ファイルの source との byte 一致、依存の有無を確認した。
core は core 3例、README の BAR 1例、tutorial の独自符号・ノイズ・decoder 3例をそれぞれ exit 0 で実行した。
optional は全6例、README 2例、tutorial 4例をそれぞれ exit 0 で実行し、toric の direct MC 条件付き平均7.068817と Z+H 6.73、回路例の500試行 `P_L=0.09` を表示した。
例の実行ログは `output/examples_core_final.log` と `output/examples_optional_final.log` にあり、これは例の実行契約の検証であって混合や研究論文の数値再現の証明ではない。
Python 3.12 の手元実行と remote CI の実結果は未確認であり、remote CI は push 後に対象 commit の4 job を確認する。
