# 独立計時以降の引き継ぎ（2026-10-26）

2026-10-26 11 時ごろ、所有者は Codex の自律ループを止め、残りの作業を Claude Code に引き継いだ。
同時に [並列化の打ち切り](independent_parallel_execution_2026-10-26_ja.md) を決めた。
この文書は引き継ぎ後の入口であり、時刻付きの詳細履歴は [状態文書](PROJECT_STATUS_2026-10-24_ja.md) と [最終成果物監査](final_deliverable_audit_2026-10-24_ja.md) に残す。
以後の進捗はこの文書の末尾に短く追記し、原本の hash や job 番号は監視 JSON に残す。

## 稼働中の仕組み

クラスタ常駐の v13 controller（PID 1598334、起動記録と command 一致を確認済み）が、独立計時を条件ごとに自動で進める。
1 条件につき MC capacity → BAR capacity → MC main → BAR main の 4 job を順に投入し、各 job の前後に observe・finish の有限 PBS 補助 job（1 CPU・96 GiB・上限 4 時間）を挟む。
全 24 task（12 条件 × MC/BAR）の main が terminal になると、同じ controller が report 段（prepare → gate → submit → observe → seal）に進み、最終 report job を PBS に投入する。
重い計算はすべて qsub で動き、ローカル PC は読み取り観測だけを担当する。
controller・job・旧待受は再起動しない。
観測の失敗や timeout だけを理由に、停止や再投入を判断しない。

## 引き継ぎ時点の進捗（10:54 JST）

| 項目 | 状態 |
|---|---|
| 条件 | 12 条件（c0/c2 × t0/t1/t2 × e0/e1） |
| 完了した条件 | 4 条件（c0t0e0, c0t0e1, c0t1e0, c0t1e1）、main 8 本が terminal・回収済み |
| 進行中 | c0t2e0 の capacity 2 本が計算終了、finish 補助 job 265785 が実行中 |
| 未着手 | c0t2e1, c2t0e0, c2t0e1, c2t1e0, c2t1e1, c2t2e0, c2t2e1 の 7 条件 |
| 手法行 | 48 行（selected 24、not_selected 24）、各 main の予定分母 192 |
| ペース | 1 条件あたり約 4.5 時間 |
| 見込み | 計時完了は 10/27 夜ごろ、その後に report 段 |

main 8 本の terminal は controller の controls 結果と collected copy の両方で確認した。
Codex の文書では c0t1e1 の 2 本を正式受理前として 6/24 と数えていたが、finish action 00047・00049 は accepted 済みで、controller 上は 8/24 である。
見込みは PBS の要求時間や過去 4 条件の実時間からの外挿であり、確定した終了時刻ではない。

## 監視方法

PowerShell から次を実行する（SSH alias `cluster` を使う）。

```powershell
& "$env:LOCALAPPDATA/Programs/Python/Python311/python.exe" -B output/takeover_monitor_v1/monitor.py
```

`output/takeover_monitor_v1/remote_collect.py` をクラスタへ送って読み取り専用で実行し、controller の生存、全 task の state と PBS 終端、controls・collected の有無、直近の action、active job を 1 画面に出す。
観測 JSON は `output/takeover_monitor_v1/obs-<時刻>.json` に保存する。
qsub・削除・書き換えは行わない。
Codex が使っていた読み取り観測 `output/finite_tail_resume_controller_v1/observe_window.py` も併用できる。

## 残作業

1. 独立計時の完了を監視し、失敗した job があれば同じ job 番号の failure・stderr・controller journal を読んでから対処する。
2. report 段の完了後、最終 report JSON を回収し、48 行・各 192 反復・失敗や未取得の件数を照合する。
3. 全 48 行の精度 gate と費用比較を集計する。
4. [最終報告草稿](final_validation_report_draft_2026-10-24_ja.md) を確定版にし、精度・被覆・速度の主張は gate を通った範囲に限る。
5. 再現用 snapshot（source・環境・seed・最終証拠）を保存する。
6. TODO.md の Zenodo DOI、生データ公開、PyPI 準備は所有者の判断を待つ。

精度 gate 未達は隠さず結論へ反映し、独立 reference のない低ノイズ領域の整合を精度・被覆の保証としない。

## 引き継ぎ時点の作業ツリー

未コミットの変更は examples の `--ladder` オプションと CLI テスト、`tools/reproducibility/`、docs/wp の 2026-10-24〜26 のメモ類である。
禁止識別子の混入はなく、commit は所有者の指示で行う。
Codex が残した並列化の候補実装は `output/` 配下に保持し、本番 controller には接続しない。

## 追記

### 2026-10-26 11:29 JST：並列 driver への切替

所有者の再判断により、補助 job を並列化する縮小版 driver を実装し、v13 controller を止めて切り替えた。
経緯・設計・受入・切替記録は [並列化の記録](independent_parallel_execution_2026-10-26_ja.md) にまとめた。
以後の監視は `output/takeover_monitor_v1/monitor.py` が新 driver の journal も表示する。
切替時点の進捗は、条件 4 完了、c0t2e0 の capacity 2 本が計算終了（BAR の finish 補助 job を引き継ぎ）、main 受理 8/24 である。
