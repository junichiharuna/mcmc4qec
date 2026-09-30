# RIMC 再利用可能ライブラリ仕様書

2026年9月29日現在  仕様案 v0.2

RIMCを他の研究者が自分の符号、ノイズモデル、デコーダーで利用・拡張できる公開ライブラリにする。公開APIの既定カーネルはZ+Hとし、各カーネルを独立に選択・組み合わせられる構成を目指す。

本書は、これまでに確認された方針と現行コードを整理し、実装に必要な設計案をまとめたもの。提案は合意済みの仕様と区別する。ライブラリの実装完了や公開済みを意味しない。

## 1 確定している要件

- 他の研究者による再利用・拡張を想定し、オープンソースとして公開する。

- 初期対象はCSS符号とし、bit-flip、depolarising、phenomenological noiseに対応する。circuit-level対応は将来の拡張目標とする。

- 新しい公開APIの既定はZ+H。OBF、Z-OBF、cluster exchangeを個別に使え、静的CSSではstabilizer flipを任意に追加できる。回路レベルでは、当面OBF・Z-OBF・cluster exchangeを候補とし、stabilizer flipを初期対応から外す方向とする。回路上の3候補の妥当性は今後検証する。

- 利用者が独自の符号、ノイズモデル、デコーダーを持ち込める。PyMatching、BP-OSD、Stimとの接続を容易にする。

- stabilizer flipとOBFの組合せのエルゴード性を扱う論文を今後まとめる予定。現時点で一般のデコーダーへの保証を宣言しない。

- BP-OSDでは失敗集合がpに依存し、通常のBARの前提が厳密には満たされないことを認識したうえで、現状は近似としてBARを用いる。

## 2 本書の読み方と対象範囲

| 区分 | 意味 |
| --- | --- |
| 確定 | 利用者が明示した目標・方針 |
| 現行実装 | 固定commitのコードから確認できた内容 |
| 提案 | 実装に向けた設計案。名称・既定値・公開方針は変更可能 |
| 未決 | 実装前または公開前に決定・検証が必要な事項 |

初期対応はCSS符号上のbit-flip、depolarising、phenomenological noiseとする。bit-flipを基盤抽出の出発点とし、depolarisingとphenomenologicalを初期公開に含める。circuit-level対応は次段階の拡張目標で、初期公開の必須条件には含めない。回路レベルのsplitting自体は既存研究で示されており、本ライブラリでの課題はその取り込みと各カーネルの適用条件の検証である。non-CSSへの拡張時期は未決。［E5］

DepolarisingではI/X/Y/Zの同時分布を扱い、YがもたらすX成分とZ成分の相関を保持する。phenomenologicalではデータ誤りと測定誤り、syndrome履歴を扱う。ラウンド数、初期・終端の測定境界、データノイズの種類、データ・測定誤り率の結び付け方は、以下の設計案で明示的に設定できるようにする。具体的な規約や既定値は未決。

現行確認対象は非公開リポジトリ junichiharuna/RIMC の main、commit 69efcfcc86af3bf24ca977a098dab0f348601aff。コードの読取確認のみで、テスト実行や証明の独立検証は行っていない。参照は第8節にまとめる。

## 3 構成と拡張用インターフェース

提案。計算の中核をファイル出力、コマンドライン、並列実行、研究用ジョブから分離する。ライブラリ用の別リポジトリを作り、現行研究リポジトリが依存する構成を推奨するが、分割は未確定。

| 層 | 責務 |
| --- | --- |
| core | 状態、符号または観測モデル、ノイズ、失敗判定、乱数、検証 |
| kernels | OBF、Z-OBF、cluster exchange、stabilizer flipと合成 |
| sampling / estimation | 失敗状態のサンプリング、direct MC、BARを用いた推定 |
| diagnostics / results | 診断量、名前付き結果、実行条件と警告 |
| adapters / io | PyMatching・BP-OSD・Stim接続、任意の保存形式やCLI |

### 3.1 共通契約の提案

- Modelは状態の次元・表現を定義し、syndrome(state)とobservables(state)を与える。CSS行列を使う実装では形状、二値性、可換条件、論理演算子との整合性を検証する。phenomenologicalでは、データ・測定故障を時刻付き状態として保持するspacetime modelを設け、syndrome履歴またはその差分からdecoder入力を構成する。どちらの表現を使うかと時間境界を明示する。

