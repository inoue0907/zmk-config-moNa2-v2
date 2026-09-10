# -*- coding: utf-8 -*-
"""moNa2 v2 の物理配置とキーマップを読むための共通モジュール。

キー位置番号 0-41 の並びは boards/shields/mona2/mona2.dtsi の
physical_layout0 / default_transform と一致させている。配置を
いじったら GEO も直すこと。
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYMAP = os.path.join(ROOT, 'config', 'mona2.keymap')
DOCS = os.path.join(ROOT, 'docs')

# (x, y) を 1u 単位で。bindings の並び順そのまま = キー位置番号。
GEO = []
for _x in range(5):      GEO.append((_x, 0))          # 0-4    左手 上段
for _x in range(8, 13):  GEO.append((_x, 0))          # 5-9    右手 上段
for _x in range(5):      GEO.append((_x, 1))          # 10-14  左手 中段
GEO.append((7, 1))                                    # 15     右手 内側
for _x in range(8, 13):  GEO.append((_x, 1))          # 16-20  右手 中段
for _x in range(6):      GEO.append((_x, 2))          # 21-26  左手 下段
GEO.append((7, 2))                                    # 27     右手 内側
for _x in range(8, 13):  GEO.append((_x, 2))          # 28-32  右手 下段
for _x in range(6):      GEO.append((_x, 3))          # 33-38  左手 親指
GEO.append((7, 3))                                    # 39     右手 親指
GEO.append((8, 3))                                    # 40     右手 親指
GEO.append((12, 3))                                   # 41     右手 端
assert len(GEO) == 42, len(GEO)

COLS = max(x for x, _ in GEO) + 1   # 13
ROWS = max(y for _, y in GEO) + 1   # 4

LAYER_NAMES = {
    'default_layer': (0, u'ベース'),
    'layer_1':       (1, u'数字・マウス'),
    'layer_2':       (2, u'記号・Fキー'),
    'layer_3':       (3, u'ナビ・選択'),
    'layer_4':       (4, u'Bluetooth'),
    'MOUSE':         (5, u'オートマウス'),
    'SCROLL':        (6, u'スクロール'),
    'numpad_layer':  (7, u'テンキー'),
}


def parse_layers(path=KEYMAP):
    """keymap から [{'id', 'node', 'ja', 'raw': [42 個の binding]}] を返す。"""
    src = io.open(path, encoding='utf-8').read()
    km = src[src.index('keymap {'):]
    found = re.findall(
        r'(\w+)\s*\{\s*bindings\s*=\s*<(.*?)>;\s*sensor-bindings\s*=\s*<(.*?)>;',
        km, re.S)
    layers = []
    for node, body, _sensor in found:
        body = re.sub(r'//[^\n]*', '', body)
        toks = [' '.join(t.split()) for t in re.findall(r'&[^&>]+', body)]
        if len(toks) != len(GEO):
            raise SystemExit('%s: bindings が %d 個（%d 個のはず）'
                             % (node, len(toks), len(GEO)))
        if node not in LAYER_NAMES:
            raise SystemExit('%s: LAYER_NAMES に名前を追加してください' % node)
        idx, ja = LAYER_NAMES[node]
        layers.append({'id': idx, 'node': node, 'ja': ja, 'raw': toks})
    layers.sort(key=lambda L: L['id'])
    return layers


# ---------------------------------------------------------------- 表示ラベル
# "\n" は意図した改行。キー内では自動折り返ししないので、
# 長いものはここで切る場所を決めておく。
KC = {
 'N0': '0', 'N1': '1', 'N2': '2', 'N3': '3', 'N4': '4',
 'N5': '5', 'N6': '6', 'N7': '7', 'N8': '8', 'N9': '9',
 'COMMA': ',', 'DOT': '.', 'MINUS': '-', 'SEMI': ';', 'COLON': ':',
 'UNDERSCORE': '_', 'FSLH': '/', 'SLASH': '/', 'ASTRK': '*', 'PLUS': '+',
 'EQUAL': '=', 'HASH': '#', 'EXCLAMATION': '!', 'SINGLE_QUOTE': "'",
 'DOUBLE_QUOTES': '"', 'LEFT_PARENTHESIS': '(', 'RIGHT_PARENTHESIS': ')',
 'LEFT_BRACE': '{', 'RIGHT_BRACE': '}', 'LEFT_BRACKET': '[',
 'RIGHT_BRACKET': ']', 'CARET': '^', 'AMPERSAND': '&', 'QUESTION': '?',
 'DOLLAR': '$', 'PERCENT': '%', 'BACKSLASH': '\\', 'GRAVE': '`',
 'TILDE': '~', 'AT': '@', 'PIPE': '|',
 'BSPC': 'BS', 'DEL': 'Del', 'ESC': 'Esc', 'TAB': 'Tab',
 'ENTER': 'Enter', 'RET': 'Enter', 'SPACE': 'Space',
 'LANGUAGE_1': u'かな', 'LANG1': u'かな',
 'LANGUAGE_2': u'英数', 'LANG2': u'英数',
 'LEFT_SHIFT': 'Shift', 'LSHFT': 'Shift', 'LCTRL': 'Ctrl',
 'LEFT_CONTROL': 'Ctrl', 'LCTL': 'Ctrl',
 'LEFT_WIN': 'Win', 'LGUI': 'Win', 'LEFT_ALT': 'Alt', 'LALT': 'Alt',
 'HOME': 'Home', 'END': 'End', 'PG_UP': 'PgUp', 'PAGE_UP': 'PgUp',
 'PG_DN': 'PgDn', 'PAGE_DOWN': 'PgDn',
 'LEFT': u'←', 'RIGHT': u'→', 'UP': u'↑', 'DOWN': u'↓',
 'LEFT_ARROW': u'←', 'RIGHT_ARROW': u'→',
 'UP_ARROW': u'↑', 'DOWN_ARROW': u'↓',
 'PSCRN': 'PrtSc', 'PRINTSCREEN': 'PrtSc',
 'C_PLAY_PAUSE': u'再生\n停止', 'C_PREV': u'前へ', 'C_NEXT': u'次へ',
 'C_RW': u'巻戻し', 'C_FF': u'早送り', 'C_MUTE': u'ミュート',
}
MODF = {'LC': 'Ctrl', 'LS': 'Shift', 'LA': 'Alt', 'LG': 'Win',
        'RC': 'Ctrl', 'RS': 'Shift', 'RA': 'Alt', 'RG': 'Win'}
MB = {'MB1': u'左\nクリック', 'MB2': u'右\nクリック', 'MB3': u'中\nクリック',
      'MB4': u'戻る', 'MB5': u'進む'}


def modsplit(code):
    """LC(LS(TAB)) -> ('Ctrl+Shift', 'TAB')"""
    mods = []
    while True:
        m = re.match(r'^(L[CSAG]|R[CSAG])\((.*)\)$', code.strip())
        if not m:
            break
        mods.append(MODF[m.group(1)])
        code = m.group(2)
    return '+'.join(mods), code.strip()


def keycode(code):
    if code in KC:
        return KC[code]
    if re.match(r'^F\d+$', code) or re.match(r'^[A-Z]$', code):
        return code
    return code.replace('_', ' ').title()


def label(binding):
    """binding 1 個 -> (main, sub, category)。main は "\\n" を含みうる。

    sub は「長押し側」や修飾キーを載せる小さい上段。
    category は色分け用: base / mod / layer / mouse / macro / system / trans
    """
    t = binding.strip().split()
    op, a = t[0], t[1:]
    if op == '&trans':
        return (u'▽', '', 'trans')
    if op == '&none':
        return (u'✕', '', 'trans')
    if op == '&kp':
        mods, base = modsplit(a[0])
        cat = 'base'
        if mods or base in ('LEFT_SHIFT', 'LCTRL', 'LEFT_WIN', 'LEFT_ALT'):
            cat = 'mod'
        if base.startswith('C_'):
            cat = 'mouse'
        return (keycode(base), mods, cat)
    if op == '&mt':
        return (keycode(a[1]), keycode(a[0]), 'mod')
    if op == '&lt':
        return (keycode(a[1]), 'L' + a[0], 'layer')
    if op == '&mo':
        return ('L' + a[0], u'長押し', 'layer')
    if op == '&to':
        return (u'→L' + a[0], u'固定', 'layer')
    if op == '&tog':
        return ('L' + a[0], u'トグル', 'layer')
    if op == '&mkp':
        return (MB.get(a[0], a[0]), '', 'mouse')
    if op == '&bt':
        return ({'BT_CLR': u'BT\n削除',
                 'BT_CLR_ALL': u'BT\n全削除'}.get(a[0], a[0]), '', 'system')
    if op == '&sys_reset':
        return (u'リセット', '', 'system')
    if op == '&bootloader':
        return (u'ブート\nローダ', '', 'system')
    if op == '&tog_ls':
        return (u'JIS/US\n切替', '', 'system')
    if op == '&bt_sel_us':
        return ('BT' + a[0], 'US', 'system')
    if op == '&bt_sel_jis':
        return ('BT' + a[0], 'JIS', 'system')
    if op == '&ctrl_alt_tab':
        return ('Tab', 'Ctrl+Alt', 'macro')
    if op == '&select_line':
        return (u'行選択', '', 'macro')
    if op == '&shift_left_drag':
        return (u'ドラッグ', 'Shift', 'macro')
    if op in ('&pair_shift', '&pair_dance'):
        return ('()[]{}', keycode(a[0]) if a else '', 'macro')
    # 未知のマクロ: ノード名をそのまま出す（気づけるように）
    return (op.lstrip('&'), ' '.join(a), 'macro')


def write(path, text):
    io.open(path, 'w', encoding='utf-8', newline='\n').write(text)
    print('wrote %s (%d bytes)' % (os.path.relpath(path, ROOT), len(text)))
