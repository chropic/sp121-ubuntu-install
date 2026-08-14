# Launch checklist

The repository and installer builder may be published before a supported
installer image. The local candidate recorded in [`CANDIDATE.json`](CANDIDATE.json)
is evidence for build-pipeline testing, not a release artifact.

## Completed

- [x] Pin and inspect the external SP12 support checkout.
- [x] Verify Canonical's signed Ubuntu 26.04 ARM64 checksum metadata.
- [x] Require exact ISO and installer-DTB hashes in the builder.
- [x] Exclude the third-party support checkout and its binary files from the ISO.
- [x] Embed the exact project revision and input hashes.
- [x] Refresh Ubuntu's media checksums after remastering.
- [x] Preserve the ARM64 EFI boot path and valid hybrid GPT.
- [x] Add an offline integration test and ShellCheck coverage.
- [x] Audit every extracted candidate file against the media manifest.

## Required before an installation-tested release

- [ ] Boot the candidate on the exact supported Surface Pro 12 model.
- [ ] Confirm the live DT model/compatible values and internal UFS visibility.
- [ ] Complete an installation on a recoverable test device.
- [ ] Exercise fallback boot installation and recovery from a deliberately broken
      primary boot path.
- [ ] Run `scripts/sp12-verify` and the full hardware-verification chapter.
- [ ] Record pass/fail results for every item in `SUPPORT.md`.
- [ ] Rebuild from the final tagged commit and repeat the complete offline audit.
- [ ] Produce signed release checksums and final build provenance.

## Distribution boundary

Under the current policy, publish the repository, builder, documentation, and
redistributable source only. Do not upload:

- the locally modified Ubuntu ISO;
- the Harrison support checkout or its firmware/DSP files;
- DTB or kernel binaries without their required source and provenance bundle;
- any image labeled supported before the physical test gates above pass.
