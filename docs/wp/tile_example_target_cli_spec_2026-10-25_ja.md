# tile固定prior利用例の目標p指定

対象は `examples/workflows/tile_capacity_fixed_prior.py` のCLIのみとし、library API・公開sampling既定・本校正の実行sourceは変更しない。
`--ladder P0,P1,...` を追加し、指定時は有限な開区間(0,1)の確率が2点以上、狭義単調減少であることを要求する。
明示ladderの末尾を目標pとし、別のtarget optionや暗黙ladder生成は追加しない。
option省略時の目標・ladder・seed・出力schema・計算budgetは従来どおりとし、tile72の目標0.03・tile288の目標0.05を維持する。

decoderは構築を1回とし、bit-flipではprior=P、depolarizingではsector prior=2P/3で固定する。
anchor・独立MC・全BAR rungに同じProblemとdecoderを渡し、depolarizingはjoint物理noiseと既存sector復号を維持する。
不正な目標・ladderは出力directory作成や符号構築より前に拒否する。
選んだladderと短いtraceは接続例であり、overlap・混合・95%被覆や推奨設定を保証しない。
低ノイズの正式selectionと独立計時は未完了であり、このCLI追加をその代わりにしない。

受入は、既存2sizeの省略時互換、明示ladder末尾の目標、非有限・境界・順序・点数の拒否、bit/depolarizingのprior・同一object共有を検査する。
契約試験と短い実native CLIは新しい独立stageからqsubへ投入し、最大2物理nodeのgateを使う。
ローカルでのテスト・計算は実施せず、既存source bundleと稼働中runtimeには触れない。
