# tile288のportable結果を独立計時へ接続する仕様

## 不足と範囲

既存の `portable_mixed` readerと最終PBS metadata readerはC0T2だけを受け付ける。
C1T0は `recovery_condition_qsub.py`、残る5条件は `planned_condition_qsub.py` を用い、元のC0T2 wrapperとsource・監査authorityが異なる。
これらをC0T2へ読み替えず、新しい明示経路 `portable_condition` と `collection_kind` を追加する。
対象は復旧collectorのC1T0、および初回collectorのC1T1・C1T2・C3T0・C3T1・C3T2に限定する。
公開候補と稼働中のsourceを変更せず、未配置の別directoryで小仕様・受入テスト・実装の順に進める。

## 親metadata段階

実最終config・投入・実行・完了・終端・report bytesを元schemaのまま照合する。
要求時間ではなく、正常終了した最終PBS jobの実walltimeと実peak memoryを返す。
条件・collector種別・固定wrapper・監査config・sampling manifest・portable contextの対応を明示して確認する。
対象を推測せず、boolを整数として受理せず、別条件・別wrapper・未完了・再実行・欠けた実測を拒否する。
この段階はmetadataとreport bytesの照合であり、raw trace・archive・native・WSSの再監査や科学的集計ではない。

## 後続の読取と選択

子readerは元snapshot、明示した監査authorityと対応するfinal join、元condition providerを使い、全768群・67,584行・192 seedを読む。
復旧collectorの失敗履歴と初回collectorのauthorityを混同しない。
全12条件が揃う前に正式設定を選ばず、既存の24行・352設定・192 seedの分母と選択規則を保持する。
source/native/import/Pythonの固定、子handleと親PBSの照合、入力変更検査を保つ。
metadata段階の受入、full readerの受入、親selectorとの接続、Linux配置、実入力候補、正式qsub、独立計時の完了を別々に記録する。
全体の独立計時の完了には残る条件の実reportと全12条件のselector入力・資源決定・実行・評価が必要である。

## 受入条件

旧recovered・C0T2経路のmetadata回帰を維持する。
6条件の正例と、条件・経路種別・wrapper・config・manifest・context・job・script・resource・実測の相違を拒否する例を用意する。
fixtureは小さいmetadataの例であり、本番の6条件や全12条件の数値検証を完了した証拠とは扱わない。

## metadata段階の実施結果

親metadata readerに `portable_condition` と明示的な `collection_kind` を追加した。
C1T0は復旧wrapper、残る5条件は初回collector用wrapperへ限定し、descriptor・config・元manifest・context・監査config・実PBS終端の対応を照合する。
内部planの `size` は符号長288ではなくtileの寸法12であり、既存planと同じ表現で検査する。
科学計算moduleはimportせず、sampling・BAR・ACF・WSSの再実行は行わない。

最初の受入は新経路の正例6件が未対応で失敗し、実装後は旧経路の回帰26件を含む94件が成功した。
保存した最終受入はWindows94件・10.32秒、Linux94件・1.28秒である。
Linuxは `20261021-low-timing-condition-metadata-v1` の隔離配置を使用し、元sourceと既存jobを変更していない。
source・実行script・両環境のstdout/stderr・受入記録は [保存manifest](data_tile_validation_2026-10-17/low_timing_condition_metadata_acceptance_v1/manifest.json) に保存した。
manifest SHA-256は `692e9fc06db1cdac128ea336c152b3a62aa0fff44616417d137f0af3738e4f22`、受入JSONは `875851dc127111c6ad2dd844613eaa3d73711b6bd3d87ba88e44b7484aa19298` である。

検査は小さいmetadata fixtureを使い、予定6条件の実final reportはまだ取得していない。
親metadataの成功をfull context・wrapper実行・raw readerの検証とは扱わず、返り値でもそれらをfalseに保つ。
残る作業は各authorityに対応したfull reader、selector親と子入口の新経路接続、実source/native環境と全12条件の入力・資源準備、正式実行である。
サブエージェントの利用上限により、この追加変更の別エージェントによる独立レビューは未実施である。

## full readerの追加仕様

snapshotのwrapper検査後、同じconfigの監査bindingを元の `load_recovery_audit` または `load_planned_audit` へ渡し、元final CLIと同じjoin・provider・追加sourceを構成する。
元reportのsource集合にはproviderも含め、数値比較moduleの一致だけでsource全体を受理しない。
collectorのledgerはC1T0では `sampling-collection-submission-retry-v1`、残る5条件では `sampling-collection-submission-budget4h-v1` を使う。
いずれもaudit manifest内の完了collectorとauthorityのjob IDが一致しなければ拒否する。
C1T0の旧collectorも実qstatで照合し、元のwalltime失敗・Exit_status=-29・run_count=1を保持する。
元collectorを正常終端へ置き換えたり、PC計算へPBS job IDを割り当てたりしない。
全source・入力・terminalの対応と全rowの再集約を通した後も、選ばれるのは独立評価候補であり、混合・精度・名目被覆を認定しない。

