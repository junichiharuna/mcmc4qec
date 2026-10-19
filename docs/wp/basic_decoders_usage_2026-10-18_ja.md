# 基本decoderの比較例

## 小仕様と受入

`examples/decoder_comparison.py`はSteane、toric d=3、tile72のbit-flipを固定prior 0.08で比較する軽量な利用例とする。
BP-OSD order0、BP-LSD LSD-0、BeliefFind inversionを比較し、toricでは単独UF peelingも加える。
任意の`--mwpm`はtoricだけで受け付ける。
Steaneだけ全128状態を列挙し、他の符号ではexactを実行しない。
direct MCは事前固定した64回（quick）または512回とし、decoder間では同じ乱数seedを使った共通入力による比較であることを明記する。
各decoderの物理補正はHc=sを検査し、不正な補正は成功として数えず例外で停止する。
新factoryの検査に加え、この例では既存BP-OSD baselineにも同じ検査を加える。
保存するJSONはdecoder設定、実行環境、符号とノイズ、seed、予定trial数、観測失敗数、exact参照の有無、各Resultのmetadataを含める。
短い実行例から精度・速度順位・95%被覆や環境間の決定性を主張しない。
受入はSteaneの独立な残差logical列挙との一致、不正補正の拒否、3符号のquick CLIと保存結果、toric限定MWPMオプションの検査である。

## 実行方法

source checkoutのWindows PowerShellでは次のように実行する。
Steaneとtile72は`bposd` extra（ldpc）で動き、toric factoryには追加で`codes` extra（bposd package）が必要である。
単独UFを含むtoric例では現在`ldpc==2.4.1`だけを受け付ける。
インストール済み環境では`PYTHONPATH`の設定を省略できる。

```powershell
$py = "$env:LOCALAPPDATA/Programs/Python/Python311/python.exe"
& $py -m pip install -e '.[bposd,codes]' 'ldpc==2.4.1'
$env:PYTHONPATH = 'src'
& $py examples/decoder_comparison.py --code steane --quick --seed 20261018 --out output/decoder-steane
& $py examples/decoder_comparison.py --code toric --quick --seed 20261018 --out output/decoder-toric
& $py examples/decoder_comparison.py --code tile72 --quick --seed 20261018 --out output/decoder-tile72
```

各出力先の`summary.json`にResultと環境・設定を保存する。
同じ出力先へ再実行するとsummaryを上書きするため、保存したい実験には別の出力先を指定する。
`--quick`を外すと各decoder512 trialとなるが、これも研究精度を校正した設定ではない。
`.[matching]`をインストールした環境では`--code toric --mwpm`で既存MWPM baselineを追加できる。
Steaneのexactはその環境・その固定decoderに対する全128状態の参照であり、最適decoderの論理エラー率を意味しない。
MCの95% Wilson区間は各固定trial実験の区間であり、この1回の包含・非包含から被覆率を評価しない。
decoder間で同じseedを使って物理誤り列を共有しており、表示する個別区間からdecoder差の独立標本検定はできない。
BP-OSD order0は軽量baselineであり、本tile校正のOSD-CS order10とは設定が異なる。

## 符号と失敗条件

bit-flipでは`H=code.hz`、logical mapは`code.lz`である。
物理誤りeからs=Heを作り、補正cがHc=sを満たすことを検査したうえで`code.lz @ (e ^ c) % 2`のいずれかが1なら論理失敗とする。
新しい3factoryは補正のbinary形状・syndrome一致を検査し、この例のBP-OSD baselineにも同じ補正検査を加えた。
不正補正の例外はtrialを論理成功として扱うことなく実行を停止させる。
未完了実験を成功したMC結果と混ぜない。

BeliefFindの既定inversionは列重み3以上を持つ一般CSSにも使えるが、単独UF peelingおよびBeliefFind peelingは各列重み1または2のgraphlike行列だけを対象とする。
tile72をpeelingへそのまま渡してはいけない。
単独UFとBeliefFindはinversionでも列重み0を持つ行列を拒否する。
単独UFは非重み付きであり、BPやchannel priorを用いない。
BP-LSD、BeliefFindのpriorはsamplingのpと独立した固定値である。
同じOS・native build上での有限試験は、全入力や別OSでの決定性の保証にならない。
JSON中のpackage版とsource hashに加え、本計測ではnative binary、実行環境、seed、decoder設定も固定して保存する必要がある。

## BARで同じdecoderを使う

次は接続方法を示す短い例であり、十分な混合や被覆を検証した本計算設定ではない。
`decoder`と`problem`をladderの外で1回だけ構築し、rungごとにpriorを変更しない。
anchorにも同じproblemを使い、固定したfailure集合を保つ。

```python
from mcmc4qec import IndependentBitFlip, Problem, SamplingConfig
from mcmc4qec import direct_mc, estimate_logical_error
from mcmc4qec.codes import make_tile_code
from mcmc4qec.bplsd_decoders import bplsd_decoder

code = make_tile_code(6, 6)
p_star = 0.08
decoder = bplsd_decoder(code, p_star)
problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), decoder)
ladder = [0.15, 0.10, p_star]
anchor = direct_mc(problem, ladder[0], trials=1024, seed=101)
result = estimate_logical_error(
    problem, ladder, anchor=anchor,
    config=SamplingConfig(samples=256, burn_in=64, chains=4),
    seed=102, bootstrap_replicates=100,
)
```

実際の研究利用では長いtrace、独立seed群、初期logical sector、kernel、ladder、誤差法を事前に固定して直接MC等と校正する。
診断未定義・未収束・区間未取得も分母から除かず保存する。
物理depolarizing確率をqとするとBP-LSDまたはBeliefFindのsector版factoryにはpriorとして`2*q/3`を明示し、samplingにはjoint I/X/Y/Zモデルを使う。
独立sectorでの復号はdecoderの近似であり、物理Y相関を独立ノイズへ置き換える操作ではない。
単独UFのsector版にはprior引数がない。

## 検証記録

2026-10-18、Windows Python 3.11.9、ldpc 2.4.1でquick CLIを各1回実行し、プロセス起動込みでSteane 1.511秒、toric 1.449秒、tile72 1.386秒だった。
実行ログと各summaryは`output/decoder-comparison-20261018/`に保存した。
この時間は利用例の軽さの確認であり、decoder同士の速度比較ではない。
SUMMARY行と研究リポジトリ出力拒否を加えた後、既定Steaneのdefault/quickを再実行し、プロセス起動込みで2.145秒/1.617秒だった。
追加の実行ログは`output/decoder-comparison-20261018/default_quick_runtime.json`に保存した。
`python -m pytest tests/test_decoder_comparison_example.py -q`は8 passed、6.17秒だった。
BAR snippetは利用方法の記述であり、この例の受入ではBAR計算を実施していない。
