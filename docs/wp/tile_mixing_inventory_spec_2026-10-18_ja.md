# 保存済み全cohort混合診断の一覧

既存の校正計画と`tile_bar_analysis.py`の診断定義を変更せず、`tile_mixing_inventory.py`で保存済みanalysis JSONを一覧化する。
対象は主校正の1 case、2 kernel×2初期化×192 replicateの768 groupである。
`tile_audited_results.read_results`の成功report、そのreportにhashで結合されたanalysis archive verification、同じproduction rootのmanifest・analysis context・analysis JSONとmarkerを入力にする。
保存済みreportのsource・192/768分母・case・manifest/contextと成功scopeを確認し、既存`_verification`と`_match_payload`で予定artifactと現在のJSON/markerを照合する。
保存reportに記録された入力pathを維持するsnapshotを前提とし、移設先の同じbyte列をpath照合なしで代用しない。
これは既存の監査結果の再利用であり、full trace auditやnative probeを再実行したとは扱わない。
NPZ、物理trace、reference trialは読まず、現在の全payloadの再監査とは呼ばない。

各groupの全chain数・burn・保存長・rungについてweight、syndrome_weight、全logical bitを列挙する。
bit-flipのlogical bit数は8、depolarizingは16で、対象は既存tile72/288の固定設計に限る。
coarse/fine ladderの各Bennett edgeの両端も列挙する。
物理観測量にladder・BAR誤差法の次元を追加せず、sector遷移・unique数は各rung/window/chainsについて1回だけ出力する。
sector観測量の定義済み要約とBennett診断を混同しない。
sectorの少なくとも一方のfieldを保存しているコピー間で値や欠落状態が異なる場合は構造不正として拒否し、両fieldとも無いコピーは比較対象から外す。
全予定identityを出力し、replicate IDは0から191をそのまま保持する。

選択chain内のsampling失敗があるrungの物理診断は欠落行として残す。
Bennett診断は選択ladder内にsampling失敗が一つでもあれば、そのladderの全edge両端が欠落する既存解析規則に従う。
記録済み失敗がないのに診断がない場合もmissing_unexpectedとして分母に残し、inventory_completeをFalseにする。
失敗と矛盾する診断の存在、予定外・重複identity、chain配列長不一致、artifact欠落・hash不一致は構造不正として拒否する。
None・欠けた数値field・非有限値は削除せず、出力ではnullと原因pathを保存する。
chain配列内のnull要素は保持するが、field自体が存在して値がnullまたはlist以外の場合は配列構造不正とし、field欠落とは区別する。
保存されたflagと一覧側のmissing/nonfinite/undefinedを区別して記録する。
全192を主分母とし、数値要約は有限値のcount・sum・min・maxと欠測/非有限件数を併記する。
有限値のみのmeanはavailable_only_meanと明記し、全予定値が有限でない場合の主meanはnullとする。
診断から収束・支持連結性・正しさ・名目被覆を保証しない。

出力はproduction root外の新規directoryを排他的に作成し、rows.jsonlをstream出力して最後にsummary.jsonを保存する。
既存出力を上書きせず、途中失敗したdirectoryには成功summaryを作らない。
全読取入力と実使用sourceは開始時hashを保存し、完了前にlexical pathの解決先とhashを再照合する。
production内の入力symlinkがroot外へ解決する場合は拒否する。
report/verificationは指定された外部入力としてhashで固定する。
ACF、FFT、bootstrap、BAR solve、decoder再実行は行わず、それぞれ非実施と明記する。
historical consumed-input hashが旧解析に無いという既存制限を引き継ぐ。
CLIは全JSON読取りのためPBS_JOBIDを要求するが、この開発ではqsub・remote・本番走査を行わない。

受入は小さい保存fixtureと制御用768 groupで、予定集合、192 seed、失敗/未定義/非有限保持、ladder全edge欠落、chain prefix外失敗、sector重複防止、hash/identity混入、入力とsourceの終端変更、排他出力とscopeを確認する。
数値診断自体の再計算は受入対象にしない。
正常時の既存計画の診断行数はcase順に811008、571392、1327104、940032で、sector一覧は別の行種別にする。
各caseの実bytes・CPU秒・本番I/Oは未測定であり、sourceから数えた行数を実測時間と扱わない。
実行前の資源判断には各caseの固定先頭groupでJSON/markerの読込み・集計時間とサイズを測り、予定件数へ外挿する必要がある。

## 実装と受入

小仕様と受入を先に保存し、未実装時のModuleNotFoundErrorを確認してから実装した。
Windows Python 3.11のoptional環境で15 passed・12.12秒、skipなしだった。
最初の大きいfixtureの反復作成はI/Oが重くなったため停止し、実gridの小単体受入と、1観測量に明示縮小した実保存768 groupの制御受入へ分解した。
この分解受入は実本番の全観測量・全artifactを通した科学検証ではない。
独立レビューでblocking指摘はなく、scopeと重複sector field・path・配列nullの契約を明文化した。
source SHA256は`bd464813f0c7d307131b3784262c639ed2677a3e60fec53913eb8905f6ed3b31`、受入test SHA256は`4af8b3cf8d957ad0d458e5159222010aa3ca872dc56765f068ea13df25e0290c`である。

本番CPU/I/Oの資源確認後、固定環境のqsubジョブ内で次のCLIを使う。
既存のproductionやfull監査を変更せず、新規output directoryにだけ保存する。

```bash
venv/bin/python cluster_scripts/tile_mixing_inventory.py \
  --root /absolute/path/to/production \
  --audited-results /absolute/path/to/audited-case0.json \
  --analysis-verification /absolute/path/to/analysis-verification-case0.json \
  --case 0 --output /absolute/path/to/new-mixing-inventory-case0
```

本番集計、Linux受入、容量/CPU/I/O測定、qsubは本開発では未実施である。
