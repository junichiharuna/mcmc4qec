# 低ノイズsampling archiveの回収検査

低ノイズの本番manifestから全anchor・sampling taskを列挙し、回収archiveの全payloadを既存のstream検証器で照合する。
本校正のtask座標を流用せず、`(case,target,kernel,initial,replicate,rung,chain)`の7座標を用いる。
anchorは`(case,target,0,0,replicate,0,0)`で、markerはsamplingと同じ`manifest`・`task`形式である。
計算元がstagedかpartitionedかによらず、集約後の同一manifest・全taskを検査する。
capacity manifestは本番archiveの根拠として拒否する。

検査には外部固定のmanifest bytes SHA、archive SHA、全file hash indexとそのSHA、case、target indexを必須とする。
archive内部だけの自己整合性で完了とは扱わない。
manifest自身をarchiveに含め、task markerの欠落・重複・別条件・不正なpayload hash、indexにないfileやindexだけにあるfileを拒否する。
失敗taskのartifactも予定集合に含め、成功分だけのarchiveは拒否する。
streamで読み、archiveをファイルシステムへ展開しない。
入力fileとarchiveは処理前後の同一processでのidentity・サイズ・mtimeを照合し、結果JSONの出力は新規作成のみとする。

受入は小規模な完全archive、失敗taskを含むarchive、欠落、重複、corruption、別case/target、capacity混入、外部hash不一致、未登録file、source変更検出を含む。
実driverのtask生成器とも全集合を照合する。
この処理は転送完全性とtask集合の検査であり、数値traceの再復号、BAR再計算、混合・被覆保証、PBS終了状態の検査を行わない。
exportのPBS終了証拠と固定sourceは投入・回収手順側で結び付ける。
本仕様ではsampling archiveのみを扱い、解析archiveの入力marker連結と全group検査は別途必要である。

export workerはPBS割当内だけで動かし、出力先を新規directoryに限定する。
外部固定manifestに対応する全anchor・traceの3ファイル組とmanifestだけをgzip level1 archiveへ保存する。
sourceのartifact directoryに余分なファイル・欠落・symlinkがある場合、またはmarkerのpayload hashが異なる場合は拒否する。
export intentを先に保存し、元fileのhash・identityを圧縮前後に照合し、archive自体も上記の回収検査器で照合してからexport完了記録を書く。
途中失敗時の出力を消さず、自動再試行・上書きを行わない。
worker自身はqsubやqueue管理を行わず、PBS終了・source binding・最大2ノードは既存の投入・正式受理手順で別途確認する。
