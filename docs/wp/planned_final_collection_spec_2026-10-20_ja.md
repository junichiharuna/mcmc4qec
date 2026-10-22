# 初回collector条件の最終report回収

## 小仕様・受入条件

C1T1・C1T2・C3T0・C3T1・C3T2の最終reportを、既存処理と別の回収入口で扱う。
外部からcase・target_index・config hash・terminal hashを明示し、対象5条件以外とboolによる整数代用を拒否する。
reportの条件と予定67,584行・192 seed・352設定、および検証範囲のflagを要求する。
固定wrapperと完全なsource censusをimport前に検査し、wrapperが要求する初回collector authority・full監査・入力・reader sourceをreportと照合する。
13成果物のmetadataとreportを転送前後に照合し、PBSの正常終了・実行回数1・script・資源・job ID・hostnameを結び付ける。
元回収処理の保存先排他、曖昧な結果と失敗証跡の保持、hash照合、転送中改変の拒否を維持する。
回収処理自身はqsub、数値再計算、raw trace再監査を行わない。
全5条件の正常snapshotと不正条件、source/census不一致、転送失敗をfixtureで確認する。
Linuxで実wrapperのprepareから最終回収までを結合し、PBS応答と科学I/Oを置換した範囲を明記する。
本番reportが存在するまで、fixture成功を実回収成功と扱わない。

## 実装・受入・配置

planned_final_collection.pyを既存回収処理から明示的な差分で導出し、source textとbyteの一致を保つLFで保存した。
Windows46 passed・8 skipped・3.21秒、Linux54 passed・1.47秒だった。
Windowsで未実施の8件はLinuxで実行し、import前のsource censusと、実wrapperのprepare・投入記録・compute・completeから回収snapshotまでの結合を確認した。
PBS応答と科学I/Oはfixtureに置き換えており、本番のqsubや最終report成功を示さない。
全5条件のsnapshot受理と不正条件・転送中の条件改変・report改変の拒否を確認した。

別配置 `/home/user/workspace/mcmc4qec/20261020-planned-final-controls-v1` に22 controlを固定した。
元bundleのacceptance manifestに基づく113ソースのbyte照合、75 import先、元native Python、5条件の実監査configのbootstrapを確認した。
worker sourceは既存の共通実装との一致を確認したが、将来5条件のPC parity実行を示すものではない。
本番の最終config、投入、report、回収は未実施であり、完了collector authorityとfull監査、全PC群の回収が前提となる。
最終reader・qsubの実装と受入は [reader接続仕様](planned_final_reader_spec_2026-10-20_ja.md)、実配置のpath/hashは [配置記録](data_tile_validation_2026-10-17/planned_final_controls_native_v1/accepted.json) を参照する。
source・受入ログ・配置・実機観測は [保存manifest](data_tile_validation_2026-10-17/planned_final_collection_progress_20261020_v1/manifest.json) に保存する。
