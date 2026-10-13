"""Run an edl command with two guards a bricked phone needs.

1. Every sahara reset is suppressed. edl resets the device when a sahara
   handshake fails, and on a phone whose boot chain crashes that reset drops it
   out of EDL and back into the crash loop.
2. The loader is uploaded only when the device's reported HWID equals
   --expect-hwid and its PK hash starts with --expect-pkhash. Otherwise the
   script exits with status 3 before anything is sent.

Usage:
  edl_guarded.py --loader FILE --expect-hwid 0008b0e10051459b \
      --expect-pkhash dd7c5f2e53176bee -- printgpt --memory=ufs

Once a loader is running, later edl commands reach firehose directly and the
loader guard never fires; the reset guard still applies.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _edl  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--loader", required=True)
ap.add_argument("--expect-hwid", required=True, help="16 hex digits, e.g. 0008b0e10051459b")
ap.add_argument("--expect-pkhash", required=True, help="hex prefix of the PK hash, 16+ digits")
ap.add_argument("edl_args", nargs=argparse.REMAINDER)
a = ap.parse_args()
edl_args = a.edl_args[1:] if a.edl_args[:1] == ["--"] else a.edl_args
want_hwid = a.expect_hwid.lower().removeprefix("0x")
want_pk = a.expect_pkhash.lower().removeprefix("0x")
if len(want_pk) < 16:
    sys.exit("--expect-pkhash needs at least 16 hex digits")

sahara = _edl.sahara_class()


def no_reset(self):
    print("[guard] sahara reset suppressed", flush=True)


orig_upload = sahara.upload_loader


def checked_upload(self, version):
    hw = getattr(self, "hwidstr", None)
    pk = getattr(self, "pkhash", None) or ""
    print(f"[guard] device hwid={hw} pkhash={pk}", flush=True)
    if hw is None:
        print("[guard] device did not report a hwid (sahara v3+?), not uploading", flush=True)
        sys.exit(3)
    if hw != want_hwid or not pk.startswith(want_pk):
        print(f"[guard] mismatch, expected hwid={want_hwid} pkhash={want_pk}..., not uploading", flush=True)
        sys.exit(3)
    print("[guard] match, uploading loader", flush=True)
    return orig_upload(self, version)


sahara.cmd_reset = no_reset
sahara.upload_loader = checked_upload
_edl.run_edl(edl_args + ["--loader=" + a.loader])
