"""Decode A/B slot attributes from an `edl printgpt` log.

Bit positions are the ones edl defines in edlclient/Library/gpt.py
(PART_ATT_*): bits 48-49 priority, 50 active, 51-53 retry count,
54 boot successful, 55 unbootable.

Usage: slotflags.py PRINTGPT_LOG [PARTITION ...]   (default: boot)
"""
import re
import sys

log = open(sys.argv[1], errors="replace").read()
want = set(sys.argv[2:] or ["boot"])
for m in re.finditer(r"^(\S+?)_(a|b):\s+Offset.*?Flags (0x[0-9a-fA-F]+)", log, re.M):
    name, slot, flags = m.group(1), m.group(2), int(m.group(3), 16)
    if name not in want:
        continue
    print(f"{name}_{slot}: flags=0x{flags:016x} priority={(flags >> 48) & 3} active={(flags >> 50) & 1} "
          f"retry={(flags >> 51) & 7} successful={(flags >> 54) & 1} unbootable={(flags >> 55) & 1}")
