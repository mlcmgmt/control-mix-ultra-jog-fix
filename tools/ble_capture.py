#!/usr/bin/env python3
"""Capture BLE-MIDI notifications from a DJControl Mix Ultra.

Usage:
    python ble_capture.py --seconds 12

Requires `bleak` (`pip install bleak`). Rotate the control you want to test
while the capture runs. The summary counts raw notification payloads.
"""

import argparse
import asyncio
import collections
import time

from bleak import BleakClient, BleakScanner

MIDI_SVC = "03b80e5a-ede8-4b33-a751-6ce34ec4c700"
MIDI_CHAR = "7772e5db-3868-4112-a1a9-f2669d106bf3"


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seconds", type=float, default=12.0)
    ap.add_argument("--scan", type=float, default=8.0)
    args = ap.parse_args()

    print(f"scanning {args.scan:.0f}s ...")
    found = await BleakScanner.discover(timeout=args.scan, return_adv=True)
    dev = None
    for addr, (d, adv) in found.items():
        uuids = [u.lower() for u in adv.service_uuids]
        if (d.name and "djcontrol" in d.name.lower()) or MIDI_SVC in uuids:
            print(f"found {addr} {d.name!r} rssi={adv.rssi}")
            if dev is None:
                dev = d
    if dev is None:
        print("no DJControl / BLE-MIDI device found")
        return 1

    packets = []
    async with BleakClient(dev, timeout=20) as client:
        target = None
        for service in client.services:
            for char in service.characteristics:
                if char.uuid.lower() == MIDI_CHAR:
                    target = char
        if target is None:
            print("BLE-MIDI characteristic not found")
            return 1

        def cb(_sender, data):
            packets.append((time.time(), data.hex()))

        await client.start_notify(target, cb)
        print(f"capturing {args.seconds:.1f}s ...")
        await asyncio.sleep(args.seconds)
        await client.stop_notify(target)

    counts = collections.Counter(h for _, h in packets)
    print(f"\n{len(packets)} notifications")
    for raw, count in counts.most_common(20):
        print(f"  {count:5d}  {raw}")

    ring = sum(1 for _, h in packets if "b109" in h)
    print(f"ring CC9 packets: {ring}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
