# 全予定 seed namespace 監査の回収・独立照合

PBS job `265220.node-PRISM` は `F / Exit_status=0 / run_count=1` で正常終了した。
固定投入は1ノード、1 CPU、2 GiB、30分上限であり、実測 wall は24分42秒、CPUは7分32秒、PBS報告memは182428 KBだった。
追加の qsub、計算の再実行、実行中 source の変更は行っていない。

予定3,855,274件をすべて検査し、未検査0件、予期しない衝突0件、異なるseed値3,846,826個、意図共有8,448件だった。
48 namespaceの予定件数をmanifestの寸法と解析設定から独立の件数式で計算し、予定件数および全roleの実検査件数と一致した。
この独立照合はseed streamを再生成した二度目の衝突探索ではない。
意図共有はstage33の `synthetic.bootstrap` が `calibration.bootstrap` の固定設定の部分集合を資源測定用に再利用する8,448件であり、独立cohortとは扱わない。
stage155の `low.synthetic.bootstrap` も件数は8,448件だが、こちらは意図共有の8,448件とは別で、全数監査に含まれる。
stage140と141は対応するBAR timing選択manifestを渡しておらず、未列挙予約namespaceとして残る。
したがって固定予定集合の全数監査は完了したが、goal全体のすべてのnamespaceを監査済みとはしない。
有限個のseed値の重複がないことは、乱数streamの統計的独立性や実sampling metadataの一致の証明ではない。

回収したmanifest、投入intent/ledger、実PBS script、execution intent、正式result、completion、stdout/stderr、終了qstatとsource/input/runtimeを相互照合した。
回収archiveの68ファイルは転送前後のSHA256が一致し、実行前に取得したmanifestとも一致した。
実行環境はPython 3.11.9、NumPy 2.4.6、ldpc 2.4.1、bposd 2.1、PyMatching 2.4.0で、master seedは2026101719だった。
baseline core package hashとPython実体hashも固定manifestに一致した。
stderrは0 bytesで、completionの全数gateも成功した。

全数探索自体は1475.391秒、driverの経過時間は1480.236秒だった。
事前resource pilotのfactor2予測378.171秒、計算開始時pilotのfactor2予測582.225秒より長く、pilot外挿を完了時間の保証とは扱わない。
固定1800秒上限内で終了した。

SQLiteは固定planから再生成できる派生seed索引であり、凍結auditorのTemporaryDirectoryにより正常終了時に削除された。
終了後scratch内にファイルがないことを確認し、実行中DBのコピーや重いDB再走査は行っていない。
保存する再現証拠は固定source/inputplans、環境、全件数、衝突統計、stream hash、正式結果とPBS実行記録である。

## 保存物

- `recovered.tar.gz`：68ファイルと回収側hash照合記録、終了qstat。
- `recovered/`：archiveを安全なパス検査後に展開した内容。
- `independent_verification.json`：独立件数式、role別件数、正式結果との照合結果と適用範囲。
- `transfer_verification.json`：archive hash、size、転送後hash照合結果。
- `running_binding_verification.json`：実行中に確認した固定source/input/runtimeの照合記録。
- 親ディレクトリの `collect_seed_census_evidence_v1.py` と `verify_seed_census_evidence_v1.py`：回収・独立照合手順。

## 主要hash

- stream SHA256：`b829922bd0ed18070201625256a4795311e92633e23681a216a3a4e371eed7b8`
- result.json SHA256：`9eed4f8324a617390c39d8663061af8aa339c6d21f6f2dfb293aa0c7f163fe86`
- manifest.json SHA256：`aa4ca60f123ae3d3045bebca5c731c0f19a1c80ae9679106bd9cedf7fc162c93`
- canonical manifest digest：`1464f4c66b2da06129a727ae352f77927e4f85dc2fb64d2617b4f877be193fe1`
- auditor SHA256：`7c6276d10d08eda9d110df0af06dbab3c661339e7d304cd545fc1fef1150fec8`
- submitter SHA256：`0d53d4f6946b259049f619ab28a62d7940121395b1d7fc03686fe12a6b756268`
- recovered.tar.gz SHA256：`00d79486631b3b23d9f3235bbc3252b33eb94e649530ea9fbef13101ed9a71dd`
