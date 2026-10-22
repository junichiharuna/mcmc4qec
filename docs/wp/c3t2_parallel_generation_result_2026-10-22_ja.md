# C3T2先行生成と後続処理の接続結果

## 変更と現在の状態

[小仕様](c3t2_parallel_generation_spec_2026-10-22_ja.md)に従い、C3T2のanchorとsampling前半を空きノードで先行できるdriverへ切り替えた。
元の全payload・task・seed・decoder・noise・trace長・ladder・誤差法・要求資源は同一で、sampling後半は引き続きC3T1の全trace監査とnative referenceの完了を待つ。
元のqsub helper、共有投入lock、最大2node検査、anchor正常終端、全3receipt発行後のregistry、科学的validatorを維持する。
これは投入順序とlocal記録先の変更であり、数値結果や混合・被覆・速度優位の認定ではない。

13:46〜13:47 JSTに新しい6controllerの実PID・command・intent・全固定hashを照合した。
C1T2最終解析265435とC3T1 sampling265438が各1nodeで稼働し、要求ノード合計は2だった。
C3T2は空き枠待ちで、C3T2のqsub receiptはまだ存在しない。
最初の投入後には、実PBS job ID・script・資源・同時要求ノード数の独立照合が必要である。

| 処理 | 実PID | 新しい記録先（data_tile_validation_2026-10-17配下） |
| --- | ---: | --- |
| generator | 42324 | c3t2_parallel_generation_handoff_v1 |
| collector・trace監査 | 39596 | c3t2_parallel_collection8h_audit_handoff_v1 |
| native/PC launcher | 6908 | c3t2_parallel_downstream_launch_v1 |
| 最終解析準備 | 49352 | parallel8h_final_c3t2_preparation_handoff_v1 |
| 最終解析実行 | 12204 | parallel8h_final_c3t2_execution_handoff_v1 |
| 独立算術確認・計時候補 | 41212 | parallel8h_final_c3t2_downstream_handoff_v1 |

native reference、PC serial、分配先、remote最終解析root、最終回収先、独立算術確認と計時候補の出力先は従来のものを使用する。
新しい後続処理は、新しい前段intentとsource hashを必須とし、依存先の未完了では待機し、失敗を正常完了として扱わない。

## 受入と切替

固定payloadの一致、投入順序、失敗時の停止、既存操作の拒否、最大2node境界、回収・監査・準備・結果の改変拒否、子processの二重起動拒否、隔離した全後続接続を113テストで確認した。
元の完全なevidence validatorを新しい接続でも実行し、実クラスタ側の科学的処理は今回のテストでは再実行していない。
受入source・回帰テスト導出・実行logは [c3t2_parallel_acceptance_v1](data_tile_validation_2026-10-17/c3t2_parallel_acceptance_v1/manifest.json) に保存した。
manifest SHA256は `63ffd7ed8f3e91b3f7988768ff4bce9c82d13bd8add9cc0b953ec4d0ae8bd9ab` である。

最初の切替検査はlauncher24964の子process36992を検出し、停止操作の前に拒否した。
実状態でこの子は同時生成された `conhost.exe` と確認し、正確なPID・親PID・実行ファイル・command・生成時刻の関係を限定する別版transition_v2を用意した。
7追加テストで、この1件だけの許可と、別PID・別command・別親・別実行ファイル・不一致生成時刻・追加の子processの拒否を確認した。
元transitionと受入記録は変更していない。
追加受入は [c3t2_parallel_transition_acceptance_v2](data_tile_validation_2026-10-17/c3t2_parallel_transition_acceptance_v2/manifest.json)、manifest SHA256は `ce8d76f42e0253ccd8d491e250beb003d3c7f7924194e504073d48d9e1826b89` である。

切替では未着手の旧6waiterだけを停止し、旧processとconsole補助processの不在を確認した。
停止前後のjournal censusとsource hashを保存し、旧journal、原source、過去の失敗記録を保持した。
稼働中クラスタjob、PC解析、C3T1のcontrollerは停止していない。
[停止証跡](data_tile_validation_2026-10-17/c3t2_parallel_generation_transition_v1/stopped.json)のSHA256は `22fbb9421bef433c5a021be1067f8b7f490ea1b625bad068ecddb0057d7dea70` である。

新controllerは依存順に一度だけ起動し、各実handleとintentの一致を確認してから次のcontrollerを起動した。
[起動記録](data_tile_validation_2026-10-17/c3t2_parallel_launch_v1/started-all.json)と[独立live観測](data_tile_validation_2026-10-17/c3t2_parallel_live_observation_20261022_v1.json)を保存した。
独立live観測のSHA256は `897c9a1d96af704e738975a9caa802957ff2f279ee32088338fbe62598468f59` である。
起動scriptは起動記録directoryに、観測scriptは [observe_c3t2_parallel_live_v1.py](data_tile_validation_2026-10-17/observe_c3t2_parallel_live_v1.py) に保存した。
これらは一度限りの実行を記録するもので、進行中のjournalを消して再実行してはならない。

正式完了は低ノイズ8/12条件のままであり、先行生成による全体所要時間の短縮量と最初のqsub実行は未確認である。

## 全12条件の後続集計との接続確認

14:07 JSTに、旧版と新版のcandidate bindingが全項目で一致し、remote final root・audit root・回収先が同じであることを実sourceから確認した。
変更したlocal preparation/execution journalは、C3T2の新しいadapterが読み取る。
全12条件のinventoryは従来と同じcandidate受入先を読み、assemblyはcandidate entryからfinal report・submissionとreaderの入力rootを導出する。
実inventoryではmetadata_ready=8で、C1T2・C3T0・C3T1・C3T2がpendingとなり、部分集合は後続へ渡されなかった。
この確認はsourceとmetadata接続の確認であり、未作成のC3T2実candidateや全12条件の親ジョブを受理したものではない。
[接続調査記録](data_tile_validation_2026-10-17/c3t2_parallel_all12_source_review_20261022_v1.json)のSHA256は `d48057a96d549d5ef61c1995a8f779c966ba5a5530ab56604b0797a1f5aa6bca` である。
