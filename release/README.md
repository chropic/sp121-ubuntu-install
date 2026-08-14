# Releases

Binary files do not belong in Git history. A future GitHub Release will contain:

- exact ARM64 kernel image and header packages;
- matching DTB;
- `SHA256SUMS`;
- `BUILDINFO.json`;
- corresponding source/patch bundle;
- installation and rollback notes;
- hardware-test results.

`reference/BUILDINFO.json` records the sanitized live system from which the guide
was written. It is evidence, not a promise that equivalent binaries have already
been published.
