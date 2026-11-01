# Reverse-engineering notes

Addresses are Thumb code at flash base `0x08000000`. File offset = address -
`0x08000000`.

## Device and image

- Hercules DJControl Mix Ultra, USB `06F8:B131`.
- STM32F4, 256 KB flash at `0x08000000`; sectors `4x16K + 64K + 128K`.
- Stock SHA-256:
  `7aa5453680753f725d21b8c20ad3bc32187dcfc17ab27632e9fd48de6295edd8`.
- Test unit option bytes: RDP `0xAA` (Level 0). The ROM DFU bootloader is
  reachable at `0483:DF11` by holding **Neural Mix** while powering on.

## Jog encoder path

The two ring encoders are read through EXTI on GPIOB pins 4-7:

| Encoder | GPIO | EXTI pair | Step counter | CC |
|---|---|---|---|---|
| Left ring | PB7 / PB6 | 7 / 6 | `0x200000F4` | `B1 09` (shift: `B4 09`) |
| Right ring | PB5 / PB4 | 5 / 4 | `0x200000F5` | `B2 09` (shift: `B5 09`) |

Key functions:

| Address | Role |
|---|---|
| `0x08000D78` | GPIO/EXTI init for PB4-7; seeds edge timestamps |
| `0x0800320C` | EXTI wrapper; clears pending and calls the decoder |
| `0x08002F40` | quadrature decoder ISR; updates step counters and timestamps |
| `0x08006048` | jog poll/translate handler, called from the task loop |
| `0x08001C4C` | MIDI CC packet builder |
| `0x08001D7C` | MIDI note packet builder |

The ISR writes the current tick to `state+0x2B0`/`state+0x2B4`
(`0x200004F8`/`0x200004FC`). The translate handler is called with
`r0 = state + 0xD0` (`0x20000318`); its fields `+0x1D8..+0x204` map to
`0x200004F0..0x2000051C`.

For each channel (`r5=0` left ring/top, `r5=1` right ring/top):

1. Checks the pending step in `0x200000F4`/`0x200000F5`.
2. Reads the step delta (`+1` or `-1`).
3. Applies the time gate.
4. Builds the relative CC.

### The ring gate

Left channel:

```asm
0x08006080  ldr.w r1, [r4, #0x1d8]   ; last edge tick
0x08006084  ldr.w r0, [r4, #0x1e0]   ; current edge tick
0x08006088  subs  r1, r0, r1         ; dt
0x0800608a  cmp   r1, #2
0x0800608c  bls   0x08006094         ; send only if dt <= 2
0x0800608e  str.w r0, [r4, #0x1d8]   ; update last tick
0x08006092  b     0x0800615c         ; drop packet
0x08006094  ldr.w r0, [r4, #0x1e0]   ; send path
```

Right channel uses `+0x1DC`/`+0x1E4` and the gate at `0x080060B0`/`0x080060B2`
with target `0x080060BA`.

The shift/left-top bypass is at `0x08006072` (`+0x1F8`); the right-top bypass
is at `0x0800606A` (`+0x204`). This is why shift+ring and the tops work at crawl
speed.

The patch changes each `bls` (`02 D9`) to `b` (`02 E0`): the send block still
updates the timestamp, so state remains consistent.

## Absolute controls and pitch faders

The absolute scanner at `0x08005D28` handles 14 controls. The CC map table at
`0x0800B700` and the dead-zone table at `0x0800B756` define them.

A djay Pro mapping export confirmed the physical assignments:

| Index | CC | Control |
|---|---|---|
| 0 | `B0 00` | crossfader |
| 1 | `B0 03` | master |
| 2 | `B1 00` | channel volume 1 |
| 3 | `B2 00` | channel volume 2 |
| 4 | `B1 08` | left pitch |
| 5 | `B2 08` | right pitch |
| 6/7 | `B1/B2 01` | filter 1/2 |
| 8/9 | `B1/B2 02` | low EQ 1/2 |
| 10/11 | `B1/B2 03` | mid EQ 1/2 |
| 12/13 | `B1/B2 04` | high EQ 1/2 |

The pitch faders send 14-bit CC8 (MSB) plus CC40 (LSB). All absolute controls
use the same 14-byte dead-zone table; entries 4/5 are pitch.

Patch groups:

- Pitch: entries 4/5 `0x80 -> 0x40`.
- Dead-zone calibration: the other 12 entries `0x80 -> 0x60`.

## MIDI map from the djay export

The export had 324 controls. Channel conventions:

- Note messages: `midiChannel` is 0-based; status = `0x90 + channel`.
- CC messages: `midiChannel` is 0-based; status = `0xB0 + channel`.
- Type 1 = note, type 3 = CC.

Key mappings:

- Shift deck 1: note 4 ch2 (`0x92 04`); deck 2: note 4 ch1 (`0x91 04`).
- Deck 1 basics: notes 7/6/5 on ch1 (`0x91`); shifted on ch4 (`0x94`).
- Deck 2 basics: notes 7/6/5 on ch2 (`0x92`); shifted on ch5 (`0x95`).
- Pads: deck 1 note ch6 (`0x96`), deck 2 note ch7 (`0x97`), notes 0-127.
- Pickup flags: high EQ and gain only.
- Jog sensitivity/acceleration values: pitch bend 55/48, scratch 55/55,
  jog seek 63 or 55.

The mapping export itself and the 4-deck drafts are kept local, not in this
repository.

## LED path

- Button/LED scanner `0x080095A4` sends a 10-byte packet over SPI3
  (handle `0x20000610`) from `0x2000009B`.
- `0x08009C5A` copies 4 bytes from deck state `+0x1D1..+0x1D4` into
  `0x2000009B..0x2000009E`.
- Four bytes per deck, one per pad, consistent with brightness rather than RGB.
- Init/test `0x08009A38` sets the first 4 bytes to `0xFF`.
- The battery indicator is separate and multi-color. The pads are
  single-channel blue.
- MIDI note messages do not directly light the pads; the LED path is separate.

## Service mode

Hold jog + Neural Mix for about 5 seconds. Top-row pads send notes 0-7 on
channel 6 (`0x96`), bottom row on channel 7 (`0x97`). The selected pad latches
a touch sensitivity level. This was tested; it does not change the ring gate.

## Failed experiments

- **Patch 1:** dead-zone table entry 0 `0x80 -> 0x00`. No effect on the ring;
  it is the absolute scanner path, not the jog.
- **Layer B firmware:** hooked the USB/BLE MIDI send functions and remapped
  deck channels. Deck 3 play worked, but deck 4 and other controls did not, and
  the controller became unresponsive after some button presses. Reverted.
- **Master offset:** a +8 CC-step offset on the master builder caused the
  controller not to boot. Recovered via DFU and stock image. Discarded.
- **4-deck djay mapping:** djay uses `condition` / `modifier` fields for native
  multi-deck mappings. A Mix Ultra modifier test file was created, but the
  work is parked.

## USB/BLE merge

The Mix Ultra is a USB device, not a USB host. Merging an external USB MIDI
controller into the Mix Ultra and forwarding it over BLE would require USB host
mode, VBUS/OTG support, a USB host MIDI stack, and a routing engine. The current
firmware does not provide this, and the port is likely device-only.

## Tooling used

- `dfu-util` 0.11 for dump/flash/revert.
- Radare2 + Capstone for disassembly and BL-target scanning.
- Ghidra for broad decompilation.
- Python `mido` for MIDI captures.
- WebUSB/Web Bluetooth in the companion site.
