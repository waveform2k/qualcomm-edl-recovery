# After recovery: installing an OS

## Custom ROMs can carry firmware

An A/B OTA zip lists every partition it writes. `payload_parts.py ROM.zip`
prints the list. Some LineageOS builds (the OnePlus 6T's, for one) carry the
full vendor firmware set (`xbl`, `tz`, `hyp`, `abl`, `modem`, ...), so the zip
itself writes the firmware it needs. `payload_parts.py ROM.zip --against DIR`
compares that set with the phone's dumps. The zip's `META-INF/com/android/metadata`
names the stock build its firmware comes from in `post-build`.

A ROM's install guide may demand a stock firmware version first. When the
phone's firmware already matches the zip's, or the zip writes it anyway,
that demand is met.

## LineageOS install, the parts that surprise

- The guide's order is: flash `dtbo`, flash the recovery `boot.img`, boot
  recovery, format data, sideload the ROM, reboot to recovery, sideload add-ons
  (gapps), then reboot to system. Gapps installed after the first boot set up
  badly.
- `adb sideload` often stops at about 47% with `adb: failed to read command: Success`
  and exit status 1. Lineage documents this as normal. The phone's own status
  is the one to trust ("Install completed with status 0", or its offer to reboot
  to recovery for add-ons).
- Gapps (MindTheGapps) fail recovery's signature check, since they are not
  signed with the ROM's key. Verify the zip against its release checksum, then
  answer yes to "install anyway".
- A fastboot write cut short by a pulled cable leaves the partition in an
  unknown state. Reflash it before booting it.
- Android setup can refuse to continue below 20% battery. EDL, fastboot and
  recovery never check the battery.

## Keep the bootloader unlocked under a custom OS

Relocking the bootloader over a custom OS can keep it from booting, since a
locked bootloader expects images signed with the vendor's key (general Android
verified-boot behaviour; not tested on any phone here). The user,
and whoever gets the phone, should know `fastboot oem lock` is off-limits
while it runs anything but stock.

## App integrity

An unlocked bootloader shows in hardware key attestation, which Play
Integrity's device verdict relies on for Android 13 and later since Google's
2025 changes (recalled, not re-checked; Google's Play Integrity docs are the
source of truth). Expect Google
Wallet and some banking apps to refuse to run, while apps that check only
basic integrity keep working. Relocked stock firmware is the only setup with
a real chance of passing. Even then, an old security patch level can fail an
app's own checks.
