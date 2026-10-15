# BAR の省略時設定と自動 anchor

## 仕様

`estimate_logical_error(problem, ladder)` で `config` と `anchor` を省略できるようにする。
`config=None` は既存の `SamplingConfig()` と同じで、保存1000サンプル、burn-in 100、thin 1、1連鎖、Z/H=0.7/0.3、cluster_k=2、lazy=0.05を維持する。
物理回路のグループ指定など、モデル固有の明示設定が必要な制約は変更しない。

`anchor=None` の場合、先頭rungの問題とノイズ強度で基準値を自動計算する。
状態数は `problem.alphabets` の積で数え、`anchor_max_states=4096` 以下なら `exact`、超える場合は `direct_mc` を `anchor_trials=10000` 回実行する。
両方ともkeywordで変更でき、`anchor_max_states=0` は全列挙を無効にする。
自動計算時の上限は非負整数、試行数は正整数とし、boolや非整数は受け付けない。
明示的な `anchor=Result` を渡す場合はこれらの自動計算用設定を使用せず、既存の検証と計算経路を維持する。
MCは固定試行数で実行し、失敗数に応じて試行を追加したり、全列挙の検証エラーをMCへの切り替えで隠したりしない。

自動MCにはrungとbootstrapから独立した追加の子seedを使い、既存rungとbootstrapのseed系列を変えない。
同じseedと設定で再現できるようにし、自動anchorの採用方法・設定と、Resultに含まれる試行数・失敗数・乱数情報を最終結果のmetadataに残す。
近似モードでは先頭rung用に構築したデコーダーを使ってanchorを計算し、元のproblemのデコーダーで代用しない。
anchorの分散は従来の誤差伝播に組み込み、MCの少数失敗時の注意も維持する。

全列挙で失敗確率ゼロ、MCで失敗ゼロまたは全試行失敗の場合は、既存のanchor受入条件を満たさないためValueErrorとする。
自動計算時には試行数や先頭のノイズ強度の変更、明示anchorの指定を案内する。
正の確率が浮動小数点でunderflowするexact結果は、従来どおり有限のlog_estimateで扱う。
BARの引数検証（ladder、configの型、誤差法、bootstrap、自動計算予算、初期状態リストの件数、近似モードの指定）で検出できる不備は自動anchorの計算前に拒否する。
モデル固有のkernel制約や個々の初期状態の検証は、従来どおりサンプリング開始時に行う。

## 受入確認

- configとanchorを両方省略した小状態の実行と、明示exact・明示SamplingConfigでの同seed計算が一致する。
- 自動MCの固定試行数、先頭rungの分散、独立seed、再現性、明示anchorへの置換でrung・bootstrapが変わらないことを確認する。
- alphabet積による閾値判定、近似モードの先頭decoder、dict座標、JSON往復を確認する。
- ゼロ失敗・全試行失敗・exactのゼロ質量・不正な設定を拒否し、exactの検証エラーを隠さないことを確認する。
- READMEの短縮した例、文書リンク、既存BAR関連テスト、strict型検査を実行する。

## 検証状況

仕様を先に記録し、新規受入テスト25件と利用者側の型テストが未実装APIで失敗することを確認してから実装した。
独立レビューで挙がったexact確率1の受入と、NumPy整数のalphabet積のoverflow防止を追加し、新規受入テストは27件が成功した（2.85秒）。
後者は状態数が2^64の場合に誤って全列挙へ入る失敗を確認した後、Python整数で数える実装に直した。
提案・受理・サンプル保存のコードは変更していない。

変更前に明示exactと明示MCの結果を保存し、変更後の点推定・区間・診断・bootstrap共分散・warningsが同seedで完全に一致することを確認した。
BAR関連・文書・型検査の計49件は14.21秒で成功し、その後の境界テスト2件も成功した。
独立レビューでは、追加seedが既存rung/bootstrapを変更しないこと、anchor分散の伝播、近似モードの先頭decoder使用を確認した。

isolated buildでwheelを作り、installed core wheelの関連テスト48件が成功した（12.53秒）。
`verify_wheel.py core` も成功し、wheel/sourceの全28 Pythonファイルの一致、core実行例、READMEとtutorialの独立コードブロックを確認した。
最初のno-isolation buildは環境の旧setuptoolsが現行license設定を受け付けず失敗したが、指定されたsetuptoolsを使う通常のisolated buildで解消し、パッケージ設定は変更していない。

toric d=3、ladder=[0.2,0.15]、seed=73でconfigとanchorを両方省略して実行した。
自動MCは10000試行で5663失敗を観測し、BAR点推定は[0.5663,0.422321432756135]、両点の区間も得られた。
これはAPIの動作確認であり、混合・精度・名目被覆率の検証ではない。
自動anchorの予算設定と採用方法は最終結果のmetadataに保存され、MCの乱数情報と試行数・失敗数もJSON往復で保持される。

source全suiteは491 passed・5 skipped、176.32秒で成功した。
strict型検査と利用者側の型テストも含み、最長の単一テストは11.23秒だった。
Windows notebook実行時の既存zmq警告が1件あり、テストの失敗はなかった。
実行ログと変更前の比較用出力はgitignore対象の `output/automatic-anchor/` に保存した。
