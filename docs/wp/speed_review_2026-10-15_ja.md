# 2026-10-15 高速化の独立レビュー

レビュー対象はHEAD `35ed7f3` に対する `faststep.py`、`sampling.py`、`adapters.py`、`tests/test_faststep.py` の未コミット差分である。
実装ファイルは変更せず、`AGENTS.md` と `next_work_2026-10-15_ja.md` の受入条件に沿って確認した。
変更由来の修正必須事項は発見しなかった。

## 静的確認

混合CDFは従来と同じ確率配列を同じ `np.cumsum` で一度だけ構築し、`searchsorted` の `side="right"` と末尾clampを維持している。
二値単一座標のXORはexact type gate内の `BinaryLinearModel` に限定され、単一座標提案が必ずビットを反転することとゼロラベルの線形効果がゼロであることに依存する。
二値複数座標のXORも実際に変化した座標だけを走査し、カテゴリモデルには旧来のbefore/after効果を使う。
任意のmodel/noise派生型とcustom failureは既存のtype gateで専用stepから除外される。
候補密度は差分加算ではなく全座標総和を維持し、履歴モデルの二つの総和も保持する。
ゼロ確率の対数は `-inf` であり、非有限候補はdecoder評価前に棄却される。
失敗集合外候補では逆分布を構築しないが、現状態の分布と対数重みは変更しない。
失敗集合内候補は受理判定前に逆分布を構築し、受理時だけその分布を次の現状態に移す。
単独 `propose` は逆比を計算し続ける。
`sample_faulty` のdecoderは `CachedDecoder` で包まれ、missの入力コピー・出力検証とhitのコピーは従来どおりである。
`adapters.py` の変更は同じboolean ndarrayの `np.all` を `.all()` に置き換えるだけで、binary値・shape検査を除去していない。

## 実行した追加検証

Pythonは `A:/dev/mcmc4qec/.venv-dev5-source/Scripts/python.exe` を使い、`PYTHONDONTWRITEBYTECODE=1` とした。
既存テストは `-m pytest tests/test_faststep.py -q -p no:cacheprovider` で26 passed、18.09秒だった。
以下はレビュー時のインメモリ検証であり、恒久的なpytestの追加ではない。
旧実装は `git show HEAD:src/mcmc4qec/faststep.py` の内容を独立moduleとして読み込んだ。

- bit、Pauli、phenomenologicalの小状態で、rateを0、最小正subnormal、1e-250、0.2、1の直前のfloat、1とし、支持内の失敗初期状態からZ・OBF・clusterを順に75stepずつ適用した。
  旧実装と新実装の2,550 attemptで、各stepの状態・密度・syndrome・受理数・移動数・observable・RNG内部状態が一致した。
- 三つの小モデルの全失敗状態からZの全近傍を強制し、受理乱数を0.137に固定した88 attemptを一般参照経路と比較した。
  状態・受理数・移動数・乱数呼び出し列が一致し、うち26の失敗集合外候補では逆分布呼び出しがなく現状態の分布が維持された。
- toric d3/d5/d7、p=0.01/0.22で、二つの論理演算子を順に初期状態として同じstepperを再初期化した。
  Zとcluster_k=2を混合し、decoder cacheをLRU cap=2としてevictionを頻発させた1,800 attemptで、旧実装と新実装の各stepの状態・密度・syndrome・受理数・移動数・RNG内部状態が一致した。

## 検証範囲と補足

極端supportの比較は旧実装との挙動一致を確認するもので、極小確率での浮動小数計算全般の正確性を証明しない。
RNG比較は実施したseed・状態・長さの範囲の検証であり、全seedについての軌道一致の証明ではない。
今回の新規d5/d7 pytestは状態列と受理集計を比較しており、RNG内部状態の直接比較は上記の独立レビュー検証で補った。
失敗集合外候補で逆分布構築がゼロ回になる検査は、今後の性能退行防止として恒久テスト化する余地があるが、現時点の正当性を妨げる事項ではない。
strict型検査の統合は別担当の変更待ちであり、このレビューでは実施していない。
全suiteと速度測定はこのレビューでは実施していない。
研究リポジトリへの変更・commit・pushは行っていない。
