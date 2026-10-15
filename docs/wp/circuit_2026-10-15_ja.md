# 回路効果差分と明示location群のH提案

## 実装前の小仕様

物理locationは排他的なカテゴリ座標として保持し、受理候補の検出器・論理効果は変更locationの旧ラベルと新ラベルの効果をXORして求める。
専用stepは厳密な組み込みCircuitFaultModel/CircuitFaultNoiseと既定failureのみ使用し、独自failureと派生型は一般経路へ戻す。
既存OBF・Z・physical単一提案の乱数呼び出し順序と全棄却の保持を維持する。
Hの群は利用者がlocation indexの互いに素な非空部分集合として明示し、各群のchannelとfault label順序が完全一致することを要求する。
同じalphabetサイズだけから異なる物理channelの対応を推測しない。
群に所属しないlocationはHで変更しない。
群は状態と無関係に一様選択し、binaryではk個の占有・空locationを交換し、その他は確率1/2ずつで交換と占有locationの再ラベルを選ぶ。
必要なlocation数が不足する枝は自己遷移とし、混合率を再正規化しない。
提案は対称だが、異なるlocation率・条件付きPauli率・零supportに対して完全な密度比と共有failureを一般MHで評価する。
H単独は群別占有数を保存するため一般に既約ではなく、詳細釣合いと別に検証する。
lazyの正の自己遷移は周期性を除くが、連結性は保証しない。
公開既定は変更せず、回路Hは明示群が設定された場合だけ使用可能とする。

## 検証計画

小さい混合alphabet回路を列挙して提案正規化・順逆確率・support・失敗条件付き詳細釣合いを検証する。
一般経路と専用経路について同seed状態・受理統計・次の乱数を比較する。
全効果再計算と差分を列挙比較し、独自failureのfallbackを確認する。
速度は軽量な固定初期状態の回路benchmarkで計測し、未計測の精度保証は行わない。

## 利用方法と実装

`PhysicalClusterExchange`を`mcmc4qec.circuit`から公開し、`KernelConfig.circuit_groups`が明示された回路だけ既存`cluster`混合率をこの提案へ割り当てる。
例えば同channelのlocation 1と2を交換する場合は`KernelConfig(single=.2, zanella=.4, circuit_single=.2, cluster=.2, cluster_k=1, circuit_groups=((1, 2),))`を使用する。
群を省略した回路で既定のclusterを使用すると従来通りエラーになり、暗黙に群や混合率を補わない。
専用stepは既存効果tableを参照して構築時の全basis再計算も省き、既存FastStepperのZ分布保持・MH・decoder cacheを再利用する。
任意の独自failureは既存の一般MH経路で評価する。

## 実測記録

2026-10-15、Windows Python 3.11の既存optional環境で、初回の新受入テストと既存回路kernelテストは20 passed、27.23秒だった。
RNG最終状態・有限例の混合連結性・lazyを追加後、新受入テストと既存faststepテストは31 passed、9.65秒だった。
等alphabetでも異channelを拒否する検証と派生型fallback検証を加えた最終の新受入テストは14 passed、3.54秒だった。
共通効果tableの型を`list[np.ndarray]`へ統一後の最終新受入テストと既存faststepテストは33 passed、9.24秒だった。
`benchmarks/bench_circuit_step.py --steps 100 --compare-delta`は共通の失敗初期状態から実行し、各kernelの全保持状態と受理統計の一致を確認した。
比較対象は既存product-noise Z高速化を有効にした一般stepであり、Zの全近傍density再計算版ではない。

| kernel | 専用step秒 | 一般step秒 | 比率 |
|---|---:|---:|---:|
| physical単一 | 0.110 | 0.705 | 6.43 |
| Z | 0.088 | 2.171 | 24.76 |
| Z+OBF | 0.103 | 1.771 | 17.19 |

初期失敗状態探索は6回・0.080秒で上記時間には含めず、各samplerの設定・cache初期化と診断は含む。
この100stepは速度と同seed軌道の確認であり、混合や被覆の校正ではない。
専用stepには効果差分以外に分布保持も含まれるため、比率は効果差分だけの寄与を分離しない。
物理Hの実符号での混合改善と一般の失敗集合上の既約性は未検証であり、小さい列挙例の連結性を一般保証にしない。

上記速度は回路担当の独立worktreeで測ったものであり、親のtoric高速化と型注釈を統合した後の性能計測とは区別する。
統合後の全source/wheel検証結果は [統合報告](final_report_2026-10-15_ja.md) に記録する。
