# 数値診断の統合検証ログ

基準は `7f8d7ba`、検証対象は今回の未コミットsourceである。
`summary.json` にsource fingerprint、wheel hash、環境と検証範囲を記録する。
`source-tests.log` は全469テスト、`core-tests.log` はinstalled core wheelの関連103テスト、`verify-core.log` はwheel/source照合とcore実行例・文書例の結果である。
source全suiteの1 warningはWindows notebook実行時の既存zmq Proactor fallbackである。
core wheel環境は既存venvを再利用し、今回buildしたwheelを依存更新なしで入れ直した。
今回optional wheel全suiteの再実行、remote CI、追加の実符号被覆sweep、速度測定は未実施である。
source全suiteではoptional依存を使うテストと研究照合も実行し、skipはなかった。
