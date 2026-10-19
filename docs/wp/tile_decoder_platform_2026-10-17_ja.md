# Tile288 BP-OSDの環境間差

本校正の完了済みtraceをWindowsで再復号したところ、Linuxで保存された失敗判定と一致しないcheckpointが見つかった。
対象はtile288・depolarizing、physical decoder prior=.05、sector prior=2*.05/3、ZH・rejection・replicate 0・chain 0・rung 4の保存index 8000で、physical weightは24である。
固定decoder設定は本校正と同じmax_iter=100、min_sum、scaling=1、parallel、osd_cs、OSD order=10である。

| 環境 | residual logical sector | 論理失敗 | 同一instanceの10反復 | 新規4instance |
|---|---:|---|---|---|
| 生成元と同じ固定Linux venv | 94 | true | すべて一致 | すべて一致 |
| Windows | 0 | false | すべて一致 | すべて一致 |

両者はPython 3.11.9、numpy 2.4.6、ldpc 2.4.1、bposd 2.1、pymatching 2.4.0で、mcmc4qecのsource hashとProblem metadata hashも一致している。
OMP・OPENBLAS・MKL・NUMEXPRのthread数をすべて1にしても差が残った。
同じ状態を4回並べたprobeでは、両環境ともrepeat・reverse・freshの不一致、syndrome制約違反、公開failure定義との不一致は0だった。
これは各環境内の有限な確認であり、BP-OSDの一般的な決定性を証明するものではない。
差の原因がcompiler・native binary・CPU上の数値演算・tie処理のどれかは切り分けていない。
環境名とnative ldpc binaryのSHA-256を実測出力に保存した。

この状態は監査不一致を見てから選んだ反例であり、無作為標本ではない。
この1状態から環境間の論理エラー率差、BAR bias、差の頻度は推定しない。
少なくともライブラリの版番号とsource/Problem hashの一致だけでは、同じfailure集合を保証できない。
BAR ladder内の固定priorに加えて、reference・anchor・sampling・再復号で実行環境とnative decoder binaryを固定する必要がある。

生成元Linux環境では、事前に選んだrung 0と4の2traceについて、各18,000保存値の構造検査と各19checkpoint・初期状態の再復号が通った。
これは38checkpointと2初期状態の確認であり、全cohortや全中間物理状態の監査ではない。
本校正・独立MC reference・anchorはいずれも固定Linux環境で実行しており、このWindowsとの不一致だけを理由に既存ジョブを変更・再投入しない。
独立reference venvのnative ldpc binaryとOS情報を追加取得し、本校正profileとの一致を `reference_native_environment.json` に確認した。
全件監査で生成元環境内の不一致が出た場合は、別途その原因を調べる。
全件数値監査driverは、生成元profileのnative binary hash・環境情報・再現状態の判定との一致を実行前に要求するよう変更した。
この追加guardを含む受入は27 passed・5.38秒で、実行環境が異なる場合に版番号だけで監査を通さない。
guard追加後の全件監査driverを別の `20261017-tile-trace-audit-v1` bundleへ配置し、Linuxで27 passed・1.92秒とnative profile・再現状態の照合成功を確認した。
bundle SHA-256は `730166cfbb1dda4ebcd29de83c9e01f1bdca03300db4a87713e8a1c2397376e0` で、全件監査のqsub実行は未実施である。
ここでの再復号・OS情報の取得・環境preflightはlogin node上で固定production/reference venvを用いたもので、元のcompute node上でOSやCPUを追加採取した結果ではない。
全件監査ジョブはcompute node上でもpreflightを通る必要があり、通らなければ環境差を確認してから進める。
既存の版番号だけのruntime記録を、native環境の完全な同一性証明へ読み替えない。

以前記録したWindows quick例とLinux高予算MC referenceの区間比較は、同じfailure集合を確認できていない環境間の数値比較でもある。
その非交差をMCMCの混合不足やBAR biasの証拠とは扱わず、同一環境の本校正で判断する。

再現状態は `data_tile_validation_2026-10-17/decoder_platform_fixture.json`、出力は `decoder_platform_windows.json` と `decoder_platform_linux.json`、2traceの監査は `production_trace_checkpoint_smoke_linux.json` にある。
`cluster_scripts/probe_tile_decoder_platform.py --fixture FIXTURE.json --output NEW_OUTPUT.json` で同じ状態を再検査できる。
Linux probe配置先は `/home/user/workspace/mcmc4qec/20261017-tile-decoder-platform-v1` で、既存production venvを使用する。
bundle SHA-256は `a1fc7df4e7e297dbf0d1a1f194949533aee60b7a318ae6b9303d3a581e2fe8b2` であり、投入済みproduction sourceを変更していない。

