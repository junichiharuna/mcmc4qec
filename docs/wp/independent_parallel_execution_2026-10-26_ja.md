# 独立計時の残工程の並列化（縮小版を実装し切替済み）

2026-10-26 午前、所有者から準備・検証・回収の並列化、worker 数に見合う CPU 予約、実測メモリの確認を依頼され、Codex が新 driver の候補実装と PBS 上の合成試験を進めた。
同日 11 時ごろ所有者は Codex のループを止め、残作業を Claude Code に引き継いだ。
いったん並列化の打ち切りを決めたが、実測の内訳を見たうえで「稼働中の controller を走らせたまま縮小版を作り、受入が通った場合だけ task 境界で切り替える」方針に変更し、11:29 JST に切り替えた。

## 実測した時間の内訳

直近の完了条件 c0t1e1（04:55〜09:49、4 時間 54 分）の内訳は次のとおりだった。

| 区分 | 内容 | 合計 |
|---|---|---|
| 科学 job | capacity MC 11 分・BAR 8 分、main MC 56 分・BAR 38 分 | 1 時間 53 分 |
| 補助 job（1 CPU・96 GiB、直列） | submit 15+15+46+47 分、observe 4+4+11+11 分、finish 41+42+23+23 分 | 4 時間 42 分 |
| queue 待ち | 全 job で 0 | 0 |

補助 job の鎖がクリティカルパスで、計算ノードが動いているのは 4.9 時間のうち約 1.9 時間だった。
補助 job の所要時間は毎回ほぼ一定で、固定の検証作業（PBS 内での大きな成果物の再 hash、投入前の深い入力検証）に由来する。
補助 job の qsub と科学 job の qsub は同じ共有ロックを使うため、submit 補助 job が走る約 2 時間は他の補助 job を新規投入できない。
この制約を織り込んだ見積もりは 1 条件 4.9 → 約 3.4 時間（約 1.4 倍）で、残り条件数から縮小幅は 8〜10 時間程度である。

## 実装した縮小版

Codex の候補（preflight・lease・new_cpu 経路・移行 authority を含む 7 部品）は組み立てが未着手だったため採用せず、単一ファイルの driver `output/independent_parallel_driver_v1/pdriver.py` を新たに書いた。

- 凍結済みの有限 action 機構（payload、job.py の prepare/submit/observe、dynamic gate、dispatch.finalize、alias 検証）は一切変更せず、同じ呼び出し順で使う。
- 直列の Coordinator ループだけを単一スレッドのイベントループに置き換え、observe・finish・submit の補助 job を最大 3 本まで同時に in-flight にする。
- submit 補助 job は常に 1 本だけ（共有ロック）。pending は main 優先。
- 科学 job の投入 gate は「所有 job が占める物理ホストが 1 以下」で判定する。補助 job が同じノードに何本あっても 1 と数えるので、補助 job が科学 job の投入を妨げない。所有ノード数の上限 2 は維持する。
- 補助 job の配置候補は policy の許可ノード 2 台とし、科学 job が占めていない側を dynamic gate が選ぶ（v13 と同じ。切替直後は 2 台目に固定していたが、12:40 に戻した。後述）。
- 切替時は v13 が実行中だった action を journal から引き継ぎ、途中状態（submitting / finishing）を照合する。不明な投入は自動再試行せず停止する。
- 全 24 task が terminal になると `independent-execution/completed.json` を書き、report 段の 3 role を v13 と同じ journal 構造で実行する。

受入は、fake cluster による単体テスト 10 件（ローカル・クラスタ双方で成功）と、v13 稼働中の実 config・実 state に対する読み取り専用 dry-run で行った。

## 切替の記録

- 11:29 JST、state をバックアップ（SHA-256 `4a9c0893…5734b`）し、v13 controller と run.py を SIGTERM で停止、共有ロックの不在を確認して driver を起動した。
- driver は実行中だった finish 補助 job 265788（c0t2e0-bar-capacity）を引き継ぎ、同時に c0t2e0-mc-main0 の submit 補助 job 265789 を投入した。2 本は同じ補助ノードで並走し、これが従来できなかった重なりである。
- 運用メモ（再開方法、journal の場所）は `output/independent_parallel_driver_v1/README_ja.md` にある。

## 稼働後に分かったこと（12:15〜12:40）

- 12:15 JST、submit 補助 job 265789 が受理され、新しい gate を通って c0t2e0-mc-main0（科学 job 265790）が投入された。切替後の最初の科学投入である。
- 科学 job の select はノード指定がなく、PBS は空いていた補助ノード（許可ノードの 2 台目）に 265790 を置いた。科学 job は 96 CPU を全部予約するので、同じノードには補助 job を置けない。許可ノードのもう 1 台は他者の job で埋まっていた。
- 切替時の driver は補助 job の配置候補を 2 台目に固定していたため、次の submit 補助（c0t2e0-bar-main0）は「安全な配置候補なし」で待ちになった。候補を許可ノード 2 台に戻し（dynamic gate が科学 job と別のホストを選ぶ、v13 と同じ挙動）、12:40 JST に driver を `--resume` で再起動した（PID 3551253、共有ロックの不在を確認済み）。
- ただし他者の job がもう 1 台を占めている間は、科学 job 265790 が終わるまで補助 job は置けない。これは配置の運であり、v13 でも同じ条件なら同じ待ちが起きた。
- 科学 job 2 本の同時実行は、所有ノード上限 2 台と「科学 job が 1 ノードを丸ごと予約する」ことの組合せで、補助 job と両立しない（2 本走ると補助 job の置き場がない）。実際の配置は v13 と同じ「科学 job 1 本 + もう 1 台で補助 job」で、短縮は補助 job 同士の重なりと科学 job との重なりの分だけである。10/27 夕方という完了見込みは楽観的で、見直しが必要である。
- 補助 driver の `--dry-run --resume` は、切替時の実装では dry-run にならず本番の再開として動いた（12:36 に誤って起動、12:40 に停止して正規の手順で再起動）。ローカルの `pdriver.py` は dry-run を読み取り専用に直したが、クラスタ側は次の再起動機会まで旧版（SHA-256 `ddaba245…1bab`）のままである。

### 科学 job の CPU 使用率

PBS の `resources_used` から、完了した main 8 本と実行中の 1 本の平均使用コア数（cput ÷ walltime）を出した。

| job | 条件 | walltime | 平均コア数 |
|---|---|---|---|
| 265721 | c0t0e0 MC | 27 分 | 1.3 |
| 265723 | c0t0e0 BAR | 30 分 | 2.5 |
| 265737 | c0t0e1 MC | 28 分 | 2.2 |
| 265739 | c0t0e1 BAR | 38 分 | 4.1 |
| 265753 | c0t1e0 MC | 34 分 | 5.2 |
| 265755 | c0t1e0 BAR | 33 分 | 3.1 |
| 265770 | c0t1e1 MC | 56 分 | 11.2 |
| 265772 | c0t1e1 BAR | 38 分 | 5.9 |
| 265790 | c0t2e0 MC | 106 分 | 15.1（終了時、cpupercent 最大 2097） |

科学 job の予約は `select=1:ncpus=96:mem=337gb`（ノード丸ごと）だが、manifest の `resource.workers` は 21 で、メモリ方針（337 GiB ÷ worker あたりの見積もり）から決まっている。
実際の使用は平均 1〜15 コアで、重い条件ほど worker 数 21 の上限に近づく（265790 の開始 16 分時点では 2.7 コアだったが、終了時の平均は 15.1 コアだった）。
96 コアの予約は排他的なノード確保と計時条件の統一のためのものである。
予約を縮めれば 1 ノードに科学 job 2 本や補助 job を同居させられるが、完了済み 8 本と計時条件が変わるため、変更するなら所有者の判断で全件やり直すことになる。本作業では変更しない。

## 稼働後に分かったこと（14:00〜14:50）

c0t2e0 MC main（265790）は 14:00:50 に終了し（walltime 1:45:39、cput 26:37:14）、観測・回収の補助 job が同時に走り、14:35 に terminal になった。
c0t2e0 BAR main の submit 補助（265791）は 265790 の終了直後 14:01 に allowed_vnodes の 2 台目に置かれ、14:46 に科学 job 265794 を投入した。
265794 は他ユーザーの job が終わって空いていた 1 台目に着地し、補助 job は 2 台目のままなので、`physical_host_count_v1` の gate は意図どおり「科学 1 台 + 補助 1 台」で通った。
投入の 2 秒後に次の c0t2e1 MC capacity の submit 補助（265795）が同じ 2 台目で始まり、科学 job と submit 補助の重ね合わせは成立している。

補助 job の所要時間は PBS の記録で次のとおりで、v13 の記録と同じである。

