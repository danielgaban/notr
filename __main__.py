import argparse
import os
import sys
import textwrap
import tomllib
from subprocess import run
from time import sleep

from escpos.printer import Serial

# --- Bluetooth lifecycle -----------------------------------------------------
# The printer is expected to be paired ONCE (manually or on first run). After
# that we only connect/disconnect, which is much faster and more reliable than
# re-pairing every run. We never unpair, so the OS keeps the bond.

PAIR_PIN = "0000"
CONNECT_RETRIES = 5
PORT_WAIT_SECONDS = 10


def _bt(*bargs, text=True):
    """Run a blueutil command and return the CompletedProcess."""
    return run(["blueutil", *bargs], capture_output=True, text=text)


def is_paired(mac):
    out = _bt("--paired").stdout or ""
    return mac.lower() in out.lower()


def is_connected(mac):
    return _bt("--is-connected", mac).stdout.strip() == "1"


def ensure_paired(mac):
    if is_paired(mac):
        return
    print("pairing (first time)...")
    result = _bt("--pair", mac, PAIR_PIN)
    if result.returncode != 0:
        print(f"Warning: pairing failed (exit {result.returncode}): {result.stderr.strip()}")


def connect(mac, port):
    """Connect to the printer and wait for its serial node to appear."""
    ensure_paired(mac)

    for attempt in range(1, CONNECT_RETRIES + 1):
        if not is_connected(mac):
            print(f"connecting... (attempt {attempt}/{CONNECT_RETRIES})")
            _bt("--connect", mac)
            sleep(1)

        if not is_connected(mac):
            continue

        # Wait for the rfcomm serial node to be created by the OS.
        print(f"waiting for {port}...")
        for _ in range(PORT_WAIT_SECONDS * 2):
            if os.path.exists(port):
                print("connected")
                return
            sleep(0.5)

        # Connected but no serial node -> bounce the connection and retry.
        print(f"{port} did not appear, reconnecting...")
        _bt("--disconnect", mac)
        sleep(1)

    raise RuntimeError(f"could not connect to {mac} after {CONNECT_RETRIES} attempts")


def disconnect(mac):
    print("disconnecting...")
    _bt("--disconnect", mac)


# --- Config ------------------------------------------------------------------


def app_dir():
    """Directory of the running script/binary (works under PyInstaller too)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def load_config():
    path = os.path.join(app_dir(), "config.toml")
    with open(path, "rb") as f:
        return tomllib.load(f)


# --- Printing ----------------------------------------------------------------


def open_printer(port):
    p = Serial(
        devfile=port,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=10,
        dsrdtr=True,
        xonxoff=False,
        profile="Sunmi-V2",
    )
    # Initialize printer (ESC @) as a connectivity check.
    p.device.write(b"\x1b\x40")
    p.device.flush()
    sleep(0.3)
    return p


def print_note(p, note, qr=None, image=None):
    width = p.profile.get_columns("a")
    note = textwrap.fill(note, width=width, break_long_words=False, break_on_hyphens=False)

    p.ln(2)
    p.set_with_default(align="center", font="a")
    if qr:
        p.qr(qr, size=8)
    if image:
        p.image(image)
    p.textln(note)
    p.textln("-" * width)
    p.cut()


# --- Entry point -------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("note", type=str, help="Note message")
    parser.add_argument("--qr", type=str, help="QR Code")
    parser.add_argument("--image", type=str, help="Image source")
    args = parser.parse_args()

    config = load_config()
    port, mac = config["printers"]["possible_devices"][0]

    connect(mac, port)
    p = None
    try:
        p = open_printer(port)
        print_note(p, args.note, qr=args.qr, image=args.image)
    finally:
        if p is not None:
            try:
                p.close()
            except Exception:
                pass
        disconnect(mac)


if __name__ == "__main__":
    main()