- NoiseModelはsample(p, rng)とlog_prob(state, p)を与える。log_probは同じ状態空間上の正規化された確率の対数を原則とし、確率ゼロを明示する。ここでpはノイズ条件の略記で、データ誤り率と測定誤り率を分離したパラメータ構造への拡張を想定する。同一の値とは暗黙に仮定しない。相関ノイズを許す契約と、各カーネルが対応するノイズの範囲を分ける。

- Decoderアダプターの共通出力は予測論理observableとする案。補正ベクトルを返すデコーダーでは、利用者指定の論理写像で変換する。型や長さから出力の意味を推測しない。

- FailurePredicateは状態と復号結果から失敗を判定する。標準判定は予測observableと真のobservableの不一致。独自判定も受け付け、exact計算、direct MC、MCMCで同じ定義を共有する。

- Proposalは候補状態と逆向き・順向き提案確率の対数比を返す。対称性を用いて省略する場合は、その成立条件を明記する。受理判定はノイズ密度比、提案比、失敗条件を組み合わせる。

同じpでのMH更新では状態に依らない正規化定数は相殺されるが、pをまたぐ確率比や絶対的な論理誤り率では一般に相殺されない。非正規化密度を許す拡張は、必要な定数または比を取得できる場合に限定する案とする。

### 3.2 現行実装との対応

CSSCodeとDecoder Protocolは既存。run_rimc_mixedはcodeとdecoderの注入、seed、各カーネルの重みを受け取れる。depolarisingの実装経路も現行コードにあるが、汎用公開APIへの整理と適用条件・テストの確認は別に必要。一方、direct_mcやsubset_samplingは符号名のfactory、並列処理、CSV保存との結合が残る。既存資産を移し替え、名前付きconfig・resultを公開する設計とする。phenomenologicalのspacetime modelと境界規約は新たに設計・検証する。［R2・R3・R5］

## 4 カーネルと実行条件

確定。公開カーネルは個別に選択・合成可能とし、既定プリセットをZ+Hとする。OBFはone bit flip、Z-OBFはZanella型のone bit flip、Hはcluster exchangeを指す。細部のAPI名と重みは提案段階。

| カーネル | 役割と適用条件 |
| --- | --- |
| OBF | 単一成分の提案。失敗集合とノイズsupportに対して受理判定する。 |
| Z-OBF | 重み付きの局所提案。選択確率と補正を一体で実装し、一般ノイズへの適用条件を示す。 |
| cluster exchange | 複数状態のcluster交換。符号・ノイズ・交換規則に依存する保存則と可逆性を確認する。 |
| stabilizer flip | CSSのstabilizerによる更新。任意追加とし、独自failure predicateでは不変性を確認する。 |

### 4.1 ZとHの既定値

READMEのZ+H例はp_zanella=0.7、p_cluster=0.3、cluster_k=2、n_replicas=1。これを新APIの初期候補とするが、Z+Hという方針以外の数値は未確定。現行runnerの既定はZ+PTであり、p_zanella=1、p_cluster=0、n_replicas=4。［R1・R3］

移行案として、新APIはZ+H、既存の研究スクリプト向けwrapperは旧既定を維持する。既定値の変更で過去の科学計算条件が変わらないよう、結果にはプリセット名と展開後の全パラメータを保存する。

### 4.2 Stabilizer更新と理論上の扱い

現行bit-flip実装はHxの行を一様に選んでXORし、iid bit-flipの重み差によるMH確率で受理する。syndromeとfailureの不変性を利用し、再復号を省略している。独自predicateや確率的デコーダーにこの高速経路を無条件で適用しない。［R4］

提案として、不変性を宣言・検査できる経路と、失敗条件を再評価する汎用経路を分ける。一般ノイズでは既存のハミング重み式を流用せず、log_probと提案比から受理確率を計算する。状態依存のstabilizer選択では提案比も必要になる。

エルゴード性の主張は、対象符号、失敗集合、デコーダー、support、カーネルの正の選択確率など、証明で必要な条件に限定する。現行ノートの主定理はgeneric weighted minimum-weight decoder等を仮定する。BP-OSDや一般モデルへの自動適用、有限時間の混合速度保証は行わない。［R9］

