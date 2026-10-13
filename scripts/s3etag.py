"""Check a downloaded file against an Amazon S3 multipart ETag ("<md5>-<parts>").

Vendor firmware CDNs often sat on S3, and an archived copy (the Wayback
Machine keeps them as `x-archive-orig-etag`) preserves the vendor's ETag. A
match proves a mirror's copy is byte-identical to the vendor's original
without trusting the mirror. Common part sizes are tried in turn.

Usage: s3etag.py FILE ETAG
"""
import hashlib
import math
import os
import sys

path, want = sys.argv[1], sys.argv[2].strip('"').lower()
md5hex, _, parts = want.partition("-")
size = os.path.getsize(path)
if not parts:
    got = hashlib.md5(open(path, "rb").read()).hexdigest()
    print("MATCH" if got == md5hex else f"no match: md5={got}")
    sys.exit(0 if got == md5hex else 1)
parts = int(parts)
candidates = [m * 1024 * 1024 for m in (5, 8, 10, 15, 16, 25, 32, 50, 64, 100, 128)]
candidates = [c for c in candidates if math.ceil(size / c) == parts]
if not candidates:
    sys.exit(f"no common part size gives {parts} parts for {size} bytes")
for part in candidates:
    digests = b""
    with open(path, "rb") as f:
        while chunk := f.read(part):
            digests += hashlib.md5(chunk).digest()
    got = f"{hashlib.md5(digests).hexdigest()}-{parts}"
    print(f"part={part} etag={got}")
    if got == want:
        print("MATCH")
        sys.exit(0)
sys.exit(1)
