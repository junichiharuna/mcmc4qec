# WP-K 静的 phase flip

## 小さい仕様

Z 誤りの状態は qubit ごとの binary support とし、`CSSCode.phase_flip_model()` は `hx` を syndrome、`lx` を observable、`hz` を stabilizer 行として使う。
`IndependentBitFlip(code.n)` は X と Z の binary product 分布を共通に表す。
`mwpm_decoder(code, errors="Z")` と `bposd_decoder(code, p, errors="Z")` は `hx` から物理 Z correction を求め、`lx` で論理予測を返す。
`errors="X"` は従来の `hz` と `lz`、識別子、既定値を維持する。
phenomenological phase flip は各 round の Z data fault と X check measurement fault を持ち、data fault と measurement fault はいずれも二値とする。
高速 Zanella の局所確率行は phase flip data fault に Bernoulli の 2 列を使い、参照密度からの提案分布と一致する。
条件付き chain は絶対論理誤り率を推定しない。

## 受入検証

実装と検証の完了後にコマンド、結果、実測時間、科学的制約、統合依頼を追記する。
