# 分割結果の結合jobと正常終了の受理

全12条件と全workerを受理する既存combine処理を、専用のPBS jobで実行する。
preparedには結合request・runner・既存runtime helper・既存証跡reader・出力先・PBS script・資源上限を固定する。
資源は1 CPU・32 GB・1 node・24時間を上限として明示し、これは実測に基づく終了予測ではなく初回の実行予算とする。
24時間以内の完了を保証せず、上限超過や異常終了は未完了として保持する。
全体の最大2要求nodeは既存の共有lock付きqsub投入経路で維持する。

開始時に実PBSのjob ID・script・要求資源・host・run_count・Pythonとnative環境を検証する。
qsub台帳の公開待ちは既存の30秒上限付きhelperを使い、不一致や観測失敗から再投入を判断しない。
元のcombineを変更せず、workerの終端証跡、raw入力、設定選択規則を検証する。
実行source、prepared、request、環境、結果hash、開始時と終了前のPBS観測を保存する。
結合結果内のproduction flagは、job実行中にはfalseのまま保持する。

正常終了の受理は、独立に指定したprepared pinと、単一job IDのqsub応答・台帳・script・実行記録・完了記録・PBS F/exit 0を照合する。
受理時に大規模raw入力を再走査せず、combine job内で検証済みの結果byteと固定sourceの同一性を確認する。
その受理は過去の検証済みsnapshotを対象とし、rawファイルが将来も不変であるとの保証にはしない。
正式選択には結合jobとworkerの出典を保持し、既存の計時planによる全24行の検証を再度要求する。
実行途中の結果、非終端、異常終了、不一致、欠損、qsub応答不明は正式選択へ昇格させない。
独立計時の実施や、精度・名目95%被覆の保証はこの受理の対象外である。
