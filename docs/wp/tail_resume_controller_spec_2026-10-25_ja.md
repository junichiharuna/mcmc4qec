# 完了済み比較からのtail専用再開controller

265675のcensus準備失敗に対し、資源方針の実測・修正と独立な再開controller部分を準備した。
仕様・受入fixture・実装の順に`output/finite_tail_resume_controller_v1/`へ保存し、本番の移行configと起動はまだ行っていない。

## 保存する完了結果

元v12 config、source、error、process/start、comparison、handoffをpinで固定する。
元12 worker・merge 265660・acceptance 265661のprepared/ledger/sourceと、実PBSのowner・script・resource・run 1・F/0を確認する。
元observerの既存completion受理を利用し、巨大result/selectionは開かない。
元workerやmerge/acceptanceのprepare・submit・run・capture、科学入力の再計算をcontrollerに持たせない。
comparisonとhandoffは既存のまま読み、新journalのresume-intentで実新configとの関係を記録する。
旧handoffの世代を新controllerの成功世代へ書き換えない。

## 再開の条件

旧v12のPID/start ticksを照合し、同じprocessが生存していれば起動を拒否する。
失敗265675の実F/1・run 1・script・資源とplanning-failureを確認し、旧partial rootsを非再利用のまま保持する。
新flow journal/launch、outer job root、inner journal、census config/job rootを新しくする。
未使用の独立計時/report出力先と、元merge root・handoff・科学入力を保持する。
既存6roleとfinal-reportを固定順序で一度ずつ実行し、任意skip、同root再利用、失敗時の自動retryを認めない。
起動には元detached launcherをそのまま利用し、新しい薄い入口で採用条件を再確認する。

censusの新sourceと資源方針はこのcontrollerで決めない。
実測後に確定したtransition validator・authority・実native acceptanceと最終tail configを外部pinとして要求する。
元seed・科学入力・完了比較の保持と、許可した運用差分だけであることを、その限定validatorで確認する。
実測前の暫定値で本番移行configを生成しない。

## 独立部分の受入と未実施の範囲

qsub 265679はF/0・run 1・wall time 1秒で、25 fixtureが0.046秒で成功した。
検証対象は比較/handoffの一致、bounded metadata読込、巨大payloadのopen前拒否、元PBS検証関数のF/1・rerun・別owner/script/resourceの拒否、旧PID生存の拒否、7role順序、失敗停止、既存journal非再利用である。
fixtureは合成metadataと元のpure検証関数を使い、科学計算を行っていない。
小証跡は`output/finite_tail_resume_controller_v1/tests-observation.json`、クラスタ原本は`$HOME/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1/pipeline-submissions/finite-tail-resume-tests-v1/`にある。
独立レビューではこの候補の静的blockingは見つからなかったが、この25件だけで実constructor全経路を受け入れたとは扱わない。
最終tail source/resource/authorityを使った実14job採用・新constructor・native接続は未実施であり、その受入後に統合担当が本番起動を判断する。
