# Ubuntu 26.10 live image

The primary tested configuration is **private live v2**, using the maintained
SP12 kernel in the live session as well as in the target bundle.
The owner confirmed `7.3.0-sp12-v7.3-platform` and reported everything working,
including Wi-Fi and sound. Installation was deferred; no fresh-install or
installed-system recovery pass is claimed.

## Exact tested artifact

| Item | Identity |
| --- | --- |
| Private image | `sp12-ubuntu-26.10-arm64-private-live-v2.iso` |
| Size | 4,971,847,680 bytes |
| SHA-256 | `d550c05575196069bd458f3a97c04acfc6660ceb4cdb5e7b7dab37879b6b6ec5` |
| Ubuntu base ISO SHA-256 | `9242a38c47eb53a5beb153c249d4843e4366f8955e9b972663e4ab7989311e9f` |
| Custom kernel | `7.3.0-sp12-v7.3-platform`, package `7.3-1~sp12candidate1` |
| Kernel package SHA-256 | `20d4cdcff128a7d3264db36b395dcd8b347ff2053ddf2c3e6001df0ea10b969b` |

Canonical's signed checksum list was verified with Ubuntu CD signing key
`843938DF228D22F7B3742BC0D94AA3F0EFE21092`. The original custom package was
inspected against its build record; it was not reconstructed from installed files.
Exact DTB, initramfs, overlay and script hashes are in the image's
`/sp12-buildinfo.txt` and its `.buildinfo` sidecar.

The [candidate record](../../release/CANDIDATE-26.10-private-live-v2.json)
contains audits and operator observations. The original build passed full media,
kernel/module/DTB, casper media identity, dependency, GPT and EFI-partition audits.
Physical ESP, firmware boot entries and ESP mount state compared unchanged.
Cleanup then failed on nested scratch mounts; no build mounts remained visible
in the host namespace. The reusable builder now unmounts recursively and always
compares physical state. That change is regression-tested, not a claim that the
new reusable wrapper produced the byte-identical tested ISO.

## Reproduce a personal build

Use native ARM64 Linux. The apply step needs root for read-only squashfs mounts
and runs in private mount/network namespaces. It does not install host packages,
write the physical ESP, change firmware entries, partition a disk or reboot.
Allow at least 24 GiB scratch space and keep a clean committed source checkout.
Required tools include xorriso, squashfs-tools, initramfs-tools, kmod, gdisk,
efibootmgr, ARM64 GRUB tools, Python, Git and dpkg.

1. Build the [maintained kernel](../../kernel/ports/v7.3/README.md) and keep its
   original package and `sp12-buildinfo.json` together.
2. Download the official Ubuntu 26.10 ARM64 Desktop ISO and verify Canonical's
   signed checksum list and the full ISO hash. The tested source is
   `https://cdimage.ubuntu.com/ubuntu/releases/26.10/release/`.
3. Run `scripts/build-installer --help`. Supply the verified ISO, bootstrap DTB,
   kernel package and build record. This first stage preserves the generic
   live kernel and creates the inspected target bundle. It is **not** the final
   maintained-kernel live image. Use 26.04 only by explicit legacy selection.
4. Run `scripts/build-live-installer --help`. Supply that first-stage ISO and
   its verified hash, the same kernel package/build record, and a new output
   path. The default is a dry run. Add `--apply` with `sudo` only after reviewing
   the inputs. The input ISO must contain the first-stage project and kernel bundle.
5. For a personal image equivalent in device setup to the tested v2, explicitly
   select `--private-machine-support`. Supply your pinned support checkout with
   `--support-source` and a root tree containing the four verified working
   board/topology/UCM files with `--machine-root`. Their pins and hashes are in
   [firmware/sources.yaml](../../firmware/sources.yaml). The default machine root
   is `/`; the tool never copies a home directory or network profiles.
6. Keep the output `.sha256` and `.buildinfo` files. Recheck the full checksum
   after copying to USB, then repeat the physical live tests.

The second stage adds `minimal.standard.live.sp12.squashfs`, rebuilds casper's
initramfs for the custom kernel, selects the matching DTB and explicit layer path,
and refreshes media checks. Original installation layers stay unchanged. Device
files in this live-only layer are not automatically installed into a new target.

Without private support, the builder does not add the personal firmware/board/
audio files and must not claim the same live hardware result. With private
support, the output is local-testing-only and must not be published. No image
from either path is an installation-tested release yet.
