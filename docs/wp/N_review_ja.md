# WP-N 独立レビュー

対象は `wp/n` の `b8fde01..db1f88c` である。
`AGENTS.md`、dev4 依頼書の共通不変条件と WP-N、`docs/wp/N_ja.md`、`docs/performance_ja.md`、実装差分、対応テスト、研究 runner の該当箇所を読んだ。

## 判定

統合を止める指摘は見つからなかった。
組み込み型の正確な組み合わせと標準 failure だけを専用経路に通す判定を確認し、独自 failure、派生 noise/model、無効化フラグは参照経路に戻ることを確認した。
公開 `KernelConfig` の既定値と `Result` の保存列、受理統計、provenance の定義は差分で変更されていない。
toric d=5/7 で研究 runner の 2 倍以内という速度目標は未達であり、これは完了記録と性能文書に明記されている。

## 独立した数値確認

`%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_faststep.py -q` は 15 passed、2.97 秒だった。
一時的な独立検査スクリプトを worktree に置いて実行し、終了後に削除した。
bit flip、depolarizing、phenomenological の 18 構成で、支持内の局所 Z 分布を参照の全密度評価と比較し、p=0/1 を含む 153 件の分布・複数 chain 軌道・受理統計・decode cache 末尾サイズの検査が通った。
phenomenological は 1/2 round、history/difference、noisy/perfect final boundary、bit flip/depolarizing data noise を組み合わせた。
3 bit の不均一積ノイズについて 8 状態を列挙し、OBF、Z、H、stabilizer の各提案分布の総和が 1 になることを確認した。
その失敗集合上の順方向・逆方向の流量は、各カーネルの MH 受理率を掛けた 16 組で `1e-14` 未満の差で一致した。
実際の `FastStepper.attempt` で OBF と Z の受理率をまたぐ乱数を与え、候補状態、受理、移動統計が両側で期待どおり変わることを確認した。
支持が一点になる p=0/1 では、Z の self-loop と lazy を含む 2 chain の保存状態と受理統計が参照経路と一致した。
既存の `test_faststep.py` は全 faulty 状態の実 step、同 seed の乱数呼び出し列、Z/H/OBF の混合、custom failure fallback、2 round の depolarizing history を検査しており、上記の追加検査と整合した。

`%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe benchmarks/bench_step.py --steps 10000` の再計測は d5 がライブラリ 1.293109 秒・研究 0.415972 秒・3.11 倍、d7 が 1.422528 秒・0.480258 秒・2.96 倍、BB72 が 2.093885 秒・1.168210 秒・1.79 倍だった。
比較コードは開始状態 `lx[0]`、p=0.01、Z/H=0.7/0.3、cluster_k=2、1 chain、lazy=0、同じ符号行列と decoder 設定、cache 上限なし、decoder 構築を除く計時で揃えている。
研究 runner とライブラリは同じ整数 seed でも RNG の初期化経路と実装が異なるので軌道そのものを対にした速度比較ではなく、短時間計測の比は負荷と軌道で変わる。
文書の 10000 step 表は別の実測値であり、今回の再計測も toric の目標未達と BB72 の目標達成という判断に一致する。

## コード上の確認と残る検証

`current_q` は Z の棄却時に保持され、Z の受理時だけ候補の `next_q` に移り、他カーネルの受理時は無効化され、chain 開始時にも無効化される。
候補状態はコピーで作られ、syndrome と observable は候補の線形効果から別配列で計算されて受理時にだけ保持されるため、棄却で現状態の cache を汚さない。
`CachedDecoder.predict` は入力と格納・返却値をコピーし、境界での cache 処理は専用経路と参照経路の共通ループに残る。
同 seed の完全な乱数呼び出し列は既存テストの代表構成で確認できるが、独立スクリプトの全 18 構成では保存軌道と統計の比較までとした。
全 suite、installed wheel、remote CI はこのレビューでは再実行していない。
研究リポジトリは読み取り専用で参照し、レビュー終了時の `git status --short` は空だった。
