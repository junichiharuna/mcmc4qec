# 低ノイズ合成解析capacityの投入仕様

専用の`low_noise_synthetic_analysis_capacity` manifestだけを受け入れ、同じcase/targetから再構成した現source・runtime・native入力と完全照合する。
sampling capacityや本番manifestを代用しない。
初回の資源要求は1ノード・96 CPU・340 GiB・24時間であり、消費量や終了時刻の予測ではない。
実行は専用driverの`run --root ROOT`とし、manifestが固定する8 workerを用いる。
合成データは資源測定だけに用い、科学的な精度・被覆の根拠にはしない。

出力rootはbundleの`runs`配下に限定し、manifest・native入力・scriptのsymlinkによる外部への脱出を拒否する。
実際に起動するbundle内driverと依存source、src packageのhashを、plan検証に用いた現在のsourceと照合する。
venvの共有は許可するが、実行予定Pythonの解決先とfile hashを証跡に含め、qsub直前に再照合する。
既存のsubmission intent・ledger・execution intent・summary・profilesがあれば自動再投入しない。
dry-runはscriptと予定記録を作るだけで、qsubもクラスタ状態照会も行わない。

実投入は既存low-noise submitterと同じ`bundle.parent/tile-low-noise-submission.lock`を排他的に取得する。
既存のlive_controllers・own_active_jobs・requested_nodesを利用し、coordinatorが稼働中、またはqueuedを含む要求ノード数が追加後2を超える場合は拒否する。
source・manifest・native入力・script・Pythonを再照合し、排他的submission intentを保存してからqsubを1回だけ呼ぶ。
応答が正規のjob IDならledgerを保存しlockを解放する。
timeout・非零終了・不明応答・intent後の記録失敗では、intentと共有lockを保持し、queueを調べるまで再試行しない。
intent作成前の拒否や状態照会失敗ではlockだけを解放する。

受入は実qsubをmockし、queued上限、controller、共有lock、再投入拒否、不明応答、任意path脱出、source変更とqsub直前の変更を確認する。
