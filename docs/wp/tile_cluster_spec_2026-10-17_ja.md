# Tile factoryとクラスタdriverの実装前仕様

2026-10-17、実装前に次の受入条件を固定する。
上位の科学計画は `calibration_cluster_design_2026-10-17_ja.md` とする。

## Tile

公開APIは `make_tile_code(l, m, *, preset="w6_288_8_12") -> CSSCode` とする。
l,mは3以上の整数で、boolを拒否する。
水平辺のX supportは(1,0),(2,0),(0,2)、垂直辺は(0,0),(2,1),(2,2)とする。
Zは水平垂直を交換し、両座標を(2-x,2-y)に反転する。
物理辺の候補は水平・垂直それぞれ0<=x<l,0<=y<mであり、順序は水平、垂直、各々y-major/x-minorとする。
X anchorは0<=x<l-2,-2<=y<m、Z anchorは-2<=x<l,0<=y<m-2である。
supportを物理辺へ制限し、X/Zの双方から支持されないqubitを同時に除き、その後に空rowを除く。
削除前後の可換性を確認し、不成立を修正せず例外にする。
GF(2) quotientから論理basisを作り、Lx Lz^T=Iに変換する。
12x12でn=288,k=8,bulk weight6、6x6でn=72,k=8を検査する。
最小例は列挙でdistanceとfailureを検査するが、代表例のdistance12の下界は独立検証したと主張しない。
内部の同一layout処理をB=2のsurface tileへ適用し、既存surfaceのn,k,dとweight分布で照合する。
各sectorのBP-OSD接続、MWPMのhyperedge拒否、公開export・型・文書を検査する。

## Cluster

全乱数keyを整数列で固定し、worker数・task順序・resumeから独立にする。
第1段階のfixed manifestを生成し、sampling46,080 task・analysis64,512行を検査する。
2ノード上限はPBS依存チェーンで強制し、dry-runと実投入が同じ計画を使う。
真値bankは有限状態を整数index順で分割し、各状態のweight、syndrome weight、残余logical sectorを記録する。
syndromeにのみ依存する固定decoderの予測をsyndrome単位で再利用し、公開Problem.is_faultyとの小状態全照合を受入条件とする。
stationary startはweight別の確率massを引いて、そのweight内のfailure状態を一様に引く二段階抽選とする。
dispersed startはweightの昇順/降順を交互に使い、未使用sector優先、同sectorなら未使用状態優先、integer state indexでtie-breakする。
compact BARは整数weightの度数に対するweighted Bennett方程式を用い、既存BARと数値照合する。
円環block度数はprefix sumsで求め、末尾blockの切断と同rungの左右共有を保持する。
各artifactはatomic renameとchecksum付きmarkerで確定し、破損・不完全・異なるmanifestの結果を成功として再利用しない。
sampling中の失敗もtask状態として記録し、cohortから黙って除外しない。
解析前に全expected taskのmanifestとartifactを検査する。
smokeは局所的な全列挙・sampling・analysis・resume・異なるworker数・tile BP-OSD経路を含む。
クラスタの実測から資源を設定し、実行するコードと依存環境をbundle hashで固定する。
RIMCのファイルや既存環境を変更せず、新しいrun領域に配置する。
