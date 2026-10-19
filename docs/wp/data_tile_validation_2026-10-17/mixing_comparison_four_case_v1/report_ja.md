# 主4条件の保存済み混合診断比較

## 受理範囲と分母

全4caseの正式回収証拠へ結合した保存summaryの比較であり、新しい数値診断や収束証明ではない。
各観測量cohortの分母は192で、chain配列とsector統計の要素数は192×chainsである。

|case|実job|group|seed|inventory_complete|failed sampling|記録済みfailureによる欠測行|予期しない欠測行|inventory undefined行|
|---|---|---:|---:|---|---:|---:|---:|---:|
|0|265271.node-PRISM|768|192|True|0|0|0|2|
|1|265272.node-PRISM|768|192|True|0|0|0|290|
|2|265273.node-PRISM|768|192|True|0|0|0|4140|
|3|265274.node-PRISM|768|192|True|0|0|0|76653|

欠測・undefined行は全observable-cohortとsector行の件数で、同じseedを重複して含み、192seed単位のORではない。
inventory_completeは一覧の構造的な完全性であり、保存値のnullやscreen undefinedがあってもtrueになり得る。
全予定条件と保存数値は[JSON](cohorts.json)・[CSV](cohorts.csv)、入力とJSONL回収hashは[証拠](provenance.json)に保持した。
stored flagのundefinedと、missing/null/nonfiniteも含むinventory undefinedを区別する。
missingのためflag自体が存在しないseedを警告なしへ読み替えない。

## target観測量と全rung/Bennettの違い

以下は最大chain・burn6000・最長保存長で、各kernel/initのtarget weightを固定した一覧である。
全rung・全物理観測量・Bennett両端の個別値は全予定表に保持しており、target weightだけで全体の混合を判定しない。

|case|kernel|init|chains|samples|stored flag /192|screen undefined /192|inventory undefined /192|missing /192|
|---|---|---|---:|---:|---:|---:|---:|---:|
|0|ZH|logical|16|60000|0|0|0|0|
|0|ZH|rejection|16|60000|0|0|0|0|
|0|ZHS|logical|16|60000|0|0|0|0|
|0|ZHS|rejection|16|60000|0|0|0|0|
|1|ZH|logical|8|12000|192|0|0|0|
|1|ZH|rejection|8|12000|192|0|0|0|
|1|ZHS|logical|8|12000|192|0|0|0|
|1|ZHS|rejection|8|12000|192|0|0|0|
|2|ZH|logical|8|12000|0|0|0|0|
|2|ZH|rejection|8|12000|0|0|0|0|
|2|ZHS|logical|8|12000|0|0|0|0|
|2|ZHS|rejection|8|12000|1|0|0|0|
|3|ZH|logical|8|12000|192|0|0|0|
|3|ZH|rejection|8|12000|192|0|0|0|
|3|ZHS|logical|8|12000|192|0|0|0|
|3|ZHS|rejection|8|12000|192|0|0|0|

同じ固定windowの全rung・全observableの値は[rung/observable対比表](rung_observable_comparison.csv)に示す。
次表の範囲は各observable/rungが持つflag件数の最小〜最大であり、seed集合の和集合ではない。
missing合計は診断行の欠測数の和で、同じseedを複数回含み得る。

