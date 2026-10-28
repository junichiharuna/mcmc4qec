# 並列比較後のクラスタ内後続処理

既存 worker の結果と既存 driver は変更せず、新しい比較の accepted seal から seed census、独立計時、最終報告までを新しい保存先で接続する。
全12条件・24比較・48手法行と未達／不適格行を維持し、選択・seed・計時・科学計算の規則は変更しない。
親環境の変更は承認された isolated reader の配置指定検証だけとし、元と新の source、resolved path、import origin、pythonpath を明示して検証する。
新しい census basis は親環境 pin、pythonpath、該当 isolated source pin だけを変更し、baseline、core、native、profile、fixture と source relocation を保持する。
報告環境は既存の報告専用 overlay を保持して同じ isolated 変更を適用する。
旧 source closure を新しい結果に付け直さず、実際に使用する新 closure を後続処理まで引き継ぐ。
元の merge runner と bridge.verify の hash を保持できるため、報告の固定された検証器を差し替えない。
新 driver adapter は、pin された元 driver を別プロセスで読み、明示された入出力パスと環境 pin の定数だけを設定する。
independent preparation の親環境パスは関数内の固定値なので、その1式だけを設定値への参照に変換し、残りの source を保持する。
census preparation の payload は新 handoff の9個の worker ID、merge ID、accepted と selection の新しいパスを照合する。
すべての待受はクラスタ上で行い、ssh/scp 呼出しは既存の同一クラスタ transport によりローカル接続を不要にする。
計算ジョブは元の qsub 実装を使い、最大2ノード制御と一回限りの投入記録を保持する。
既存の出力先に error や完了記録があっても削除・再利用せず、新しい journal root と config/job root を使う。
受入テストは設定変更範囲、source 改変拒否、完全な handoff、元環境の混入拒否、報告 overlay の保持を対象にし、PBS 上だけで実施する。
実環境の bootstrap と後続準備の受入は別途必要であり、構文・単体テストの成功だけで完了を宣言しない。
