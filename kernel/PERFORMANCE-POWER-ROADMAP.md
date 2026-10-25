# SP12 battery and performance implementation plan

Current direction (2026-10-23): 7.3 platform is the sole maintained/default build
and installed-system target. The operator canceled the proposed 7.2 rollback
test. The original planning-state/default-preservation notes below are historical;
see the [current project status](../README.md#support-status) and [testing report](../docs/developer/records/hardware-2026-10-23.md).

## Summary

Implement the supplied roadmap in gated milestones, starting with recovery verification and measurement tooling, then isolated power-management experiments.

Planning inspected remote `main` at `dab1a4b`; the original checkout remains at `53e7f3f`. Pulling is deferred because this session is in Plan mode.

Use the 7.3 `platform` profile as the experimental foundation. Preserve historical 7.2 reproduction inputs, recovery artifacts and existing installation defaults.

## 1. Synchronize and establish safe recovery

- Recheck the working tree and run `git pull --ff-only origin main`. Stop on divergence or conflicting local edits; do not reset them. Record the resulting commit and revalidate any changes since this review.
- Add the supplied roadmap as `kernel/PERFORMANCE-POWER-ROADMAP.md`. Store experiment instructions, manifests and sanitized evidence under `kernel/experiments/performance-power/`.
- Inspect the actual SP12 hardware, running kernel, installed packages, boot hooks, configuration, ESP payload and recovery media.
- Resolve the recorded legacy boot-sync helper issue using the maintained installer with explicit kernel-release and DTB selection. Verify matching kernel, modules, initramfs and DTB before package updates.
- With the operator present, verify cold boot, warm reboot and restoration of the complete recovery set. Block deployment experiments until these pass.

## 2. Implement baseline and experiment tooling

- Add a read-only Python collector, exposed through a shell entry point compatible with the repository’s script checks. Provide `inventory`, timed `sample`, and `compare` commands with explicit output directories.
- Inventory build/package identities and hashes, firmware/Mesa versions, CPUFreq, CPUIdle, thermal interfaces, device runtime PM, battery telemetry, swap, MGLRU and sched_ext. Record missing or unreadable interfaces explicitly.
- Capture the existing power service, udev rules, CPU/GPU limits, ASPM settings, USB autosuspend and power-profiles-daemon state. Treat the installed policy as part of the baseline.
- Produce versioned JSON metadata, timestamped CSV samples and a Markdown comparison report. Include conditions, units, workload identity, failures, recovery instructions and disposition.
- Default to five-second sampling. Use battery energy deltas while unplugged; label current/voltage-derived estimates separately. Invalidate energy comparisons interrupted by charging, missing samples or gauge discontinuities.
- Keep full command lines and raw diagnostic logs private; publish only reviewed, sanitized evidence. Do not collect firmware contents or device/network identifiers.
- Define fixed workloads for screen-on idle, browsing/editing, video, background compilation with interaction, batch completion and suspend. Freeze input files, versions and latency instrumentation before comparisons.

## 3. Execute isolated workstreams

1. **Runtime PM, suspend and CPU behaviour:** diagnose GPU, DSP/audio, radios, USB, UFS, wakeups, idle residency and thermal behaviour. Rank observed failures by measured impact. Trial only supported settings or fixes tied to an observed failure and pinned upstream provenance.
2. **Suspend:** retain the existing workaround initially. Run operator-assisted short cycles before longer unplugged intervals; record wake reasons, RTC behaviour and energy loss per hour. Test peripherals and input reattachment. Change the workaround only in a separately measured candidate.
3. **CPU policy:** compare supported governor settings and conservative frequency caps individually. Snapshot and restore previous values. Establish one policy owner during each experiment; prevent existing services and udev events from reapplying competing settings.
4. **sched_ext:** evaluate one pinned, ARM64-compatible `scx_lavd` revision after checking the running kernel’s BPF requirements. Begin with manual execution; verify registration, clean stop and return to the default scheduler. If compatibility cannot be established, record the blocker rather than substituting an unreviewed scheduler.
5. **Memory and media:** independently evaluate bounded zram configurations and actual video-decoder paths. Measure pressure, stalls, CPU cost, storage activity, dropped frames and energy. Keep kernel, Mesa and application changes separate.
6. **Timer/preemption:** compare 250 Hz against 1000 Hz first, holding scheduler and preemption constant. Evaluate tickless configuration and supported preemption alternatives separately afterward.
7. **Optional BORE:** proceed only after sched_ext results establish a remaining need. Require an exact-version patch and provenance review; test without active sched_ext.
8. **Combined candidate:** combine only accepted changes and repeat the complete measurement and hardware matrix.

Do not introduce blanket autosuspend, forced ASPM, invented energy tables, voltage changes or unverified thermal settings.

## 4. Candidate interfaces and verification

- Add an explicit optional `--manifest` argument to candidate preparation/build tooling and its wrappers. Preserve existing default behaviour.
- Experimental manifests pin the base commit, ordered patches, complete resulting configuration, hashes and unique release/package identifiers. Retain full source/config verification, serial packaging and native ARM64 header procedures.
- Keep historical build manifests and evidence immutable. Runtime experiments use separate settings records; no experimental policy starts automatically.
- Add fixture-based tests covering missing telemetry, battery selection, unit conversion, charging transitions, counter resets, privacy filtering and comparison validity.
- Extend candidate tests to reject incorrect hashes, modified source/configuration and mismatched manifests. Verify existing platform/camera defaults remain compatible.
- Run `scripts/check-repository` and relevant tooling tests. Kernel candidates additionally require compilation, package inspection, target initramfs verification and operator-assisted boot tests.
- Record documentation, software validation, hardware tests and energy acceptance separately. Unperformed tests remain pending.

## Acceptance and defaults

- **Battery-first:** require at least 10% lower energy for equivalent work, allowing at most 10% longer completion time and 5% worse p95 latency. Differences must exceed observed measurement noise.
- Start with at least three interleaved baseline/candidate pairs per scenario. Extend trials when variation prevents a conclusion; retain the baseline when benefit remains inconclusive.
- Match brightness, radios, peripherals, workload, battery charge range, starting temperature and background activity. Collect intrusive traces separately.
- Any new storage error, scheduler watchdog event, failed resume or functional regression rejects the candidate regardless of energy results. Preserve thermal protections.
- Hardware testing is operator-assisted. Repository tooling must remain useful when target access is unavailable, with hardware gates explicitly pending.
- Camera enablement, hibernation, charge limits, compiler optimization and release/default-kernel promotion remain outside this implementation.
