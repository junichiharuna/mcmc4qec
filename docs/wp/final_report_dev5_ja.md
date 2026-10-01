# dev5 最終報告

## 1. 到達点

0.1.0.dev5としてWP-Q/Pの実装、独立レビュー、固定seed科学計測、source/wheel/remote CIの検証を完了した。
BARに追加のcross-chain誤差評価を用意し、長さ比較60行と被覆比較240行を保存したが、名目95%被覆・収束・論文精度の保証は主張しない。
Z分布保持とdecoder cacheの高速化後もtoricの研究runner比は2.58–2.72で、2倍以内の速度目標は未達である。
公開既定を維持し、P/Qのworktreeとbranchを統合確認後に削除した。

## 2. WPごとの実装・検証・レビュー

開始時のMIT・研究パス除去等は所有者の承認を受けて前提コミット `22a8e9c` に保存し、dev5の変更とは区別した。

| WP | 実装 | 実行した検証 | 未実施・未達 | レビュー指摘と対応 |
| --- | --- | --- | --- | --- |
| Q | Zの局所確率表と順逆確率を再利用、cache hitの重複decoder検証を削減、適用条件とRNG消費を維持 | 関連pytest 45 passed /5.96秒、独立136近傍のsupport・詳細釣合い、toricの同seed prefix比較、3符号各2回のbench_step | toricの2倍以内は未達、広い符号・ノイズでの性能一般化は未実施 | cache検証境界と正規化回数を補強、型検査の2失敗を修正、最終独立レビューで高・中の未解決指摘なし |
| P | `uncertainty="cross_chain"`、chain別BAR log比の共分散/K、共有rungと独立anchorの分散伝播、個別5 IAT cut、固定cohort/cache検証 | `pytest tests/test_bar_uncertainty.py -q` は独立6 passed /4.87秒、研究照合20 passed /1.97秒、live研究BARとの差2.43e-13、長さ60行・被覆240行と全派生値の独立再計算一致 | 長い研究精度実験・一般符号の校正は未実施、追加burn/chain一要因感度は持続bias未確定のため未発動 | 研究runnerの各chain cutと未burn checkpointへ修正、真値検証を強化、CSV空欄の未判定数を850fa0fで修正し全表再集計 |

Pの合成試験は既知の標準誤差、共有rung共分散、anchor分散、2法の同点推定、1chain/不正値拒否、小問題10seed、JSON往復を含む。
独立レビューは [P_review](P_review_ja.md) と [Q_review](Q_review_ja.md)、実装・コマンドの詳細は [Pメモ](P_ja.md) と [Qメモ](Q_ja.md) に記録した。

## 3. 数値結果

WP-Pの全群は結果を見る前に固定したseed2026–2045であり、seedの選び直しや途中結果による構成の変更を行っていない。
最終sampling sourceは `05c7005`、package SHA-256は `50f47ab86aadb8ddc25142c696ce6cfbce631a8cf8357cbbca8ca33d397f56d5` である。
生CSV・事前計画・環境・全実行ログ・派生量の再計算scriptは [data_dev5](data_dev5/README.md) に保存した。

toric d=3、固定unweighted MWPM、p=0.22のexactは0.602662564702で、長さ比較は4chain・固定burn180・block8・bootstrap30・MC anchor1500試行を保った。
SDはseed間標準偏差、SEは20seed平均の標準誤差で、±SEを95%区間とは扱わない。

| 保存数/chain | 点推定平均 | 平均偏差 | SD | SE | BAR被覆 | 平均区間幅 | seed2026点推定（exactとの差） |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 600 | 0.590749 | -0.011914 | 0.025610 | 0.005727 | 13/20 | 0.062566 | 0.534471（-0.068191） |
| 2400 | 0.601433 | -0.001230 | 0.012282 | 0.002746 | 20/20 | 0.046805 | 0.590558（-0.012105） |
| 9600 | 0.599411 | -0.003251 | 0.006966 | 0.001558 | 20/20 | 0.041138 | 0.593408（-0.009255） |

