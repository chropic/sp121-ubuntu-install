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

`CANDIDATE.json` preserves the earlier stock-live/bootstrap image-pipeline audit.
It does not describe the new 7.3 target bundle. That historical image is not
a release artifact and must not be uploaded under the current builder-only
distribution policy.

Linux 7.3 platform is now the sole maintained/default build and installed-system
target. The builder requires its inspected image package and matching build
information and embeds them under `/sp12-kernel/`. Ubuntu's stock live kernel and
frozen bootstrap DTB are retained separately; the installed target uses the DTB
from its 7.3 package. A complete fresh installation with this bundle is untested.

The [main Linux 7.3 kernel](../kernel/ports/v7.3/README.md) has separate build,
package and physical-boot evidence. Its successful kernel boot does not validate
the ISO or the installer workflow below.

## Installer release checklist

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
- [ ] Run `scripts/sp12-verify` and the full hardware checks in [hardware checks](../docs/hardware-tests.md).
- [ ] Record every [support matrix](../docs/support.md) item as pass or fail.
- [ ] Rebuild from the final tag and repeat the complete offline audit.
- [ ] Produce signed release checksums and final build provenance.

Until then, publish only the repository, builder, documentation, and
redistributable source. Do not upload the modified Ubuntu ISO; the Harrison
checkout or its firmware/DSP files; DTB or kernel binaries without required
source and provenance; or any image labeled supported before those gates pass.