| 補助 job | 種別 | walltime | cput |
|---|---|---|---|
| 265789 | submit（c0t2e0 MC main） | 45 分 31 秒 | 45 分 20 秒 |
| 265791 | submit（c0t2e0 BAR main） | 45 分 17 秒 | 45 分 08 秒 |
| 265792 | observe | 11 分 17 秒 | 11 分 14 秒 |
| 265793 | finish | 22 分 26 秒 | 22 分 21 秒 |

### submit 補助が 45 分かかる理由

submit 補助は凍結済みの原本 submit script（`submit_tile_low_noise_timing_execution.py` 系）を qsub 差し止めで実行しており、その 45 分はほぼ全部が 1 コアの検証計算である。
証跡 file の mtime から内訳を読むと、開始から最初の qstat（parent-gate-000）まで 23 分、次の qstat 2 回（parent-gate-001・002）まで 11 分、qsub 境界まで 11 分である。
原本 script の構造上、投入前に `read_plan`（pinned source closure の全 file 再 hash、上流 final report 群の再読込と再検証、prepared の再計算）が 3 回走り（開始時と gate 2 回）、1 回あたり約 11 分かかる。
共有ロックは最初の gate から driver の finalize まで握られたままなので、submit 補助を 2 本同時に走らせることはできず、submit lane が 1 本なのは driver の都合ではなくロック設計の帰結である。
残り科学 job は 28 本（capacity 13、main 15）で、submit lane だけで 28 × 45 分 ≒ 21 時間が下限になる。
この 45 分を縮めるには凍結済み script の検証を変えることになり、pinned closure の hash が変わるので所有者の判断が要る。本作業では変更しない。

### 15:01 の観測（capacity の submit は 14 分、科学 job の同居）

c0t2e1 MC capacity の submit 補助（265795）は 14 分 17 秒で終わり、main の 45 分より短かった。
capacity の原本 submit script は上流 report の再検証を持たないので、再検証 3 回分が軽い。
したがって submit lane の下限は main 1 本あたり 45 分、capacity 1 本あたり 14 分で、残り 28 本（capacity 13、main 15）では約 14 時間になる。

15:01 に c0t2e1 MC capacity（265796、`select=1:ncpus=2:mem=340gb`）が投入され、BAR main 265794 が 1 台目で実行中のまま、2 台目（補助 job と同じノード）に着地した。
`physical_host_count_v1` は所有 job の物理ホスト数を数えるので、submit 補助が終わって 2 台目が空いた瞬間に「1 台」と判定して投入を許し、capacity job は PBS の配置で 2 台目に入った。
所有 job が占める物理ホストは 2 台のままで、2 台上限は守られている。
capacity job は 2 CPU の予約で、以前も他ユーザーと同居するノードで走っていたので、計時条件は変わらない。
main 同士は 96 CPU 予約のため同居できないが、capacity は main と重ねられることが分かり、これは v13 には無かった重ね合わせである。

### 見込み（15:01 時点、後述の停止で改訂）

条件あたりの壁時計は「submit lane の占有（capacity 14 分 × 2 + main 45 分 × 2 ≒ 2 時間）+ main の実行時間が 45 分を超える分」で近似できると考えた。
この見積もりは 15:28 の停止で分かった凍結 gate の制約を含んでいないので、次節で改訂する。

## 15:28 の停止と 15:42 の再開（凍結 gate の node 予算）

15:20 に BAR main 265794 が終わり、driver は観測補助 00006（265797）と、次の c0t2e1 BAR capacity の submit 補助 00007（265798）を同時に 1 台目へ出した。
このとき 2 台目では capacity job 265796 が実行中だった。
00007 は 7 分で失敗し、driver は PBS の失敗記録を見て 15:28 に停止した（`error-1792996113.json`）。

失敗の中身は、凍結済みの原本 submit script（stage3 の `submit_tile_low_noise_timing_execution.py`）が持つ gate である。

```
r.require(not controller_query() and requested_nodes(active_query())+1<=2,'controller active or two-node budget exceeded')
```

`requested_nodes` は所有者の active な job（補助 job も含む）それぞれの要求ノード数（どれも 1）を合計するので、submit 補助の gate 時点では「自分以外の自分の job は 1 本まで」が条件になる。
00007 の gate が見た future view には capacity job 265796 と観測補助 265797 の 2 本があり、2 + 1 = 3 > 2 で落ちた。
driver の finalize が使う `live_gate` も同じ数え方で、こちらは submit 補助が終わった後に「他の job + 1 ≦ 2」を要求する。
v13 の直列運用では補助 job が常に 1 本だったのでこの制約は表に出なかった。
driver の `physical_host_count_v1`（物理ホスト数）は別の gate で、こちらは満たしていた。

修正は driver 側だけで、凍結 script は触っていない。
`pdriver.py`（SHA-256 `36c0a6dc…ac70`）に「凍結予算の hold」を入れた。

- submit 補助は、自分以外の自分の PBS job（実行中の科学 job + prepared/submitted の補助 job）が 1 本以下のときだけ出す。
- submit action が生きている間（policy から finalize まで）、他の補助 job は自分以外の自分の job が 0 本のときだけ出す。
- hold 中は journal に `waiting_for_frozen_budget` を記録する。

単体テストに hold の 3 件を足して 12 件がローカルとクラスタで成功した。
失敗した action 00007 は `reconcile_failed_submit.py` で手動退役させた（journal で `done` と `abandoned`、root は orphans へ、task は `pending` に戻す）。
科学側の run root には `timing.sh` だけが書かれており、原本 script は同一内容なら再利用するので、再試行は同じ root で安全である。
15:42 に `--resume` で再開し（PID 3630470）、直後に c0t2e1 BAR capacity の submit 補助 00008（265799）が出て、c0t2e0 BAR main の回収補助 00009 は hold に入った。

### 改訂した見込み

凍結予算のため、科学 job 1 本あたりの周期は「max(実行中 job の残り時間, 回収 33 分 + submit 14 分または 45 分)」になる。
capacity なら約 47 分、main なら max(実行時間, 78 分) で、v13 の「実行時間 + 78 分」に対して 1.5 倍程度の短縮にとどまる。
条件あたりでは c0 の実績に当てはめて 4.2〜4.6 時間で、c0t2e1 の残りが約 5.5 時間、c2 の 6 条件が c0 と同程度なら約 26 時間である。
全件 terminal は 10/28 未明、report 段を含めて 10/28 朝の見込みで、c2t0e0 の main が終わった時点で見直す。

### 18:15 の観測（再開から 2.5 時間）

再開後の driver は error を増やさず、hold の規則どおりに動いている。

| 時刻 | 出来事 |
|---|---|
| 15:57 | c0t2e1 BAR capacity を投入（265800） |
| 16:13 | c2t0e0 MC capacity を投入（265802、実行 7 分）。submit が終わった瞬間に hold 中の回収補助 3 本を 2 台目へ出した |
| 16:36 | c2t0e0 BAR capacity を投入（265808、実行 8 分） |
| 17:24〜17:29 | c0t2e1 と c2t0e0 の capacity 計 4 件が terminal |
| 17:25 | c0t2e1 BAR main の submit 補助 00020 を作成。finish 補助 2 本が残っていたため 1 分 hold |
| 18:11 | c0t2e1 BAR main を投入（265817）。submit 補助は 45 分 |
| 18:12 | c2t0e0 MC main の submit 補助 00021 を開始（qsub は 18:57 ごろ、着地は 265817 の終了後） |

この時点で capacity は 24 件中 14 件、main は 24 件中 10 件が terminal で、main 1 本が実行中、1 本が submit 中である。
残りは capacity 10 件と main 14 件で、c2 の capacity は c0 と同じ 7〜8 分だった。
main の投入が eligibility の順（capacity が terminal になった順）で進むため、c0t2e1 MC main は c2t0e0 MC main の後になる。
見込みは変えない。c2 の main の実行時間は c2t0e0 MC main（19 時台に着地）で初めて分かる。

### 19:50 の観測（c2 の main は短い）

| 時刻 | 出来事 |
|---|---|
| 18:51 | c0t2e1 BAR main（265817）が PBS で終了（39 分 40 秒） |
| 18:59 | c2t0e0 MC main を投入（265819）。27 分 36 秒で終了、walltime 30 分 |
| 19:45 | c0t2e1 MC main を投入（265821）。walltime 13 時間、予測 22,415 秒なので実際は 6.5 時間前後で 10/27 02 時ごろ終了の見込み |
| 19:45 | c2t0e0 BAR main の submit 補助 00025 を開始 |

c0t2e1 BAR main と c2t0e0 MC main の回収補助は submit 00025 が生きている間 hold で、20:30 ごろから回収に入る。
main は 24 件中 10 件 terminal、2 件が PBS 終了済みで回収待ち、1 件実行中、1 件 submit 中である。

### walltime 下限の問題（凍結 policy の見落とし）

