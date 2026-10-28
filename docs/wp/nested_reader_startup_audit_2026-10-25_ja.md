# isolated reader の起動階層監査

parent runner の起動検証と nested reader の起動検証を分けて扱う。
監査対象は v3 front の全12条件であり、manifest の SHA-256 `e973a1844e870fa38f4eb44f65008aa7cb1f03a0e26ab6b7d2376715638d688d` を prepared receipt の pin と照合した。
9個の nested CLI の実 bytes は、それぞれの環境に記録された source pin と一致した。
この文書の確認はソースと実配置の読み取りであり、科学処理を再実行していない。

| index | 条件 | route | nested CLI の実ディレクトリによる衝突 |
|---|---|---|---|
| 0 | c0t0 | recovered | 旧 recovered module が承認済み修正版を隠す |
| 1 | c0t1 | recovered | 旧 recovered module が承認済み修正版を隠す |
| 2 | c0t2 | portable_mixed | 全 import origin の file/package 候補に衝突なし |
| 3 | c1t0 | portable_condition | 同上 |
| 4 | c1t1 | portable_condition | 同上 |
| 5 | c1t2 | portable_condition | 同上 |
| 6 | c2t0 | staged | nested CLI なし |
| 7 | c2t1 | staged | nested CLI なし |
| 8 | c2t2 | staged | nested CLI なし |
| 9 | c3t0 | portable_condition | 全 import origin の file/package 候補に衝突なし |
| 10 | c3t1 | portable_condition | 同上 |
| 11 | c3t2 | portable_condition | 同上 |

起動経路は parent `run_worker` → selector → `isolated.load_complete` → `process.start_reader` の `Popen` → `tile_low_noise_timing_reader_cli` → `bootstrap` → route の `load_complete` である。
`Popen` は固定された Python・CLI・入力 pin を用い、working directory は新しい reader 出力先である。
Python が CLI のディレクトリを探索順の先頭へ置くため、index 0/1 では `PYTHONPATH` の先頭に修正版を追加するだけでは足りなかった。
この2条件は、承認済み recovered 修正と byte が同一の CLI を新しい同一ディレクトリへ配置し、実 import origin を環境へ記録する対象である。
当該例外の CLI 名は `tile_low_noise_timing_reader_cli.py` と import key `tile_low_noise_timing_reader_cli` であり、短縮名ではない。

reader 内部の経路も確認した。
recovered 0/1 の snapshot・parent・join の読み取り経路には追加の `sys.path` 操作がない。
portable_mixed 2 の snapshot wrapper は明示的な module 読み込みを使い、provider の再配置 runner が追加するディレクトリにも全環境 module と異なる参照先はなかった。
portable_condition 6件では wrapper・audit・collection・bundle の source root の追加を確認した。
index 9 の追加先に旧 `recovery_final_collection.py` があるが、承認済み override は `snapshot_module(entry)` で先に import され、その後の `load_wrapper` と読み取りでも同じ `sys.modules` の module が使われる。
ほかの追加先には異なる参照先を見つけていない。

確認した `load_complete` は snapshot・read・join を使い、内部の外部コマンドは明示された PBS job に対する `qstat` に制限される。
source に存在する collect・compute・ProcessPool の実行 API は、この読み取り経路からは呼ばれない。
staged 6/7/8 は同じ parent process 内で `staging_control.collect` → `read_all`／`read_completion` → `read_staged_audited_collection` を使い、別の Python CLI を起動しない。
今回の読み取り監査では、既知の recovered 2条件以外に修正を要する起動衝突を発見しなかった。
実際の修正後CLIの両ノード検証と canary 成功は、この静的監査とは別の証跡で確認する。

後続の census・独立計時・報告は別途 qsub 265552 で実CLI起動と import binding を確認済みであり、今回の nested reader 修正でそのコードや承認済み環境を変更しない。
front の更新に合わせた現行の tail 設定は `$HOME/workspace/mcmc4qec/20261025-low-parallel-tail-v2/tail-config-v4.json`、SHA-256 は `7ab65ef08f07b965f78cb4a6ac4bbabd3a220e77bf81c5fe254b0218204026cd` である。
設定の更新は入出力先だけであり、以前の設定を保存している。
