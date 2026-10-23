# ARM64 configuration migration

Both profiles start with the byte-identical historical configuration
`kernel/config/config-7.2.0-rc7-sp12-extra-camera`. `listnewconfig` and
`olddefconfig` run with `ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-` on the
patched 7.3 source. Exact resulting configs and full `scripts/diffconfig` outputs
are retained; compiler-derived values are part of the pinned config bytes.

## Deliberate changes

- `LOCALVERSION` is `-sp12-v7.3-platform` or `-sp12-v7.3-camera`.
  `LOCALVERSION_AUTO` remains disabled, keeping releases distinct from recovery.
- The platform profile disables `VIDEO_QCOM_CAMSS`; its source/DT dependencies
  are present only in the camera profile. The camera profile retains CAMSS,
  OV13858, OV02C10 and `PHY_QCOM_MIPI_CSI2` as modules. Its board camera nodes
  remain disabled independently of module compilation.
- `CRYPTO_DEV_QCOM_RNG=m` moved upstream to `HW_RANDOM_QCOM`; the new option is
  explicitly set to `m`, preserving the `qcom-rng` driver. Accepting the new
  default of `n` would have silently removed that module.
- Upstream now makes `CRYPTO_DEV_QCE` depend on `BROKEN` because the accelerator
  races secure-world ownership and is slower than the CPU. Its disappearance
  and that of dependent algorithm choices is retained; `BROKEN` is not enabled.
  Existing CPU crypto remains available. This is an intentional upstream safety
  restriction, not an accidentally lost root-storage driver.

## Required reference features

The following important settings retain their reference values: ARM64, EFI,
EFI stub, initrd, EXT4, VFAT, UFS/UFS-QCOM, DRM/MSM and eDP panel, QCOM SCM,
RPMH/command DB, SMEM/SMP2P/RMTFS, Q6V5 PAS, SCMI CPU frequency, Surface
Aggregator/bus/registry/hub, Surface HID/keyboard, ATH12K, Bluetooth QCA, QFPROM,
PMIC GLINK, Type-C, X1E80100 sound and the optional Surface RTC. Many are modules,
including UFS and DRM. A target-generated initramfs must include the required
root-storage, firmware and display dependencies; successful cross-compilation
does not verify that initramfs or target boot.

New architecture, MM, crypto-library and selected common dependency symbols use
their 7.3 Kconfig defaults. New unrelated device drivers defaulting to `n` remain
disabled. Newly selected Qualcomm clock/interconnect/pinctrl dependencies and
generic library defaults are recorded in the complete diff rather than removed
to make the result look smaller. Existing multi-platform coverage is preserved.
Renamed/removed unrelated legacy drivers, architecture implementation symbols,
compiler capability values and default-driven built-in/module changes are
visible in the diff reports. They do not replace the preserved SP12 settings.

Debug DWARF5, BTF, module BTF and the existing optional module-signing policy are
preserved. The build generates a local signing key in its ignored output tree;
that does not enable or validate Secure Boot. No private signing material belongs
in Git or the candidate provenance report.

## Reproducible review inputs

- `validation/platform-listnewconfig.txt`, `validation/platform-config-diff.txt`
- `validation/camera-listnewconfig.txt`, `validation/camera-config-diff.txt`
- `manifest.json` pins each final config's SHA-256 and the ordered series.

The build helper verifies the exact base, full resulting source tree and final
config before invoking make. It refuses changed config/source bytes rather than
treating `rtc-surface.c` presence as proof that a candidate tree is correct.
Cross-built Debian package metadata/content and target initramfs/install behavior
require separate inspection; the hardware and installer gates are unchanged.
