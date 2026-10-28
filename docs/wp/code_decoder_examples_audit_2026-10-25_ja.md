# tile符号・decoder利用例の提供範囲監査

2026-10-25に追跡対象のsource・tests・利用例・保存済み検証記録を読み取り、[最終報告草稿](final_validation_report_draft_2026-10-24_ja.md)第1・4節の記述と照合した。
今回、新たな符号構築・復号・sampling・テスト・数値再集計は実施していない。
以下の「受入済み」は保存された過去の実行記録を指し、現在の全環境を再検証したという意味ではない。

## 提供済みの利用例

| 利用例 | 実装されている範囲 | 出力と解釈 |
|---|---|---|
| [tile_bposd.py](../../examples/tile_bposd.py) | tile72 bit-flip、prior .03、BP-OSD order2、直接MCと失敗条件付きMCMC | `direct_mc.json`・`conditional.json`・summaryを保存し、条件付き重み平均を絶対論理誤り率と区別する |
| [tile_capacity_fixed_prior.py](../../examples/workflows/tile_capacity_fixed_prior.py) | `--size 6/12`、`--noise bit/depolarizing`、BP-OSD-CS order10、目標prior固定BARと独立MC | anchor・BAR・独立MC・比較CSVを保存し、初期化・ZH/ZHS・誤差法を選べる |
| [decoder_comparison.py](../../examples/decoder_comparison.py) | Steane・toric d=3・tile72のbit-flip、固定prior .08のBP-OSD order0・BP-LSD order0・BeliefFind inversion | 共通seedの直接MCを比較し、Steaneだけ全128状態のexact参照を付ける |
| 同じdecoder比較例のtoric指定 | 単独UF peelingを追加し、`--mwpm`でMWPMも追加可能 | UFの利用例はtile以外で提供済みで、decoder性能順位の測定ではない |
| [日本語利用案内のBAR snippet](basic_decoders_usage_2026-10-18_ja.md) | tile72に固定BP-LSDを接続し、同一Problemでanchorとladderを評価する記述 | 接続方法の例であり、このsnippetのBAR実行受入は未実施と明記されている |

いずれも短い利用例であり、主校正の設定や校正済み精度をそのまま提供するものではない。
特にBP-OSDのorder2・order0の例を、本校正のOSD-CS order10と同じdecoderとして扱わない。
当初の監査時点ではtile workflowはtile72で目標p=.03、tile288でp=.05に固定され、低ノイズの目標pを指定するCLIはなかった。
その後、[明示ladderのCLI追加とPBS受入](tile_example_target_cli_acceptance_2026-10-25_ja.md)で `--ladder P0,P1,...` の末尾を目標pとする接続例を追加し、省略時の従来値を維持した。
これは任意目標への接続を補うもので、正式な低ノイズselectionの読込み・推奨設定・精度校正は未提供のままである。
実行方法・extras・既存のquick実行記録は[利用例一覧](../../examples/README.md)と[基本decoder利用案内](basic_decoders_usage_2026-10-18_ja.md)にある。

## 符号とdecoderの受入範囲

[make_tile_code](../../src/mcmc4qec/codes.py)は開境界weight-6 preset `w6_288_8_12`を実装し、`make_tile_code(6,6)`がn=72・k=8、`make_tile_code(12,12)`がn=288・k=8に対応する。
引数は格子寸法であり距離ではなく、tileの距離を独立に証明していない。
[構造監査](data_tile_validation_2026-10-17/structure_audit/summary.json)にはpaired logical basis、各rank、最大列重み3、距離未証明・全失敗支持の連結性未確立を記録している。
[factory受入テスト](../../tests/test_tile_codes.py)にはCSS可換性・logical pairing・境界supportの独立評価・tile72の単一qubit誤りに対するBP-OSD検査がある。

