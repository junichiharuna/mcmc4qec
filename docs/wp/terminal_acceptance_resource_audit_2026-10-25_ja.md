# 合流後のterminal受入処理の資源監査

## 結論

現行の`accept_terminal`はraw科学payloadを再hashしないが、大容量の合流JSONを複数回読み、全件parse・辞書検査・deepcopy・全体serializeを行う。
これはcontroller上の軽い待受処理とは扱えず、資源を予約した別PBS jobへ隔離する必要がある。
実合流JSONは監査時点で未生成なので、正確な最大メモリと所要時間は未測定である。
この結論はsourceとファイルstatに基づく資源リスクの判断であり、実際のOOMや処理時間を測定した結果ではない。

## 読取り範囲と観測

稼働中controller・worker・科学source・結果は変更せず、小さいconfig・prepared・terminal descriptorだけを上限256 KiB付きで読んだ。
小さいJSONをparseした回数は21回、各入力の最大は30,311 bytes、合計84,839 bytesであり、巨大JSON・rawの中身は読んでいない。
pin照合のため同じ小さいファイルを再読込みする箇所と、sourceの読込みはこの合計に含めない。
巨大成果物はstatで存在・byte数・mtimeを取得した。
私的な原観測は`output/merge_terminal_acceptance_audit_v1/stat-observation.json`に保存した。

|worker index|存在するvalues.jsonのbyte数|
|---:|---:|
|0|230,919,516|
|1|300,319,375|
|2|249,070,805|
|3|86,840,127|
|6|88,196,318|
|7|112,452,533|
|8|128,754,590|
|上記7件の合計|1,196,553,264|

合計は約1.11 GiBであり、これはworker成果物の合計であって将来のmerge-resultの実サイズではない。
残るindex4・5・9・10・11のvaluesと、merge-rootのprepared・merge-result・selection・acceptedはこのstat観測時点では未生成だった。
workerが参照するmanifestは約1.24 MB、resource planは約23 KB、親environmentは79,840 bytesであり、巨大成果物とは規模が異なる。
既知3条件の738,006 inputfilesという依頼時情報は本監査で再数えず、上表は独立したstat観測とする。

## sourceから確認した処理

現行flowの`merge()`はPBS成功終了を確認した後、同じcontroller processで`merge_runner.accept_terminal()`を呼ぶ。
実execution runnerはSHA-256 `4419108ed08f0f133659423108a418b5caeaf679db902b5b6d9d2d3e716a6522`で、8 CPU対応の差分以外は元runnerの受入処理を維持する。
その処理には次が含まれる。

1. `terminal.json`を保存した後、`e.pin(output)`と`Proof.read(output)`でmerge-result全体を読む。
2. `Proof.read`は全byteを読み、hash照合後に`json.loads`し、前後の`Proof.track`でもファイル全体をhashする。
3. resultは全workerの`worker_acceptances`、トップレベルの`input_sha256/input_resolved`、candidate内の同名mapを保持する。
4. `contract.promote`はcandidateをdeepcopyし、元の科学的選択規則を再検証する。
5. 選択検証は全input mapの型・hash・key集合を確認し、24行の選択規則も再構成して照合する。
6. `Proof.finish`はmerge-resultファイルも再hashし、`runtime.save`は全体を`json.dumps(..., sort_keys=True).encode()`してから書く。

merge-resultだけで、`pin`、`Proof.read`前のtrack、read_bytes、同read後のtrack、finishの少なくとも5回のファイル全体読取り経路がある。
OSのpage cacheが効けば同量の物理ディスク読取りになるとは限らないが、hash・メモリ走査・parse・serializeの費用は残る。
これはraw科学payloadの再検査と区別する。

## メモリと失敗時のリスク

merge-resultのbyte数をB、parse後のPython object群をE、候補deepcopyで増えるcontainerをD、selection serialize量をSとすると、単にBだけのメモリでは足りない。
parse時の全入力buffer、decode buffer、辞書・文字列object、Eを保持したままのD、serialize時の全体文字列とbytesが重なる局面がある。
deepcopyは不変な文字列まで必ず複製するわけではないため、全文字列が二重になるとは断定しない。
それでも巨大dictのcontainer複製、集合生成、ソート、全体serializationは入力件数に比例する追加メモリを必要とする。
7workerのserialized出力だけで約1.11 GiBあり、合流resultには複数のinput mapが含まれるため、数GiB規模以上のRSSとなる懸念は強いが、倍率や上限は未測定である。
controllerにはこの仕事用のPBSメモリ・時間予約がない。
OOM等で停止すると、先に保存した`terminal.json`だけが残り、元runnerの再試行禁止規則により単純な再実行はできない。
自動再試行でこの状態を隠してはならない。

## 最小の隔離仕様

元merge prepared・runner・execution contract・結果・元job IDを固定したまま、別のterminal受入jobを`qsub`で一度だけ投入する。
初期予算は1 CPU・96 GiB・4時間・単一ノードとし、未実測の保守的な資源予算であって完了時刻や十分性の保証ではない。
job内で元の`accept_terminal`を変更せずに呼び、元と同じ検査、selection内容、accepted schemaを保存する。
元merge job IDと新受入job IDは別フィールドで管理し、元のsealを付け替えない。
controllerへ返すのは小さい完了receiptとaccepted artifact pin、selection pin、サイズ・stat・元preparedとの対応だけとする。
controllerは受入jobのF/exit 0、実script・資源・run_count・source・receiptを照合し、大きいresultやselectionをparse・再hashしない。
既存のintent・qsub response・ledgerがある場合は実PBS状態と照合して採用し、曖昧な投入応答や途中成果物を再投入の根拠にしない。
成功receiptなしの既存terminal/selection/acceptedは自動受理せず、原本を保持して個別照合する。

この仕様は受入処理だけの境界を示す。
独立監査で後続tailの全6roleにも巨大selection/resultを読む経路が見つかっており、census準備とreport準備だけを隔離して全体完了とはしない。
有限な重いactionをPBSへ分離し、軽い待受・資源gate・子job投入は外に残す境界を別途設計・受入する。
大メモリの親PBS jobにtail全loopを包み、子job待受中も資源を保持する方式は採用前にdeadlockと2物理ノード制約を検証する必要がある。
