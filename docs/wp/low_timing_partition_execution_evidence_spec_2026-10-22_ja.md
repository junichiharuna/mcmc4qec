# 分割workerのPBS証跡：小仕様

[読み込みと結合の中核](low_timing_partition_values_spec_2026-10-22_ja.md)に、worker一件の保存済み実行証跡を照合する検証関数を追加する。
新しい実行契約を小さい人工証跡で検証する段階であり、既存ジョブの証跡を読み替えたり、新しいジョブを投入したりしない。

呼出側が外部から固定したprepared、全12条件manifest、全12条件資源計画、実行環境の各pathとSHA256を必須にする。
prepared自身が指定した別の全条件manifestや環境へのすり替えを認めない。
担当worker index、全体の重複のない固定順割当、計画器の割当と要求資源、manifestのparent設定を照合する。
scriptは固定prepared pinから生成される全内容と一致させ、qsub command・script hash・要求資源・prepared digestを投入intentと台帳で結合する。
台帳には一つのPBS job IDだけを認め、開始・終了前のR状態と終了後のF状態を同じID・run_count 1・host・script・要求資源へ結合する。
F状態は整数のexit 0を要求し、未終了、再実行、異なるhost・資源・scriptを拒否する。

実行開始と完了の記録は固定prepared・全体manifest・環境・worker index・実argvに一致させ、完了記録はworker値ファイルのhashを固定する。
値ファイルのindex、全体manifest digest、担当、source closure、engine source、PBS ID、未認定flagを照合する。
環境のPython executable、source、resolved source、native bindingをhash照合するが、新しいnative probeを実行したと主張しない。
workerが記録した入力hashとresolved pathも再照合し、検証終了時にすべての入力を再確認する。
検証関数はファイルを書かず、ネットワークへ接続せず、qsubを呼ばない。

受入テストでは成功証跡の結合と、不正な外部pin、別manifest、別割当、script変更、曖昧な台帳、未終了・非ゼロ終了・run_count変更・資源変更・host変更、値hash不一致、環境変更、入力変更の拒否を確認する。
人工証跡の成功は実schedulerを照会した証拠ではなく、実データの受入件数を増やさない。
実行runner、投入lockと最大2node制御、native環境の事前検査、結合ジョブ、後続censusへの接続は引き続き必要である。
この検証だけで `production_selection_validated` をtrueへ変更しない。
