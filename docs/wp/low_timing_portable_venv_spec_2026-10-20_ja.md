# C0T2計時readerの実venv wrapper接続

完成したC0T2最終reportのconfigは、`portable_mixed_venv_qsub_v1.py` と元venv入口を明示する。
既存計時readerの `portable_mixed` routeは旧 `portable_mixed_final_collection_v1` を参照するため、実configのwrapperを扱う回収moduleと一致していない。
計時readerは新しい隔離配置に複製し、snapshot依存だけを既に実report回収に使った `portable_mixed_venv_final_collection_v1` へ変更する。
他のreader本文、全768群・67,584行の照合、元trace監査、WSS reference、実PBS job検査と科学的な選択規則は維持する。
ASTで変更箇所を限定し、既存portable routeの受入を新配置でも実行する。
実config・元156 source・metadata・Python bindingは保持し、新しい子環境ではmoduleのimport元とnative binaryを明示してbootstrapする。
新readerの試験成功、実子環境のbootstrap、実metadata候補作成、全raw読取・独立計時の実行は別々に記録する。

## 実施結果

変更箇所をASTで確認し、既存portable routeと追加bindingの受入はWindows16件・Linux16件で成功した。
初回Linux配置は2件成功・14件失敗となり、原因は試験に必要なplatform fixture 2ファイルの配置漏れだった。
その記録を保持して別配置へfixtureを追加し、[受入sourceとログ](data_tile_validation_2026-10-17/low_timing_portable_venv_acceptance_v2/manifest.json)を保存した。

元configの156 source・136 metadataと、venv入口・実体・prefix・Python/package versionを照合した。
実子環境では108 sourceと137 native binaryのbyte・import元を確認し、元科学moduleのhashがconfigと一致した。
環境SHA-256は `f7619406473f5df8565f214cb3385b492e00ee535575fe678ed580b5d112e030` である。
157入力のmetadata候補を作成し、最終job265366の実qstatとreport・script・投入・終端記録を再照合した。
実walltimeは2035秒、実peak memoryは1,352,040,448 byteであり、要求32 GB・4時間や独立sampling計時とは区別する。
候補と実行記録は[実環境・metadata manifest](data_tile_validation_2026-10-17/low_timing_portable_actual_v1/manifest.json)に保存した。

既存5候補と共通のWSS reference root・監査summaryを参照することを確認し、[部分inventory v2](data_tile_validation_2026-10-17/low_timing_partial_input_inventory_20261020_v2.json)を6候補・6未完了へ更新した。
元最終job6件の実walltime合計は14,076秒であり、再hash・copy・残る6条件・queue待ちを含まない。
この合計は全体ETAや、同精度に達するまでの計算時間ではない。
全12条件のparent descriptor・資源決定、実raw reader、選択と独立計時は未実施である。
新しい準備script、初回失敗ログ、実子プロセスのsource・標準出力・標準エラー・bootstrap受入と候補を[55ファイルのmanifest](data_tile_validation_2026-10-17/low_timing_portable_progress_20261020_v1/manifest.json)に保存した。
bootstrapで読んだ元科学moduleのsource mapは65ファイルであり、元config全体の156 sourceや、子環境全体の108 sourceとは別の範囲である。
