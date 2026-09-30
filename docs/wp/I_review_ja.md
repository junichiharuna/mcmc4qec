# WP-I 独立レビュー

## 判定

担当コミット `6f3e8cb` の4冊、再生成器、focused test、完了メモを確認し、後述の数値上の留保を明示した上で受け入れる。
保存済みの4枚の PNG を実際に抽出して目視し、trace、BAR曲線、3種の初期状態、条件付き重みの図と軸が判読できることを確認した。
4冊のサイズは21,789〜49,242 byteで、それぞれ3 MB以下である。

## 指摘と対応

初版の03は最小重みとランダム論理セクターの比較だけを4条件へ渡し、最大重み初期状態は図にだけ使っていた。
担当は最小対ランダムと最小対最大の両方について `evaluate_convergence` の4条件と warnings を表示するよう直した。
初版の02は有限の bit-flip 確率における粗い ladder と `OverlapError` の関係を強く書き過ぎていた。
担当は全状態が正の support を持つ場合の低い観測 overlap と、双方向 support が欠ける場合の `OverlapError` を区別して説明した。
02の独立直接 MC 確認点の追加時には、BAR 区間が `None` の場合の処理と、anchor を独立確認点と呼ばない表示を指摘し、担当は両方を修正した。
01〜03の対応するF/G実行例と異なっていた試行数と bootstrap 回数は、担当が実行例の最終設定に揃えた。
03は乱数 seed を固定 root から派生し、最小・ランダム・最大の初期状態が相異なることを実行時に検査する。

## 検証

初版に対する source mode の `pytest tests/test_notebooks.py -q` は4 passed、14.45秒であった。
初版に対する dev3 installed wheel mode の `pytest --override-ini pythonpath= tests/test_notebooks.py -q` は4 passed、13.70秒であった。
最終版の dev3 installed wheel mode の同 focused test は担当が実行し、4 passed、8.06秒であった。
最終版の source mode focused test は個別には未実施であり、メインの統合 suite に委ねる。
独立に `regenerate.py --quick --out output/review_i_regen` を実行し、使用パッケージが dev3 wheel の site-packages にあることと4冊の成功を確認した。
独立に `C:/dev/RIMC/review_i_must_not_create` を出力先に指定し、終了コード2で拒否され、ディレクトリが作られないことを確認した。
担当は出力消去後の再生成を確認し、最終版の既定4冊と quick 4冊を再生成して保存済み出力をコミットした。
最終版の保存済み出力では全コードセルに実行番号と出力があり、各冊に `image/png` が1枚ある。
`examples/` の import と探索パス書き換えがないこと、先頭パラメータセルで `MCMC4QEC_QUICK` と root seed を設定することを確認した。

## 科学上の留保

絶対 `P_L` は direct MC、exact、anchor付き BAR から示し、条件付き chain の重み統計と区別している。
02のデコーダーは全 rung で固定され、正の失敗観測数を持つ MC anchor と overlap の説明がある。
03は独立直接標本から条件付き分散を計算して4条件に渡し、診断が収束・エルゴード性・正しさの証明でないと明記する。
04は独自ノイズを全列挙で正規化し、物理回路の例ではないことと回路カーネルの制約を説明する。
4冊はいずれも論文図の再現を主張しておらず、論文は `in preparation` と記す。
02の保存済み既定実行では d=3、p=0.22 のBAR区間と独立直接MC区間が交わらず、ノートブックは原因未特定の調査警告を表示する。
この非交差は同設定の推定精度を保証しないため、チュートリアルは研究結果の再現や収束の証拠として扱わない。
Ubuntu CI と統合後の全 suite はこのレビューでは未実施である。
