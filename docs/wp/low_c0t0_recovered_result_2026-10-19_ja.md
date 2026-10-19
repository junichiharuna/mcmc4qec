# tile72 bit-flip p=0.01の低ノイズ比較

C0T0の最終比較265333.node-PRISMはF・exit 0・run_count 1、walltime 29分7秒で終了した。
修正済みの親側受理と転送前後の同一性確認を通し、reportと実行記録13点をローカルへ回収した。
352設定×事前固定192 seedの67,584行を保持し、全設定で点推定192件、区間未取得0件、記録された失敗0件だった。

参照は重み層別samplingによる有限の99.9%区間`[0.0025764593946474706, 0.0025779929648659643]`であり、厳密な真値ではない。
各MC層のClopper–Pearson区間、Bonferroni調整、未計算重みの確率上限を含む。
以下は事前計画の長い設定（16 chain・burn-in 6,000・保存60,000・fine ladder）を記述的に抜き出したもので、結果を見て選んだ推奨設定ではない。
相対biasと相対RMSEの幅は参照区間内での範囲であり、母集団RMSEの信頼区間ではない。

| kernel | 初期化 | 相対bias範囲 (%) | 相対RMSE範囲 (%) | block1024 被覆件数 | cross-chain 被覆件数 |
|---|---|---:|---:|---:|---:|
| ZH | logical_basis | 0.0349–0.0944 | 0.921–0.926 | 183 / 186 | 182 / 185 |
| ZH | logical_combination | −0.0080–0.0515 | 0.943–0.945 | 178 / 180 | 181 / 183 |
| ZHS | logical_basis | 0.0357–0.0952 | 1.026–1.030 | 185 / 186 | 183 / 184 |
| ZHS | logical_combination | 0.0015–0.0610 | 0.941–0.944 | 185 / 185 | 185 / 185 |

被覆欄の左右は「参照区間全体を含む件数 / 参照区間と交差する件数」であり、いずれの分母も192である。
この8設定ではflagged・undefined・high R-hat・low ESSの件数がすべて0だった。
診断の通過は収束や支持の連結性の証明ではなく、この有限cohortの被覆件数も名目95%被覆を保証しない。
全352設定ではflagged・high R-hat・low ESSが0–192、undefinedが0–185だったため、長い設定の診断を全設定へ一般化しない。
誤差法とnested trace長は軌道を共有しており、独立の追加cohortとして数えない。
この条件の結果だけではZHSの一律の優位性や低ノイズ全域の精度を主張しない。

trace監査は768 group・192 anchor・122,880 planned sampling taskを対応付け、8,232,960の保存checkpointを再復号した。
失敗samplingは0件だった。
全MCMC状態の独立再復号やanchor MCの再実行をしたわけではない。
時間切れとなった元解析の検証済み672 groupを再利用し、欠けていた96 groupを復旧した履歴をreportに保持している。

最初の親側受理は`metrics.failures`を整数と誤認して拒否した。
[修正仕様](low_report_failure_counts_fix_2026-10-19_ja.md)に従い、理由別件数辞書を検証する新helperを作り、実producerを使う13件と回帰・transportの25件、計38件を通した。
旧helper・失敗記録・計算reportは保持し、科学計算ジョブの再投入や数値結果の変更は行っていない。
新completion SHA256は`bc887cafe1701d442a384e23bc497127b382d2bef274a0388cabfeacc1928305`、report SHA256は`fb95bd83fc83bcd5a3f4d6c438d5bf9b6065d39869b3d1cad97a9ed2498ab9ab`である。

[集約JSON](data_tile_validation_2026-10-17/low_c0t0_recovered_summary_v1.json)と[再現スクリプト](data_tile_validation_2026-10-17/summarize_low_c0t0_recovered_v1.py)を保存した。
集約JSONのSHA256は`7cf609169dc6fb349e5d93290207e8db136873762ea4721a899944e264c1588d`である。
元reportと13点の実行記録は`data_tile_validation_2026-10-17/low_bar_recovery_report_collection_v3/artifacts/`にあり、約348 MBのreportを固定済み公開候補へ追加していない。
同じ精度までの計算時間の比較と、残る条件の検証は未完了である。
