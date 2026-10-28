# 実行中 v8 の有限 private snapshot

既存の v5 保存物（qsub 265599、source 1031・metadata 75）を変更せず、新しい採取ジョブと保存先を用いる。
保存ライブラリは 25 テストを通過した snapshot_v2.py の固定原本を使い、raw/native の content read・hash を行わない。
旧 request が宣言した source 1031 と envelope 1223 を歴史的基準として保持し、現在の source と同一の意味には扱わない。
現行 source は固定 v8 flow、front v6 の実12 worker prepared / manifest / resource / environment、並列 merge v6 production-ready、tail v3 / config v8 / 新 report-only 環境、実 controller launch の明示 authority から追加する。
保存する source ごとに宣言 path と原本 hash を保持し、別 path を同一内容だけで統合しない。
source alias は固定 target と前後の bytes を検証し、native alias は所在・stat のみとする。
現行文書が参照する source 数には、保持した worker の元 manifest に含まれる非担当 slot と、歴史的な検証用 source も含む。
その全 source が現在の12 workerで実行されたという意味には使わず、実 worker / prepared / job の対応は別に保存する。

metadata は旧有限75文書に加え、明示した現行設定・環境・受入・実 submission・immutable launch 文書だけを追加する。
JSON 文書の参照を自動的に再帰収集しない。
保存文書の認識可能な全 one-hop edge は索引に残し、scope 外・相対 base 未指定・historical・native/raw を欠落のない形で記録する。
observations.jsonl や実行中 controller の可変ログ全体を pin しない。
worker の qstat は採取時点に新しい immutable JSON として保存し、その観測後の状態まで証明したとは扱わない。
全12 merge・独立計時・最終 report の完了証拠は未取得として final_proofs_complete=false を維持する。

実採取は共有 physical-node gate を通す qsub、1 CPU・2 GB・10 分で行う。
source の全件 hash、明示 metadata の hash、別 pin 間の矛盾、全 envelope の分母、source alias の同一 target を受入済みライブラリで検証する。
private source / metadata ZIP を生成し、公開版の識別子処理や任意 workspace への exact replay 完了とは主張しない。
