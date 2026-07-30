import argparse
import asyncio
import os
import sys
import textwrap
import tomllib

from bleak import BleakClient, BleakScanner
from escpos.printer import Dummy

# --- Config ------------------------------------------------------------------

SCAN_TIMEOUT = 15.0      # seconds to look for the printer while advertising
CONNECT_RETRIES = 3
CHUNK_DELAY = 0.02       # pause between BLE writes so the printer keeps up
DRAIN_SECONDS = 2        # let the printer finish before we disconnect


def app_dir():
    """Directory of the running script/binary (works under PyInstaller too)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def load_config():
    path = os.path.join(app_dir(), "config.toml")
    with open(path, "rb") as f:
        return tomllib.load(f)["printer"]


# --- Receipt building (ESC/POS bytes) ----------------------------------------


def build_receipt(profile, note, qr=None, image=None):
    """Render the note to a raw ESC/POS byte stream using a captured printer."""
    d = Dummy(profile=profile)
    width = d.profile.get_columns("a")
    note = textwrap.fill(note, width=width, break_long_words=False, break_on_hyphens=False)

    d.ln(2)
    d.set_with_default(align="center", font="a")
    if qr:
        d.qr(qr, size=8)
    if image:
        d.image(image)
    d.textln(note)
    d.textln("-" * width)
    d.cut()
    return d.output


# --- BLE transport -----------------------------------------------------------


async def find_printer(name):
    """Return the BLE device whose advertised name starts with `name`."""
    def match(dev, adv):
        advertised = dev.name or adv.local_name or ""
        return advertised.upper().startswith(name.upper())

    return await BleakScanner.find_device_by_filter(match, timeout=SCAN_TIMEOUT)


async def send(device, write_char, data):
    async with BleakClient(device) as client:
        chunk = max(20, client.mtu_size - 3)
        for i in range(0, len(data), chunk):
            await client.write_gatt_char(write_char, data[i:i + chunk], response=False)
            await asyncio.sleep(CHUNK_DELAY)
        await asyncio.sleep(DRAIN_SECONDS)


async def print_bytes(name, write_char, data):
    print(f"scanning for '{name}'...")
    device = await find_printer(name)
    if device is None:
        raise RuntimeError(f"printer '{name}' not found (is it on and in range?)")

    for attempt in range(1, CONNECT_RETRIES + 1):
        try:
            print(f"connecting ({attempt}/{CONNECT_RETRIES})...")
            await send(device, write_char, data)
            print("printed")
            return
        except Exception as e:
            print(f"  attempt failed: {e}")
            await asyncio.sleep(1)
    raise RuntimeError(f"could not print after {CONNECT_RETRIES} attempts")


# --- Entry point -------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("note", type=str, help="Note message")
    parser.add_argument("--qr", type=str, help="QR Code")
    parser.add_argument("--image", type=str, help="Image source")
    args = parser.parse_args()

    cfg = load_config()
    data = build_receipt(cfg["profile"], args.note, qr=args.qr, image=args.image)

    try:
        asyncio.run(print_bytes(cfg["name"], cfg["write_char"], data))
    except RuntimeError as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
