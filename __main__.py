# from escpos.constants import QR_ECLEVEL_H
from escpos.printer import Usb
from datetime import datetime
import textwrap

XP_P503A = (
    0x0483,
    0x070B,
)
lr = "-" * 32

p = Usb(*XP_P503A, profile="Sunmi-V2")

if not p.is_online():
    print("not online")
    exit()

# get params
prior = int(input("Prior(1-3): "))
if not (0 < prior <= 3):
    print(prior)
    print("invalid prior, exiting")
    exit()
note = textwrap.fill(
    input("Note: "), width=32, break_long_words=False, break_on_hyphens=False
)
if not note:
    print("no note, exiting")
    exit()

# do print
p.ln(3)
p.set_with_default(align="center", font="a", double_height=True)
p.textln("!" * prior)
p.set_with_default(align="center", font="a")
p.ln(1)
p.textln(note)
p.ln(1)
p.textln(lr)
p.set(align="right", underline=0, bold=False, font="b")
p.text(datetime.now().strftime("%A %d %b"))
p.cut()