### 4.3 ノイズ別の更新設計

Depolarisingの局所更新はI/X/Y/Zのカテゴリ間の提案として設計し、順向き・逆向きの提案確率と同時分布のlog_probを用いてMH受理を計算する。X成分とZ成分を内部で二値表現しても、独立なbit-flip分布に置き換えない。phenomenologicalではデータ故障と測定故障の選択確率、時刻・位置・カテゴリの選択を提案比に反映する。対称提案を使う場合も対称性の条件を示す。

Z+Hを公開既定とする方針を保ちつつ、各ノイズでZ-OBFとcluster exchangeの状態表現・可逆性・不変分布を検証する。未検証の組合せへbit-flip用カーネルを暗黙に適用せず、対応状況を明示する。phenomenologicalでは、静的CSSのstabilizer更新が時間境界や失敗判定を保存するとは限らない。spacetime上の更新を別に定義し、既存のエルゴード性の定理もそのまま適用しない。

### 4.4 ノイズとカーネルの対応範囲

次表は実装の有無と採用候補を区別する。初期ノイズ対応の確定は、すべてのカーネルがすべてのノイズで検証済みという意味ではない。

| 対象 | OBFとZ-OBF | Cluster exchange | Stabilizer flip |
| --- | --- | --- | --- |
| 静的CSS bit-flip | 既存経路を公開APIへ抽出し検証 | 既存経路を公開APIへ抽出し検証 | 任意追加。predicate不変性等を確認 |
| 静的CSS depolarising | Pauliカテゴリ提案として既存経路との対応とMHを検証 | Y相関を含む同時分布に対する交換を検証 | 任意追加の候補。Pauli状態とfailureの保存を確認 |
| CSS phenomenological | 時刻付きデータ・測定故障に対して設計・検証 | Spacetime上の交換則を設計・検証 | 更新の定義と時間境界の保存を別途検証。静的更新を流用しない |
| Circuit-level | 次段階の候補。まず論文に基づく単一fault更新を独立実装し、Z-OBFへ拡張 | 次段階の候補。合法な物理故障配置と提案比を検証 | 当面の回路対応の対象外 |

### 4.5 入力検証の提案

- 混合確率は有限・非負・総和1を要求し、暗黙に再正規化しない。clusterの必要状態数、replica数、p ladderの整合性を確認する。depolarisingのカテゴリ確率、phenomenologicalのラウンド数、時間方向の状態形状、初期・終端規約も検証する。

- initial_stateは形状・support・失敗条件を検証する。見つからない場合は試行上限付きの初期化エラーを返す。seedと乱数生成器を明示し、並列workerの乱数系列を分離する。

## 5 推定 API と結果の意味

以下は公開APIの提案。既存関数の名称・返り値をそのまま公開するのではなく、利用目的ごとに入口を分ける。関数名、引数、結果型は実装時に確定する。

| 入口の候補 | 入力と返り値の要点 |
| --- | --- |
| sample_faulty | model、noise、decoder、p、config、seedを受け、失敗集合上の試料・実行情報を返す。 |
| estimate_logical_error | p ladder、基準点の推定、サンプリング設定を受け、論理誤り率・不確かさ・仮定を返す。 |
| direct_mc | 同じmodel・noise・failure定義で独立試行を行い、失敗数、試行数、推定値、区間を返す。 |
| diagnose | chainと実行情報を受け、自己相関、ESS、chain間比較、受理率等を返す。 |

### 5.1 BARとp依存デコーダー

現行実装は試料の重みとpからBARの比を計算する。BP-OSDを各pで構築すると復号則が変わり、失敗集合も変わり得る。この状況で通常のBARを近似として使うことは、既に認識された研究上の選択である。近似の精度や偏りの大きさは、現時点で保証しない。［R6］

提案として、固定decoder・固定failure集合で標準の前提を満たす経路と、pごとにdecoderを変える明示的な近似経路を区別する。後者を禁止せず、実行設定と結果にapproximationの有無・理由、各levelのsampling_pとdecoder_prior、復号器設定を記録する。名称や警告方式は未決。

