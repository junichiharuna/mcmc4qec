# C1T2のcollector・trace監査への接続

## 小仕様

C1T2生成再開driverの正常完了recordと、実投入3件を束ねたregistryを待つ。
元のregistry readerで条件・production manifest・script・resource・receipt・異なるjob IDを照合する。
既存のLinux受入済みC1T2 collector configとcapacity/full監査configを外部hashで固定する。
同じ受入済みC1T1制御driverの順序・実PBS終端・最大2要求ノード・一度だけの操作を継承する。
先行監査は修正後C1T1 full監査の実正常終端とterminal受理を要求する。
全workerの呼出しに生成時と同じthread環境をPython起動前に付ける既存adapterを再利用する。
collector、capacity監査、full監査の順に実行し、sourceや数値計算やnative判定を変更しない。
reference生成とPCでのBAR処理は別driverが担当し、このdriverは科学的なcohort受理を宣言しない。
失敗や投入結果不明は証拠を残して停止し、自動再投入しない。

## 受入条件

実C1T2 configの受入hashと条件・root・collector参照が一致することを確認する。
別条件、別root、異なるcollector参照は拒否する。
生成registry未完了なら操作せず待ち、生成error・別registry・hash違い・scope違いを拒否する。
実registry readerの条件検査と、元driverの操作順・実PBS検査・slot制限・一度だけの操作の回帰テストを実施する。
前条件の実行recordや未完了の科学結果を成功証拠として代用しない。

## 実施結果

Windows Python 3.11で新しい接続部分13 passed・0.79秒、元制御と環境adapterの回帰38 passed・0.83秒、registry契約の回帰26 passed・0.67秒だった。
実C1T2 config・native受入record・生成と先行監査のintentを読み、子起動やremote操作なしでprelaunch bindingsを照合した。
新driver自体のLinux試験は未実施であり、Windows上の制御driverとして動かす。
Linuxで稼働するworker・元のnative検査・科学的計算は変更していない。
[sourceと受入ログ](data_tile_validation_2026-10-17/c1t2_collection_audit_handoff_acceptance_v1/manifest.json)のmanifest SHA-256は `4b352b187586630ec52ea581b507b84f9f3f7109d3e82fc74c03a5525f89e5ef` である。
driver SHA-256は `d35e1ddb57f8e0f7284126c1a3ca9d19c02df82bc34e19f0344d4b4ba2e8a534` で、稼働中に変更しない。
local PID7312で起動し、00:39 JSTにsessionの継続をpollで確認した。
実行記録は `data_tile_validation_2026-10-17/c1t2_collection_audit_handoff_v1/` に保存する。
この時点では生成registry未完了であり、新collector・監査のqsubは未実施である。
この接続準備をC1T2のsampling・監査・科学的検証の完了とは扱わない。
