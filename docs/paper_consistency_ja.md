# 論文の手順とライブラリの BAR の整合

この表は読み取り専用の `RIMC/paper/main.tex` の 2026-10-01 時点の記述とライブラリの公開既定を比較したものであり、論文の図表を再現したという意味ではない。
WP-P の被覆比較は Q 統合後の dev5 main で固定20 seedを計測し、詳細を [BAR感度の最終表](bar_sensitivity_ja.md) に記録した。

| 項目 | 論文の根拠行 | ライブラリの状態 | 判定 |
| --- | --- | --- | --- |
| 独立 chain 数 | Setup 600–602、615–623 | `SamplingConfig` の既定は 1 chain、dev4 の曲線例は 4 chain、論文は 50 chain | 違う |
| 保存長 | Setup 600–602 | 論文の平均重み benchmark は各 chain 2,000,000 step、曲線例は保存 600 step | 違う |
| burn-in | Setup 609、研究 `src/postprocess.py` 35–91 | 論文は反復 Geyer IAT の 5 倍を切り、非収束なら半 trace を切るが、API 既定は固定 100 step | 違う |
| 実験 runner の cut 単位 | 研究 `cluster_scripts/lowp_audit.py` 267–277 | 研究 runner は各 chain に 1D の burn 手順を適用し、WP-P benchmark も各 chain 別 cut を用いる | benchmark で対応 |
| 誤差棒 | Setup 615–623、658–660 | 論文の式は観測量の chain 平均の標本分散を K で割るが、API 既定の BAR 区間は block bootstrap | 違う |
| BAR への cross-chain 適用 | Setup 615–623、results 987–1031 | 追加 `uncertainty="cross_chain"` は chain ごとの BAR log ratio 共分散を K で割り、共有 rung の相関と独立 anchor 分散を伝播する | ライブラリ側の漸近的適用、論文の直接検証対象外 |
| production kernel | Setup 603–606 | 論文は Z 0.7 と H 0.3、交換サイズ 2 で、ライブラリの公開混合と一致する | 同じ |
| lazy step | 研究 `src/runners.py` 17–35・167–202 | 研究 production runner に独立 lazy 抽選はなく、ライブラリ既定は 0.05 で、WP-P の paper 構成は 0 にする | 違う |
| 研究 runner の API 既定 | 研究 `src/runners.py` | runner の既定は Z+PT であり、論文の production 設定 Z+H と区別する | 論文 production と違う |
| 初期状態 | Setup 602、results 820–822 | 論文は最小または最大の論理 X 基底から開始し、API 既定はノイズ標本から失敗状態を探索する | 違う |
| 多初期値検査 | Setup 669–681、results 820–822 | toric d=3 の最小と最大の基底状態は同一なので、WP-P benchmark は論文の検査を vacuous と表示する | この符号では実質未検査 |
| 収束規則 | Setup 664–680、研究 `compare/convergence_flags.py` 25–105 | 1/4 対全長の散らばり、直前四半分対後半の drift、多初期値、chain 内分散と IAT の予測の四条件を全て扱う | benchmark で判定、証明ではない |
| 収束規則の trace | 研究 `cluster_scripts/lowp_audit.py` 234–251・267–324 | 研究実行は scaling と drift を未burnの prefix、multistart と dispersion を各 chain の 5·IAT cut 後に適用する | benchmark で対応 |
| 評価 p の領域 | 導入 153、Setup 588、results 905–907 | 論文の主な領域は 10^-1 から 10^-5、dev4 の問題点 p=0.22 は範囲外 | 違う |
| ladder と anchor | splitting 248–282、results 997–1008・1022–1027 | 論文は高 p の direct MC anchor と隣接 BAR 比の積、幾何的 ladder の例を述べ、ライブラリは任意の順序付き座標と exact または MC anchor を許す | 方法は同じ、既定 ladder はない |
| BAR の式 | splitting 261–282 | 論文の Fermi 関数 `h(t)=1/(1+t)` と self-consistent ratio に `bennett_log_ratio` の score が対応する | 同じ |
| 論文の end-to-end 評価 | results 987–1031 | 論文は full BAR estimator の end-to-end cost を未実行と明記しており、平均重みの cross-chain SE は BAR 被覆の保証ではない | ライブラリでも独立評価が必要 |

`cross_chain` は独立で定常な chain の有限標本散らばりを用いる不確かさの近似であり、点推定の bias と混合不足を含まない。
20 seed の被覆数と Wilson 区間だけで名目 95% 被覆を確証したり、設定を最適化したりしない。
WP-P の論文寄せ16/50 chainは各chain raw250で、研究の2,000,000 stepとは大きく違う。
全ての16/50 chain構成で20/20 seedに半trace cut上限のchainがあり、cut後の保存数はchainごとに違った。
正式な論文multistartはtoric d=3の同一basisで実質未検査なので、異なるfaulty startの補助四条件と分けて報告した。
default4とpaper16/50はchain数、開始、lazy、burn、長さが同時に違い、paper16対paper50だけが同じraw250のchain追加比較となる。
低pでMC/exact anchorを同じBAR軌道に適用すると点推定と区間の双方が変化し、有限20 seedの被覆差をどちらかの一般的優劣とは扱わない。
`cross_chain`の2chainは計算可能な下限であり、少数chainの分散推定とlog尺度の正規近似の精度を保証しない。
実行条件、全seedのCSVと派生解析は [dev5データ](wp/data_dev5/README.md) に保存した。
