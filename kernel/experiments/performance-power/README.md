# Performance and power experiments

The [roadmap](../../PERFORMANCE-POWER-ROADMAP.md) defines acceptance and scope.
Use the 7.3 **platform** profile for future experiments. The historical 7.2
inputs and the v7.3 port evidence remain immutable. Installation defaults are
unchanged. No experimental service starts automatically.

## Current gates

See [status.json](status.json) for separately recorded software, hardware and
energy status. The operator requested that hardware gates remain pending on
2026-10-23. Do not deploy candidates until the complete recovery set, cold boot,
warm reboot and restoration tests pass. Existing evidence of a prior 7.3 boot
is historical; this session observed the running 7.2 kernel.

Before package updates, use the maintained `scripts/install-boot-sync` with an
explicit kernel release and DTB. Its dry run succeeded for the running 7.2
selection, but the initramfs was unreadable to this user. The installed helper
matches the legacy hash and no boot.conf is present. This issue is unresolved.
Have the operator verify matching kernel, module tree, initramfs contents, DTB,
active ESP and loader before applying the installer. Record hashes and exact
release, not assumptions from symlinks. Follow [recovery](../../../docs/recovery.md)
and [maintenance](../../../docs/maintenance.md). Verify the backup of the
complete loader/payload/hooks/configuration set, as well as bootable external
recovery media. Restoring the ESP payload alone is not proof of complete
configuration restoration. Record actual test results; leave unperformed tests
pending. No reboot, root installation or recovery restoration is automated here.

## Collector

Run from the repository; Python 3 standard library only. Sysfs/procfs and
allowlisted package/service queries are read-only. Output directories must be
new, explicit paths. Directories are private by default (0700; files 0600).
Never use the evidence directory as the destination for unreviewed captures.

```sh
scripts/sp12-power-measure inventory --output /tmp/sp12-inventory
# Copy conditions.example.json into private storage and replace every placeholder.
scripts/sp12-power-measure sample --duration 600 --interval 5 \
  --conditions /tmp/frozen-conditions.json --workload screen-idle-v1 \
  --output /tmp/sp12-baseline-01
scripts/sp12-power-measure compare --baseline /tmp/sp12-baseline-01 \
  --candidate /tmp/sp12-candidate-01 --output /tmp/sp12-comparison-01
```

`inventory.json` records kernel/package identities, boot/configuration hashes,
firmware version (when exposed by DMI), Mesa packages, policy/helper hashes,
service/profile state, CPUFreq (kHz), CPUIdle (usage/time in kernel units),
GPU/devfreq (Hz), thermals (millidegrees Celsius), runtime PM, autosuspend,
ASPM, battery, swap without paths, PSI, MGLRU and sched_ext availability.
Missing/unreadable attributes carry status/errno. A failed service query means
unknown state, not inactive. Policy files are hashed rather than exported;
review their contents privately to identify policy ownership. GPU/devfreq and
runtime devices use ordinal labels to avoid exposing device/network identifiers;
map those labels privately if diagnosis needs device-specific attribution.
Firmware contents, serials, command lines, logs and network data are excluded.

`sample` emits versioned metadata and timestamped CSV. It selects a present
system battery, excluding device-scoped and disconnected HID supplies. Ambiguous
batteries require `--battery SUPPLY`. Supply names are not exported. Battery
energy in micro-Wh is converted to Wh; direct power in micro-W is preserved in W
with the driver's sign. Current × voltage produces `estimated_power_w` only;
charge counters never become measured energy. CPU/GPU frequency, thermals and
PSI are included in each row's `telemetry_json`. Intrusive tracing stays separate.
The full inventory is taken once per run, before the timed interval.

Comparison requires identical nonempty conditions and workload IDs, complete
captures, at least two samples, discharging state and known disconnected external
power throughout. Missing/nonfinite energy, gaps above 1.5× interval, unordered
timestamps, rising/reset counters, >1% full-gauge changes and physically implausible
energy steps invalidate comparison. `--max-power` sets the documented plausibility
ceiling (default 100 W); freeze it before trials. Flat gauge readings cannot prove
a saving. Very small gauge steps require longer captures. Suspend-inclusive elapsed
time exposes suspend as a sampling gap, which invalidates ordinary awake comparisons.

Reports deliberately leave acceptance pending: one pair does not establish noise,
equivalent work, completion latency or hardware reliability. Save ≥3 interleaved
baseline/candidate pairs per scenario. Extend when variation is inconclusive.
Require ≥10% energy improvement beyond observed noise, ≤10% completion increase,
and ≤5% p95 latency regression. Reject any storage error, watchdog, failed resume
or functional regression. Review results and publish only sanitized evidence.
The collector does not execute workloads or compute application latency for you.

## Freeze workloads before measurement

Use these workload IDs only after all inputs, application/tool versions, scripts,
durations, event timestamps and latency instrumentation are frozen and hashed in
a private workload record. The example conditions file is a schema aid, not a
ready measurement protocol. Record actual brightness, radios, peripheral types,
charge range, initial temperature, background services and policy owner.

