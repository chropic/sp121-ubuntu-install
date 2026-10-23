# Linux 7.3 port

**Platform boot verified on the supported SP12.** The device reports
`7.3.0-sp12-v7.3-platform`. Installation and target-generated initramfs checks
pass. Both profiles build full images, modules and Debian packages; matching
native ARM64 headers compile an external module, which was not loaded.

This remains a development candidate. Rollback, broad hardware regression and
camera capture tests are incomplete. The installer and default kernel
reproduction path retain their 7.2 inputs.

## Profiles and evidence

| Profile | Changes beyond upstream 7.3 | Validation |
|---|---|---|
| `platform` | Volume GPIOs, Surface RTC, SP12-scoped suspend workaround, DP audio, charge NVMEM | Image/EFI zboot, 8,490 modules, DTB/schema, inspected image/native-header packages; physical boot |
| `camera` | Platform plus reconciled PHY, CAMSS, sensor drivers, SoC nodes and bindings | Image/EFI zboot, 8,492 modules, DTB/schema, four binding examples, image/native-header packages |

Camera sensor, CCI, PHY, CAMSS and privacy-LED nodes **remain disabled**. The
existing 7.2 device's idle MCLK4 source reads 19.2 MHz despite its 12 MHz DT
request; active sensor clocking and capture remain untested. The staged 19.2 MHz
request is not a capture-proven fix. RTC, suspend, volume, DP audio and charge
interfaces need separate runtime tests; do not guess charge thresholds.

- [Software results](validation/software-results.json): check scope and remaining gates.
- [Boot smoke test](validation/boot-smoke.json): SSH, Wi-Fi, display enumeration,
  headless Freedreno EGL, RTC discrepancy and remaining boot warnings.
- [Platform package inspection](validation/packages.json) and
  [build provenance](validation/platform-buildinfo.json): exact hashes and architectures.
- [Source decisions](source-review.md), [configuration](config-review.md),
  [RTC/suspend](rtc-suspend-review.md), [camera bindings](camera-bindings-review.md): detailed review.
- [Manifest](manifest.json): ordered patches, configs and all 37 vendor dispositions.
- [Aggregate audit](aggregate-audit.json): 25 verified reference postimages and hunks.

The manifest and build reports are fixed snapshots of their build stage; their
pending hardware fields are historical. The software results and boot report
above record subsequent verification without changing the build's input hashes.

## Authenticated base

Linux `v7.3`, commit `c03c1a14507dfaf8b856c2608f9ac216021fc222`, tag object
`091b06388b117fefdcb63336ac09956a4914b961`. The extracted official tarball matches
the signed tag tree `30fd2ef82912c26cf3a58ad0ba6afc375fa851ac`.

Tag and tarball signatures verify against the published Kernel.org keys;
[verification evidence](validation/source-verification.txt) records fingerprints
and results. The [source review](source-review.md#source-and-publication-identity)
explains attribution and remaining publication provenance. Original source
notices and vendor patch metadata are preserved; regenerated patches add no
invented author or sign-off.

## Reproduce preparation and builds

Use Linux, Git, Python 3.9+, an ARM64 GCC/binutils toolchain and the normal kernel
build dependencies, including make, flex, bison, OpenSSL/ELF headers, bc and
pahole. Debian packaging also needs dpkg-dev, debhelper, fakeroot, rsync, cpio
and kmod. DeviceTree checks use an isolated `dtschema` environment. Actual
versions used here are recorded in `validation/toolchain.json`.

Run from the repository root. Use disk-backed storage with room for the broad
module/debug configuration; a small RAM-backed `/tmp` is insufficient. These
commands create fresh source and output paths:

```sh
mkdir -p /var/tmp/sp12-port
git clone --depth 1 --branch v7.3 --single-branch \
    https://github.com/torvalds/linux.git \
    /var/tmp/sp12-port/reproduce-linux-7.3-platform
kernel/prepare-tree --kernel v7.3 --profile platform \
    --source /var/tmp/sp12-port/reproduce-linux-7.3-platform \
    --output /var/tmp/sp12-port/reproduce-build-7.3-platform
kernel/prepare-tree --kernel v7.3 --profile platform \
    --source /var/tmp/sp12-port/reproduce-linux-7.3-platform \
    --output /var/tmp/sp12-port/reproduce-build-7.3-platform --apply
kernel/build-packages --kernel v7.3 --profile platform \
    --source /var/tmp/sp12-port/reproduce-linux-7.3-platform \
    --output /var/tmp/sp12-port/reproduce-build-7.3-platform \
    --cross-compile aarch64-linux-gnu- --jobs 12
```

Preparation defaults to dry run. It verifies the exact clean base, input hashes,
ordered application in a temporary index, and config destination. It refuses to
overwrite an existing config. Linked Git worktrees are supported. `--output`
keeps the source unconfigured for an out-of-tree build; do not run in-tree make
first on that source.

The build helper verifies the complete patched source tree and exact reviewed
config, including extra untracked files, using disposable indexes. It builds
ARM64 Image, the selected EFI zboot payload, modules and the SP12 DTB, then packages serially with
`KBUILD_DEBARCH=arm64` and candidate version `7.3-1~sp12candidate1`. Use
`--build-only` for compilation without packaging. It never installs packages.
It records output hashes and compiler/linker identity in `sp12-buildinfo.json`
in the output directory. Cross-build packaging uses upstream's `nokernelheaders`
profile: target headers are built natively against the completed kernel's exact
`Module.symvers`. This avoids target-libcrypto linkage and host BTF executables
inside ARM64 headers. The optional debug package is omitted while debug data
remains in the build output. A successful package command alone is not boot evidence.

The helper uses the Debian package revision as the Kbuild version and keeps one
build timestamp across compilation and packaging. An explicit
`KBUILD_BUILD_TIMESTAMP` takes precedence over `SOURCE_DATE_EPOCH`; otherwise it
records the current UTC time. This prevents serial packaging from needlessly
regenerating all module BTF. It does not assert bit-for-bit reproducibility:
local module-signing keys and other build inputs must also be controlled.

For the camera profile, use a separate pristine 7.3 checkout and output directory
and select `--profile camera` in both preparation and building. The profiles
must not be mixed. Their config localversions are respectively
`-sp12-v7.3-platform` and `-sp12-v7.3-camera`.

## Remaining gates

The test device's legacy boot-sync helper remains pinned to 7.2. Migrate its
configuration and helper before package/initramfs updates, which could otherwise
restore the old ESP payload. The new repository helper has passed isolated fault
tests; it has not been installed on that device. No further reboot or suspend
test was performed while the operator was away.

1. Prove cold boot, warm reboot and rollback to the retained known-good payload.
2. Complete the [hardware tests](../../../docs/hardware-tests.md), including
   feature-specific RTC, volume, suspend, DP audio and charge-interface checks.
3. Before enabling camera nodes, validate clock/power behavior, media topology,
   real capture, privacy indication and repeated start/stop.
4. Independently validate live-installer boot, installation, handoff, updates and
   recovery before changing its matched kernel/DTB inputs.
5. Resolve recorded provenance gaps and complete release checks before binary
   publication. Successful builds do not promote a supported release.

The supplied notes and patch audit remain verbatim in [`research/`](research/).
They are research inputs, not executable instructions or new support claims;
their relative links refer to their original location.
