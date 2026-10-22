# C0T2最終ジョブから回収への引継ぎ

既存の投入監視が作るsubmitted.jsonを、固定config・事前検査結果・実job IDと照合する。
この引継ぎ自身はqsubを呼ばず、新規の数値計算も開始しない。
対象jobの実qstatで固定script、1 CPU・32 GB・4時間、F・exit 0・run_count 1を確認するまで待つ。
観測timeoutは同じjobを再観測し、計算の再投入やcompleteの再試行へ置き換えない。

正常終端後、固定済みvenv wrapperのcompleteを一度だけ実行し、返されたjob ID・report hashと実terminal.jsonのhashを保持する。
そのterminal hashを既存のvenv対応collectorへ渡し、転送前後とlocalの13成果物を照合する。
変更操作は排他的intentを先に書き、曖昧な応答や失敗では証跡を残して停止する。
本番reportの回収をもって名目被覆や推奨設定が確定したとは扱わず、科学的解釈と日本語報告への反映は別途行う。

2026-10-20のWindows受入は13 passed・0.84秒だった。
投入記録とpreflightの一致、異なるjob・terminal・report・PBS失敗・再実行の拒否、complete失敗時に回収へ進まないことをfixtureで確認した。
観測と排他的intentには同日の復旧監査引継ぎで30件の受入を通した固定sourceを利用する。
転送・metadata検査は既存のvenv対応collectorを変更せず利用し、これらの新しい試験を本番report回収の証拠とは扱わない。
20:24 JST前後に引継ぎを起動し、既存のC0T2投入監視のsubmitted.jsonを待っている。
起動直前の実クラスタdirectoryにはconfig.jsonとreport.shだけがあり、実qstatは265361と265362の2ジョブがRだった。
この起動によるqsub・complete・report回収はまだ行っていない。
実行入口は `python -B output/c0t2_final_handoff_v1/driver.py` だが、この起動は使用済みであり再実行しない。
記録先は `data_portable_bar_2026-10-19/mixed-c0t2-final-completion-handoff-v1`、成功時の回収先は同階層の `mixed-c0t2-final-collected-v1` とする。
両引継ぎのsource・受入結果・起動証跡・実機観測は [49ファイルのmanifest](data_tile_validation_2026-10-17/automatic_handoffs_progress_20261020_v1/manifest.json) に保存し、SHA-256は `52eb9cd2617bd702374ea44ac554dbb649b7df03e71473362f9125c38cf5d7ab` である。