凍結 policy の walltime は `max(1800, 1800 × ceil((2 × 予測 + 600) / 1800))` 秒で、予測は「ceil(192 / 21) × task 秒 + 192 × artifact 秒 + job overhead」である。
job overhead は capacity job で測った約 430 秒だが、main では pool の外に 1,550〜1,854 秒かかっている。
内訳は起動から execution-intent まで 11 分（closure の再検証）、native preflight 4 分、pool 終了から summary まで 11.5〜12.6 分で、submit 補助の 45 分と同じ再検証が job の中でも走っている。
このため予測が 600 秒以下で 30 分枠に入った main は、task がほぼ 0 秒でも 26〜31 分かかり、walltime 切れの瀬戸際になる。

| main | walltime | 実績 | pool | pool 外 |
|---|---|---|---|---|
| c0t0e0 BAR | 30:00 | 29:52 | 149 秒 | 1,640 秒 |
| c0t0e1 MC | 30:00 | 28:13 | 113 秒 | 1,578 秒 |
| c2t0e0 MC | 30:00 | 27:36 | 64 秒 | 1,590 秒 |
| c0t0e0 MC | 30:00 | 26:53 | 29 秒 | 1,582 秒 |

c0t0e0 BAR main（10/25）は残り 8 秒で終わっており、これは幸運であって設計ではない。
予測が 600 秒を超えると 1 時間枠以上になり、最悪でも「予測 + 1,424 秒」が walltime を下回るので安全である。
30 分枠に入る条件は MC で task 約 17 秒以下、BAR で約 15 秒以下である。
残りの main のうち該当しうるのは c2t0e1 MC だけで、c0t0e1 MC の task は 10.5 秒、c2 は t0e0 で c0 の 1.8〜2.2 倍だったので 1 時間枠に入る見込みが高いが、c2t0e1 MC capacity が terminal になるまで確定しない。
c2t0e0 BAR main は予測 689 秒で 1 時間枠である。

walltime で killed になった main は、凍結 script の `_completion` が「failed main execution is not capacity evidence」で拒否するので driver はその finish action で止まり、同じ capacity から同じ 30 分枠が再計算されるため再投入しても同じ危険がある。
救済には凍結 policy の下限（1,800 秒）か overhead 項の変更が要り、これは所有者の判断である。
c2t0e1 MC capacity が terminal になった時点で予測秒数を計算し、30 分枠なら main の投入前に報告する。

21:41 に c2t0e1 MC capacity（265828、8 分 10 秒、F/0）が終わり、task は 23.8 秒と 28.7 秒、予測 748 秒で 1 時間枠に入った。
c0t0e1 MC の 10.5 秒に対して 2.7 倍である。
これで残りの main に 30 分枠へ入るものはなく、walltime 切れの危険は残りの行には及ばない。
凍結 policy の下限の見落とし自体は、将来の再計測や別条件のために所有者へ報告する事項として残す。

### 23:37 の観測（c2t0e1 の capacity 2 件が終了）

| 時刻 | 出来事 |
|---|---|
| 21:41 | c2t0e1 MC capacity（265828）が 8 分 10 秒で終了 |
| 22:22 | c2t0e1 BAR capacity（265834）を投入、8 分 55 秒で終了 |
| 23:12 | c2t0e1 MC capacity が terminal、c2t0e1 MC main の task が pending に入った |
| 23:28 | c2t1e0 MC capacity（265837）を投入 |

この時点で terminal は 48 件中 28 件、main は 24 件中 13 件 terminal である。

稼働を見て分かった driver 側の性質を 3 つ記録する。
submit action は車線が空いた時点の pending 先頭で作られ、hold 中に新しく pending に入った main を追い越さないので、c2t0e1 MC main の前に c2t1e0 MC capacity の submit（22:31 作成、23:12 まで hold）が入った。
`schedule()` は state 上の実行中科学 job が 2 本以上だと submit を作らず、PBS では終了済みでも observe が済むまで実行中と数えるので、observe の hold がそのまま submit の遅れになる。
capacity job は 2 CPU でも `mem=340gb` を要求するため node を memory で埋め、main と capacity が 1 本ずつ走る 8 分間は補助 job を置ける node がなく `multiple_full_node_children_running` で待つ。
いずれも正しさには影響せず、遅れは数十分の単位なので driver は変更しない。

### 10/27 01:48 の観測（c0t2e1 MC main が終了）

| 時刻 | 出来事 |
|---|---|
| 00:26 | c2t0e1 MC main（265840）を投入。30 分 42 秒で終了、walltime 1 時間 |
| 01:22 | c0t2e1 MC main（265821）が 5 時間 37 分で終了（予測 6.5 時間より短い） |
| 01:38 | c2t1e0 BAR capacity（265845）を投入、8 分で終了 |
| 01:40 | c2t0e1 BAR capacity が terminal、c2t0e1 BAR main が pending に入った |

c2t0e1 MC main の 30 分 42 秒は、30 分枠に入っていれば walltime 切れになっていた長さで、前節の判定が実際に効いた。
terminal は 48 件中 29 件、main は 24 件中 13 件 terminal で、2 件が finish 中、c0t2e1 MC main が observe 中である。
補助 job の上限 `MAX_HELPERS = 3` は submit action を新しく作るときにだけ効き、observe と finish は必要な分だけ作られるので、この時点で finish 2 本と observe 2 本の計 4 本が同時に走った。
PBS の予算に関わるのは submit 補助だけなので、これは問題ではない。

### 10/27 04:00 の観測と pending 順の変更

| 時刻 | 出来事 |
|---|---|
| 02:20〜02:32 | c2t1e0 の capacity 2 件が terminal |
| 03:05 | c2t0e1 BAR main（265853）を投入、46 分 3 秒で終了 |
| 03:49 | c2t1e0 MC main（265855）を投入 |
| 03:51 | c2t1e0 BAR main の submit 補助 00050 を開始 |

terminal は 48 件中 33 件、main は 24 件中 15 件 terminal である。
残りは capacity 6 件（c2t1e1、c2t2e0、c2t2e1）と main 9 件で、このうち c2t2e1 MC が全体の critical path になる。

c2 の capacity の task 時間は c0 の 1.7〜2.8 倍で（MC t0e0 2.2 倍、t0e1 2.5〜2.8 倍、t1e0 1.7〜2.1 倍）、c0t2e1 MC の 2,198 秒から c2t2e1 MC の task は 4,800 秒前後と見込まれる。
凍結 policy では予測 × 2 + 600 秒が 24 時間を超えると 192 replicate を分割するので、c2t2e1 MC main は 168 + 24 の 2 partition になり、part0 だけで pool 10.7 時間、全体で 11 時間強かかる。
capacity 自体も 2 task 並列で 1.5 時間かかる。
driver の pending 順は state の並び（c2t1e1 → c2t2e0 → c2t2e1）だったので、c2t2e1 MC capacity の投入は 8〜10 時間後になり、全件 terminal は 10/28 未明から朝にずれる見込みだった。

そこで driver の `schedule()` の並べ替え key を `pending_priority()` に替えた。
main が capacity より先なのは変えず、同じ mode の中では identity の target、epsilon が大きい順、同じ identity なら MC を BAR より先にする。
科学 job の内容や凍結 script には触れず、投入する順番だけが変わる。
単体テスト `test_costliest_capacity_submitted_first` を足して 13 件がローカルとクラスタで成功した（新版 SHA-256 `bfa08fd8…8fc5`）。
入れ替えは `swap_pdriver.sh` が行う。submit 補助が PBS にいない、共有ロックがない、journal の snapshot 間隔が 28 秒以上（driver が待機中）という条件が揃った直後に SIGTERM で止め、`pdriver.py` を差し替えて `--resume` する。
c2t2e1 MC capacity を次に投入できれば、critical path は 14.5 時間程度で全件 terminal は 10/27 夜の見込みに戻る。

04:51:59 に旧 driver が c2t1e0 BAR main（265857、04:37）に続けて c2t1e1 MC capacity（265859）を旧順で投入し、その finalize 直後の 04:52:31 に `swap_pdriver.sh` が条件を満たして停止、04:52:39 に新版（SHA-256 `bfa08fd8…8fc5`、PID 3871009）で `--resume` した。
引き継いだ action は observe 2 本で、error file は増えていない。
次の submit から新しい順になり、c2t2e1 MC capacity が先に出る。

### 10/27 06:05 の観測（新しい順での最初の投入）

| 時刻 | 出来事 |
|---|---|
| 05:05 | c2t1e1 MC capacity（265859、14 分）が PBS で終了し、observe 3 本が 2 台目に乗った |
| 05:10 | 同 capacity が terminal になり、driver が pending 先頭として c2t2e1 MC capacity の submit 補助 00054 を作った |
| 05:17 | 他の自分の job が 1 本になった時点で 00054 を投入（凍結予算 hold どおり） |
| 05:31 | c2t2e1 MC capacity（265864）を 1 台目に投入、即時に実行開始。submit 補助は 14.5 分 |
| 05:32〜05:56 | finish 3 本と observe 1 本を 2 台目に置いた。5 本目の finish 00059 は 13 分待った |
| 06:02 | c2t1e0 MC main が terminal |

