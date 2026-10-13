"""List the memory regions a phone in Qualcomm crashdump mode (05c6:900e) offers.

Reads only the region table: no region contents, no reset, so the device stays
in crashdump. Dump chosen regions afterwards with
`edl memorydump --partitions=NAME,NAME`, which writes ./memory/ (deleting any
existing ./memory first) and resets the device when done.

The sahara session is left half-open; a later edl run may wait for the device
until the cable is replugged.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _edl  # noqa: E402

sahara = _edl.sahara_class()


def list_only(self, partitions):
    total = sum(p["length"] for p in partitions)
    print(f"[list-only] {len(partitions)} regions, 0x{total:x} bytes in total", flush=True)
    return True


sahara.dump_partitions = list_only
_edl.run_edl(["memorydump"])
