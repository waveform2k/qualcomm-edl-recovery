"""Verify a Qualcomm signed ELF against its own hash-table segment.

Recomputes the sha256 of every loadable segment and checks each digest appears
in the signed hash table, which catches truncation and corruption. It does not
check the signature itself; certs.py shows which key signed the image.

Accepts a raw partition dump: bytes past the image end are ignored.
Usage: segcheck.py IMAGE
Exit status: 0 when every segment verifies, 1 otherwise.
"""
import hashlib
import struct
import sys

d = open(sys.argv[1], "rb").read()
if d[:4] != b"\x7fELF" or d[4] != 2:
    sys.exit("not a 64-bit ELF")
phoff, = struct.unpack_from("<Q", d, 0x20)
phentsize, phnum = struct.unpack_from("<HH", d, 0x36)
ph = [struct.unpack_from("<IIQQQQQQ", d, phoff + n * phentsize) for n in range(phnum)]
# qualcomm marks the hash-table segment with segment type 2 in bits 24-26 of p_flags
hseg = [p for p in ph if (p[1] >> 24) & 7 == 2]
if len(hseg) != 1:
    sys.exit("no unique hash segment")
table = d[hseg[0][2]:hseg[0][2] + hseg[0][5]]
end = max(p[2] + p[5] for p in ph)
print(f"segments={phnum} image_end=0x{end:x} file=0x{len(d):x}")
if end > len(d):
    sys.exit("image is truncated")
ok = bad = 0
for n, p in enumerate(ph):
    if p is hseg[0] or p[5] == 0:
        continue
    if hashlib.sha256(d[p[2]:p[2] + p[5]]).digest() in table:
        ok += 1
    else:
        bad += 1
        print(f"  segment {n} off=0x{p[2]:x} size=0x{p[5]:x}: hash not in table")
print(f"segment hashes verified {ok}, missing {bad}")
sys.exit(1 if bad else 0)
