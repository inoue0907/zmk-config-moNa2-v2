# tools

## ble_flash.py — PC から無線でファームを焼く

```bash
uv run tools/ble_flash.py --side r      # 右手(親機)
uv run tools/ble_flash.py --side l      # 左手
```

先にキーボードで `&blueboot` を押して DFU モードに入れておく。`dfu-latest`
リリースから DFU ZIP を落として、PC 内蔵の Bluetooth で転送する。

依存（`bleak`）は PEP 723 のインラインメタデータに書いてあるので、`uv` があれば
どの PC でも環境構築は不要。`uv` が無い環境なら `pip install bleak` して
`python tools/ble_flash.py` でも動く。

DFU プロトコルの実装は [recrof/nrf_dfu_py](https://github.com/recrof/nrf_dfu_py) の
`dfu_lib.py`。**ライセンス表記が無いリポジトリなので同梱していない。**
`NRF_DFU_PY_COMMIT` で固定して実行時に取得し、`DFU_LIB_SHA256` で検証して
`~/.cache/zmk-ble-flash/` に置く。上流を更新するときは 2 つの定数を揃えて差し替える
（`sha256sum dfu_lib.py` で出せる）。

`dfu_cli.py` を使わず `dfu_lib` を直接呼んでいるのは、あちらが buttonless DFU
（アプリに繋いでブートローダーへ飛ばす）前提で、`&blueboot` で既に DFU モードに
入っている今回の使い方と噛み合わないため。

詳細と iPhone 経路はリポジトリ直下の README「無線でファームウェアを書き換える」を参照。

## キーマップの図の生成

キーマップの図を `config/mona2.keymap` から生成するスクリプト。どこから実行しても
リポジトリ直下を基準にパスを解決する（標準ライブラリのみ、Python 3）。

```bash
python tools/gen_keymap_svg.py      # -> docs/keymap-positions.svg  (READMEの番号図)
python tools/gen_keymap_viewer.py   # -> docs/keymap-viewer.html    (レイヤー切替表)
```

`docs/` の 2 ファイルは生成物なので、直接編集せずスクリプトを直して再生成する。

| ファイル | 役割 |
| --- | --- |
| `mona2_layout.py` | キー位置番号 0–41 の並び（`GEO`）、keymap のパース、キー名の表示ラベル |
| `gen_keymap_svg.py` | 番号だけの静的 SVG |
| `gen_keymap_viewer.py` | ビューアの HTML（データを `keymap.template.html` に流し込む） |
| `keymap.template.html` | ビューアの見た目。`__DATA__` がデータの差し込み位置 |

## 自動更新

`.github/workflows/keymap-docs.yml` が `config/mona2.keymap` /
`boards/shields/mona2/mona2.dtsi` / `tools/**` の変更を拾って再生成し、
差分があれば `docs/` をコミットし、早見表を GitHub Pages に出す。

- 早見表: <https://inoue0907.github.io/zmk-config-moNa2-v2/>
- 手動実行: `gh workflow run keymap-docs.yml`

コミットメッセージ本文に `[skip ci]` という文字列を書かないこと。
GitHub はメッセージ全体を見るので、説明として書いただけでも
その push のワークフローが全部スキップされる。

## 配置やレイヤーを変えたとき

キーを増減・移動したら `mona2_layout.py` の `GEO` を
`boards/shields/mona2/mona2.dtsi` の `physical_layout0` に合わせて直す。
レイヤーを追加したら同ファイルの `LAYER_NAMES` に名前を足す。
`bindings` の数が合わない場合と名前の無いレイヤーがある場合は生成時に止まるので、
図だけ古いまま気づかず進むことはない。
