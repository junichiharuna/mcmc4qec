# 再起動後の引き継ぎ：mcmc4qec

記録時点は2026-10-24 12:09 JSTである。
このファイルはローカルの作業再開用であり、公開配布物にそのまま追加しない。

## 最初に読む結論

このPCを再起動しても、mcmc4qecのクラスタ計算と後続処理は継続する構成に移設済みである。
12:08頃のWindowsプロセス確認では、mcmc4qecの計算・待受Python、SSH・SCP・SFTP・rsync転送は残っていなかった。
残るPython 2本はarxiv MCP serverであり、科学計算のworkerではない。
12:09のクラスタ照会では、最終集約ジョブ265507.node-PRISMはRで、独立したcontrollerも生存していた。
全工程の完了はまだ確認できておらず、goalは未完了である。
再起動後は既存の実状態を照合し、ジョブや旧待受を起動し直さない。

## 再開時の指示文

次の文を新しい会話へ渡せる。

> A:\dev\mcmc4qec\RESTART_HANDOFF_2026-10-24_ja.md と現在の AGENTS.md を読み、既存クラスタジョブとcontrollerを確認して、未完了の数値検証・日本語最終報告を継続して。
> 旧ローカル待受やcontrollerを重複起動せず、公開済みGit履歴へ旧履歴をpushしないこと。

## 再起動後に最初に実行する確認

PowerShellで以下を実行する。
これは既存のクラスタ状態を読み取る確認で、ジョブ投入や計算の再開操作ではない。

```powershell
Set-Location -LiteralPath 'A:\dev\mcmc4qec'
& 'C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe' -B output/cluster_postprocess_pipeline_v1/observe_controller.py --compact
```

確認scriptはSSH alias `cluster`を使用し、時刻付きの観測JSONを`output/cluster_postprocess_pipeline_v1/`へ保存する。
`controller_live`、`controller_error`、`errors`、`stages`、`active_jobs`、`final_progress`を読む。
`final_progress`には最終集約の実行・完了・失敗記録とreaderログ末尾が含まれる。
ログが空というだけで、停止・成功・進捗率を判断しない。
SSHの失敗やtimeoutだけでジョブが停止したと判断せず、同じジョブIDとcontrollerを再照会する。

個別のPBS状態を直接確認する場合は次を使う。

```powershell
ssh cluster qstat -xf -F json 265507.node-PRISM
```

時間が経つとPBSの完了履歴が消える場合があるため、ジョブが一覧にないだけで再投入しない。
controllerの段階記録、投入ledger、出力、保存済み終端記録を併せて確認する。

## 記録時点の処理状況

| 工程 | 確認済み状態 |
|---|---|
| C3T2のsampling・PC解析回収 | 全38バッチ・768群・67,584行を回収済み |
| 索引265505 | 終了コード0、25分10秒 |
| 入力配置・hash照合265506 | 終了コード0、3分55秒 |
| 保存済み診断内訳265508 | 終了コード0、2分42秒、結果回収済み |
| C3T2最終集約265507 | 11:02:46 JST開始、12:09確認時点でR、1ノード1CPU32GB・walltime上限12時間 |
| 算術照合・12番目のcandidate準備 | 最終集約終了後にクラスタcontrollerが進める |
| 全12条件比較・独立計時・日本語最終報告 | 後続へ接続済みだが本番完了は未確認 |

記録時点では最終集約の`completion.json`、`failure.json`、`final-report.json`はなく、readerのstdout・stderrは空だった。
記録時点の観測証跡は`output/cluster_postprocess_pipeline_v1/controller-observation-1792811369541030100.json`である。
最終集約開始や移設の受入成功を、科学的合格・全工程完了とは扱わない。

## クラスタ側の保存先と制御

クラスタ側の移設起点は以下である。

```text
/home/user/workspace/mcmc4qec/20261024-c3t2-index-relocation-v1
```

この起点の`pipeline-state/controller/`に段階別記録とエラー記録があり、`pipeline-state/controller-launch/launched.json`に起動commandとPIDを保存している。
起動時controller PIDは4045000であり、別SSH接続から親PID1・command一致・生存を確認済みである。
PIDは再利用され得るため、番号だけで停止・再起動・生存判定を行わない。
後段の実装は起点の`output/cluster_postprocess_pipeline_v1/control.py`であり、同じ相対パスにローカルの控えがある。
固定source・入力1,223件を結び付けたcontroller envelopeを配置済みで、稼働中の固定sourceや入力は変更しない。
最終集約の実体は以下にある。

