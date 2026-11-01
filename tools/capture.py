#!/usr/bin/env python3
"""Capture and summarize MIDI from a DJControl Mix Ultra.

Usage:
    python capture.py --seconds 15
    python capture.py --seconds 15 --port "DJControl Mix Ultra 1"

Rotate the control you want to test while the capture runs. The summary prints
packet counts by raw MIDI hex and the observed rate.
"""

import argparse
import collections
import time

import mido


def find_port(explicit: str | None) -> str:
    if explicit:
        return explicit
    names = mido.get_input_names()
    for name in names:
        if "DJControl Mix Ultra" in name:
            return name
    raise SystemExit(f"DJControl Mix Ultra not found. Inputs: {names}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seconds", type=float, default=15.0)
    ap.add_argument("--port", default=None)
    args = ap.parse_args()

    port_name = find_port(args.port)
    print(f"input: {port_name}")
    print(f"capturing for {args.seconds:.1f}s ...")

    inp = mido.open_input(port_name)
    counts = collections.Counter()
    rows = []
    t0 = time.time()

    while True:
        now = time.time() - t0
        if now >= args.seconds:
            break
        for msg in inp.iter_pending():
            counts[msg.hex()] += 1
            rows.append((now, msg.hex()))
        time.sleep(0.0005)

    print(f"\n{len(rows)} packets in {args.seconds:.1f}s")
    for raw, count in counts.most_common(20):
        print(f"  {count:5d}  {raw}")

    if rows:
        dt = max(0.001, rows[-1][0] - rows[0][0])
        print(f"rate: {len(rows) / dt:.1f} packets/s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
