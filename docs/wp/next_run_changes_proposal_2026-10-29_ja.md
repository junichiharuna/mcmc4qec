# 次回 run 向けの変更案（低ノイズ独立計時の運用から、2026-10-29）

本稿は 2026-10-25〜29 の低ノイズ独立計時（48 手法行）と report 段の運用で見つかった、次回 run で変えるべき点を 1 枚にまとめたものである。
個々の観測は[並列化の記録](independent_parallel_execution_2026-10-26_ja.md)に時刻付きで残っており、本稿はその索引と判断材料である。
凍結された script・policy・config の変更はすべて所有者の判断で行い、今回の run には何も適用していない。
優先度は、次回 run の所要時間と失敗リスクへの効きで付けた。

## 一覧

| # | 項目 | 影響 | 変更箇所 | 優先度 |
|---|---|---|---|---|
| 1 | report script の binding 照合に移設後の source path を受理させる | 今回 report 段が最初の役で失敗し、別経路に 1 日かかった | `tile_low_noise_timing_evaluation_report.py` の `reference_evidence`（今回の delta v2 を次版に取り込む） | 高 |
| 2 | report 段の補助 job のメモリを 32 GB にする | seal 補助 job が 16 GB で kill された | 経路 script の `run_step`（既定 16 GB → 32 GB）、v13 の finite action の資源指定 | 高 |
| 3 | `allowed_vnodes` を広げる（2 物理ノード上限は維持） | 2 台目を他ユーザーに取られると補助 job も science job も置けず、1 台で直列になった | `20261025-census-active-node-v13/policy.json` の後継版（新 sha）、`census-recovery` config、driver 再起動 | 高 |
| 4 | 凍結 submit script の自己 job 数え方 | 補助 job（observe・collect）も「1 ノード」と数え、others+1 ≤ 2 の gate で submit が失敗した。driver 側の「frozen budget hold」で回避したが、補助の並列度が落ちる | stage3-v2 の submit script の gate（`requested_nodes(own_active_jobs())`） | 中 |
| 5 | walltime 下限の defect | main の walltime は `max(1800, 1800·ceil((2·predicted+600)/1800))` で、pool 外の固定費 1550〜1854 秒（closure 再検証 11 分 + preflight 4 分 + 後処理 12 分）を見込まない。30 分 bucket に入る main は kill の危険がある（c0t0e0 BAR main は残り 8 秒で終了） | `tile_low_noise_timing_execution.py` の資源 policy（凍結、所有者判断） | 中 |
| 6 | report 段の並列化 | report job は 48 root を直列に再検証して 9 時間 43 分。root ごとの検証は独立なので 12 並列なら 1 時間弱 | report script の `run`/`load_method`（delta v3）と `report_job.py` の `RESOURCE`（1 CPU → N CPU） | 中 |
| 7 | science job の 96 CPU 予約 | main は平均 1〜15 コア（workers=21）しか使わず、ノード 1 台を丸ごと占有する。予約を減らせば 2 本を同居させられるが、完了済み行との比較可能性が崩れる | manifest の `workers` と select 行 | 低（所有者判断） |
| 8 | capacity job の `mem=340gb` | 350 GB ノードで capacity job の横に 96 GB の補助 job が置けず、9 分の待ちが毎回発生 | capacity の資源指定 | 低 |
| 9 | 補助 job の 96 GB 要求 | 補助 job は 1 CPU で実 RSS 1〜18 GB。96 GB 要求のためノードあたり 3〜4 本で頭打ち | 補助 job の `mem`（32 GB で足りる） | 低 |
| 10 | login host の python は 3.6 | `subprocess.run(capture_output=…)` が使えない。経路 script はすべて環境 v2 に pin された venv の python 3.11 で起動する | 運用手順（script の冒頭に明記） | 低 |

## 各項目の根拠

### 1. binding 照合の移設耐性

受理済み selection の 12 calibration bindings のうち 9 件は復旧・portable reader に由来し、`reference_audit_digest` が参照 audit report の `source_sha256` を v11 の path で持つ写しから計算されている。
凍結 script は raw の v7 audit report を digest するので、この 9 件は path 接頭辞の違いだけで必ず落ちる。
今回の delta（`output/report_relocation_route_v1/binding_delta.py`）は、同関数内で既に計算している移設後の source 一覧で `source_sha256` を差し替えた report の digest も受理するもので、hash の集合は同じである。
次版の report 環境にこの 1 箇所を取り込み、effective.py 以下 5 層の pin を更新すれば、別経路は不要になる。

### 2. report 段の補助 job のメモリ

