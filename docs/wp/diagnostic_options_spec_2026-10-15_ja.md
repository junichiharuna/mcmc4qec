# オプション付き数値診断の追加仕様

依頼は、統計誤差とMCMC統計量を計算結果と同時に返し、追加計算を選択可能にすることである。
`sample_faulty` と `estimate_logical_error` にkeyword `diagnostics=False` を追加する。
追加指示により、統計誤差は標準で返し、詳細診断だけをオプションにする。
`False` でも従来の軽量診断が計算したIATを再利用し、chain別・平均の標準誤差を計算するが、追加のACF・ブロック解析を呼ばない。
`Result.conditional_weight` と `Result.conditional_weight_standard_error` に条件付き重みの平均と標準誤差を格納する。
`diagnostics["mean_standard_error"]` は独立chainを仮定した sqrt(sum_j s_j^2 tau_j / n) / K とし、定数・短いtraceなどで一つでもIATが未定義ならNoneとする。
標準誤差は診断対象の平均に対するMCSEであり、サンプル値自体の標準偏差とは区別する。
direct MCのWilson区間とBARの既定誤差区間も従来どおり返す。
`True` または `DiagnosticsConfig` を渡すと、`Result.diagnostics["trace_analysis"]`、BARでは各rungの `EstimationResult.diagnostics[i]["trace_analysis"]` に解析を格納する。
対象は保存済み状態の非identity座標数であり、burn-inの再除去や間引きの追加は行わない。
自己相関のlagとIATの単位は保存サンプルであり、samplingのthinも補助情報として記録する。
詳細解析の標準誤差とbootstrap区間はこの条件付き観測量の平均に対するものであり、BARの論理誤り確率区間とは別に格納する。
追加計算のseed既定は0とし、samplingとBARのRNGを消費しない。
同seedで有効化前後の状態、acceptance、BAR点推定・既存誤差区間・共分散が等しいことを受入条件とする。
計算量と返却量を制御する設定は最大lag、ブロック長列、bootstrap反復数とseedである。
bootstrap反復数0はbootstrapだけを省略し、1は分散推定不能のため拒否する。
不正設定はサンプリング前に拒否する。
後処理用 `diagnostic_report` は既存Result群と任意のスカラー観測量を扱い、状態を変更しない。
任意の数値traceには `analyze_traces` を公開する。
既存のclassical split R-hatとchainごとのGeyer IATを使用し、rank-normalized R-hatやbulk/tail ESSとは区別する。
定数・短いtraceで算出できない量はNoneと理由を返し、良好な診断や狭い区間を収束または名目被覆の保証とは扱わない。
グラフの自動作成は行わず、ACF配列・ブロック長別の数値を返す。
数値公式と検証仕様は `trace_stats_spec_2026-10-15_ja.md` に記録する。
