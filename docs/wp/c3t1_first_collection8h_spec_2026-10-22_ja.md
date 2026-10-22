# C3T1の初回回収を8時間枠にする仕様

C3T0の初回回収が4時間で時間切れになったため、未投入のC3T1回収は8時間・1 CPU・32 GBに変更する。
8時間は資源上限であり、完了時刻の予測ではない。
対象はcase 3・target 1だけとし、既存の4時間版、C3T0復旧版、実行中のsamplingには変更を加えない。
新directoryは `sampling-collection-budget8h-v1` と `sampling-collection-submission-budget8h-v1` とする。
元の回収directory、retry directory、4時間版directoryが存在する場合は初回実行として受理しない。
元のseed、全192 seed、768群、失敗・未定義を含む全task検証、科学計算、qsub共通lockと最大2ノード検査を維持する。

受入では旧版が8時間契約を満たさないこと、新版の資源・対象制限・旧実行拒否・一回限りqsub・失敗taskを含む完全なindex検証を確認する。
監査authorityは新directoryと実PBSの8時間資源、F・exit 0・run_count 1を要求し、4時間のterminalは拒否する。
監査の数値処理、capacityからfullへの資源推定、共有lockとノード上限は変更しない。
WindowsとクラスタのPythonでfixture試験を実行し、実configのbootstrapと未実行状態を確認してから後続実行係を接続する。
この受入は実trace監査や科学的な条件完了を意味しない。

後続実行係は新しいC3T1 generationとC3T0復旧監査の固定source・intentを結ぶ。
旧C3T1監査係が `Preceding audit failed` で終了し、collector・capacity・fullの投入を行っていないことと旧PIDの消失を確認する。
新係は3件のgenerator receiptが揃うまで待ち、実sampling成功終端・C3T0復旧full監査成功・空きノードを順に確認してからqsubする。
元の一回限りの操作、config・source固定、実PBS終端照合、capacityからfullへの検証順を維持する。
