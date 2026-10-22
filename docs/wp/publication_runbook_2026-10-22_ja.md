# Experimental版公開の手順書（2026-10-22）

公開前の準備は完了しており、GitHubのリポジトリはprivateのまま、tag `v0.1.0.dev5` が `main` の先頭を指している。
ここに書くのは、所有者が公開を決めてから行う操作と、その後に残る作業である。
各手順は実行した日時と結果を `docs/handoff/IMPLEMENTATION_STATUS.md` に追記する。

## 1. 公開前の最終確認

`git status --short` が空で、`git log -1` が tag `v0.1.0.dev5` と同じcommitであることを確認する。
`gh run list --limit 1` で最新のremote CIが success であることを確認する。
文書中の公開日は 2026-10-22 と書いてあるので、別の日に公開する場合は README日英・リリースノート日英・`CITATION.cff`・`CONTRIBUTING.md`・`CHANGELOG.md`・`AGENTS.md` の日付を直してcommit・pushし、tagを付け直す。

GitHubの Settings → Emails で「Keep my email addresses private」と「Block command line pushes that expose my email」をONにする。
noreplyアドレスの `user.email` は研究室PCの `C:\dev\mcmc4qec` にしか設定していないので、この設定がないと自宅PC・クラスタ・Codex worktreeからのcommitで個人メールアドレスが公開履歴に戻る。
各マシンで `git config --global user.email 29061066+junichiharuna@users.noreply.github.com` を実行してもよいが、GitHub側のブロックは1回で全マシンに効く。

## 2. public化

```sh
gh repo edit junichiharuna/mcmc4qec --visibility public --accept-visibility-change-consequences
gh repo view junichiharuna/mcmc4qec --json visibility
```

public化は所有者が指示したときだけ行う。
RIMC側の投稿手順は、投稿当日にこのvisibilityがpublicであることを確認する。

## 3. Zenodo連携とRelease

Zenodoの GitHub 設定（https://zenodo.org/account/settings/github/）で `junichiharuna/mcmc4qec` のスイッチをONにする。
この操作はWeb UIで所有者が行う。
連携をONにした後に Release を作らないとZenodoはアーカイブしないので、順番を守る。

リリースノートの相対リンクはReleasesページでは解決されないので、`.github/scripts/release_body.py` で `blob/v0.1.0.dev5` の絶対URLに変換した本文を使う。

```sh
python .github/scripts/release_body.py v0.1.0.dev5 > output/release_body.md
gh release create v0.1.0.dev5 --prerelease --title "mcmc4qec 0.1.0.dev5 (experimental)" --notes-file output/release_body.md
```

Zenodoの記録ができたら、concept DOI（版をまたぐDOI）を `CITATION.cff` の `doi` に書き、README日英の引用節にも載せてcommit・pushする。
Zenodo側のメタデータは `CITATION.cff` から読まれるので、著者・ORCID・所属が `CITATION.cff` と一致していることを記録ページで確認する。

## 4. 公開後に残る作業

- クラスタ側ドライバがホスト名と絶対ホームパスを証跡に書かないように直してから、低ノイズ検証の次回実行を行う（`TODO.md`）。
- 低ノイズ検証の完了後に、識別子を置換した生データと新しいSHA-256 manifestをZenodoのdataset記録として公開し、リリースノート日英の「公開download先は未確定」をDOIに置き換える（`TODO.md`）。
- 他のクローン（自宅PC、クラスタ、Codex worktree）は旧履歴をmergeせず、`git fetch origin` の後に `git reset --hard origin/main` で置き換える。
- GitHub上に残る旧コミットのキャッシュは所有者の判断でそのままとした。消す場合はGitHub Supportに unreachable commits の削除を依頼する。

## 5. 参照

- 公開準備の記録: [experimental_release_readiness_2026-10-19_ja.md](experimental_release_readiness_2026-10-19_ja.md)
- 履歴書き換えの経緯: `docs/handoff/IMPLEMENTATION_STATUS.md` の 2026-10-22 の節
- RIMC側の投稿手順: `RIMC/docs/handoffs/2026-10-15-zenodo-release-rehearsal.md` 第6節
