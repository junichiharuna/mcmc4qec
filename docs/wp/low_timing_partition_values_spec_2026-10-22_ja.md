# 分割した低ノイズ設定選択：読み込みと結合の小仕様

[資源計画器](low_timing_partition_plan_spec_2026-10-22_ja.md)に続き、既存selectorの `load_complete` を条件単位で呼び、全24行へ結合する中核処理を追加する。
稼働中sourceや公開パッケージのAPIは変更しない。
この段階では新しいPBS envelopeと後続censusを接続せず、実データでの実行や本番選択の受理を主張しない。

## 固定入力とworker

全12条件を固定順序で含むmanifestと、条件ごとのworker割当を要求する。
割当は資源計画器の連続区間に対応し、全12条件をちょうど一度含む。
manifestは既存selector source closure、各workerのscript pathと要求資源、子readerのparent設定を固定する。
全12条件で共通reference root・audit root・audit summary pinを一致させる。
workerは自分の条件だけに既存 `load_complete` を呼び、設定選択・seed・分母・reference・診断flagの扱いを変更しない。
PBS_JOBIDと既定single-thread環境を確認し、子readerのparent設定が割当先に対応することを確認する。
開始前・終了後のsource closureとproofによる入力不変性を確認し、異常を選択不能へ変換しない。
worker結果には全manifestのdigest、担当条件、PBS_JOBID、選択値、binding、入力hashとresolved pathを保持する。

## 結合

全worker結果を必要とし、worker重複・不足・manifest/source不一致を拒否する。
各条件にepsilon index 0と1の二行が対応し、各行の固定192 replicateと全352設定を保持することを確認する。
未取得・不適格・診断未定義を含む選択値とbindingをそのまま保持し、結果を見た再選択はしない。
workerが記録した全入力とsourceのhash・resolved pathを結合前に再照合し、結合終了時にもproofを確定する。
入力不変性の再確認は省略せず、実行する場合のhash費用は後続の結合ジョブ資源見積りに含める。
全24行と12 bindingを固定順序で返すが、PBS台帳・正常終了・native環境を認定するenvelopeが未接続なので `production_selection_validated=False` とする。
既存の正式selector結果と異なるpurposeを使い、後続処理がこの中間結果を正式結果として誤受理しないようにする。

## 受入

小さな固定metadataと既存の実 `choose` 関数から全12条件の選択値を作り、単一selector経路と分割・結合経路で24行とbindingの全値一致を確認する。
raw readerはテスト用doubleを使い、この確認を実traceの再検証と扱わない。
referenceなし・reference幅不適格・精度未達・選択成功を含め、診断情報を保持する。
担当外条件を読まないこと、読込異常で部分成功を返さないこと、欠落・重複・分母違い・設定数違い・source変更・入力変更・resolved path変更を拒否することを確認する。
PBS環境なし、workerのparent設定違い、結果を返す直前の入力変更を拒否する。
本番envelope・qsub投入・実metadata全12条件の実行・後続census接続は別の未完了項目として残す。
