# C0T1 回復後の独立reference比較の準備

対象は `partitioned-full-0-1-v1` の192 seed・768群であり、元BAR job 265334の時間切れを回復job 265340で補う。
既存の `low_bar_recovery_report_parent.py` とそのtrace・reference・result binderを変更せずに用いる。
集計式、失敗定義、seed集合、未収束・診断未定義・区間未取得の扱いは変更しない。

まず検証済みC0T0配置transportの接続先control、証拠ファイル名、report出力先だけをC0T1用に変更し、独立した `report_helpers_v1` ディレクトリへ配置する。
配置時には元回復deploymentの全source hashとruntimeを照合し、Linux上のimportとbash構文を検査する。
配置はqsubを行わず、reportの準備や数値比較の完了を意味しない。

reportの準備には、回復jobの実PBS F・exit 0・run_count 1と受入済みcompletion、C0T1のfull trace監査job 265336の受入済み証拠、独立WSS referenceとその監査証拠を必要とする。
referenceの条件番号は `4 * case + target_index + 1 = 2` とし、前のC0T0の条件番号1を流用しない。
実終端前にcompletionや資源計画を作ったことにはしない。
既存の資源方針は実終端の時間・RSSから要求上限を決めるものであり、終了時刻の予測ではない。

reportを投入する際は既存の共有lockと直前の占有ノード数確認を使い、qsubで最大2ノードを守る。
PBS内で全BAR payload、元trace、独立referenceを読み直し、最終67584行の分母を保持して比較する。
実PBS終端の受入、成果物の回収とhash照合が済むまで、C0T1の最終bias・RMSE・被覆は未検証とする。

この文書作成時点では、C0T1向けreportの配置、起動transport、準備、投入、回収はいずれも未実施である。
実施後の状態と証拠は `POST_FREEZE_STATUS_2026-10-19_ja.md` に追記する。

## 起動・回収手順の追加

C0T1用の起動・完了受入・回収transportを追加し、以下の順序で実行する。
全コマンドはリポジトリ直下から指定のPython 3.11で実行し、既存の実行証拠がある場合は再実行せず、その証拠と実PBS状態を調べる。

1. job 265340の実PBS F・exit 0・run_count 1を確認した後、`output/complete_low_bar_recovery_c0t1_once_v1.py` で回復結果を受け入れる。
2. `output/control_low_bar_recovery_report_c0t1_v1.py prepare` で回復completionとtrace job 265336、独立referenceの証拠を照合し、実測済み上流資源を基にreportを準備する。
3. 同じcontrollerの `preflight` で準備済み入力と空きノードを確認し、`execute` で共有lock内の直前確認を経てqsubを1回だけ呼ぶ。
4. report jobの実PBS正常終端後、`output/complete_low_bar_recovery_report_c0t1_once_v1.py` で終端と成果物metadataを受け入れる。
5. `output/collect_low_bar_recovery_report_c0t1_once_v1.py` で転送前後のsnapshotとローカルbyte/hashを照合して回収する。

`observe` は読み取り専用であり、実行した結果は回復job 265340がR、report launch未作成、占有2ノードだった。
起動transport・入力照合は14 test・2.32秒、完了受入・回収transportは10 test・1.57秒で成功した。
テストではSSH・qsubをmockし、実traceの受入証拠と配置証拠の読み直しも行った。
外部pytest pluginの自動読込みは `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` で無効にした。
回復受入前のprepareはネットワーク呼出しや実行証拠作成より前に拒否する。
reportのprepare・preflight・execute・実終端受入・回収は引き続き未実施である。
