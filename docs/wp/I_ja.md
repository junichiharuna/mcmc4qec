# WP-I 完了メモ

## 作成物

`notebooks/01_quickstart.ipynb` は toric d=5 の直接 MC による絶対論理誤り率と Z+H の失敗条件付き重みを図で説明する。
`notebooks/02_pl_curve_with_bar.ipynb` は toric d=3,5 の固定 MWPM デコーダー、ladder `[0.30, 0.26, 0.22]`、失敗観測数が正の直接 MC anchor を使った BAR 曲線を描く。
`notebooks/03_conditional_sampling_and_diagnostics.ipynb` は非対称 toric (3,5) の異なる3初期状態、2 chain の重み trace、ESS、split R-hat、独立直接標本の条件付き分散を渡した4条件の収束スクリーンを示す。
`notebooks/04_bring_your_own.ipynb` は3量子ビットの自作 CSS 符号、正規化を全列挙で検査する独自ノイズ、論理予測デコーダーを持ち込み、exact・direct MC・失敗条件付き chain を比較する。
4冊は `examples/` を import せず、先頭パラメータセルで `MCMC4QEC_QUICK` と固定 root seed を扱い、全乱数 seed をそこから派生させる。
英語の説明には条件付き chain と絶対 `P_L` の区別、正の MC anchor、observed overlap、p 依存デコーダーの近似 bias、診断の限界、独立直接分散、論文 in preparation、物理回路カーネル制限のうち該当事項を明記した。
各冊の実行済み出力に低 dpi の PNG 図が1枚含まれ、3 MB の上限を下回る。
`notebooks/regenerate.py` は実行中 Python を指す一時 kernel spec を作り、既定設定で4冊を順番に上書き保存する。
同スクリプトの `--quick --out DIR` は CI 向けにソース notebook を変更せず実行済みの縮小版を別ディレクトリに保存し、`--clear` はコミット対象の実行結果を空にする。
出力先が `C:/dev/RIMC` または `A:/dev/RIMC` の内側になる指定は、ディレクトリ作成前に拒否する。
`tests/test_notebooks.py` は実行中 Python の一時 kernel spec を用い、quick で4冊を実行し、コードセル出力と PNG の存在を調べる。

## 実行した検証

共有 optional venv `C:/dev/mcmc4qec/.venv-dev3-optional/Scripts/python.exe` には最終再生成時点で `mcmc4qec 0.1.0.dev3` wheel が入っていた。
同 venv には nbclient、nbformat、ipykernel、matplotlib、PyMatching、ldpc、bposd が入っていた。
`python notebooks/regenerate.py --clear` で全4冊の出力を消した後、`python notebooks/regenerate.py` で既定設定を全4冊再実行して保存し、全て成功した。
`python notebooks/regenerate.py --quick --out output/notebooks-quick` は全4冊成功し、元の notebook の実行済み出力を保持した。
下表の時間は `regenerate.py` が報告した notebook ごとの実測値で、サイズは実行済み既定 notebook の値である。

| notebook | 既定秒 | quick 秒 | 既定サイズ byte |
| --- | ---: | ---: | ---: |
| `01_quickstart.ipynb` | 2.16 | 1.84 | 25,250 |
| `02_pl_curve_with_bar.ipynb` | 16.33 | 5.10 | 31,241 |
| `03_conditional_sampling_and_diagnostics.ipynb` | 2.56 | 2.11 | 48,749 |
| `04_bring_your_own.ipynb` | 1.69 | 1.50 | 21,789 |

`regenerate.py` のプロセス全体では既定23.22秒、quick 11.05秒だった。

`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_notebooks.py -q` は source mode で4 passed、15.07秒だった。
`C:/dev/mcmc4qec/.venv-dev3-optional/Scripts/python.exe -m pytest --override-ini pythonpath= tests/test_notebooks.py -q` は dev3 installed wheel mode で4 passed、10.64秒だった。
source mode のテストは dev2 wheel 環境の試行と並列に実行したため、その時間には並列負荷が含まれる。
4冊それぞれの実行済み出力に `image/png` が1個あることを確認した。
非対称 toric (3,5) の固定 seed から派生した最小・ランダム論理セクター・最大の初期状態は全て異なり、重みは順に3、8、5だった。

## 未実施

統合後の全 suite、Ubuntu CI での notebook 実行はメイン担当の検証待ちである。
数値が論文の図を再現するという検証は実施していない。

## メインへの依頼

`pyproject.toml` の `notebooks` extra に nbformat、nbclient、ipykernel、matplotlib を含め、前3冊用には `matching` と `codes` を案内してほしい。
toric factory は既存実装では ldpc と bposd を要求するため、前3冊の利用者は `notebooks,matching,codes` をインストールする必要がある。
CI と installed wheel helper は `MCMC4QEC_QUICK=1` と `python notebooks/regenerate.py --quick --out <temporary directory>` を使ってほしい。
4冊のコミット済み出力は dev3 wheel で最終再生成済みである。
