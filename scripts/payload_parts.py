"""List the partitions an A/B OTA zip (payload.bin) writes, with image sha256.

With --against DIR, also compares each image with partition dumps named
<partition>_<slot>.img in DIR, truncating each dump to the image's size, so
you can tell whether a phone already carries a package's firmware.

Usage: payload_parts.py OTA.zip [--against DIR]
"""
import argparse
import hashlib
import os
import struct
import zipfile


def varint(b, i):
    r = s = 0
    while True:
        c = b[i]
        i += 1
        r |= (c & 0x7F) << s
        s += 7
        if c < 0x80:
            return r, i


def fields(b):
    i = 0
    while i < len(b):
        k, i = varint(b, i)
        f, t = k >> 3, k & 7
        if t == 0:
            v, i = varint(b, i)
        elif t == 2:
            n, i = varint(b, i)
            v = b[i:i + n]
            i += n
        elif t == 1:
            v = b[i:i + 8]
            i += 8
        elif t == 5:
            v = b[i:i + 4]
            i += 4
        else:
            raise ValueError(f"wire type {t}")
        yield f, v


ap = argparse.ArgumentParser()
ap.add_argument("zip")
ap.add_argument("--against")
a = ap.parse_args()

with zipfile.ZipFile(a.zip) as z, z.open("payload.bin") as p:
    hdr = p.read(24)
    if hdr[:4] != b"CrAU":
        raise SystemExit("payload.bin has no CrAU header")
    _, manifest_size = struct.unpack(">QQ", hdr[4:20])
    manifest = p.read(manifest_size)

# DeltaArchiveManifest field 13 = PartitionUpdate: field 1 name, field 7 new_partition_info (1 size, 2 hash)
for f, v in fields(manifest):
    if f != 13:
        continue
    name = size = digest = None
    for g, w in fields(v):
        if g == 1:
            name = w.decode()
        elif g == 7:
            for x, y in fields(w):
                if x == 1:
                    size = y
                elif x == 2:
                    digest = y.hex()
    line = f"{name:<12} size={size} sha256={digest}"
    if a.against and size:
        for slot in "ab":
            dump = os.path.join(a.against, f"{name}_{slot}.img")
            if os.path.exists(dump):
                with open(dump, "rb") as fh:
                    same = hashlib.sha256(fh.read(size)).hexdigest() == digest
                line += f"  {slot}:{'same' if same else 'DIFFERS'}"
    print(line)
