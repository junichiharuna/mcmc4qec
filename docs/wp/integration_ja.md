# 統合時の仕様と検証

## 論理基底の明示指定

研究の Hamming HGP と BB ファクトリは完全な論理基底を返すが、X/Z 交差行列は必ずしも単位行列ではない。
研究行列との byte 一致を保つため、`CSSCode(..., logical_basis="independent")` を明示した場合だけ、交差行列が GF(2) 上で可逆な基底を受け入れる。
既定の `logical_basis="paired"` は従来どおり単位行列を要求する。
行列の再基底化は行わず、observable の順序は入力された `lz` / `lx` の行順を保つ。
独立基底の第 i 行の論理 X が、第 i 番の Z observable だけを反転するとは限らない。
decoder の予測と真の observable を同じ可逆変換で変換した場合、標準の全論理 observable 不一致という失敗定義は不変である。
decoder の予測だけを旧座標のまま使えば標準失敗判定も変わり得るため、補正 decoder の論理写像も入力の `lz` / `lx` と一致させる。
独自 predicate の基底不変性は仮定しない。
受入試験では既定の拒否、明示許可、特異な交差行列の拒否、bit / Pauli 全状態の失敗定義と stabilizer 不変性を検証する。

## 進捗

共通基盤統合後の `python -m pytest tests -q` は 156 passed、35.46 秒だった。
ユーザーが著者を `junichi haruna` と明示したため、CFF 著者の判断待ちは解消した。
追加契約の受入試験は実装前に 6 failed（未実装のキーワード引数）、実装後は符号基盤と合わせて 20 passed、0.61 秒だった。
独立レビューでは実装の数学条件に問題は見つからず、関連 80 テストが成功したと報告を受けた。
レビューで decoder の予測座標も変換すべきという説明と試験の不足が指摘され、説明を修正し、補正 decoder の写像を含む全状態テストを追加した。
レビュー対応後の論理基底と provenance 試験は合計 8 passed、0.24 秒だった。
main `f5323c1` の全 suite は 164 passed、40.40 秒だった。

## provenance と公開契約

新しい circuit サブパッケージもソース識別に含めるため、package source hash は相対パス付きの再帰的な Python ファイル列から作る。
実装が未 commit という古い理由は削除し、commit がパッケージに埋め込まれていないため hash を使うと明示する。
ネストしたソースの内容変更およびファイル名変更が hash に反映される試験を実行した。
WP-D の監査結果に基づき、core、noise、results、Stim 接続の公開 docstring に引数、返り値、例外と実験全体の単位を補った。

## 再開後の統合準備

2026-09-30 14:02 JST にユーザーの明示指示で再開した。
最終統合に向けて pyproject と実行時 VERSION を `0.1.0.dev2` に更新したが、この更新だけで WP の受入完了とは扱わない。
core と optional の別 venv は作成済みで、最終 wheel の導入と検証は未実施である。
基準 Python に build は未導入のため、既存の D 作業用 `.venv-cff/Scripts/python.exe` の build 1.6.1 を最終 wheel の構築に使う。
