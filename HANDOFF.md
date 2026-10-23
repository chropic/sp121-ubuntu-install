# Handoff: SP12 7.3 improvements

Recorded 2026-10-23. Repository: `chropic/sp121-ubuntu-install`.
Continue on branch `7.3-improvements`; implementation commit: `6afb21f`.
The branch was created from `main` at `dab1a4b` and pushed to origin.

## User direction and scope

The user supplied the [battery/performance implementation plan](kernel/PERFORMANCE-POWER-ROADMAP.md).
They subsequently instructed: **“Keep hardware gates pending; finish repository tooling.”**
They requested the work be pushed to `7.3-improvements`, then requested this
handoff on the same branch. Do not interpret the handoff request as permission
to resume deployment or hardware experiments.

Repository tooling is implemented. The full hardware/energy roadmap is not
complete. Use the 7.3 **platform** profile for future experiments. Preserve
historical 7.2 reproduction inputs, existing v7.3 port evidence, recovery
artifacts and installation defaults. No experimental policy starts automatically.
Camera enablement, hibernation, charge limits, compiler optimization and
release/default-kernel promotion remain out of scope.

## Implemented

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
  `--manifest`. Wrappers require `--kernel v7.3`; existing defaults are preserved.
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

## Validation performed

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

## Hardware state observed in this session

Recheck live state before acting; these are observations, not promises about the
next session. The local machine identified as Surface Pro 12in 1st Edition,
ARM64, Ubuntu 26.04.1 LTS, running **7.2.0-sp12-extra-camera**. A matching module
tree and installed 7.3 platform files were visible. Historical v7.3 evidence
records a successful earlier boot, but it does not establish the current boot.

The installed `/usr/local/sbin/sp12-sync-boot` hash was
`56665776ff137bc6c4f30c535a79f25f7f6faf7567bd85e5e1dec08ba20ddfa8`, matching
the legacy helper. `/etc/sp12-linux/boot.conf` was absent. This issue remains
unresolved. The maintained installer's **dry run** succeeded using:

```sh
scripts/install-boot-sync --kernel-release 7.2.0-sp12-extra-camera \
  --dtb /boot/dtb-7.2.0-sp12-extra-camera
```

No `--apply` was used. The kernel and DTB hashes matched the historical baseline;
the initramfs was unreadable without root. Active ESP/loader, complete recovery
set and restoration capability were not verified. Service-state queries failed
in the execution environment; do not infer those services were inactive.

No root installation, reboot, recovery restoration, boot payload change, policy
change, scheduler deployment or package update was performed.

## Next steps

1. Inspect branch/status and read the roadmap, experiment guide and status record.
   Repository-only reviews/fixes may continue while hardware gates stay pending.
   Run `scripts/check-repository` after relevant changes.
2. When the user explicitly resumes hardware work, coordinate with the operator
   to verify external recovery media and the complete recovery set, including
   loader, kernel/initramfs/DTB, hooks and configuration. Verify matching module
   and initramfs contents and active ESP hashes before repairing boot sync or
   updating packages. Follow [maintenance](docs/maintenance.md) and
   [recovery](docs/recovery.md); do not select a release from symlinks alone.
3. Record successful cold boot, warm reboot and complete restoration separately.
   Keep deployment experiments blocked until these pass.
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
   stays explicitly pending.

This handoff itself does not create another chat, launch an agent or schedule work.
