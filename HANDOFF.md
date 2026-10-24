# Handoff: SP12 7.3 improvements

Recorded 2026-10-23. Repository: `chropic/sp121-ubuntu-install`.
Continue on `main`; the default-target migration was tested from base `babd4aa`.
The tooling implementation was recorded at `6afb21f`; the branch began at
`dab1a4b` on `main`.

**Current main version:** the target runs `7.3.0-sp12-v7.3-platform`. Read the
[human testing report](docs/testing-2026-10-23.md) and
[sanitized evidence](kernel/experiments/performance-power/on-device-2026-10-23.json)
for verified results, unresolved suspend errors and remaining work.

## User direction and scope

The user supplied the [battery/performance implementation plan](kernel/PERFORMANCE-POWER-ROADMAP.md).
The earlier tooling phase followed **“Keep hardware gates pending; finish repository
tooling.”** The user subsequently authorized on-device testing and operated the
target through boot, restoration and suspend checks. That testing authorization
supersedes the earlier pause; it does not establish hardware or energy acceptance.

Repository tooling is implemented. The full hardware/energy roadmap is not
complete. Use the 7.3 **platform** profile for future experiments. Preserve
historical 7.2 reproduction inputs, existing v7.3 build evidence, recovery
artifacts. The user subsequently selected **7.3 platform as the sole maintained
kernel and default build/installed-system target**, canceled the proposed 7.2
rollback test, and retired new 7.2 work. Historical evidence/recovery copies
remain. No experimental policy starts automatically.
Camera enablement, hibernation, charge limits, compiler optimization and
binary publication remain out of scope. Default-target selection is authorized;
known feature issues and fresh-installer validation are tracked separately.

## Implemented

- Default wrappers and boot-config example now select 7.3 platform. The ISO
  builder requires and inspects its image package/build record, embeds a target
  bundle, and preserves the separate stock Ubuntu live bootstrap. New
  `scripts/install-kernel-target` installs/checks that exact native ARM64 target
  before fallback setup. Fallback defaults to 7.3 and rejects a bootstrap DTB
  that differs from its packaged DTB. Fresh live installation is still untested;
  its validation is separate from the maintained kernel's on-device results.

- `scripts/sp12-power-measure` is the shell entry point for
  `kernel/power-measure.py`: read-only `inventory`, timed `sample`, and `compare`,
  each requiring an explicit new output directory.
- Inventory collects allowlisted interfaces, package versions and policy/boot
  hashes. Missing/unreadable data is explicit. Device names are replaced with
  ordinal labels where identifiers could leak; firmware contents, network data,
  raw logs and command lines are excluded.
- Sampling defaults to five seconds and emits versioned JSON metadata and CSV,
  with battery energy in Wh, direct/estimated power separately labeled, and
  CPU/GPU/thermal/idle/PSI telemetry. Comparisons reject charging/unknown supply
  state, missing energy, gaps, counter resets/discontinuities and flat gauges.
- Comparison emits JSON and Markdown; acceptance remains pending repeated trials,
  equivalent-work and latency review, and hardware tests.
- Candidate preparation/build Python tools and their shell wrappers accept
  `--manifest`. Wrappers now default to `v7.3` and `platform`; archived 7.2
  reproduction requires an explicit legacy selection.
  Alternate manifests require experiment identities, hash-pinned inputs and full
  config. A preparation receipt binds the canonical manifest/profile; build
  verification checks source/config identity and the actual kernel release.
  Serial packaging and native ARM64 header procedures remain in place.
- [Experiment guide](kernel/experiments/performance-power/README.md) documents
  collection, workload freezing, isolated workstreams, rollback records and the
  manifest contract. Example conditions/settings are templates with placeholders,
  not frozen workloads. No experimental kernel manifests or candidate builds
  were introduced.
- [Status record](kernel/experiments/performance-power/status.json) separates
  documentation, software validation, hardware gates and energy acceptance.

