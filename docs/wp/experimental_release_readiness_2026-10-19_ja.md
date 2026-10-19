# Experimental版の公開準備

10月20〜21日のGitHubでのexperimental版公開を優先する。
ユーザーは最初の公開先をGitHubとし、PyPIは後にする方針を指定した。
長い数値検証は公開準備と並行して継続し、公開時点で未完了の検証を完了済みと扱わない。
現時点でリポジトリはprivateで、release・tagの作成、公開操作、commit・pushは行っていない。
版番号は現在の0.1.0.dev5を維持し、CITATION.cffの旧dev4表記を合わせた。
著者名・MITライセンスを維持し、所属・DOI・公開日は新たに確定していない。

## 現時点の変更と確認

英日READMEにBP-LSD（order 0）・BeliefFind・Union-Findを追記し、追加依存と制約への案内を加えた。
英日READMEと文書indexから、tile検証報告と継続中の検証状況を参照できるようにした。
主4条件の完了、低ノイズ校正の継続、被覆不足・混合診断の問題、BP-OSDの環境間差、追加decoderの科学的校正が未実施であることを明記した。
CHANGELOGに追加decoderと文書更新を記載した。

文書サイトはstrict buildが成功し、生成した13content pageと1,441local link/assetの検査も成功した。
実行ログと記録は[data_experimental_release_2026-10-19/documentation_v1.json](data_experimental_release_2026-10-19/documentation_v1.json)にある。
全sourceテストの直列実行は300秒上限で停止し、成功とは扱わない。
同じsource・test入力の4worker・6worker実行も300秒上限で停止したため、全suite成功とは扱わない。
停止後にpytest workerの終了を確認し、最後に残るテストを特定するためverboseログ付きの6worker実行を開始した。
このverbose実行も300秒上限に達し、2,313 collectedのうち2,309件の終了をログで確認したが、全体成功とは扱わない。
停止時は`test_complete_artifacts_comparison_and_corruption_rejection`が実行中で、同じファイルの後続3件が未開始だった。
このファイルが97%付近で開始されていたことを確認したため、installed optional wheelでは8workerのworksteal方式へ変更し、全2,313件と個別時間・参照data記録の取得を開始した。
installed optionalの全suiteは2,306 passed・7 skipped、282.73秒で完走した。
記録は[data_experimental_release_2026-10-19/optional_installed_suite_v1_analysis.json](data_experimental_release_2026-10-19/optional_installed_suite_v1_analysis.json)にある。
新core環境の初回全suiteではSciPyが必要な研究用の1テストにoptional依存の確認がなく、1 failed・696 passed・251 skippedだった。
このテストだけにSciPyのimportorskipを追加し、core全suiteは696 passed・252 skipped、28.32秒で成功した。
記録は[data_experimental_release_2026-10-19/core_installed_suite_v2_analysis.json](data_experimental_release_2026-10-19/core_installed_suite_v2_analysis.json)にある。
修正したファイルはoptional環境でも21 passed・1.70秒で再確認した。
全optional suiteの成功は修正前、core全suiteと該当optionalファイルの成功は修正後の証拠であり、package sourceとwheelは変更していない。
CIのinstalled wheelテストにもpytest-xdistとworkstealを設定したが、remote CIは未実行である。
並列時の累積時間が60秒を超えた4ファイルは個別に再実行し、37.54秒・31.70秒・36.55秒・27.50秒でいずれも成功した。
個別記録は`data_experimental_release_2026-10-19/file_time_v1_0.json`から`file_time_v1_3.json`にある。
並列実行の累積時間と単独ファイルの経過時間を区別し、今回の単独確認は全て60秒以内だった。
直列実行の入力hashと途中ログは[data_experimental_release_2026-10-19/source_suite_v1.json](data_experimental_release_2026-10-19/source_suite_v1.json)に保存した。

