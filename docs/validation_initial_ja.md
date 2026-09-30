# 初期ライブラリ 0.1.0.dev1 検証結果

2026-09-30、Windows / Python 3.11.9、NumPy 2.4.6、pytest 9.1.1。
参照した仕様は本文v0.2。公開・回路論文再現・大規模混合性能の確認ではない。

## 実際に実行した確認

| 環境 | 結果 | 条件 |
| --- | --- | --- |
| source tree | **142 passed** | 全tests、70.69秒 |
| installed wheel、optional decoderあり | **142 passed** | `-I`、pythonpath無効、72.70秒 |
| installed wheel、coreのみ | **130 passed, 7 skipped** | `-I`、pythonpath無効、70.67秒 |

optional環境はPyMatching 2.4.0、ldpc 2.4.1、Stim 1.16.0。
core環境はPyMatching/ldpc/Stim/SciPyが**未インストール**であることをassertした。
optionalなしでモジュール全体をskipするケースがあるため、collected件数は環境間で異なる。
どちらも `.venv-*/Lib/site-packages/rimc` からimportしたことを確認。
sourceの13個のPythonファイルとwheel内部の内容がbyte単位で一致。

wheel: `dist/rimc-0.1.0.dev1-py3-none-any.whl`

SHA256: `abdbf8a9d80e40d76ffde838342850799fb045f4fb58eda68408fa58ffe1e7b0`

結果metadataと同じ方式によるpackage source SHA256:
`82831fc8c33645466c8bd2ac8364f24ba8976c4e60e2fcfce254a076483d07ea`。

追加のテストを先に失敗させてから実装・修正した項目は、初期API不在、Stim接続不在、
exactのunderflowである。独立レビューでmodel-bound noiseの誤接続とJSON alphabetの
uint8 wrapも発見し、修正後の回帰試験で確認した。

## 主な受入内容

- binary/Pauli/mixed alphabetで提案確率と実測頻度、Hastings比、詳細釣合いを比較。
- OBF/Z/H/静的stabilizer、非同一確率・相関ノイズ、独自failure、棄却保持。
- Pauliカテゴリの正規化とY相関、両論理sector、p=0/1とsupport。
- phenomenologicalのhistory/difference、clean開始、perfect/noisy終端、測定誤り0の極限。
- 三種のノイズでexact/directMC/MCMCを同じfailureで比較。
- 一般log密度のBARを列挙normalizer比と照合。共有rungのblock再標本化、JSON、seed。
- p依存failure近似の反例: 真値0.5に対して近似BARは1.5。近似を厳密経路と区別。
- 二bit同時故障、p=1e-200のexact: 浮動小数点の率は0でもlogPと条件付き平均2を保持。
- model-bound noiseの意味が異なるモデルとの誤接続を拒否。
- 実PyMatching/BP-OSDの補正写像、履歴全体の接続、相関設定一致、hyperedge拒否。
- Stim DEMの^を同一機構として保持し、全潜在状態replayとランダム標本のH/LをStimと照合。
- 初期化上限、不正入力、seed系列分離、カテゴリJSON、dev0 binary JSON互換。

## installed wheel の例

`examples/bit_flip.py`、`examples/three_noise.py` はcoreのみのwheel環境で実行成功。
`examples/stim_dem.py` はoptional環境で実行成功。

| 三種ノイズ例の対象 | Exact P_L | Direct MC | Fixed-failure BAR |
| --- | ---: | ---: | ---: |
| static depolarizing、p=.15 | .230000 | .242000 | .218718 |
| phenomenological bit-flip、data=.12/measurement=.04 | .211200 | .209500 | .205472 |
| phenomenological depolarizing、同確率 | .324664 | .328000 | .320129 |

各例は2量子ビットの小さい符号、固定された単純なreference decoder。
phenomenologicalは2round・clean開始・perfect終端・historyで実験全体の率。
MC=2000試行、MCMC=500保存標本、burn-in=50、BAR bootstrap=20回。
これは実行smokeであり、精密な精度評価ではない。
**静的depolarizingの短いBAR実行では近似区間 [.209707,.228116] が厳密値 .23 を外した。**
区間の精度・混合・block長の妥当性を確立したとは扱わない。数値を見た後にseedを選び直していない。

Stim例では3機構の全8状態でreplayとH/Lが一致。exact=.0078、MC=.008。
DEMの分布に対する確認であり、物理回路の排他faultモデルや論文実験の再現ではない。

## 実施していない事項

remote CIの実行、Python 3.12のローカル実行、元研究tests全体の移植、旧runner互換wrapper、
大規模速度比較、重いsweep、クラスタ投入、物理回路baseline、論文図表再現。
公開repo作成、commit/push、package publish、license選択も行っていない。

研究cloneと `A:/dev/RIMC` のgit statusはともにclean。実装は別のtaskディレクトリに保存。
設計と未対応範囲は [initial_library_ja.md](initial_library_ja.md) を参照。