| Scenario | Fixed procedure and additional evidence |
| --- | --- |
| Screen-on idle | Fixed brightness and desktop, 10-minute settling followed by 10-minute capture; no input. |
| Browsing/editing | Local frozen pages/document; replay a pinned input sequence for 10 minutes; measure input-to-present p95 with one frozen method. |
| Video | Hash one local clip, fixed player/version/resolution/codec and 10-minute playback; record actual decoder API/backend, CPU time and dropped frames. |
| Compile with interaction | Same source commit, toolchain, clean build, job count and scripted interaction sequence; measure completion and interaction p95, PSI and storage activity. |
| Batch completion | Fixed input and command hash, start/end event instrumentation and exact output equivalence check; capture the full job, including baseline overhead equally. |
| Suspend | Operator-assisted short cycles first, then fixed longer unplugged intervals; record pre/post energy, elapsed RTC/wall time, wake reason and peripheral/input reattachment. Ordinary sample comparisons are invalid across suspend. |

## Isolated workstreams

Create a settings record for every trial using `settings.example.json`. Keep exact
sysfs paths and original values privately. Snapshot before any write, define an
explicit restore command and verify restored readback even after a failed trial.
Do not introduce blanket autosuspend, forced ASPM, voltage changes, invented energy
tables or unverified thermal limits. Keep thermal protections enabled.

1. Diagnose GPU, DSP/audio, radios, USB and UFS runtime state, wakeups, CPU idle
   residency and temperature. Rank observed failures by energy impact. Trial only
   supported changes linked to an observed failure and exact upstream provenance.
2. Keep the existing suspend workaround initially. Test wake reasons and RTC,
   input/peripheral reattachment and energy/hour. Change the workaround alone.
3. For governor/frequency trials, enumerate supported governors/frequencies first.
   Establish one policy owner: snapshot the installed power service, udev event
   rules and power-profiles-daemon state; operator-reviewed temporary inhibition
   must cover service restarts and AC/udev events. Stop a trial if values drift.
   Restore the complete previous policy, then verify it after AC events.
4. sched_ext remains blocked until one exact `scx_lavd` commit and ARM64 toolchain
   are reviewed, kernel BPF/BTF/JIT and sched_ext requirements checked, and manual
   registration, clean stop, default-scheduler return and watchdog handling pass.
   No scheduler revision is selected or downloaded by this implementation.
5. Trial bounded zram separately, with memory limits, original swap state and
   rollback; measure pressure, stalls, CPU and storage. Confirm actual video
   decoder backend separately; kernel, Mesa and application changes stay isolated.
6. Compare HZ=1000 with HZ=250 holding scheduler, NO_HZ and preemption constant;
   then evaluate supported tickless/preemption changes separately. Any generated
   config needs olddefconfig review and compilation before hardware use.
7. BORE is optional, only after sched_ext demonstrates remaining need. Require an
   exact-version patch with reviewed provenance and no active sched_ext.
8. Combine only accepted changes, then repeat the complete hardware/energy matrix.

## Alternate candidate manifests

Both Python tools and shell wrappers accept an explicit optional `--manifest`.
Shell wrappers require `--kernel v7.3`; historical defaults remain unchanged.

```sh
kernel/prepare-tree --kernel v7.3 --profile platform --source /path/to/linux \
  --output /path/to/build --manifest /path/to/experiment.json
# Review dry run, then repeat with --apply.
kernel/build-packages --kernel v7.3 --profile platform --source /path/to/linux \
  --output /path/to/build --manifest /path/to/experiment.json
# Python verification without compiling:
python3 kernel/build-candidate.py --source /path/to/linux --output /path/to/build \
  --manifest /path/to/experiment.json --verify-only
```

Alternate manifests require `experiment_schema: 1`, a full `base_commit`, an
ordered `series` of repository-relative path/SHA-256 entries, and explicit
`profiles.platform.config` pointing at the **complete resulting configuration**
with its SHA-256. Pin upstream provenance for every changed patch separately.
Each profile requires a unique `kernel_release` such as
`7.3.0-sp12-exp-hz250-r1` and Debian `package_version` such as
`7.3-1~sp12exphz250r1`. Config must contain the corresponding
`CONFIG_LOCALVERSION="-sp12-exp-hz250-r1"` and disable LOCALVERSION_AUTO.
Choose a fresh ID whenever any input changes; do not overwrite published inputs.

The preparation receipt binds the entire canonical manifest and selected profile.
Build verification rejects a mismatched receipt, input hash, base, complete config
or source tree. Actual kernel release is checked before compilation; build info
hashes the selected manifest. Serial packaging and native ARM64 header procedures
remain in effect. Use `kernel/inspect-candidate.py`, inspect the target initramfs,
and complete operator boot tests independently. A software pass is not a hardware
or energy pass. No uncompiled experiment manifests are presented as accepted
candidates here. Keep new runtime settings outside historical port manifests.

Run `scripts/check-repository` for fixture and integration checks. `--root` is a
fixture filesystem override for the collector; live package/service queries run
only for `/`. Full command lines and raw diagnostic logs belong only in private
storage. Conditions and workload labels are operator supplied: review them for
sensitive data before publication, too.
