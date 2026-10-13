"""Survey firmware partition dumps from both A/B slots.

Expects files named <partition>_a.img and <partition>_b.img in DIR (the names
`edl r` writes when given them). For each partition prints the ELF magic, a
short sha256, the QC/OEM version strings, and whether the slots are identical.
The partition whose slots disagree, or whose version breaks from its
siblings (tz and hyp ship as a pair), is the first suspect.

Usage: fw_survey.py DIR
"""
import glob
import hashlib
import os
import re
import sys

d = sys.argv[1]
names = sorted({os.path.basename(f)[:-6] for f in glob.glob(os.path.join(d, "*_[ab].img"))})
ver_re = re.compile(rb"(QC_IMAGE_VERSION_STRING|OEM_IMAGE_VERSION_STRING)=([\x20-\x7e]{1,60})")
for name in names:
    digests = {}
    for slot in "ab":
        path = os.path.join(d, f"{name}_{slot}.img")
        if not os.path.exists(path):
            continue
        data = open(path, "rb").read()
        digests[slot] = hashlib.sha256(data).hexdigest()
        versions = " ".join(f"{k.decode()[:2]}={v.decode()}" for k, v in ver_re.findall(data)[:2])
        magic = "elf" if data[:4] == b"\x7fELF" else ("blank" if not data.strip(b"\x00\xff") else data[:4].hex())
        print(f"{name}_{slot:<1} {magic:<6} sha256={digests[slot][:12]} {versions}")
    if len(digests) == 2:
        print(f"  -> slots {'identical' if digests['a'] == digests['b'] else 'DIFFER'}")
