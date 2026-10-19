# BeliefFind factoryの小仕様

2026-10-18の追加decoder依頼に対し、一般CSS用の`belief_find_decoder`と独立sector合成`depolarizing_belief_find_decoder`を追加する。
実装前にこの仕様を定め、受入テストを作成してから本体を実装する。

## 契約

`code`はCSSCode、`errors`はXまたはZであり、Xにはhz/lz、Zにはhx/lxを用いる。
`p`は0<p<1の有限な固定sector priorであり、samplingのpを追従しない。
depolarizing版のpも既存BP-OSD APIと同じsector priorであり、物理depolarizing確率p_starに対応させる場合は利用者が`p=2*p_star/3`を渡す。
独立sector復号という近似をmetadataに残し、物理I/X/Y/Zノイズの相関は変更しない。
既定はmax_iter=100、bp_method=min_sum、ms_scaling_factor=1、uf_method=inversion、bits_per_step=1とする。
schedule=parallel、omp_thread_count=1、random_schedule_seed=0、serial_schedule_order=None、input_vector_type=syndrome、random_serial_schedule=Falseを固定する。
ldpc 2.4.1のBeliefFind constructorはrandom_serial_scheduleを受け付けないため、構築後のpropertyにFalseを明示設定し、その実効値を確認する。
許可したkeyword以外を拒否し、整数・実数・文字列の型と範囲をnative constructorより前に検査する。
max_iterは1以上のC int範囲、bits_per_stepは1以上n以下とする。
bp_methodはmin_sum/minimum_sumとproduct_sumを許可し、metadataにはcanonical名を残す。
ms_scaling_factorは有限非負値とし、0の動的係数というbackendの意味を維持する。
uf_method=peelingは全列の重みが2以下である場合のみ許す。
境界を表すdegree1を許すが、degree0列はinversionでもnative constructorより前に拒否する。
ldpc 2.4.1のUfDecoder constructorはdegree0でC++例外を投げ、BeliefFindもこのconstructorを使うためである。
syndromeの実現可能性と補正のHc=sを共有CheckedCorrectionAdapterで必ず検査する。
入力は1次元binary syndrome、出力は明示したlogical mapによるbinary logical predictionである。
不正な補正・実現不能syndrome・native例外を黙って成功や別decoderへ変換しない。
BeliefFind自体が行うBP後のUF処理は名前の付いたアルゴリズムの一部であり、追加の隠れたfallbackは実装しない。

## 受入

Steaneとtoric d2の全実現可能syndromeについて、X/Z両sectorの直接native補正との一致、Hc=s、反復・逆順・新規objectの一致を調べる。
peelingはdegree1/2を含む小CSSの全syndromeとsurfaceの小符号で検査し、degree3以上はnative呼出し前に拒否する。
degree0の両modeでの入口拒否もnativeを呼ばず検査する。
depolarizingはsector順と同一priorの伝達、metadataの独立近似を確認する。
不正設定、syndrome、補正、optional依存なしのImportErrorを検査する。
この受入は有限の入力での同一環境内再現性を示すもので、全入力・異なるOS/ビルドでの決定性や論理エラー率を保証しない。

一次資料は[公式BeliefFind API](https://software.roffe.eu/ldpc/ldpc/belief_find_decoder.html)と導入済みldpc 2.4.1の`belief_find_decoder/_belief_find_decoder.pyx`および`bp_decoder/_bp_decoder.pyx`である。
文書に記載された既定inversionと導入済みconstructorの既定peelingは異なるため、factoryはinversionを明示する。
degree0制約は[上流UF source](https://github.com/quantumgizmos/ldpc/blob/main/src_cpp/union_find.hpp)のUfDecoder constructorと、ldpc 2.4.1 sdistの同じ箇所でも確認した。

## 実装後の確認

Windows Python 3.11.9・ldpc 2.4.1で`tests/test_belief_find_decoders.py`を実行し、58 passed・1.80秒であった。
Steane・toric d2のX/Z全実現可能syndromeをnative補正と照合し、SteaneではBP非収束後のUF経路を実際に通ることも確認した。
toric d2とsurface d2のpeelingを全syndromeで確認し、HGP・BB72・tile72・tile288の両sectorでは固定した3状態ずつを確認した。
全入力検査と、この有限のprobeでの結果を一般の混合・収束・論理エラー率の検証とは区別する。
strict mypyは既存`.venv-dev5-source`環境で本体1sourceを検査し、成功した。
Linuxでの新factoryテスト、decoder間の速度比較と論理エラー率の比較はこの作業では未実施である。
本実装は公開exportを別途統合するための独立moduleであり、既存decoderとクラスタの稼働中設定は変更していない。
