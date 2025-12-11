from time import sleep
from datetime import datetime
from subprocess import run
from escpos.printer import Serial
import tomllib
import textwrap

note = textwrap.fill(
    input("Note: "), width=32, break_long_words=False, break_on_hyphens=False
)
if not note:
    print("no note, exiting")
    exit()

with open("config.toml", "rb") as f:
    config = tomllib.load(f)

_devices = config["printers"]["possible_devices"]
PORT = _devices[0][0]
MAC = _devices[0][1]

print("pairing...")
print(PORT)
print(MAC)
run(["blueutil", "--pair", MAC, "0000"], capture_output=True)
run(["blueutil", "--connect", MAC], capture_output=True)

while True:
    try:
        print("trying to connect")
        # Change the device name to yours
        p = Serial(
            devfile=PORT,
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=10,
            dsrdtr=True,  # Hardware flow control—often needed for Bluetooth stability
            xonxoff=False,  # Software flow control—usually off for printers
        )
    except Exception as err:
        print(err)
    else:
        break

sleep(1)
p.ln(3)
# p.set_with_default(align="center", font="a", double_height=True)
# p.qr("bitcoin:bc1qn5yn2mpmzcvky8kme7zep75rcr92t4kw02snj4?amount=0.0037779", size=8)
# p.image("/Users/danielgaban/Downloads/image.png")
# exit()
p.set_with_default(align="center", font="a")
p.ln(1)
p.textln(note)
p.ln(1)
lr = "-" * p.profile.get_columns("a")
p.textln(lr)
p.set(align="right", underline=0, bold=False, font="b")
p.text(datetime.now().strftime("%A %d %b"))
p.cut()
# p.close()

print("unpairing...")
run(["blueutil", "--unpair", MAC], capture_output=True)
run(["blueutil", "--disconnect", MAC], capture_output=True)
