# 全設定での後処理移植照合の開始

2026-10-19 23:35 JSTまでに、事前指定したC0T0 group `(0,0,0,0,0)` の全設定を両PCで照合する処理を開始した。
[最終結合の小仕様](portable_bar_final_join_spec_2026-10-19_ja.md)に記録した追加受入であり、C0T2の科学cohortへ加えない。
全設定の照合結果はまだ未取得である。

既存のparity archiveの全入力と保存済みクラスタ結果を使い、元の4/16 chain、burn-in 600/6000、保存600/6000/60000、coarse/fine ladder、block 32/128/1024とcross-chain、bootstrap 1000を保持した。
比較元の88行・診断1536件・ACF1536配列の集合を実データで確認した。
元の配列解析sourceとAST変換、loader、decoder factoryを禁止する処理は短いwindowの検証で使ったものと同一である。
今回のdriverは元planを短いwindowへ縮めず、そのまま全設定を実行する。
浮動小数点の許容差はrtol=1e-10・atol=1e-12を維持し、flag・離散値・未定義位置の変更は拒否する。

小仕様の後に受入テストを作り、実装前のmodule未存在による失敗を保存した。
実装後は長いwindowの欠落、設定の重複、別group、誤差法の変更、ACF欠落、flag・未定義位置・数値の変更を含む21テストが2.91秒で通った。
これは実cluster結果との全設定一致を示すものではない。

両PCで各1プロセス、BLAS等のthread数1で実行する。
既存のDGX 20 worker・Labo 24 workerに加えて行う検証であり、同時実行時の速度を独立したbenchmarkとして扱わない。
remote PIDはDGX 581605、Labo 15784であり、実processとCPU使用を照会した。
source hash・入力archive hash・実行環境のhostname/Python/platformが準備した記録と一致することを確認した。
local SSHはDGX PID 14400、Labo PID 16264で、dispatcherが接続を維持する。
曖昧なSSH応答や完了待ちを根拠に再起動しない。

実行先は各hostの既存環境root配下の`portable-bar-full-parity-v1/result`である。
`execution-intent.json`、比較結果のartifact、終端時の`completion.json`を別出力として保存する。
失敗した場合もerror・tracebackと出力を残し、許容差を緩めて同じ実行を成功扱いにしない。
localの起動記録とprocess照会は`data_portable_bar_2026-10-19/`の`*-full-parity-*.json`にある。
再現source・受入logは同directoryの`full_parity_sources_v1/`に保存した。
これらの追加作業によって、CI成功済みの公開候補`47ef1b6`を変更していない。
