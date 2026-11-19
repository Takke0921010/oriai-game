# 折り合い v2.0

福島の除去土壌をめぐる3人用ゲームの試作です。ブラウザだけで動きます。

- 遊ぶ：`oriai-v2.0-testplay.html` をブラウザで開く（GitHub Pages のURLからも遊べます）
- 説明動画：`video/oriai-v2.0-explainer.mp4`（約3分）

## ゲームの流れ

1. **フェーズ1　土の行き先**（最大4ラウンド）　除染で出た土を、自分の仮置場に置くか、トークンを渡して他の地域に頼むか、庭先に残す。
2. **どんでん返し**　仮置場が満杯になり、施設をどこに建てるかを話し合っていると、国から知らせが届く。D・E・F……県内の多くの地域の土も集まる施設を、A・B・Cにまたがって建てる計画だった。3人とも「受け入れる側」になる。
3. **フェーズ2　受け入れの問い**（3ターン）　説明会、土地の買い取りの提案、時間の経過と住民からの決断の要請。町長はサイコロを振り、住民の反応（賛成・条件次第・反対）を知る。最後に、他の人に見せずに受け入れるかどうかを決める。勝ち負けはない。
4. **振り返り**　実際の大熊町・双葉町の経緯と両町長の証言をもとに、受け入れた判断も、受け入れなかった判断も間違いではないことを考える。

地域A・B・Cは架空です。ゲーム内の効果・数値は想定で、史実は振り返りの画面に出典を示しています。

## ファイル

| ファイル | 内容 |
|---|---|
| `index.html` | トップページ |
| `oriai-v2.0-testplay.html` | ゲーム本体（1ファイルで完結） |
| `video/oriai-v2.0-explainer.mp4` | 説明動画 |
| `video/oriai-v2.0-explainer.html` | 説明動画の映像（時刻を指定して描くアニメーション） |
| `video/narration.json` | ナレーション原稿 |
| `video/build_timeline.py`, `render.mjs`, `assemble.swift` | 動画を作り直すスクリプト |

## 説明動画の作り直し（macOS）

```sh
cd video
# 原稿から音声（say -v Kyoko）を作り、各場面の時間を決める手順は narration.json → build/narration-timed.json → build_timeline.py
python3 build_timeline.py
node render.mjs all 30          # Playwright 付属の headless Chromium で1コマずつ撮る
swiftc -O -o build/assemble assemble.swift
./build/assemble build/frames build/timeline.json build/audio oriai-v2.0-explainer.mp4
```

音声ファイルとコマ画像（`video/build/audio`, `video/build/frames`）は容量が大きいためリポジトリに含めていません。
