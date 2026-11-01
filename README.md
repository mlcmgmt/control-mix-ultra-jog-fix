# Hercules DJControl Mix Ultra - Jog, Pitch, and Dead-Zone Fixes

Three independent firmware patches for the **Hercules DJControl Mix Ultra**:

1. **Jog ring behavior** - both outer rings send at crawl speed.
2. **Pitch fader stepping** - finer 14-bit pitch movement.
3. **Dead-zone calibration** - the other 12 absolute controls respond sooner.

Each group can be applied alone or in any combination. Tested on hardware on
2026-10-31 and 2026-11-01. Stock firmware is fully restorable through the STM32
ROM DFU bootloader; no case opening or SWD probe is required.

Companion web tool: https://cmu-mlcmgmt.pages.dev

---

## The problems

**Jog rings.** On stock firmware both outer rings emit relative MIDI CC9 only
when turned faster than a threshold. At roughly 1 revolution / 6 seconds they
emit zero packets. The top of the jog and shift+ring work at any speed.

**Pitch faders.** The faders are 14-bit (CC8 MSB plus CC40 LSB), but the stock
dead zone is larger than necessary. At a 6% pitch scale, slow movement produced
about 0.3 BPM steps. Lowering the dead zone gives about 0.1 BPM steps.

**Other controls.** The same dead-zone table covers crossfader, master, channel
volumes, filters, and EQs. Lowering it makes them slightly more responsive. The
center-notched controls do not drift at rest.

## The patches

All offsets are **file offsets**; add `0x08000000` for the flash address.

| Group | Offset | Stock | Patched | Effect |
|---|---|---|---|---|
| Jog left | `0x00608D` | `D9` | `E0` | `bls` -> `b`, send slow left ring edges |
| Jog right | `0x0060B3` | `D9` | `E0` | `bls` -> `b`, send slow right ring edges |
| Pitch left | `0x00B75A` | `80` | `40` | pitch dead zone 128 -> 64 |
| Pitch right | `0x00B75B` | `80` | `40` | pitch dead zone 128 -> 64 |
| Dead zones | `0x00B756`..`0x00B763` except `B75A/B` | `80` | `60` | 12 other absolute controls |

The jog bytes change the Thumb instruction `02 D9` (`bls`) to `02 E0` (`b`) in
the encoder handler at `0x08006048`. The dead-zone bytes are entries in the
14-byte table at `0x0800B756` used by the absolute scanner at `0x08005D28`.

## Compatibility

This patch set is specific to the stock image with:

```
SHA-256  7AA5453680753F725D21B8C20AD3BC32187DCFC17AB27632E9FD48DE6295EDD8
Size     262144 bytes (256 KB)
Device   Hercules DJControl Mix Ultra, USB 06F8:B131
MCU      STM32F4, 256 KB internal flash at 0x08000000
```

`apply_patch.py` refuses an image whose hash does not match. Do not apply it to a
different firmware revision.

## Requirements

Pick one path.

**Browser (recommended):** <https://cmu-mlcmgmt.pages.dev>

- Desktop Chrome or Edge. WebUSB is required; Firefox, Safari, and mobile
  browsers do not support it.
- A USB-C data cable. Charge-only cables will not enumerate the controller.
- No Python, terminal, or account. The backup and patching stay in the browser.
- Windows: if the browser cannot open the DFU device, bind `0483:DF11` to
  WinUSB with Zadig (one-time). Linux may need a udev rule.

**Command line**

- `dfu-util` 0.10 or newer to dump, flash, and revert.
- Python 3.8 or newer to run `apply_patch.py`.
- A terminal and a USB-C data cable.
- Windows: if `dfu-util` cannot open `0483:DF11`, bind it to WinUSB with Zadig
  or run the shell as administrator. macOS: `brew install dfu-util`. Linux:
  install `dfu-util` from your package manager and use `sudo` or a udev rule.

You must dump your own stock firmware. This repository does not distribute
firmware images, and the patch only applies to the stock hash above.

## Install

