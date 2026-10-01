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
