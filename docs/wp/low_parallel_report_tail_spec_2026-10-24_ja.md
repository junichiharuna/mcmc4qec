# 並列再開後の報告環境の継承仕様

新しい並列 worker の配置指定を受理するため、親 selector の isolated ヘルパーに追加した正規表現だけを、既存の報告用環境にも継承する。
報告用の evaluation_report オーバーレイ、その import_prepend、Python、native binding、runtime、科学計算の設定は維持する。
旧親環境から新親環境への差分は、isolated ヘルパーの source_sha256、resolved_sources、import_origins と、そのディレクトリを先頭に加える pythonpath の四項目に限る。
ヘルパーの変更前後の SHA-256 と内容を確認し、変更内容は単一ノードの select 正規表現に明示的な vnode を許容する一箇所だけとする。
旧報告環境と旧親環境の差分も、既存 evaluation_report の単一モジュール差し替えと import_prepend に限ることを確認する。
新報告環境は実際の新しい source パスと SHA-256 を記録し、旧環境の識別子として扱わない。
報告が merge の証跡を確認するときは従来の bridge.verify と merge runner を使い、census 準備用の別アダプターへ置き換えない。
受入テストでは許可された差分、元入力の保持、科学設定・native・Python・報告オーバーレイの改変拒否、余計な source 変更の拒否を確認する。
テストは許可されたクラスタの qsub ジョブで実施し、ローカルでは未実施とする。
