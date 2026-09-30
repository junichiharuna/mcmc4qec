# WP-A 完了メモ（2026-09-30）

## 実装

`codes.py` に asymmetric toric、HGP Hamming、任意の bivariate bicycle、BB72/108/144、Steane、連接 Steane のファクトリと連接ヘルパーを追加した。
研究行列の行順と論理基底を変えずに移植し、非単位だが可逆な論理交差行列を持つファクトリでは `logical_basis="independent"` を明示した。
`decoders.py` に MWPM、BP-OSD、depolarising 用 X/Z sector の四つの factory を追加した。
各 decoder は研究の物理補正を `lz` または `lx` で論理予測へ変換し、出力の意味を長さから推測しない。
PyMatching が扱えない列次数3以上の check matrix は明示的に拒否する。
ldpc 2.4.1 は Windows で nullity より大きい OSD order により native heap crash を起こしたため、整数型の正規化と上限検証を C 拡張の呼出前に行う。
符号、decoder、exact、direct MC、Z+H、研究テスト対応の詳細は `docs/crossval_research_ja.md` に記録した。

## 実行した検証

以下の Python 実行は `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe` を使用し、研究側を import する場合は `PYTHONDONTWRITEBYTECODE=1` を設定した。
`python -m pytest tests/test_codes.py tests/test_crossval_research.py tests/test_decoders.py -q` は optional 環境で 66 passed、39.65 秒だった。
同じコマンドを `C:/dev/mcmc4qec/.venv-dev2-core/Scripts/python.exe` で実行すると 40 passed、26 skipped、0.57 秒だった。
BP-OSD guard の最終変更前に実行した `python -m pytest tests -q` は 201 passed、271.25 秒であり、この結果を最終変更後の全 suite 合格とは扱わない。
12 構成の研究 `hx/hz/lx/lz` の shape と raw bytes をまとめた SHA-256 はすべて一致した。
toric d=3 の実現可能 syndrome 256 個について、研究の MWPM、BP-OSD、depolarising MWPM、depolarising BP-OSD と直接照合した論理予測の不一致は各0件だった。
toric d=3 の研究 syndrome table の256行でも MWPM 論理予測の不一致は0件だった。
`mcmc4qec.exact` の `p=0.01` は `P_L=0.0020442815656133238`、`E[w|F]=2.261042002778366`、44.19秒で、研究 exact の `0.0020442815655904952` と `2.2610420028036122` に数値一致した。
固定 seed 20260930 の100000 trial direct MC は BB72 で166 failures、`P_L=0.00166`、95% Wilson区間 `[0.0014261085,0.0019321771]`、`E[w|F]=3.74699`、23.52秒だった。
同じ条件の toric d=5 は14 failures、`P_L=0.00014`、95% Wilson区間 `[0.0000834003,0.0002350020]`、`E[w|F]=4.0`、21.95秒だった。
研究 CSV の両 `P_L` は対応するライブラリの Wilson 区間に含まれた。
3000保存標本、500 burn-in の Z+H は toric d=5 で `E[w|F]=3.77733`、ESS 52.60、参考95%区間 `[3.55680,3.99787]`、15.21秒だった。
同じ Z+H は BB72 で `E[w|F]=3.57433`、ESS 65.56、参考95%区間 `[3.38725,3.76142]`、18.74秒だった。
研究 CSV の条件付き平均は両方の参考区間に含まれた。
研究 `splitting_pl.py` と同じ合成 weight trace の BAR log ratio は研究 `-1.2130084485394683`、ライブラリ `-1.213008448539711` だった。
指定された八つの研究テストファイルの102 test関数を意味論ごとに対応付け、WP-A 新規52 parameterized case、既存の等価試験、新 API 未対応を数値照合文書の表に記録した。
研究リポジトリの `git status --porcelain=v1` は出力なしだった。

## 未実施と制約

大きい符号の最小距離の下界は独立に証明しておらず、BB108 の距離10は研究ラベルとして扱った。
HGP Hamming と BB のテストでは実際の論理代表が与える上界のみ確認した。
toric、surface、asymmetric toric、HGP Hamming は研究の行列と論理行順を一致させるため optional `ldpc` と `bposd` に依存する。
core-only NumPy でこれらの論理行順まで再現する実装は未実施である。
研究 runner の旧 Z+PT 既定、PT/hot replica、Barker balancing、plain BP、研究 postprocess の自動 burn-in と thin は新 API に直接移植していない。
toric d=5 と BB72 の短い Z+H はそれぞれ1 chainのみであり、参考区間の被覆確率、混合、正しさを保証しない。
toric d=5 のノイズからの初期化は上限10000回で失敗したため、事前に定めた `lx[0]` を指定して再実行した。
最終変更後の全 suite、remote CI、installed wheel、公開 API の `__init__.py` 追加はメイン統合後の検証事項である。

## レビューとメインへの依頼

研究 HGP/BB の交差行列が単位でない契約衝突はメインと協議し、メイン commit `e8a488b` の明示 `logical_basis="independent"` を担当 branch に cherry-pick した。
この契約は既定の paired 検証を維持し、研究行列を無変換で受け取る。
メインの独立レビューはこの共通契約の実装に問題なしとし、予測座標同時変換の説明修正と非ゼロ補正の追加試験を main commit `f5323c1` に入れた。
WP-A 自体の独立レビューは未実施である。
メインには `__init__.py` へ `make_asymmetric_toric_code`、`make_hgp_hamming`、`make_bb_code`、`make_bb_code_72`、`make_bb_code_108`、`make_bb_code_144`、`make_steane_code`、`concatenate_css`、`make_concatenated_steane_code` と四つの decoder factory の追加を依頼する。
メイン commit `916612b` は `pyproject.toml` の `[codes]` optional extra に `ldpc>=2.4,<3` と `bposd>=2.1,<3` を追加済みである。
toric を使う README の install command には codes 依存を含める必要がある。