```text
/home/user/workspace/mcmc4qec/20261022-planned8h-c3t2-final-v1
```

固定config SHA256は`7d3e4fc4b0143e70c8c79f0dfa93099e62c53981c73e44accec356b1373404b7`である。
controllerは集約結果の回収、算術照合、candidate準備、全12条件の分割比較、独立census・計時、最終報告へ順に進む。
最終報告jobの成功、report JSON・日本語Markdownの回収とhash一致まで確認してからcontrollerの完了を記録する。
重い計算は必ずqsub投入し、共有lockと待機・保留を含む要求ノード数最大2を維持する。
ローカルへの新しい重い計算の戻しや、旧待受の再起動は行わない。

## 完了後に行うこと

最終集約が終了していたら、PBS終端・終了コード・投入記録・出力hashを照合し、クラスタcontrollerが既に後続を開始していないか確認する。
正常進行中なら重複投入せず、その処理を追跡する。
失敗していたら同じjob IDのfailure・stderr・controller journalを読み、既存成果を保持して復旧する。
全12条件の正式比較・独立計時・日本語報告の結果を回収し、設定数・独立seed分母・未定義診断・未取得区間・実行環境・再現手順を照合する。
事前規則で計時対象なしとなる場合も、その根拠と全method行を保持する。
科学的gate未達は隠さず結論へ反映し、独立referenceのない低ノイズ領域の整合を精度・被覆の保証としない。
全要件の実体を確認するまでgoalをcompleteにしない。

## ここまでの結果と文書

状態の一覧は[PROJECT_STATUS](docs/wp/PROJECT_STATUS_2026-10-24_ja.md)、移設の詳細と異常時の扱いは[クラスタ移設記録](docs/wp/cluster_postprocess_pipeline_2026-10-24_ja.md)にある。
要件ごとの完了判定は[goal完了条件](docs/wp/goal_completion_status_2026-10-23_ja.md)を参照する。
主4条件の校正・直接MC・重み層別referenceは[tile中間報告](docs/wp/tile_validation_report_2026-10-18_ja.md)、C3T1は[条件別結果](docs/wp/low_c3t1_result_2026-10-23_ja.md)にある。
C3T2の追加診断集計は[保存済み診断内訳](docs/wp/c3t2_saved_diagnostic_result_2026-10-24_ja.md)に保存済みである。
全352設定各192反復で診断flagがあり、区間未取得は0、分母除外は0だった。
logical bit診断の未定義が全設定・全反復に含まれるが、全観測量が未定義という意味ではなく、未定義だけから支持の非連結や原因を断定しない。

## 公開済み履歴を壊さないこと

GitHubリポジトリと[v0.1.0.dev5 experimental Release](https://github.com/junichiharuna/mcmc4qec/releases/tag/v0.1.0.dev5)は公開済みで、PyPIには公開していない。
公開mainとtagのcommitは`c27ca896a1025c74975bc45322798eea2e0409b0`である。
この計算用作業ツリーのHEADは`98222e1daf80e4387a5fd588729052baee923515`で、公開時に修正する前の履歴を維持している。
この作業ツリーから旧履歴をmerge・pushしない。
未コミット変更と計算入力を削除・reset・cleanしない。
公開作業を行った隔離リポジトリは`output/publish_experimental_20261024/repo`である。
新しいcommit・pushは所有者の指示時だけ行い、公開履歴への同期は差分と固定入力を保全してから設計する。
公開結果と配布物の検証記録は[公開記録](docs/wp/publication_result_2026-10-24_ja.md)を参照する。

## 回答待ち・その他の制約

所有者からZenodoのGitHub連携済みとの回答はあるが、DOIとmetadataの照合は未完了である。
11:20の公開records API検索は0件、11:48のGitHubリポジトリwebhook一覧も0件だったが、それだけで連携失敗や原因を断定しない。
ブラウザ確認はTransport closedで利用できず、Zenodo設定画面にv0.1.0.dev5が表示されるか、状態またはErrorsの文面を所有者に問い合わせ済みである。
回答が来たら取り込み、同じ質問を繰り返さない。
この回答待ちはクラスタ計算の継続を妨げない。
サブエージェント枠は前の実行で利用上限に達し、10月25日05:41まで再試行しないという記録があるため、制限を迂回しない。
RIMCは読み取り専用で参照し、稼働中の数値設定・seed・failure定義・校正の分母は維持する。
