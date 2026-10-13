---
name: qualcomm-edl-recovery
description: Recover a bricked Qualcomm phone over USB with the boot ROM's EDL mode and bkerler/edl. Use when a phone is stuck in Qualcomm crashdump (USB 05c6:900e, QUSB_BULK), sits in EDL (05c6:9008), or shows a black screen or boot loop after flashing.
---

# Qualcomm EDL recovery

Every Qualcomm phone carries a boot ROM that flashing cannot overwrite, and that ROM speaks EDL over USB. So a phone that still enumerates on USB is almost always recoverable. The work is a diagnosis: read the phone until one partition stands out as the **odd one out**, prove a replacement image is genuine, write it, and watch what the phone does next.

The user's hands do the physical part (key combos, the cable, on-screen menus); you watch USB and say what each id means. Every step below is **read-only** until step 9, and nothing is written without the user's go-ahead for that write.

Ground rules that hold throughout:

- The device-unique partitions (`modemst1`, `modemst2`, `fsg`, `fsc`, `persist`, and vendor NV backups such as OnePlus's `oem_stanvbk`/`oem_dycnvbk`) hold the IMEI and calibration. No download can restore them, so they are backed up before the first write and only ever written back from this phone's own backup.
- Run edl as root (pkexec or sudo) from an empty directory, and keep the cable seated during any write.
- Setup, the edl gotchas and the `EDL_SITE_PACKAGES` variable for the scripts are in [references/environment.md](references/environment.md).

## Steps

### 1. Identify the mode

Read the USB vendor:product id from `lsusb` or the kernel log (`journalctl -k`, `dmesg`) and match it against [references/usb-modes.md](references/usb-modes.md). A black screen tells you nothing: both 900e and 9008 run before any display driver.

Done when: you can name the mode from the id.

### 2. Crashdump (900e): read the crash evidence

1. `scripts/crashdump_list.py` prints the memory regions on offer without dumping or resetting.
2. Dump only the small log regions: `edl memorydump --partitions=KMSG.txt,PMSG.bin,device_info.txt,RST_STAT.BIN,PMIC_PON.BIN,PMON_HIS.BIN`. A plain `edl` run in 900e dumps all of RAM, gigabytes.
3. Read them. A kernel log full of text names the kernel-side failure. Log regions holding only `0xff` mean the kernel never ran, so the crash sits in the firmware chain the bootloader loads (`tz`, `hyp`, `aop`, `abl`, `devcfg`, ...).

Done when: you can say "the crash is before the kernel" or quote what the kernel logged.

### 3. Reach EDL (9008)

From a powered-off phone, the vendor key combo does it (OnePlus: hold volume up + volume down while plugging in). A phone in crashdump stays running on battery, so unplugging and replugging only reconnects it, and its reboots go straight back to crashdump. Make the reboot happen with the keys held: the user holds the combo with the cable in, and `scripts/crashdump_reset.py --delay 30` reboots the phone over USB.

Done when: `05c6:9008` enumerates.

### 4. Upload a loader behind the guard

1. Pick the firehose loader for the device. edl ships many under `Loaders/`, named `<hwid>_<pkhash16>_...`.
2. Cross-check the name against `scripts/certs.py LOADER`: the self-signed root's sha256 must start with the filename's pkhash.
3. Run every edl command through `scripts/edl_guarded.py --loader LOADER --expect-hwid HWID --expect-pkhash PKHASH -- <edl args>`. It refuses to upload unless the phone reports that HWID and PK hash, and it suppresses the sahara reset edl sends on a handshake error, which would drop the phone back into its crash loop.

Done when: the guard prints `match` and edl prints `Loader successfully uploaded`.

### 5. Map the storage

`edl printgpt --memory=ufs` (or `--memory=emmc` on older phones), saving the log. `scripts/slotflags.py LOG boot` decodes the active slot, its retry count and whether it ever booted successfully.

Done when: every LUN parsed and you know the active slot.

### 6. Back up

Read the device-unique partitions, the partition tables (`edl gpt DIR --genxml`) and the firmware partitions of both slots (`edl r a_part,b_part a_part.img,b_part.img`). Hash everything into a `SHA256SUMS`, copy it to the user's home directory, and tell them the path.

Done when: `sha256sum -c SHA256SUMS` passes in the user's copy, and every device-unique partition is in it.

### 7. Find the odd one out

1. `scripts/fw_survey.py DIR` compares the slots and prints each image's version strings. Look for a partition whose slots differ, or whose version breaks from the set around it (`tz` and `hyp` ship as a pair, from one build).
2. With an official package for the device, `scripts/payload_parts.py OTA.zip --against DIR` says which partitions on the phone match that release byte for byte.

Done when: you can point at the partition (or set) at fault with a version or hash as evidence, or show that every firmware image is consistent, which moves the search to the boot image and step 2's evidence.

### 8. Prove the replacement genuine

The candidate comes from the phone's healthy slot or from an official package whose download is verified per [references/verification.md](references/verification.md). Before writing it:

- `scripts/certs.py IMAGE`: the root's sha256 equals the PK hash the phone reported in step 4, and the attestation certificate's `SW_ID` matches the partition's image type.
- `scripts/segcheck.py IMAGE` exits 0: every segment hash verifies and the image is complete.

Done when: both checks pass on the exact file you will write.

### 9. Write, then read back

With the user's go-ahead for this write: `edl w PARTITION FILE`, then `edl r PARTITION readback.img` and compare sha256 with the source.

Done when: the readback's sha256 equals the source's.

### 10. Reboot and observe

`edl reset`, then watch USB for a minute or two. A fastboot or adb device, or the boot logo, means the chain got further; on Linux the gadget's `bcdDevice` carries the kernel version, so a value like `4.09` proves a kernel booted. A return to 900e brings new evidence: go back to step 2 with it.

Done when: the phone reaches its bootloader or OS, or crashdump has handed you new evidence.

Installing an OS once the phone boots, including the traps around bundled firmware, sideload and app integrity, is in [references/after-recovery.md](references/after-recovery.md). A complete worked case, a OnePlus 6T revived from a mismatched `tz`, is in [references/case-oneplus-6t.md](references/case-oneplus-6t.md).
