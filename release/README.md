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
distribution policy.

## Launch checklist

Completed: the external support checkout is pinned and inspected; Canonical's
signed checksum metadata is verified; exact ISO and installer-DTB hashes are
required; third-party support binaries are excluded; project and input
provenance is embedded; Ubuntu media checksums are refreshed; the ARM64 EFI path
and hybrid GPT are preserved; offline integration and ShellCheck coverage exist;
and every extracted candidate file was audited against the media manifest.

Before an installation-tested release:

- [ ] Boot the candidate on the exact supported Surface Pro 12 model.
- [ ] Confirm live DT model/compatible values and internal UFS visibility.
- [ ] Complete installation on a recoverable test device.
- [ ] Exercise fallback installation and recovery from a deliberately broken
      primary boot path.
- [ ] Run `scripts/sp12-verify` and the full hardware checks in `../GUIDE.md`.
- [ ] Record every `../SUPPORT.md` item as pass or fail.
- [ ] Rebuild from the final tag and repeat the complete offline audit.
- [ ] Produce signed release checksums and final build provenance.

Until then, publish only the repository, builder, documentation, and
redistributable source. Do not upload the modified Ubuntu ISO; the Harrison
checkout or its firmware/DSP files; DTB or kernel binaries without required
source and provenance; or any image labeled supported before those gates pass.
