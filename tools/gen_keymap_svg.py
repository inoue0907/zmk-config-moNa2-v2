# -*- coding: utf-8 -*-
"""README 冒頭に貼るキー位置図（番号だけ）を書き出す。

    python tools/gen_keymap_svg.py   ->  docs/keymap-positions.svg

Web フォントは読み込めない環境で表示されるので、フォントは
システム等幅のみ。背景色を自前で持たせて GitHub のライト/ダーク
どちらでも読めるようにしている。
"""
import os

from mona2_layout import COLS, DOCS, GEO, ROWS, write

U, K, PAD = 60, 54, 16
W = PAD * 2 + (COLS - 1) * U + K
H = PAD * 2 + (ROWS - 1) * U + K

BG, KEY, LINE, NUM = '#f7f5f2', '#ffffff', '#cfc8be', '#2a2d33'
FONT = 'ui-monospace,SFMono-Regular,Menlo,Consolas,monospace'


def main():
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
        'width="%d" height="%d" role="img" '
        'aria-label="moNa2 v2 key positions 0-%d">' % (W, H, W, H, len(GEO) - 1),
        '<rect width="%d" height="%d" rx="10" fill="%s"/>' % (W, H, BG),
        '<g stroke="%s" stroke-width="1.25" fill="%s">' % (LINE, KEY),
    ]
    for x, y in GEO:
        out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="6"/>'
                   % (PAD + x * U, PAD + y * U, K, K))
    out.append('</g>')
    out.append('<g fill="%s" font-family="%s" font-size="21" font-weight="600" '
               'text-anchor="middle">' % (NUM, FONT))
    for pos, (x, y) in enumerate(GEO):
        out.append('<text x="%d" y="%d" dominant-baseline="central">%d</text>'
                   % (PAD + x * U + K // 2, PAD + y * U + K // 2 + 1, pos))
    out.append('</g>')
    out.append('</svg>')

    if not os.path.isdir(DOCS):
        os.makedirs(DOCS)
    write(os.path.join(DOCS, 'keymap-positions.svg'), '\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
