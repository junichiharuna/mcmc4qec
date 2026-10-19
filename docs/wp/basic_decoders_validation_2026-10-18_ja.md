# 基本decoder追加の実装・検証記録

BP-LSD、BeliefFind、単独Union-Findと各depolarizing sector版の6factoryを公開APIへ統合した。
小仕様・受入・実装の順で分担し、独立sourceレビューとWindows/Linux受入を行った。
既存BP-OSD・MWPM・sampling既定と稼働中cluster bundleは変更していない。
利用例と再現手順は [基本decoderの比較例](basic_decoders_usage_2026-10-18_ja.md)、APIの引数は [英語API](../api_en.md) にある。

## 契約と適用限界

新factoryはsyndromeの実現可能性と補正のbinary形状・Hc=sを確認した後、logical predictionを返す。
不正補正やbackend例外を論理成功とせず、例外を呼出し元へ伝播する。
BP-LSDとBeliefFindのpは固定binary sector priorで、depolarizing物理確率qに合わせる場合は2q/3を明示する。
独立sector decoderは復号の近似であり、noiseのY相関を変更しない。
native binary・環境・設定をladder全体で固定し、decoderごとに独立referenceを構成する必要がある。

BP-LSDはorder0のみ対応する。
[独立レビュー](basic_decoders_review_2026-10-18_ja.md)でzero syndromeの未初期化local読取りと、LSD-CSのglobal/local nullity差による境界問題をsource上で見つけた。
zero syndromeはnativeに渡さず恒等補正とする規則をmetadataに記録し、正orderはnative前に拒否した。
この処理を他decoderへ暗黙に適用せず、backend依存本体も変更していない。
LSD-Eに同じ範囲外書込みがあると確認したわけではなく、正orderの非対応は現時点の受入範囲である。
sourceと配布binaryの厳密な対応や、特定binaryでの未定義動作の発生を証明したとは扱わない。

BeliefFindはinversionが既定で、peelingは列次数1または2に限る。
単独UFもpeelingとinversionを区別し、ldpc 2.4.1限定のstr/bool binding互換処理をmetadataへ記録する。
UF系の両方式はnative制約により次数0の列を拒否する。
単独UFは非重み付きでpriorを用いず、実装が成長制限を無視するためbits_per_step=1だけを受け付ける。
別版のUFは検証されるまで明示例外となる。

## 実行済みの確認

| 対象 | 結果 | 範囲 |
|---|---|---|
| Windows source、新factory・adapter・公開API | 202 passed / 3.60秒 | 最終zero規則・正order拒否を含む7ファイル |
| Linux source、上記と利用例 | 210 passed / 4.13秒 | 同一source、ldpc 2.4.1、skipなし |
| installed core wheel、上記7ファイル | 114 passed / 88 skipped / 0.98秒 | native依存なし、skipはoptional受入 |
| installed optional wheel、上記7ファイル | 202 passed / 3.83秒 | ldpc 2.4.1 |
| 既存decoder・phase flip・公開型検査 | 40 passed / 23.80秒 | 追加decoder統合時の回帰 |
| 最終sourceのstrict mypy | 32 source成功 | 全package |
| 文書index・比較例 | 14 passed / 7.58秒 | 3符号CLI、exact/MC、保存結果、公開export文書 |

core/optionalの`verify_wheel.py`も終了コード0を確認し、wheel内32 Python sourceと作業treeのbyte一致、全登録quick例とoptionalの4quick notebook、README/tutorialのPython blockを確認した。
全pytest suiteは今回再実行していない。
検証ログ・Linux入力hash・native hash・source bindingは [data_basic_decoders_2026-10-18](data_basic_decoders_2026-10-18/) にある。
最終Linux配置は`20261018-basic-decoders-v2`で、v1は独立レビュー修正前の履歴として保持する。
Linux v2 archive SHA256は`d61c442052c570309d8ff904e80b6dedd79a4c28198a8d8dc0903b4371563e90`である。

小符号全syndrome・全128状態・固定少数状態と同環境の再呼出し等は、全入力の決定性やOS間一致の証明ではない。
新decoderの速度順位、混合、bias・被覆、time-to-accuracyは未校正であり、利用例の短いMCを根拠に推奨順位を決めない。
このdecoder受入の後、主4条件のtile BAR校正・混合比較・独立計時と層別reference本番は完了した。
低noiseの本校正・独立計時とgoal全体の最終報告は未完了であり、最新の進行状況は [tile検証の状態文書](tile_validation_status_2026-10-17_ja.md) を参照する。

2026-10-18の追加照合では、現在のpackage 33ファイルと受入対象の計46 repository入力がLinux v2受入manifestとbyte単位で一致した。
統合記録が参照する15件の検証証拠のSHAも一致し、結果は [現worktreeの照合記録](data_basic_decoders_2026-10-18/current_worktree_binding_2026-10-18_v1.json) に保存した。
これは保存された受入と現sourceの対応確認であり、新たなテスト実行、Linux native環境の再検査、追加decoderの科学的校正ではない。
