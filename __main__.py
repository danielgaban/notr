from time import sleep
from datetime import datetime
from subprocess import run
from escpos.exceptions import DeviceNotFoundError
from escpos.printer import Serial
import tomllib
import textwrap
import argparse

# args handling
parser = argparse.ArgumentParser()
parser.add_argument("note", type=str, help="Note message")
parser.add_argument("--qr", type=str, help="QR Code")
parser.add_argument("--image", type=str, help="Image source")
args = parser.parse_args()

args.note = textwrap.fill(
    args.note, width=32, break_long_words=False, break_on_hyphens=False
)

with open("config.toml", "rb") as f:
    config = tomllib.load(f)

_devices = config["printers"]["possible_devices"]
PORT = _devices[0][0]
MAC = _devices[0][1]

# TODO iterate over devices infinitely
while True:
    try:
        print("pairing...")
        print(PORT)
        print(MAC)
        run(["blueutil", "--pair", MAC, "0000"], capture_output=True)
        run(["blueutil", "--connect", MAC], capture_output=True)
        sleep(1)
        print("trying to connect")
        p = Serial(
            devfile=PORT,
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=10,
            dsrdtr=True,  # Hardware flow control—often needed for Bluetooth stability
            xonxoff=False,  # Software flow control—usually off for printers
            profile="Sunmi-V2",
        )
        if p.is_online():
            print("Connected")
            break
        print("unpairing...")
        run(["blueutil", "--disconnect", MAC], capture_output=True)
        run(["blueutil", "--unpair", MAC], capture_output=True)
        sleep(1)
    except (
        Exception
    ) as e:  # Broader catch, or specifically DeviceNotFoundError + serial exceptions
        print(f"Connection failed: {e}")
        sleep(2)  # Avoid hammering too fast")


# p.ln(3)
# p.set_with_default(align="center", font="a", double_height=True)
if args.qr:
    p.qr(args.qr, size=8)
if args.image:
    p.image(args.image)
p.set_with_default(align="center", font="a")
p.ln(2)
p.textln(args.note)
# p.ln(1)
lr = "-" * p.profile.get_columns("a")
p.textln(lr)
# p.set(align="right", underline=0, bold=False, font="b")
# p.text(datetime.now().strftime("%A %d %b"))
p.cut()
p.close()

print("unpairing...")
run(["blueutil", "--disconnect", MAC], capture_output=True)
sleep(1)
run(["blueutil", "--unpair", MAC], capture_output=True)
sleep(1)