32sourceのmypy strictは成功した。
記録は[data_experimental_release_2026-10-19/strict_typing_v1.json](data_experimental_release_2026-10-19/strict_typing_v1.json)にある。
宣言されたbuild依存を使用するisolated buildでwheelの生成に成功し、32Python sourceの一致を確認した。
wheelのSHA256は`707868b21308028f5a76033f763663b449531b003e9c338c6ee90931c8fb7a2e`である。
記録は[data_experimental_release_2026-10-19/wheel_build_v2.json](data_experimental_release_2026-10-19/wheel_build_v2.json)にある。
古いsetuptoolsを使ったno-isolation buildの失敗記録も保存し、成功記録と区別した。
新しいcore・optional環境を用意し、installed wheelの全テストと例を確認した。
両環境で当該wheelのインストールに成功し、依存package一覧を保存した。
新core環境の`verify_wheel.py core`は15.25秒で成功し、wheel/source一致、optional依存の不在、core向けquick例と文書中コードを確認した。
記録は[data_experimental_release_2026-10-19/core_examples_v1.json](data_experimental_release_2026-10-19/core_examples_v1.json)にある。
これはinstalled wheelの全pytest suite成功を意味しない。
新optional環境の`verify_wheel.py optional`も127.04秒で成功し、全23quick例・4quick notebook・文書中コードとwheel/source一致を確認した。
記録は[data_experimental_release_2026-10-19/optional_examples_v1.json](data_experimental_release_2026-10-19/optional_examples_v1.json)にある。

[英語リリースノート案](../experimental_release_notes_en.md)と[日本語リリースノート案](../experimental_release_notes_ja.md)を作成した。
公開未実施と科学的検証の適用限界を明示し、GitHubから利用するcheckout手順を記載した。
両ノートを文書サイトのnavigationへ追加し、strict buildと15content page・1,562local link/assetの確認が成功した。
ログは[data_experimental_release_2026-10-19/documentation_v2.log](data_experimental_release_2026-10-19/documentation_v2.log)に保存した。

## 公開候補に残る作業

1. 最終候補の差分と配布物を提示し、commit・pushの依頼を受けてremote CIを確認する。
2. GitHub公開時のtag・release note・公開操作を確定し、公開済みと書き換える時点を実際の公開操作に合わせる。
3. 全生データの公開先は未確定のため、別途配布方法を整備する。

全生データを含まないことと、完全な独立再解析に必要なデータがあることは日英リリースノートに明記した。

現時点のtracked fileは358件である。
新しいtile検証データの未追跡部分だけで19,831file・約13.48GBあるため、未追跡ファイルを一括でcommitする方法は使わない。
公開するソースと小さい検証記録、別途配布する計測データを区別し、欠けたデータへのリンクを公開済みとして案内しない。
現状のinventoryは[data_experimental_release_2026-10-19/publication_inventory_v1.json](data_experimental_release_2026-10-19/publication_inventory_v1.json)に保存した。
Markdownリンクとoptional全テストで実際に開いたdataを含む候補を`output/experimental_release_20261019/candidate_v1/`へ取り出した。
このローカル候補は125,719,140byteで、内容のSHA256・元テスト記録との対応・SciPy guard修正後の照合を[data_experimental_release_2026-10-19/candidate_export_v1.json](data_experimental_release_2026-10-19/candidate_export_v1.json)に保存した。
全科学計測のraw dataを含む配布物ではなく、staging・commit・公開も行っていない。
候補ディレクトリからのstrict buildと15content page・1,562local link/asset確認は成功した。
候補ディレクトリの全optionalテストは2,306 passed・7 skipped、251.45秒で成功した。
候補の全809ファイルのSHA256は実行前後で一致し、probeで元worktreeの計測dataへのアクセスは検出されなかった。
記録は[data_experimental_release_2026-10-19/candidate_optional_suite_v1.json](data_experimental_release_2026-10-19/candidate_optional_suite_v1.json)にある。
この確認はテスト実行時に観測した依存の範囲であり、全研究データの収録を意味しない。
公開候補809ファイルとlocal Git refsから到達できる977 blobを、秘密鍵・代表的なaccess token等の6patternで読み取り専用検査し、該当は0件だった。
binary 18件とencoded secret等はこのpattern検査の対象外であり、包括的な機密性保証とは扱わない。
検査の範囲・結果・サイズは[data_experimental_release_2026-10-19/publication_review_v1.json](data_experimental_release_2026-10-19/publication_review_v1.json)に保存した。
最大候補ファイルはmixing比較の`cohorts.json`、74,208,154byteで、100MiBを超えるファイルはない。
GitHubの[通常Gitの上限](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)と[release assetの説明](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)を2026-10-19に確認した。