pending 順の変更は意図どおりに効き、旧順なら 8〜10 時間後だった c2t2e1 MC capacity が再起動の 39 分後に出た。
06:03 時点で terminal は 48 件中 34 件（capacity 18、main 16）、回収中が c2t1e1 MC capacity と c2t0e1 BAR main と c2t1e0 BAR main、実行中が c2t2e1 MC capacity、pending が capacity 4 件（c2t1e1 BAR、c2t2e0 MC/BAR、c2t2e1 BAR）である。
error file は増えていない。

補助 job の同時数には memory の上限がある。
補助 job は 1 本 96 GB を要求するので、2 台目に 4 本乗ると 5 本目は `waiting_for_capacity`（Owner physical-host resource ceiling exceeded）になり、1 本終わるまで待つ。
今回の 00059-finish がその例で、driver の上限 3 は submit 作成時だけに効くため、observe と finish が重なるとこの memory 上限のほうが先に効く。
待ち時間は十数分なので、driver は変えない。

c2t2e1 MC capacity は 1.5 時間程度で 07:00〜07:15 に終わり、observe と finish と main の submit 補助（45 分）を経て、main part0 の投入は 08:45〜09:15 の見込みである。
part0 は 11 時間前後なので 10/27 20:00〜20:30 に終わり、回収を含めて 21:00〜21:30 に terminal になる。
part1（24 replicate、pool 2.7 時間）と残りの capacity 4 件と main 6 件は submit 車線で合計 6 時間程度なので、part0 の実行中に 2 台目で消化できる。
全件 terminal は 10/27 21〜22 時、report 段を含めて 10/28 未明の見込みに変わりはない。

06:15〜06:27 に c2t0e1 BAR main、c2t1e1 MC capacity、c2t1e0 BAR main が terminal になり（48 件中 37 件、capacity 19、main 18）、新しい順の 2 番目として c2t2e1 BAR capacity（265871）を 06:41 に 2 台目へ投入した。
その submit 補助 00060 は、他の自分の job（finish 2 本）が終わるまで `waiting_for_frozen_budget` で 12 分待ってから出ている。
これで 2 台とも mem=340gb の capacity が占め、MC capacity（265864）が 07:05 ごろに終わるまで補助 job は置けない。
BAR capacity は task が 150 秒前後なので 15 分程度で終わる。

### 10/27 07:33 の観測（c2t2e1 の capacity 2 件が終了）

| 時刻 | 出来事 |
|---|---|
| 06:52 | c2t2e1 BAR capacity（265871）が 11 分で PBS 終了。同時に pending 先頭の c2t1e1 MC main の submit 補助 00062 を投入 |
| 06:57 | c2t2e1 MC capacity（265864）が 86 分で PBS 終了（見込み 1.5 時間どおり） |
| 07:31 | c2t1e1 MC main（265873、walltime 2 時間 30 分）を投入し、続けて c2t2e0 MC capacity の submit 補助 00064 を投入 |

c2t2e1 の capacity 2 件は PBS では終わっているが、observe 00061 と 00063 は `waiting_for_frozen_budget` で待っている。
submit action が生きている間は他の自分の job が 0 本のときしか補助 job を出せないという hold のためで、main 265873 が走っている限り 00064 の finalize（07:46 ごろ）まで observe は置けない。
その後は c2t2e0 MC capacity（mem=340gb、25〜30 分）が 2 台目を占めるので、observe は 08:15 ごろ、finish は 09:00 ごろ、c2t2e1 MC main part0 の投入は 10:00〜10:30 になる見込みで、06:05 時点の見込みより 1 時間ほど遅れる。
hold は原本 submit script の gate（他の自分の job + 1 ≦ 2）をそのまま写したものなので緩められず、driver は変えない。
全件 terminal は 10/27 22〜23 時、report 段を含めて 10/28 未明の見込みである。

### 10/27 08:34 の観測（c2t2e0 の capacity を投入）

| 時刻 | 出来事 |
|---|---|
| 07:47 | c2t2e0 MC capacity（265875）を 2 台目に投入、26 分で PBS 終了 |
| 08:13 | 2 台目が空いたので observe 3 本（c2t2e1 MC/BAR、c2t2e0 MC）を置き、4 分で 3 本とも受理 |
| 08:17 | 同じ step で c2t2e0 BAR capacity の submit 補助 00066 と finish 3 本を作成。finish 3 本は submit が生きている間 `waiting_for_frozen_budget` |
| 08:32 | c2t2e0 BAR capacity（265881）を 2 台目に投入 |

observe が 4 分で終わったのは、終わったばかりの capacity 3 件の artifact が小さいためと思われる（main の observe は 11 分）。
08:34 時点で terminal は 48 件中 37 件、回収中が capacity 3 件（c2t2e1 MC/BAR、c2t2e0 MC）、実行中が c2t1e1 MC main（265873、1 時間 2 分経過）と c2t2e0 BAR capacity、pending が c2t1e1 BAR capacity だけである。

driver は submit と finish を同じ step で作るが、submit を先に作るため finish 3 本が submit の finalize まで 15 分待った。
c2t2e0 BAR capacity は 10 分程度で終わるので、finish は 08:45 ごろに置かれ、c2t2e1 MC main part0 が pending になるのは 09:10〜09:25 の見込みである。
ただしその前に c2t1e1 BAR capacity の submit が車線を使い、main 265873 が終わるまで hold もかかるので、part0 の投入は 10:30〜11:00 になりうる。
差は 30 分程度で driver の入れ替えに見合わないので、順序は変えない。
全件 terminal は 10/27 23 時ごろ、report 段を含めて 10/28 未明の見込みである。

### 10/27 12:55 の観測（c2t2e1 MC main part0 を投入、2 台目を他ユーザーが占有）

| 時刻 | 出来事 |
|---|---|
| 08:44〜09:14 | c2t2e0 MC capacity の finish、c2t1e1 MC main の observe と finish を順に置いた |
| 09:23〜09:47 | capacity 4 件（c2t2e1 MC/BAR、c2t2e0 MC/BAR）と c2t1e1 MC main が terminal になり、48 件中 42 件 |
| 10:24 | 他ユーザーの 96 CPU job（walltime 48 時間）が 2 台目に着地 |
| 10:32 | submit 00074 が受理され、c2t2e1 BAR main0（265891、walltime 1:30）を 1 台目に投入。同じ step で c2t2e1 MC main0 の submit 00075 を作ったが、2 台目は他ユーザー、1 台目は main で埋まっているので `waiting_for_capacity`（`no_safe_helper_candidate`） |
| 11:38 | BAR main0 が 66 分で PBS 終了。1 台目が空いたので submit 補助 00075 を置いた。observe 00076 は submit が生きている間 `waiting_for_frozen_budget` |
| 12:23 | submit 00075 が 45 分で受理され、c2t2e1 MC main0 part0（265894、walltime 22:30、replicates 0〜188 の 189 本）を 1 台目に投入。part1（replicates 189〜191 の 3 本、workers 3、walltime 3:00）の submit 00077 を作ったが置き場がなく `waiting_for_capacity` |

10:35 ごろから自宅の PC からは学内ゲートウェイへの ssh が通らなくなった（TCP 接続がタイムアウトする）。
Tailscale で繋がるラボ PC からはゲートウェイに届くので、以降の観測はラボ PC 経由で行っている。
driver 自体はクラスタ常駐なので影響はなく、error file も増えていない（履歴の 1 件のみ）。

12:55 時点で terminal は 48 件中 42 件である。
残りは、c2t2e1 BAR main0（PBS 終了済み、observe 待ち）、c2t2e1 MC main0 part0（実行中、12:23 開始）、同 part1（pending）、c2t2e0 MC main0（pending、walltime 7:00）、c2t2e0 BAR main0（pending、walltime 1:00）、c2t1e1 BAR capacity（pending）と、その後に生成される c2t1e1 BAR main である。
pending の順は main 優先の規則どおり part1 → c2t2e0 MC main → c2t2e0 BAR main → c2t1e1 BAR capacity になる。

いまの律速は 2 台目を占めている他ユーザーの job である。
補助 job は 1 台目（part0 が 96 CPU を取っている）にも 2 台目にも置けず、part0 が終わるまで submit も observe も進まない。
観測 00076 が `waiting_for_frozen_budget` で待つのは submit 00077 が生きているためだが、00077 自身も置けないので、この hold によるロスは今のところない。
part0 は predicted 約 11 時間なので 23:30 ごろに終わる見込みである。

