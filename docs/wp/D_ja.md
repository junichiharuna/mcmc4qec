# WP-D 公開準備の実施記録

## 実装

README を冒頭の機能説明、20 行以内の toric d=5 + PyMatching 例、BAR ladder、対応表、制約を中心に書き直した。
`docs/api_en.md` に公開 API と確率の単位を一覧化した。
`docs/tutorial_en.md` に独自 CSS 行列、正規化ノイズ、物理補正を返す decoder の実行可能な最小例を記載した。
`examples/toric_pymatching.py` と `examples/bar_ladder.py` を追加した。
`CITATION.cff` に所有者指定の著者名 `junichi haruna` を加え、未確定の DOI、公開日、license、公開 URL は記載しなかった。
CI の core/optional wheel test を Python 3.11 と 3.12 の行列にし、bar と toric の例を実行対象に加え、toric factory に必要な `bposd` を optional job に加えた。
`CONTRIBUTING.md` の検証手順と公開前の未決事項を更新した。

## 実行した検証

`%USERPROFILE%/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests -q` は 162 passed、33.70 秒だった。
`.venv-cff/Scripts/python.exe -m build --wheel` は `mcmc4qec-0.1.0.dev1-py3-none-any.whl` を作成した。
別 venv に wheel、pytest、pymatching、ldpc、bposd、stim を install し、`.venv-wheel/Scripts/python.exe -I -m pytest --override-ini pythonpath= tests -q` は 162 passed、42.84 秒だった。
同じ wheel 環境の `examples/toric_pymatching.py` は toric d=5、p=0.1、direct MC 2000 trials で `P_L=0.2325`、95% Wilson 区間 `(0.2145101595, 0.2515154608)`、条件付き MCMC の平均重み `6.730` と出力した。
同じ wheel 環境の `examples/bar_ladder.py` は p=0.4、0.25、0.1 の推定値 `0.35200`、`0.15501`、`0.02844` を出力し、最後の exact は `0.02800` だった。
`docs/tutorial_en.md` の Python コードブロック 3 件を wheel 環境で個別実行し、終了コードはすべて 0 だった。
AST で現行 `mcmc4qec.__all__` の 35 名を読み、`docs/api_en.md` に 35 名すべてが記載されていることを確認した。
`.venv-cff/Scripts/cffconvert.exe --validate` は `Citation metadata are valid according to schema version 1.2.0.` を出して終了コード 0 だった。

## メインへの依頼と未実施

`pyproject.toml` は担当外なので、version を `0.1.0.dev2` に上げ、`[project.urls]` に所有者確認後の公開先と issue/documentation URL、keywords に quantum error correction・rare-event sampling・MCMC、classifiers に対象 Python 3.11/3.12 と scientific research を追加する案を示す。
PEP 561 に従って `src/mcmc4qec/py.typed` を wheel に含めるなら、公開 Protocol を含む型注釈の整備と型検査を先に確認する必要がある。
`CHANGELOG.md` には公開文書、例、CI、citation validate の実績を追記してほしい。
公開 docstring の最初の AST 監査では `Model`、`Noise`、`Decoder`、`Problem`、`diagnose`、`IndependentBitFlip`、`Result`、`KernelConfig`、`SamplingConfig`、`exact`、`from_stim_dem`、`matching_from_dem` に docstring 欠落を見つけた。
レビューにより、既存の 1 行 docstring にも引数、返り値、例外、確率の単位が不足すると判明し、現段階では依頼書の全公開 symbol docstring 条件は未達である。
担当外の残りの補完案は `docs/wp/D_docstrings.patch` に保存し、`git apply --check docs/wp/D_docstrings.patch` で適用可能性を確認した。
この patch は adapters、adapter_composition、noise_categorical、models、estimation の公開 symbol を対象とし、main が担当した core、noise、results、stim_dem および B の sampling、E の diagnose とは分けている。
全変更統合後の新公開名を含む最終監査と patch 適用はメインへの依頼として残る。
remote CI の実行、Python 3.12 の手元検証、publish は未実施である。
この記録の wheel は A/B/C/E 統合前の作業枝を対象にしており、統合後はメインで再ビルドと再検証が必要である。
レビュー指摘に基づき README の toric install 手順と BAR の独立実行例を修正し、別 venv の wheel で README の Python ブロック 2 件を個別実行してともに終了コード 0 を確認した。
メインの `codes` extra 追加 commit を作業枝に取り込み、独立 `.venv-readme` で `pip install -e '.[codes,matching]'` が bposd、ldpc、pymatching を導入することを確認した。
同環境で README の Python ブロック 2 件を個別実行し、両方とも終了コード 0 だった。

## 再開後の公開 API 追随

A の実符号 factory 11 名と decoder constructor 4 名、C の物理回路 8 名、E の診断・初期化 7 名を各作業枝の実装とメモに照らして README、API 文書、tutorial に追記した。
B の `SamplingConfig.cache_cap/cache_policy` と `KernelConfig.zanella_fastpath`、C の明示 `circuit_single` 選択も記載した。
回路では Z/H と stabilizer を使えないこと、DEMs は baseline decoder 構築用で物理配置の尤度と異なること、収束四条件の完全判定に独立 direct MC の条件付き分散が要ることを明記した。
CI の optional job に `examples/circuit_baseline.py` を追加した。
A/C/E の追加公開名の docstring に引数、返り値、例外、確率の単位が不足する箇所を各担当に連絡し、担当側の補完を待っている。
追加した toric d=3 + `mwpm_decoder` の tutorial コードブロックは A 作業枝の `src` を import path に指定して実行し、終了コード 0、MC 推定値 `0.25` を確認した。
A/C/E の公開予定 30 名がすべて `docs/api_en.md` に個別の inline-code 名で現れることを照合し、漏れは 0 件だった。
この追加 API の installed wheel 実行、`__all__` の最終突合、統合後 Python 3.11/3.12 CI はまだ未実施である。
