# 主混合診断 full 終端回収

固定 preparation SHA `011aef0ef043c6f36d94b82e14079c31c12e64b4502c8d18132a9b14a88a350d` の4 caseだけを対象とする。
親の実job ID、親保存receiptのbyte SHA、caseを必須とし、既定は計画表示だけ、明示 `--collect` のときだけread-only SSH/scpを行う。
qsub、再解析、原本変更、未投入rootの完了認定は行わない。
PBS F/exit0・script・run_count・host・要求資源、準備済みmanifest/script/dry-run、source/package/Pythonと既存read_plan/bindingを照合する。
cluster module import前にstdlibだけで全source、coreの相対path+NUL+bytesによるaggregate SHA、Pythonの実解決pathとSHAを固定dry-runの値へ照合する。
nativeは固定runtimeと既存監査・配置証拠との結合であり、native probeは再実行しない。
execution summaryとinventory summary、全観測量cohort、各192分母、sectorのchain分母、失敗・欠損・undefined件数を照合する。
inventory_complete=falseを成功診断に変更せずそのまま保持する。
大きいrows.jsonlは全byte hashと転送一致を検証し、平均・IAT・ACF・bootstrap・decoderは再計算しない。
全rung/観測量の予定集合は既存expected_diagnosticsから得る。
固定名の正式metadata・summary・rows・stdout/stderrを新規local rootへ回収し、remote前後とlocalの全hash/sizeを一致させる。
PBS終端stable fieldsは回収前後に再確認し、resources_usedのような観測値は記録するが秘密環境は保存しない。
未終端・異常終了・binding不一致では成功verificationを作らず、localの実行証拠を残して停止する。
親が個別job IDを通知するまで本番回収は実施しない。
observer SSHは全output hashの複数passを含むため600秒を明示上限とする。
capacityは1groupであり、case0..3のrows.jsonl実bytesは1,189,188・675,549・1,551,436・1,091,113である。
同じbytes/groupという未検証仮定の768倍ではfullは約0.913・0.519・1.192・0.838 GBとなる。
正式fullの実bytesは回収時のfile censusへ別途保存する。
これは保存値の文字列表現やI/O速度の変動を保証せず、600秒は実測完了時間の保証ではない。
受入は小さいsynthetic reportの全cohort/sector/失敗分母とPBS gate、既存4case準備hashを確認し、remoteやfullデータを使わない。