見込みは他ユーザーの job がいつ終わるかで変わる。
2 台目が空かないまま（最長 10/29 10:24 まで）だと 1 台目だけで直列に進み、part1 の submit 45 分 → part1 約 2 時間 → 回収と submit 45 分 → c2t2e0 MC main 約 3.5 時間 → 回収と submit 45 分 → c2t2e0 BAR main 約 1 時間 → c2t1e1 BAR の capacity と main で約 2 時間、となって全件 terminal は 10/28 10〜11 時、report 段を含めて 10/28 昼ごろになる。
他ユーザーの job が夕方までに終われば part1 と c2t2e0 の main を part0 と重ねられるので、全件 terminal は 10/28 03〜05 時に戻る。
policy の `allowed_vnodes` に 3 台目を加えれば他ユーザーの影響を避けられるが、計時の比較可能性に関わるので所有者の判断に委ね、driver 側では何も変えない。

### 10/28 00:02 の観測（part0 が終了、part1 を投入）

| 時刻 | 出来事 |
|---|---|
| 15:09 | 自宅から学内ゲートウェイへの ssh が回復。以降は直接接続で監視 |
| 23:08 | c2t2e1 MC main0 part0（265894）が PBS 終了。walltime 10 時間 45 分、exit 0、cput 201 時間（平均 18.8 コア）。1 台目が空いたので同じ step で part1 の submit 補助 00077 を置き、part0 の observe 00078 を作成 |
| 23:53 | submit 00077 が 45 分で受理され、part1（265900、replicates 3 本、96 CPU・mem 65gb、walltime 3:00）を 1 台目に投入。同じ step で c2t2e0 MC main0 の submit 00079 を作成したが置き場がなく `waiting_for_capacity` |

2 台目の他ユーザー job は 00:02 時点で 13 時間 37 分経過（walltime 48 時間）で、10/27 12:55 以降ずっと占有している。
part0 の実行時間 10 時間 45 分は predicted 約 11 時間どおりで、capacity 2 本からの予測は c2t2e1 でも正確だった。
observe 2 本（c2t2e1 BAR main0、part0）は submit 00079 が生きている間 `waiting_for_frozen_budget` で待つが、00079 自身も置けないので、これによるロスはない。

terminal は 48 件中 42 件のまま、実行中が part1、PBS 終了済みで回収待ちが c2t2e1 BAR main0 と part0、pending が c2t2e0 MC main0、c2t2e0 BAR main0、c2t1e1 BAR capacity である。
part1 は 3 本を workers 3 で回すので task 1 本分の約 1 時間 20 分 + 前後処理 25 分で 01:30 ごろに終わる見込みである。
その後は 1 台目だけで直列に進み、回収と submit 45 分 → c2t2e0 MC main 約 3.5 時間 → 回収と submit 45 分 → c2t2e0 BAR main 約 1 時間 → c2t1e1 BAR の capacity と main で約 2 時間、となって全件 terminal は 10/28 10〜11 時、report 段を含めて昼ごろの見込みである。
2 台目が途中で空けば、c2t2e0 の 2 本を重ねられる分だけ早まる。

### 10/28 02:23 の観測（part1 が終了、c2t2e0 MC main を投入）

| 時刻 | 出来事 |
|---|---|
| 01:34 | part1（265900）が PBS 終了。walltime 1 時間 41 分、exit 0。1 台目が空いたので同じ step で c2t2e0 MC main0 の submit 補助 00079 を置き、part1 の observe 00080 を作成 |
| 02:20 | submit 00079 が 45 分で受理され、c2t2e0 MC main0（265902、walltime 7:00）を 1 台目に投入 |

これで c2t2e1 の 4 件（MC capacity、BAR capacity、BAR main0、MC main0 の part0 と part1）はすべて PBS を抜け、critical path は c2t2e0 MC main に移った。
observe 3 本（c2t2e1 BAR main0、part0、part1）はまだ置けていない。
01:35〜02:20 の submit 補助だけが走っていた 45 分間も、凍結予算の hold が submit 補助自身を「他の自分の job 1 本」と数えるため observe は `waiting_for_frozen_budget` のままだった。
原本の gate は submit 補助以外の job が 1 本までなら通るので、submit が生きている間も補助 job を 1 本だけ許せば回収を重ねられる。
ただし残りの submit は 3 回で、得られるのは合計 1 時間前後なので、driver の入れ替えはせず所有者への報告事項に留める。

terminal は 48 件中 42 件のまま、実行中が c2t2e0 MC main、回収待ちが 3 件、pending が c2t2e0 BAR main0 と c2t1e1 BAR capacity である。
2 台目の他ユーザー job は 15 時間 58 分経過で、空く気配はない。
見込みは、c2t2e0 MC main が 06:00 ごろ終了 → submit 45 分 → c2t2e0 BAR main（約 50 分）が 07:40 ごろ終了 → c2t1e1 BAR capacity の submit 15 分と実行 10 分 → 回収 45 分 → c2t1e1 BAR main の submit 45 分と実行 50 分 → 回収 40 分、で全件 terminal は 10/28 11 時ごろ、report 段を含めて正午ごろである。

### 10/28 06:05 の観測（c2t2e0 MC main が終了、回収がまとめて進む）

| 時刻 | 出来事 |
|---|---|
| 05:24 | c2t2e0 MC main0（265902）が PBS 終了。walltime 3 時間 4 分、exit 0、cput 51.6 時間（平均 16.9 コア）。1 台目が空いたので同じ step で observe 3 本（c2t2e1 BAR main0、part0、part1）を置き、MC main の observe 00081 を作成 |
| 05:36 | observe が 11 分で受理され始め、finish を順に置いた。補助 job は 1 台目に最大 3 本並走 |
| 05:59 | part1 と c2t2e1 BAR main0 が terminal（48 件中 44 件）。c2t2e0 BAR main0 の submit 00086 を作成したが、finish 2 本（part0、c2t2e0 MC main）が走っているので `waiting_for_frozen_budget` |

submit 00086 が 05:24 ではなく 05:59 に作られたのは、`schedule()` が PBS を抜けて未 observe の task を実行中として数え、2 件以上あると submit を作らないためである。
05:24 の時点では未 observe が 4 件あった。
submit 補助は他の自分の job が 1 本以下になるまで出せないので、finish のどちらかが終わる 06:25 ごろに置かれ、c2t2e0 BAR main の投入は 07:10 ごろになる。

terminal は 48 件中 44 件、回収中が part0 と c2t2e0 MC main、pending が c2t2e0 BAR main0 と c2t1e1 BAR capacity である。
2 台目の他ユーザー job は 19 時間 40 分経過で、まだ空かない。
見込みは、c2t2e0 BAR main が 08:00 ごろ終了 → c2t1e1 BAR capacity の submit と実行で 08:25 → 回収 25 分 → c2t1e1 BAR main の submit 45 分と実行 50 分で 10:25 → 回収 40 分、で全件 terminal は 10/28 11 時ごろ、report 段を含めて正午ごろのままである。

### 10/28 08:25 の観測（c2t2e0 BAR main と c2t1e1 BAR capacity が終了、残りは main 1 本）

| 時刻 | 出来事 |
|---|---|
| 06:10 | part0 の finish が受理され terminal。同時に c2t2e0 BAR main0 の submit 00086 を 1 台目に置いた |
| 06:21 | c2t2e0 MC main0 が terminal（48 件中 46 件） |
| 06:56 | submit 00086 が 46 分で受理され、c2t2e0 BAR main0（265912、walltime 1:00）を 1 台目に投入。c2t1e1 BAR capacity の submit 00087 を作成したが、1 台目は 96 CPU の main で満杯、2 台目は他ユーザー job で `waiting_for_capacity`（48 分） |
| 07:44 | BAR main0 が PBS 終了。walltime 47 分 39 秒、exit 0、cput 4 時間 39 分（平均 5.9 コア）、余裕 12 分。submit 00087 を置き、observe 00088 を作成 |
| 07:59 | submit 00087 が 14 分 32 秒で受理され、08:00 に c2t1e1 BAR capacity（265914、`1:ncpus=2:mem=340gb`）を 1 台目に投入 |
| 08:09 | capacity が 9 分 5 秒で終了（exit 0）。observe 00088（BAR main0）と 00089（capacity）を同時に置いた |
| 08:13 | observe 00089 が 3 分 40 秒で受理され、finish 00090 を置いた |
| 08:21 | observe 00088 が 11 分 33 秒で受理され、finish 00091 を置いた |

observe 00088 は 07:44 から 08:09 まで待った。
前半は submit 00087 が生きている間の `waiting_for_frozen_budget`、後半（08:00 以降）は `waiting_for_capacity` で、capacity job が `mem=340gb` を予約するため 350 GB のノードに 96 GB の補助 job が同居できない。
つまり capacity job の実行中はその台に補助 job を置けず、2 台目が塞がっている今回の配置では capacity の 9 分がそのまま直列に足された。

