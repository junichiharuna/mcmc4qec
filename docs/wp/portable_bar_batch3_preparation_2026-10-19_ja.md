# Portable BAR batch 3の準備

2026-10-19 23:29 JSTまでに、元のhost割当と未予約groupの選択規則を維持して、DGXの20 groupとLaboの24 groupを配置した。
DGXは`(0,2,0,1,36..47)`と`(0,2,0,1,72..79)`、Laboは`(0,2,0,1,48..71)`である。
推定値や診断値を選択に使わず、完了した入力の有無だけで選んだ。
archive・sourceの転送hashを検証した。

全予約は176 groupで、DGX 80・Labo 96、重複は0、未予約は592 groupである。
これは完了数ではなく、回収済みはDGX batch 0/1の40 groupのままである。
照合記録は`data_portable_bar_2026-10-19/batch3-preparation-verification-v1.json`にある。

DGX batch 2→3のcontrollerをlocal PID 6916で起動した。
controllerは元の回収helperを用い、実行中のbatch 2が終端して回収の検証を通るまでbatch 3を開始しない。
23:29 JSTにbatch 2のremote PID 536478がliveであることを再照会した。
この時点でDGX・Laboともbatch 3は未起動である。
既存のPID 34240はbatch 0→1、PID 40396はDGX batch 1→2を担当しており、同じ回収・起動を別processから重複実行しない。
Labo batch 2/3の引継ぎcontrollerは、先行batchの実起動と実execution intentへの回収設定を確認してから準備する。

最終集約の受入条件を[別の小仕様](portable_bar_final_join_spec_2026-10-19_ja.md)に記録した。
最終reader、全設定での追加移植比較、全768 groupの監査・reference結合は未完了である。
