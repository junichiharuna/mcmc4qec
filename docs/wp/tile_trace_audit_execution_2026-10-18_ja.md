# Tile全trace監査の計算資源計測と実行仕様

## 全4条件のfull監査完了（2026-10-18 15:22 JST）

各caseで事前固定96群のcapacityを実測し、既存submitterが測定artifactを検査してfullの資源を算出した後、全768群の本監査をqsubした。
全8ジョブはF・exit 0で、各fullのfailed_auditsとfailed_samplingは0だった。

|case|capacity job|full job|full phase秒|trace数|再復号checkpoint数|
|---|---:|---:|---:|---:|---:|
|tile72 bit-flip|265222|265223|72.624|86,016|5,763,072|
|tile288 bit-flip|265224|265225|48.880|30,720|583,680|
|tile72 depolarizing|265226|265228|23.390|43,008|817,152|
|tile288 depolarizing|265229|265230|79.991|30,720|583,680|

正式summary全予定group identityとPBS/native/manifest/scriptの結合を確認し、原本12ファイルずつを`data_tile_validation_2026-10-17/trace_audit_evidence_v1/`へ回収した。
集約証拠は`data_tile_validation_2026-10-17/main_trace_audit_completion_v1.json`にあり、集計手順は`data_tile_validation_2026-10-17/summarize_main_trace_audits_v1.py`である。
全groupの監査payloadはremoteに保存し、後続audited-results adapterで現在payloadと回収archiveの結合を検証する。
この完了は保存compact点とinitial/checkpointの検査範囲に限り、未保存物理状態の再生、独立decoderの正しさの証明、混合・被覆の保証ではない。

## 2026-10-18 15:13 JSTの実行記録

case0 capacityを265222としてqsubし、96群・failed_audits 0、phase 10.789秒、PBS F・exit 0を確認した。
既存submitterが全96 measurementと監査artifactの結合を検査し、fullの予測phase 86.313秒・要求1ノード96 CPU/32 GB/30分を算出した。
fullを265223としてqsubし、全768群・failed_audits 0、phase 72.624秒、PBS F・exit 0・wall 1分15秒で完了した。
正式summaryの全768 record、native、manifest、脚本、PBS、ログを`data_tile_validation_2026-10-17/trace_audit_evidence_v1/full-0/`へ回収した。
group payloadはremoteに保持しており、後続の全数結果adapterで照合する。
この監査は全compact点と保存済みinitial/checkpointを対象とし、全乱数軌道再生・独立decoderの正しさの証明・混合や被覆の保証は含まない。
次のcase1 capacityを265224としてqsubし、seed照合と合わせ最大2ノードを維持する。
以下の準備時点の未実施記載は履歴として保持する。

既存の `audit_tile_traces.py` は変更せず、固定された本校正manifestとnative環境に結び付く実行wrapperを追加する。
監査対象はcompact配列全点と保存済みinitial/checkpointで、未保存の物理状態の復元や全乱数軌道の再生は行わない。
監査成功を混合・既約性・BARの被覆の保証として扱わない。

## 固定対象と失敗の扱い

caseごとに資源計測は全kernel・全初期化のreplicate 0–23、計96 groupを対象とする。
対象は所要時間・成否・推定値を見る前に固定し、depolarizingのX/Z初期化の両parityも含める。
本監査は全192 replicate・768 groupを別rootで処理する。
資源計測の監査結果を本監査完了の代わりにしない。
各groupのwall・CPU・worker peak RSSと、保存済み監査artifactのhashを記録する。
sampling自体の失敗は既存監査仕様に従って分母に残し、欠落・破損・復号不一致は監査失敗として別に保存する。
監査失敗がある資源計測は本監査の資源根拠として受け付けない。
実行開始intentを排他的に作成し、同じrootを自動再実行してcacheから計測しない。

## 環境と投入

