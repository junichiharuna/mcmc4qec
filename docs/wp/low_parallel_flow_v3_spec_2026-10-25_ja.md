# Reader CLIの固定を含むcontroller仕様

v3の比較workerでnested reader CLIのimport origin不一致が見つかったため、同じ内容のCLIを専用ディレクトリへ移し、readerとCLIの両方を環境の変更規則に記録する。
controllerもreaderとCLIの両方のsource pinを固定する。
環境の規則は従来の5フィールド、または`cli_before`と`cli_after`を追加した7フィールドだけを受け入れる。
片方だけのCLIフィールド、未知のフィールド、不正なpinは拒否する。
`stable()`は追加したCLIの内容変更も検出する。
数値処理、worker数、配置、mergeとtailの順序、投入方針は変更しない。
v2 controllerとその30テストの証跡は過去の記録として保持する。

## 受入条件

- 従来の規則と新しい規則の両方を検証する。
- 不完全または未知の規則を拒否する。
- CLIファイルを変更すると、controllerの固定ファイル確認が失敗する。
- 既存の制御とlauncherの30テストを維持する。
- テストと実際の設定によるconstructor確認はPBSで行い、ローカル計算を実行しない。

constructorの確認だけでは、nested readerや全計算の正常完了を保証しない。
実entrypoint確認、canary、全worker終了、merge、独立計時、最終報告は別の受入対象である。

## 受入記録

PBSジョブ265556で36テストが成功し、F/exit 0を確認した。
この36件は従来の制御・launcherの30件と、新しい環境規則とCLI変更検知の6件で構成する。
PBSジョブ265565でv4の実際の12個のprepared入力と環境によるconstructor確認を実施し、F/exit 0を確認した。
265565の標準エラーログは空だった。
受入JSONの原本SHA-256は`cb953c694fc8596788f412f0b6b40bab3a8b37e6f38c87b85e26dc3808c72830`である。
この確認はshadow journalだけを作り、本番controllerの起動とworkerの投入を行わない。