## Default-target migration validation (current)

Repository checks and ShellCheck pass: 15 candidate tests, eight collector tests,
seven installer-package safety tests, 12 ESP fault tests and installer/fallback
integration fixtures. All 105 checked local documentation links resolve. The
actual locally built 7.3 image package passed the new bundle verifier, including
its 8,490 AArch64 modules. No new ISO or fresh native installation was performed;
live bootstrap and complete installation/recovery validation remain pending.
The migration builds on `babd4aa`; Git history records its implementation commit.

## Repository tooling validation (earlier phase)

`scripts/check-repository` passed after the final implementation changes:
15 candidate tests, 8 collector tests, existing installer/fallback tests and
12 boot-space tests. `git diff --check` passed. Shellcheck was unavailable;
shell syntax checks passed. No kernel compilation, candidate package inspection
or privileged target initramfs verification was performed for this change.

A read-only live inventory and a ten-second collector smoke capture completed.
Comparison of the smoke capture with itself correctly reported invalid energy
measurement because the battery gauge did not move. This is only a software
smoke test and provides no battery or performance acceptance evidence.

Private temporary captures were written outside Git:

- `/tmp/sp12-power-inventory-20261023`
- `/tmp/sp12-power-smoke-20261023`
- `/tmp/sp12-power-report-smoke-20261023`

These paths may disappear; do not depend on their persistence or commit them
without manual privacy review. Sanitized observations are in `status.json`.

## Current device state and completed gates

The current target is Ubuntu 26.04.1 LTS on **7.3.0-sp12-v7.3-platform**.
The maintained boot-sync helper/hooks are installed and configuration explicitly
selects that release and its matching DTB; the ESP is read-only. The legacy
helper/absent-configuration issue described in the earlier handoff was repaired.

Completed during operator-assisted testing:

- 7.2 warm reboot and cold boot, including display and input checks.
- Complete original-state archive verification and independent backup transfer.
- Original 7.2 loader/payload/hooks/configuration restoration rehearsal and reboot.
- Fresh 7.3 initramfs/module audit, boot from 7.2 and cold boot, with matching
  active payload hashes and confirmed display, keyboard, touchpad and touchscreen.
- Built-in speaker playback, intelligible microphone recording/playback and
  physical volume-button checks; original output volume restored.
- Local accelerometer, light and compass event capture; all four orientations
  and changing light/heading readings observed. Calibration and desktop policy
  behavior were not independently checked.
- Stylus motion, varying pressure, both tilt axes, proximity, tip contact and
  one side-button event path; application inking/calibration remain unverified.
- Bluetooth audio connection and short playback; connected A2DP/LDAC node
  verified. Reconnection, sustained playback and post-suspend checks remain pending.
- USB-C-to-HDMI video on both tested ports (`DP-2`, then `DP-1`) with the built-in panel
  also active. No HDMI/DP audio playback route appeared despite monitor audio
  capability; monitor-speaker playback remains blocked.
- Three short deep suspend/resume cycles with working physical input/display,
  but repeated touchscreen resume and Wi-Fi PCIe errors. Wi-Fi reconnection took
  about 16–22 seconds in the two completed measured reconnects.

USB recovery media is operator-confirmed available; USB boot/restoration was not
exercised. The installed-system restoration rehearsal is a distinct result.
The 7.3 initramfs differs from the historical snapshot but passed fresh checks
and actual boots. Preserve historical build evidence unchanged.

These checks do not establish a clean suspend pass, energy savings or feature-wide
hardware acceptance. See the [testing report](docs/testing-2026-10-23.md) for the
RTC discrepancy, remaining boot messages, tested boundaries and recovery checksum.
Raw captures remain private; publish only reviewed, sanitized evidence.

## Next steps

1. Recheck branch and live target state. Finish repeated 7.3 warm reboots;
   do not resume the canceled 7.2 rollback test. Follow
   [maintenance](docs/maintenance.md) and [recovery](docs/recovery.md).
