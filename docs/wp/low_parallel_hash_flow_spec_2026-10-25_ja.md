# 並列hash合流を使う常駐controller仕様

科学計算worker12件とfront-v6のprepared・seed・入力・sourceを維持し、合流時の証拠hash照合だけを並列化する。
未起動のserial controller設定とshadow受入証拠は保存し、新しいconfig・journal・合流出力先を使う。
controllerは保持11件と新index0の実投入ledgerを照合して引き継ぎ、再投入しない。

## 固定する追加契約

`parallel_hash`は`policy`、`sources`、`baseline`の3項目だけを持つ。
policyはCPU8、process1、thread8、最大inflight16を明示し、暗黙の資源増加を許さない。
sourcesはbounded_hash・worker_validator・execution_adapter・integrationの実source pinを持つ。
baselineは既存の逐次mergerとcontractのsource pinを保持する。
全pinをcontrollerの不変性確認へ登録し、途中のsource差替えを拒否する。
合流のexecution runner・contractは8 CPU・32 GiB・壁時間24時間・単一ノードの明示資源を用いる。
壁時間は資源予算であり、完了時刻の予測ではない。
元workerの固有runner・manifest・job IDを新しい世代へ書き換えない。
科学的選択条件、数値・seed・独立計時の計画、最終報告の受理条件は変更しない。

## 受入条件

- 追加policyの未知field、誤ったCPU・thread数、boolによる整数の代用を拒否する。
- sourceとbaselineの欠落・未知項目・不正pinを拒否する。
- 初回固定後のhelper改変を不変性確認で検出する。
- PBS実配分とexecution evidenceの両方で8 CPU資源を確認する。
- 全12成功終了前、または所有者の別active jobが残る間に合流を投入しない。
- 不明なPBS照会やcontroller停止からの自動再投入・自動再起動をしない。
- 最終完了は合流だけでなく、独立計時、報告回収、JSONと日本語Markdownのhash照合まで確認する。

PBSジョブ265607で63受入テストが成功し、F/exit 0、実行時間0.029秒、空のPBS標準エラーログを確認した。
63件は既存54件と、並列hashの固定policy・source census・source改変検知の9件である。
PBSジョブ265615で実worker入力・新merge helper・更新tailを結合するshadow constructorが成功し、F/exit 0と空のPBS標準エラーログを確認した。
新execution contractが実際に固定したmain evidenceの配置を使い、旧配置とのbyte同一性を別記録へ保存した。
各worker固有のevidence pinは元のまま保持する。
shadow確認はtick・投入・科学計算・実controller起動を行っていない。
全12実ジョブを改めて照合して実v8 controllerを起動し、SSH切断後の別接続でPID・起動識別子・commandの一致と生存を確認した。
初回巡回では全12件を観測し、index1・2・6・7・8の5件のF/exit 0 terminalを元preparedに結合して回収し、残る7件を処理中として記録した。
初回巡回時点のerror記録と標準エラーは空で、合流・独立計時・最終報告はまだ開始していない。
