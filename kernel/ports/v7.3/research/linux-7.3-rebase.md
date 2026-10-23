# Linux 7.3 feasibility and rebase plan

Research date: 2026-10-20. Project baseline: `6f0de3d` (`main`).
Status: **feasible to begin porting; build and hardware compatibility unproven**.

## Decision and scope

Yes: porting this project's downstream kernel changes onto Linux `v7.3` is
technically plausible. Upstream now includes several SP12 enablement changes.
This is a kernel patch-stack port, not a Git rebase of this installer repository
onto the Linux repository. Keep Ubuntu 26.04 ARM64 as the userspace target.

Do not change the installation default yet. The current reproduction scripts
intentionally require `v7.2-rc7`; the aggregate snapshot fails `git apply --check`
on pristine `v7.3`. No 7.3 kernel, packages, DTB, installer, or hardware tests have
been produced by this research.

## Sources and reproducible evidence

Primary sources inspected:

- [Kernel.org release index](https://www.kernel.org/): lists 7.3, released
  2026-10-18. This establishes availability, not SP12 compatibility or LTS status.
- [Linux v7.3 tree](https://github.com/torvalds/linux/tree/v7.3): cloned and
  inspected at commit `c03c1a14507dfaf8b856c2608f9ac216021fc222`;
  tag object `091b06388b117fefdcb63336ac09956a4914b961`.
  The tag contains a signature; cryptographic verification was not performed.
- [Upstream SP12 DTS](https://github.com/torvalds/linux/blob/v7.3/arch/arm64/boot/dts/qcom/x1p42100-microsoft-sp12in.dts),
  [SAM registry](https://github.com/torvalds/linux/blob/v7.3/drivers/platform/surface/surface_aggregator_registry.c),
  [SCM allowlist](https://github.com/torvalds/linux/blob/v7.3/drivers/firmware/qcom/qcom_scm.c),
  and [panel database](https://github.com/torvalds/linux/blob/v7.3/drivers/gpu/drm/panel/panel-edp.c).
- [Camera clock driver](https://github.com/torvalds/linux/blob/v7.3/drivers/clk/qcom/camcc-x1p42100.c),
  [hamoa.dtsi](https://github.com/torvalds/linux/blob/v7.3/arch/arm64/boot/dts/qcom/hamoa.dtsi),
  [purwa.dtsi](https://github.com/torvalds/linux/blob/v7.3/arch/arm64/boot/dts/qcom/purwa.dtsi),
  and the corresponding CAMSS, PHY, RTC, and sensor source files.
- This repository's [kernel inputs](../../kernel/README.md),
  [patch inventory](../../kernel/patches.yaml),
  [reference manifest](../../release/reference/BUILDINFO.json),
  [support matrix](../../SUPPORT.md), and [source policy](../../SOURCES.md).

The accompanying [patch audit](linux-7.3-patch-audit.json) records patch hashes,
both applicability checks, diagnostics, source identities, and comparison hashes.
Each vendor patch was checked **independently** against pristine 7.3, without
applying it. The unrelated Intel Surface Go 2 patch was excluded.

| Independent check result | Patches | Meaning |
|---|---:|---|
| Forward only | 16 | Text applies; dependencies and correctness still require review |
| Reverse only | 3 | Exact patch text can be removed from upstream; exclude duplicate changes |
| Neither direction | 16 | Context or implementation differs; inspect source before deciding |
| Both directions | 1 | Ambiguous deletion patch; inspect the resulting tree |
| Excluded | 1 | Intel Surface Go 2 work outside SP12 scope |

A failed reverse check does not prove a change is missing. A clean forward check
does not prove the patch belongs in the tested release or that a series builds.

The original base tag was also fetched and resolved to the expected commit
`db2ddb87143519e20a95aa36c60b36107b736a58`. Its 20 existing files touched by
the snapshot were materialized in a disposable directory, then the snapshot
was successfully applied, producing all 25 changed/new files. These postimages
were compared against 7.3. This reconstructs the snapshot's tracked changes; it
does not reproduce the complete kernel build or authenticate the installed DTB.

## Findings and patch dispositions

Numbers below refer to filenames in `kernel/patches/vendor/mias/`, not an approved
application order. The aggregate snapshot is the authoritative tested input.

| Area | Observed in pristine 7.3 | Proposed action |
|---|---|---|
| Surface 0001: QSEECOM | Exact reverse check passes | Drop duplicate from new active series |
| Surface 0002: SAM registration | Exact reverse check passes | Keep upstream registration; port RTC additions separately |
| Surface 0007: initial SP12 DTS/Makefile | Exact reverse check passes | Use upstream board file, not another copy |
| Surface 0003: Sharp panel | `SHP:15a7`, `LQ120P1JX51`, and matching delay already present | Drop duplicate despite both text checks failing |
| Camera 0002: X1P42100 CAMCC driver | Driver and compatible present; implementation differs | Retain upstream; audit functional differences before dropping vendor version |
| Camera 0010–0011: CAMCC DT nodes | Hamoa CAMCC node and Purwa compatible override present | Retain upstream nodes; reconcile instead of replaying |
| Surface 0004–0005: RTC | Driver absent; both patches individually apply forward | Review driver/API and add as a distinct optional feature |
| Surface 0006: suspend workaround | Patch applies; upstream defaults `d3_closes_handle` to true | Review global impact on all OF Surface devices; do not blindly carry |
| Surface 0008: volume GPIOs | Up/down still 8/6; snapshot uses 6/8 | Carry reviewed board correction; validate physical buttons |
| Surface 0010–0011: DP audio and charge NVMEM | Additions absent in upstream board file; present in snapshot | Port separately; preserve experimental runtime status |
| Camera 0003–0009: PHY/CAMSS | New MIPI CSI2 PHY files absent; several patches apply, others conflict | Resolve dependencies and reconcile against actual snapshot before enabling cameras |
| Camera 0012/0014/0015 and Surface 0012 | Snapshot contains CCI/CAMSS/board camera additions missing from upstream tree | Port as one dependency-reviewed camera series, including bindings |
| Camera 0018–0024: OV13858 | Neither-direction checks fail; large sensor delta remains | Reconstruct actual reconciled snapshot; do not force rejected sensor patches |
| Camera 0025–0026: OV02C10 | Both independently apply forward | Review and retain if required by selected camera series |
| Camera 0017: Surface Go 2 | Unrelated Intel support | Exclude |

### Vendor corpus is not the tested series

Reconstruction exposed differences that must be resolved before selecting patches:

- Surface 0009's revised display/backlight regulators are **not** in the snapshot:
  it retains the 5,000,000 ns PWM and `vreg_panel_en` wiring, matching upstream
  7.3 in this area. Do not add the regulator rewrite merely because it applies.
- Surface 0013's `disable-rfkill` property and Surface 0014's explicit board IRIS
  override are absent from the reconstructed board file. This observation alone
  says nothing about inherited video support or runtime decoding.
- Surface 0015 deletes the board's 512 MiB CMA reservation, but the snapshot
  **retains** that reservation. Both forward and reverse checks pass on upstream;
  this result is ambiguous and must not select a memory-layout change.
- Both upstream and reconstructed board files use touchscreen GPIOs 38/48.
  Never reintroduce the historical GPIOs 51/52.

Do not replace 7.3 files with old snapshot postimages: that would discard upstream
changes. The comparison identifies intent to port, not a replacement patch.

## Implementation plan and acceptance gates

### 1. Freeze inputs and reconcile provenance

- [ ] Verify the upstream signed 7.3 tag against a trusted maintainer key; record
  the verified commit, patch/config hashes, toolchain, and build architecture.
- [ ] Preserve the existing snapshot, config, vendor originals, reference hashes,
  and old preparation path. Create separate 7.3 inputs and a complete ordered
  manifest with author, origin, DCO, dependencies, disposition, and test status.
- [ ] Map every aggregate hunk to vendor/upstream/local intent. Resolve the
  display, CMA, RF-kill, IRIS, and sensor discrepancies above explicitly.

Gate: every retained change has a reason; upstream duplicates and rejected work
are excluded. Stop on unresolved regulator, reserved-memory, firmware, power-domain,
or device-tree wiring conflicts; never force application.

### 2. Prepare a minimal 7.3 platform candidate

- [ ] Start from upstream SP12 support. Port only reviewed changes required to
  preserve the reference's working daily-driver features. Separate RTC, suspend,
  charge-limit, DP audio, and camera changes into reviewable feature groups.
- [ ] Retain camera dependencies together where needed, but gate camera enablement
  separately from boot/storage/display testing. Cameras were never capture-proven.
- [ ] Derive an ARM64 config from the exact old config; run `listnewconfig` and
  `olddefconfig` with `ARCH=arm64`, inspect `scripts/diffconfig`, and review new
  defaults, removed symbols, built-ins, modules, and initramfs requirements.
- [ ] Review UFS/root filesystem, EFI, DT, Qualcomm clocks/regulators/interconnects,
  DRM/Adreno, remoteproc/firmware, SCMI, SAM/input, Wi-Fi, audio, and sensors.

Gate: a deterministic ordered series applies to the pinned 7.3 commit without
rejects, missing dependencies, duplicate nodes, or unreviewed config changes.

### 3. Build, validate DT, and package

- [ ] Add an explicit 7.3 selection to `kernel/prepare-tree` with exact base,
  snapshot/series, and config checks. Preserve its default dry run and refusal of
  dirty/wrong-base trees; support Git worktrees deliberately if using them.
- [ ] Update `kernel/build-packages`: its required `rtc-surface.c` is currently a
  proxy for the old snapshot, and must not define whether a minimal 7.3 tree is
  valid. Check selected series/config/base and expected outputs instead.
- [ ] Build ARM64 Image, modules, and `qcom/x1p42100-microsoft-sp12in.dtb`; run
  `dtbs_check` and applicable `dt_binding_check`. Include missing/new camera
  bindings if retaining the vendor series; review new warnings against baseline.
- [ ] Keep Debian packaging serial until the prior DTB race is disproven. Inspect
  package architecture, exact release, dependencies, modules, image, headers,
  DTB location, and initramfs contents. Use distinct candidate package versions.
- [ ] Publish no binaries yet; record build inputs, compiler/linker versions,
  package versions, checksums, and corresponding source in a candidate manifest.

Gate: clean build/package/DT validation with no unexplained new failures. A cross
build alone does not validate target Ubuntu package installation or boot.

### 4. Validate installed-system boot and rollback on physical SP12

- [ ] Record model, panel, UEFI/firmware, Ubuntu, current kernel, and payload hashes.
  Keep Secure Boot disabled, a bootable USB, and the known-good recovery set.
- [ ] Stage exact 7.3 packages, matching DTB and generated initramfs without purging
  running/recovery packages. Preserve the current boot configuration and payload.
- [ ] Rehearse recovery before switching the pinned `KVER`/`DTB` pair. Preview the
  existing sync tooling, synchronize the full three-file set, and compare hashes.
- [ ] Cold-boot, warm-reboot, verify `uname -r`, DT model, root storage, display,
  and input; collect redacted `sp12-diagnostics` output and kernel logs.
- [ ] Prove rollback: boot the retained recovery environment, restore the previous
  kernel/initramfs/DTB together using the guide, reboot, and verify old hashes.

Gate: boot and rollback both succeed on the supported physical device. Stop on
missing UFS, display/input loss, firmware crash loops, or unstable power behavior.

### 5. Run hardware regression and feature tests

- [ ] Repeat the reference matrix: storage I/O, display/brightness, GPU rendering,
  Wi-Fi/Bluetooth, Type Cover, touch/pen, conservative-volume audio capture/playback,
  sensor events, battery reporting, SCMI scaling, and actual IRIS decoding.
- [ ] Measure comparable idle/load/charging behavior; inspect faults and thermal
  behavior before reusing power policies. Review firmware requests and userspace
  dependencies against pinned sources; do not import proprietary binaries.
- [ ] Test RTC across reboot/off-time, physical volume buttons, DP audio, and
  repeated suspend/resume separately. Inspect charge-limit interfaces read-only
  until their semantics/ranges are established. Hibernate and EL2 remain excluded.
- [ ] For cameras, verify media graph, sensor probe, links/formats, actual capture,
  privacy indicator behavior, and repeated start/stop. Device nodes are not a pass.

Gate: no regression in previously working features; experimental features remain
explicitly unproven unless each has recorded physical test evidence.

### 6. Integrate installer and promote only after validation

- [ ] Treat live-installer support as a separate target: `scripts/build-installer`
  keeps Canonical's stock kernel and injects a DTB. A 7.3 DTB must not be swapped
  into that older kernel without independent compatibility evidence. Either keep
  its tested pair or design and validate a complete matched live kernel payload.
- [ ] Rebuild and test live boot, target handoff, fresh installation, APT updates,
  reboot, ESP sync hooks, and recovery. An installed-system boot is insufficient.
- [ ] Update `kernel/patches.yaml`, new config/series and hashes,
  `scripts/check-repository`, new candidate provenance, `kernel/README.md`,
  `GUIDE.md`, `README.md`, `SUPPORT.md`, and boot examples for the validated result.
  Keep `release/reference/BUILDINFO.json` and reference notes as historical facts.
- [ ] Run repository checks, ShellCheck, and whitespace checks. Only then decide
  whether to promote 7.3 and publish source/config/checksummed packages under the
  existing builder-only ISO policy.

Gate: installation, recovery, provenance, and feature evidence are complete.
The initial installer candidate was already not hardware-tested; 7.3 does not
remove that existing release gate.

## Next concrete work

Begin phase 1 by decomposing the aggregate's 25-file delta and settling the
observed vendor/snapshot differences. Then construct the minimal 7.3 series.
Compilation and physical validation are outstanding; no completion date or
hardware support claim can be established from applicability checks alone.
