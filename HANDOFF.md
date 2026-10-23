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

The user also requested a separate Ubuntu 26.10 upgrade assessment. It is not an
instruction to run a release upgrade; keep that assessment separate from these
hardware results.