2. Diagnose repeated suspend errors under matched conditions. Wait for complete
   Wi-Fi reconnection between cycles. Existing 7.2 comparisons are insufficient
   to confirm a 7.3 PCIe regression. Longer suspend/energy tests remain pending.
3. Complete application inking, desktop auto-rotation/brightness behavior, Bluetooth
   reconnection/sustained playback, missing HDMI/DP audio routing and load/thermal
   checks. Video through both USB-C ports passed. Enumeration or
   service activity is not a functional pass.
4. Freeze actual workload inputs, versions, conditions and latency instrumentation;
   collect the installed policy as the baseline and establish one policy owner.
   Then diagnose and trial one observed issue at a time with snapshot/restore.
5. Follow the roadmap's workstream ordering. sched_ext has no selected revision:
   pin/review one ARM64-compatible `scx_lavd` commit and verify BPF requirements
   before any manual trial. Timer comparisons start at 1000 vs 250 Hz with
   scheduler/preemption held constant. BORE remains conditional on sched_ext results.
6. Require at least three interleaved baseline/candidate pairs per scenario.
   Accept only ≥10% energy improvement beyond noise, ≤10% extra completion time
   and ≤5% p95 latency regression, with no functional/storage/watchdog/resume
   regressions. Combine only independently accepted changes. Unperformed work
   stays explicitly pending. Run `scripts/check-repository` after relevant
   tooling changes.

The user then asked to progress toward moving from Ubuntu 26.04 to 26.10. Keep
this work separate from the kernel/energy results and use the release-upgrade
gates below before changing the device's Ubuntu release.

## Ubuntu 26.10 preparation and current status

The read-only first-stage checker is `scripts/sp12-upgrade-preflight`. It
checks release metadata, release track, package state, holds, APT simulation,
third-party sources, filesystem space, GRUB settings, configured kernel/DTB,
ESP payloads and fallback EFI type. It is read-only and never initiates an
upgrade. It has fixture coverage for ARM/deb822 sources, pending updates,
third-party repositories and missing release metadata. The latest fix makes
unreadable root-only initramfs comparisons manual checks rather than false
content failures.

The user directed that recovery-media readiness be bypassed for other checks.
That was followed for read-only inspection only; it does not waive the need for
independent full-system and user-data backups before an actual OS upgrade.
Current detailed status and remaining gates are in [docs/release-upgrade.md](docs/release-upgrade.md).

