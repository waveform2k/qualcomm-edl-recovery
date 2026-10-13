# Worked case: OnePlus 6T stuck in crashdump

One full run of the procedure on a OnePlus 6T, international A6013 (codename
fajita, SDM845, 8 GB RAM, Samsung UFS `KLUDG4U1EA`), bootloader unlocked,
bricked by an earlier flashing session that left no record of what it wrote.
It took about an hour and a quarter from first plug-in to LineageOS booting.

## Symptoms

- Black screen. USB showed `05c6:900e`, product `QUSB_BULK_SN:<serial>`.
- Later, the screen showed "QUALCOMM CrashDump Mode" with an empty line under it.

## Evidence from crashdump

- The memory table listed 43 regions, four of them 2 GB DDR banks (8 GB in all).
- `KMSG.txt`, `PMSG.bin` and `device_info.txt` held only `0xff`, so the kernel
  never ran this boot. That pointed at the firmware chain after XBL.
- The memory table itself came from XBL's ramdump handler, so XBL was alive.

## Reaching EDL

Two tries of "power off with power + volume, then hold volume up + volume down
and plug in" came back as 900e. What worked: the user held volume up + volume
down with the cable in while `crashdump_reset.py --delay 30` rebooted the phone.
9008 appeared 3 seconds after the reset. After the repair, the plain key combo
worked from a powered-off phone.

## Loader

edl's bundled `Loaders/oneplus/0008b0e10051459b_dd7c5f2e53176bee_fhprg_op6t.bin`.
The phone reported HWID `0x0008b0e10051459b` (MSM_ID `0x0008b0e1`, OEM_ID
`0x0051`, MODEL_ID `0x459b`) and PK hash `dd7c5f2e53176bee91747b53900ccec3...`.
The loader's root certificate, Qualcomm's "QCT Root CA 1 / General Use Test
Key", hashes to the same value, and so does the root of every firmware image
on this phone.

## The odd one out

Every firmware partition matched across slots except `tz`:

| partition | slot a (active) | slot b |
|---|---|---|
| `tz` | `TZ.XF.5.0.1.C5-00018` | `TZ.XF.5.0.1.C5-00083.1` |
| `hyp` | `TZ.XF.5.0.1.C5-00083.1` | `TZ.XF.5.0.1.C5-00083.1` |

Both `tz` images were genuinely signed (same root, `SW_ID 07`) and intact (14
of 14 segment hashes). Slot a paired an older TrustZone with the newer
hypervisor. `boot_a`'s flags read `0x001f`: active, 3 retries left, never
booted successfully.

## Fix

`tz_b` written to `tz_a` (2 MB, LUN 4, sector 134), and the readback's sha256
matched. After `edl reset`, the phone came up as `18d1:4ee0` in fastbootd
(`bcdDevice 4.09`: a 4.9 kernel had booted).

## Backup findings

- `fsg`, normally the factory spare of the radio data, was all zeros, so
  `modemst1`/`modemst2` were the only working copies. Whether that's normal
  for the 6T is unknown.
- `cdt` was all zeros too, and the phone booted fine.

## Afterwards

- The last stock build is OxygenOS 11.1.2.2,
  `OnePlus6TOxygen_34.J.62_OTA_0620_all_2111252336_f6eda340d7af4e3e.zip`,
  2,197,912,110 bytes. The vendor host `oxygenos.oneplus.net` is gone, and the
  Wayback Machine kept a copy with the original ETag
  `64c3778e62aa5a799f7a007791a009f7-140` (15 MiB parts). AndroidFileHost's copy
  (md5 `fb113b6ccf7376a49399f40de9bb3cbe`) matched that ETag and downloaded
  about 20 times faster.
- LineageOS 22.2 (Android 15) is the latest official build for fajita. Its zip
  carries the OxygenOS 11.1.2.2 firmware set, which already matched the phone
  apart from `tz`. Even `tz` held the same `C5-00083.1` code, re-signed, with
  differences confined to the OEM signature region. So no stock install was
  needed before Lineage.
- Install went dtbo, recovery boot.img, format data, sideload Lineage (stopped
  at 47%, normal), reboot to recovery, sideload MindTheGapps (signature prompt,
  install anyway), reboot. Calls, SMS, mobile data, Wi-Fi and the camera worked.
- On Lineage with the bootloader unlocked and no root, the Wealthsimple and
  Scotiabank apps both ran, so the integrity warning in after-recovery.md
  describes a risk, not a certainty.
