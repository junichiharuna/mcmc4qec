# 重み層別referenceの条件別監査

`audit_condition(plan,index,inputs,summary,chunk_records)`は固定順序のchunk bytesを逐次検査する純粋な監査関数とする。
各入力は`.done.json`・`.json`・`.npz`のbytesを持ち、marker identity・2 payloadのSHA256・spec・chunk summaryを検査する。
既存`aggregate_condition`を再利用して、成功chunkの全物理誤りをseedまたは列挙rankから再生成し、配列・weight・alphabet・記録failure countを照合する。
欠落・重複・並べ替え・marker不備は失敗taskとして補完せずエラーとする。
記録済みfailed chunkは全予定試行数に残し、reference unavailableを保持する。

成功chunkごとに、事前固定した先頭16個以内と末尾1個のindexの和集合を公開Problem.is_faultyで再判定する。
chunk長によるindex重複はuniqueにし、結果を見て検査点数や位置を変更しない。
小chunkで全ラベルが偶然含まれても、監査方式の宣言は`all_labels_redecoded=False`のままとし、実checked数とavailable数を併記する。
同じnative decoderの再判定であり、独立decoder実装の正しさの証明にはしない。

`audit_saved_condition(root,index)`は固定5入力からdriver.make_contextを再構成して保存manifestと完全照合する。
native_preflight_run、submission intentとledgerのmanifest・PBS job ID・script hash、chunks_summaryとsummaryのpreflight hashを結び付ける。
実行時profileと現在のprobe結果を固定profileと照合し、異なるplatform/native環境では監査結果を返さない。
全condition・全chunkのsummary identity集合を照合するが、raw監査する範囲は指定1conditionだけと明記する。
当該conditionの保存summary・global summary・再集計値を一致させる。
入力・source・summary・native証拠のhashと、検査したchunk marker/payload hashを返し、監査中の変更を拒否する。
最後に当該conditionの全marker・JSON・NPZのhashを再照合するため、容量測定ではpayloadを二度読むI/Oも含める。
このAPIは書込み・qsubを行わず、全16条件・約9700万試行の監査runnerは別の容量測定後にクラスタで実行する。

受入は小さな実tile全4case、末尾ラベル改変、payload checksum不一致、raw draw改変、失敗保持、native/PBS/summary結合違反を検査する。