On 2026-10-23, read-only SSH checks confirmed Ubuntu 26.04.1 on
`7.3.0-sp12-v7.3-platform`, initially `Prompt=lts`, held `iio-sensor-proxy`, three
pending current-release package updates, and no supported 26.10 upgrade-tool
entry in stable metadata. The target has only its internal disk attached and
no noninteractive sudo for the SSH user. The actual 26.10 removal plan,
full-system backup and separate user-data backup remain outstanding. The
operator subsequently ran the staged preflight as root. It returned `NOT
READY` with three failures: `Prompt=lts`, no supported stable 26.10 upgrader
metadata, and `grub2/no_efi_extra_removable=false`. It passed the running and
configured 7.3 kernel checks, exact kernel/initramfs/DTB ESP comparisons,
fallback loader presence and ARM64 EFI validation. The output lists three
pending current-release package updates, the held sensor package, third-party
sources, 186 GiB root free space and 810 MiB ESP free space. The actual 26.10
removal plan remains unavailable. The root-only initramfs comparison passed;
full-system backup and separate user-data backup remain outstanding.
A follow-up SSH check again confirmed `Prompt=lts` and the read-only ESP mount.
The root-only cache listing returned no `/var/lib/update-manager/meta-release*`
files. Read-only inspection found only an empty
`/var/lib/ubuntu-release-upgrader/release-upgrade-available` marker and no
`/var/log/dist-upgrade` files. Installed update-manager source confirms the
stable endpoint and cache path; the root preflight fetched the endpoint and
found no supported 26.10 entry, so stale local metadata does not explain that
failure. A second direct fetch listed versions only through 26.04.1 LTS.
No-cache headers showed `200 OK` with `Last-Modified: 2026-09-11` for the
stable interim-release endpoint on 2026-10-24, indicating upstream metadata
publication has not caught up with the 2026-10-15 release.
Ubuntu's public `stonking` package catalogue lists iio-sensor-proxy
3.9-1ubuntu1 (versus held 3.8-1), grub2-common 2.14-2ubuntu3 (versus installed
2.14-2ubuntu2.1), and shim-signed 1.59+15.8-0ubuntu2. The sensor package and
GRUB changes require compatibility and hook review; these public versions are
not a device-specific release-upgrader plan. The operator confirmed the 7.3
initramfs matches its ESP copy.
Release-note-specific checks show `/lib32` absent, `/` directly on `/dev/sda2`
as ext4, no active crypttab entry or crypt mapper, `/boot` sharing ext4, and a
vfat ESP. The TPM-backed FDE and dangling-`/lib32` upgrade blockers do not
apply. The 26.10 switch to Rust `cp`, `mv` and `rm` still needs a scratch-ESP
test of boot-sync staging and rollback before relying on those helpers.
Repository endpoint checks found no R `stonking-cran40` or Waydroid `stonking`
metadata (HTTP 404); Waydroid is not installed. Tailscale's `stonking` index
advertises ARM64, and VS Code/ChatGPT stable indexes respond; VS Code's index
advertises ARM64. This does not prove package compatibility. Keep the R source
disabled unless its vendor publishes a supported 26.10 suite.
The preflight script was missing from the target at its first invocation; it is
now staged at `/tmp/sp12-upgrade-preflight-20261023` and its SHA-256 matches
the repository copy. The root run is complete and is documented above.

A non-rebooting reinstall of `shim-signed`, `grub2-common` and
`grub-efi-arm64` was performed. Despite temporarily setting
`grub2/update_nvram=false`, the shim hook created an Ubuntu NVRAM entry and
changed BootOrder. The operator restored the original NVRAM state and restored
the ESP byte-for-byte from the same-disk image. Follow-up confirms the original
fallback loader/payload hashes, ARM64 EFI format, read-only ESP mount and
pre-rehearsal BootOrder. Do not reboot: shim-to-custom-GRUB boot behavior has
not been tested. This rehearsal is complete as a package-write/restore check,
not as a boot test or full-system recovery test.

The installed scripts explain the side effect: GRUB's postinst honors its
`no_efi_extra_removable` and `update_nvram` debconf values, but shim invokes
`grub-multi-install` directly without those arguments. Exact package-script
findings, hashes and preflight results are recorded in `docs/release-upgrade.md`.
The release upgrade remains not ready; do not run `do-release-upgrade` yet.

Fallback protection work: read-only inspection confirmed shim's two install
calls go through `/usr/lib/grub/grub-multi-install`, whose helper forwards
arguments to `grub-install`; no separate `efibootmgr` invocation exists in the
shim postinst. Added a local `dpkg-divert` guard and installer in the repository.
The guard forces `--no-extra-removable --no-nvram`, handles `--help` without
delegating, fails closed if either option is unavailable, and has a reversible
remove path. The installer is dry-run by default and does not write the ESP or
NVRAM. Both files and the updated preflight are staged under
`/tmp/sp12-grub-fallback-guard`; hashes match the repo copies, syntax checks
passed, and the dry run reported the intended diversion with no changes. The
operator then applied the staged installer as root. It confirmed the diversion,
preserved helper and support for both safety options; it did not run GRUB or
write the ESP/NVRAM. The subsequent root preflight passed the verified-guard
check, clearing the prior fallback-path failure. The operator then reinstalled
`shim-signed`, `grub2-common` and `grub-efi-arm64` with the guard active. All
three packages configured and both GRUB installer runs reported success.
Post-rehearsal checks confirm the ESP is read-only, `BootCurrent=0003`,
`BootOrder=0001,0004,0000,0002` with no Ubuntu entry, all six fallback/SP12
payload hashes are unchanged, and the diverted helper verifies. The guarded
package-hook rehearsal is complete; firmware boot compatibility remains
untested. The earlier accidental helper `--help` invocation left all six
recorded ESP hashes unchanged; NVRAM was not checked at that time. It was
captured before the guarded package rehearsal and confirmed unchanged afterward.