|case|kernel|init|observable family|診断cohort数|各cohort flag件数範囲 /192|missing診断行数|
|---|---|---|---|---:|---|---:|
|0|ZH|logical|coarse_bennett|6|0–0|0|
|0|ZH|logical|fine_bennett|12|0–0|0|
|0|ZH|logical|logical_bit|56|0–0|0|
|0|ZH|logical|syndrome_weight|7|0–0|0|
|0|ZH|logical|weight|7|0–0|0|
|0|ZH|rejection|coarse_bennett|6|0–0|0|
|0|ZH|rejection|fine_bennett|12|0–0|0|
|0|ZH|rejection|logical_bit|56|0–0|0|
|0|ZH|rejection|syndrome_weight|7|0–0|0|
|0|ZH|rejection|weight|7|0–0|0|
|0|ZHS|logical|coarse_bennett|6|0–0|0|
|0|ZHS|logical|fine_bennett|12|0–0|0|
|0|ZHS|logical|logical_bit|56|0–0|0|
|0|ZHS|logical|syndrome_weight|7|0–0|0|
|0|ZHS|logical|weight|7|0–0|0|
|0|ZHS|rejection|coarse_bennett|6|0–0|0|
|0|ZHS|rejection|fine_bennett|12|0–0|0|
|0|ZHS|rejection|logical_bit|56|0–0|0|
|0|ZHS|rejection|syndrome_weight|7|0–0|0|
|0|ZHS|rejection|weight|7|0–0|0|
|1|ZH|logical|coarse_bennett|4|188–192|0|
|1|ZH|logical|fine_bennett|8|192–192|0|
|1|ZH|logical|logical_bit|40|0–11|0|
|1|ZH|logical|syndrome_weight|5|56–191|0|
|1|ZH|logical|weight|5|192–192|0|
|1|ZH|rejection|coarse_bennett|4|191–192|0|
|1|ZH|rejection|fine_bennett|8|192–192|0|
|1|ZH|rejection|logical_bit|40|0–10|0|
|1|ZH|rejection|syndrome_weight|5|48–192|0|
|1|ZH|rejection|weight|5|192–192|0|
|1|ZHS|logical|coarse_bennett|4|192–192|0|
|1|ZHS|logical|fine_bennett|8|192–192|0|
|1|ZHS|logical|logical_bit|40|0–16|0|
|1|ZHS|logical|syndrome_weight|5|113–192|0|
|1|ZHS|logical|weight|5|192–192|0|
|1|ZHS|rejection|coarse_bennett|4|192–192|0|
|1|ZHS|rejection|fine_bennett|8|192–192|0|
|1|ZHS|rejection|logical_bit|40|0–9|0|
|1|ZHS|rejection|syndrome_weight|5|119–192|0|
|1|ZHS|rejection|weight|5|192–192|0|
|2|ZH|logical|coarse_bennett|6|0–0|0|
|2|ZH|logical|fine_bennett|12|0–0|0|
|2|ZH|logical|logical_bit|112|0–140|0|
|2|ZH|logical|syndrome_weight|7|0–0|0|
|2|ZH|logical|weight|7|0–0|0|
|2|ZH|rejection|coarse_bennett|6|0–0|0|
|2|ZH|rejection|fine_bennett|12|0–0|0|
|2|ZH|rejection|logical_bit|112|0–142|0|
|2|ZH|rejection|syndrome_weight|7|0–0|0|
|2|ZH|rejection|weight|7|0–0|0|
|2|ZHS|logical|coarse_bennett|6|0–1|0|
|2|ZHS|logical|fine_bennett|12|0–1|0|
|2|ZHS|logical|logical_bit|112|0–153|0|
|2|ZHS|logical|syndrome_weight|7|0–0|0|
|2|ZHS|logical|weight|7|0–1|0|
|2|ZHS|rejection|coarse_bennett|6|0–1|0|
|2|ZHS|rejection|fine_bennett|12|0–1|0|
|2|ZHS|rejection|logical_bit|112|0–154|0|
|2|ZHS|rejection|syndrome_weight|7|0–0|0|
|2|ZHS|rejection|weight|7|0–1|0|
|3|ZH|logical|coarse_bennett|4|192–192|0|
|3|ZH|logical|fine_bennett|8|192–192|0|
|3|ZH|logical|logical_bit|80|0–192|0|
|3|ZH|logical|syndrome_weight|5|192–192|0|
|3|ZH|logical|weight|5|192–192|0|
|3|ZH|rejection|coarse_bennett|4|192–192|0|
|3|ZH|rejection|fine_bennett|8|192–192|0|
|3|ZH|rejection|logical_bit|80|0–192|0|
|3|ZH|rejection|syndrome_weight|5|192–192|0|
|3|ZH|rejection|weight|5|192–192|0|
|3|ZHS|logical|coarse_bennett|4|192–192|0|
|3|ZHS|logical|fine_bennett|8|192–192|0|
|3|ZHS|logical|logical_bit|80|1–192|0|
|3|ZHS|logical|syndrome_weight|5|192–192|0|
|3|ZHS|logical|weight|5|192–192|0|
|3|ZHS|rejection|coarse_bennett|4|192–192|0|
|3|ZHS|rejection|fine_bennett|8|192–192|0|
|3|ZHS|rejection|logical_bit|80|1–192|0|
|3|ZHS|rejection|syndrome_weight|5|192–192|0|
|3|ZHS|rejection|weight|5|192–192|0|

## kernel・初期化の比較

全予定表は同じcase/chains/burn/samples/rung/observableのZH・ZHSとrejection・logicalを対比できる。
周辺件数と保存統計の比較に限り、同じreplicate番号の差・相関や共通乱数による効果は未評価である。

## chain数・burn-in・保存長の比較

4chainと最大chain、burn600と6000、各保存長を一つの軸ずつ対比する。
この対比用の[target weight全window表](controls_target_weight.csv)は全kernel/initを保持する。
windowは同じtraceを再利用し、4chainはprefixなので、設定数を独立試行数として扱わない。
主meanがnullの場合も保持し、available_only_meanは有限値のみの補助平均である。

## logical sector移動

sector行はrung/window/chainsごとに一回で、screen flagはnot_applicableである。
sector_transitionsとunique_sectorsは192×chains要素の集計であり、chain間の訪問集合の和集合や全支持の連結性を示さない。

固定windowの全rungの[sector対比表](sector_comparison.csv)を併記する。
## BAR精度・被覆報告との対応と限界

主BARの既存flagは選択ladderの物理観測量とBennett診断をseed単位でORした別の受理済み集計である。
本表の個別flagを足して主BARのflag数を復元しない。
全rung/observableのseed単位OR、相関、対応差、depolarizingの96/96層別、median/quantileは本summaryでは未評価である。
rows.jsonlは回収済みhash・sizeへの参照だけを保存し、今回JSONL/NPZ/ACF/raw trace/nativeを再読込・再監査していない。
元解析にhistorical consumed-input hashが無い制限を引き継ぐ。
警告の有無から収束・既約性・正しさ・bias・名目95%被覆を保証しない。
wrapperのCPU/wall/RSSは保存診断の後処理時間であり、MCMCの計算効率やtime-to-accuracyではない。