対応seed差の平均±SEは2400−600で+0.010684±0.004678、9600−600で+0.008663±0.005146、9600−2400で−0.002022±0.002497だった。
同じBAR比をexact anchorへ換算した補助平均偏差は600/2400/9600で−0.010479/+0.000274/−0.001737、9600は約1.09SEで、持続的biasの有無を確定できない。
defaultはこの問題では条件付きtargetから開始するため初期過渡を原因と断定せず、有限相関、非線形BARの有限標本bias、少数chainの散らばりを候補として残す。
MC anchorが残す理論SD目安は約0.010であり、9600の実測SDがこれより小さいのは有限20seedの負の標本共分散を含むためで、独立性を証明・否定する結果とは扱わない。
9600の計測は事前固定した10+10seedの483.39/469.81秒、合計953.19秒であり、全20seedが600秒以内だったとは主張しない。

被覆比較のdefault2法は4chain・cut後600・固定burn180・lazy0.05、paper16/50はraw250・個別反復5 IATと半trace上限・lazy0である。
dev4 ladderは0.30/0.26/0.22、低p ladderは0.10/0.07/0.05/0.03で、MC anchor1500試行とblock8・bootstrap30を固定した。
低pのtarget exactは0.0210747598592で、MC/exact anchorは同じBAR比を使う。
全240行で区間を得ており、次の被覆の角括弧はWilson区間である。

| 領域 | 構成 | anchor | 被覆 [Wilson] | 平均偏差±SE | 平均区間幅 | 正式四条件未判定 | 補助四条件合格 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| dev4 | default_block | mc | 13/20 [0.433, 0.819] | -0.0119139 ± 0.0057265 | 0.0625657 | 4/20 | 4/20 |
| dev4 | default_cross | mc | 18/20 [0.699, 0.972] | -0.0119139 ± 0.0057265 | 0.0969837 | 4/20 | 4/20 |
| dev4 | paper16 | mc | 17/20 [0.640, 0.948] | +0.0096593 ± 0.0070172 | 0.0966360 | 11/20 | 11/20 |
| dev4 | paper50 | mc | 19/20 [0.764, 0.991] | +0.0066602 ± 0.0036033 | 0.0655513 | 18/20 | 18/20 |
| 低p | default_block | mc | 18/20 [0.699, 0.972] | -0.0001626 ± 0.0003025 | 0.0043546 | 3/20 | 3/20 |
| 低p | default_block | exact | 14/20 [0.481, 0.855] | +0.0000179 ± 0.0001766 | 0.0018484 | 3/20 | 3/20 |
| 低p | default_cross | mc | 18/20 [0.699, 0.972] | -0.0001626 ± 0.0003025 | 0.0047140 | 3/20 | 3/20 |
| 低p | default_cross | exact | 15/20 [0.531, 0.888] | +0.0000179 ± 0.0001766 | 0.0024223 | 3/20 | 3/20 |
| 低p | paper16 | mc | 20/20 [0.839, 1.000] | -0.0003000 ± 0.0002915 | 0.0046481 | 12/20 | 12/20 |
| 低p | paper16 | exact | 19/20 [0.764, 0.991] | -0.0001233 ± 0.0001307 | 0.0024926 | 12/20 | 12/20 |
| 低p | paper50 | mc | 19/20 [0.764, 0.991] | -0.0001648 ± 0.0002605 | 0.0041734 | 19/20 | 19/20 |
| 低p | paper50 | exact | 19/20 [0.764, 0.991] | +0.0000177 ± 0.0000971 | 0.0013778 | 19/20 | 19/20 |

同じ4chain軌道でdev4のcrossはblockより幅が平均0.034418増え、5seedが追加で真値を含んだが、低pのexact anchorは14/20から15/20にとどまった。
MC→exact anchorは点推定と区間の双方を変え、この有限cohortではMCの追加分散がBAR側の未校正を覆う可能性がある。
16/50chainは低p exactで各19/20、50chainはdev4でも19/20と名目に近い観測だったが、Wilson幅は広く、これを設定の一般的優劣や95%保証には使わない。
default4対paper16/50では初期化・lazy・burn・長さも同時に変わるため単一原因を分離できず、paper16対paper50だけが同じraw250のchain追加比較である。
16/50は設計上先頭16chainを共有し、全seed/rungのcut列一致を確認したが、CSVから状態列全要素を再照合したものではない。
toricの論文式short/longは同じbasisなので、正式四条件の全合格は全構成0/20であり、表の未判定以外は別条件の不合格である。
補助四条件は異なるfaulty startを追加した別診断であり、診断合格は収束・エルゴード性・正しさの証明ではない。

