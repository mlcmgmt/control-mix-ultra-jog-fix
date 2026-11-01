# Repository audit

Audit date: 2026-11-01

Scope: all tracked files in this repository, plus the git history after the
single-commit rewrite.

## What is included

- Original Python scripts for applying the patches and capturing MIDI.
- Documentation covering the three patch groups, flashing, reverting,
  reverse-engineering notes, validation, and safe-update practice.
- The SHA-256 of the stock firmware and byte-level patch descriptions.
- An MIT license.

## What is not included

- No stock or patched firmware binary.
- No firmware dumps, option-byte dumps, or full flash images.
- No djay Pro mapping exports. The decoded findings are described in text, but
  the original `.djayMidiMapping` files remain local.
- No device serial numbers, MAC addresses, USB instance IDs, or local
  filesystem paths.
- No personal email addresses in tracked files.
- No vendor source code, SDK, manual PDF, or proprietary tools.
- No API keys, tokens, passwords, or private keys.

## Checks performed

- Regex scan of every tracked file for Windows and POSIX absolute paths, MAC
  addresses, email addresses, long digit strings, GitHub/AWS tokens,
  private-key markers, and password/secret words.
- Manual review of the README, docs, scripts, license, and patch text.
- `git ls-files` review: all tracked files are text; no binaries.
- Git history collapsed to a single commit with a generic project identity.

## Privacy

- The GitHub account that hosts this repository is public by design.
- The commit identity is generic and uses a no-reply address.
- No device-unique identifiers are published.
- The companion site is separate from this repository and has its own
  third-party notices for the WebDFU driver.

## Trademarks and affiliation

Hercules and DJControl are trademarks of their respective owners. This project
is independent and is not affiliated with or endorsed by Hercules or Guillemot.
The names are used only to describe compatibility.

## Legal notes

- This repository does not distribute vendor firmware. Users must dump their
  own device and keep their own restore image.
- Modifying firmware may void the warranty and may be restricted by the vendor
  EULA. Laws on reverse engineering and interoperability vary by jurisdiction.
  This is not legal advice.
- On the tested unit the firmware was not read-protected (RDP Level 0), and the
  patches do not implement a bypass of an access-control or DRM system. They
  change behavior in firmware the owner can already read and write.
- The repository contains factual addresses, byte values, and test results. It
  does not contain a substantial portion of vendor code.
- If a rights holder contacts you about this repository, review the request with
  counsel before responding.

## History

The repository was rewritten to a single commit so that earlier experimental
files and commit history are not part of the current published branch. GitHub
may retain unreachable objects in its internal cache for a period; they are not
reachable from the branch.
