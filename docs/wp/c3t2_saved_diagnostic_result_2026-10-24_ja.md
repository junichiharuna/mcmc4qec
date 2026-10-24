# tile288 depolarizing p=0.001：保存済み診断の内訳

2026-10-24に、C3T2の保存済み解析JSONを独立したqsubジョブ265508で集計した。
全352設定・各192反復の67,584行で診断flagが立ち、今回の設定群を診断合格として扱えないことを確認した。
これは保存値の記述的集計であり、BARのbias・RMSE・被覆の最終集約は別ジョブ265507で継続中である。

## 範囲と分母

全38バッチ・768群を保持し、2,893,824件の保存診断と全67,584結果行を照合した。
設定はkernel ZH/ZHS、初期化logical_basis/logical_combination、4/8 chains、burn-in 600/6,000、保存長600/6,000/12,000、coarse/fine ladder、block 32/128/1,024またはcross_chainの予定された組合せである。
block 1,024は保存長6,000以上に限り、全直積ではなく352設定となる。
各設定の192反復のうち、undefined・high R-hat・low ESS・flaggedはいずれも192だった。
区間未取得は0行、overlap errorは0行、分母からの除外は0行だった。
区間が取得できたことを、その区間の被覆が校正されたこととは解釈しない。

## 保存診断の内訳

保存値の判定は、R-hat欠落またはchain ESSのいずれかの欠落をundefined、R-hat > 1.01をhigh R-hat、取得できたchain ESSのいずれかが100未満の場合をlow ESSとする。
行のflagは、その行で使用するrungの基本観測量と対応ladderのBennett edgeの診断を論理和でまとめる。
同じ行・診断が複数の理由に該当し得るため、以下の列は排他的な内訳ではない。

| 観測量族 | 診断件数 | undefined | R-hat欠落 | chain ESS欠落を含む診断 | high R-hat | low ESS |
|---|---:|---:|---:|---:|---:|---:|
| weight | 138,240 | 63 | 0 | 63 | 136,110 | 138,044 |
| syndrome weight | 138,240 | 0 | 0 | 0 | 134,318 | 138,208 |
| logical bits | 2,211,840 | 1,390,146 | 177,796 | 1,390,146 | 1,848,107 | 1,827,209 |
| Bennett edges | 405,504 | 128 | 0 | 128 | 399,536 | 405,080 |

診断例外は全観測量族で0件だった。
上表の「chain ESS欠落を含む診断」は欠落chainの本数ではなく、少なくとも1本の欠落がある診断の件数である。
同じ反復から複数rung・観測量・保存長・burn-in・chain数を集計するため、この診断件数を独立な反復数として扱わない。

| 観測量族 | undefinedを含む群数／768 | undefinedを含む結果行数／67,584 |
|---|---:|---:|
| weight | 43 | 369 |
| syndrome weight | 0 | 0 |
| logical bits | 768 | 67,584 |
| Bennett edges | 43 | 369 |

logical bit診断の未定義は全設定・全反復の行に含まれており、全行undefinedという保存flagと整合した。
weightとBennett edgeの未定義行数は同じだが、この件数の一致だけから同一原因とは結論しない。
未定義を含まないsyndrome weightにも多数のhigh R-hat・low ESSがあり、logical bitの未定義だけを取り除けば診断上の懸念が解消する、とは扱わない。
欠落ESSや保存された平均だけから、定数trace、logical sector間移動の欠如、支持の非連結を断定しない。
詳細釣合い・既約性・非周期性の証明と実測診断は別の要件である。

## 実行と再現情報

実行前に[小仕様](c3t2_diagnostic_census_spec_2026-10-24_ja.md)と4件の合成受入を確認し、既存の数値集約controllerや固定sourceは変更しなかった。
qsubジョブ265508.node-PRISMは1ノード1CPU4GB、終了コード0・run count 1で終了した。
PBS実測walltimeは2分42秒、最大メモリは59,648 KiBだった。
最終集約265507と並行して実行し、共有lockと要求ノード数最大2の制限を維持した。
archiveとJSON memberのhash、全予定診断key、全設定行、保存flagの再構成を要求し、全件が通った。
sampling・decode・BAR・bootstrap・IAT・ESS・R-hatの再計算は実施していない。

結果は[summary.json](data_tile_validation_2026-10-17/c3t2_saved_diagnostic_census_v1/summary.json)、設定別の192反復集計は[settings.csv](data_tile_validation_2026-10-17/c3t2_saved_diagnostic_census_v1/settings.csv)に保存した。
summary.jsonのSHA256は`ec5425201f8566e4ded261e024c4a10a1ce127a3e68613d5edca81d56dc17261`である。
settings.csvのSHA256は`27f5cb1d7a1805da51bdc98662635b942e8a7ba29d92550acadd9d7ca55c0b10`である。
[receipt.json](data_tile_validation_2026-10-17/c3t2_saved_diagnostic_census_v1/receipt.json)にPBS終端・回収ファイルhash・クラスタ保存の群別詳細のhashとサイズを記録した。
同ディレクトリの`reproduction/`にsource・受入・入力指定・投入・観測・回収scriptを保存した。
再実行は新しい出力先と入力hashを照合してqsub投入し、既存の投入scriptや稼働中controllerをそのまま再起動しない。

この集計は結果を見た後に追加したものであり、事前校正や新しい推奨gateとして扱わない。
最終的な適用限界・設定間比較・計算効率の結論には、継続中の条件別集約、全12条件比較、独立計時と最終報告の照合が必要である。
