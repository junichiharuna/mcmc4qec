# 校正結果の回収・監査仕様

稼働中のdriverとmanifestを変更せず、解析完了後に別のPBSジョブで以下を検査する。
追加ジョブもqsubを用い、既存解析との合計を最大2ノードに制限する。

1. 固定manifestから生成した46,080 traceと2,304 analysis groupの全期待keyが存在し、余分なkey、重複、途中ファイルがないことを確認する。
2. 全artifactのmarker、identity、NPZ/JSON両方のSHA-256を検査する。
3. traceの長さ66,000、dtype、値域、exact bankの支持、seed、初期状態、model/decoder、kernel、noise座標、source hashとmetadataを照合する。
4. 3符号の全状態を96分割し、公開Problem.is_faultyでfailure bankの欠落・余分を独立検査する。
5. 全解析行の条件集合、重複、truth、pooled BAR root方程式、covariance、SE、区間、被覆flagを照合する。
6. 全64,512行を独立に再集計し、既存CSVとsummaryの分母、未取得数、bias、RMSE、被覆率、Wilson区間、対応差を照合する。
7. 診断のmeanをtraceから照合し、weight・syndrome weight・logical indicatorのexact条件付き平均と比較する。
8. 結果を全cohortで報告し、診断flagのあるreplicateを主集計から除外しない。

R-hat>1.01、各chainのESS<100、診断未定義を探索的なscreeningとして別列に記録する。
これらは結果取得後に追加した記述基準であり、事前固定の合否基準や収束の証明として扱わない。
exact分散が0のlogical indicatorは構造的定数として分け、IAT/R-hat未定義を混合失敗に数えない。
初期化・burn-in・長さ・誤差法の比較はreplicate対応を維持し、多条件の結果を独立な反復としてまとめない。
全生artifactは分割archiveとして回収し、archive hashとfile inventoryを照合する。
公開既定の変更判断は点の被覆率だけで決めず、未取得・bias・初期化依存・診断の限界を併記する。

## Steaneの初期化依存に対する追加の有限状態検証

解析完了後の集計でSteaneのdispersed armに大きなbiasが見つかったため、初期化と提案supportを全128状態で調べる。
64 failure状態の全組について公開Zanella・ClusterExchange(k=2)・StabilizerFlipのproposal probabilityを取得する。
既定Z/Hと、候補Z/H/stabilizer=0.6/0.3/0.1の遷移行列をMH受理・棄却・lazyを含めて組み立て、正規化・詳細釣合い・stationarity・連結成分を別々に検査する。
候補は有限状態の接続性確認だけに使い、公開既定や今回のcohortを変更しない。
成分ごとのweight分布・真の条件付きmass・dispersed初期状態の所属を保存し、各rungに50%ずつ固定した成分混合のBAR極限値を計算する。
この追加解析は事後に原因を調べるものであり、事前計画の測定と区別する。
