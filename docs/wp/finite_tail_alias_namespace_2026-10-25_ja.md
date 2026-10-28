# 後処理 alias の host 間検証

PBS の計算 host と外側 controller の host では、共有ファイルが同じでも `st_dev` が異なる場合がある。
旧 alias record の stat 全体を別 host でそのまま比較すると、移動していない alias を拒否する。
別版 binding は producer の観測と共有 namespace の明示 authority を持つ schema 2 の record を生成する。
元 schema の record に producer 情報を後付けして受理する経路は設けない。

同じ host 内の stat 比較と、control ファイルの読取前後検証は変更しない。
別 host の比較では共通 namespace helper に各 stat を渡し、明示した host・mount・path・device の対応だけを許可する。
inode・size・mtime・ctime・mode、リンク文字列と順序、解決先、元の内容 hash と authority は保持する。
device を一律に比較対象から除く実装ではない。
共通 helper の capture は同じ host・PBS job・mount 状態で決定的である必要があり、同一 alias の重複検証を緩めない。

元 source の SHA-256 は `bb61f1d3031302708b0b6263341c85e3cdc2b846b047144d434f733f71bb385c` である。
派生 transform の SHA-256 は `26f7a32e6c6dc0e9b6e38b492fed7c5a86a714284c7cf169944d1bfe79daeb38` である。
元 source の exact bytes から alias の構築・検証と小 helper の pin 検証だけを変更し、科学入力の列挙・読取は変更しない。

最初の fixture ジョブ 265663 は、追加試験の spy が準備中の呼出しも集計したことと、反復試験で模擬 host の初期化を忘れたことにより F/1 となった。
production transform や拒否条件は変更せず、この 2 箇所の fixture bookkeeping を修正した。
元の失敗 source・ログ・PBS 終端を保持し、別 stage の 265664 で元 21 件と追加 14 件の計 35 件が 0.104 秒で成功した。
265664 は F/0、run count 1、wall 1 秒である。
受入 receipt の SHA-256 は `d4b56b72cdc54c0328c8c814e5f60ab3c35de20c81b7579df822e621086a06dc` で、識別子除去前の非公開原本を指す。

この 35 件は共通 namespace helper を明示的な test double にした binding 境界の受入である。
実 mount の対応、実 helper を埋め込んだ派生 source、実 PBS から外側 host への移行、本番 config の接続は、この fixture 成功だけでは受入済みとしない。
科学データの再計算と本番 controller の切替は実施していない。

## 共通 helper との保証範囲の照合

独立レビューで、最初の test double が producer の job 番号を固定値と比較し、実 helper の構文検査より強くなっていることが分かった。
実 helper に合わせて double を訂正し、有効な別 job 番号を binding 単体では拒否しない試験を追加した。
正しい producer との対応は、実 PBS job と host を確認する元 job runner、実 parent と一致する operation、capture、固定 source による completion/candidate の封印、外側 receiver の exact parent/proof 検証という既存経路で拘束する。
これを binding 単体の保証とは記載しない。
production binding transform は変更していない。

合同試験の初回 265668 は F/1 であり、dispatch の transform が元 source の改行を含まない literal を要求したことと、追加の job 試験が旧版の policy fixture を使ったことが原因だった。
alias 36 件と receiver 6 件はこの初回も成功したが、合同受入済みとは扱わなかった。
dispatch の literal を実際の元 source に合わせ、job fixture に実 v2 が要求する dynamic policy の field を追加し、原本と失敗記録を保持して別 stage で再試験した。
本番 job の source や拒否条件は変更していない。

265670 は F/0、run count 1、wall 1 秒で、次の合同 77 件が成功した。

| 対象 | 件数 | 所要秒 |
|---|---:|---:|
| dispatch の元 fixture と namespace 委譲 | 31 | 0.179 |
| alias の元 fixture と訂正した境界試験 | 36 | 0.108 |
| 元 Coordinator の submit parent・source・payload・completion 拒否 | 6 | 0.020 |
| 実 job v2 の parent・host・source・ledger 拒否 | 4 | 0.053 |

合同受入 receipt の SHA-256 は `ca11d86f8ad00a1fe1f7aff9e22f6901ea6bc30b3a8b71c1e0ad805ee64f3a08` で、識別子除去前の非公開原本を指す。
dispatch transform の受入 SHA-256 は `8fb58341ba8d8f188de895664fe2b0575f1bd896d89e5ed9778dcb28290e7d66` である。
実 mount の観測と派生した本番設定の native 受入は、合同 fixture と別の証跡として接続する。

## 実 alias・lock・carrier の host 間往復

265674 の実 PBS 内で、固定した新 binding と dispatch の source/API を使い、受入 stage 内だけに小 source の symlink、scratch lock、5 MiB を超える sparse fixture carrier を作成した。
実 parent job の submission・script・qstat・host を照合した後、元 Hooks で qsub 直前の Deferred candidate を生成した。
親の実 F/0 後、別 host の observer が同じ alias と candidate を検証し、qsub を呼ばない fake runner に限って scratch ledger の作成と scratch lock の release を確認した。
この往復は実 namespace helper と実 host ごとの device 対応を用いており、前節の double による fixture とは別の受入である。

observer の受入原本 SHA-256 は `725562b9ff35dfc510c28db7160db4d75b10228ab1cb5c14da758106dfdbb476` である。
probe source の SHA-256 は `c76d4385bd7de8c408b1ab0137eaf904904ee4aedb4378a415b8b77d86edba18` である。
実 alias 検証、実 lock/carrier の stat 検証、scratch lock release が成功した。
carrier の内容を observer が開くことは audit hook で禁止し、実 qsub、本番容量の承認、科学的な検証、本番出力の変更はいずれも実施していない。
元 finalizer の戻り値に含まれる投入フラグは、この受入では fake runner の結果であり、実 scheduler へ child を投入したことを意味しない。
本番 lock、既存科学 job、科学データはこの scratch 往復の対象外である。
