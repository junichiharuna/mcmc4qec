# dev5 最終計測の事前固定

2026-10-01 20:39 JSTに、Q統合後の予備計測の実行時間から以下を固定した。
最終の被覆率や平均偏差を見てseedや長さを選び直さない。
予備計測の出力は動作と時間の検証に使い、最終の20seedの科学表へ混ぜない。

## 共通条件

符号はtoric d=3、固定unweighted MWPM、bit-flip、Z/H=0.7/0.3、cluster_k=2とする。
全群のseedは2026–2045の連続した20個で、欠落・重複を拒否する。
dev4領域のladderは `[0.30,0.26,0.22]`、低p領域は `[0.10,0.07,0.05,0.03]` とする。
dev4領域はMC anchor、低p領域はMCとexact anchorの両方とし、4構成と領域/anchorの3通りを組み合わせた計12 cohortを得る。
MC anchorは独立1500試行で、block bootstrapはblock長8・30反復とする。
全群で異なるfaulty初期状態の補助比較を有効にし、toricの論文式short/longが同じbasisであることによる正式multistart未判定と区別する。
sourceの最終変更とversion更新後のmainで失敗重みcacheを新規に作り、問題・source・countのdigestを記録して検証する。
最終CSVにはsourceを凍結したcommit、実行コマンド、設定、経過時間を添える。

## 被覆の構成

| 構成 | chain | 長さ | burn | lazy | 誤差法 |
| --- | ---: | --- | --- | ---: | --- |
| default_block | 4 | cut後600、全780 | 固定180 | 0.05 | block bootstrap |
| default_cross | 4 | cut後600、全780 | 固定180 | 0.05 | cross-chain |
| paper16 | 16 | cut前全250 | 各chain反復5 IAT、半trace上限 | 0 | cross-chain |
| paper50 | 50 | cut前全250 | 各chain反復5 IAT、半trace上限 | 0 | cross-chain |

defaultの2方式は同じseedと保存軌道に対してpooled点推定を共有する。
低pの2 anchorも同じseedと軌道を使い、anchorの差だけを比較する。
paper16とpaper50は長さを揃え、最も遅い50 chain群でも20seed全体を600秒以内に収めるため全250を採用した。
論文の2,000,000 stepより非常に短く、pilotで半trace上限も生じたため、これは論文精度の再現ではない。
診断合格は収束・エルゴード性・正しさの証明ではない。

## 時間による根拠

以下はQ後のseed2026、checked cache、補助初期状態ありの1seed実測である。
20seedの欄は単純な実行時間見積で、最終計測の実時間ではない。

| 予備構成 | 1seed秒 | 20seed見積秒 |
| --- | ---: | ---: |
| dev4 default_block 保存600 | 5.04 | 100.8 |
| 低p default_block 保存600 | 7.55 | 151.0 |
| 低p paper16 全250 | 7.22 | 144.4 |
| dev4 paper50 全250 | 13.77 | 275.4 |
| 低p paper50 全250 | 24.03 | 480.6 |

MC/exactを同じ軌道から出力する場合もcohortの定義と設定は変えない。
追補の `--anchor both` はBAR比とMCMC log分散も1回だけ評価し、paper50・低p・全250・補助比較ありの1seedは19.84秒だった。
これは20seed約397秒の見積であり、保存250という事前固定は変更しない。
MCと単独MCの全CSV列、exactと単独exactのCSV bytesの一致、およびdefault_blockの両anchorと公開APIの一致を確認した。

## 長さによる偏差の比較

dev4領域について4 chain、固定burn180、block8、bootstrap30反復、MC anchor1500試行を保ち、保存600・2400・9600を同じ20seedで比較する。
各長さの全seedの点推定、区間、被覆数、平均signed偏差、seed間SD、平均偏差のSE、seed2026の推移を残す。
対応seed間の差も確認し、単一seedの推移や1/sqrt(N)に似た変化だけでbiasと分散を一意に区別しない。
有限長biasが残る候補があれば、固定180・反復5 IAT・半trace、および4/16/50 chainの感度を追加仕様として測定前に固定する。
2026-10-01 20:41に、保存9600のseed2026のpilotは46.50秒と確認した。
全20seedの単純見積は930秒になるため、依頼の同じ20seedを保持し、2026–2035と2036–2045の固定2分割を各約465秒のinvocationとして実行する。
この長さ比較は合計600秒以内ではなく、各benchmark invocationを600秒以内に保つ運用である。
§5の4構成の被覆実験は別で、各cohort全20seedを600秒以内へ収める250stepの短縮設定を維持する。