固定failure集合でも、隣接分布のsupport・重なり、正しい密度比、基準点の絶対確率、十分なサンプリングは別に必要。depolarising、phenomenological、独自ノイズでは、iid bit-flipの重みだけによるBAR式をそのまま使わず、各モデルのlog_probを用いる。phenomenologicalのladderでは、データ・測定誤り率の変化経路と固定するラウンド数・境界条件を明示する。論理誤り率と条件付き試料の統計を明確に区別する。

### 5.2 結果と再現性の提案

- 名前付き結果に、推定値、不確かさと計算法、試行数・保存試料数、burn-in、chain/replica設定、実行時間、警告を含める。失敗ゼロを誤り率ゼロの確定値として扱わない。

- seed、乱数生成器、全config、符号・noise・failure定義の識別子、コードcommit、ライブラリとdecoderのversion、decoderの設定を保存する。可能なら行列・設定のhashを含める。phenomenologicalではラウンド数、初期・終端測定の規約、各故障の確率、syndrome履歴の表現を記録する。

- phenomenologicalの推定対象は、指定したラウンド数と境界条件の実験全体に対する失敗確率として明示する案とする。1ラウンド当たりの率へ換算する場合は、その定義と追加仮定を別に記録し、黙って換算しない。

- 受理率、IAT、ESS、R-hat、chain間ばらつき、replica交換、BAR overlap等を取得可能にする。定数系列・短い系列・推定不能な場合は理由付きで返す。

診断には現行postprocessの資産を活用する。診断が良好でも、エルゴード性、収束、推定値の正しさや近似BARの精度の証明にはならない。［R7］

## 6 既存ツールとの接続

確定要件はPyMatching、BP-OSD、Stimを使う研究者の導入を容易にすること。以下の接続方式と段階分けは提案。既存オブジェクトを受け取る薄いwrapperを優先し、利用者が既存の復号設定を保持できるようにする。

### 6.1 PyMatchingとBP OSD

| 対象 | 接続の設計と制約 |
| --- | --- |
| PyMatching | Matchingオブジェクトを受け取る。DEMやfaults_matrixの構成に応じた論理予測と、通常のcheck matrixから得る物理補正をoutput_kindで区別する。decode_batchは任意の最適化。 |
| BP-OSD | ldpc.BpOsdDecoderのdecodeを利用する。補正を論理observableに写すLを指定する。error_channelやupdate_channel_probs等の設定を保持し、固定decoderとdecoder_factory(p)を区別する。 |

PyMatchingではgraphlike性と分解を事前検証する。未分解の2個超のdetectorに作用する機構を黙って欠落させない。correlated matchingを使う場合は対応versionを固定し、構築時と復号時の両方の設定を揃える。［E1・E2］

DepolarisingのwrapperはX/Zの復号結果を共通observableへ写す。復号器がX/Zを別々に処理する場合も、サンプラーのY相関を失わせず、復号側の独立近似を設定として記録する。phenomenologicalではspacetimeのcheck構造とsyndrome履歴をdecoderへ渡し、最後のデータ状態だけを静的decoderへ渡す接続に置き換えない。PyMatching・BP-OSDのいずれも、採用する入力表現とノイズ条件との適合性を検証する。

### 6.2 StimのDetector Error Modelと回路レベルへの拡張

Stimはdecoder wrapperと分け、Detector Error Model（DEM）からmodel・noiseを作るアダプターとして扱う案とする。初期のphenomenological対応は明示的なspacetime modelで進め、Stim DEMとの接続は表現可能な範囲で検証に利用できるようにする。circuit-levelへの本格的な拡張は次段階とする。DEMの各error機構を独立Bernoulli故障変数とし、detector写像H、observable写像L、各機構の確率を構成する。復号結果と真のobservableの不一致を失敗とする。［E3］

- DEMの「^」は同じerror機構の分解の提案であり、各片を独立に再サンプリングしない。機構の同一性と相関を保持する。

- compile_sampler().sample(return_errors=True)の故障ビット、detector、observableを使い、モデルの写像とサンプリングを照合する。回路sampleだけを受け取っても、RIMCに必要な潜在状態とlog_probは得られない。

