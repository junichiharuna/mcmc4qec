# 巨大metadataの下流実行境界監査

2026年10月25日の現行tail v3について、小さいsourceと固定environment metadataを読み取り監査した。
巨大result・selection・rawデータは読み込まず、ローカルテスト・数値再計算は行っていない。
この文書は修正の受入結果ではない。

## 結論

mergeの`accept_terminal`だけをPBSへ移しても、下流の全6roleに非PBS processで重いmetadataを再検証する経路が残る。
tailのtransportは`ssh`を同じhostのsubprocessへ変換するだけで、PBS allocationを付与しない。
元の科学的検査を省略せず、有限の重処理actionを別PBS jobへ移す必要がある。

| role | 現行の重い経路 |
|---|---|
| census preparation | `remote.run → bridge.prepare → bridge.verify`がacceptedの入力map、merge-result、promoteされたselectionを読み、比較・hash照合を行う。 |
| census execution | `remote.run`のgate・observe・sealを含む各actionが`bridge.read_plan → inspect_inputs`でselection・scientific-bundleを読み直す。 |
| independent preparation | `execution.inputs`、各capacityの`prepare/read_plan`がselection・bundleと依存証拠を再検証する。 |
| independent execution | `checked → execution.read_plan → envelope_value → inputs`がsubmit・observe・finishでselection・bundleを再検証する。 |
| report preparation | `report.selector_evidence → partition_check → bridge.verify`に加え、`report.prepare → inputs`でも同じ大きな入力を再検証する。 |
| report execution | `report_job.validate`がprepare・submit・observe・seal等から呼ばれ、`report.inputs → partition_check → bridge.verify`へ入る。 |

主な確認箇所は`output/low_timing_partition_census_bridge_v1/bridge.py`の`verify/prepare`、各tail roleの`remote.py/preparation.py/report_job.py`、`cluster_scripts/tile_low_noise_timing_census.py`の`inspect_inputs/read_plan`、`tile_low_noise_timing_execution.py`の`inputs/read_plan`である。
現行remoteのcensusとreport overlayの該当関数も直接読み、ローカルの公開用識別子置換版だけから結論していない。
現行report overlayの`partition_check`は子processの制限を120秒とし、`proof.files`全mapをstdoutのJSONで返して親が再parseするため、PBSへ移すだけでも時間制限と同時保持量の検討が残る。
selectionとscientific-bundleはまだ生成前であり、最終サイズや必要最大RSSは未計測である。
別担当のstat棚卸しでは、現行workerのmanifestは1,240,950〜1,241,842 bytes、resource planは22,647〜22,867 bytes、environmentは79,840 bytesであり、merge準備のmetadataを巨大valuesと同じ規模とは扱わない。

## 最小のversioned隔離方針

既存sourceと稼働workerを変更せず、acceptanceおよび3つのpreparationを有限PBS jobとして実行し、元の検証と出力形式を保持する。
実行roleのsubmit・finish・seal等についても、深い検証を必要とするactionを同じ境界に含める。
controllerは上限付きの小receiptと実PBS状態を扱い、巨大artifactはpath・既存hash・stat情報で引き渡す。
controllerで大きなファイルのhashを再計算して小receiptを検証した扱いにはしない。
周期的な観測を軽量化する場合は、実qstatと小さい実行識別情報だけを読む新しい観測APIを仕様化し、深い検証の実施境界と省略していない検査を明示する。
全roleを長時間の親PBS jobで単純に包む案では、内側の96CPU jobと親の予約資源との競合や自己controller検出による待ち続けが起こり得るため、既存gateとの整合を別途検証する。
PBS要求メモリ・walltimeは資源予算であり、実測の必要量や終了時刻の予測ではない。

## 必要な受入

- controllerのprepare・observe・adopt経路に巨大artifactのopen/read/hashを拒否するtrapを置き、小receiptとstatだけで進むことを確認する。
- PBS workerは実allocationと固定source・request・commandを確認してから元の重処理を呼び、原本の検査・出力・科学的値を維持する。
- 元実装とwrapperの出力を有限fixtureで比較し、selection24行、timing48行、各192分母、未取得・失敗理由を保持する。
- claim後の異常終了、timeout、曖昧なqsub応答、receipt欠落・改変、F/0とcompletion不一致では再実行・再投入を自動で行わない。
- 親のallocation解放後に後続jobを投入し、待機予約も含め最大2物理ノードのCPU・メモリ上限を共有gateで守る。
- report内の120秒制限と全mapのprocess間転送について、有限fixtureに加え本番statからの資源予算とfailure時の証拠保持を確認する。

小さい受入の成功は、本番の巨大入力全体の完了や科学的結論を保証しない。

## merge acceptance wrapperの静的レビュー

新しい`output/merge_terminal_acceptance_pbs_v1/acceptance.py`の初稿と修正版を読み、元のremote `accept_terminal`も照合した。
初回のcanonical terminal・selection・accepted生成を許可し、既存出力や部分出力を変更せず、排他的claimを`xb`作成する構成である。
元mergeのjob IDとacceptance job IDを分離し、source・script・submission intent・ledger・qsub response・実PBS resourceを照合する。
レビューで依頼した上限付き`read(MAX_SMALL+1)`と、重処理import前の実process hostname・exec_host・vnode照合は修正版へ反映された。
controllerは巨大resultとselectionを読み込まず、statの不変性を確認する。
4MiB以下に制限されたaccepted receiptはcontrollerでhashと値を再確認し、この小receipt検証を巨大artifactの独立hash検証とは称さない。
不確実な投入応答、claim後の失敗、部分出力を自動で再実行しない。
この時点の静的レビューでは残るblocking指摘はないが、専用fixture・実CLI/native受入・本番巨大入力の完了は未確認である。
