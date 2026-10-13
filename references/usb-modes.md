# USB ids and boot modes

What each id means for a Qualcomm phone, and how the phone gets there. The ids
marked *observed* were seen on a OnePlus 6T (SDM845); the rest of the table is
the usual Qualcomm assignment.

| id | mode | who answers | what it accepts |
|---|---|---|---|
| `05c6:9008` | EDL, product string `QUSB__BULK` / `QUSB_BULK_CID:...` (*observed*) | boot ROM (PBL), sahara protocol | a signed firehose loader, then reads and writes of any partition |
| `05c6:900e` | crashdump, product `QUSB_BULK_SN:...` (*observed*) | XBL's ramdump handler, sahara in memory-debug mode | memory reads and a reset, nothing else |
| `18d1:4ee0` | fastbootd (*observed*, `fastboot getvar is-userspace` = yes) | recovery's userspace fastboot | fastboot flashing of logical and physical partitions |
| vendor-specific, check `fastboot devices` | bootloader fastboot (abl) | abl | fastboot flashing, slot switching |

## How the phone lands in each

- **EDL** is entered by the boot ROM when XBL is missing or invalid, when a test
  point is shorted, or when XBL sees the vendor key combo at cold boot.
  OnePlus: power off, then hold volume up + volume down while plugging in.
- **Crashdump** follows a crash anywhere after XBL starts. On the 6T, every
  attempt at the key combo from crashdump came back as 900e, and the combo
  worked the moment the phone rebooted with the keys held. The working
  explanation (inferred, not read from XBL source): a crash flag sends each
  boot back to crashdump and the combo goes unread, so the phone has to reboot
  with the keys held: `scripts/crashdump_reset.py` (see SKILL.md step 3).
- **Holding power + volume for 10-20 s** on a phone in crashdump appears to
  trigger a reset that reboots it rather than powering it off, which is why
  "power off, then key combo" guides failed from crashdump. That reading is
  inferred from the 6T's USB timing.

## Reading the kernel log

`journalctl -k` (or `dmesg`) shows each enumeration with `idVendor`, `idProduct`,
`bcdDevice` and the product string. Timestamps between a disconnect and the next
enumeration measure the boot loop: on the 6T a sahara reset came back as 900e
in 9 seconds, a full trip through XBL into the crash and back.

A Linux USB gadget reports the running kernel's version in `bcdDevice`
(`4.09` means a 4.9 kernel), so a fastboot or adb device with a kernel-shaped
`bcdDevice` proves the kernel booted.
