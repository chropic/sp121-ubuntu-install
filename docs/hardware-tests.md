# Verify hardware

Run these tests after every kernel or DTB change; a DTB node is not a hardware
pass.

For completed checks and remaining work on the current 7.3 platform kernel, see
the [23 October 2026 testing results](testing-2026-10-23.md). The checklist below
is a procedure, not evidence that each feature passed.

| Area | Command or test | Expected result / caution |
|---|---|---|
| Display/GPU | `glxinfo -B` | Direct rendering, Freedreno, Adreno X1-45 |
| Audio | `wpctl status`; `aplay -l`; `arecord -l` | Test playback and recording at conservative volume |
| Sensors | `monitor-sensor` while rotating and covering the light sensor | Accelerometer, ambient-light, and compass events |
| Video | `readlink -f /sys/bus/platform/devices/aa00000.video-codec/driver` | `qcom-iris`; install only firmware the kernel requests |
| Cameras | `media-ctl -p`; `v4l2-ctl --list-devices`; `ls -l /dev/video* /dev/media* 2>/dev/null` | Configure links only after CAMSS, CSIPHY/CSID/VFE, sensor, media, and video entities exist |

Inspect CPU frequency policies:

```bash
for policy in /sys/devices/system/cpu/cpufreq/policy*; do
    printf '%s cpus=%s driver=%s governor=%s min=%s max=%s\n' \
        "${policy##*/}" \
        "$(cat "$policy/affected_cpus")" \
        "$(cat "$policy/scaling_driver")" \
        "$(cat "$policy/scaling_governor")" \
        "$(cat "$policy/scaling_min_freq")" \
        "$(cat "$policy/scaling_max_freq")"
done
```

The tested system exposes policies for CPUs 0–3 and 4–7 after loading
`scmi_perf_domain` and `scmi_cpufreq`.

For experimental features: attach a USB-C DP/HDMI display before testing
DisplayPort audio; use `libinput debug-events` for volume buttons; save work and
prove multiple suspend/resume cycles; and inspect charge-limit attributes
read-only until their range is established.


Record the exact kernel, DTB and observed result. Compare against the
[support matrix](support.md); a successful boot is not a pass for every feature.