| 領域 | chain | cut後長の最小/中央値/最大 | 半trace上限のchain数 | 上限のあるseed |
| --- | ---: | --- | ---: | ---: |
| dev4 | 16 | 125/132/230 | 474/960 | 20/20 |
| dev4 | 50 | 125/125/233 | 1503/3000 | 20/20 |
| 低p | 16 | 125/201/235 | 396/1280 | 20/20 |
| 低p | 50 | 125/202/236 | 1217/4000 | 20/20 |

raw250は短く、全16/50構成で半trace上限が頻発し、不等長pooled BARに等重みchain共分散/Kを適用する追加の漸近近似も残る。
被覆の8 sampling invocationは各20seedを600秒以内で終え、最大は低p50chain両anchorの410.15秒（外側計測）だった。

速度はWindows11 Pro、Python3.11.9、AMD Ryzen5 3600で、p=0.01、10000step、Z/H=0.7/0.3、cluster_k=2、lazy0、1chain、seed731を各2回測った。
decoder構築を除きlibraryの結果・診断生成を含む時間で、同seed反復は科学的な独立反復ではなく時間の変動を見るものである。

| 符号 | 回 | library step/s | 研究 step/s | library秒/研究秒 |
| --- | ---: | ---: | ---: | ---: |
| toric d=5 | 1 | 8386.0 | 22824.9 | 2.722 |
| toric d=7 | 1 | 7322.0 | 19148.8 | 2.615 |
| BB72 | 1 | 4825.5 | 7962.4 | 1.650 |
| toric d=5 | 2 | 8553.4 | 23202.2 | 2.713 |
| toric d=7 | 2 | 7604.6 | 19628.9 | 2.581 |
| BB72 | 2 | 4931.7 | 7741.7 | 1.570 |

toricではattempt/proposeとcache/adapter境界のPython処理が残り、BB72はdecoder時間の寄与が大きい。
実行方法・profile・適用条件は [performance](../performance_ja.md) と英日READMEに公開し、環境を越えた性能保証とは扱わない。

## 4. 論文との整合

行番号付きの全対応表は [paper_consistency](../paper_consistency_ja.md) にある。
論文はin preparationであり、図表や研究精度を再現したという主張はしない。

| 項目 | 論文・研究側 | 公開既定と今回の扱い |
| --- | --- | --- |
| chain・長さ | 50chain、各2,000,000step | API既定1chain、例4chain/600、benchmark16/50はraw250へ時間制約で短縮し差を明記 |
| burn・誤差 | 各chain反復5 IAT、非収束時半trace、観測量chain平均のSE | APIは固定burn/既定block、benchmarkで個別cutを扱い、BAR cross-chainへの適用は追加の漸近近似と明記 |
| kernel・lazy | 論文production Z0.7/H0.3/k2、研究runner API既定Z+PT | 公開Z/H/k2は一致、公開lazy0.05とpaper構成lazy0は区別、既定維持 |
| 初期化・収束 | 最小/最大論理basis、四規則 | APIはnoiseからfailure棄却、d3の同一basisでは正式M未検査、補助初期値診断を別に記録 |
| p・ladder | 主にp≤0.1、幾何的ladderの例 | dev4 p=0.22は範囲外とし、低p ladderを別測定、APIの任意ladderを維持 |
| BAR・anchor | Fermi関数とself-consistent BAR、高p direct MC anchor | 式と方向を照合、独立MC/exact anchorを比較、論文の平均重み実験をfull BAR被覆保証としない |

既定変更は行わず、相違・未検証部分をAPI、README、例、notebookへ反映した。

