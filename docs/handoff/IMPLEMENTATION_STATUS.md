# RIMC ライブラリ: 引き継ぎ後の進捗

2026-09-30。元の HANDOFF.md は過去時点の記録として保持。
ユーザーの「引き継いで」「初期段階から、段階的にやってって」で再開し、
「サブエージェント使って並列」の追加指示に基づき3エージェントへ分担した。

## 到達点

独立パッケージ rimc-library/ で bit-flip 基盤を検証後、depolarising、phenomenological、
BAR、Stim DEMへ段階的に拡張。現在版は 0.1.0.dev1。全仕様・公開準備の完成宣言ではない。

- CSS/有限カテゴリ状態・正規化ノイズ・decoder・独自failureの共通契約。
- I/X/Y/Zの同時分布、clean開始とperfect/noisy終端を明示する時空間モデル。
- OBF/Z/H/静的stabilizer。MHは全密度と提案比、独自failureを再評価。
- Z .7/H .3/k2/1 replicaを既定化。別のlazy .05と展開後設定も保存。
- exact/directMC/conditional MCMC、seed系列、JSON、行列hash・source hash・診断。
- 極小のexact確率を対数で保持し、underflowを空失敗集合と区別。
- 一般log_probによるBAR、固定failureとp依存decoderの明示近似mode、block bootstrap。
- PyMatching/BP-OSD object wrapper、sector分割、履歴全体の明示変換。
- Stim DEMの各error機構と^相関保持、p族の機構順序・署名・H/L検証。
- 英語README/例、日文設計・制約、wheel型CI定義、暫定引用情報。

設計・制約: rimc-library/docs/initial_library_ja.md。
最新検証: rimc-library/docs/validation_initial_ja.md。
最初のbit-flip版の検証: rimc-library/docs/validation_stage1_ja.md。

## パスと実行

- package: %USERPROFILE%/Documents/Codex/2026-09-30/task/rimc-library
- source: rimc-library/src/rimc/、tests: rimc-library/tests/
- current wheel: rimc-library/dist/rimc-0.1.0.dev1-py3-none-any.whl
- 最初の到達点のwheel: rimc-library/dist/rimc-0.1.0.dev0-py3-none-any.whl
- core-only installed environment: rimc-library/.venv-core/
- optional-decoder installed environment: rimc-library/.venv-decoders/
- spec: 既存 spec/RIMC_ライブラリ仕様書_v0.1.md（本文v0.2）
- Python: %USERPROFILE%/AppData/Local/Programs/Python/Python311/python.exe

source test: python -m pytest tests/ -q
installed-wheel test: .venv-core/Scripts/python.exe -I -m pytest --override-ini pythonpath= tests/ -q
bit-flip / 三種ノイズ / DEM の例は examples/。

新packageはGit初期化していない。研究cloneと A:/dev/RIMC は変更しない。
commit/push/publish、重いMC sweep、clusterジョブ、global依存インストールは行っていない。

## 次段階・残る境界

1. 研究runnerの引数/返値を維持する互換wrapperと既存tests全体の移植は未実施。
   既存研究runnerは変更せず、新APIを独立検証した。旧既定Z+PTはそのまま。
2. 現実的サイズの性能と混合特性、BAR block長/ladder/anchorへの感度は今後の研究課題。
   短いsmoke例の近似区間は厳密値を外れることもあり、有限標本一致を保証と扱わない。
3. 物理回路の排他fault baseline、論文の2d round/前半d補正を合わせた比較、Z/H拡張は未実装。
   DEM接続から論文回路の再現成功とは主張しない。回路stabilizerは対象外。
4. 正式名称、license、公開先、第三者権利、正式著者情報は未決。
   CITATIONはdraft。remote CIは定義のみで未実行。公開承認は受けていない。

## 継続時の注意

Zは一般log densityを全近傍で評価する参照実装で、大規模性能を主張しない。
確率的decoderは対象外。モデルに束縛されたnoiseの取り違えはmetadata比較で拒否する。
任意callableの実装・識別子を利用者が保持する。結果だけからcallableを再構成しない。
新コードのsource_commitは未commitのためnull。package_source_sha256と研究参照commitは別保存。
MCMCは条件付き分布であり、単独で絶対P_Lを求めない。BAR近似modeのbiasは区間に含まれない。

## 2026-09-30 開発依頼書の実行開始後の追記

上記は 2026-09-30 午前時点の引き継ぎ記録として保持する。
現在は `C:/dev/mcmc4qec` の開発依頼書に従い、WP-A〜E を別 worktree で進めている。
開始時の main と origin/main は `93ebb5932db99debe6f77c783510396402c23823` で一致し、既存 142 テストは 54.09 秒で成功した。
Phase 0 の toric / surface ファクトリと受入試験を main に追加した。
研究の非単位な論理交差行列を保つため、従来の paired 既定に加えて明示的な independent 基底指定を実装し、独立レビューの指摘を修正した。
回路サブパッケージを含む再帰的ソース hash と公開契約の docstring を補った。
main `f5323c1` の全 suite は 164 passed、40.40 秒だった。
ユーザーが著者を `junichi haruna` と明示し、WP-D で CFF 検証成功の報告を受けた。
各 WP の実装・独立レビュー・main 統合、dev2 wheel の別環境検証、version 更新、push、remote CI、最終報告は未完了である。
研究リポジトリ `C:/dev/RIMC` は変更せず、直近の git status も clean だった。
今回の検証と判断の詳細は `docs/wp/phase0_ja.md` と `docs/wp/integration_ja.md` に記録した。

## 2026-09-30 12:05 JST ユーザー指定の中断

ユーザーが一旦中断して後日再開できるようにすることを指示したため、実装と並列担当を停止した。
未完了の A/C/E を各 worktree の checkpoint commit に保存し、B/D の既存成果とレビュー記録も保持した。
再開の起点、各 HEAD、未完了レビュー、merge の注意点と残る達成条件は `docs/wp/RESUME_ja.md` に記録した。
ユーザーの再開指示までは作業を再開しない。
main への WP 統合、dev2 最終 wheel 検証、push、remote CI、最終報告は未完了である。

## 2026-09-30 午後・再開後の統合結果

