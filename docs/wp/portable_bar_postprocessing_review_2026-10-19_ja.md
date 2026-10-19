# 保存traceのBAR後処理を追加PCへ分担するための確認

現在のcluster sourceとlocal sourceをhashで照合し、`tile_low_noise_analysis.py`と`tile_low_noise_partitioned_analysis.py`がそれぞれ一致することを確認した。
SHA256は順に`4b2e4fa26ab54180dbdf4bc9cdfadd2cbe0781087037c84ac343def481080f7e`と`5ae94aaec62506d7b54d946530c3988f4b3ba5dbac844905915c574fdc7e0491`である。

`tile_low_noise_analysis.analyze_arrays`の数値処理は、保存済みweight・syndrome_weight・sector、anchorの失敗数・試行数、固定planを使う。
この関数は現在`build_problem`を呼ぶが、取得後に使うのはcode.nとlogical数であり、decoder.predictやProblem.is_faultyを呼んでいない。
したがって、数値処理からdecoder構築を明示的に分離すれば、sampling側のfailure集合を保ったまま別環境で後処理する設計が可能である。
これはsourceからの設計上の判断であり、異なる環境で同じBAR結果が得られることを実測したものではない。

現在の経路は`load_group`のProblem metadata照合、`validate_context`のruntime/source照合、partition runnerのPBS・native preflightを含む。
追加PCでこれらの検査を無効にしたり、clusterで実行したようなprovenanceを付けたりして既存cohortへ差し込まない。
保存済みsamplingの環境と、新しい後処理の環境を別々に記録できる入力・出力契約が必要になる。

転送量の参考として、C0T1の1 group `0-1-0-0-0`のtrace成果物をstatで確認した。
624ファイル・17399545 byteであり、anchor・全group・最終出力の総量ではない。
この観測ではtrace本体を追加PCへ転送せず、新しいBAR計算も行っていない。

## 実装する場合の受入条件

- 同じ保存状態からのweight・syndrome_weight・sectorとanchorをhash付きで受け取り、sampling時のdecoder設定・prior・native環境を保持する。
- 後処理へnとlogical数を明示し、decoder構築・再復号を不要にする。
- 後処理側のPython・numpy・scipy・source・seed・thread設定を別のprovenanceとして記録する。
- 元の独立seed、全group、window、burn-in、chain数、ladder、bootstrap seed、失敗・欠測の分母を維持する。
- 小規模のexact例と保存traceで、元経路との点推定・区間・診断・未定義処理の一致を許容誤差付きで確認する。
- runtimeが異なる処理を含む集約readerを明示的に追加し、元の固定cohortのruntime検査を黙って緩めない。
- 実行時間はsamplingと後処理を分け、異なるmachine構成を混ぜて既存の同精度到達時間を報告しない。

これはGPU実装を必要としないCPU後処理の分担案である。
現在のexperimental候補は変更せず、稼働中の265334・265338は既存の検証済み経路で継続する。
この分離機能の実装・実環境での一致確認・本cohortへの適用は未実施である。
