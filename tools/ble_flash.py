# /// script
# requires-python = ">=3.10"
# dependencies = ["bleak>=0.22"]
# ///
# -*- coding: utf-8 -*-
"""PC の内蔵 Bluetooth から moNa2 のファームを無線で焼く。

    uv run tools/ble_flash.py --side r          # 右手(親機)を更新
    uv run tools/ble_flash.py --side l          # 左手を更新
    uv run tools/ble_flash.py --zip path/to.zip # 手元の DFU ZIP を使う

先にキーボード側で &blueboot を押して DFU モードに入れておくこと。
スマホの nRF DFU アプリは 20 バイトパケット固定だが、こちらは
OTAFIX の高 MTU (最大 244 バイト) を使えるので大幅に速い。

DFU プロトコルの実装は recrof/nrf_dfu_py の dfu_lib.py を使う。
あちらはライセンス表記が無いので同梱せず、コミット固定で実行時に取得して
~/.cache/zmk-ble-flash/ に置く。取得物は SHA-256 で検証する。
"""
import argparse
import asyncio
import hashlib
import io
import logging
import platform
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

# recrof/nrf_dfu_py をコミットで固定する。更新するときは SHA と一緒に
# DFU_LIB_SHA256 も差し替える(取得後に sha256sum で出せる)。
NRF_DFU_PY_COMMIT = "409e4b75d55c8d75859022217dfba0db33730f16"
DFU_LIB_SHA256 = "90da46edd370ca9a893aa1ee18585fd814b50e088af4877772351f3eaf34b8a3"
DFU_LIB_URL = (
    "https://raw.githubusercontent.com/recrof/nrf_dfu_py/"
    f"{NRF_DFU_PY_COMMIT}/dfu_lib.py"
)

DEFAULT_REPO = "inoue0907/zmk-config-moNa2-v2"
DEFAULT_TAG = "dfu-latest"

# OTAFIX は基板ごとの名前で広告する。標準の Adafruit ブートローダーは AdaDFU。
BOOTLOADER_NAMES = ["XIAO_DFU", "AdaDFU"]

CACHE_DIR = Path.home() / ".cache" / "zmk-ble-flash"


