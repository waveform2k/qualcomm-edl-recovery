"""Print the certificate chain embedded in a Qualcomm signed image (ELF/MBN).

The sha256 of the self-signed root certificate is the PK hash a device fused
with that key reports in sahara (edl prints it as PK_HASH). The attestation
certificate's OU fields carry SW_ID (image type), HW_ID, OEM_ID and MODEL_ID.

Usage: certs.py IMAGE   (needs the openssl command)
"""
import hashlib
import re
import subprocess
import sys

data = open(sys.argv[1], "rb").read()
seen = []
i = data.find(b"\x30\x82")
while i != -1:
    length = int.from_bytes(data[i + 2:i + 4], "big") + 4
    der = data[i:i + length]
    # a DER certificate opens with a nested SEQUENCE for tbsCertificate
    if der[4:6] == b"\x30\x82" and length > 300 and der not in seen:
        r = subprocess.run(["openssl", "x509", "-inform", "DER", "-noout", "-subject", "-issuer"],
                           input=der, capture_output=True)
        if r.returncode == 0:
            seen.append(der)
            text = r.stdout.decode()
            subject = text.split("\n")[0]
            cn = re.search(r"CN\s*=\s*([^,\n]+)", subject)
            ous = re.findall(r"OU\s*=\s*(\d\d [0-9A-F]+ [A-Z_]+)", subject)
            print(f"cert {len(seen)} @0x{i:x} sha256={hashlib.sha256(der).hexdigest()}")
            print(f"  CN={cn.group(1) if cn else '?'}")
            for ou in ous:
                print(f"  {ou}")
            if "issuer=" in text and text.split("issuer=")[1].strip() == subject.removeprefix("subject=").strip():
                print("  (self-signed root)")
    i = data.find(b"\x30\x82", i + 1)
if not seen:
    sys.exit("no certificates found")