planはsampling manifest、profile、fixture、wrapperと監査のsource hashおよびruntimeを固定する。
実行時に入力を再検査し、compute node上のnative probeが一致してからworkerを起動する。
実際のprobe、hostname、PBS job ID、所要時間を保存してsummaryにhashを結び付ける。
実行はqsub・96 worker・BLAS等1 threadとし、既存controller稼働中の別投入を拒否する。
待機中を含む要求node数と新規1nodeの合計を2以下に制限する。
sampling jobがPBSでterminalかつ全taskの成功または失敗記録が揃っていることを投入前に確認する。
資源計測は1node・96 CPU・32 GiB・30分を上限とする初期予算で、完了時間の保証ではない。
本監査は計測phase walltimeの8倍と、各kernel/初期化で最長groupを全replicateに外挿した値の大きい方を予測時間とする。
要求walltimeは予測の2倍に600秒を加え、30分単位に切り上げる。
memoryは最大worker RSSの96倍・1.5倍に8 GiBを加え、最低32 GiBとする。
24時間または340 GiBを超える場合は投入を拒否して分割を再設計する。
qsub前にintentを保存し、応答不明・timeout時は自動再投入しない。
別の手動submitterとの原子的な同時実行制御は保証せず、管理された投入手順で使う。

## 受入

固定対象・manifest/native入力の改変拒否、実際の小規模trace監査、監査失敗の保持、計測値の検査、資源外挿、controller/node上限、曖昧なqsub応答後の再投入拒否を検査する。
wrapperとsubmitterを実装し、関連41件の受入がWindowsで7.36秒で通った。
並列workerの完了順を固定group順へ整列してから全件のidentityを照合する。
実資源計測・本監査は未実施である。

## 2026-10-18の配置と確認

新bundleを `/home/user/workspace/mcmc4qec/20261018-tile-trace-audit-v2` に配置し、archive SHA-256 `8531c174f3e67917a2233b9552a5882692aed252d1e447ebd11b91d050ef611e` のremote/local一致を確認した。
Linuxでも関連41件が2.35秒で通った。
完了済みcase3を対象に `runs/capacity-3` と `runs/full-3` のmanifestを保存し、capacityのdry-runが実sampling/anchor summaryを受理した。
login nodeで取得したnative profileを固定Linux profileと照合し、一致を確認した。
この確認はcompute node上の実行前検査の代用ではない。
capacityのqsub・資源計測と、その測定に基づくfullの資源要求・qsub・全件監査は未実施である。
既存controllerと265209/265210が実行・待機中のため、競合する投入は行っていない。
source、test、manifest、PBS scriptと配置のhashは `data_tile_validation_2026-10-17/trace_audit_execution_deployment_v2.json` に保存した。

## 全4caseの監査計画の準備

主sampling4条件が完了した後、同じ固定v2 bundleにcase0・1・2の`runs/capacity-{case}`と`runs/full-{case}`を追加した。
各capacityは予定96群、各fullは全768群を保持し、条件やseedを変更していない。
既存case3の全fileとbundleの85 source/test/data fileは作成前後で同じhashだった。
login nodeでの厳密native照合、既存readerによるplan再読込、capacity submitterの正式dry-run、全3caseの`bash -n`を確認した。
native probeは1.18秒で、実際の監査や資源計測は行っていない。
各root・manifest・dry-run・file hashと確認範囲は[残り監査計画の準備記録](data_tile_validation_2026-10-17/trace_audit_remaining_plans_preparation_v1.json)に保存した。
full manifestは作成済みだが、full資源要求には対応caseのcapacity実測が引き続き必要である。

既存controllerの終端とqueued込み最大2ノードを確認できる状態になった後、caseごとに次の既存submitterを用いる。
以下の`0`は対象caseに置き換え、複数caseを一度に投入するloopにはしない。

```bash
venv/bin/python cluster_scripts/submit_tile_trace_audit.py \
  --bundle "$PWD" --root "$PWD/runs/capacity-0" \
  --source-root /home/user/workspace/mcmc4qec/20261017-tile-production-v1/runs/production --execute
```

capacity完了後のfull投入では`--root "$PWD/runs/full-0" --capacity-root "$PWD/runs/capacity-0"`を使い、実測結果の検証を通す。
準備記録をcapacity/fullの実行成功や混合・被覆の証拠として扱わない。
