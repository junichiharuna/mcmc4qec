# 残り5条件のshared入力と最終転送context

## 小仕様

対象は事前固定済みC1T1・C1T2・C3T0・C3T1・C3T2とする。
元C1T0のcollector・保存replay検証・distribution関数を別directoryへ導出し、旧sourceは変更しない。
collectorは明示conditionとhostを受け、固定assignmentに一致するbatch0のstage、recipe、parity検証だけを使う。
既存の7ファイルtransportでparityの5ファイルとpredecessorの2ファイルをread-onlyで回収する。
回収前後のhash、実path、runtime、88保存行のparity受理、stageのexternal evidenceの検査を維持する。
保存replay検証は当該conditionのnative reference・recipe・転送receiptを使い、元の全保存値照合とfinal providerのpredecessor検査を再利用する。
5条件で一致確認済みの元113 source bundleを使い、別の現行libraryを読み込まない。
distributionは新しい保存replay verifierのsource pinを要求し、それ以外の全batch・768群・67,584予定行・全input hashの検査を維持する。
sampling・BAR・bootstrap・decoderの再実行と新しいqsubは行わない。
旧sourceのhash、変更箇所、導出後sourceを保存し、条件間の入力混在を拒否する。

## 受入条件

5条件の明示的な選択と、異なるcase・target・host・recipeの拒否を確認する。
元の7ファイルtransportの改変・欠落・source違い拒否を回帰試験する。
distributionの全件分母・欠落batch・改変replay・書込み前拒否の元fixtureを、新verifier名だけ変更して実行する。
元sourceが変更されていないことと、導出が記録した変更以外を含まないことを検査する。
本番PCの初回stage/parityがまだない条件は、受入fixtureを実行結果の代用にせず未実施と記録する。

## 実施結果

元sourceをhashで固定してcollector・verifier・distributionを別directoryへ導出し、全変更を `derivation.json` に保存した。
7ファイルtransportとtransfer本体は元sourceと同じ内容を使用する。
distributionの元fixtureはverifier名と明示condition fieldだけを変更して使用した。
Windows Python 3.11で契約・元回帰82 passed・32.13秒、厳密な導出照合と実CLI起動5 passed・1.08秒だった。
旧sourceが変わっておらず、記録した変更から導出後sourceを正確に再現できることを確認した。
全5条件の固定metadataと113 sourceの照合も試験に含めた。
新adapterのLinux試験、本番PCからのshared入力回収、実saved replayの再検証、実distribution作成・転送は未実施である。

[source・導出記録・受入ログ](data_tile_validation_2026-10-17/planned_condition_distribution_acceptance_v1/manifest.json)は17ファイルで、manifest SHA-256は `8a4d2f8c4465be8b095ac8bd0bbe56b06450b98a6f46a8610dfd1c37e0874d44` である。
実行入口は `output/planned_condition_distribution_v1/collect.py`、`verify_shared.py`、`distribution.py`、`transfer.py` である。
collectorは `HOST --condition CONDITION`、保存replay検証は `--condition CONDITION` を受ける。
distributionとtransferは元の外部pin付きrecipe/plan引数を維持する。
これらの自動待機・呼出しと、最終qsub configへの接続は引き続き必要である。
