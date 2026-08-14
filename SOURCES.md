# Source ledger

This file records what the project depends on and how each source may be used.
Release manifests will pin exact commits, hashes, and package versions.

| Source | Role | Distribution policy |
|---|---|---|
| Linux kernel | Kernel and modules | Publish corresponding source, config, patches, and build recipe with binaries |
| Harrison SP12 repository | DTB, firmware layout, scripts, platform research | Tested pin: `ea0f07e66beea95898d96fbeb6daa472f4735af3`; do not redistribute its binary files from this project |
| Mias Gentoo overlay | Kernel patch source | Preserve original patch metadata and upstream status |
| Ubuntu ARM64 ISO | Base installation system | Users download the official ISO; initially distribute a builder, not a modified ISO |
| linux-firmware | Redistributable firmware packages | Use distribution packages under their included licences |
| Microsoft Surface driver package | Device-specific proprietary firmware | Never redistribute without confirmed permission; document extraction from the user's device/package |
| Audioreach topology | Audio topology build input | Tested pin: `d7a5e9d80ad18a7a6844eeb32cacbdeea0e7e677` (`v1.0.4`); preserve source and build provenance |
| libssc and sensor stack | Sensor support | Build from pinned upstream sources and record licences |

Machine-readable support-source pins, tested output hashes, installation
allowlists, and the no-redistribution policy are in
[`firmware/sources.yaml`](firmware/sources.yaml).

## Patch policy

Every patch entry must record:

- original author and origin URL;
- full commit message and DCO trailers;
- base kernel and applicability range;
- whether it is upstream, superseded, local, or rejected;
- physical hardware on which it was tested;
- features and risks it changes;
- exact release where it became unnecessary.

Obsolete patches remain in history for provenance but must not remain in an active
patch series. In particular, the early SP12 DTS using touchscreen GPIOs 51/52 is
known incorrect and must never be applied to a release build.

## Binary provenance

Every binary release must contain or link to:

```text
BUILDINFO.json
SHA256SUMS
kernel configuration
base kernel commit
ordered patch manifest
compiler and linker versions
package version
DTB source and checksum
reproduction instructions
```