## full readerと接続の受入結果

WindowsとLinuxでそれぞれ167件が成功し、内訳はreader・集計回帰73件、子processとdispatch68件、親wrapper26件である。
Windowsの各群は18.79秒・11.52秒・21.50秒、Linuxは7.48秒・13.38秒・13.34秒だった。
最初のLinux配置は検証script内の `PAYTHON` 誤記で停止し、その記録と配置を保持したまま、修正版を別配置で実行した。
成功した受入は [保存manifest](data_tile_validation_2026-10-17/low_timing_condition_reader_acceptance_v2/manifest.json) に保存した。
manifestのSHA-256は `b2a3bbafa1b69bd82fe5143a0affc043b44677b7e65d29766e181c30d610c406`、受入JSONは `98b28dad5764f944e8904b60c25795887f863e587f5c71121710b421f7b89b27` である。
これらは小さい合成row・模擬authorityを含む受入であり、本番6条件のraw読取や独立計時の完了ではない。

## 実復旧authorityとの接続確認

次の軽い実機検査では、テスト済みreaderを別配置し、既存のC1T0 final helper・元venv・復旧audit configを外部hashで固定して、`dependencies` と元joinのsource照合を実行する。
監査authorityが指す成功collectorと保持された失敗collectorを確認し、全入力sourceを前後で再照合する。
本番final configはまだ未作成なので、検査用の最小bindingを明示し、これを本番設定や子process全体のbootstrap検証とは扱わない。
raw traceの読取、全群contextの生成、復号、BAR再集計、新しいqsubは行わない。

実クラスタの元venvでこの接続確認を実施し、254 sourceの前後一致と元joinの56 sourceを照合した。
新readerの `dependencies` が実際のC1T0復旧authority・join・providerを構成し、成功collector265362と保持された失敗collector265356を返すことを確認した。
新readerと元snapshotのimport先も照合した。
結果は [実機接続manifest](data_tile_validation_2026-10-17/low_timing_condition_native_recovery_v1/manifest.json) に保存し、SHA-256は `5b733368551cb4a1fc2cbf2962812cc572fd02f1d64ebc426a8ec17223c3989a` である。
本番final config、全子processのbootstrap、raw reader、全12条件の正式選択、独立計時は未実施のままである。

## 子process環境の準備

C1T0の子reader環境を別配置に準備し、元venv、全core source、静的な推移的import、明示的に選ぶsnapshot・CLI・join・provider、native binaryを記録する。
静的解析で見えないroute固有のimportは明示的な起点に加え、動的に読むaudit controlは元CLIの外部hash付きconfig検査を引き続き通す。
実際の別processで既存 `bootstrap` を前後に呼び、途中で実復旧authorityを構成してもsource・import先が変わらないことを確認する。
この段階では本番final config、親PBS、実入力全体、数値結果を受理せず、環境準備とraw読取・正式選択を分けて記録する。

C1T0の実子processで100 source・137 native binaryを記録し、実復旧authorityの読込前後に既存bootstrapが成功した。
元joinの56 sourceも照合し、stderrは空だった。
環境JSONのSHA-256は `cf7d8425f042a6d01bd83fc82e7200cf061122a4ebb397ced54bc1d94714dc3c` である。
[環境準備manifest](data_tile_validation_2026-10-17/low_timing_condition_environment_recovery_v1/manifest.json) のSHA-256は `514248d6ca654dc05516205ba879e7f316d13a2f5370fa575594cc0b053f39b8` である。
これは本番親PBSや全入力を含む実child実行ではなく、最小bindingによる環境の検査である。

残る5条件は共通の初回collector用sourceと元venvを使うため、別配置に共通環境を準備する。
collector完了前はauthorityを構成せず、各条件の元CLI `bootstrap` で外部hash付きaudit config・collector config・bundle sourceを読み、sampling root・full監査rootの対応を照合する。
初回collector用環境の成功を、5条件の実authority、最終report、raw読取の成功として扱わない。