- 単一DEMだけではpに対するモデル族は定まらない。probabilities(p)または検証可能なdem_factory(p)を受け取り、初期対応ではp間で故障の同一性・次元・H/Lを固定し、確率のみ変える案とする。

- CircuitからDEMへの変換でapproximate_disjoint_errorsを無断で有効化しない。decompose_errorsも任意のhyperedgeで成功するとは限らない。I/X/Y/Zの排他的カテゴリ故障と独立Bernoulli機構列は同じ表現ではないため、元のdepolarisingや回路ノイズとの同等性・相関・近似の有無を確認する。導入された近似や未対応構造を報告する。［E4］

DEM対応から任意回路対応を自動的に主張しない。CSS向けcluster交換・stabilizer更新・エルゴード性の定理はDEMへ自動継承されない。汎用のsingle-fault提案から検証し、カーネルごとの対応表を公開する。

### 6.3 既存の回路レベルsplittingを取り込む経路

Rare Event Simulation of Quantum Error-Correcting Circuits（arXiv:2509.13678v2）は、回路レベルでsplittingを用いる既存研究である。状態はdecoder graphの辺ではなく物理的な(gate, fault)配置で、各gate locationは無故障または一つのfaultを取る。独立locationモデルにおける配置の確率と、失敗集合内の追加・削除・置換更新を扱う。rotated surface codeとMWPMによる数値実験を示している。［E5 第II・III・IV節］

提案として、CircuitFaultModelにlocationごとの排他的なfault alphabet、配置のlog_prob、配置からsyndrome・observableへの写像、failure oracleを分離して持たせる。これを既存のsplitting・BARと接続し、論文の回路・ノイズ・復号条件に沿う小規模な基準問題から検証する。Stim DEMへの変換を唯一の入口にせず、元の物理故障配置を直接扱う経路も設ける。汎用更新は一般のMH提案比、または対象範囲で詳細釣合いを確認した受理規則を用いる。

この論文の共通失敗集合上のBARを、p依存decoderの失敗集合の変化を補正する方法とは扱わない。第5.1節の近似BARの扱いは維持する。また、回路splittingの存在から本ライブラリの各カーネルの回路への適用可能性やエルゴード性を自動的には導かない。回路の初期候補はOBF、Z-OBF、cluster exchangeとし、stabilizer flipは対象外とする。候補ごとに合法性、提案確率、不変分布、到達可能性を検証する。

### 6.4 論文に基づく独立実装の作業案

2026年9月29日時点の本文・arXiv情報と関連する限定検索では、論文著者による公開コードは確認できていない。不存在を確認したものではない。公開コードが見つかることを前提にせず、論文の方法を独立に実装するbaselineを作る案とする。現時点で実装着手や再現成功を意味しない。

1. 回路、locationごとのfault alphabetと確率、復号器、ラウンド数、時間境界、失敗率の定義を論文の選んだ基準問題と一致させる。論文の受理式、提案選択、確率パラメータの適用範囲で解釈が必要な箇所は記録し、別の受理規則を採用した場合も明記する。
2. 物理fault配置と単一faultの追加・削除・置換を扱うbaselineを実装し、小規模状態でlog_prob・提案比・詳細釣合い・failure判定を検証する。標準BARの検証では共通failure集合という前提を揃える。
3. Direct MCで十分な失敗数を観測できる領域を用い、同じ回路・ノイズ・decoder・境界条件で推定値と不確かさを比較する。その後、論文の図表や希少領域との比較を進める。有限標本の一致だけで全領域の正しさを保証しない。
4. 検証したbaselineにZ-OBFとcluster exchangeを追加し、分布の整合性と効率を別々に評価する。実装元は論文に基づく独立実装と記載し、原著者のコード、検証済み再現、未検証の拡張を区別する。

## 7 実装と公開までの計画

提案。既存計算の再現性を保ったまま段階的に抽出する。以下は実装順の案であり、作業完了を示すものではない。

