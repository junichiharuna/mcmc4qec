# 分割workerの結合と計時選択への接続：小仕様

結合は固定された全12条件manifest、資源計画、環境、全workerのprepared pinを独立入力として受け取る。
各workerのterminal descriptorとqsub応答を読み、prepared・script・intent・台帳・実PBS開始時と終了前の状態・F/exit 0・出力hashを既存の証跡検証関数で照合する。
qsub応答はreturncode 0と単一job IDを要求し、台帳と一致させる。
一部workerの失敗、未終了、欠落、重複は結合失敗とし、選択不能の科学的結果へ変換しない。

結合はPBS内で行い、結合job IDとworker job IDを別に保持する。
全workerのraw入力・source・native file・resolved pathを再照合し、終わりにも入力不変性を確認する。
既存の値結合処理で固定順序の24行・12 binding・全352設定・各192 replicateを保持する。
計時planの既存検証関数を使い、reference、設定選択、rank、状態、分母を全行で再構成して照合する。
元の値結合処理は書き換えず、新しい証跡結合層を追加する。

この段階の成果物は `low_noise_partition_verified_merge` とし、既存selector結果への無条件な置換を認めない。
選択候補には元の入力manifestのfile SHA256とworker証跡のprovenanceを保持する。
候補の `production_selection_validated` はfalseとし、計時planへ直接渡した場合は拒否されることを確認する。
結合job自身の実PBS実行・正常終了と全成果物を外側のrunnerで検証してから、後続censusに接続する。
結合jobの資源計画・投入・正常終了の受理は別途実装・検証し、値とworker証跡の結合だけで完了と扱わない。

受入では実choose・値結合・PBS証跡検証・計時plan検証を組み合わせる。
raw reader・source探索・native環境は明示したdoubleを使い、小さな人工入力で欠落・重複・qsub曖昧応答・PBS異常・値とbindingの破損・結合中の入力変更を拒否する。
本番traceでの検証はqsubを使い、未実施の間は科学的受入や精度の保証を主張しない。