初回collector用の共通環境も実子processで100 source・137 native binaryのbootstrapが前後とも成功した。
C1T1・C1T2・C3T0・C3T1・C3T2の5設定を元CLIでbootstrapし、sampling rootとfull監査rootの対応を確認した。
stderrは空で、未完了のcollector authorityを構成する呼出しは行っていない。
環境JSONのSHA-256は `d756ee0ece45d90bb0d90ea0865aa55ff2269afcc257dc586e191cc51da0efd7` である。
[初回collector用環境manifest](data_tile_validation_2026-10-17/low_timing_condition_environment_planned_v1/manifest.json) のSHA-256は `4c1a4b0cd182fe72f1a348367364215be81d9b09d370ca576c0f4e4e43b36693` である。
復旧用12ファイルと初回collector用13ファイルを各保存manifestで再照合した。
この2環境は親PBSの照合、本番final config、正式な全12条件の入力準備をまだ含まない。

## 最終回収からmetadata候補への接続

対象はC1T0・C1T1・C1T2・C3T0・C3T1・C3T2に限定する。
既存collectorが保存したbefore/after snapshot、受理receipt、13成果物を元のsnapshot validatorと外部hashで照合する。
条件・collector種別・remote final root・sampling root・監査root・元Python・元helperのimport先が一致しなければ準備しない。
既存の独立reference候補から共通metadataのpinだけを引き継ぎ、対象conditionのmarkerとartifactは元のcase/prior照合に従って追加する。
新しい候補はmetadata準備として保存し、raw再監査・本番親PBSの照合・全12条件の選択・独立計時を完了したとは扱わない。
未回収や失敗したreportを成功へ置き換えず、保存済みの候補先を再使用しない。

入力候補の組立25件、remote metadataの11件、待機・一度だけの呼出し7件の計43件がWindowsで4.26秒、Linuxで0.69秒で成功した。
remote metadataの検査では元のmetadata readerとcase/prior照合を使い、native bootstrap・wrapperの実file・PBS問合せは模擬化している。
localのsnapshot委譲も組立試験では模擬化し、別の2件で固定した元validator sourceを読んでいる。
したがって、本番reportでの候補作成を実証した受入ではない。
実referenceの `conditions/5.done.json` をread-onlyで確認し、identityがmanifestとcondition、artifact拡張子が `.json` と `.npz` であることを確認した。
[候補接続の受入manifest](data_tile_validation_2026-10-17/low_timing_condition_candidate_acceptance_v1/manifest.json) のSHA-256は `1de73a6af37d97a3d3b4a5ded7da5ef39bed81fc3bdebbd37dcdc42678a36c39` である。
起動前に175 sourceと6条件の既存最終処理handleの継続を確認し、保存manifestの182ファイルも再照合した。
最初のrunpy形式の起動はimport経路不足で停止し、待機directoryが未作成であることを確認して、通常のscript形式で起動した。
02:54にPID24708・session10693の継続を確認し、6条件とも既存最終回収の完了待ちである。
待機記録は `data_tile_validation_2026-10-17/low_timing_condition_candidate_handoff_v1/` に保存する。
新規qsub、本番metadata候補作成、全12条件の正式選択、独立計時はまだ未実施である。

## 親prepared値の追加照合

親wrapperの `prepared_value` は旧2経路だけを対象にしており、`portable_condition` の親script・資源・子出力directoryとの対応を照合していなかった。
子側には実親PBSの検査が残るが、不整合なdescriptorは親の準備時点でも拒否する。
既存の受入済み配置と稼働sourceは保持し、親wrapperだけを別版にして新経路を同じ照合対象へ追加する。
6条件の正例、script・資源・directoryの不一致、旧2経路の同検査を受入で確認する。

修正前に新経路のscript・資源・directory不一致の3件が拒否されないことを確認した。
別版への追加後、単体15件と既存親処理の回帰26件がWindows・Linuxの両方で成功した。
Windowsは0.80秒・20.97秒、Linuxは0.06秒・12.81秒だった。
[親binding受入manifest](data_tile_validation_2026-10-17/low_timing_parent_binding_acceptance_v1/manifest.json) のSHA-256は `d99b9b362ea2160638d086ff7dae99b690e409bc6de6dcea083d474bd59925ba` である。
次にこのwrapperと新reader入口を専用の `cluster_scripts` に配置し、親のsource/bootstrap契約を元venvで確認する。
この検査では全12条件の入力、資源決定、親PBS、本番selectorをまだ構成・実行しない。

専用配置の元venvで親bootstrapが前後とも成功し、親source93個・native binary137個・selector source53個を照合した。
元reportのsource closureとruntime契約も照合し、stderrは空だった。
親環境JSONのSHA-256は `5433c9747ff581fb9273f52ff628c6538712a489e1791848b32bfd8bab0087cb` である。
[親環境manifest](data_tile_validation_2026-10-17/low_timing_parent_environment_v1/manifest.json) のSHA-256は `306c48d91d02d26cb4a18257a6ee8fe12dde2b9dc28ed8679c044790689c61e3` である。
親binding受入180ファイルと親環境10ファイルを各manifestで再照合した。
全12条件の入力と実測を使った資源決定、本番selector、独立計時は未実施である。

