# 分割workerの実行runner：小仕様

固定prepared pinを受け取る `run-worker` と、終了後のPBS記録を保存する `capture-terminal` を追加する。
このrunnerはqsubを呼ばず、実投入は別の共有lockと最大2node制御を持つcontrollerから行う。
既存の稼働sourceとcontrollerは変更しない。

科学moduleをimportする前にprepared、runner自身、証跡検証module、全体manifest、資源計画、実行環境のbytesを照合する。
PBS_JOBIDとsingle-thread環境、PythonとPYTHONPATH、投入intent・台帳・script、実PBSのR状態と割当hostを検査する。
元の環境検証関数を使ってsource closure・native binding・runtimeを確認してから既存selectorと分割値処理moduleを読み込む。
担当条件の最終report・terminal・collection・copy費用を保存証跡から読み、既定費用式の再計算と要求資源の一致を確認する。
資源不足を係数緩和や条件削減で回避しない。

未使用の出力先だけを認め、実行開始と実PBS開始記録を保存してから既存の分割worker関数を呼ぶ。
値処理・入力不変性・実PBS終了直前のR状態を確認した後で値ファイルと完了記録を保存する。
読込異常や環境変更で完了記録を作らず、例外記録を保持して自動再実行しない。
既存の出力・開始記録・例外記録がある場合は再実行を拒否する。

`capture-terminal` は同じPBS jobの実F状態を照会して保存し、正常終了の場合に限り外部pin付きdescriptorを作る。
この段階では巨大なtrace payloadを再hashせず、descriptorを受理済みと扱わない。
全入力の再照合とworker証跡の受理は、別の資源計画済み結合ジョブ内で行う。
実行枠外で重い再検証を始める経路は設けない。

受入テストでは、保存証跡のfixtureと明示したnative bootstrap・reader doubleを使い、開始から完了、実行中poll、終了記録、後段の証跡検証までを接続する。
PBS未割当・台帳不一致・入力破損・資源不足・reader異常・実行途中のPBS状態変化・出力再利用を拒否し、失敗を完了扱いにしない。
費用検証は既存の費用規則との一致と、実測値・pin・collection scopeの不一致を確認する。
これらはrunner制御の受入であり、実cluster配置・qsub投入・native環境での実trace再読込・全条件結合・後続census接続は未実施として残す。
