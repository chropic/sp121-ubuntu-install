# Device support files

This directory contains provenance records and installation tooling, **not**
firmware blobs. Some files needed by the Surface Pro 12 originated in Microsoft
or Qualcomm driver packages and do not have redistribution terms suitable for
this project.

The tested source checkout is Harrison van der Byl's Surface Pro 12 repository
at the exact revision recorded in [`sources.yaml`](sources.yaml). A user may
place their own checkout on the target machine and inspect it with:

```bash
scripts/inspect-support-source --source /opt/surface-pro-12-linux
```

The inspection is read-only. To preview the narrowly scoped installation:

```bash
sudo scripts/install-platform-files --source /opt/surface-pro-12-linux
```

That command does not write without `--apply`. Read its output, confirm that the
checkout came from a source you trust, and review any applicable third-party
licence terms before using the apply option described in
[`docs/03-first-boot.md`](../docs/03-first-boot.md).

Wi-Fi board extraction, AudioReach topology generation, and the ALSA UCM routing
fix are separate, checksum-verifying steps. This prevents a broad firmware copy
from silently installing or replacing unrelated components.

## Why the blobs are absent

- A public Git repository is not proof that every binary in it may be
  redistributed in another project or release.
- GitHub Releases and custom ISO images are redistribution too.
- A checksum establishes identity, not permission.
- This project can reproduce the installation procedure without republishing
  third-party binaries.

Do not attach a firmware bundle to an issue. The diagnostics script deliberately
does not collect firmware contents.