1. Dump your stock firmware first. See [`docs/flashing.md`](docs/flashing.md).
2. Verify the dump:

   ```sh
   sha256sum firmware_original.bin
   # 7aa5453680753f725d21b8c20ad3bc32187dcfc17ab27632e9fd48de6295edd8
   ```

3. Build the image with any combination:

   ```sh
   # default: jog only
   python apply_patch.py firmware_original.bin firmware_patched.bin

   # individual groups
   python apply_patch.py --pitch firmware_original.bin out.bin
   python apply_patch.py --deadzone firmware_original.bin out.bin

   # any combination
   python apply_patch.py --jog --pitch firmware_original.bin out.bin
   python apply_patch.py --jog --pitch --deadzone firmware_original.bin out.bin

   # all three
   python apply_patch.py --all firmware_original.bin out.bin
   ```

4. Enter DFU: **power off, hold Neural Mix, power on.**
5. Flash:

   ```sh
   dfu-util -a 0 -s 0x08000000:0x40000 -D out.bin
   ```

6. Read it back and compare:

   ```sh
   dfu-util -a 0 -s 0x08000000:0x40000 -U firmware_readback.bin
   cmp -l firmware_original.bin firmware_readback.bin
   ```

   The number of differences depends on the selected groups:
   jog 2, pitch 2, dead-zone 12, and the sums for combinations.

7. Power-cycle and test.

## Revert

```sh
dfu-util -a 0 -s 0x08000000:0x40000 -D firmware_original.bin
```

The ROM DFU bootloader is in system memory and is not touched, so recovery does
not depend on the application firmware booting.

## Validation summary

| Test | Result |
|---|---|
| Left ring, 1 rev / 6 s, stock | 0 packets |
| Left ring, 1 rev / 6 s, patched | 237 packets (`B1 09`) |
| Right ring, 1 rev / 6 s, patched | 87 packets (`B2 09`) |
| Left ring, 1 rev / 12 s, patched | 152 packets |
| Idle, 6 s | 0 packets |
| Violent shake, 15 s | 0 packets |
| Pitch at 6% scale | about 0.3 BPM steps -> about 0.1 BPM |
| Dead-zone calibration | EQ/filter/volume feel precise; no drift at center |
| WebUSB read/write/restore | validated end to end on Edge |
| BLE-MIDI slow ring | 228 packets / 12 s, all `B1 09 01` |

Full details: [`docs/validation.md`](docs/validation.md).

## Project findings

- Full 256 KB dump, read twice with identical SHA-256.
- RDP Level 0 on the test unit; standard STM32 DFU at `0483:DF11`.
- Jog path: EXTI pairs 7/6 (left) and 5/4 (right), ISR `0x08002F40`,
  translator `0x08006048`.
- Pitch faders are 14-bit CC8/CC40; all absolute controls use the same
  dead-zone table.
- MIDI map decoded from a djay Pro export: note channels are 0-based, CC
  channels use 0-based indexing with the mapping's channel 0 as global.
- Pads are single-channel brightness over SPI3, not RGB. The battery indicator
  is separate and multi-color.
- Service mode: hold jog + Neural Mix; top-row pads are notes 0-7 on channel 6,
  bottom row on channel 7; used for touch sensitivity.
- Failed experiments: the absolute dead-zone entry 0 for the ring, a firmware
  layer-B channel remap, and a master-volume offset. The layer-B and
  master-offset test images were unstable and were reverted.
- djay 4-deck mappings on iOS use `condition` / `modifier` fields rather than
  new firmware channels. The 4-deck work is parked.
- USB/BLE MIDI merge would require USB host support and is not available in the
  current firmware.

More detail: [`docs/reverse-engineering.md`](docs/reverse-engineering.md).

## Safety

- Keep the verified stock dump.
- Do not interrupt power during a DFU write.
- A firmware modification may void the warranty.
- This project is independent and not affiliated with Hercules or Guillemot.

## Repository audit and license

Repository hygiene and legal notes: [`docs/repo-audit.md`](docs/repo-audit.md).

MIT. See [`LICENSE`](LICENSE).
