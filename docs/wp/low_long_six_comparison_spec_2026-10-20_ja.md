# tile72低ノイズ6条件の比較追補仕様

既存5条件の独立算術レビューに基づく80設定を保持し、回収済みC0T2 reportから事前固定の長い16設定を追加する。
C0T2はreport集計の抽出であり、この追補によって保存BAR行の独立算術レビューを実施したとは扱わない。
元5条件の比較記録とCSV、C0T2 reportと回収receiptをSHA-256で固定し、入力を処理前後で照合する。
条件はtile72のbit-flip/depolarizingとp=.01/.003/.001の6組であり、各条件352設定・67,584行・192 seedという元集計の識別情報を検査する。
長い設定はbit-flipで16 chain・保存60,000、depolarizingで8 chain・保存12,000、共通でburn-in 6,000・fine ladderとする。
ZH/ZHS、logical_basis/logical_combination、block32/128/1024とcross_chainの16組を全て保持する。
各設定の分母192を保持し、警告・診断未定義・区間未取得によって分母を縮めない。
方法別の範囲は4組の最小値・最大値であり、seedをプールしない。
同一condition・kernel・初期化の4方法で点推定のbias/RMSEと混合診断が一致することを検査する。
差異があれば自動修正せず停止する。
受入ではC0T2 identity、欠落・重複、分母変更、未取得区間とnullの保持、方法間の点推定差異の検出を確認してから実装する。
保存済みreportの抽出と描画のみを行い、sampling、decoder、BAR、bootstrap、WSSを再実行しない。
有限reference区間との重なり・包含を真値の95%被覆保証とせず、観測結果による誤差法の事後選択や公開既定の変更を行わない。
source・試験・環境・入力hash・集計CSV・再現手順を新しいdirectoryへ保存し、既存5条件の成果物を上書きしない。