ユーザーの「再開して」で中断指定が解除され、A → B → E → D → C の順に全 WP を main に統合した。
version は `0.1.0.dev2`、公開 API は65名であり、CHANGELOG、README、API/tutorial、CFF、CIを更新した。
著者はユーザー指定の `junichi haruna`、CFF schema検証は成功した。
各統合後の全 suite は成功し、全WPと公開API追加後は 268 passed / 4 skipped、76.01秒だった。
最終wheelを新規のcore/optional別venvへ導入し、installed wheelの試験は core208 passed / 43 skipped（41.23秒）、optional268 passed / 4 skipped（81.52秒）だった。
coreは3実行例と4文書例、optionalは全6実行例と全6文書例が成功し、23 Pythonファイルのsource一致とsite-packagesからのimportを確認した。
初回core検証で発見したMILP試験2件のoptional依存skip漏れは修正した。
詳細なコマンド、wheel SHA、検証範囲と制約は `docs/wp/validation_dev2_ja.md`、最終報告は `docs/wp/final_report_ja.md` に記録した。
研究側との速度差は残り、profileに基づく代替受入条件を満たしたが、性能同等や収束の証明とはしない。
研究リポジトリは読み取り専用で保持し、license追加、publish、public化、既定値の変更は行っていない。
この追記時点ではremote CIの確認だけが残り、push後に結果を追記する。

## 2026-09-30 午後・remote CI確認完了

