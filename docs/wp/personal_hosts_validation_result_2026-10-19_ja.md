# 追加PCでの公開候補検証

DGX SparkとLabo PCに隔離したPython 3.11.17環境を作り、同じ公開候補wheelのoptional依存付きテストを実行した。
両環境とも2308 passed・5 skippedで、skipは外部RIMC環境を必要とする照合テストである。
実行前後に候補source 915ファイルを照合し、回収済みcompletionと各成果物のSHA256・サイズも再照合した。
集計は[再現スクリプト](data_personal_hosts_2026-10-19/summarize_validation_v1.py)と[結果JSON](data_personal_hosts_2026-10-19/validation_summary_v1.json)に保存した。
実行runner、再確認runner、runnerのテストと実行ログは[保存manifest](data_personal_hosts_2026-10-19/runner_sources_v1/manifest.json)に対応付けた。

| 環境 | worker数 | テスト処理の経過時間 | JUnitのmodule別累積時間の最大 |
| --- | ---: | ---: | ---: |
| DGX Spark / Linux aarch64 | 20 | 19.837秒 | 13.093秒 |
| Labo PC / Windows x86-64（初回） | 24 | 95.094秒 | 62.040秒 |
| Labo PC / Windows x86-64（再確認） | 16 | 97.063秒 | 49.481秒 |

Labo初回は機能テストを通過したが、module別累積時間が60秒を超えたため、並列数を16にして全suiteを再実行した。
初回結果を残した上で、再確認では全suite 5分以内・module別60秒以内を確認した。
DGX初回のsystem Python 3.12環境ではARM依存のビルド時にPython.hが不足し、テスト実行前にsetupが失敗した。
失敗ログを保持し、ヘッダー付きの独立したPython 3.11.17環境で成功した。
既存のPython環境や他プロジェクトを変更していない。

この時間はテストsuiteの実測であり、MCMCやBP-OSDの処理速度を測った値ではない。
OS・プロセス起動・並列数などが異なり、クラスタとの同条件比較もないため、クラスタより速いとは結論しない。
GPUは使用していない。
速度比較のための追加計算は行わず、GPU専用実装は将来課題とする。

## BP-OSDの環境差

既知のtile288 depolarizing p=0.05の単一検査状態を同じ設定で復号した。
Python、numpy、ldpc、pymatching、bposdのversionとパッケージsource hashは両PCで一致する。
同一instanceで10回・新instanceで4回の結果は、Laboではsector 0・論理失敗false、DGXではsector 94・論理失敗trueだった。
各環境内の検査ではrepeat・reverse・freshの不一致、syndrome違反、failure定義の不一致は0だった。
これは選んだ1状態の結果であり、一般的な決定性の証明でも、不一致率や論理誤り率への影響の推定でもない。
OS、CPU architecture、native binaryの効果は分離できていない。
probe JSONはローカルhashを記録したが、テスト成果物とは別回収であり、remote側とのhash再照合は未実施である。

この環境差を踏まえ、追加PCの数値結果を既存クラスタの固定cohortへ無条件に混ぜない。
追加PCでは現時点で公開候補の機能検証と上記probeを完了しており、新しい数値校正cohortは未実行である。
公開候補の固定treeと配布物は変更しておらず、本記録は候補固定後の追加証拠である。

## その後の固定予算比較

上記の機能検証後、両PCで同じiid状態を使う16条件・合計1048576対の比較を完了した。
この追加実験の事前仕様、生データ、全状態の一致確認、失敗判定不一致と区間は[別報告](paired_platform_mc_result_2026-10-19_ja.md)に記録した。
上記の「数値校正cohort未実行」は機能検証完了時点の状態であり、追加比較を既存クラスタのBAR校正完了として扱わない。
