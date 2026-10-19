# Portable BARの最終集約：小仕様

## 目的と現状

C0T2の元samplingを使ったPC側の後処理について、全768 group・192 replicateを元環境の監査と独立referenceへ結び付ける。
既存のcluster collectorはanalysisのruntime・PBS identityも固定しているため、そのmarkerをPC出力で置き換えない。
sampling環境、後処理環境、trace監査環境、reference環境を別々に記録する明示的なreaderを用意する。
公開済みcommit候補と、実行中driver・入力・source hashは変更しない。
この文書は受入条件であり、最終readerの実装・全cohortの検証完了を示さない。

## 受入条件

1. 元production manifestと全768 groupの集合を固定し、各groupのhostを既定の通番mod 44で照合する。
2. 回収archiveは既存のmember hash・parent binding・実execution intent・source・runtime検証を再利用し、archiveの取り違え、同一groupの重複、未知group、host変更を拒否する。
3. samplingの全partitionが終端し、既存の完了証拠で192 anchorと全184320 sample taskの集合を検証する。
4. trace監査は元のnative環境でqsubにより実行し、実PBS終端・submission・runtime・元production manifestを照合する。
5. 全成功groupについて、元の`verify_group`と同じsample marker集合・全payload hash・記録済みsampling failure・checkpoint数の照合を行う。
6. 192 anchorの全artifact、完了証拠、解析入力markerを照合し、同じreplicateで共有するanchorを別物へ置き換えない。
7. source・plan・変換規則・geometry・Problem metadataを照合し、後処理のdecoder factory呼出しを禁止する。
8. 元の全設定、bootstrap seed、burn-in、trace window、chain数、ladder、誤差法を保持する。
9. 解析のinfrastructure failure、sampling failure、未定義診断、区間未取得を別々に記録する。
10. infrastructure failureのgroupも全88設定の予定行を分母に残し、取得していない推定値・区間・診断を作らない。
11. 未完了groupが残る段階は途中集計として出力し、全cohortのbias・RMSE・被覆とは表示しない。
12. 全group終端後の比較では、元の有限区間referenceと未観測重みの上界を保持し、元環境でreferenceのraw artifact・source・conditionを再検証する。
13. 解析環境ごとのprovenanceを結果へ保持し、元runtimeで全後処理を実行したという記録を作らない。
14. 読み取り前後の入力hash・解決済みpathを照合し、別directoryへの排他的な出力を用いる。

## 必要な受入テストと追加の実測

小さいfixtureで、欠落・重複・未知group、host違い、source/runtime差替え、入力markerとpayloadの不一致、referenceの条件違いを拒否する。
infrastructure failureとsampling failureを含むfixtureでは、予定group数・設定行数・seed分母が変わらず、未取得項目が明示されることを確認する。
診断flagの有無や推定値によってgroupを除外しないことを確認する。
実回収済みのbatchを使ってarchiveからgroupへの結び付きを検証するが、その部分集合を全cohortの受入とは扱わない。

移植受入の実測は現在4 chain・burn 600・保存600の短いwindowである。
追加で事前指定したC0T0 group `(0,0,0,0,0)` の全設定を、保存済みの元環境の解析と比較する。
浮動小数点の許容差は既存のrtol=1e-10・atol=1e-12を維持し、離散値・flag・NaN/None位置は一致を要求する。
この追加比較は後処理の検証用であり、C0T2の科学cohortへ加えない。
全設定の比較は未実施であり、実施後に許容差を結果に合わせて緩めない。

既存`tile_low_noise_partitioned_collection.py`のPBS・runtime検査を迂回する形の移植は行わず、別entry pointとして小仕様・受入テスト・実装の順で進める。
最終検証に成功しても、`nominal_coverage_certified=False`、`population_rmse_certified=False`、全物理状態の再復号は未実施という区別を維持する。

## providerの入力契約（10月20日追記）

providerは独立に固定したcontextファイルのSHA-256を受け取り、各archive・parent binding・receipt・移植照合artifactを相対pathとhashで結ぶ。
最終処理では両hostの全設定照合を必須とし、固定した元reference archiveと回収したJSON・NPZの値を再比較する。
照合結果の`accepted`だけを読んで通過させず、runtime、source、入力archive、変換規則、intent、marker、全設定の行数、許容差と未定義位置を検証する。
成功groupの元sampling recordとanchorは現在のsampling rootから読み取り、既存のpayload readerへ渡す。
全768群の集合・固定host割当・失敗群を保持した計数は既存cohort indexにより検証する。
入力のhashと解決済みpathは全体のEvidenceへ登録し、最終レポートの直前にも再検証する。

転送用contextの作成は、全768群が終端した固定indexと両hostの全設定照合を前提とする。
indexが途中の場合は出力directoryを作らず拒否し、infrastructure failureを含む全群終端は予定分母を保持して扱う。
contextと転送一覧には元ファイルのpath・SHA-256・転送先の相対pathを対応付け、作成前後の入力変更を拒否する。
context作成自体は転送やqsubを行わず、配置後のproviderが全archiveと移植照合を再検証する。
