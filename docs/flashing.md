# Dumping, flashing, and reverting

The DJControl Mix Ultra exposes the STM32 ROM DFU bootloader at
`0483:DF11` when you hold **Neural Mix** while powering on. The application
firmware is at `0x08000000`, 256 KB, and is fully readable/writable when RDP is
Level 0 (the stock unit tested here was Level 0).

## Requirements

- [`dfu-util`](https://dfu-util.sourceforge.net/) 0.10 or newer. Windows: use
  the prebuilt binary. macOS: `brew install dfu-util`. Linux: install it from
  your package manager.
- Python 3.8 or newer for `apply_patch.py`. A dump/flash-only workflow does not
  need Python.
- A USB-C data cable. Charge-only cables will not enumerate the controller.
- USB only. Bluetooth cannot flash the firmware.

Driver notes:

- Windows: if `dfu-util` reports it cannot open `0483:DF11`, bind the device to
  WinUSB with [Zadig](https://zadig.akeo.ie/), or run the shell as
  administrator.
- Linux: use `sudo` or a udev rule for the DFU device.

## 1. Enter DFU

1. Power the controller off.
2. Hold **Neural Mix**.
3. Power on while still holding it.
4. Release when the device enumerates.

Check:

```sh
dfu-util -l
# Found DFU: [0483:df11] ... "STM32  BOOTLOADER"
```

## 2. Dump the stock firmware

```sh
dfu-util -a 0 -s 0x08000000:0x40000 -U firmware_original.bin
```

The dump must be exactly **262144 bytes**:

```sh
sha256sum firmware_original.bin
# 7aa5453680753f725d21b8c20ad3bc32187dcfc17ab27632e9fd48de6295edd8
```

Keep this file. It is your revert image.

## 3. Build the patched image

```sh
# Default: jog only
python apply_patch.py firmware_original.bin firmware_patched.bin

# Or select groups:
python apply_patch.py --pitch firmware_original.bin out.bin
python apply_patch.py --jog --pitch --deadzone firmware_original.bin out.bin
python apply_patch.py --all firmware_original.bin out.bin
```

Expected output includes each applied group and the number of changed bytes.

## 4. Flash

```sh
dfu-util -a 0 -s 0x08000000:0x40000 -D firmware_patched.bin
```

`dfu-util` may print `Warning: Invalid DFU suffix signature` for a raw `.bin`.
That is normal; the download still succeeds.

## 5. Verify the write

```sh
dfu-util -a 0 -s 0x08000000:0x40000 -U firmware_readback.bin
sha256sum firmware_readback.bin
```

The readback should match `firmware_patched.bin`. The number of differences
from the stock dump depends on the selected groups:

- Jog: 2 bytes (`0x608D`, `0x60B3`)
- Pitch: 2 bytes (`0xB75A`, `0xB75B`)
- Dead-zone calibration: 12 bytes (`0xB756..0xB763` except `B75A/B`)

```sh
cmp -l firmware_original.bin firmware_readback.bin
```

For the default jog-only build, the two lines are:

```
24718 331 340     # offset 0x608D, 0xD9 -> 0xE0
24756 331 340     # offset 0x60B3, 0xD9 -> 0xE0
```

Power-cycle normally. The patched firmware is now running.

## 6. Revert

Enter DFU again, then:

```sh
dfu-util -a 0 -s 0x08000000:0x40000 -D firmware_original.bin
```

Read it back and compare the SHA-256 to the stock hash. Power-cycle.

## Notes

- The ROM bootloader lives in system memory and is not modified by this patch,
  so recovery does not depend on the application firmware booting.
- Do not interrupt power during a DFU write. The write is small (256 KB) and
  takes only a few seconds.
