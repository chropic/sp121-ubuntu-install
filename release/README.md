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

`CANDIDATE.json` records the current local image-pipeline audit. The image is not
a release artifact and must not be uploaded under the current builder-only
distribution policy. See [`LAUNCH-CHECKLIST.md`](LAUNCH-CHECKLIST.md) for the
remaining physical-test and release gates.