## 5. 統合・wheel・CI・保護条件

下表のpythonは指定Python3.11由来の環境で、sourceでは研究envと `PYTHONDONTWRITEBYTECODE=1` を指定した。
wheelは新規core/optional venvへ `python -m build --wheel` の成果物をinstallし、PYTHONPATHと研究envを外して検証した。

| gate | コマンド・対象 | 結果 |
| --- | --- | --- |
| 開始基準 | `python -m pytest tests -q` | 362 passed、151.22秒 |
| Q merge後 | 同上 | 366 passed、153.24秒 |
| P/版更新後 | 同上 | 372 passed、156.56秒 |
| 最終文書merge後 | 同上、final_merged.xml | 372 passed、148.48秒、skipなし、file最大24.90秒 |
| core wheel | `python -m pytest --override-ini pythonpath= tests -q` | 269 passed /69 skipped、64.00秒 |
| optional wheel | 同上 | 367 passed /5 skipped、155.69秒 |
| core例・文書 | `python -I docs/wp/verify_wheel.py core` | exit0、7.31秒 |
| optional例・文書 | `python -I docs/wp/verify_wheel.py optional` | exit0、42.76秒、全20例・4quick notebookを含む |
| 既定notebook再生成 | `python -I notebooks/regenerate.py` | 全4本成功、各5.19/12.60/4.88/2.50秒、合計25.17秒 |

全suite300秒、追加60秒、各file60秒の制限を満たし、最終sourceの開始基準との差は−2.74秒だった。
時間は負荷で変動するため、先行統合時の156.56秒も記録に残した。
local optionalの5skipは研究checkoutを指定しないlive照合で、sourceでは実行済みである。

検証済みmain `9d25acc9330533582460976714d961c2bb71e61a` をpushし、[CI run36865462463](https://github.com/junichiharuna/mcmc4qec/actions/runs/36865462463)の全5job成功を確認した。

| CI job | pytest | 秒 |
| --- | --- | ---: |
| core Python3.11 | 267 passed /71 skipped | 51.88 |
| core Python3.12 | 267 passed /71 skipped | 49.93 |
| optional Python3.11 | 365 passed /7 skipped | 83.70 |
| optional Python3.12 | 365 passed /7 skipped | 64.49 |
| typing Python3.11 | mypy24files成功、3 passed | 0.78（pytest） |

各CIのwheel/例/文書とoptional notebook検証も成功し、wheel jobでのmypy不在による2skipは専用typing jobで検査した。
上記CIはruntime検証headに対する記録で、最終監査記録の追記でpackage本体と英語READMEは変更していない。
P/Qはgit cherryが空・tracked状態clean、出力P40/Q33ファイルの保存先とのSHA一致と削除対象絶対パスを確認してからworktree/branchを削除した。
研究repoのHEAD69efcfcとclean、handoff既存本文のprefix一致、承認済み前提以後のLICENSE/CITATION/sampling/kernels不変を確認した。
詳細な要件対応は [完了監査](audit_dev5_ja.md)、実行記録は [検証記録](validation_dev5_ja.md) にある。

## 6. 所有者判断と次の依頼候補

- `estimate_logical_error` の既定はblock bootstrap、公開SamplingConfigは1chainのままとし、cross-chainやchain数の既定変更は今回の有限20seed表だけで決めない。
- `pl_curve.py` の4chain/600設定は短い例として維持し、研究用の既定へ引き上げる場合は長さ・chain数・区間法を別々に固定した追加校正と費用評価を依頼候補とする。
- 多数chainの19/20等は観測上名目に近いだけで、より長いtrace、block長、少数chainの正規近似、不等長cutによる誤差伝播、一般符号/ノイズの被覆校正は未実施の研究課題として残す。
- toricの2倍以内へ向けた残存Python処理のprofileと高速化、回路専用の差分更新・H提案、非公開helperを含むstrict型検査は次の実装候補とする。
- MITの前提変更は承認済みであり、PyPI等の公開先、private repoの公開化、著者の所属・DOI・release情報は所有者判断のままで、今回変更・publishしていない。
