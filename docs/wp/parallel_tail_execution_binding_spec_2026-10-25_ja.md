# 並列 merge 後段の実行検証接続

対象は tail v2 の六段階と、8 CPU merge を受け取る census / report の運用上の接続だけである。
旧 tail、report、環境、科学的な選択・24 行・校正・seed の仕様は変更しない。
新版は別ディレクトリに保存し、元 source と実際に実行する source の SHA-256 を別々に記録する。

census driver は旧 bridge / runner の受入原本を従来通り検証した後、新しい明示 pin に切り替え、新 source も stable 検査に含める。
report preparation は selection_descriptor の検証と返す科学情報を維持し、bridge / runner の二つの pin だけを明示設定に切り替える。
bridge と report source の変更範囲は別仕様 `parallel_tail_bridge_overlay_spec_2026-10-25_ja.md` に従う。
新 execution runner と contract の SHA は受入済み parallel merge v6 の値に固定する。
設定は元の source closure と新 adapter closure を保持し、parallel merge deployment、元 report 環境、新 report 環境、環境差分を byte pin で結ぶ。
環境検証は元 report 環境を再読込し、唯一許可した四フィールド差分と新 report source を再導出して完全比較する。
native bootstrap の成功記録を science 実行、全条件比較完了、独立計時完了と解釈しない。

受入は旧 pin の保持、census の新 pin 登録、report の科学 descriptor 不変、新 helper 改変拒否、余分な source 編集拒否、環境差分拒否を対象とする。
ローカルでは実行せず、最大二つの物理ノードの既存 admission gate を通す qsub で実施する。