| 段階 | 主な成果物 | 完了条件 |
| --- | --- | --- |
| 1 基盤抽出 | src/rimc、pyproject、config/result、旧runner互換層 | wheelを別環境にinstallして主要例を実行できる |
| 2 初期ノイズと拡張契約 | CSSのbit-flip・depolarising、phenomenologicalのspacetime model、独自model/noise/decoder、kernel合成 | Y相関、測定誤り、時間境界、提案比と無効入力を検証する |
| 3 推定と診断 | 3種のノイズに対するdirect MC、BARモード表示、診断、再現性情報 | 小規模厳密値・既存条件との比較を説明できる |
| 4 初期アダプター | PyMatching・BP-OSD、phenomenologicalの履歴入力、導入例、可能な範囲のStim DEM照合 | 公式APIと各ノイズ・状態表現の対応をテストする |
| 5 初期公開準備 | CSSのbit-flip・depolarising・phenomenologicalの文書と例、CI、license、release手順 | 初期対応3種の受入条件と公開チェックを完了する |
| 次段階 回路baseline | 論文に基づく独立実装、CircuitFaultModel、単一fault更新、splitting、Direct MC照合 | モデル・時間境界・復号器を一致させ、提案比・詳細釣合いと観測可能な領域の推定を検証する |
| 次段階 回路拡張 | Z-OBF、cluster exchange、Stim DEM接続、近似表示。Stabilizer flipは当面対象外 | 分布の整合性と効率を別々に確認し、検証した範囲だけ公開する |

### 7.1 テストの受入条件

- 小さい符号を列挙し、同じFailurePredicateを用いた厳密値とdirect MC・MCMC・推定器を照合する。現行exact_ewはis_faultyを呼ばずlzで判定するため、独自decoderの基準値に流用する前に統一する。［R8］

- 各カーネルのsupport保存、失敗条件、提案比、詳細釣合いまたは必要な不変性を小規模問題で検証する。stabilizerのsyndrome・論理作用・predicate保存を分けて調べる。失敗集合内の到達可能性と周期性も確認し、必要に応じてlazy stepを設ける。MCMCの棄却による同一状態の反復を保持し、遷移した状態だけを標本にしない。

- DepolarisingはI/X/Y/Zの頻度、YによるX/Z相関、log_prob、カテゴリ提案の逆向き確率、両セクターの論理失敗を検証する。X/Z独立生成への誤った置換を検出する。

- Phenomenologicalは小さい符号・少数ラウンドでデータ誤りと測定誤りを列挙し、syndrome履歴・差分、初期・終端境界、decoder入力、実験全体の失敗判定を照合する。測定誤りゼロの極限は、ラウンド数や累積ノイズを揃えた参照問題と比較する。

- 固定失敗集合のBARを基準問題で確認し、p依存decoderの近似BARは別に偏り・感度を評価する。3種のノイズで使う密度比を各モデルの厳密値と照合する。診断の良さだけで近似の妥当性を判定しない。

- p=0/1、確率ゼロ、空の失敗集合、不正行列、NaN、初期化失敗、decoderエラーを扱う。seed再現性、並列系列の分離、serializationの往復、optional依存なしのimportを確認する。

- 既存testsを移植し、対応Python・依存versionでCIを実行する。テスト成功、性能改善、数値的一致は実際の実行結果で確認してから宣言する。

### 7.2 公開チェック

確認したtreeではLICENSE、pyproject.toml、setup.pyは見当たらず、testsは42ファイル。現在のCIはPython 3.11のリポジトリ内importを使う。パッケージ導入テストと公開用metadataは追加が必要。

採用license、依存ライブラリのlicense整合性、第三者コード・データの権利を確認する。PyMatching・ldpc・Stimはoptional dependencyに分ける案とし、対応versionを明示する。README、API説明、独自adapter例、数値上の制約、CHANGELOG、引用情報、貢献手順を揃える。研究データ、PBS設定、秘密情報の公開範囲も別途確認する。

## 8 未決事項と参照資料

### 8.1 次に決めること

| 決定事項 | 現在の整理 |
| --- | --- |
| リポジトリと名称 | 再利用ライブラリを別repoに切り出す案。package名、公開先、licenseは未決。 |
| 初期対応の詳細 | CSSのbit-flip・depolarising・phenomenologicalは確定。phenomenologicalのデータノイズの種類、ラウンド数、初期・終端測定、syndrome履歴の規約と既定値を決める。 |
| 将来の拡張 | circuit-levelは次段階の目標。論文の独立実装から始める案。採る基準問題、物理故障配置とStim DEMの対応、OBF・Z-OBF・cluster exchangeの検証順、non-CSSの優先度を決める。回路のstabilizer flipは当面対象外。 |
| 公開API | protocol、状態表現、result型、例外、後方互換の範囲を確定する。 |
| 既定の詳細 | Z+Hは確定。混合比、cluster_k、replica数、stabilizerの既定重みは未決。 |
| BARの表示と検証 | p依存decoderの近似利用は認識済み。モード名、警告、記録項目、評価例を決める。 |

