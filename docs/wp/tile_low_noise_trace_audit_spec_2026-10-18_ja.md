# 低ノイズtraceの数値監査

## 対象と境界

`audit_tile_low_noise_traces.audit_task(plan, task, arrays, record, code, problem)` は、既存低ノイズdriverの7座標taskを対象とする純粋な数値検査である。
capacityの `chain == replicate` 制約とproductionの全chainを区別し、予定task外・欠落・破損を記録済みsampling failureに変換しない。
この関数への `code` と `problem` はplanの符号・noise・固定target priorで構築したものを渡す契約とする。
単独の純粋検査はnative環境の検証済み結果を名乗らず、`native_platform_verified=False` を返す。
実artifact監査用の `audit_saved_task` はplanのsource/runtime一致、保存済みnative入力のdigest、実行環境で再取得したprofileとの厳密一致、artifact markerとpayload hashを確認してから数値検査を行う。
旧coreで生成した計測と新decoder追加後のpackage hashを暗黙に同一視せず、既存profileを置換しない。
CLI・全数実行runner・qsubはこの変更の対象に含めない。

## 検査する情報

task座標、stage、physical p、固定decoder prior、Problem metadata、初期化・sampling seed、保存長、全SamplingConfig、初期状態の記録、timingを照合する。
Windows等で未取得のRSSはNoneとして保持し、数値がある場合だけ有限・非負を要求する。
成功artifactのpayload集合と全compact traceの長さ・dtype・範囲を検査し、sectorは全保存stepで非零を要求する。
checkpoint indexはplanのstrideと最後のstepから再構築し、initial・checkpoint・finalはnoiseに対応する物理alphabetのuint8配列でなければならない。
finalは最後のcheckpointと一致しなければならないが、initialと最初のcheckpointは同一とは限らない。
bit-flipではX logical basis、depolarizingではX/Z交互のbasisから、記録した係数・seed・replicate/chainに対応するinitialを検査する。
logical combinationは非零係数を一度だけ生成する既存規則と一致を要求し、再抽選を認めない。
initial syndromeとsectorを検査し、initialと各checkpointを同じ固定decoderで再復号して失敗集合内・有限密度を確認する。
checkpointに対応するweight・syndrome weight・logical sectorをcompact traceと照合する。
acceptanceの整数計数と全proposal数を検査し、保存長とともに棄却stepを省略していない記録を確認する。
記録済みfailed taskは例外理由と予定の座標・prior・seed・timingを検査して結果に保持し、部分payloadを成功traceとして扱わない。

## 受入条件

tile72/288のbit-flip/depolarizingの短い実traceを、capacity/productionと両初期化方式を含めて検査する。
座標・prior・seed・metadata・設定・dtype・長さ・範囲・checkpoint・初期化・sector・acceptanceの改変を拒否する。
初期状態生成またはsamplingの失敗を分母から除外せず、native入力/profile不一致とartifact欠落を明示的に拒否する。
各テストファイルは60秒以内の軽量計算とし、長いtrace・全数sweep・クラスタ計算は実施しない。

## 主張しない事項

全保存stepのcompact値を検査することと、全物理状態を再復号することは異なる。
物理状態の再復号は保存されたinitialとcheckpointだけであり、全RNG軌道の再実行ではない。
同じdecoderによる整合性検査はdecoderの独立な正しさ証明ではなく、混合・収束・既約性・精度・95%被覆も保証しない。
