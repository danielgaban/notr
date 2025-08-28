# from escpos.constants import QR_ECLEVEL_H
import os
import textwrap
from escpos.printer import Usb
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

id_vendor = os.getenv("ID_VENDOR")
id_product = os.getenv("ID_PRODUCT")
if not id_vendor or not id_product:
    print("Please setup ID_VENDOR and/or ID_PRODUCT of your printer device on .env")
    exit(1)
printer_profile = os.getenv("PRINTER_PROFILE")
p = Usb(int(id_vendor, 16), int(id_product, 16), profile=printer_profile)

lr = "-" * p.profile.get_columns("a")

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
