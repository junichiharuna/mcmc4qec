# 未予約群の分担planと群数検査の受入記録

## 確認できた範囲

2026-10-20に[小仕様](portable_bar_remaining_assignment_spec_2026-10-20_ja.md)に従い、分担planの生成・検証器と旧新経路の群数検査を実装した。
小仕様、受入テストの追加、未実装による失敗確認、実装、テスト実行の順に進めた。
新経路の配置・起動・回収・実artifactの混合集約・最終provider接続は未実施であり、264群の再割当て計算はまだ開始していない。

[固定plan](data_portable_bar_2026-10-19/remaining_assignment_plan_v1.json)のSHA-256は `d866e2a0df455dc267aade83ec9f05b3a5d19f0fc936368a17017f191f459b11` である。
予約済み484群を保持し、基準snapshotで未予約だったLaboの264群だけをDGXへ移す。
全768群・192 seed・67584行を保ち、変更後の実行先総数はDGX 624群・Labo 144群とする。
新しい14 batchは20群×13本と4群×1本で、いずれも最大20 workerとし、既存のDGX batchと同時実行しない。
元のDGX担当で未予約だった20群は既存経路のbatch 17に対応し、その予約追加は再割当て対象の変更ではない。

## テストと制約

plan検証と既存予約処理の23テストは2.05秒で成功した。
さらに割当てbindingと混合集約の受入テストを加え、既存予約処理を含む48テストが24.88秒で成功した。
群の重複・欠落・順序変更・不正な座標・実行先違い・worker数違い・plan hash変更・既存予約の変更を拒否する。
既存18 DGX batch・6 Labo batchと新規14 batchを合わせた全768群の一意性を、合成した終端記録で確認した。
infrastructure failureのある群も分母に含め、部分回収時には未回収群と未回収行数を明示する。
これらは割当てと群数の検査であり、実データの数値一致、実runtime、archiveの真正性、混合、精度、被覆を検証した結果ではない。
新経路の実行intent・runtime・元の数値関数とparity証拠の結び付け、および旧新artifactを読む最終providerの実装と検証が引き続き必要である。
既存の数値関数、既存の予約・回収記録、公開候補のsourceと配布物は変更していない。

## 保存物と再現

[保存ディレクトリ](data_portable_bar_2026-10-19/remaining_assignment_sources_v1/)には、source、テスト、RED/GREENログ、固定plan、基準snapshotとその予約証拠を計86ファイル保存した。
保存前後で各ファイルのSHA-256を照合した。
[manifest](data_portable_bar_2026-10-19/remaining_assignment_sources_v1/manifest.json)のSHA-256は `8e2d08fd155efe8ee71530c569e83321742cb6b17e30345b0e53502aac727b88` である。
manifestにはPython・OS・pytest・NumPyの版も記録した。
保存したsourceとテストを使って下記コマンドを再実行し、48 passed・26.30秒を確認した。
再実行ログは [remaining_assignment_archived_replay_v1.log](data_portable_bar_2026-10-19/remaining_assignment_archived_replay_v1.log) に保存した。
次のコマンドは保存した受入テストと合成入力による検査を再実行し、数値解析やSSH・qsubを起動しない。

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$assignmentArchive = 'docs/wp/data_portable_bar_2026-10-19/remaining_assignment_sources_v1'
& 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe' -B -m pytest "$assignmentArchive/test_portable_bar_assignment_binding_v1.py" "$assignmentArchive/test_portable_bar_reassignment_plan_v1.py" "$assignmentArchive/test_portable_bar_schedule_v1.py" -q
```

固定planの再生成コマンドは一度実行済みであり、既存planへ上書きする再実行は行わない。
原本の予約証拠との再照合には、元のsourceと予約ディレクトリの位置関係を用いる。
すべてのsampling、元環境trace監査、独立referenceとの照合は最終受入の前提として残る。
