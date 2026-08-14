# Hardware verification

Run these tests after every kernel or DTB change. “A node exists in the DTB” is
not a hardware pass.

## Display and GPU

```bash
glxinfo -B
```

Expected highlights are direct rendering, Freedreno, and Adreno X1-45.

## Audio

```bash
wpctl status
aplay -l
arecord -l
```

Test both playback and recording at a conservative volume.

## Sensors

```bash
monitor-sensor
```

Rotate the tablet and cover/uncover the light sensor. Confirm accelerometer,
ambient light, and compass events.

## CPU frequency scaling

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

## IRIS video codec

```bash
readlink -f /sys/bus/platform/devices/aa00000.video-codec/driver
```

The expected driver is `qcom-iris`. Install only firmware that the kernel actually
requests; do not copy a collection of unrelated Windows firmware.

## Cameras

```bash
media-ctl -p
v4l2-ctl --list-devices
ls -l /dev/video* /dev/media* 2>/dev/null
```

Run a camera-link configuration script only after CAMSS, CSIPHY/CSID/VFE, sensor,
media, and video entities exist.

## Experimental checks

- Connect a USB-C DP/HDMI display before testing DisplayPort audio.
- Test volume buttons with `libinput debug-events`.
- Save all work before testing suspend, and prove multiple resume cycles.
- Inspect charge-limit attributes read-only until their valid range is established.
