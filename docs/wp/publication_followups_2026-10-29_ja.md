# 公開に向けた残作業（独立計時の完了を受けて、2026-10-29）

本稿は独立計時 48 行と最終 report の受理（2026-10-29 02:21 JST）を受けて、公開文書・論文整合・所有者判断の残りを整理したものである。
公開文書のうち README と release notes の文面は所有者の確認を要するので、本稿では案として書き、適用していない。
英語の途中案内（`docs/tile_validation_interim_en.md`）だけは「2026-10-29 の更新」節を先頭に追加した。
所属・DOI・Zenodo は所有者のみの判断で、本稿では触れない。

## 1. 公開文書の更新点

### 1.1 `docs/tile_validation_interim_en.md`（適用済み）

旧版は「全 12 条件の比較・独立計時・最終推奨は未完了」（2026-10-23 時点）だった。
先頭に 2026-10-29 の更新節を加え、次を書いた。

- 独立計時 48 行が完了し、選択 12 条件（tile72 bit-flip・depolarizing × p ∈ {0.01, 0.003, 0.001} × ε ∈ {0.2, 0.1}）は MC・BAR とも 192/192。
- 凍結 report の費用比（両手法が精度 gate を通った 3 条件）と、精度正規化比のクロスオーバー（p = 0.01 では直接 MC、p ≤ 0.003 では BAR）。
- BAR の区間被覆は 151〜176/192 で名目 95% に届かず、混合診断は未取得。
- tile288 の 12 行は参照区間の幅のため未選択。
- 原本・写し・条件別の表への参照。

旧版の本文は履歴として残し、冒頭の 1 文で更新節を指すようにした。

### 1.2 `docs/experimental_release_notes_en.md`（案、未適用）

44 行目の「low-noise calibration and timing studies remain in progress. Observed mixing problems and interval undercoverage prevent a general claim of nominal 95% coverage or speed improvement.」を次に置き換える案である。

> The low-noise calibration and the independent timing study (48 method rows, 192 replicates each) have completed; see `tile_validation_interim_en.md` for the 29 October 2026 update.
> BAR interval under-coverage (151–176 of 192) and the absence of mixing diagnostics in the timing study still prevent a general claim of nominal 95% coverage.
> A speed advantage of BAR over direct MC is supported only for tile72 at `p ≤ 0.003` (2–35× in precision-normalized cost); at `p = 0.01` direct MC is cheaper.

31 行目の Zenodo dataset の計画（「after the low-noise validation completes」）は条件が満たされたので、raw データの公開範囲（校正 raw 223 GiB を含めるか）を決めてから文面を更新する。

### 1.3 `README.md`・`README_ja.md`（案、未適用）

「Status and limitations」に 1 文を足す案である。

> The low-noise timing study found BAR cheaper than direct MC only below `p ≈ 0.003` on the tile72 codes, and its intervals under-covered; see the release notes.

性能の節（dev5 WP-Q の `docs/performance_ja.md`）は研究 runner との step 速度の比較であり、今回の MC/BAR 費用比とは別の量なので混ぜない。

## 2. 論文（RIMC）との整合点

| 論点 | 論文の記述 | 今回の結果 | 整合 |
|---|---|---|---|
| MC との速度比較の定義 | 目標精度 2% に達するまでの時間 T₂%（分散は参照計算から固定） | 精度正規化費用 C_ε = C×(r/ε)²（192 反復の経験的 RMSE） | 同じ趣旨。定義の違い（固定分散 vs 経験的 RMSE、ε = 10〜20% vs 2%）を論文側で明記する |
| クロスオーバー | p = 10⁻¹ で直接 MC が 2〜3 桁速く、10⁻⁵ で splitting が全符号で速い | tile72 では p = 0.01 と 0.003 の間 | 定性的に整合。tile72 の論理エラー率は p = 0.01 で約 2.6×10⁻³ と高めで、クロスオーバーが論文の符号より高い p にあるのは自然 |
| 被覆 | 誤差棒は独立 chain 間のばらつき（K = 50）、burn-in 5·IAT | ライブラリの BAR 区間（ladder 固定、独立 192 反復で評価）は 79〜92% 被覆 | 名目被覆は主張しない方針を維持。WP-P の結論（ライブラリ既定の区間法は論文の手順と異なる）と整合 |
| bias | — | case 2・p = 0.001・ε = 0.2 の BAR に相対 bias −0.14 | 論文の「trapping による bias」の議論と照らし、tile72 depolarizing の低 p で BAR 鎖の混合を疑う材料として記録する |

## 3. 所有者判断と実施状況（2026-10-29 11:10 時点）

- 9 条件の扱いは決定済み（精度正規化で全 12 条件を示す）。
- raw データの公開範囲は決定済み: 校正 cohort の raw（223 GiB）は非公開で保管、それ以外を公開する。README・release notes の文面（上の 1.2・1.3 の案）は適用した。
- 公開データセットの staging は完了した。クラスタの `zenodo-dataset-staging-v1/`（20 GB、150,936 ファイル）に、A: 最終 report が pin する全 path（86,902）、B: report job root（16）、C: 経路記録（76）、D: 校正 run の summary 類（traces と analysis を除く 63,942）を置いた。テキスト 1,415 ファイル（512 MiB 超の 5 本は stream 処理）でユーザー名・ホスト名を置換し、置換後の grep は 0 件。`MANIFEST.tsv`（公開物の sha）と `ORIGINALS.tsv`（原本の sha、証拠内の hash と照合用）、`STAGING.json` を同梱した。script は `output/zenodo_dataset_staging_v1/`、manifest の写しは `docs/wp/data_tile_validation_2026-10-17/low_noise_final_report_2026-10-29/`。
- 残りは所有者による Zenodo record の作成（tarball 分割・metadata・所属・DOI）と、Zenodo 作成後の README の DOI 追記である。
- クラスタ workspace の削除は実施した（[整理案の実施記録](cluster_workspace_cleanup_proposal_2026-10-29_ja.md)）。bar-recovery 2 本（17 GiB）だけ保留。
- 次回 run の変更は delta G・W・P・R として実装・検証済み（[変更案の実装状況](next_run_changes_proposal_2026-10-29_ja.md)）。次版 authority 層の作り直しの時期は未定。
- 所属・DOI・Zenodo の作成、experimental 版の更新公開の時期は所有者判断のまま。

## 4. 完了していないこと

- 正規化比の bootstrap 標準誤差（per-replicate 記録から計算可能、未実施）。
- 最終科学証拠の snapshot 保存（source・環境・seed・設定・script の束ね）と再現手順の照合。
- v13 config に束ねた final-report 役の受領書（環境 v2 では作れないので、次版の鎖で作る）。
