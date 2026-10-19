# 追加BAR seed全数監査の回収・独立照合

ジョブ `265253.node-PRISM` はPBSで正常終了し、経過時間は25分14秒だった。
既存48 namespaceとBAR stage140/141の追加8 namespaceを合わせた56 namespace・3,963,562件を全数検査した。
未検査は0件、予期しない衝突は0件、unique seedは3,955,114件、既知の意図的共有は8,448件だった。
全数監査本体は1,504.881秒、driver全体は1,511.514秒であり、pilot外挿428秒を完了予測として扱わなかった。

`recovered/` に保存した172ファイルの転送hashを確認し、固定plan、source、環境、submission、PBS、execution、completion、全数結果との結合を独立照合した。
追加件数はmanifestから別途数式で数え、既存48 namespaceの件数とrole別件数へ加えて保存結果と一致することを確認した。
独立照合ではseed列を再生成せず、予定全数監査の保存証拠を検証した。
全stream SHA256は `89c16e9c9ebb47298c402b2f04b5b1f60fc4b28578987011b01d5a13fd239bb9` である。
独立検証証拠 `independent_verification.json` のSHA256は `a480854ea51d32056f6baa72f0720e560481e63ab1681470d52fe4e51ace214d` である。
stage140/141の未列挙予約はなく、SQLite集合DBは監査終了時に削除されている。

この結果は有限の予定seed集合の非衝突確認であり、乱数列の統計的独立性や実sampling記録の正しさを保証しない。
BARの独立計時・精度確認や同精度速度比較の完了を意味しない。

BAR capacityの4caseについて、既存sourceとruntimeからのmanifest再構築一致、各192task、PBS構文と固定初期資源1ノード・96CPU・340GiB・24時間を確認した。
その証拠は `../bar_capacity_readiness_v1/` に保存した。
親による投入用wrapperは共有lock、直前のcontroller不在・queuedを含む最大2ノード、全数監査成功、source/input/output hash、PBS F/0を再確認する。
外部pinを固定したcase0の読み取り専用preflightは成功し、`../bar_capacity_case0_preflight_v1_*` に保存した。
この監視・回収・照合担当は追加qsubを実行していない。
