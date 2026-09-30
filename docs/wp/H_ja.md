# WP-H 持ち込み用テンプレート完了メモ

## 作成したもの

`examples/templates/byo_css_bitflip.py` は利用者のCSS行列、論理観測量を返すデコーダー、決定的なfailure predicateを編集箇所に置き、exact、direct MC、条件付きchain、exact anchorのBARを実行する。
12量子ビットを超える場合は正規化を未検査と明示し、BARのanchorを固定試行数のdirect MCへ切り替え、観測失敗が0なら停止する。
`examples/templates/byo_noise.py` は正規化された`log_prob`と同じ分布を引く`sample`を持つノイズの雛形で、全列挙による正規化検査後にexactとdirect MCを実行する。
`examples/templates/byo_decoder.py` は既存の`decode(syndrome)`を`DecoderAdapter`で包み、correction出力の長さ、syndrome整合、`lz`による論理写像、全syndromeの出力を検査する。
`examples/templates/byo_stim_dem.py` は編集した`stim.Circuit`から固定DEMを作り、`from_stim_dem`と`matching_from_dem`を使ってdirect MCと条件付きchainを実行する。
DEMの状態は独立なlatent mechanismのビットであり、物理回路fault配置のsamplingとの等価性やper-round rateは主張しない。
4本とも`# >>> EDIT HERE`と`# <<< END EDIT`で編集箇所を示し、既定は動く小規模設定にした。
検査は各テンプレート内に置き、ライブラリ本体と公開APIは変更していない。
大きい入力のsyndromeと状態の部分検査は`--seed`から派生した乱数を使い、1回のGeneratorから異なる候補を引く。
出力先は既定で一時ディレクトリに置き、解決後の`C:/dev/RIMC`、`A:/dev/RIMC`、`RIMC_RESEARCH_ROOT`、`RESEARCH_ROOT`の配下を拒否する。

## 科学的注意とチュートリアルとの整合

条件付きchainの平均重みは条件付き量として表示し、絶対`P_L`はexact、direct MC、BARだけから表示する。
標準BARではデコーダーとfailure predicateを全rungで固定し、p依存デコーダーを使用しない。
exactを使えない大きい入力のMC anchorでは失敗観測数を出力し、0件なら停止する。
BARで隣接rungのsupport overlapが観測できない場合は`OverlapError`で停止する旨をCSSテンプレート冒頭に記した。
診断が収束、エルゴード性、正しさの証明ではないことと、完全な四条件判定には独立なdirect MCの条件付き分散が必要なことを出力する。
研究論文の図表の再現は主張せず、関連論文はin preparationと記した。
物理回路baselineはこのWPでは扱わず、DEMのlatent state上でのみZ/Hを使う。
独自failure predicateのstabilizer不変性は仮定せず、stabilizer flipを有効にする前に利用者が確認する責任をコメントに記した。
`docs/tutorial_en.md`のCSS、正規化ノイズ、correctionとobservableの区別、DEMの契約との食い違いは確認しなかった。

## 実行した検証

指定の`C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe`を使い、`PYTHONPATH`をこのworktreeの`src`に指定して各ファイルを`--seed 7 --out <一時ディレクトリ>`で実行した。
下表は外部プロセスの壁時計時間で、全実行のexit codeは0だった。

| テンプレート | `--quick`秒 | 既定秒 |
| --- | ---: | ---: |
| `byo_css_bitflip.py` | 0.274 | 0.605 |
| `byo_noise.py` | 0.186 | 0.311 |
| `byo_decoder.py` | 0.187 | 0.318 |
| `byo_stim_dem.py` | 0.577 | 0.779 |

`python -m pytest tests/test_examples_templates.py -q`は12 passedで3.40秒だった。
既定の4実行ではSUMMARYキー集合と`result.json`の存在を検査した。
テスト環境変数で非可換な`hx,hz`、非正規化の`log_prob`、幅の違うdecoder出力を注入し、いずれも出力ディレクトリを作らずに1行の`CHECK FAILED`で止まった。
4本の`C:/dev/RIMC`配下への出力拒否と、環境変数で指定した研究rootへの出力拒否も検査した。
固定seedのMCやBARの数値自体は環境による変動を認め、テストで固定値をassertしていない。

## 未実施とメインへの依頼

全suite、installed wheel、CIでの検証はこのWPでは未実施で、メインの統合検証に委ねる。
利用者が編集した任意の大符号や実際の外部デコーダーとの接続は未実施で、検査の範囲外の意味的正しさまで保証しない。
共有ファイル、extras、CI、`verify_wheel.py`、ライブラリ本体の変更依頼はない。