main `a47a141433fb97ccd9a44e597f8604352999df0a` を origin/mainへpushした。
[Actions run 36675225072](https://github.com/junichiharuna/mcmc4qec/actions/runs/36675225072) は全4job成功で、Python3.11/3.12のcoreは各208 passed / 43 skipped、optionalは各268 passed / 4 skippedだった。
各jobの実行例も成功し、開発依頼のローカル統合・wheel検証・versionと記録更新・pushとCI確認・最終報告の各条件を満たした。
今後の所有者判断と未対応範囲は `docs/wp/final_report_ja.md` 第5・6節に明記した。

## 2026-09-30 夕方・dev3実行例依頼の統合

`docs/dev_request_2026-09-30_examples.md`に従いWP-F〜Jを個別worktreeで実装し、各WPの独立レビュー後にH → F → G → I → Jの順でmainへ統合した。
既存6例のCLIを揃え、実符号・workflow・持ち込みテンプレート12例、実行済み英語notebook4本と再生成スクリプト、英日READMEと実測一覧を追加した。
版番号を`0.1.0.dev3`に揃え、plot/notebooks extras、再帰的wheel検証、notebookを含むCIを整備した。
公開APIは65名のままであり、公開既定のZ 0.7 / H 0.3 / cluster_k=2 / 1 chainは変えていない。
メイン向け最小修正の例外として実行時version定数と回路fault構築の理想区間再利用を変更し、受入テストとsurface d=3のH/L全2588列一致を確認した。
最終sourceは314 passed / 4 skipped（231.28秒）、新規core wheel環境は231 passed / 61 skipped（113.04秒）、optional wheel環境は314 passed / 4 skipped（225.23秒）だった。
sourceの追加5ファイル合計は84.876秒、optional wheelでは83.405秒であり、ファイル別最大も60秒以内だった。
J統合直後は321件成功したが追加テストの時間を超過したため、検証済みの重複seed 7件を整理し、条件付き重み例のquick標本数を縮小した。
Steaneの全rung被覆やBAR曲線の独立MCとの区間一致は保証せず、実測した非交差、未特定の原因、診断の限界を出力と文書に残した。
PyMatchingのmatplotlib依存のため、描画層のImportError時のCSV保持とmatplotlib本体なしでの実行は区別した。
研究リポジトリは読み取り専用を維持し、著者名は指定された`junichi haruna`、所属・DOI・ライセンス・公開・publishは未確定のままとした。
各WPの完了メモとレビュー、`docs/wp/examples_integration_ja.md`、`docs/wp/final_report_examples_ja.md`に根拠と未実施範囲を記録した。
この追記時点ではwheelの実行例・文書の補足検証、push後のremote CI確認、作業worktreeと枝の整理を進めており、完了結果は追記する。

## 2026-09-30 18時台・dev3 wheel補足検証完了

`verify_wheel.py core`は7例・文書4ブロック、optionalは全18例・notebook4本・文書6ブロックが成功した。
各例に10秒のprocess上限を適用し、補足検証全体はcore13.90秒、optional71.02秒だった。
Python 23ファイルのsource一致、site-packagesからのimport、versionとmetadataのREADME一致、coreでのoptional依存不在も確認した。
同じoptional wheel環境の既存テスト比較実行は271 passed / 4 skipped（140.96秒）で、最終全suiteとの差84.27秒も90秒の予算内だった。
ローカル検証を完了し、この後mainのみpushして全4 CI jobを確認する。

## 2026-09-30 18時台・dev3 remote CIと作業枝整理の完了

main `7afd3ac3ef60ca62ec3c174516fe179054901ad7`をorigin/mainにpushし、[Actions run 36694827034](https://github.com/junichiharuna/mcmc4qec/actions/runs/36694827034)の全4 job成功を確認した。
UbuntuのPython 3.11/3.12でcoreは各231 passed / 61 skipped、optionalは各314 passed / 4 skippedで、各jobの実行例・文書とoptionalのnotebook実行も成功した。
各worktreeがcleanで、`git cherry main wp/<x>`が空かつmainに取り込み済みであることを確認し、解決したパスを検査してからf〜jのworktreeと`wp/f`〜`wp/j`を削除した。
最終報告は`docs/wp/final_report_examples_ja.md`であり、実行時間表、ローカルとCIの結果、制約、所有者判断待ち事項を記録した。
研究リポジトリの変更、公開化、LICENSE追加、publishは行わず、依頼された実装・レビュー・統合・検証・push・CI確認・作業枝整理を完了した。

## 2026-10-01 09時台・dev4実装とローカル検証

WP-K/N/L/M/Oの順に独立レビュー済みの実装をmainへ統合し、版を`0.1.0.dev4`とした。
phase flip、物理回路locationのOBF/Z/physical単一提案混合、同seed軌道を維持する専用step、BARのexact被覆・感度評価、公開65名と返り値の公開メソッドの型注釈・`py.typed`を追加した。
LはN統合後、OはK/N/L/M統合後にrebaseし、対応する等価性検査と型検査を再実行した。
各merge後のsource全suiteは順に330/345/354/355/358 passedで、最終は5 skipped、146.28秒だった。
新規core wheel環境は258 passed / 71 skipped、56.23秒、新規optional wheel環境は358 passed / 5 skipped、142.24秒で成功した。
研究checkoutを明示したinstalled wheel照合5件も1.00秒で成功し、読み取り専用を維持した。
通常mypyは24 source filesで成功し、strictの252 errorsは非公開helper等の残件として記録した。
20本の実行例、notebook4本、英語文書コードのwheel実行、24 Python fileと空py.typed・版・READMEのsource一致を確認した。
notebook4本はinstalled optional wheelで既定出力も再生成し、各3.04/12.05/3.53/2.49秒だった。
追加5test fileの合計37.117秒、全fileの最大25.186秒で、各file60秒・増分60秒・全suite300秒の制約を満たした。
KのX/Z等号・不等号には現行decoderで反例があり、事実に反する受入条件を固定せず双対性と実測を記録した。
Lでは集約提案MHだけのテストを実成分別MHと固定乱数samplerへ補強し、Mではsample数と自動block長の交絡をblock8固定で再測定した。
toricの速度比2倍目標、BARの名目95%被覆、回路H・stabilizer対応、非公開helperまでのstrict解消は達成を主張しない。
公開既定、ライセンス、著者の所属・DOI、公開先は変更していない。
この追記時点ではmain push、remote CI、統合済みworktree整理、最終報告の確定が残っており、結果は続けて追記する。

## 2026-10-01 09時台・dev4 remote CIと完了監査

main `c1c6fb919c3bb3cb7a89a2b4e2fae5fb060f80a4`をpushし、[Actions run36798208073](https://github.com/junichiharuna/mcmc4qec/actions/runs/36798208073)の全5jobが成功した。
Python3.11/3.12のcoreは258 passed / 71 skipped、optionalは356 passed / 7 skippedで、型検査jobは通常mypy24filesと型テスト3件が成功した。
remote optionalの2件の追加skipはmypy不在によるもので、型検査専用jobで検査している。
各worktreeのclean状態、git cherryが空、mainへの祖先関係を確認し、解決済み対象パスを検査した上でk〜oのworktreeと枝を削除した。
研究repoは開始時HEADのままcleanであり、既存handoff本文、CITATION、ライセンス・公開状態は変更していない。
最終報告`docs/wp/final_report_dev4_ja.md`と`docs/wp/PROGRESS_dev4_ja.md`に完了根拠、未達の性能目標、未実施の研究精度検証、所有者判断待ち事項を記録した。

## 2026-10-01 21時台・dev5実装と科学計測・ローカル検証

開始時のMIT・研究パス除去等の未コミット変更は、所有者の承認を受けて前提コミット `22a8e9c` に保存した。
Qを `8d00cf8`、Pを `82c003a` の順にmainへ統合し、`05c7005` で版を0.1.0.dev5へ揃えた。
QはZの局所確率表を保持し、decoder cache hitの重複検証を削減し、専用経路の適用条件・軌道・乱数消費・公開既定を維持した。
独立136近傍のsupport/詳細釣合い確認と同seed等価性試験を通したが、研究runnerとの最終時間比はtoric d5で2.71–2.72、d7で2.58–2.62、BB72で1.57–1.65で、toricの2倍以内は未達である。
Pは追加keyword `uncertainty="cross_chain"` を実装し、pooled点推定を維持したままchain別BAR log比の共有rung共分散/Kと独立anchor分散を伝播する。
既定のblock bootstrapと1chainを維持し、cross-chainの2chain下限は精度推奨ではないこと、少数chainの分散推定・log尺度1.96SE近似・有限長biasの限界を記録した。
研究論文のcross-chain SEは観測量平均の実験であり、BAR被覆の保証ではないことを論文行番号付きで区別した。
研究env付きsource全suiteはQ後366 passed /153.24秒、Pと版更新後372 passed /156.56秒で、後者はskipなし、開始時362 passed /151.22秒からの増分5.34秒、file最大26.652秒だった。
新規core wheel環境は269 passed /69 skipped /64.00秒、optional wheel環境は367 passed /5 skipped /155.69秒で、verify_wheelの両構成・全20例・4quick notebook・文書コードも成功した。
installed optional wheelで4notebookの既定出力を再生成し、実行時間合計は25.17秒だった。
sampling sourceを `05c7005`、package SHA-256を `50f47ab86aadb8ddc25142c696ce6cfbce631a8cf8357cbbca8ca33d397f56d5` に固定し、全262144状態のchecked truth cacheを再列挙した。
保存600/2400/9600・同20seedの長さ比較60行と、2領域・4構成・低p両anchorの全12cohort各20seed・240行を測定し、事前計画・生CSV・派生量・環境・実行ログを `docs/wp/data_dev5/` に保存した。
長さ比較の被覆は13/20・20/20・20/20で、9600のexact-anchor換算平均偏差は約1.1SEとなり、持続biasの有無を確定せず追加burn/chain感度は未発動とした。
dev4領域のblock/cross/paper16/paper50の被覆は13/18/17/19（各20seed）、低pのMCは18/18/20/19、exactは14/15/19/19だった。
全250stepのpaper構成は全seedで半trace cut上限が生じ、toric d3の論文式short/long初期化は同一なので正式multistartは実質未検査であり、異なるfaulty startによる補助診断を分けて記録した。
独立レビューでCSV再読込時の正式四条件未判定数の誤集計を検出し、benchmark集計のみを `850fa0f` で修正して全表を再生成した。
独立算術監査は全60行・240行、source/cache、seed、設定、区間式、Wilson、bias/SD/SE、対応差、cut分布と修正後未判定数を再計算し一致を確認した。
科学的な誤差評価の校正や論文2,000,000stepの精度再現は主張せず、公開既定の変更は所有者判断に残す。
この追記時点では最終文書レビューと統合、main push・remote CI、worktree/branch整理、最終報告の確定が残っており、結果を続けて追記する。

## 2026-10-01 22時台・dev5最終統合とremote CI・作業枝整理

P最終文書と独立レビューを `0e4fcab` に統合し、研究env付きsource全suiteを再実行して372 passed /148.48秒、skipなし、file最大24.90秒を確認した。
検証記録を含むmain `9d25acc9330533582460976714d961c2bb71e61a` をpushし、[Actions run36865462463](https://github.com/junichiharuna/mcmc4qec/actions/runs/36865462463)の全5job成功を確認した。
UbuntuのPython3.11/3.12でcoreは各267 passed /71 skipped（51.88/49.93秒）、optionalは各365 passed /7 skipped（83.70/64.49秒）だった。
各wheel jobの例・文書とoptionalの4quick notebookも成功し、型検査jobはmypy24filesと型テスト3件（0.78秒）が成功した。
wheel jobでのmypy不在による2skipは専用typing jobで検査し、研究checkoutを持たないoptionalの5live skipはlocal sourceで実行済みである。
`git cherry main wp/p` と `git cherry main wp/q` が空、両worktreeのtracked状態がclean、全出力P40/Q33ファイルがmain側の保存先とSHA一致であることを確認した。
削除対象の解決済み絶対パスが `A:/dev/mcmc4qec-wt/` 配下であることを検査し、P/Qのworktreeとbranchを削除した。
研究repoは開始時HEAD `69efcfcc86af3bf24ca977a098dab0f348601aff` のままcleanで、handoffの承認済み前提本文はprefix一致、LICENSE・CITATION・公開sampling/kernel既定は `22a8e9c` 以後不変だった。
最終報告は `docs/wp/final_report_dev5_ja.md` とし、名目被覆・収束・論文精度・toric速度2倍以内を達成したという主張と、要求された実装・計測・検証の完了を区別する。


## 2026-10-15 残課題4項目の実装・軽量校正・統合検証

ユーザーの指示でtoric高速化を優先し、Astraの分担3体と独立レビュー2体を用いて残課題へ対応した。
開始HEADは35ed7f3であり、版番号0.1.0.dev5を維持した未コミット差分としてmainに統合した。
混合CDFの事前構築、全密度総和を維持した重複走査削減、二値効果XOR、failure集合外Z候補の逆分布省略により、最終2反復の研究runner時間比はtoric d5で1.873–1.915、d7で1.925–1.941、BB72で1.295–1.330だった。
固定p=0.01・10000step・seed731のtoric条件では2倍以内の目標を達成したが、一般性能・混合精度の保証にはしない。
回路には既存効果tableの差分更新と、同channel・同順序fault alphabetの互いに素なlocation群を明示するHを追加し、非一様率・零support・共有failure・提案対称性・詳細釣合い・同seed/RNG・有限例の連結性とlazyを検証した。
H単独は一般に可約で、回路stabilizerは未対応、実符号でのH混合改善は未検証のままである。
非公開helperを含むmypy strictを有効にし、optional backend例外を限定し、新回路を含む26sourceとconsumer契約の検査を通した。
toric d3・exact anchor・4chain/保存600でblock長8/32/128だけを変えた各20seedは被覆12/20・16/20・16/20で、全60行・事前計画・環境・exact cache・再集計を保存した。
同seedの点推定と記録診断は一致し、block調整は混合を改善せず、名目95%被覆・一般符号・低pの校正は未達として公開既定を維持した。
統合sourceは394 passed・188.05秒・skipなし、core wheelは271 passed/76 skipped・78.84秒、optional wheelは389 passed/5 skipped・206.97秒で、source/optionalのWindows notebookにzmq event-loop warningが各1件あった。
両verify_wheelで26sourceファイルの一致、対応する実行例・文書コード、optionalの4quick notebookを確認した。
研究checkoutのHEADは6c13ba0で、使用したrun_rimc_mixedはdev5参照時点から不変であり、比較前後のrunners.py hashも一致した。
研究側のpaper/main.texとpaper/refereeには並行する別作業の変更があり、本作業は研究checkoutへ書き込んでいない。
分担3worktreeは変更ファイル54個とdiffを退避してSHA確認後に削除し、mainの未コミット差分とoutput/dev6/worktree_snapshotsに成果を残した。
handoff既存本文はbyte prefixを維持し、この節だけを追記した。
LICENSE・CITATION・公開sampling既定は維持し、commit・push・remote CI・publishは実施していない。
最終報告はdocs/wp/final_report_2026-10-15_ja.md、実行ログは同階層data_validation_2026-10-15、性能と校正の生データはdata_speed_2026-10-15とdata_calibration_2026-10-15にある。

## 2026-10-17 Tile factory・クラスタdriverとPBS投入

ユーザーの追加依頼により、開境界weight-6 tileのmake_tile_code、BP-OSD接続例、固定cohortのクラスタ校正driverを実装した。
6×6で72qubits/8logical、12×12で288/8、最小3×3で13/3と距離2を確認し、288qubitsの文献上の距離12は独立証明していない。
RIMCを読み取り専用で参照し、専用venvとbundleをclusterへ配置してqsubでsmoke265188を実行し、終了コード0を確認した。
第1段階の真値・4sampling shard・解析を265189〜265194としてqsub投入し、2本のafterokチェーンにより同時最大2ノード・各96CPUへ制限した。
真値計算265189は完了したが、46,080chain・64,512解析行の校正結果はまだ確定していない。
既定sampling設定・版番号・licenseを維持し、commit・push・remote CIは実施していない。
実装、受入、wheel検証と投入台帳はdocs/wp/tile_cluster_report_2026-10-17_ja.mdおよびdata_calibration_2026-10-17を参照する。

## 2026-10-17 固定cohort校正の完了・全件監査・回収

本番265189〜265194と追加監査265195は全て終了コード0となり、46,080 trace・2,304 group・64,512解析行を回収した。
全投入をqsubで行い、2本の依存列で同時最大2ノードを守り、再投入は不要だった。
全marker・manifest・seed・初期状態・source・compact traceの支持・BAR方程式・区間・集計を検査し、3符号の全270,464状態を公開failure定義で再判定した。
欠落・記録されたsampling失敗・区間未取得は0で、97 archiveの全145,449 payloadをローカルでもSHA-256照合した。
生archiveはoutput/cluster_results/20261017-calibration、全解析行・336条件の被覆・1,776条件の混合診断・816対応比較・図とchecksum台帳はdocs/wp/data_calibration_2026-10-17/resultsに保存した。
保存長60,000・burn-in6,000では、Steane dispersedを除いたblock128被覆は175–186/192、cross-chainは157–168/192で、全条件の名目95%被覆は保証できない。
今回の固定BP-OSDのSteaneでは、既定Z/Hのfailure支持がweight2–4の56状態とweight6–7の8状態に分断され、詳細釣合いが成立しても可約であることを全状態対で確認した。
dispersedは両成分に2chainずつ固定され、長traceでも相対biasはp=0.03で−92.15356%、p=0.0001で−99.998955%となり、block被覆0/192に対してcross-chainは広い区間で192/192を被覆した。
stabilizerを含む候補は有限例で連結になったが、その混合時間と被覆は未校正なので、公開既定を変更せず、反例をAPI文書に追記した。
Steaneの成分を結ぶ提案、16/32chainの誤差校正、tile・大きい符号・別noise・MC anchorは後続計測とする。
最終の文書・監査・回収・有限状態テストは16 passed・13.02秒であり、今回全suiteとremote CIは再実行していない。
RIMCは読み取り専用のままclean、基準HEADは6f7528645ddf988ed8008bad5c81e321aa2aaaf8のまま、commit・pushは実施していない。
完了報告はdocs/wp/calibration_results_2026-10-17_ja.md、検証記録はdata_calibration_2026-10-17/completion_validation.jsonに保存した。

## 2026-10-17 Tile code-capacity検証の開始

d78377eを基準に、tile72-bitからtile288/depolarizingまでの独立検証を開始した。
仕様・受入を先行し、decoder再現性とlogical failure、候補ZHS、直接MC reference、長trace保存とBAR解析のdriverを追加した。
qsub265196の96task pilotは終了コード0で完了し、全artifact archiveを回収した。
tile288低pのrejection初期化上限到達も記録し、失敗seedを置き換えていない。
固定81,788,928試行の独立referenceを265197、384taskの最長trace容量測定を265198としてqsub投入した。
各1ノード96CPU、同時最大2ノードとし、本校正sampling・被覆評価・低noise拡張・最終利用手順は未完了である。
進捗はdocs/wp/tile_validation_status_2026-10-17_ja.md、事前計画と生データは同階層のtile_validation_planおよびdata_tile_validation_2026-10-17に保存する。
新たなcommit・push、公開既定とRIMCの変更は実施していない。

### 2026-10-17 Tile独立reference完了と本校正開始

直接MC referenceのqsub265197は81,788,928試行・1,248chunkを終了コード0で完了し、回収hash、全seed/RNG、target priorを含むProblem metadata、生countからのsummary再現を確認した。
sampling容量測定265198も384task全成功で完了し、回収照合済みである。
人工配列による解析容量測定265199を実行し、本校正case 3を265200としてqsub投入した。
容量実測から本番samplingは合計約25.4ノード時間と予測し、投入順3/0/1/2、各ジョブ1ノード96CPU、同時要求最大2ノードを維持する。
ユーザーの追加指示を受け、weight-stratified referenceの小仕様・有限受入・層別primitive・独立pilot driverを追加した。
層別の最終受入は8 passed・2.08秒で、weight-pilot-v2を準備したが、この記録時点で層別qsubは未投入である。
全体の検証と報告は未完了で、詳細と再開先は `docs/wp/tile_validation_status_2026-10-17_ja.md` とデータ索引にある。

### 2026-10-17 Tile解析資源確定と層別pilot投入

人工配列による解析容量測定265199は96group全成功、終了コード0・walltime20分14秒で完了し、全artifactを回収・hash照合した。
本解析の資源計画を固定し、samplingとanchorの全task記録を確認してから解析をqsubするcontrollerを別bundleへ配置した。
本校正case 3の265200は実行中、層別pilotの265201はqsub投入済み・待機中で、要求は計2ノードである。
層別pilotの全task・raw状態・seed・prior・failure countを照合する監査を仕様・受入・実装の順で追加し、local 11 passed・1.99秒、cluster 11 passed・1.05秒を確認した。
本pilotの回収・監査と層別本計測は未実施で、pilotをP_L referenceとして扱わない。
公開APIのみのtile72/288・bit/depolarizing利用例4本を実行し、ladder全体の固定priorを確認した。
短いtile72-depolarizing例のBAR区間は高予算直接MCの参考区間と非交差であり、利用例の動作確認を精度保証にしない。
各配置先・再現コマンド・実測・hashはdata_tile_validation_2026-10-17の索引に保存した。

### 2026-10-17 Tile固定条件の投入継続controller

本校正の一要因対応比較を追加し、受入10 passed・0.49秒、追加driverの統合71 passed・4.92秒を確認した。
実データの対応比較は解析完了後に行い、欠落推定・未取得区間・未定義診断を除外しない。
固定済みsampling4条件と解析4条件を最大2要求ノード内で順次qsubする軽量controllerを追加し、local/clusterで関連13testを通した。
2026-10-17 11:18 UTC、別bundleのtile-coordinator-v1でPID3756042として起動し、process表から生存確認した。
初回観測は265200 R・265201 Q、要求2ノードで待機だった。
controller稼働中は手動で同じproductionをqsubせず、終了・観測エラー・未受領intentは実processとPBS・投入台帳で確認する。
再現手順・sourceと設定hash・記録先はデータ索引に追記し、既存ジョブのsource・科学manifestは変更していない。

### 2026-10-17 Tile支持の代数的確認と初期化層別の準備

tile72/288のbit/depolarizingについて、同じsyndrome・logicalを保存する差分空間がstabilizerのrow spaceと一致することをrank32/140/64/280で確認し、行列・環境・hashをstructure_auditへ保存した。
このfiber内の連結性を全failure支持の既約性・実測混合・被覆と分けて説明するtile_kernel_support文書を追加した。
depolarizingのlogical初期化は偶数replicateがX basis、奇数replicateがZ basisとなるため、主結果192 replicateを再現したうえで各96 replicateを補助集計する後処理を追加した。
層別の受入は6 passed・1.30秒、追加driver統合は90 passed・6.56秒で、失敗を除外せず原replicate IDを保持する。
実データの層別評価は未実施で、固定ジョブとcontrollerは稼働を継続し、source・manifestは変更していない。

### 2026-10-18 Tile層別referenceのqsub準備

層別referenceの固定manifestと監査済みpilotから資源要求を見積もるsubmitterを仕様・受入・実装の順で追加した。
未測定weightと未実測の合成用予備時間を明示し、24時間・340 GiBを超える計画を拒否する。
coordinator稼働中と最大2要求ノードを超える投入を拒否し、qsub前のintent保存により応答不明時の自動再投入を防ぐ。
関連受入はWindowsで39 passed・10.43秒で、資源・投入の受入は合成pilotと模擬qsubを使った。
実pilotによる予算・資源要求の確定、追加submitterのLinux配置と実投入は未実施で、稼働中のジョブ・既存bundleを変更していない。
同日の追加配置で `20261018-tile-weight-reference-v3` にsubmitterを含む新bundleを置き、Linuxで39 passed・7.24秒とlogin nodeのnative probe一致を確認した。
実pilotからのplanと資源要求・compute node preflight・qsubは未実施で、今後の準備先をv3とする。

### 2026-10-18 Tile本校正case3 samplingと層別pilotの回収

265200は終了コード0・7時間16分10秒でsampling完了し、30,720 trace全て成功記録だった。
192 anchorと合わせた30,912 artifactを回収してidentity・payload hashを照合したが、全件数値trace監査とBAR解析は未実施である。
265201も終了コード0・13秒で完了し、層別pilotの全1,536 task・721,024試行・192層を回収・raw乱数再生成・metadata/count監査した。
失敗taskとlabel矛盾はなくRSS取得も完全で、本番driverが実監査を受理した。
pilotは論理エラー率referenceに使わず、独立本番予算の固定・投入は未実施である。
controllerは後続のtile72-bit 265209とtile288-bit 265210をqsub投入し、最新確認はR/Q・要求計2ノードだった。
証跡と制約は `docs/wp/data_tile_validation_2026-10-17/case3_weight_pilot_completion.json` および索引に保存した。

### 2026-10-18 Tile層別referenceの独立本番予算固定

実pilotだけから配分するplannerを仕様・受入・実装の順で追加し、Windowsで30 passed・2.94秒、Linuxで30 passed・1.11秒を確認した。
全16条件について4,000,000パターン以下を全列挙し、他の層は平滑化pilot分散と計算費用に基づく固定MC予算とした。
最低4,096試行、最大4,194,304試行、尾部上限1e-14を維持し、合計97,857,608試行・23,938 chunkを固定した。
新v4 bundleでbyte一致、実pilotを用いるplanとlogin node native照合、1ノード・96 CPU・32 GiB・4時間30分のdry-runを確認した。
本番qsubとreference取得は未実施で、既存coordinatorに競合する投入は行っていない。
記録は `weight_reference_allocation.json`、`weight_reference_manifest_v4.json`、`weight_reference_deployment_v4.json` などに保存し、今後の層別本番の準備先をv4とした。

### 2026-10-18 Tile全trace監査の計測・投入wrapper

既存の数値監査を維持し、固定96 groupの資源計測と全768 groupの本監査を別rootで行うwrapper・qsub submitterを追加した。
実compute nodeのnative証跡とgroupのwall/CPU/RSSを保存し、監査失敗を除外しない。
関連41件がWindowsで7.36秒、Linuxで2.35秒で通り、新v2 bundle上でcase3のplan・capacity dry-run・login node native照合を確認した。
実資源計測と全件監査は未実施で、既存controller稼働中の追加投入を拒否する。
03:32 JSTに265209のR、265210のQ、coordinator PID3756042の稼働を確認し、要求計2ノードを維持した。
記録は `docs/wp/tile_trace_audit_execution_2026-10-18_ja.md` と `trace_audit_execution_deployment_v2.json` に保存した。

### 2026-10-18 Tile単独BARの計時driver

選択設定を独立seed stage140/141で再実行し、構築・独立anchor・初期化・sampling・compact検証・解析を別計時するdriverを追加した。
選択chain数でも元の校正の最大chain数をlogical初期化strideに使い、X/Zの割当てを維持する。
失敗chainを残し、anchor 0失敗を確率0の結論にせず、cached taskの過去時間を新規phase時間と区別する。
短い実tile traceを含む関連32件がWindowsで9.46秒、Linuxで7.57秒で通り、新v1 bundleとlogin native照合を保存した。
実比較設定の選択・本計測manifest・資源実測・専用submitter・独立精度確認は未完了で、追加qsubは行っていない。
03:39 JSTに265209 R・265210 Q・coordinator PID3756042の稼働を確認した。
記録は `docs/wp/tile_time_to_accuracy_plan_2026-10-17_ja.md` と `bar_timing_deployment_v1.json` に保存した。

### 2026-10-18 Tile全cohortの経験的相対精度評価

reference区間に対して分母も変化する相対RMSEの最小・最大を評価する追加集計を実装した。
全固定replicateと既存summary/raw rowsのhash・数値整合を確認し、未取得や0下端を合格にせず、診断と区間被覆を別に残す。
関連26件がWindowsで0.85秒、Linuxで0.19秒で通り、新v1 bundleを配置した。
実BARデータへの適用・設定選択は未実施で、有限cohortの経験的判定を母RMSEや名目被覆の保証とは扱わない。
03:44 JSTに265209 R・265210 Q・coordinator PID3756042の稼働を確認し、要求2ノードを維持した。
証跡は `precision_assessment_deployment_v1.json`、仕様は `docs/wp/tile_time_to_accuracy_plan_2026-10-17_ja.md` に保存した。

### 2026-10-18 Tile pilotのpaired prior効果

全96taskの元記録とcompact countsをhash・集計値で照合し、全64 prior比較のpaired表と不確実性を派生保存した。
physical p=.1、prior .1→.0001のtile288-bitは成功→失敗16例・失敗→成功7例、depolarizingは7例・8例で、判定境界の変化と失敗率純差を区別した。
全64比較の3周辺確率へBonferroniを適用し、0不一致をfailure集合の同一性と扱わない。
関連18件がWindowsで1.96秒、Linuxで0.98秒で通り、両環境で同じLinux pilotの派生値を再生成した。
これは新しいdecoder実行やBAR bias計測ではなく、判定集合のprior依存性の記録である。
03:51 JSTに265209 R・265210 Q・coordinator PID3756042の稼働を確認した。
記録は `docs/wp/tile_decoder_prior_effect_2026-10-18_ja.md` と `prior_effect_validation.json` に保存した。


## 2026-10-18 Tile decoder段階別観測の追記

固定1状態のWindows/Linux差を追加調査し、最終BP soft値・hard decision・OSD-0は一致、X側のOSD-Wで26ビット・logical predictionで5ビットの差を確認した。
両X correctionは重み22でsyndromeを満たし、Z側の出力は一致した。
各native実装内部の候補順は未観測で、原因・頻度・論理エラー率差は未確定である。
同梱Cython sourceは改行正規化後に一致し、raw hash差をアルゴリズム差と扱わない。
probeの受入3件はWindowsで2.47秒、Linuxで1.72秒で通った。
実測・環境・source hash・新規bundleの記録は docs/wp/data_tile_validation_2026-10-17/decoder_stages_validation.json、説明は docs/wp/tile_decoder_platform_2026-10-17_ja.md にある。
既存production環境とジョブは変更せず、qsubの追加投入・commit・pushは行っていない。


## 2026-10-18 単独BAR計時のcase別投入

単独BAR計時driverにcase別分割と排他的execution intentを追加し、専用qsub submitterで完全なcapacity artifact・native証跡・資源要求・2ノード上限を確認するようにした。
元のcondition indexとseed、全8条件の選択・未達記録、独立96/192 replicateは保持する。
関連42件はWindowsで12.47秒、Linuxで8.49秒で通り、不変bundle 20261018-tile-bar-timing-v2へ配置した。
単一threadのlogin profile照合も通り、指定なし手動probeがguardに拒否された証跡も保存した。
実設定選択・capacity・本計時・同精度の時間比は未実施で、合成資源測定や模擬qsubの受入を実投入と扱わない。
実行手順は docs/wp/tile_time_to_accuracy_plan_2026-10-17_ja.md、hash・検証記録は同階層dataのbar_timing_deployment_v2.jsonにある。
04:15 JSTにcoordinator PID3756042と265209・265210の実稼働を確認し、追加投入・commit・pushは実施していない。


## 2026-10-18 独立計時候補の固定選択規則

全192 replicateから再計算した相対RMSEをreference区間全体で評価し、目標を満たした設定から予定step数と固定tie規則で独立計時候補を選ぶ処理を追加した。
診断未定義・区間未取得・被覆は別指標として保持し、全8条件のselected/unmetと根拠hashを保存する。
これは独立確認用の候補であり、最速・推奨・名目被覆の保証ではない。
関連30件はWindowsで2.14秒、Linuxで0.99秒で通り、不変bundle 20261018-tile-selection-v1へ配置した。
実校正への適用は未実施で、根拠は docs/wp/data_tile_validation_2026-10-17/timing_selection_deployment_v1.json にある。
04:20 JST時点でcoordinatorと265209・265210の稼働を確認し、追加qsub・commit・pushは行っていない。


## 2026-10-18 Tile検証の日本語中間報告

docs/wp/tile_validation_report_2026-10-18_ja.mdへ確認済み結果と適用限界を集約した。
符号構成・failure・BP-OSDの環境間差とprior感度、独立MC reference、kernel議論の範囲、低noise・計時の未実施事項を区別した。
reference表の全count・丸め値・区間、16ローカルリンク、利用例sourceと実行済み記録の一致を確認した。
証跡は同階層dataのinterim_report_validation.jsonにあり、最終校正や推奨設定が完了した報告とは扱わない。


## 2026-10-18 条件付き平均weightのreference比較

target rungのweight診断を独立MC referenceと比較する全cohort集計を追加した。
欠測・診断未定義を除外せず、weight観測量の平均差・RMSE・replicate間SE・reference delta SEをBARの確率誤差と区別する。
短い実tile traceとの平均一致を含む13件がWindowsで2.61秒、Linuxで1.42秒で通った。
不変bundle 20261018-tile-weight-comparison-v1へ配置し、hashと範囲は docs/wp/data_tile_validation_2026-10-17/weight_comparison_deployment_v1.json にある。
本校正への適用は未実施で、JSON metadata照合を元trace・ACF配列の全件監査とは扱わない。
04:49 JSTにcoordinatorと265209・265210の稼働を確認し、追加qsub・commit・pushは行っていない。

## 2026-10-18 MC計時の新規実行と容量artifact照合

MC計時runで既存task・summary・実行intentを拒否し、再利用を新規phase時間に混ぜないようにした。
資源見積もりで全容量taskのidentity・JSON/NPZ hash・summaryとの一致・MC metadataと、native preflightのmanifest・hostname・PBS_JOBID・実行intentへの結合を検査する。
小仕様と受入失敗を先に確認し、関連59件がWindowsで22.99秒、Linuxで9.40秒で通った。
不変bundle 20261018-tile-mc-timing-v3でmanifest、login node上のnative preflight、capacity dry-runを確認し、今後のMC計時先をv3とする。
証跡は docs/wp/data_tile_validation_2026-10-17/mc_timing_deployment_v3.json にあり、capacity・本計測・同精度の実測比較は未実施である。
05:07 JSTの実processとPBSではcoordinatorと265209・265210が稼働し、計2ノードを維持した。
既存bundle・稼働ジョブは変更せず、追加qsub・commit・pushは行っていない。

## 2026-10-18 独立計時cohortの精度・費用集計

全replicateの精度と費用を比較する tile_timing_metrics.py を追加した。
有限reference区間全域でMC・BAR双方が経験的精度を満たす場合だけ、平均task wall・CPU時間の比を出す。
失敗taskの費用・時間欠測・BAR計時で未収集の混合診断を保持し、母精度や名目95%被覆の保証にしない。
小仕様・未実装時の受入失敗・実装の順に進め、関連32件がWindowsで1.73秒、Linuxで0.47秒で通った。
不変bundle 20261018-tile-timing-metrics-v1へ配置し、証跡は docs/wp/data_tile_validation_2026-10-17/timing_metrics_deployment_v1.json にある。
この変更は統計後処理の中核であり、実計時artifactの読込みと監査adapter、実結果への適用は未完了である。
05:16 JSTにcoordinatorと265209・265210の稼働を実確認し、計2ノードを維持、追加qsub・commit・pushは行っていない。

## 2026-10-18 計時artifactと精度・費用集計の接続

計時artifactのmanifest・元budget/settings・native記録と実行intent・全task hash/identity・summary・seed/model metadata・referenceを照合する接続処理を追加した。
全192 replicateの失敗費用や選択未達を保持し、job全体のphase walltimeを条件別に按分しない。
小仕様と未実装時の受入失敗の後、関連36件がWindowsで28.04秒、Linuxで2.74秒で通った。
初期fixtureは80.45秒を要したため、合成modelの結合検査と短い実MC metadataを分離し、最終の同testはWindowsで25.51秒となった。
不変bundle 20261018-tile-timing-comparison-v1へ配置し、既存MC v3の両manifestが再構築と一致することも確認した。
今後のBAR計時は新bundle、MC計時は準備済みv3を使い、旧bundleを変更しない。
実計時への適用・比較ジョブの資源測定とqsub・独立精度と時間比の評価は未実施であり、全物理状態の再復号や選択元の再解析を済ませたとは扱わない。
証跡は docs/wp/data_tile_validation_2026-10-17/timing_comparison_deployment_v1.json にある。
05:28 JSTにcoordinatorと265209・265210の稼働を確認し、計2ノードを維持、追加qsub・commit・pushは行っていない。

## 2026-10-18 bit-flip 2caseの完了anchorを回収・監査

稼働中のsamplingに先行して完了したtile72-bit・tile288-bitの各192 anchorを回収した。
全archive payloadのhash・identity・固定manifestと、記録seed・予算・Problem hash・count/推定値/Wilson区間・phase summaryの一致を確認した。
各3,145,728試行で失敗countは1,838,748 / 2,114,117、task失敗と0失敗countのanchorはいずれもなかった。
物理sampling p=.1、decoder prior .03 / .05のanchorであり、target pのreferenceやBAR被覆の結果とは区別し、各replicateのanchorを合算値で置き換えない。
元の物理誤り列と完全なdirect_mc RNG metadataは未保存のため、独立raw試行再集計・再復号はしていない。
証跡は docs/wp/data_tile_validation_2026-10-17/production_anchor_recovery_01.json とcase別の原summary・転送検証・anchor auditにある。
05:49 JSTにはcoordinatorと265209・265210が計2ノードで稼働し、sampling完了・BAR解析・校正は未完了だった。
既存source/manifest・ジョブを変更せず、追加qsub・commit・pushは行っていない。

## 2026-10-18 固定reference・anchor・MCMCのseed重複検査

固定source/manifestのreference 1,248・anchor 768・初期化190,464・sampling 190,464の計382,944 seedを列挙し、cohort間を含め重複0件を確認した。
回収済みcase 0・1・3の576 anchor記録も予定seedと一致し、referenceについてはarchive/summaryに結び付いた既存の全chunk seed監査を使用した。
未完了samplingの記録seed全件、bootstrap・計時用namespaceは未確認で、乱数列の統計的独立性の証明とは扱わない。
Windowsで10.73秒の照合を実行し、結果・再現script・環境を docs/wp/data_tile_validation_2026-10-17/seed_namespace_audit.json、audit_seed_namespaces.py、seed_namespace_environment.json に保存した。
05:53 JSTにcoordinatorと265209・265210の稼働を確認し、計2ノードを維持、追加qsub・commit・pushは行っていない。

## 2026-10-22 公開前の履歴書き換えと識別子の置換

GitHubでのexperimental版公開に先立ち、全218コミットのauthor・committerメールアドレスを個人アドレスからGitHubのnoreplyアドレス `29061066+junichiharuna@users.noreply.github.com` に書き換えた。
同時に、追跡ファイルと全履歴のblobで、クラスタのユーザー名を `user`、別利用者のホームパスを `/home/other`、Windowsのユーザー名を `user`、クラスタのホスト名接頭辞 `node` を `node` に置換した。
この置換で128ファイル・1,572行が変わり、挿入と削除の行数は一致した。
置換後の追跡ファイルと履歴に、個人メールアドレス・クラスタのユーザー名・ホスト名・Windowsのユーザー名は0件である。
tile検証とcalibrationの証跡はファイル同士をSHA-256で束ねているため、置換したrepo内コピーは記録された指紋と一致しない。
記録された指紋は置換前の原本を指し、原本は書き換え前の履歴 `C:\dev\mcmc4qec-pre-rewrite-2026-10-22.bundle` とクラスタ側の生データに残る。
指紋そのものは書き換えていない。
repo内コピーの指紋を実データで検証する `tests/test_tile_timing_evaluation_report.py` の3件（`test_real_case0_saved_pbs_metadata_only`、`test_real_accepted_inventory_metadata_chain_only[mc]`、同 `[bar]`）は、置換の理由を記したskipにした。
`docs/wp/data_tile_validation_2026-10-17/README.md` と `docs/wp/data_calibration_2026-10-17/README.md` に同じ注記を加えた。
`docs/wp/data_experimental_release_2026-10-19` の公開候補inventoryも書き換え前snapshotの指紋であり、置換後のファイルとは一致しない。
履歴書き換えにより全commit SHAが変わったため、本文書やdocs/wpに記録された旧SHA（例: 886b44b、47ef1b6）は書き換え前の履歴を指す。
GitHub上に残る旧コミットのキャッシュと、他のクローン（自宅PC、クラスタ、Codex worktree）の旧履歴は所有者の判断でそのままとした。
他のクローンを使うときは旧履歴をmergeせず、`git fetch origin` の後に `git reset --hard origin/main` で置き換える。
このリポジトリのローカル `user.email` はnoreplyアドレスに設定した。
置換後の全suiteとremote CIの結果はこの節の末尾に追記する。
置換後の全suiteはWindowsのsource直列実行で2303 passed・10 skipped、1300.21秒で成功し、MkDocsのstrict buildも成功した。
force push後のcommit 6e09463に対するremote CI（run 39734392100）は12 job全て成功した。
リポジトリは所有者の指示でこの時点ではprivateのままとし、tag `v0.1.0.dev5` を付けて公開操作の直前で停止した。

## 2026-10-22 公開直前の状態と所有者側の設定

公開準備の最終commit 18f91bf（手順書 `docs/wp/publication_runbook_2026-10-22_ja.md` の追記まで）に対するremote CI（run 39738324144、tag pushのrun 39738317950）は12 job全て成功した。
`main` とtag `v0.1.0.dev5` はいずれも18f91bfを指す。
所有者は同日、GitHubの Settings → Emails で「Keep my email addresses private」と「Block command line pushes that expose my email」をONにした。
前者はAPIの公開プロフィールで email が null になることで確認した。
後者はAPIから読めないため所有者の申告による。
リポジトリはprivateのままで、public化は所有者の指示待ちである。

## 2026-10-22 Release本文の絶対リンク化とGitHubリポジトリ設定

`docs/experimental_release_notes_en.md` の相対リンク7件はGitHubのReleasesページでは解決されないため、`.github/scripts/release_body.py` でリンクを `blob/<tag>` の絶対URLに変換した本文を `output/release_body.md` に生成し、それを `gh release create --notes-file` に渡す手順に手順書第3節を改めた。
変換の単体テストと、生成した本文に相対リンクが残らず全リンク先がリポジトリ内に存在することの確認を `tests/test_release_body.py` に加えた。
GitHubのリポジトリ設定は、descriptionをREADMEの表現に揃えてexperimental・PyPI未公開を明記し、topicsに quantum-error-correction・quantum-computing・mcmc・rare-event-simulation・monte-carlo・python を設定し、Projectsタブを無効にした。
homepageはMkDocsサイトの公開先が決まるまで空のままとした。
