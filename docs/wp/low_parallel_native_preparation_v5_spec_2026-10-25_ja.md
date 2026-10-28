# portable reader修正と既存5worker保持のnative準備v5

portable readerの計算後PBS照合で、qstat出力の最上位timestampだけが観測ごとに変わるため失敗する条件を復旧する。
比較対象から最上位timestampだけを除き、全出力の保存・返却とそれ以外の項目の照合は維持する。
正常に継続しているindices 0・1・6・7・8は、条件・親ジョブ・prepared・manifest・投入証拠を変更せず保持する。
indices 2・3・4・5・9・10・11の7条件だけ、明示した運用上のreader修正とbyte同一CLI移設を使って新しいworkerを準備する。
数値入力・復号条件・選択規則・分母・親環境・親runtime・主なsource closureは変更しない。

新しいeffective manifestは全12 singletonを含み、既存5workerの条件と親ジョブは元manifestと完全一致させる。
新しく生成するprepared・scriptは置換対象7workerだけとする。
新receiptの全12worker一覧は実際の旧・新preparedとscriptの絶対pinを記録し、旧workerを新manifestで実行したものとして書き換えない。
既存5workerのindex・prepared pin・実job IDと、新7workerの投入対象を別々に記録する。
旧7workerの終端状態と、新readerの実CLI検証の証拠を確認してから準備する。

環境とreaderの変更は受入済みmixed merge契約と運用変換の検証器へ直接渡す。
新manifestの差は置換対象7条件の承認済み環境・親ジョブ・出力先に限定する。
元5workerの資源・source・Python・native binary・入力pinを検査するが、元workerに新たなfresh-output検査や書込みを適用しない。
新7workerのscript・資源・配置・native import・fresh出力先をPBS内で検証する。
上限は2物理ノードで、最終配置は各ノード6workerを維持する。
ローカルPCで計算・テストを行わず、準備成功と本番の完走・混合・精度の保証を区別する。

本仕様の作成時点でv5準備・試験・投入は未実施である。
