# WP-C 完了メモ

## 実装したこと

`src/mcmc4qec/circuit/` に、物理 `(location, fault)` 配置の `CircuitFaultModel`、排他的カテゴリの `CircuitFaultNoise`、`PhysicalFaultProposal`、surface logical idle baseline を追加した。
Stim 回路の `X_ERROR`、`Y_ERROR`、`Z_ERROR`、`DEPOLARIZE1`、`DEPOLARIZE2` の各 target group を物理 location として列挙する。
同じ命令の重複 target group は `target_group_index` で別の独立 location として識別する。
利用者が物理 location の列挙規則を渡す入口も追加した。
各 location の fault alphabet と条件付き確率を明示し、location 間の積分布と正規化された `log_prob` を与える。
同一チャネル内でも location 別の条件付き fault 確率と故障率を指定できる。
単一 fault の detector と observable 効果を Stim で取得し、複数 fault を GF(2) XOR で合成する。
物理 location を一様に選ぶ追加・削除・置換の提案と一般 MH 比を実装した。
rotated surface d=3 の noisy 6 ラウンドの中点に理想 `MPP` を置き、前半 3 ラウンドの logical observable を定義した。
後半 3 ラウンドの noisy detector 履歴を PyMatching decoder に渡し、終端のデータ測定は detector 境界用に残した。
中点 `MPP` の追加でずれる測定記録の参照を補正し、Stim DEM と PyMatching の構築を検証した。
`examples/circuit_baseline.py` と科学的な仕様・検証記録 `docs/circuit_baseline_ja.md` を追加した。

## 一次資料との対応

