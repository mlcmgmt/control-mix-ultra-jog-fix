# Validation

All captures were made over USB MIDI with Python `mido`, unless noted. The
controller was power-cycled between firmware images.

## Stock baseline

- Left plain ring, 1 rev / 6 s: **0 packets**.
- Right plain ring, 1 rev / 6 s: **0 packets**.
- Shift + left ring: steady `B4 09` packets.
- Left top: steady `B1 0A` packets.
- Right top: steady `B2 0A` packets.

This isolated the problem to the plain-ring paths rather than the sensors, app
mapping, or USB/BLE transport.

## Jog patch

### Crawl speed

- Left ring, 1 rev / 6 s, 15 s: **237 packets**, all `B1 09 7F`.
- Right ring, 1 rev / 6 s, 7 s: **87 packets**, all `B2 09 01`.

### Very slow and idle

| Phase | Result |
|---|---|
| Hands off, 6 s | 0 packets |
| Left ring, 1 rev / 12 s | 152 x `B1 09 01` |
| Tiny back-and-forth nudges | 9 x `B1 09 01` |

No drift when idle; no missed edges at the slowest tested speed.

### Other controls

| Phase | Result |
|---|---|
| Left ring slow clockwise | `B1 09 01` |
| Left ring slow counter-clockwise | `B1 09 7F` |
| Right ring slow | `B2 09 01` |
| Left top, slow | `B1 0A 01` |
| Right top, slow | `B2 0A 01` |
| Shift + left ring, slow | `B4 09 01` |
| Left ring at normal speed | about 49 packets/s, no duplicate bursts |

### BLE-MIDI

Captured from the BLE-MIDI GATT characteristic
(`7772e5db-3868-4112-a1a9-f2669d106bf3`) with `bleak`.

- Left plain ring, 1 rev / 6 s, 12 s: **228 notifications**, all `B1 09 01`,
  about 19/s.
- The first notification was a stray note-on; every ring notification carried
  the same CC9 stream.

### Vibration

With the patched firmware and the USB MIDI listener open, the controller was
shaken vigorously for 15 seconds without intentional rotation. **0 MIDI
packets** were emitted. The device stayed enumerated, so the zero is real. The
unconditional send does not turn vibration into phantom pitch bend.

## Pitch fader patch

- Pitch faders are 14-bit CC8 (MSB) plus CC40 (LSB).
- Stock dead zone at entries 4/5: `0x80`.
- Patched at `0x40`.
- At a 6% pitch scale, slow movement changed from about **0.3 BPM** steps to
  about **0.1 BPM** steps.
- Real-performance feedback: pitch and jog feel good; keep the `0x40` value.

## Dead-zone calibration

- The other 12 entries changed from `0x80` to `0x60`.
- Crossfader, master, channel volumes, filters, and EQs felt precise.
- The center-notched controls do not drift at rest.
- The biggest subjective improvements remain the jog rings and pitch faders;
  this group is a smaller polish change.

## WebUSB flow

Validated end to end in Edge:

- Read the full 256 KB image.
- Download a stock backup.
- Apply the selected patch groups.
- Write and reboot.
- Re-enter DFU, read back, and verify the hash.

The site now supports all eight combinations of jog, pitch, and dead-zone
groups. The pure patch logic was verified against the stock image for every
combination; the three main builds (jog, jog + pitch, all three) were also
flashed and tested on hardware.

## Failed or abandoned tests

- **Patch 1:** dead-zone entry 0 `0x80 -> 0x00` had no effect on the ring.
- **Layer B firmware:** deck 3 play worked, deck 4 did not, and the controller
  became unresponsive after some button presses. Reverted.
- **Master offset:** a +8 CC-step master offset caused a no-boot state. Recovered
  via DFU and the stock image; discarded.

## Caveats

- Validated on one unit over USB MIDI and BLE-MIDI.
- Real-app feel was tested by the owner, not measured in a lab.
- The snapshot is tied to the stock image hash listed in the README.
