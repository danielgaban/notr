# Notr

This is an python script to print notes to handle adhd easier

## Installation

- On MacOS `brew install libusb`. On windows go to [zadig](zadig.akeo.ie) and replace ur printer driver to libusbK. TIP: on that page u can get vendor/product id on USB ID boxes

## Usage

If not setup before, it will be prompted for setup your usb printer vendor and product ID, as long of printer profile name. You can find all availables profile (here)[https://python-escpos.readthedocs.io/en/latest/printer_profiles/available-profiles.html] 

The configuration will be saved, but if you need to reset the config just pass `--clear` as argument when running the program i.e. `notr-v1.0.0-windows-x64.exe --clear`

## Build

Compile with `pyinstaller --onefile --collect-data=escpos .\__main__.py`