## 初回collectorの実authority接続

C1T1 collector265370が正常終了したため、準備済み初回collector用環境で実authorityの構成を確認する。
元のcollector完了受理、audit config、元join・provider・snapshotの対応を照合し、既存bootstrapを前後に呼ぶ。
これは最小bindingを使う接続確認であり、full trace監査や最終report、raw読取の代替ではない。

元venvの実processでC1T1の初回collector authorityを構成し、collector265370と復旧履歴なしの契約を確認した。
source100個・native binary137個のbootstrapが前後とも成功し、元joinの201 sourceを照合した。
[実初回collector接続manifest](data_tile_validation_2026-10-17/low_timing_condition_native_planned_c1t1_v1/manifest.json) のSHA-256は `3a25be6813ebea9cc100ebee8275ad6d748b5bb5ddc258e6647b255ca93cc096` である。
保存6ファイルを再照合し、full trace監査・本番final config・raw readerは未実施として保持した。

## 既存staged条件との親環境互換性

既存C2T0・C2T1・C2T2のmetadata候補はstage2専用venvと元の比較module配置を前提にしている。
親環境v1のbootstrap成功だけではこの契約を確認できておらず、元環境と比較するとPython入口と比較moduleのimport先が異なるため、正式な全12条件用環境にはまだ採用しない。
v1の記録は保持し、既存staged親環境を基準にした別配置で新しい親wrapperとreader入口を重ねる。
元runtime・core・非置換moduleのimport先を保持し、3条件それぞれの保存planと比較moduleのsource契約を実metadataで確認する。
raw trace読取や数値再集計は行わず、この成功を全12条件の入力受理と区別する。

親環境v2の実子processで元runtimeを保持し、93 source・137 native binary・selectorの53 sourceを照合した。
既存stagedの3条件とも保存planが元 `make_plan` と一致し、保存reportの数値比較source契約も一致した。
親環境JSONのSHA-256は `c1599d70a98822261653ef182c2fe27bcda1c237766c164f5b3c0442e53b1d3c` である。
[親環境v2 manifest](data_tile_validation_2026-10-17/low_timing_parent_environment_v2/manifest.json) のSHA-256は `93db36d0ce975af8ee0a5daa03952f807d237a820a4cccd8d586a7ea9b8e0bcd` である。
v1は保存したまま正式な親入力の候補から外し、以後の組立はv2を基準にする。

## 全12条件の入力組立と資源方針

case0〜3・target0〜2の固定順で12候補を要求し、欠落・重複・順序違い・未完了があれば組立を行わない。
case0は復旧2条件とportable1条件、case1とcase3は明示的portable条件、case2は既存staged条件を保持する。
isolated子processの出力先を親root内の専用directoryに固定し、親scriptと同じ資源を渡す。
資源基準は各finalの実測walltimeとpeak memoryで、finalに含まれるcollectionを二重計上しない。
追加hash予算は各final時間の25%または60秒の大きい方とし、staged条件ではcopy実測の2回分に1.25倍を掛けた値も下限に含める。
walltimeはその合計の1.5倍に600秒を加えて300秒単位で切り上げ、memoryは実測最大の2倍と32 GBの大きい方を使う。
これは計算資源の余裕を決める方針であり、実行時間や精度の保証ではない。
要求が既存wrapperの24時間・340 GB上限を超える場合は切り詰めず、実行を止めて別の実行設計を検討する。
qsubは既存wrapperの全12条件検査、実metadata検査、共有lock、最大2要求ノードの確認を通して行う。

全12条件の組立・共有reference・親子対応・資源計算・未完了拒否・上限超過拒否・collection二重計上拒否の16件がWindowsで0.55秒、Linuxで0.03秒で成功した。
これは合成metadataによる算術と組立の受入であり、実12条件の資源決定や正式parent準備ではない。
実inventoryを読むと6/12候補が準備済みで、関数は部分候補を後段へ返さず、全12条件準備済みをfalseに保った。
[入力組立受入manifest](data_tile_validation_2026-10-17/low_timing_input_assembly_acceptance_v1/manifest.json) のSHA-256は `901eb9b93cb8bcefb7d12de1483cc07a554cefd6009f03cd5b7ab50ed27efc49` である。
親環境v2の11ファイルと入力組立受入の11ファイルを各manifestで再照合した。
実12候補の収集、子環境の読込、親入力・acceptance・資源JSONの保存、既存wrapperの実検査と正式qsubへの接続は引き続き残る。
