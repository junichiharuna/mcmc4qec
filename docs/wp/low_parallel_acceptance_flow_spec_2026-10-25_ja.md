# 巨大メタデータ受入の PBS 隔離

既存 v8 controller と全12 worker、merge の科学的入力・実装・結果を保存したまま、新しい v9 journal へ引き継ぐ。
変更対象の flow は別 namespace に置き、実運用への切替は統合受入と旧 process の識別子付き終了確認後に行う。

## 境界

controller は巨大 merge-result/selection JSON を parse、deepcopy、serialize しない。
元の accept_terminal を変更せず 1 CPU・96 GiB・4時間の独立 qsub job 内で実行し、controller は小さい完了証跡・元 merge job ID・別の acceptance job ID・PBS 終端・artifact の stat を検証する。
この資源量は未実測の保守的予算であり、所要時間やメモリ上限内での成功を保証しない。
受入 claim、部分出力、曖昧な qsub response が存在する場合は自動再実行しない。
既存 worker terminal descriptor はそのまま採用し、未回収 worker では元 capture_terminal の streaming hash を維持する。
したがって保証は大 JSON の controller 処理禁止であり、bulk hash を一切行わない保証ではない。

## 引継ぎ

新 controller は全12 worker の既存 ledger を要求し、worker を一切再投入しない。
旧 config・起動記録・process 記録を固定し、実起動時には旧 PID と start ticks の組が live でないことを確認する。
PBS 内の shadow 構成検証のみ旧 process の稼働中も許すが、tick・投入・科学処理は呼ばない。
同じ merge root に完全な request/prepared があれば、元 config と同じ入力・12個の実 terminal 証跡・source・script・resource を照合して採用する。
不完全な request/prepared や曖昧な submission は停止し、上書きも再投入もしない。

## tail

全6 role にある巨大 JSON の検証経路を有限 PBS action へ隔離する。
軽い待受・資源検査・子 job 投入は外側に置き、大メモリ親 job が子 job 完了まで資源を保持する構成を避ける。
数学的検査、selection、seed、原データの定義は変えない。
新 tail adapter の受入完了までは新 flow の本番切替を行わない。

## 受入条件

旧 process が live、設定が変化、worker ledger が欠落、既存 merge の入力が不一致、qsub 応答が曖昧なら停止する。
既存 job を採用しても qsub 回数は増えない。
acceptance の未知・未終端・失敗では comparison/tail を進めない。
元 merge job と acceptance job を取り違えた証跡を拒否する。
controller から元 accept_terminal を直接呼ばないことを fixture で検証する。
ローカルテストは行わず、受入 fixture と actual native shadow を qsub で実行する。

## 実装と受入状況

別 namespace `output/low_parallel_flow_v7/` に実装し、qsub 265625 は F/0、82 fixture が 0.041 秒で成功した。
この受入には、旧 process 稼働拒否、全 worker 再投入禁止、部分準備の採用拒否、元 merge job と acceptance job の分離、既存 merge result を開かずに prepared を採用するケースを含む。
flow SHA-256 は `cf8918c04b7b2d96eb193acb1b986fdcdb29446a888202931498274dcbe21b5a`、launcher は `2f79f7ec4b7b082f19ea155de3503f5852960df88ab9dbf379db8abae841700b` である。
これは fixture の受入であり、実際の巨大 merge result の受入成功や資源実測ではない。
独立レビューで final-report の stdout にも無制限 JSON 読込が残っていたため、旧版を保存して `output/low_parallel_flow_v8/` に 4 MiB 上限と `read(MAX+1)` を加えた。
修正版は qsub 265626 が F/0、84 fixture が 0.041 秒で成功し、flow SHA-256 は `58ada8dedaf393d01f501a9615ee7e920146c6596989b20c1b0f67b47a21e138` となった。
launcher の SHA-256 は上記と同じで、計画する実 journal 名は v9 のままである。
新 tail の全境界受入、actual config の native shadow、本番 controller 切替はこの記録時点で未実施である。
旧 v8 controller と既存 worker/merge source は変更していない。

## Actual v9 への切替受入

上記は fixture 受入時点の記録であり、その後、finite tail の全境界 fixture・実構成・CLI受入を経て actual v9 設定を作成した。
実 config は workspace 相対 `20261025-low-parallel-controller-v9/flow-config.json`、SHA-256 は `5b44a838edcf35f9d02d119c323530ef17bab880aeb8c29e74ff3fe81c4748ed` である。
PBS265644 は F/0・壁時間1秒・標準エラー0 bytesで、実12 prepared と元 source binding を保持した shadow constructor が成功した。
この shadow は tick、worker投入、科学計算、実controller起動を行っていない。
native accepted.json は controller配置先の `pipeline-submissions/parallel-flow-native-v9/accepted.json`、SHA-256 は `1c95d2ed0ab6095cf2ef903f0fb18865a408f2e1b74387758791c83d2d0ad96d` である。

10月25日04時18分JST、統合担当が旧 v8 の PID・start ticks・command・sleep状態・子process不在を照合して停止し、旧 journal と全12 PBS jobを保持して新 v9 を起動した。
停止・起動の実施は統合担当によるもので、この文書の担当はその後の別SSH接続で生存と初回巡回を独立確認した。
新 PID は898820、start ticksは767964369で、実commandも新sourceとconfigに一致した。
launch started.json の SHA-256 は `ff09c182ad53930668b8cd2a1d2a157b3ec459795702ced6b3ee9cc8386189ef`、process.json は `2f670a0d080b822ad7c7c81210e29af0b0fbf9a36a0b9aa4cfdfcab2144ebb5c` である。
初回全12件の観測で index0〜8の9 terminalを元preparedのまま採用し、index9〜11は処理中、error記録と標準エラーは空だった。
worker結果の深い受理、並列merge、PBS内 terminal acceptance、独立計時、最終報告の完了はこの切替確認に含まれない。
巨大JSON処理の実RSS・所要時間も未測定であり、1 CPU・96 GiB・4時間の予算を完了時刻保証とは扱わない。
現行再開手順と最終成果物の確認は別途更新された再開文書・成果物監査文書を使用し、起動コマンドを繰り返さない。