## 段階別観測の小仕様（2026-10-18）

同じ保存済み1状態・同じdecoder設定について、X/Zそれぞれのsyndrome、channel probability、BPのconverge/iterとlog probability ratio、BP hard decision、OSD-0とOSD-W、最終物理correctionを保存する。
ldpc 2.4.1に同梱された `_bposd_decoder.pyx` のdecodeとproperty定義を読み、BP非収束時だけOSDが呼ばれることと、BP収束時のOSD propertyがBP出力を返すことを確認した。
OSDが実行されなかった場合、そのproperty値をOSD段階の結果として報告しない。
syndromeが0ならBP自体も省略されるため、BP途中状態を計算済みとして扱わない。
各propertyは次のdecode呼出し前にcopyし、physical correctionのsyndromeとlogical mapを明示的に検証する。
段階別のlogical residualと公開decoder/failureの結果を比較し、一致しない場合も観測として保存する。
既存のnative profile、fixture hash、Cython source hashと新probe source hashを同時に保存する。
比較では設定・syndrome・channel入力を先に照合し、BP soft値、BP hard decision、OSD-0、OSD-Wと最終出力の差を別々に数える。
これは選択済み1状態の最終反復時点の観測で、最初に差が生じた反復やcompiler/tie処理の原因を特定する実験ではない。
既存ジョブのsource・decoder設定・seedは変更しない。
受入では実fixtureの物理correction検証と公開failureとの一致、BP収束/zero-syndrome時の未実行段階の扱い、段階別比較の入力不一致拒否を確認する。

## 段階別の実測結果（2026-10-18）

同じ保存状態をWindowsと固定Linux環境で観測し、両セクターともBPは100反復で未収束、OSDが実行された。
両環境の設定・syndrome・channel probabilityは一致した。

| 比較量 | X側 | Z側 |
|---|---:|---:|
| BP最終LLRの最大絶対差 | 0 | 0 |
| BP hard decisionのHamming距離 | 0 | 0 |
| OSD-0のHamming距離 | 0 | 0 |
| OSD-Wと最終correctionのHamming距離 | 26 | 0 |
| predicted logicalのHamming距離 | 5 | 0 |

X側のOSD-0は両環境とも重み32、OSD-Wは重み22で、異なる最終correctionはいずれもsyndromeを満たした。
Z側の最終correctionは両環境とも同じ重み20である。
段階別に計算したlogical residualは公開failure判定と一致し、Windowsではsector 0、Linuxでは94だった。
観測した最終BP値とOSD-0が一致することから、今回保存した段階ではX側のOSD-Wで初めて差を確認した。
内部の列順序・候補列挙・比較過程は観測していないため、最初の内部差や根本原因を特定したとは扱わない。

同梱Cython sourceのraw hash差は改行に由来し、CRLFをLFへ正規化すると両ファイルとも環境間で一致した。
そのraw hash差をアルゴリズム変更の証拠とは扱わない。
[PyPIのldpc 2.4.1](https://pypi.org/project/ldpc/2.4.1/)のsource archiveを公表SHA-256と照合して読み、`osd.hpp` の候補更新が厳密な小なり比較であることを確認した。
等コスト候補の探索順は調査候補だが、各native binaryで実行された候補順は未確認であり、今回の差の原因とは断定しない。
このsource archiveには参照先の `sort.hpp` が含まれず、その実装は今回の固定版sourceから確認できなかった。
sourceの閲覧のみを行い、native packageの再ビルド・再インストールは行っていない。

段階別probeの受入3件はWindowsで2.47秒、Linuxで1.72秒で通った。
Linux配置先は `/home/user/workspace/mcmc4qec/20261018-tile-decoder-stages-v1` で、production sourceや投入済みジョブを変更していない。
実測・比較・改行照合・source取得の証跡とhashは `data_tile_validation_2026-10-17/decoder_stages_validation.json` にまとめた。
この1反例から環境間の論理エラー率差やBAR biasを推定せず、校正・reference・再復号は同じ固定Linux環境で続ける。
