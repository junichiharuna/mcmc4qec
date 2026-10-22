# 復旧監査を用いるportable BAR最終reader

## 範囲

固定割当ての全condition providerと既存の最終joinを維持し、復旧collectorを用いた全trace監査backendを明示的に選ぶ。
元collector失敗の読み替え、portable結果のcluster結果への偽装、未回収・失敗・診断未定義の分母除外を行わない。
現在配置済みの復旧監査controlを変更せず、最終readerは別sourceとする。

## 接続契約

元 `condition_final_join` の別namespaceで、監査backendを外部hash固定された復旧実行configから構築したbackendに置き換える。
BAR値の再計算、summaryの数式、WSS reference監査、raw traceのhash照合、checkpoint検査の規則は変更しない。
元のreaderを通常の監査へ接続する動作も変更しない。
新readerのsource censusには元join、復旧監査control、最終adapterを含める。
復旧authorityのinput hashと旧成果物全fileのhashを、最終reportのinput evidenceへ追加する。
既存の証跡と同じpathに異なるhashや解決先がある場合は拒否する。
source/root・保存guard・復旧authorityをjoin前後と最終source検査時に再確認し、reference監査中の変化もreport受理前に検出する。
旧成果物のdirectory censusは復旧guardで確認し、既知fileのhash照合だけで追加fileを見逃さない。
reportには復旧authorityを記録するが、名目被覆・母RMSE・全物理状態の再復号を保証するfieldは従来どおりfalseにする。

## 実行入口

新CLIは元のsampling・audit・portable・reference rootとcontext hashに加え、配置済み復旧監査configのpath/hashを明示指定する。
configと監査controlのhashを確認してからworker moduleを読み込み、元sampling rootとfull監査rootの一致を必須とする。
実際の復旧collector・全trace監査・全portable群・独立referenceが揃うまで本番reportは作成しない。
qsub wrapperと回収入口は、このreaderの接続とは別に新CLI/configへのbindingが必要である。
本番final configは全群の実input censusと監査成功後に固定する。

## 受入

全12条件の合成768群で未取得区間・context失敗を含む67,584行と192 anchorの保持を確認する。
authority fileの変化、旧成果物の変化、異なるsampling root、証跡hashの衝突を拒否する。
元moduleの不変と元report関数のbytecode保持を確認する。
既存のreference・PBS・thread・出力先・再実行・入力変化の検査を新namespaceでも実行する。
fixtureの成功と、本番のraw trace・native decoder・reference照合の完了は区別して記録する。

## 実装と受入結果

`output/recovery_bar_final_v1/recovery_final_join.py` は元joinの別namespaceで復旧監査を選び、authorityと旧成果物のhashを最終evidenceに登録する。
元のreport関数のbytecode、全768群・67,584行・192 anchor、reference/PBS/threadの受入規則を維持した。
`recovery_final_cli.py` は配置済み監査configと既知worker sourceを先に検査し、sampling/full監査root・実Python入口・importしたcontrolの実pathを照合する。
CLI自身のsource hashもreportのsource evidenceに加える。
Windowsの統合受入は64 passed・34.42秒、Linuxは64 passed・17.24秒だった。
実Linuxの [読取確認](data_tile_validation_2026-10-17/recovery_bar_final_reader_native_v1/accepted.json) は、配置済み監査config `c1fded776101ec8ff167d0652ceb431cc730d218655ef7222a4a49152d0ac898` と元source/rootのbootstrapを確認した。
この確認では復旧collectorの正常完了authority、全群provider、実raw trace、referenceを結合する本番reportを実行していない。
Linux受入用sourceは `/home/user/workspace/mcmc4qec/20261020-recovery-bar-final-reader-v1` に保存した。
既存のcondition providerと通常joinは変更していない。
新旧reader source・受入ログ・native bootstrap・PC回収進捗と実PID観測は [30ファイルのmanifest](data_tile_validation_2026-10-17/recovery_bar_final_reader_progress_20261020_v1/manifest.json) に保存した。
manifest SHA-256は `6ae12850564e0d158f944b0b0f41ea4affecfa54fd735cf77f17415d881b65c2` である。

## 残る本番接続

新CLIと復旧audit configを固定するfinal qsub wrapper、全38 batchのcontext生成・転送、final reportの回収bindingが残る。
元のcondition qsub wrapperはcanonical Python binaryと通常CLIを前提にするため、そのまま新readerへ使わない。
元venv入口と実prefixを区別する既存の検証済みbindingを再利用し、復旧configをmetadataへ追加する別wrapperが必要である。
本番final config・resource・input censusは、全群回収と新監査の成功証跡を得てから固定する。
新CLIはfinal qsub jobの内部から呼び、本番計算をlogin nodeで直接起動しない。
現在はreader/CLIの受入まで完了しており、本番final qsub・report・回収は未実施である。
