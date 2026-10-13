# Verifying images and downloads

Two separate questions: is an image one this phone will accept, and is a
downloaded package the vendor's original?

## Will the phone accept this image?

A fused Qualcomm phone verifies its firmware chain at boot, and every link is
a signed ELF:

- The **root certificate** at the end of the image's chain hashes (sha256) to
  the PK hash the phone reports in sahara. `certs.py` prints it. A different
  root means a foreign key: the phone rejects the image.
- The **attestation certificate** carries OU fields: `SW_ID` (the image type,
  e.g. `07` for TrustZone on SDM845), `HW_ID`, `OEM_ID`, `MODEL_ID`.
- The **hash-table segment** holds a sha256 for every loadable segment, and the
  signature covers that table. `segcheck.py` recomputes the segment hashes,
  which catches truncation and corruption.

A correctly signed image can still be rejected for its version: anti-rollback
fuses or a pairing between images (`tz` with `hyp`) turn an older but genuine
build away. Version strings (`QC_IMAGE_VERSION_STRING`) settle that.

Two images of the same build can differ only in the OEM signature block and
the attestation certificate, which are regenerated at every signing. If `cmp`
confines the differences to that region, and the segment hashes and the
Qualcomm certificates match, the code is identical.

Partitions outside the chain (`system`, `vendor`, `boot` on an unlocked
bootloader, `LOGO`) are not verified by the phone; their trust rests on the
download alone.

## Is the download the vendor's original?

In order of strength:

1. **A vendor checksum** published next to the file.
2. **The vendor's own ETag.** Vendor CDNs often ran on S3, and the Wayback
   Machine keeps the original response headers as `x-archive-orig-etag`. Check
   them with
   `curl -sI "https://web.archive.org/web/<timestamp>id_/<original url>"`. An
   ETag of the form `<md5>-<parts>` is an S3 multipart hash. `s3etag.py FILE ETAG`
   recomputes it on a copy from any mirror, and a match proves the copy is
   byte-identical to what the vendor served.
3. **A mirror's md5** (AndroidFileHost lists one per file). This proves only
   that you got what the mirror holds.

To locate an archived copy: `https://archive.org/wayback/available?url=<host>/<filename>`.
Wayback downloads can run at around 100 KB/s, so find a fast mirror for the
bytes and use the archived headers for the proof.