06:56 から 07:44 の 48 分も同じ構図で、main が 1 台目を占める間は次の submit 補助を置く場所がなかった。
2 台目が空いていれば submit は main と並走し、capacity の投入は 07:12 ごろに前倒しできたはずである。

terminal は 48 件中 46 件、finish 2 本（c2t2e0 BAR main0、c2t1e1 BAR capacity）が走っている。
残りは c2t1e1 BAR main の submit（45 分）、実行、observe と finish だけである。
2 台目の他ユーザー job は 22 時間経過、walltime 48 時間なので今回の実行中には空かない。
見込みは、finish が終わる 08:45 ごろに submit 00092 を置き、main の投入が 09:30 ごろ、実行 50 分で 10:20 ごろ終了、回収 40 分で全件 terminal は 11 時ごろのままである。

### 使える vnode の allowlist の確認（10/28 08:00）

side agent から「policy の allowed_vnodes は 1 台目と 012 で、空いている 012 を使い損ねているのではないか」という指摘があったので、effective な policy を確かめた。

- driver が読む `20261025-finite-tail-census-recovery-v13/config.json` は `policy` として `20261025-census-active-node-v13/policy.json` を sha で指し、その `allowed_vnodes` は 1 台目と 2 台目（008 と 009）の 2 台である。
- 各 action の `physical-policy/dynamic-policy.json` も `allowed_vnodes` と `candidate_vnodes` に同じ 2 台を記録し、`base_policy` は census-active-node-v13 を指す。
- 008 と 011 または 012 を書いた `20261025-low-parallel-dispatch-policy-v2..v6/policy.json` は古い版で、v13 の鎖からは参照されていない。
- 過去の補助 job と capacity job の `exec_host` はすべて 008 か 009 で、012 に置かれたものはない。

したがって 012 が空いていたのは policy の設計どおりで使えなかったのであり、driver と gate の食い違いではない。
2 台目を他ユーザーが占有したことによる遅れの説明はそのまま成り立つ。

2 ノード上限は allowlist の長さとは独立に効いている。
`physical_node_capacity_v1/capacity.py` が `max_physical_nodes: 2` と「legacy host 1 台 + 固定の new-work host 1 台」を要求し、原本の submit gate も自分の job 数で others+1 ≤ 2 を要求する。

所有者の決定（10/28）: 次回の実行では新しい policy 版で `allowed_vnodes` を使えるノードに広げ、2 ノード上限は維持する。
候補は 008、009、010、012、019、020、031、032、039、040、042（同一構成の 350 GB 機）で、043 は 1 TB 機なので計時の均質性を優先するなら外す。
policy は config に sha で固定され、frozen gate も `base_policy` の sha を検証するので、変更には新しい policy 版、config の sha 更新、driver の再起動が要る。
今回の実行は残りが 1 台目で直列に進む 1 本だけなので適用しない。
dispatcher が候補を順に試す実装の細部は未確認で、policy 版を作る段で読む。

### 10/28 11:04 の観測（48 件すべて terminal、report 段へ）

| 時刻 | 出来事 |
|---|---|
| 08:45 | c2t2e0 BAR main0 の finish が受理され terminal |
| 08:54 | c2t1e1 BAR capacity の finish が受理され terminal（48 件中 47 件）。同じ step で c2t1e1 BAR main0 の submit 00092（265921）を 1 台目に置いた |
| 09:40 | submit 00092 が 46 分で受理され、c2t1e1 BAR main0（265923、walltime 1:30）を 1 台目に投入 |
| 10:29 | main0 が PBS 終了。walltime 49 分 26 秒、exit 0、cput 6 時間 51 分（平均 8.3 コア）、余裕 40 分。observe 00093 を置いた |
| 10:41 | observe が 11 分で受理され、finish 00094 を置いた |
| 11:04 | finish が 22 分で受理され terminal。driver が `all_jobs_terminal` を記録し、`independent-execution/completed.json` を書いた |
| 11:04 | driver が続けて report 役を開始。`pipeline-state/parallel-flow-v13/low_partition_report_preparation_v2/` に intent を書き、PBS の action job 265927 が 1 台目で走り始めた |

48 件（capacity 24、main 24、c2t2e1 MC main は part0 と part1 の 2 分割）がすべて成功で terminal になった。
最後の 1 本は submit 46 分、実行 49 分、observe 11 分、finish 22 分の合計 2 時間 10 分で、1 台だけで直列に進む場合の 1 条件あたりの固定費がそのまま出ている。

残りは report 役 3 つ（report_preparation_v2、report_job_v2、final-report）で、driver が旧 controller と同じ `run.py` を役ごとに順に呼ぶ。
各役の返り値と標準出力は `parallel-flow-v13/<役>/response.json` と `stdout.log` に残り、3 つとも返り値 0 なら `parallel-flow-v13/completed.json` が書かれて driver が終了する。
report 役の所要時間は旧 controller の記録がないので未知で、PBS job を介する分は 1 役あたり 15〜45 分と見ている。

### 10/28 11:15 の観測（report 役の最初の段で失敗、driver 終了）

| 時刻 | 出来事 |
|---|---|
| 11:04 | driver が report 役 `low_partition_report_preparation_v2` を開始。outer の `run.py` が action `low_partition_report_preparation_v2/00001-prepare-role` を作り、補助 job 265927 を 1 台目に置いた |
| 11:15 | 補助 job が exit 1 で終了（walltime 10 分 44 秒）。`run.py` は「Finite action failed or unknown; preserve original job and output」で返り値 1、driver は `run_tail` の `check_returncode` で CalledProcessError を投げて終了した |

driver の journal には error ファイルは増えていない（`run_tail` は `Cluster.run` の try の外で、traceback は driver の resume log に残る）。
science job はすべて terminal のままで、PBS に自分の job は残っていない。
失敗した action の原本 `pbs/` と、report 役の journal `pipeline-state/parallel-tail-v13/report-preparation/`（intent-v2、preparation-intent、remote.py、stderr.log、error.json、response.json）はそのまま保存した。

**失敗箇所**: 補助 job の中で走った `20261025-low-parallel-report-inputs-v9/preparation.py` が `report.prepare(...)` を呼び、凍結された評価 report script `20261025-finite-tail-report-environment-v1/cluster_scripts/tile_low_noise_timing_evaluation_report.py` の `reference_evidence` が

```
ValueError: selection and evaluation WSS audit differ
```

で止まった。
この検証は、selection の `calibration_bindings[i].reference_audit_digest` が、参照 audit `20261018-tile-low-analysis-v7/runs/weight-reference-audit/conditions/<i>.json` の `report` の `c.digest` と一致することを 12 条件すべてに要求する。

**原因（確定）**: merged selection `20261025-low-parallel-front-v6/merge-parallel-v2/selection.json` の 12 bindings のうち、case 2 の 3 件（条件 9、10、11、reader = staged）だけが参照 audit の digest と一致し、残り 9 件（条件 1、2、3、5、6、7、13、14、15、reader = recovered / portable_mixed / portable_condition）は一致しない。
9 件の digest は、各 worker の reader が最終 report（例: `20261019-tile-low-bar-recovery-v2/runs/case0-target0-report-v1/report.json`）に埋め込まれた `reference_audit` を `c.digest` したものである。
その `reference_audit` と参照 audit の `report` を比べると、`source_sha256` 以外のすべての key と値は同一で、`source_sha256` も 10 個の sha256 値は同一だが、path が `20261018-tile-low-analysis-v11/cluster_scripts/` と `20261018-tile-low-analysis-v7/cluster_scripts/` で異なる。
つまり数値内容は同一で、差は参照 audit の source 閉包を記録した**ディレクトリ名だけ**である。
評価 report script は source の移設を `source_binding.reference_sources(... saved_root, current_root ...)` で別途扱えるが、binding の digest 照合は生の `report` をそのまま digest するので、移設後の path で digest した recovered 系の bindings を受け付けない。

**driver との関係**: `run_tail` は旧 controller と同じ `run.py` を同じ config で役ごとに呼んだだけなので、旧 controller でも同じ段で同じ失敗になる。
v13 の鎖は merge を「Fixed snapshot accepted after successful merge PBS completion」として受理したが、report 段は merged selection では一度も通っていなかった（`report-plan.json` はクラスタのどこにもなく、`20261022-low-timing-report-v2-tests-v2` の 21 テストは fixture のみ）。

**副作用**: `preparation.py` は `request["output_root"]`（`20261025-low-parallel-report-inputs-v9`）を `mkdir(exist_ok=False)` で作ってから失敗したので、同じ config で再実行しても `FileExistsError` になる。
再実行には新しい output_root（v10）を指す config 版、config の sha 更新、driver の再起動（`--resume` は science が全件 terminal なので即 `run_tail` に入る）が要る。

