# qualcomm-edl-recovery

An agent skill for recovering a bricked Qualcomm phone over USB: a phone stuck
in Qualcomm crashdump (`05c6:900e`), sitting in EDL (`05c6:9008`), or black-
screened after a bad flash. It walks an agent through diagnosing the phone
read-only, backing up its irreplaceable radio partitions, finding the one
partition at fault, proving a replacement image genuine, and writing it with a
readback check.

It grew out of a real recovery: a OnePlus 6T bricked by a mismatched TrustZone
image, revived with a 2 MB write and then moved to LineageOS. That case is
written up in `references/case-oneplus-6t.md`.

## Install

Copy this directory into your agent's skills folder, e.g. for Claude Code:

```sh
git clone <this repo> ~/.claude/skills/qualcomm-edl-recovery
```

The agent picks it up when you describe a bricked or crashdumped Qualcomm phone.

## Requirements

- [bkerler/edl](https://github.com/bkerler/edl) (`edl` and its `edlclient`
  package); see `references/environment.md`, including NixOS notes
- Python 3.9+, `openssl`, root access for USB (pkexec or sudo)
- the phone's own firehose loader (edl ships many) and, for a stock restore,
  the vendor's firmware package

## Layout

| path | contents |
|---|---|
| `SKILL.md` | the procedure the agent follows |
| `references/` | USB modes, environment and edl gotchas, image and download verification, installing an OS afterwards, the 6T case |
| `scripts/edl_guarded.py` | runs edl with a HWID/PK-hash check before any loader upload, and with sahara resets suppressed |
| `scripts/crashdump_list.py`, `crashdump_reset.py` | list crashdump memory regions; reboot from crashdump on a countdown so the EDL keys can be held |
| `scripts/certs.py`, `segcheck.py` | signing chain and segment-hash checks for Qualcomm signed images |
| `scripts/fw_survey.py`, `slotflags.py`, `payload_parts.py` | compare firmware across slots, decode A/B flags, list and compare an OTA's partitions |
| `scripts/s3etag.py` | verify a mirror's download against a vendor's S3 multipart ETag |

## Testing status

The offline scripts were run against the real dumps from the 6T recovery and
reproduced its findings. The three edl-driving scripts were tested for
start-up only (edl's command line ran and waited for a device). They are
rewrites of the exact code paths that ran against the phone, but have not yet
run end to end against a device in their packaged form. Reports from other
devices are welcome.

## Safety

The skill keeps every step read-only until a specific write is approved, backs
up `modemst1`/`modemst2`/`fsg`/`persist` before the first write, and refuses
to upload a loader whose identity doesn't match the phone. Flashing still
carries risk: you run this on your own device at your own risk.

## Authorship

Written by Claude (Opus 5.5) with waveform2k, from the OnePlus 6T recovery
session on 2026-10-12.
