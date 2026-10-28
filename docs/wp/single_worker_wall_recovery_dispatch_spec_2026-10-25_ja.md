# index 0 の walltime 復旧投入契約

旧 index 0 のジョブが walltime 上限で終了したため、計算設定と保存済み入力を保持し、index 0 だけを新しい実行場所と明示した 4 時間の上限で再投入する。
残りの index 1〜11 は、元の prepared・manifest・runner・ジョブをそのまま維持する。
本契約は index 0 の既定外 walltime に限定し、任意条件の override を一般に許可しない。

新 dispatcher の `submit` は index 0 以外を、外部入力の読み出しや qsub より先に拒否する。
全 12 条件の検証では、各 prepared が指す固有の manifest・runner・resource plan を照合する。
旧 11 条件の prepared と script は、直前の pin 済み receipt に記録したものと完全一致させる。
元の ledger のジョブ ID を保持し、既存ジョブを再投入しない。
index 0 のみ新 front の prepared・script・出力先を用い、同じ物理ノード・1 CPU・既存メモリ量・4 時間の制限を要求する。
science engine、evidence reader、親と子の環境、数値設定の変更は許可しない。

qsub の前に、既存の共有ロックと物理ノード上限判定を二回行う。
投入意図と応答を保存し、応答が不明な場合は再投入せず照合を待つ。
テストは PBS 内で実施し、本番投入は root の実行判断後に行う。
新 dispatcher の 13 件の境界テストは、PBS ジョブ 265598 で成功した。
ジョブは `F`・終了コード 0、walltime は 1 秒、テスト本体は 0.143 秒だった。
テストには 12 件の固有 prepared の読取検証、保持済み 11 件への投入拒否、異なる runner の誤適用拒否、元 ledger の変更拒否、4 時間以外やメモリ・CPU 変更の拒否、元ファイルを変更しないことを含む。
この fixture の成功は、本番 native preparation または再投入の完了を意味しない。
本番再投入は、この文書更新時点では未実施である。

## 実環境での全 12 prepared の受入

native preparation のジョブ 265602 が成功した後、既存 policy の preparation と index 0 の runner pin だけを差し替え、新しい v6 policy を作成した。
物理ノード、共有ロック、容量上限と残りの policy フィールドは保持した。
ジョブ 265603 を `qsub` で投入し、全 12 件について実際に各 prepared が指す runner を読み込み、dispatcher の preflight、native bootstrap、manifest と resource の既存検査を行った。
265603 は 69 秒で `F`・終了コード 0 となり、全 12 件が通過した。
元の 11 件を新 runner に置き換える検査ではなく、それぞれの元 runner・manifest・plan を用いた。
この受入ジョブも本番 worker の投入と科学データの読み出しを行っていない。
policy と原本証跡 13 ファイルは private `output/single_wall_policy_native_acceptance_v1/` に保存した。
本番 index 0 の投入は、引き続き root が後続 controller の準備状態と照合して行う。
