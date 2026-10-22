# C3T2の独立生成を空き枠へ前倒しする小仕様

## 目的と範囲

C3T2の現行generatorはC3T1のfull trace監査とnative referenceの完了を待ってから全生成を開始する。
C3T2の固定partition入力はcase3・target2に閉じており、C3T1の生成結果を科学的な入力として参照しないことを、元payload・元manifest・実装で確認してから順序だけを変更する。
C1T2最終解析の終了等により枠が空いたとき、C3T2のanchorとsampling前半を先行できるようにする。
sampling後半は従来どおりC3T1 full trace監査とnative referenceの受理を待つ。
前条件の完了待ちを廃止する範囲はanchorとsampling前半だけで、全体の短縮を保証するものではない。

## 不変条件

元のcase・target・全task・seed・anchor共有・partition・decoder・noise・trace長・burn-in・chain・ladder・誤差法・要求資源を変更しない。
元の成功preflightと固定payloadを再利用し、各投入前の空き枠確認、共有投入lock内の最大2node検査、qsub、実PBS receiptの検証を維持する。
anchorの正常終端を確認してからsampling前半を投入する。
C3T1監査とnative referenceの正常終端を確認してから後半を投入し、全3receiptが揃って初めて元のregistryを発行する。
未収束・診断未定義・区間未取得を分母から除かず、科学的な受理は後続処理に委ねる。

## 移行

既存のgenerator、C3T2のaudit、native/PC launcher、final preparation・execution・downstreamの実PIDと子process、全記録を確認する。
対象が未投入・未起動の待機状態であることを確認してから、そのlocal waiterだけを停止し、停止前後の記録とsource hashを別のtransition記録に保存する。
稼働中クラスタjob、PC解析、C3T1のcontroller、原sourceと過去の失敗記録は変更しない。
各後続controllerは新しいsource・journalを参照する別版を作り、native/PC実処理、collector、audit、final reader、科学的validatorは元のものを使用する。
待機状態の停止記録は計算失敗や数値結果として扱わない。
曖昧な投入応答・観測timeoutを理由に再投入しない。

## 受入

元payloadの全項目一致、異なるcondition拒否、順序、各qsub前の枠待ち、anchor失敗時の停止、前条件未完了時のsampling後半禁止を確認する。
既に投入・子起動・最終解析準備を試みた記録があれば移行を拒否する。
後続は新しい実intentとsource hashを要求し、未完了の依存関係では待機し、失敗は伝播させる。
移行後に実processとjournalを確認し、最初のqsubが行われた時点でPBSのjob ID・script・資源・同時node数を独立照合する。
