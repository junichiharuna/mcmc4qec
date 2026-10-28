# index0の壁時間延長と11件保持のcontroller仕様

比較index0のジョブ265564は要求壁時間1時間5分を超え、PBS終了コード-29となった。
旧controllerとjournal、旧失敗ジョブの記録を保持し、正常終了・実行中の他11件を再投入しない。
新front-v6ではindex0だけを壁時間4時間のrunnerで置き換える。
engine・evidence・readerと科学的選択規則は変更せず、wall-only source変換を明示した証拠で検証する。

## 固定契約

新準備receiptはschema4、purposeを`low_noise_wall_recovery_native_preparation`とする。
`prior_preparation`で旧front-v5の準備receiptを固定し、`worker_sources_by_index`で12件それぞれのrunner・evidence・engineを固定する。
launch対象はindex0のみで、保持対象はindex1〜11の11件である。
保持記録はindex、元prepared pin、元実ジョブIDを明示し、元manifest・資源・環境を新しいものへ書き換えない。
保持11件のledger欠落や不一致は停止条件とし、自動投入しない。
新index0の投入だけを共有lockと2物理ノードの容量ゲートを通す`qsub`で許す。
workerのpreflightとterminal回収は各preparedに固定された固有runnerを使う。
不明なPBS照会、timeout、履歴欠落は再投入の根拠としない。
failedジョブやcontroller異常時も他の実行中ジョブを保持する。

## 受入条件

- index0だけを新規投入でき、11件のどれにも再投入関数を呼ばない。
- 保持prepared、job ID、runner、manifestの差替えを拒否する。
- 新index0に旧runnerを流用したり、保持workerに新runnerを割り当てたりできない。
- 実workerごとの資源とPBS配置を照合し、旧失敗ジョブを成功workerとして取り込まない。
- 新controllerは新しいjournalに一度だけ起動し、旧journalと常駐processを上書きしない。
- 全12結果の受理は新merge内で検証し、その後に独立計時と最終報告へ進む。

PBSジョブ265600で54受入テストが成功し、F/exit 0、実行時間0.027秒、空のPBS標準エラーログを確認した。
保持11件の欠落ledgerが投入関数へ進まないことと、12件それぞれの固有runnerでpreflight・terminal回収を行う実workerメソッドを検査した。
PBSジョブ265604で実preparedを用いたshadow constructorが成功し、F/exit 0、walltime 1秒、空のPBS標準エラーログを確認した。
shadow確認はtick・投入・科学計算・実controller起動を行っていない。
実controller起動は別に検証し、本記録時点では未実施である。
