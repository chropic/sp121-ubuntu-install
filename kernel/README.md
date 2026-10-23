# Kernel builds

Linux **7.3 platform** is the sole maintained default for builds and installed
targets. The 7.2 inputs are frozen historical/recovery material, not a maintained
line. Select `--kernel v7.2-rc7` explicitly only to reproduce that archive.
Build tools prepare and package sources but never install the resulting kernel.

| Kernel | Entry point | Status |
|---|---|---|
| Linux 7.3 | [Build and validation guide](ports/v7.3/README.md) | Main maintained version; boot/cold boot and feature tests recorded; known suspend/Wi-Fi/DP-audio issues remain |
| Linux 7.2-rc7 | Recipe below | Archived reproduction only; no new maintenance or rollback test planned |

The 7.3 `platform` profile carries the reviewed board/RTC/power additions. The
separate `camera` profile also compiles the reconciled media stack with camera
runtime nodes disabled. See the build and validation guide for evidence and commands.

## Build the default 7.3 target

Follow the [7.3 preparation/build recipe](ports/v7.3/README.md#reproduce-preparation-and-builds),
including its toolchain requirements. Both wrappers now select `v7.3` and
`platform` when those options are omitted. Its documented output directory is
`/var/tmp/sp12-kernel/reproduce-build-7.3-platform`; the Debian image package is
created in its parent directory. Keep the generated `sp12-buildinfo.json` with
that exact package. The [installer guide](../docs/install.md) uses both to verify
and bundle the installed-system kernel. Native ARM64 headers remain a separate
procedure; no package is installed by the build tools.

## Reproduce the 7.2 reference

The archived release is based on Linux `v7.2-rc7`, commit
`db2ddb87143519e20a95aa36c60b36107b736a58`.

## Reproduction inputs

- `config/config-7.2.0-rc7-sp12-extra-camera` — byte-identical to the running
  kernel configuration.
- `patches/release/0001-...working-tree.patch` — exact aggregate difference
  between pristine `v7.2-rc7` and the source tree that produced the tested build.
- `patches/vendor/mias/` — the original patch corpus at Gentoo-overlay commit
  `877e0707f816b83ef8ce66a23277febdc2ff6448`, retained for authorship,
  review history, and reconstruction of a clean series.

The aggregate snapshot is presently the reproducible release input. It is not a
claim that one person authored the combined changes. Original authorship belongs
to the metadata in the vendor patches and their upstream submissions.

## Prepare and build

From the repository root, create a clean checkout of the exact base and preview:

```bash
mkdir -p build
git clone --depth 1 --branch v7.2-rc7 --single-branch \
  https://github.com/torvalds/linux.git build/linux-v7.2-rc7
kernel/prepare-tree --kernel v7.2-rc7 --source build/linux-v7.2-rc7
```

Apply only after reviewing the base commit and snapshot hash:

```bash
kernel/prepare-tree --kernel v7.2-rc7 --source build/linux-v7.2-rc7 --apply
kernel/build-packages --kernel v7.2-rc7 --source build/linux-v7.2-rc7
```

Compilation is parallel; Debian packaging is deliberately serial to avoid the
observed DTB installation race. The scripts never install the resulting packages.

Do not distribute a kernel binary without the base reference, aggregate snapshot,
config, original patch corpus, build information, and checksums.

## Patch provenance

`patches/release/` is the exact aggregate difference from pristine `v7.2-rc7`
to the worktree that built `7.2.0-rc7-sp12-extra-camera`, package revision
`7.2.0~rc7-6`. It recreates every tracked modification and required new file
byte-for-byte; generated `.orig` files and the patch-tool `err` file are excluded.
The snapshot is necessary because the tested worktree contained applied and
manually reconciled patches as uncommitted changes. It does not assign their
combined authorship to one person.

`patches/vendor/mias/` contains unmodified files from Mias van Klei's Gentoo
overlay:

```text
repository: https://github.com/miasvanklei/Gentoo-overlay
commit:     877e0707f816b83ef8ce66a23277febdc2ff6448
```

The Surface directory contains hardware enablement; the camera directory holds
the dependency/sensor series considered during the build. Not every patch is
active: some were already present, some conflicted after earlier patches, one
OV13858 patch was deliberately not forced, and unrelated Surface Go work is not
part of this release. Future work should split the release snapshot into a
reviewed series while preserving original authorship and producing the identical
final tree.

## Performance and power measurement

The [gated roadmap](PERFORMANCE-POWER-ROADMAP.md) and
[experiment protocol](experiments/performance-power/README.md) provide read-only
baseline collection, comparisons and optional experiment manifests. Hardware and
feature and energy gates remain pending. Selecting 7.3 as the default does not
establish a clean suspend pass or a physically validated installer release.
