"""Reboot a phone in Qualcomm crashdump mode (05c6:900e) after a countdown.

A phone in crashdump keeps running on battery, so unplugging it and holding
the EDL key combo while replugging never reaches the boot ROM. This sends the
sahara reset that edl's memorydump path ends with, after --delay seconds,
giving the user time to hold the EDL keys so the reboot happens with them
held. It reads one tiny region to get the session going and writes nothing.

Usage: crashdump_reset.py [--delay 30]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _edl  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--delay", type=int, default=30)
a = ap.parse_args()

sahara = _edl.sahara_class()


def reset_after_delay(self, partitions):
    for left in range(a.delay, 0, -1):
        print(f"reset in {left}s", flush=True)
        time.sleep(1)
    self.cmd_reset()
    print("reset sent", flush=True)
    return True


sahara.dump_partitions = reset_after_delay
# the filter only has to match nothing large; the region list is not read further
_edl.run_edl(["memorydump", "--partitions=RST_STAT.BIN"])