def fetch(url: str, desc: str) -> bytes:
    print(f"取得中: {desc}")
    req = urllib.request.Request(url, headers={"User-Agent": "zmk-ble-flash"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def load_dfu_lib():
    """dfu_lib.py をキャッシュに用意して import できるようにする。"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"dfu_lib_{NRF_DFU_PY_COMMIT[:12]}.py"

    if not path.exists():
        data = fetch(DFU_LIB_URL, f"dfu_lib.py ({NRF_DFU_PY_COMMIT[:7]})")
        digest = hashlib.sha256(data).hexdigest()
        if digest != DFU_LIB_SHA256:
            sys.exit(
                "dfu_lib.py のハッシュが一致しません。中断します。\n"
                f"  期待: {DFU_LIB_SHA256}\n  実際: {digest}"
            )
        path.write_bytes(data)
    else:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != DFU_LIB_SHA256:
            path.unlink()
            sys.exit("キャッシュが壊れていたので削除した。もう一度実行してほしい。")

    sys.path.insert(0, str(CACHE_DIR))
    sys.modules.pop("dfu_lib", None)
    import importlib.util

    spec = importlib.util.spec_from_file_location("dfu_lib", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["dfu_lib"] = module
    spec.loader.exec_module(module)
    return module


def resolve_zip(args) -> Path:
    """--zip か --side からローカルの DFU ZIP パスを返す。"""
    if args.zip:
        p = Path(args.zip).expanduser().resolve()
        if not p.is_file():
            sys.exit(f"ファイルが無い: {p}")
        return p

    name = f"mona2_{args.side}-blueboot.zip"
    url = f"https://github.com/{args.repo}/releases/download/{args.tag}/{name}"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out = CACHE_DIR / name
    data = fetch(url, f"{name} ({args.tag})")
    out.write_bytes(data)

    # Legacy DFU パッケージとして最低限成立しているか見ておく
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if "manifest.json" not in z.namelist():
            sys.exit(f"DFU パッケージに manifest.json が無い: {out}")
    return out


async def find_bootloader(dfu_lib, names, timeout, wait):
    """DFU モードで広告している基板を探す。"""
    from bleak import BleakScanner

    wanted = {n.upper() for n in names}
    svc = dfu_lib.DFU_SERVICE_UUID.lower()

    while True:
        found = await BleakScanner.discover(timeout=timeout, return_adv=True)
        others = []
        for _, (dev, adv) in found.items():
            adv_name = adv.local_name or dev.name or ""
            uuids = [u.lower() for u in (adv.service_uuids or [])]
            if adv_name.upper() in wanted or svc in uuids:
                return dev, adv_name
            if adv_name:
                others.append(f"{adv_name} ({dev.address})")

        print(f"見つからない。探した名前: {', '.join(names)}")
        if others:
            print("  近くにあったもの: " + ", ".join(sorted(set(others))[:10]))
        if not wait:
            sys.exit(
                "DFU モードの基板が見つからなかった。\n"
                "キーボードで &blueboot を押して DFU モードに入れてから実行してほしい。\n"
                "  右手: layer_1 の pos 39 / 左手: layer_3 の pos 37"
            )
        print("再スキャンする...")


async def run(args):
    dfu_lib = load_dfu_lib()
    zip_path = resolve_zip(args)

    high_mtu = not args.no_high_mtu
    if platform.system() == "Darwin" and high_mtu:
        print("macOS は高 MTU 非対応なので無効にする")
        high_mtu = False

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        datefmt="%H:%M:%S")
    logging.getLogger("bleak").setLevel(logging.ERROR)

    state = {"last": -1, "t0": None}

    def progress(pct):
        if pct != state["last"]:
            state["last"] = pct
            sys.stdout.write(f"\r転送中: {pct}%")
            sys.stdout.flush()
            if pct == 100:
                sys.stdout.write("\n")

    dfu = dfu_lib.NordicLegacyDFU(
        str(zip_path), args.prn, args.delay,
        high_mtu=high_mtu, progress_callback=progress,
    )
    dfu.parse_zip()

    names = [args.device] if args.device else BOOTLOADER_NAMES
    device, adv_name = await find_bootloader(dfu_lib, names, args.scan_timeout, args.wait)

    print()
    print("=" * 56)
    print(f"  書き込み先 : {adv_name or '(名前なし)'}  {device.address}")
    print(f"  ファーム   : {zip_path.name}  ({len(dfu.bin_data):,} bytes)")
    print(f"  高 MTU     : {'ON' if high_mtu else 'OFF'}   PRN: {args.prn}")
    print("=" * 56)
    if not args.yes:
        if not sys.stdin.isatty():
            sys.exit("対話環境ではないので --yes が必要。")
        if input("続行する? [y/N] ").strip().lower() not in ("y", "yes"):
            sys.exit("中止した。")

    state["t0"] = time.monotonic()
    await dfu.perform_update(device, max_retries=args.retry)
    elapsed = time.monotonic() - state["t0"]

    size = len(dfu.bin_data)
    print(f"\n完了: {size:,} bytes / {elapsed:.1f} 秒 "
          f"= {size / 1024 / elapsed:.1f} KB/s")
    print("転送が途中で切れた場合、OTAFIX ならリセット 1 回で DFU 待機に戻る。")


def main():
    p = argparse.ArgumentParser(
        description="PC の内蔵 Bluetooth から moNa2 のファームを無線更新する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="先にキーボードで &blueboot を押して DFU モードに入れておくこと。",
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--side", choices=["l", "r"],
                     help="l=左手 / r=右手(親機)。リリースから DFU ZIP を取得する")
    src.add_argument("--zip", help="手元の DFU ZIP を使う")

    p.add_argument("--repo", default=DEFAULT_REPO, help=f"既定: {DEFAULT_REPO}")
    p.add_argument("--tag", default=DEFAULT_TAG, help=f"既定: {DEFAULT_TAG}")
    p.add_argument("--device", help="広告名か BLE アドレスを直接指定する")
    p.add_argument("--prn", type=int, default=30,
                   help="Packet Receipt Notification の間隔。0 で無効。既定: 30")
    p.add_argument("--delay", type=float, default=0.4,
                   help="Start/Size コマンド後の待ち秒数。既定: 0.4")
    p.add_argument("--retry", type=int, default=3, help="接続リトライ回数。既定: 3")
    p.add_argument("--scan-timeout", type=float, default=5.0,
                   help="1 回のスキャン秒数。既定: 5.0")
    p.add_argument("--wait", action="store_true",
                   help="見つかるまでスキャンを繰り返す")
    p.add_argument("--no-high-mtu", action="store_true",
                   help="高 MTU を使わない(転送が早々に失敗するときに試す)")
    p.add_argument("--yes", "-y", action="store_true", help="確認を省略する")

    args = p.parse_args()
    if args.no_high_mtu is False and args.prn > 60:
        print("警告: PRN が大きすぎると不安定になることがある")

    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        sys.exit("\n中断した。")


if __name__ == "__main__":
    main()
