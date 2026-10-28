# 2物理ノードへの12ワーカー投入仕様

上限はジョブ数ではなく2物理ノード、各96コア・所有者の予約メモリ340 GiBとする。
12条件を独立した1コアのワーカーに分け、nodeAとnodeBへ6件ずつ固定する。
各ワーカーのメモリとwalltimeは既存の計測証跡から計算し、実際の他利用者の割当と待機中の予約も容量検査へ含める。
96コアの予約だけで直列処理が速くなるとは扱わない。

実装は `output/low_parallel_dispatch_v2/dispatch.py`、容量検査は検証済みの `output/physical_node_capacity_v1/capacity.py` を再利用する。
v1の8ワーカー案は、旧ワーカーの失敗を受けて採用しない。
旧ジョブや旧出力は変更せず、12ワーカーの新しい準備receipt・manifest・実行環境を用意する。
失敗ジョブを自動的に再投入する機能は設けない。

投入ポリシーには所有者、workspace、共有lock、準備receipt、runtime、capacityのSHA-256 pin、2つのvnode、12件の配置を保存する。
共有lockを取得してから完全な `qstat` と `pbsnodes` のJSONを再取得し、投入直前にも再検査する。
同一物理hostのvnode別名は物理ノード数と容量を水増ししない。
未知の非固定ジョブ、資源値欠落、実割当と要求の不一致を検出した場合は投入しない。
容量不足と他の投入主体によるlock保有は待機として返し、投入intentを作らない。

全入力と完全なPBS scriptを照合し、intentを排他的に保存してから `qsub` を一度だけ呼ぶ。
返答を保存し、確定したjob IDを既存形式のsubmission ledgerへ保存した後でlockを解除する。
timeout、不正な返答、ledger書込み失敗は不確実な投入としてlockと証跡を残し、自動再試行しない。

mergeは全12ワーカーの実ジョブがF・exit 0・run_count 1で、所有者のactive jobがゼロであることを同じlock内で確認する。
この条件で元の単一ノードmerge scriptをそのまま一度投入し、科学的なmerge契約を変更しない。
versioned merge adapter・元control・recovery contractをすべてpinして再構成する。

受入テストはfixtureのみを使い、実ジョブの投入をmockする。
実行場所はPBS割当内とし、このPC上ではテストを実行しない。
テスト実行とproduction投入の成否は別の実行証跡で報告する。
