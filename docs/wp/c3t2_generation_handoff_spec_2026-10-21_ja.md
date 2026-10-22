# C3T2生成への順次引継ぎ

## 小仕様

C3T2の固定済みanchor 0・sample 0・sample 1だけを対象とし、未使用の実preflightと先行C3T1の監査開始記録を照合する。
先行C3T1のfull監査とnative referenceの実PBS正常終端を確認してから、元のqsub wrapperでanchorを投入する。
anchorの正常終端後にsample 0・1を順次空き枠へ投入し、実receiptから同条件registryを作る。
共有lock・最大2要求ノード・一度限りの操作・曖昧な結果に対する停止を維持する。
受入済みC3T1 adapterの条件・先行source・preflight pinだけを変更し、導出元と導出結果のhashを保存する。

## 受入条件

実3 preflightと未使用executeの照合、native開始記録待ち、異なる条件・source・監査script・job・成果物pathの拒否を確認する。
元生成driverの観測・投入・registry作成の操作と、anchor正常終端を先行させる順序を維持する。
registry完成はsampling全件完了や科学的受理を意味しない。

## 実施結果

Windowsの11件が成功し、実3 preflight・未使用execute・C3T1監査開始記録を照合した。
source・導出記録・結果は `data_tile_validation_2026-10-17/c3t2_generation_handoff_acceptance_v1/` に保存した。
PID15328・session83145で待機を開始し、02:08のsession pollで生存を確認した。
本番先行ジョブの正常終端受理と新規qsubは未実施である。
