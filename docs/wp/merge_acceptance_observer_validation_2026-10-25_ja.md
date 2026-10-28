# 完了済み merge acceptance の観測復旧受入

元 merge の job 265660 と acceptance の job 265661 は成功済みであり、今回はそれらを再実行せず、完了証拠を controller が観測する経路だけを修正した。
停止原因は、PBS 側と login 側で filesystem の device 番号が異なる一方、4 artifact の inode、size、mtime_ns、ctime_ns、mode は一致していたことである。
元 completion、prepared、script、ledger、元 wrapper、科学結果は変更していない。

新 observer は元 wrapper を実際の原本 path と SHA-256 で読み、`check_artifact_stat` のみを専用 callback に置き換え、終了時に復元する。
元の PBS F0 / run1、script / ledger、別々の merge / acceptance job identity、claim、native preflight、completion、bounded accepted receipt の照合を残した。
固定 completion 内の4 artifact だけを対象とし、canonical path、symlink 禁止、regular file、元 pin、device 以外の全 stat 項目を照合する。
device の差は無条件で無視せず、login の XFS と許可された2計算 node の NFS export が同じ共有 home を指すという明示的な namespace authority に限定した。
authority は実 mount、host、元 source sentinel の hash / stat、各 witness の qsub script と F0 / run1 を固定する。
stat 照合を独立した内容 hash 検査へ格上げせず、巨大 artifact の hash の根拠は元 acceptance が PBS 内で行った検証のままとする。

| 受入 | 結果 | 確認範囲 |
|---|---|---|
| 265665 | F0 / run1、wall 2秒 | 元 wrapper 31件、新 observer 30件、namespace 13件の計74 testsと27 subtestsが0.96秒で成功し、計算 node B の実 namespace witnessを保存 |
| 265666 | F0 / run1 | 計算 node A の実 namespace witnessを保存し、両 node と login を authority で結合 |
| 265667 | F0 / run1、wall 2秒 | 元の実 completion / prepared による bind → inspect → 元 observe が accepted となり、元 accepted payload の一致と4 artifact の照合を確認 |

fixture は device 差だけの元失敗と新成功、非 device 全項目の変化、同じ witness による変更の隠蔽、未知 host、別 device、path / hash / completion の変更、symlink、namespace 不一致を拒否する。
元 claim、native preflight、accepted receipt、PBS 失敗の検査が残ることも確認した。
実 native probe では元 prepare / submit / run / native preflight の再呼出しを禁止し、巨大 result / selection の `Path.open` / `read_bytes` を禁止した状態で観測を完了した。
小 metadata と source の読込には4 MiBの上限を設け、実 entrypoint と request の source pin も照合した。

受入済み observer の SHA-256 は `c9d3f95d6d882185438ac4c5a8cf4bd48fcfed6da2fceb148faa368ea608a381`、namespace helper は `f01c0f3fdb4b58d19564f64bc20c30b5f803a8dcbece174287cd193e0db8bf8b` である。
元 wrapper は `0e3d3a44092d1cab57c200e73e1041a405d8381485b5c232b7cbaff0003c4823` のまま保持した。
小さい受入要約は [receipt.json](data/merge_acceptance_observer_20261025/receipt.json) に保存した。
記載する SHA-256 は、識別子を含む private 原本を指し、本文や公開用要約の置換後 bytes の hash ではない。

この受入は controller の本番起動、後続 timing / report の完了、科学計算の再現を示すものではない。
本番採用は別の flow 移行受入と root の切替記録に従う。
今回の受入から元 worker、merge、acceptance を再投入せず、科学値を再計算していない。