| decoder | source上の契約・制限 | 保存受入を構成する有限検査の範囲 |
|---|---|---|
| [BP-OSD](../../src/mcmc4qec/decoders.py) | 固定priorで構築し、tileの主校正はOSD-CS order10 | tile72/288のbit-flip・joint depolarizingで主4条件の校正・環境間差・prior感度を記録し、全入力の決定性は未証明 |
| [BP-LSD](../../src/mcmc4qec/bplsd_decoders.py) | order0のみ、zero syndromeはnative呼出し前に恒等補正、不正補正は例外 | [テスト](../../tests/test_bplsd_decoders.py)はSteaneの全syndromeとsector結合、tile72/288を含む6符号の各6固定状態・X/Z・再呼出し・新instanceを対象とする |
| [BeliefFind](../../src/mcmc4qec/belief_find_decoders.py) | BPとUF inversionが既定、peelingは列次数1/2、両方式とも次数0列を拒否 | [テスト](../../tests/test_belief_find_decoders.py)は小符号全syndromeとsector結合、tile72/288等のX/Z各3代表状態を対象とする |
| [単独Union-Find](../../src/mcmc4qec/union_find_decoders.py) | 非重み付き・priorなし、`ldpc==2.4.1`限定、`bits_per_step=1`限定、peelingとinversionを区別 | [テスト](../../tests/test_union_find_decoders.py)は小toric/surfaceの全syndrome、Steane inversion、surfaceの全sector組合せを対象とし、tile専用fixtureはない |

BP-LSD・BeliefFind・UFにはそれぞれdepolarizing sector版factoryも公開されている。
新3系統は補正のbinary形状・syndrome整合性を検査するが、一般BP-OSD factoryへ同じ追加検査が入ったとは記述しない。
decoder比較例ではBP-OSD baselineにも独自に補正検査を加えている。
[統合検証記録](data_basic_decoders_2026-10-18/integration_validation.json)にはWindows source 202件、Linux sourceと利用例210件、optional wheel 202件の成功が保存されている。
同記録のcore wheelは114件成功・88件skipで、native依存を含む全受入成功とは読み替えない。
[2026-10-18のsource対応記録](data_basic_decoders_2026-10-18/current_worktree_binding_2026-10-18_v1.json)と[検証範囲の説明](basic_decoders_validation_2026-10-18_ja.md)を併せて参照し、本監査ではそのhashやnative環境の再検査は行っていない。

## 利用時の境界と不足している例

bit-flipの失敗は残余logicalのいずれかが非zeroとなる事象であり、P_anyをkで割った値を1logicalあたりの誤り率としない。
depolarizingではjoint I/X/Y/Zのnoiseを維持し、BP系sector decoderのpriorには物理確率qに対して`2*q/3`を明示する。
独立sector復号はdecoder側の近似であり、物理Y相関を独立noiseへ変更しない。
BARでは同一のdecoder・prior・設定・native環境をanchorと全rungに固定し、別decoderへ変えた場合はそのfailure定義に対応するreferenceを取り直す。
[BP-OSDの環境間差](tile_decoder_platform_2026-10-17_ja.md)があるため、package版一致だけで同じfailure集合と判断しない。
tileは列重み3を含むため、UF/BeliefFindのpeelingや標準graphlike MWPMへそのまま渡す利用例は提供対象にしない。
UF inversionの一般行列対応から、tileでの性能・再現性を検証済みと推論しない。

現状の不足は次の通りであり、この監査では追加実装しない。

- 追加3decoderのtile288・depolarizingを実行して保存するCLI例はなく、現decoder比較CLIはbit-flipとSteane/toric/tile72に限定される。
- tileに単独UF inversionを適用する専用例・有限fixture受入はなく、必要ならまず対象を限定した受入から追加する。
- BP-LSDのBARは文書snippetまでで、追加decoder別のMCMC混合・BAR bias/RMSE・95%被覆・time-to-accuracyは未校正である。
- 低ノイズの正式な選択設定を読み込み、利用例に接続する完成例は未提供であり、最終比較・独立計時の受理後に、推奨対象なしの場合も含めて設定表と接続する必要がある。

最終報告の「tile/BP-OSDの主校正」と「追加decoderの実装受入・利用例」は分けたまま記載できる。
低ノイズ比較の進行と最終推奨は[状態文書](tile_validation_status_2026-10-17_ja.md)に委ね、本監査を完了宣言や精度保証へ用いない。
