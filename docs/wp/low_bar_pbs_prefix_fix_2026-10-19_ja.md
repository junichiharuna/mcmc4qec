# PBS終了メッセージの接頭辞対応

元BAR job 265324はF・Exit_status -29・run_count 1・walltime 06:01:29で終了し、PBS commentはwalltime超過を示した。
実stderrの行は `=>> PBS: job killed: walltime 21678 exceeded limit 21600` だった。
v1のprepareは行頭を `PBS:` に限定していたため拒否し、qsubには進んでいない。
元の失敗receipt・元データ・v1配置・固定公開候補は保持する。

## 小仕様

終了メッセージの行頭に、接頭辞なし又は正確な `=>> ` のみを許可する。
終了状態・非zero終了・run_count・実script・資源・経過時間・上限一致・メッセージが1件であることの検査は維持する。
任意の接頭辞、引用行、複数メッセージ、異なる上限、上限未満の経過時間を拒否する。
修正版8 helperを別のv2配置へ保存し、旧配置のbytesと失敗記録を変更しない。
変更点は終了メッセージの構文だけで、計画・seed・失敗集合・BAR計算は変更しない。
v2のprepare・preflight・executeはそれぞれ別receiptへ記録し、待機中を含む最大2ノードとqsub一回の条件を維持する。
実行後のcompletion・report経路もv2のhelper hashと配置へ明示的に結び付ける。

## 受入条件

v1の既存inventoryテストを修正版にも適用する。
実stderr書式と接頭辞なしの両方を受理し、上記の不正なメッセージを拒否する追加テストを実行する。
修正版だけが異なることを8 helperの比較で確認し、Linux importと実元jobへのprepareで確認する。
テスト・配置・実投入・回収の結果は、実施後に記録する。