**所有者の判断が要る選択肢**（凍結 script の変更、または selection の作り直しを含むので、ここでは実施しない）:

1. 評価 report script の binding 照合を、`source_sha256` の path を `saved_root → current_root` で正規化した上で digest 比較するように改める（凍結 script の変更）。数値内容が同一であることは確認済みなので、科学的な意味は変わらない。
2. recovered / portable の reader が `reference_audit_digest` を生の参照 audit（v7 path）で digest するように改め、merge をやり直す（merge-parallel-v3）。12 worker の再実行は不要で、selection の再構成だけで済むかは merge 側の契約次第である。
3. report 段を v13 の鎖から切り離し、48 件の state と row digest を入力に別経路で final report を作る。

いずれも新しい policy 版・config 版と driver の再起動を伴うので、allowlist の拡張（上記）と同じ機会にまとめるのが自然である。

### 10/28 15:10 の対応（所有者決定: 別経路で同じ script に 1 箇所の delta）

所有者は選択肢 1 を選び、その実現方法として「v13 の凍結鎖は触らず、同じ report script に 1 箇所だけ delta を当てた写しを新しい report 環境 v2 として pin し、report 3 役を別経路で明示 pin つきで実行する」（1'）を選んだ。
凍結鎖の内側で実現するには、report script の sha が effective.py → relocation.py → outer-v9 → merge-relocation-v1 → cross-host-v2 → census-recovery-v13 と 5 層の authority に pin され（config の `source_pins` は約 120 本）、各層の builder・テスト・native 受理 PBS job（10 本前後）を v2 として作り直す必要があると分かったためである。

**delta の内容**（`output/report_relocation_route_v1/binding_delta.py`、純粋な文字列置換で、復元して原本と一致することを検証する）:

- 対象は v1 の `tile_low_noise_timing_evaluation_report.py` の `reference_evidence` 内の binding 照合 1 箇所のみ。
- 置換後は、生の audit report の digest に加えて、`source_sha256` を同関数内で既に計算済みの移設後 source 一覧 `reference_sources['sources']` に差し替えた report の digest も受理する。
- それ以外の行は一切変えない（`diff` は 1 行 → 6 行の置換のみ）。

**report 環境 v2**: `20261028-finite-tail-report-environment-v2/`（v1 の `report-environment.json` から `import_origins`・`import_prepend`・`resolved_sources`・`source_sha256` の 4 項目だけを差し替え、v1 の delta と同じ規則）。
report script sha `5fa48f69…`、environment sha `18449f85…`、`derivation.json` に原本 pin・delta の old/new 本文・復元検証を記録した。

**純粋検証**: login node で環境 v2 を bootstrap し、失敗した v9 の `prepared/report-config.json` の `reference` と `selection` に対して `reference_evidence(full=False)` を呼んだところ、12 bindings すべてを受理して 36 秒で返った（書き込みなし）。

**別経路の実行**（`20261028-report-relocation-route-v1/`、script は `output/report_relocation_route_v1/`）:

| 段 | 方法 |
|---|---|
| preparation | v13 driver が実行した preparation program（journal の `remote.py`）の PAYLOAD だけを書き換え（入力 root を `20261028-low-parallel-report-inputs-v10`、environment を v2 pin）、PAYLOAD 行以降は byte 単位で同一。受理済みの補助 submit helper（`physical_aux_submission_v1/submit.py`）経由で policy v3（1 台目 + 011）の下に投入し、2 物理ノード上限をそのまま適用。15:08 に job 265936 が 011 で開始 |
| 回収 | `collect_preparation.py` が凍結 driver と同じ検査（method_rows 48、cohort_rows 24、qsub 未実行、prepared 4 ファイルの pin 一致）で `preparation/accepted.json` を書く |
| report job | 原本 `20261023-low-partition-report-job-v1/report_job.py` を無改変で使い、`runs/report-all24-relocation-v1` を root に `prepare` → 凍結 gate（自分のノード数 + 1 ≤ 2、共有 lock なし、controller なし）→ `submit`（原本が共有 lock を取って qsub、1 CPU・32 GB・walltime 24 h）→ observe → `seal` |
| 完了 | sealed descriptor と env v2・derivation・preparation の pin を `report-job/completed.json` に記録。final report は `runs/report-all24-relocation-v1/result/{report.json,report_ja.md}` |

v13 の `parallel-flow-v13/completed.json` は書かない（driver の完了記録を偽装しない）。
policy v3 を使ったのは、15:00 時点で 1 台目・2 台目・012 がいずれも他ユーザーの job で埋まり、受理済み policy の中で空きノード（011）を含むのが v2/v3 だけだったためで、Codex の受理 job が policy v4 で 012 を使ったのと同じ扱いである。

### 10/28 15:25〜18:20 の経過（report job の投入と進捗の読み方）

preparation 補助 job 265936 は 13 分 14 秒で終わり、`collect_preparation.py` の検査（method_rows 48、cohort_rows 24、qsub 未実行、prepared 4 ファイルの pin 一致）を通って `preparation/accepted.json`（sha `81578075…`）を書いた。

**login host での runner は失敗した**（15:25）。
原本 `report_job.py` の `prepare` は `validate` → `report.inputs` → `partition_check` を通り、そこで `ValueError('partition proof IPC requires PBS')` を投げる。
つまり prepare・submit・seal の 3 段はすべて PBS job の中で走らせる必要がある（凍結 driver の finite actions がそうしていたのと同じ）。
この試行の記録は `report-job-attempt1-login/` に移し、途中まで作られた root `runs/report-all24-relocation-v1` は `control.json` だけを残して使わない。

**PBS 段の orchestrator に組み直した**（`pbs_step.py` と `orchestrate_report_job.py`、root は `runs/report-all24-relocation-v2`、記録先は `report-job-v2/`）。

| 段 | 補助 job | 所要 | 内容 |
|---|---|---|---|
| prepare | 265937（011、1 CPU・16 GB） | 10 分 03 秒 | `report_job.prepare(job_root, accepted)`、`prepared.json` に control の pin |
| submit | 265938（011） | 30 分 29 秒 | 凍結 gate（自分の job のノード数 + 1 ≤ 2、controller なし）→ `report_job.submit` が共有 lock を取って qsub。30 分の大半は lock 取得後の入力再検証 |
| report job | 265940（011、1 CPU・32 GB・walltime 24 h） | 16:14 開始 | 原本 `report_job.py compute` |
| seal | report job の終了後に投入 | 15 分見込み | `report_job.seal` → `report-job-v2/completed.json` |

補助 job はいずれも受理済みの補助 submit helper 経由で、policy v3（1 台目 + 011）の空きノードに置いた。
orchestrator は login host で nohup 実行し（`orchestrate.log`、`observations.jsonl`）、report job を 2 分おきに観測して terminal になれば seal を投入する。
失敗時は `error.json` を書いて止まり、自動再投入はしない。

**report job の進捗の読み方**。
計算ノードには ssh できず、`report.out`/`report.err` は終了まで空のままなので、各実行 root の raw ファイルの最終アクセス時刻（atime）を進捗の代わりにした。
job は 16:14 に開始し、10 分の再検証（`validate`）のあと 16:24 に `execution.json` を書き、入力の再読込と WSS 参照の raw 再 hash を経て 16:28 ごろから 12 条件を順に処理している。
1 条件あたり MC capacity → MC main → BAR capacity → BAR main の 4 root を読み、main root は 12〜15 分、capacity root は 4〜6 分、合計で 1 条件 約 37 分かかる。

| 時刻 | 読み終えた root |
|---|---|
| 17:10 | c0t0e0 の 4 root |
| 17:47 | c0t0e1 の 4 root |
| 18:13 | c0t1e0 の BAR capacity まで |

遅いのは hash ではない。
raw の総量は 49 root で 5.7 GB、14,752 ファイルにすぎず、hash だけなら数分で済む。
時間を使っているのは凍結 script の `load_execution` → `execution.completed` → `_completion` が task ごとに record を再検証する部分（成功した BAR 鎖の初期・終状態の再 decode を含む）で、root のサイズにはほぼ依存しない。
メモリは 17.9 GB で 17:00 から一定、CPU は 1 コアを 98% で使っている。

**見込み**: 12 条件 × 37 分 ≈ 7.4 時間で、計算は 10/29 0:00 ごろに終わる。
その後に入力の再検証と report 出力、seal 補助 job（約 15 分）が続くので、完了は 0:30 ごろである。

