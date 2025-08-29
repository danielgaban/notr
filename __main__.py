# from escpos.constants import QR_ECLEVEL_H
import textwrap
from configparser import ConfigParser, NoSectionError
from datetime import datetime
import argparse
from escpos.printer import Usb
from platformdirs import user_data_dir

DATA_PATH = user_data_dir("notr", "danielgaban", ensure_exists=True)
INI_PATH = DATA_PATH + "/cfg.ini"

parser = argparse.ArgumentParser()
parser.add_argument("--clear", action="store_true", help="Clear ini file")
args = parser.parse_args()

cfg = ConfigParser()

if args.clear:
    cfg.clear()
    with open(INI_PATH, "w") as configfile:
        cfg.write(configfile)

cfg.read(INI_PATH)
try:
    cfg.get("settings", "vendor_id")
    cfg.get("settings", "product_id")
    cfg.get("settings", "printer_profile")
except NoSectionError:
    print("Please setup ID_VENDOR and ID_PRODUCT")
    cfg.add_section("settings")
    cfg["settings"]["vendor_id"] = input("ID Vendor: ")
    try:
        int(cfg["settings"]["vendor_id"], 16)
    except ValueError:
        print("Invalid Vendor ID, exiting...")
        exit(1)
    cfg["settings"]["product_id"] = input("ID Product: ")
    try:
        int(cfg["settings"]["product_id"], 16)
    except ValueError:
        print("Invalid Product ID, exiting...")
        exit(1)
    cfg["settings"]["printer_profile"] = input("Printer profile code string: ")
with open(INI_PATH, "w") as configfile:
    cfg.write(configfile)

p = Usb(
    int(cfg["settings"]["vendor_id"], 16),
    int(cfg["settings"]["product_id"], 16),
    profile=cfg["settings"]["printer_profile"],
)

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