During that inspection, the package helper was mistakenly invoked with
`--help`. It proceeded to `grub-install --help` while the ESP was mounted
read-only. Follow-up checks confirmed the six recorded ESP payload hashes are
unchanged and the ESP remains read-only. NVRAM could not be inspected through
noninteractive sudo at that time; the operator later captured it before and
after the guarded package rehearsal, confirming the expected state remained
unchanged. Full details are recorded in `docs/release-upgrade.md`.

Preparation runbook now separates actions possible before metadata publication
from the gated upgrade sequence. The operator set `Prompt=normal`; it does not
start an upgrade. The runbook retains the guarded root command in case the
setting must be repeated, followed by an ordinary 26.04 APT simulation that
must be reviewed before applying updates. It also specifies scratch-ESP
uutils testing, explicit GRUB/shim loader-preservation work, backup and
recovery requirements, and stop/go checks once stable metadata advertises the
26.10 `UpgradeTool`. The release track was changed to `Prompt=normal`; the
three reviewed ordinary updates were applied later, as recorded below.

The operator has since set `Prompt=normal`; the latest root preflight confirms
it and reduces the failed checks to one: no supported stable 26.10 upgrader
metadata. The local GRUB fallback guard has now been installed and verified;
six manual gates remain. Review of the actual 26.10 GRUB/shim maintainer
scripts remains a manual gate until those target packages are available.
After refreshing APT indexes, the operator reviewed the `full-upgrade`
simulation and applied its three upgrades (`ubuntu-pro-client`,
`ubuntu-pro-client-l10n`, and `chatgpt`), with no removals or new packages.
Ten phased packages remain deferred. The proposed/applied packages did not
include kernel, GRUB, shim or the held sensor package. The latest preflight
reports no current-release updates pending. Current `resolute` R and Waydroid
indexes refresh, which does not prove support for `stonking`. See the latest
output and suite distinction in `docs/release-upgrade.md`.

### Remaining Ubuntu 26.10 handoff gates

Before starting the release upgrade:

1. Make and verify independent full-system and user-data backups; test the
   recovery route. The ESP image is not a full-system backup.
2. Resolve the held `iio-sensor-proxy` against the local sensor fork/build and
   the actual target plan; preserve and retest the sensor integration.
3. Review compatibility of R, ChatGPT, Tailscale, VS Code and Waydroid sources.
   R and Waydroid lacked 26.10 suite metadata in recorded checks; Waydroid is
   not installed.
4. Test ESP boot-sync staging and rollback on a scratch ESP with 26.10 Rust
   `cp`, `mv` and `rm`.
5. When stable metadata advertises a supported `UpgradeTool`, rerun preflight
   and inspect the actual device upgrade plan. Check kernel/recovery/SP12 hook
   retention, removals, repository changes, prompts and required free space.
6. Review the target 26.10 GRUB/shim maintainer scripts and confirm their
   hooks still pass through the local diversion guard.
7. Validate firmware boot through the custom GRUB using a safe boot/recovery
   procedure. The guarded package reinstall passed but did not test firmware
   boot compatibility.

Do not use `-d` or start `do-release-upgrade` until the stable metadata is
present and these gates are closed. See [docs/release-upgrade.md](docs/release-upgrade.md)
for the detailed status and commands.
