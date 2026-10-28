# 後続ジョブの実起動コンテキスト検証

通常の helper 経由の bootstrap だけでは、Python の実行スクリプトのディレクトリが import 探索順の先頭になる影響を再現できない。
後続の census・独立計時・報告の実 entrypoint と、そのディレクトリに存在するモジュールをクラスタで調べた。
census のディレクトリには意図した census module だけがあり、独立計時のディレクトリには意図した runner と submitter だけがあった。
報告 helper のディレクトリには科学 module がなく、報告 overlay には報告 module だけがあった。
したがって、これらの実ディレクトリに新しい isolated module を隠す同名 module は見つからなかった。

qsub 265552 で実際の3スクリプトを `python -B -i SCRIPT --help` として起動し、同じプロセス内で実スクリプトの場所、`sys.path[0]`、元の厳密な bootstrap と全 import origin を検証した。
報告では実 helper の `bootstrap` 関数を使用し、報告専用の `import_prepend` も適用した。
3 entrypoint はすべて成功し、F・終了値0、経過11秒を確認した。
別の負例では、同じ isolated source を偽の先頭ディレクトリへ置き、元の origin 検査が `actual import origin differs` で拒否することも確認した。
既存 entrypoint の移動や改変、検査の緩和はしていない。
生の hash を保持して識別子を除去した証跡は [parallel_tail_startup_v1](data_tile_validation_2026-10-17/parallel_tail_startup_v1/accepted.json) に保存した。
ログの `SystemExit: 0` と対話プロンプトは `--help` 後の検査方法によるもので、受入成否は各プロセスの終了値と一意な成功記録で判定した。

検証対象の実設定は `$HOME/workspace/mcmc4qec/20261025-low-parallel-tail-v2/tail-config-v3.json` であり、SHA-256 は `1ef117530cafc2e0e17c517245e429b1244c92d0f969b7feac1c4a2fe2ed76ea` である。
この設定は v3 の merge・handoff・journal と新しい後続出力先を使い、以前の設定と環境証跡を保存している。
今回の検証は起動と import binding の範囲であり、科学的な入力を渡した census・独立計時・最終報告の完走はまだ確認していない。