### 8.2 現行コードの参照

すべて固定commit 69efcfcc86af3bf24ca977a098dab0f348601affを参照。非公開リポジトリへのアクセス権が必要。

[R1 README](https://github.com/junichiharuna/RIMC/blob/69efcfcc86af3bf24ca977a098dab0f348601aff/README.md)  実行例とZ+H設定

[R2 css_code.py 8–21行](https://github.com/junichiharuna/RIMC/blob/69efcfcc86af3bf24ca977a098dab0f348601aff/src/css_code.py#L8-L21)  CSSCodeとDecoder契約

[R3 runners.py 16–60行](https://github.com/junichiharuna/RIMC/blob/69efcfcc86af3bf24ca977a098dab0f348601aff/src/runners.py#L16-L60)  注入可能な入力と現行既定

[R4 kernels.py 210–217行](https://github.com/junichiharuna/RIMC/blob/69efcfcc86af3bf24ca977a098dab0f348601aff/src/kernels.py#L210-L217)  stabilizer flip

[R5 direct_mc.py 246–299行](https://github.com/junichiharuna/RIMC/blob/69efcfcc86af3bf24ca977a098dab0f348601aff/src/direct_mc.py#L246-L299)  factory・並列・保存との結合

[R6 splitting_pl.py 103–155行](https://github.com/junichiharuna/RIMC/blob/69efcfcc86af3bf24ca977a098dab0f348601aff/src/splitting_pl.py#L103-L155)  BARの比の計算

[R6補足 p1_pl_audit.py 168–184行](https://github.com/junichiharuna/RIMC/blob/69efcfcc86af3bf24ca977a098dab0f348601aff/cluster_scripts/p1_pl_audit.py#L168-L184)  各pでdecoderを構築

[R7 postprocess.py 118–162行](https://github.com/junichiharuna/RIMC/blob/69efcfcc86af3bf24ca977a098dab0f348601aff/src/postprocess.py#L118-L162)  chainの診断

[R8 exact_ew.py 72–99行](https://github.com/junichiharuna/RIMC/blob/69efcfcc86af3bf24ca977a098dab0f348601aff/compare/exact_ew.py#L72-L99)  厳密参照値のfailure定義

[R9 ergodicity_minweight.tex 555–564行](https://github.com/junichiharuna/RIMC/blob/69efcfcc86af3bf24ca977a098dab0f348601aff/misc/ergodicity_note/ergodicity_minweight.tex#L555-L564)  主定理の仮定

[R9補足 1201–1210行](https://github.com/junichiharuna/RIMC/blob/69efcfcc86af3bf24ca977a098dab0f348601aff/misc/ergodicity_note/ergodicity_minweight.tex#L1201-L1210)  適用範囲と制限

### 8.3 外部ツールの公式資料

[E1 PyMatching documentation](https://pymatching.readthedocs.io/en/stable/#loading-from-a-parity-check-matrix)  行列・DEM・復号出力

[E2 PyMatching matching.py](https://github.com/oscarhiggott/PyMatching/blob/master/src/pymatching/matching.py)  graphlike制約とcorrelations

[E2補足 LDPC BpOsdDecoder](https://software.roffe.eu/ldpc/ldpc/bposd_decoder.html)  channel設定とdecode API

[E3 Stim DEM format](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md)  error機構と分解

[E4 Stim Python API](https://github.com/quantumlib/Stim/blob/main/doc/python_api_reference_vDev.md)  DEM samplerと回路変換

[E5 Rare Event Simulation of Quantum Error-Correcting Circuits](https://arxiv.org/html/2509.13678v2)  回路レベルのsplitting、物理gate-fault配置、共通失敗集合上のBAR、rotated surface codeとMWPMでの検証