## Gitに保存するbyte列の確認

このWindows環境はcore.autocrlf=trueであり、通常のGit追加では一部のpackage source・凍結driver・保存JSONがCRLFからLFへ変換されることを一時indexで確認した。
これはbyte hashを使うprovenanceと凍結証拠の一致に影響するため、公開時に検証済みbyte列を保つことを受入条件とする。
`.gitattributes`でsrc・cluster_scripts・tests・docs/wp/data_*の改行変換を無効化し、内容自体は書き換えない。
受入は、一時indexのGit blobと検証済みsource・driver・test・dataのbyte一致、および実indexが変更されていないことで確認する。
一時indexの893ファイルを確認し、保護対象のbyte差は0件、実indexは変更されていないことを確認した。
記録は[data_experimental_release_2026-10-19/git_candidate_preserved_v1.json](data_experimental_release_2026-10-19/git_candidate_preserved_v1.json)にある。
文書だけの改行正規化は区別し、文書buildとリンク検査で確認する。

## 2026-10-19 11:31 JST: Git保存内容からの確認

Gitの一時indexから896ファイル・140,023,217byteの候補を取り出し、全ファイルのGit blobとのbyte一致を確認した。
初回archiveはWindowsの改行変換を受けたため採用せず、core.autocrlf=falseで書き出した候補を使った。
以前の候補から変わった保護対象は進捗台帳への追記だけであり、テスト済みコードと科学データは一致した。
実index・HEAD・remoteは変更していない。
記録は[data_experimental_release_2026-10-19/git_export_v3.json](data_experimental_release_2026-10-19/git_export_v3.json)にある。
この候補からinstalled optional suiteを実行し、2,306 passed・7 skipped、246.44秒で成功した。
全896ファイルの内容は実行前後で一致し、元worktreeの計測dataへのアクセスはprobeで検出されなかった。
記録は[data_experimental_release_2026-10-19/git_optional_suite_v3.json](data_experimental_release_2026-10-19/git_optional_suite_v3.json)と[集計](data_experimental_release_2026-10-19/git_optional_suite_v3_analysis.json)にある。
Git候補のstrict文書buildと15content page・1,568local link/asset確認も成功した。
Git候補から新たに作ったwheelは、既にcore・optional・実行例で検証したwheelと全memberの内容が一致した。
zipコンテナのSHAは生成日時等で異なるため、wheel memberのbyte一致と区別する。
記録は[data_experimental_release_2026-10-19/git_wheel_v3.json](data_experimental_release_2026-10-19/git_wheel_v3.json)にある。
公開候補と到達可能なGit履歴のpattern検査では該当0件で、範囲と対象外は[検査記録](data_experimental_release_2026-10-19/git_publication_review_v3.json)に保存した。
ライブラリの検証コマンドは[公開候補の確認手順](experimental_release_checks_2026-10-19_ja.md)にまとめた。
この結果を反映する最終候補ではコード・テスト・既存科学データの一致を維持し、追加の検証記録と文書を含めて配布物を作る。
remote CI・commit・push・公開は未実施である。

## 継続する数値検証

tile72/288のbit-flip・depolarizingを対象とした長い低ノイズ検証と独立計時は未完了である。
低ノイズ正式比較は3/12条件完了で、2026-10-19 11:24 JSTの実行中ジョブは標本生成265319と標本集約265323である。
標本生成265316はexit 0・run_count 1で完了し、保存済み実行証拠を確認して集約265323をqsubで投入した。
クラスタ投入はqsubを使い、待機中を含む要求node数を最大2とする。
最新の状態は[tile検証の進捗](tile_validation_status_2026-10-17_ja.md)に記録する。
公開後もこの検証を継続し、生データ・環境・再現手順・日本語報告を保存する。
