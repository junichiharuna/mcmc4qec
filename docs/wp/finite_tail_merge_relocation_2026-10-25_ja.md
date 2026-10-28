# 失敗した merge の保存と後処理設定の移設

2026-10-25 の merge ジョブ 265651 は、worker の値を読み込む前の `selector closure differs from environment` で終了コード 1 となった。
成功した 12 worker と失敗した merge の原本は保持し、新しい `merge-parallel-v2` を後処理の入力先として明示した。
この記録は後処理の設定構築と constructor の受入であり、新 merge や科学的な集計結果の受理ではない。

旧 effective loader で旧設定を検証した後、別版 loader が `merge_root` と移設根拠の pin だけを追加変更する。
外側設定の変更は `effective_config`、`effective_loader`、`merge_root`、`source_pins` の 4 項目で、元 source map は全件保持する。
元 runner、科学的な条件、親環境、報告環境、資源予算は変更しない。
未使用だった後処理の出力先は、構築時と native 検査時に不存在を確認して継承する。
運転開始後に出力先が存在することを理由に設定検証を拒否する設計にはしていない。

移設根拠は旧 prepared・request・recovery policy・submission・script・実 PBS 終端・実行エラーの pin を固定する。
旧ジョブの番号、F/終了コード 1、run count 1、所有者、投入引数、prepared の digest、要求資源と script の一致を検証する。
旧 merge の accepted・selection・merge-result が存在する場合は、今回の未受理状態からの移設として扱わない。
部分構築後の失敗は残し、自動再試行しない。

| PBS ジョブ | 実施内容 | 結果 |
|---|---|---|
| 265655 | 移設契約の synthetic fixture 18 件 | F/0、18 passed、0.100 秒、wall 1 秒 |
| 265656 | 元 validator を使った実設定の構築 | F/0、wall 1 秒 |
| 265659 | 新 probe の fixture 12 件と実 13 constructor | F/0、12 passed、0.003 秒、wall 6 秒 |

実 constructor は全 6 role を collection 変換の有無で確認した 12 ケースと、final-report の constructor 1 ケースである。
各ケースで、新しい merge の伝搬、旧 merge を戻した設定と旧 effective 設定の拒否、継承する出力先の不変性と未使用状態を確認した。
旧 merge 配下への読取例外は、外部 pin で固定した `prepared.json`、`submission.json`、`merge.sh`、`execution-error.json` の 4 ファイルだけである。
各例外に 4 MiB 上限、読み取り専用、canonical path、hash と前後の stat 同一性を課し、その他の operational payload と科学データへのアクセスは禁止した。
科学処理の main、巨大な値や selection の読取、科学環境の native bootstrap、最終報告の生成は、この受入では実施していない。

公開用の小証跡は [receipt.json](data/finite_tail_merge_relocation_20261025/receipt.json) に保存した。
記載 SHA-256 は識別子を除去する前の非公開原本を指す。
非公開の小原本 117 ファイルをローカルの ignored output に保存し、4 MiB を超える synthetic fixture 26 ファイルは転送していない。
本番の切替と新 merge の完了判定は、この設定・constructor 受入とは別に行う。
