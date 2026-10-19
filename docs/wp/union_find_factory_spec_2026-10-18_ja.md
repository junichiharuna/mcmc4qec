# 単独Union-Find factoryの小仕様

2026-10-18の追加decoder依頼に対する仕様である。
既存のBP-OSD、公開sampling既定、実行中のクラスタ校正を変更しない。

## APIと意味

`union_find_decoder(code, *, errors="X", method="peeling", bits_per_step=1)` は固定したCSS符号のXまたはZ syndromeからlogical予測を返す。
Xは`hz`で復号して`lz`へ写し、Zは`hx`で復号して`lx`へ写す。
`depolarizing_union_find_decoder(code, *, method="peeling", bits_per_step=1)`はX、Zの順にsectorを合成する。
これはdecoderの独立sector近似であり、物理I/X/Y/ZノイズとY相関は変更しない。
単独UFはBPとchannel priorを用いず、LLRなしの非重み付き復号を行う。
`bits_per_step`は整数1のみを受け取りdecodeへ明示して渡すが、ldpc 2.4.1のLLRなし経路はこの値によらず全隣接bitを同時に成長させる。
この挙動をmetadataに記録し、有効な成長速度制御と誤解されないよう1以外を拒否する。

`method="peeling"`は列重み1または2のgraphlike行列のみを受け入れる。
列重み1は境界へ接続するbitとして対応し、toricの偶数syndrome制約とsurfaceの境界を区別して検証する。
`method="inversion"`は列重み3以上も受け入れる。
両方式とも列重み0はnative constructorより前に拒否する。
これはldpc 2.4.1の制約であり、syndromeに現れないbitを暗黙に消去して別decoderに変換しない。
共有`CheckedCorrectionAdapter`でsyndromeのbinary形状と実現可能性を確認し、復号後に物理補正のbinary形状と`H c = s`を確認してからlogical mapへ写す。
実現不能syndromeはnativeの停止を待たずに例外とし、不正補正やnative例外を論理成功へ変換しない。

## 版限定の互換処理

対応版は今回実装・受入する`ldpc==2.4.1`のみとする。
この版の`.pyx`は`uf_method`をstrとして受け取り、`.pxd`のC++ boolへ代入するため、空文字列でpeeling、非空文字列`"inversion"`でmatrix inversionを指定する。
public引数は方式名のみで、nativeへ渡した値・互換処理の識別子・ldpc版・LLR非使用をmetadataに記録する。
未知の版は明確な例外とし、例外を捕捉した方式切替・別decoderへのfallback・依存本体の変更を行わない。
optional依存がないときはfactory呼出し時にImportErrorを返す。

導入済みCython sourceと[ldpc 2.4.1 sdist](https://files.pythonhosted.org/packages/ac/3d/1642f2456dc4c494ab1209b8da8a886cd4e82280839c8ef434294492738d/ldpc-2.4.1.tar.gz)の`src_cpp/union_find.hpp`を読んだ。
取得したsdistのSHA256は`729376026af4e46e550c333152f073dcf42224589380d309f38923e00736ceba`であり、LLRなし成長とzero-degree拒否の記述を確認した。

## 受入

小さなtoricとsurfaceの全実現可能syndromeについて両方式のsyndrome一致・X/Z mapping・反復・逆順・新規objectの有限再現性を確認する。
Steaneの全syndromeでinversionを確認し、peelingはnativeに入る前に拒否する。
X/Zを合成した小符号の全sector対とmetadataを確認する。
不正code・sector・方式・成長数・未知版・optional依存欠落・zero-degree・不正syndromeを検査する。
境界のある独立小行列でも奇数syndromeが復号できることを確認する。
有限試験は全符号・全環境の決定性やdecoderの精度・速度・BAR被覆の保証にはしない。
## 実行した受入

Windowsの導入済みldpc 2.4.1で`tests/test_union_find_decoders.py`は40 passed・1.64秒だった。
optional依存を持たない既存core環境では同じファイルが18 passed・22 skipped・1.66秒だった。
既存`.venv-dev5-source`のmypyで`--strict src/mcmc4qec/union_find_decoders.py`が成功した。
toric2とsurface2の全実現可能syndromeについて、X/Z・両方式の物理補正とlogical予測を同object反復・逆順・新規objectで照合した。
Steaneのinversion全syndromeとsurface2のdepolarizing全sector対も検査した。
native方式の区別を調べた追加probeでは、surface2の4syndrome中2個で物理補正が異なり、`[0,1]`に対してpeelingは`[0,0,1,0,0]`、inversionは`[0,0,0,1,0]`だった。
同じprobeのsurface3は64syndrome中20個、toric2は8syndrome中0個の物理補正差だった。
これはこのWindows環境の観測であり、その補正列を他OSの期待値として固定しない。
このfactory実装のLinux受入、time-to-accuracy比較、BAR被覆校正はここでは未実施である。
