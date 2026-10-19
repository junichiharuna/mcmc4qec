# 最終比較の失敗件数辞書の受理仕様

C0T0最終比較265333はF・exit 0・run_count 1で完了したが、親側completion v2は`report outcome census differs`で受理を拒否した。
実reportの`assessment.metrics.failures`は失敗理由から件数への辞書であり、既存の`tile_weight_reference_comparison.assess_bounds`が保持する正規の形式である。
旧completionはこの項目を整数と誤認していた。
remoteに`parent-completion.json`と`terminal.json`は作成されていないことを読み取りで確認した。

計算結果、既存helper、失敗した受理記録は変更せず、新しいcompletion helperとtransportで受理する。
整数の件数項目は従来どおり0以上192以下の厳密な整数とする。
`failures`は空辞書を許容し、各keyは空でない文字列、各valueは1以上192以下の厳密な整数とする。
失敗理由別件数の合計も192以下とし、bool・負数・小数・整数への置換・不正key・合計超過を拒否する。
元producerの実`assess_bounds`出力をテストへ渡し、正常結果と失敗を含む結果の両方を受理する。
残る終端、入力hash、分母、source、監査scopeの確認は維持する。
数値結果の再計算、計算ジョブの再投入、raw結果の書き換えは行わない。