**並列化は見送った**（所有者判断、18:30）。
report 段を並列化するには、凍結 script の `run`/`load_method` の構造変更と、原本 `report_job.py` の `RESOURCE`（1 CPU・32 GB）の変更が要り、所有者が承認した「同じ script に 1 箇所の delta」の範囲を超える。
今から停止して並列版で再実行しても、実装と検証 1 時間、補助 job 3 本 55 分、再検証 16 分、並列計算 40〜60 分、seal 15 分で早くて 22:00 ごろであり、節約は 2〜3 時間にとどまる。
初回経路の失敗リスクと provenance の説明が複雑になることを考え、所有者は現状維持を選んだ。
並列版（delta v3、`RESOURCE` の変更を含む）は次回以降の改善候補として残す。

### 10/29 01:58〜02:21 の完了（report job 終了、seal の再投入、final report）

report job 265940 は 10/29 01:58 に exit 0 で終わった（walltime 9 時間 43 分、CPU 1 コア、最大 17.9 GB）。
見込みの 7.4 時間より長かったのは、後半の c2 条件のほうが root あたりの record 再検証に時間がかかったためである。
`completion.json` に `report_compute_complete: true` と出力 2 ファイルの pin が書かれ、`result/report.json`（1.85 GB、sha `79d1357d…`）と `result/report_ja.md`（8.9 KB、sha `3614ab8f…`）ができた。

**seal の 1 回目は PBS のメモリ上限で kill された**（補助 job 265949、16 GB 指定、4 分 15 秒で `mem 17810188kb exceeded limit 16777216kb`）。
原本 `report_job.seal` は入力の再検証に加えて完了記録と出力の検証を行い、prepare・submit の補助 job（16 GB で通過）より多くのメモリを使う。
kill された時点で job root には何も書かれておらず（`terminal.json`・`descriptor.json` なし）、入力も結果も変わらないので、seal の段だけを 32 GB で再投入した。

- `orchestrate_report_job.py` の `run_step` にメモリ引数を足し、`resume_seal.py` が `error.json` を `error-attempt1.json` に改名して理由を `observations.jsonl` に記録したうえで `04-seal` を投入する。
- login host の `python3` は 3.6 で `subprocess.run(capture_output=…)` が使えず、最初の起動は qstat の手前で止まった（job root や記録には触れていない）。orchestrator と同じく環境 v2 に pin された venv の python（3.11.9）で起動し直した。
- 2 回目の補助 job 265950（011、1 CPU・32 GB）は 02:11 に始まり、10 分 12 秒、最大 18.0 GB で exit 0。

**完了記録**: `report-job-v2/completed.json` に `status: report_completed`、report job 265940、seal 補助 job 265950（32 GB）、失敗した 1 回目の記録の pin、環境 v2（sha `18449f85…`）と derivation（sha `3bf7f8aa…`）の pin、出力 2 ファイルの pin を書いた。
job root には `terminal.json` と `descriptor.json` が 02:21 に書かれた。
v13 の `parallel-flow-v13/` には `completed.json` を書いていない。
自分の PBS job は残っていない。

**手元への写し**: `docs/wp/data_tile_validation_2026-10-17/low_noise_final_report_2026-10-29/`（gitignore 済み）に `report_ja.md`、`report.json.gz`（gzip 後 219 MB、展開後の sha が `completion.json` と一致）、`completed.json`、`descriptor.json`、`terminal.json` を置いた。

**final report の要点**（`report_ja.md`）:

- 選択 12 条件（case 0・2 × p ∈ {0.01, 0.003, 0.001} × ε ∈ {0.2, 0.1}）は MC・BAR とも 192/192 replicate が completed。case 1・3 は参照区間の幅が条件を満たさず（`ineligible_reference_width`）、計画どおり未選択。
- 費用比 MC/BAR（wall・CPU）は、両手法が経験的精度 gate（相対 RMSE ≤ ε）を通った 3 条件だけに出る。

| case | p | ε | wall 比 MC/BAR | CPU 比 MC/BAR |
|---|---:|---:|---:|---:|
| 0 | 0.003 | 0.2 | 2.03 | 2.04 |
| 0 | 0.003 | 0.1 | 3.03 | 3.03 |
| 0 | 0.001 | 0.1 | 29.7 | 29.7 |

- 残り 9 条件は MC か BAR のどちらかが gate をわずかに外れて `both_empirical_precision_gates_required` になった（例: case 0・p = 0.01・ε = 0.2 で BAR の相対 RMSE 0.206）。予算は相対 RMSE が ε の近傍に来るように決めているので、判定は境界で割れる。
- 区間の被覆（192 中）は MC が 178〜186、BAR が 151〜176 で、BAR の区間は過小被覆である。
- report の但し書きどおり、費用比は経験的精度 gate を通った固定設定の記述量であり、母精度や最速設定を保証しない。BAR の混合診断は未取得。

### 10/29 08:19 の補足（v13 の collect・final-report 役との差と、経路側の写し検証）

別経路で実行したのは v13 の report 3 役のうち preparation と report job（prepare → submit → seal）であり、v13 の report_job 役の末尾と final-report 役は実行していなかった。
outer `run.py` と `low_parallel_tail_v3/adapter.py` を読んで確認した両者の内容は次のとおりで、どちらも新しい科学成果物は作らない。

| v13 の段 | 内容 |
|---|---|
| report_job 役の末尾（`low_partition_report_job_v2/driver.py`） | seal 後に sealed descriptor が列挙する 9 artifact（control・submission・report.sh・terminal・descriptor・execution・completion・result の 2 ファイル）を journal の `collected/` へ写し、sha を照合して `completed.json` に `collection_verified: true`、`manifest.json` に journal 全ファイルの sha を書く |
| final-report 役（PBS action → `adapter.final_report`） | その `completed.json` の `report_completed`・`collection_verified` と `collected/result/` の sha を再照合し、小さな受領書（completion pin・reports pin・job_id）を返す。outer はそれを v13 config の sha と束ねて `finite-final-report.json` に保存する |

経路側では `collect_report_route.py` で同じ byte 検査を login host で行い（両段とも copy と hash だけで PBS 専用の IPC は使わない）、`report-job-v2/collected/`（9 artifact）、`collection.json`（`collection_verified: true`）、`final-receipt.json`、`manifest.json` を 08:19 に書いた。
`final-receipt.json` には `v13_final_report_role_executed: false` を明記した。
v13 の受領書は v13 config（原本の report script を pin）に束ねるものなので、環境 v2 を使ったこの経路では作れず、v13 journal には何も書かない。
したがって「v13 の凍結鎖としての完了」ではなく、「同じ検査を通した別経路の完了」として文書化する。

### 見込み（19:50 時点）

c2 の main は c0 より短く（c2t0e0 MC で 28 分）、残り 11 本の main の submit 補助 45 分と回収 33 分が実行時間を上回る。
submit 車線の残りは capacity 10 本 × 14 分 + main 11 本 × 45 分で約 10.6 時間、回収は submit が生きていない間に最大 3 本並列で進む。
c0t2e1 MC main が 10/27 02 時ごろまで 1 台を占めるが、submit 補助が終わって finalize する時点では補助 job が消えているので、2 台目に補助 job がいなければ別の main を 2 台目に着地させられる。
全件 terminal は 10/27 夕方から夜、report 段を含めて 10/27 夜から 10/28 朝の見込みである。

## 実メモリ確認の結果（Codex 実施分）

診断 job 265775 は F/0 で、同 job 内の合成 fixture 12 件は成功した。
対象 BAR 本計時 265772 の PBS 報告メモリは 7,608,952 kB（約 7.26 GiB）だったが、プロセス別の RSS・PSS は計算 host への SSH が失敗して未取得である。
PBS の集計範囲を断定できないため、337 GiB の予約は変更していない。
原本は `output/independent_memory_probe_v1/PBS_PROBE_2026-10-26_ja.md` にある。

## Codex が残した候補実装

いずれも `output/` 配下（git 管理外）にあり、将来の参考として保持する。

| 部品 | 作業場所 | 状態 |
|---|---|---|
| 単一 writer の実行制御 | `output/independent_tail_event_loop_v1/` | 仕様と候補実装、未受入 |
| 投入前処理と配置 | `output/independent_tail_preflight_v1/` | 仕様と候補実装、未受入 |
| 移行・実運用接続 | `output/independent_tail_migration_v1/` | 候補実装、未組立 |
| CPU 予約 | `output/independent_tail_cpu_policy_v1/` | 仕様のみ、本番の 96 CPU・337 GiB 予約は未変更 |
| report の旧新経路 | `output/independent_tail_report_routes_v1/` | 仕様のみ |
| 統合受入 | `output/independent_tail_parallel_acceptance_v1/` | PBS 試験 2 回（job 265776・265778）は fixture 側の不具合で失敗、v3（265786）の結果は未記録 |
| 同じ job 内のメモリ観測 | `output/independent_local_memory_monitor_v1/` | 仕様のみ、未実行 |
| 静的な変更案 | `output/finite_tail_census_recovery_v1/INDEPENDENT_PARALLEL_REMAINDER_PLAN_ja.md` | 直列化箇所と第一・第二段階の案 |
