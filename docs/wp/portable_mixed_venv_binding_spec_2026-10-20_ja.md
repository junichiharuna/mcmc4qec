# 最終readerのvenv起動binding

実クラスタのsampling用Pythonはvenv内のsymlinkであり、実体はcondaのPython 3.11である。
venvはNumPy 2.4.6・SciPy 1.17.1・ldpc 2.4.1、実体を直接起動した環境はNumPy 1.26.4・SciPy 1.16.2・ldpc 2.3.9だった。
元の最終qsub wrapperはPythonのpathにも非aliasを要求するため、元venvの入口をそのまま渡せない。
実体を直接起動して数値環境を変える方法は採用しない。

## 小仕様

元wrapperと科学readerを保持し、Pythonのbindingだけを明示的に拡張する別wrapperを用意する。
configのPythonには、venvの入口path、canonicalな実体pathとhash、venv prefix、pyvenv.cfgのpath/hash、Python version、5依存packageのversionを固定する。
実測ではvenv directory自身も元production環境へのsymlinkだったため、入口側prefixとcanonicalな実prefixを別々に記録する。
入口側prefixの親はcanonical directoryを要求し、固定された `venv` directoryが指定の実prefixへ解決されることを照合する。
aliasを許すのは固定venvの `bin/python` 入口だけとし、その他のinput・source・configの非alias検査は変更しない。
実行時は入口path・実体path・prefix・Python/package versionのすべてを照合する。
sys.prefixは入口側prefixとの文字列path一致と、実prefixへの解決の両方を要求する。
元read_configのPython検査とcomputeの実行Python検査だけを置き換え、qsub・共有lock・最大2ノード・曖昧応答時の停止・終端受理は同じ関数本体を保つ。
Python/package versionの一致だけをdecoderの全入力等価性の証明とは扱わず、元native fixtureと既存のsource・trace・reference検査も維持する。

## 受入

変更範囲をASTで確認し、元moduleを変更しないことを検査する。
同じbinaryへのリンクでもprefixや依存版が異なる場合、リンク先・pyvenv.cfg・binaryが変わった場合を拒否する。
Linuxでは実際のsymlinkを使うfixtureを含め、旧qsub制御の受入も別wrapperに対して実行する。
実入力のprepareとpreflightが通ってから投入候補とし、実qsub・科学report完了とは区別する。

## 実運用への接続

Windowsは10 passed・1 skipped、Linuxは実directory symlinkを含め11 passedとなった。
初回Linux stageはfixture試験の後、venv directory自身もsymlinkであるという実環境の違いを検出して停止した。
失敗stageとsourceを保持し、入口側prefixと実prefixを明示する修正後の別stageで、元venvの実Python・依存版の照合まで成功した。
配置先は `/home/user/workspace/mcmc4qec/20261020-portable-mixed-venv-controls-v2` である。
最終configは156 source・136 metadataを固定してprepareとpreflightを通過し、SHA-256は `4aa2210aafc1d0f25c987da488516f57f110bfe16413a2bf9a980999fbacf8b9` である。
実PBS scriptは `76f04966f311e52fdc4b6403069d63c2dc2bda30a1af00c0334aa250d0bfa81e` に固定した。
実qsubと科学reportの完成は未確認であり、旧collector復旧の投入後に空き枠を待つ一度限りの監視を起動した。

最終reportの回収も、新wrapperの固定path/hashと `backend()` に明示的に接続する別collectorを使用する。
旧collectorのPBS・metadata・report・転送前後hash検査は保ち、旧sourceを変更しない。
そのcollectorのfixture試験と、実reportの回収完了は区別する。
