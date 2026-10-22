# 分割workerの単発qsub投入：小仕様

既存の共有 `tile-low-noise-submission.lock` を使い、準備済みworkerを一度だけqsubへ渡す。
RIMCの `AGENTS.md` にあるheavy processはlogin nodeで動かさずqsubを使う規則と、既存mcmc4qec wrapperの単発投入方式を参照する。
研究リポジトリや既存controllerは変更しない。

準備receipt、全固定成果物、元入力・source・resolved path、対象prepared・script・環境を再照合する。
投入は `qsub <script>` とし、実行前に同じ共有lockの所有を確認する。
利用者の非終端PBSジョブをQ・Hなども含めて数え、複数chunkを含むselectの要求node合計に新しい1nodeを加えて2以下とする。
既存の旧coordinatorが動いている場合やlockが既にある場合は、投入しない。
qstatの失敗や不明な資源を空きnodeとして扱わない。

intentをexclusiveに保存し、qsub呼出し前にもう一度node数と固定入力を確認する。
qsub応答、stderr、returncodeを保存し、一つの明確なjob IDだけを台帳へ保存する。
timeout・非ゼロ終了・曖昧な応答ではintentと応答・例外を保持し、共有lockを自動解放せず再投入しない。
未投入でのgate失敗や正常な台帳保存後は、自分が取得したlockだけを解放する。
既存intent・台帳・実行記録を持つworkerを再投入しない。

qsub応答保存より先にworkerが起動する場合に備え、runner v2は実PBSのR状態・script・資源・hostを確認してから台帳を最大30秒待つ。
同じジョブ内で欠落または書込途中のJSONだけを待ち、有効だが不一致の台帳は直ちに拒否する。
待機終了をジョブの終了や再投入許可とみなさず、timeoutは失敗記録として残す。
v1のsource・受入資料・クラスタbootstrap結果を保持し、新しいv2を別のsourceとして扱う。

受入テストではqsubをdoubleに置き換え、lock所有、Qを含む2node上限、二重投入拒否、応答異常での保存とlock保持を検証する。
runnerの台帳待機は時計と待機処理をdoubleにし、欠落・部分JSON・不一致・timeoutを検証する。
実clusterへの新規投入、全12条件の本番準備、結合と後続census接続は未実施として区別する。
