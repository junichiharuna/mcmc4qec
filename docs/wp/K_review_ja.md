# WP-K 独立レビュー

## 判定

`b8fde01..f9b7b93` の実装差分を第三者として確認し、統合を止める不具合は見つからなかった。
`CSSCode.phase_flip_model()` は `hx`、`lx`、`hz` をそれぞれ検査、論理 observable、stabilizer に使い、既定の X 経路と識別子は維持されている。
Z 用 MWPM と BP-OSD は `hx/lx` を選び、`errors` と `data_noise` の無効値は `ValueError` になる。
非 self-dual な repetition、Hamming HGP、BB72 の行列選択と、asymmetric toric の双対 exact 比較を確認した。

## 独立の数値検査

Python 3.11 の絶対パスを使い、source を `PYTHONPATH=src`、`PYTHONDONTWRITEBYTECODE=1` で読み、レビュー用コードを標準入力から実行した。
phase phenomenological の1ラウンド5座標、全32状態、`p={"data":0.2,"measurement":0.3}` では、確率和は `1.0`、高速 Zanella の提案行和の最大偏差は `2.22e-16`、全状態間の高速経路と参照経路の最大差は `1.11e-16` だった。
状態に依存する独自 failure predicate の16失敗状態上で、MH 受理を含む詳細釣合いの最大残差は `0.0` だった。
境界 `p={"data":0,"measurement":1}` と `p={"data":1,"measurement":0}` では、それぞれ全状態の確率和が `1.0`、support は1状態で、phase data の高速確率行は二値の列だけに質量を持った。
別の3量子ビット phase 問題で `failure=bool(state[0])` とすると、`hz` stabilizer による `[1,0,0]→[0,1,0]` は failure を真から偽へ変えるが、`StabilizerFlip` の100ステップの条件付き chain は全保持状態が failure 内に留まった。
この検査は custom failure の stabilizer 不変性を仮定していないことを直接確認するが、chain の既約性や収束は証明しない。

MWPM の `p=0.13` を全状態でベクトル化して独立に計算すると、toric d=3 の `P_L(X)=0.33955890909626174` と `P_L(Z)=0.339876518254405` は異なり、重み4の失敗状態数も X が2403、Z が2411だった。
asymmetric toric 2×3 の `P_L` は X と Z の両方が `0.3829395240663862` で、条件付き平均重みも両方が `2.339574133207471` だった。
したがって依頼書第5項(b)の「toric d=3 は一致し asymmetric は不一致」という仮説を受入条件として強制しない完了メモの判断は妥当である。
Hamming HGP の `2^58` 状態と asymmetric 3×5 の `2^30` 状態の exact は軽い検証の範囲を超え、完了メモも未実施と記している。

## 実行した検証

`%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_phase_flip.py tests/test_decoders.py tests/test_noise_models.py tests/test_fastpath.py tests/test_initial_states.py tests/test_public_api.py -q --tb=short` は `96 passed in 20.78s` だった。
`RIMC_RESEARCH_ROOT=A:\dev\RIMC` と `PYTHONDONTWRITEBYTECODE=1` を設定した `%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_crossval_research.py -q --tb=short` は `20 passed in 1.72s` だった。
研究リポジトリの `git status --short` は空だった。
`PYTHONPATH=src` で `examples/phase_flip_asymmetric.py --quick --seed 20261001` を実行すると X `0.312`、Z `0.364`、`exact_available=false`、所要1.87秒だった。
同じ例を既定試行数と同じ seed で実行すると X `0.364`、Z `0.37566666666666665`、`exact_available=false`、所要3.80秒だった。
両実行の Wilson 区間は重なり、例と完了メモは有限標本による差を確定的な X/Z gap と主張していない。

## 残る確認範囲と改善案

新しい `tests/test_phase_flip.py` は全32状態の高速・参照提案分布を比べるが、失敗集合上の MH 詳細釣合いと endpoint support の検査を回帰テストとしては固定していない。
独立計算では通ったため停止級とはしないが、今後 phase 経路の確率行や proposal を変更する際には、上記の小問題を決定的テストにするのがよい。
3量子ビットの Z+H 平均重みの統計テストは1 seed と推定 ESS に依存するため、混合や正しさの保証として使わないという完了メモの留保は必要である。
全 suite、installed wheel、remote CI、3×5 と Hamming HGP の exact、長い chain の混合診断はこのレビューでは未実施である。