原本 `report_job.py` の prepare・submit は 16 GB で通ったが、seal は 17.8 GB を使って PBS に kill された（job 265949）。
report job 本体も 17.9 GB を使う。
補助 job の既定を 32 GB にすれば済む。

### 3. allowlist の拡大

v13 の実 allowlist は `20261025-census-active-node-v13/policy.json` の 2 ノード（1 台目・2 台目）だけで、`low-parallel-dispatch-policy-v2〜v6` の allowlist は v13 鎖では使われていない。
2 物理ノード上限は `physical_node_capacity_v1/capacity.py`（`max_physical_nodes: 2`）と凍結 submit gate が allowlist の長さと独立に守るので、allowlist を広げても上限は変わらない。
10/27〜28 に 2 台目が他ユーザーの 48 時間 job に取られ、約 18 時間を 1 台で直列に進めた。
10/28 時点で使えるノードは 44 中 15 台程度（27 台は 2026-08 から down）で、空きは 010・012・019・020・031・032・039・040・042・043 だった。
変更には新しい policy 版（sha）、`census-recovery` config の差し替え、driver 再起動が要る。
`dispatch.py` が allowlist の候補を順に試すこと（先頭固定でないこと）を変更前に確認する。

### 4. 凍結 submit script の自己 job 数え方

凍結 submit script と finalize の live_gate は自分の PBS job をすべて「要求ノード 1」と数え、others+1 ≤ 2 を要求する。
補助 job は 1 CPU で science job と同じノードに同居するので、この数え方では補助 2 本が同時に生きているだけで submit が止まる。
driver 側の「frozen budget hold」（submit 中は他の補助を 0 本に、通常は 1 本までに抑える）で回避したが、補助の重なりが減り、並列化の利得が小さくなった。
gate を「exec_host の物理 host 数」で数えるよう変えれば、補助 job を自由に重ねられる。

### 5. walltime 下限

predicted は capacity job の約 430 秒の overhead を使って見積もられるが、main は pool の外で 1550〜1854 秒を使う。
30 分 bucket（predicted ≤ 600 秒 ⇔ MC task ≲ 17 秒、BAR ≲ 15 秒）の main は余裕がほとんどない。
kill された main は凍結 `_completion` が「failed main execution is not capacity evidence」として拒否し、同じ walltime で再実行されるので、自力で回復しない。
今回は c2t0e1 以降の capacity 値が 1 時間 bucket に入ったため実害はなかった。
pool 外の固定費を predicted に足すか、下限を 1 時間にする。

### 6. report 段の並列化

report job の `load_method` は 48 root を順に読み、root ごとに `_completion` が task 単位の record を再検証する（BAR 鎖の初期・終状態の再 decode を含む）。
root の大きさにはほぼ依存せず、main root 12〜15 分、capacity root 4〜6 分、合計 9 時間 43 分だった。
root ごとの検証は独立なので、`Evidence` の hash 集約を worker から親に戻す形で並列化すれば 12 並列で 1 時間弱になる。
`report_job.py` の `RESOURCE`（1 CPU・32 GB）も変える必要があり、所有者は 10/28 に今回の run では見送った。
worker ごとに 18 GB 程度のメモリを見込む。

### 7〜9. 資源予約

science job は 96 CPU を予約するが実使用は平均 1〜15 コアで、capacity job の `mem=340gb` と補助 job の 96 GB 要求が同居を妨げた。
これらは完了済み行との比較可能性（同じ予約条件での計時）に関わるので、変えるなら次の計測系列からにする。

### 10. 運用上の注意

- login host の python3 は 3.6 なので、経路 script は環境 v2 に pin した venv の python 3.11 で起動する。
- 計算ノードには ssh できないので、report job の進捗は各実行 root の raw ファイルの atime で読む。
- 自宅 PC から大学の gateway に届かない時間帯があり、ラボ PC 経由（Tailscale）の relay が要った。relay では入れ子の ssh が標準入出力を継承すると止まるので、`Start-Process` で切り離す。
- `qstat -f -u <user>` はこの PBS では何も出ないので、`qstat -u <user>` で id を取ってから `qstat -f <id>` を使う。

## 所有者の判断待ち

- 1〜3 は次回 run の前に入れることを勧める。
- 4〜6 は凍結 script の変更を伴うので、変更する版の authority 層（effective → relocation → outer → merge-relocation → cross-host → census-recovery）の作り直し費用（PBS 受理 job 約 10 本）と合わせて判断する。
- 7〜9 は計測の比較可能性に関わるので、次の計測系列の設計で決める。
