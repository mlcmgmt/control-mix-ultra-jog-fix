#!/usr/bin/env python3
"""Apply DJControl Mix Ultra jog, pitch, and dead-zone patches to a stock dump.

Default behavior is the jog-ring fix only, matching the original project.

Examples:
    python apply_patch.py firmware_original.bin firmware_patched.bin
    python apply_patch.py --pitch firmware_original.bin firmware_patched.bin
    python apply_patch.py --jog --pitch --deadzone firmware_original.bin out.bin
    python apply_patch.py --all firmware_original.bin out.bin

The script verifies the stock SHA-256 and every source byte. It refuses to
touch an unknown image unless --force is given.
"""

import argparse
import hashlib
import sys
from pathlib import Path

STOCK_SHA256 = "7aa5453680753f725d21b8c20ad3bc32187dcfc17ab27632e9fd48de6295edd8"
EXPECTED_SIZE = 0x40000

PATCH_GROUPS = {
    "jog": [
        (0x608D, 0xD9, 0xE0, "left ring gate"),
        (0x60B3, 0xD9, 0xE0, "right ring gate"),
    ],
    "pitch": [
        (0xB75A, 0x80, 0x40, "left pitch dead zone"),
        (0xB75B, 0x80, 0x40, "right pitch dead zone"),
    ],
    "deadzone": [
        (0xB756, 0x80, 0x60, "crossfader dead zone"),
        (0xB757, 0x80, 0x60, "master dead zone"),
        (0xB758, 0x80, 0x60, "channel volume 1 dead zone"),
        (0xB759, 0x80, 0x60, "channel volume 2 dead zone"),
        (0xB75C, 0x80, 0x60, "filter 1 dead zone"),
        (0xB75D, 0x80, 0x60, "filter 2 dead zone"),
        (0xB75E, 0x80, 0x60, "low EQ 1 dead zone"),
        (0xB75F, 0x80, 0x60, "low EQ 2 dead zone"),
        (0xB760, 0x80, 0x60, "mid EQ 1 dead zone"),
        (0xB761, 0x80, 0x60, "mid EQ 2 dead zone"),
        (0xB762, 0x80, 0x60, "high EQ 1 dead zone"),
        (0xB763, 0x80, 0x60, "high EQ 2 dead zone"),
    ],
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", nargs="?", default="firmware_original.bin")
    ap.add_argument("output", nargs="?", default="firmware_patched.bin")
    ap.add_argument("--jog", action="store_true", help="apply the jog-ring fix")
    ap.add_argument("--pitch", action="store_true", help="apply pitch dead-zone fix")
    ap.add_argument("--deadzone", action="store_true", help="apply the other 12 dead zones")
    ap.add_argument("--all", action="store_true", help="apply jog + pitch + deadzone")
    ap.add_argument("--force", action="store_true",
                    help="patch even if the stock hash is unknown")
    args = ap.parse_args()

    groups = []
    if args.all:
        groups = list(PATCH_GROUPS)
    else:
        if args.jog:
            groups.append("jog")
        if args.pitch:
            groups.append("pitch")
        if args.deadzone:
            groups.append("deadzone")
        if not groups:
            groups = ["jog"]  # backward-compatible default

    src = Path(args.source)
    dst = Path(args.output)
    if not src.is_file():
        print(f"error: {src} not found", file=sys.stderr)
        return 1

    data = bytearray(src.read_bytes())
    if len(data) != EXPECTED_SIZE:
        print(f"error: expected {EXPECTED_SIZE} bytes, got {len(data)}",
              file=sys.stderr)
        return 1

    digest = sha256(data)
    if digest != STOCK_SHA256:
        print(f"warning: stock SHA-256 is {digest}", file=sys.stderr)
        print(f"         expected          {STOCK_SHA256}", file=sys.stderr)
        if not args.force:
            print("refusing to patch an unknown firmware image "
                  "(use --force only after verifying the offsets)",
                  file=sys.stderr)
            return 2
        print("--force given; continuing", file=sys.stderr)

    for group in groups:
        for offset, old, _new, label in PATCH_GROUPS[group]:
            if data[offset] != old:
                print(f"error: {group}/{label} byte at 0x{offset:06X} is "
                      f"0x{data[offset]:02X}, expected 0x{old:02X}",
                      file=sys.stderr)
                return 1

    applied = 0
    for group in groups:
        for offset, _old, new, _label in PATCH_GROUPS[group]:
            data[offset] = new
            applied += 1

    dst.write_bytes(data)
    print(f"source : {src}  ({digest})")
    print(f"output : {dst}  ({sha256(data)})")
    print(f"groups : {', '.join(groups)}")
    for group in groups:
        for offset, old, new, label in PATCH_GROUPS[group]:
            print(f"  {group:8s} {label:28s} file 0x{offset:06X} "
                  f"(flash 0x0800{offset & 0xFFFF:04X})  0x{old:02X} -> 0x{new:02X}")
    print(f"verify : {applied} bytes changed from the stock image")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