[Rare Event Simulation of Quantum Error-Correcting Circuits, arXiv:2509.13678v2 の第 III・IV 節](https://arxiv.org/html/2509.13678v2) を実際に確認した。
第 III 節の物理 gate fault 配置と排他的な fault を採用した。
第 IV 節の `2d` noisy rounds と前半 `d` rounds のみの論理誤り評価を中点 observable と後半 buffer で実装した。
論文の置換受理 `q_new` と実装の一般 MH 受理 `min(1,q_new/q_old)` は異なるが、どちらも一様な fault ラベル選択に対する詳細釣合いを満たす。
論文の図表再現は主張しない。

## 実行した検証

| 検証 | コマンドと結果 |
| --- | --- |
| 回路モデル | `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_circuit_model.py -q`、10 passed、0.32 秒。 |
| 回路 pipeline | `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_circuit_pipeline.py -q`、5 passed、3.39 秒。 |
| 回路提案 | `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_circuit_proposal.py -q`、3 passed、0.25 秒。 |
| surface baseline | `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_circuit_surface.py -q`、2 passed、20.64 秒。 |
| 回路4ファイル | `C:/Users/user/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_circuit_model.py tests/test_circuit_pipeline.py tests/test_circuit_proposal.py tests/test_circuit_surface.py -q`、20 passed、25.53 秒。 |
| 全 suite | 第1回レビュー修正前は 168 passed、45.11 秒。修正後の全 suite は約 296 秒で 5 分の制約に近づいたため停止し、最終合否は未確認。 |
| core venv | 修正前の全 suite は 140 passed、15 skipped、235.38 秒だが別 suite との CPU 競合があった。Stim/PyMatching を含まない状態で回路パッケージと sampling の import に成功。 |
| example | `PYTHONPATH=src` で `examples/circuit_baseline.py` を実行し、500 試行、失敗率 0.0900、Wilson 95% 区間 `[0.067943, 0.118309]` を得た。 |
| repetition exact | d=3 の 1 ラウンドは 3 location の `4^3=64` 配置、2 ラウンドは全 6 location の `4^6=4096` 配置を列挙した。 |
| repetition zero decoder | `p=0.1` の exact 失敗率は 1 ラウンド `0.0666666667`、2 ラウンド `0.1244444444` で解析値と一致した。 |
| repetition PyMatching | 2 ラウンドの exact 失敗率は `0.02515682853`、同じ Stim 回路と decoder の直接 20,000 試行は `510/20000=0.0255` だった。 |
| surface direct MC | d=3、6 noisy rounds、`p=0.01` の Stim 直接 5,000 試行は 442 失敗、率 0.0884 だった。 |
| surface physical direct MC | 同じ decoder を用いた物理配置 700 試行は 74 失敗、率 0.105714、Wilson 95% 区間 `[0.085049, 0.130683]` で、Stim 直接率を含んだ。 |

小回路の全配置で正規化、support、提案確率の正規化と順逆比、失敗条件を含む詳細釣合いを検証した。
同一チャネルの location 間に異なる確率を与えた小回路でも、正規化、sampling、失敗集合上の MH 詳細釣合いを検証した。
重複 `X_ERROR` target group は二つの独立 location として列挙され、`p=0.1` の exact 失敗率 `0.18` を得た。
確率付き `M(0.2)` と `MPP(0.2)` は決定的な単一 fault 効果を壊すため、回路構築時に拒否する回帰試験を追加した。
条件付き確率の和 `1.0000000005` を拒否する回帰試験を追加し、許容を絶対差 `1e-12` のみにした。
repetition の `sample_faulty` と `estimate_logical_error` への接続、保存標本の failure 条件、非回路での `circuit_single` 拒否、回路での未対応 kernel 混合の拒否を検証した。
ランダムな複数 fault 配置について、単一 fault 効果の XOR と直接 Stim 挿入シミュレーションを照合した。
中点前後のデータ fault で中点 observable の反転有無が異なることを検証した。
別の正式レビュー担当は通常の最終時刻回路と中点回路を独立に構築し、両者の 368 location の順序、48 detector、全単一 fault の detector 効果 368 列が一致することを `docs/wp/C_review_ja.md` に記録した。

## 共有ファイルの接続

メイン担当が `src/mcmc4qec/sampling.py` に `KernelConfig.circuit_single` と `PhysicalFaultProposal` の選択・未対応混合拒否を追加した。
この変更は WP-C の worktree にあり、WP-C コミットに含めることをメインと合意した。
`estimate_logical_error` は既存の `SamplingConfig` を `sample_faulty` に渡すので変更不要だった。

## メインへの依頼

`src/mcmc4qec/__init__.py` への公開名として `CircuitFaultModel`、`CircuitFaultNoise`、`FaultLocation`、`stim_noise_locations`、`uniform_fault_noise`、`PhysicalFaultProposal`、`surface_logical_idle_circuit`、`surface_logical_idle_problem` を検討してほしい。
`KernelConfig.circuit_single` と回路専用設定を README と `docs/api_en.md` に記載してほしい。
共有 `sampling.py` は WP-B の変更と merge 時に競合し得るため、両変更を保持して統合してほしい。

## 未実施と制約

installed wheel の検証、遠隔 CI、論文図表との数値再現、d>3 の統計的照合、回路での BAR ladder の大規模精度検証は未実施。
Z-OBF、cluster exchange、stabilizer flip の回路対応は対象外。
回路内の非 Pauli ノイズ、location 間の相関、排他的でない複数 fault、非 Clifford 回路は未対応。
PyMatching DEM の graphlike 分解に伴う decoder 近似は物理配置分布の近似とは区別する。
診断が良くても収束、既約性、周期性、推定値の正しさの証明にはならない。

## 独立レビューと対応

`docs/wp/C_review_ja.md` の第1回レビューは、2 ラウンド repetition の列挙範囲、location 別の非一様分布、確率和の相対許容の三点を指摘した。
2 ラウンド全 6 location の exact と PyMatching・独立 Stim 照合、location 別 `q_i,p_i` と正規化・sampling・詳細釣合い試験、絶対許容の修正で対応した。
第2回レビューは進行中で、確率付き測定と同一命令の重複 target group に関する反例を修正した。
最終受入判定はレビュー担当の確認待ち。

## 作業履歴

一時的な所有者判断待ちの指示に従い実装を停止し、論文と API の調査だけを旧メモに残した。
所有者から著者情報が明示されて停止理由が解消した後、実装を再開して本メモを完了結果へ更新した。
