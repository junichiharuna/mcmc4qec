# 基本decoder追加の独立sourceレビュー

2026-10-18にBP-LSD factoryと共有`CheckedCorrectionAdapter`を読み、native sourceの安全性を有限テストとは別に確認した。
このレビューではpackage sourceを変更せず、危険なnative経路の再現実行も行っていない。
既存198件のWindows/Linuxテスト成功は、以下の経路の安全性を証明しない。

## P1: BP-LSDのzero syndrome経路

導入済みldpc 2.4.1の`bplsd_decoder/_bplsd_decoder.pyx`の133–140行は、非zero成分を見つけた場合にだけ`zero_syndrome=False`を代入してから、その変数を判定する。
冒頭のTrue初期化がない。
同梱のgenerated `_bplsd_decoder.cpp`は7265行で未初期化のint localを宣言し、7398行で非zero時に0を代入し、7417行で読む。
このgenerated sourceをそのままコンパイルした場合、all-zero入力は未初期化localの読み取りに到達する。
今回読んだsourceと配布binaryの厳密なbuild対応は独立に証明していないため、特定binaryで未定義動作が実際に生じたという観測報告にはしない。
all-zeroでテストが成功してもsource上の問題は消えない。
BP-LSDだけに明示したzero syndrome→identity補正をnative呼出し前に設け、metadataにこのdecoder定義を記録することを推奨した。
このidentity規則はp>0.5を含む利用者priorでも同じ規則として定義し、nativeの結果から暗黙に推測しない。

導入済み`.pyx`のSHA256は`2c437681466791f22eed076128f297e185a91a8ea788f691f816b98a192c25e4`である。
導入済みgenerated `.cpp`のSHA256は`c1c5eb1307ea6f9d54f864a9d97cff7972d398e16d51bc44a362116f7074caf6`である。
sdist版`.pyx`のSHA256は`7064a43fc09fc8f3cb8001f7d737e38d341151e0f1ecfa5313b4c0a3fdfb2145`で、同じ初期化欠落を含む。

## P1: LSD-CSのglobal nullity guardではlocal orderを制限できない

[ldpc 2.4.1 sdist](https://files.pythonhosted.org/packages/ac/3d/1642f2456dc4c494ab1209b8da8a886cd4e82280839c8ef434294492738d/ldpc-2.4.1.tar.gz)の`src_cpp/lsd.hpp`を確認した。
archiveのSHA256は`729376026af4e46e550c333152f073dcf42224589380d309f38923e00736ceba`、当該headerのSHA256は`f9710d608870329acfa15bf2df4d7f726a2950ce120314308562c8e566e19bf0`である。
798–803行のcluster追加成長は、要求order、追加成長回数、global bit数、初期cluster sizeによって打ち切られる。
このループの終了はlocal nullityが要求order以上になったことを保証しない。
820–827行は要求orderを変更せず`DenseOsdDecoder`へ渡す。

sdistは`osd_dense.hpp`をincludeしているが、そのheader自体をarchiveに含めていなかった。
そこで[upstream固定commitのosd_dense.hpp](https://raw.githubusercontent.com/quantumgizmos/ldpc/1b0790f682ce572bae5a073a4b9ff02009a587db/src_cpp/osd_dense.hpp)を別資料として読んだ。
SHA256は`227c2b5fca7a32664be368a811a43e01c5267788a568d7d0bf7c742f15bf9263`である。
GitHubのpath別commit履歴ではこのfileの最後の変更は2024-07-01で、PyPI 2.4.1のupload日は2025-12-08だった。
この時系列を配布binaryのbuild証明とは扱わない。
当該headerの58行はlocal nullityをkに設定し、76–84行は長さkのcandidateに対し要求orderまでの添字で書き込む。
条件はk>0だけであり、orderのkへのclampがない。

具体的には`H=[[1,1,0,0],[0,0,1,1]]`はglobal nullityが2なので既存factoryの`lsd_cs, order=2`条件を満たす。
syndrome `[1,0]`のclusterは最初の2bitの連結成分に閉じてlocal nullityが1となり、残り成分のbitを成長で取り込めない。
sourceのCS経路では長さ1のcandidateの添字1へ書き込む可能性があり、global nullity guardでは防げない。
これはCSSとしても`hx`を空、`lx=[[1,1,0,0],[0,0,1,1]]`、`lz=[[1,0,0,0],[0,0,1,0]]`と置けば成立する。
この危険な経路は実行していない。
依存本体をpatchせず、検証済み修正版または安全な別実装を得るまではfactoryでpositive LSD orderをnative呼出し前に拒否することを推奨した。

## LSD-Eとorder0の切り分け

同じDenseOsd sourceのexhaustive経路は2^order個の候補を生成するが、候補の長さはkである。
[固定commitのutil.hpp](https://raw.githubusercontent.com/quantumgizmos/ldpc/1b0790f682ce572bae5a073a4b9ff02009a587db/src_cpp/util.hpp)の11–27行は候補長までしか書かず、kより多いbitは切り捨てる。
このhelperのSHA256は`cc3081270eccf27b0a00bde62cd876e9a770d097549374a41a0838bcd1195dac`である。
この箇所だけを見る限り、EにCSと同じ添字逸脱は見つからず、local k<orderなら候補重複と余分な計算が生じる。
positive orderをまとめて拒否する方針は受入範囲の制限であり、LSD-Eにも同じ欠陥が確認されたという主張ではない。

sdist `lsd.hpp`の743–764行はorder==0ならmethod値によらず既存PLU分解のsolveを行い、`apply_lsdw`に入らない。
そのためcs/eのorder0指定を受け付けるなら、実効動作がLSD-0になることを明記できる。
zero syndromeの対策はこのorder分岐とは別に必要である。

## 共有adapter・一般CSS・設定

共有adapterは左零空間制約で実現可能syndromeだけをnativeへ渡し、binary・長さn・Hc=sを確認してからlogical mapを適用していた。
このため依存check、zero rowに対する不可能な入力、不正な物理補正をlogical成功として通さない。
LSD sourceのconstructorにはUFと同じzero-degree列の拒否はなく、zero columnのあるCSSを一律にUFと同様に制限する根拠は見つからなかった。
zero rowはrealizability checkで入力を制約する。
一般CSSのsector mappingと独立sector近似の記録、parallel schedule・thread1・random schedule無効の明示を確認した。
`_checked_decoder -> codes -> core`の参照は今回のfactory追加による循環importを作っていなかった。
native build間の決定性、混合、論理エラー率、BAR被覆の保証はこのsourceレビューの対象外である。
