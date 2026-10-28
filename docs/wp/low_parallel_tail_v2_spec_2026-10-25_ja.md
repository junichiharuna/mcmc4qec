# 全12 singleton 比較の後続処理

旧 worker の結果が未成立であるため、全12条件をそれぞれ新しい worker で処理し、固定2ノードに6件ずつ配置する。
後続処理は `output/low_parallel_tail_v2` を使用し、凍結済み v1 は変更しない。
v1 に対する実装差分は handoff の worker ID 件数を9件から12件へ変更することだけである。
全12条件への一意な割当は上流の versioned merge が検証し、tail は12件の異なる worker ID と、それらとは異なる merge ID、完全な accepted seal を要求する。
staged の不足 metadata pin 補完は科学 source の変更ではなく、上流で既存証跡と照合して行う。
親環境・census basis・報告環境の変更範囲と、元 driver・元検証器・完全な科学的分母を保持する契約は v1 の仕様を継承する。
受入テスト17件のうち handoff fixture を12件へ変更し、ローカルでは実行しない。
