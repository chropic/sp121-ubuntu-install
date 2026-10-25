> Historical record. For the current configuration and test limits, use the
> [project README](../../../README.md). These notes are not a new 26.10 installation pass.

# Support matrix

Support depends on the exact kernel, DTB, firmware and userspace setup. A boot
result does not establish support for every peripheral.

## Maintained default: Linux 7.3 platform

Linux 7.3 platform is the project's main kernel and sole maintained version,
with release `7.3.0-sp12-v7.3-platform`. It is the default for builds and installed
systems. Target installation, initramfs inspection, boot/cold boot and the
physical checks below have passed. Both platform and camera profiles pass full
image/module/package builds. Fresh end-to-end installer validation is tracked
separately in the [installation guide](../../install.md). Linux 7.2 is archived.

The camera profile keeps sensor, CCI, PHY, CAMSS and privacy-LED nodes disabled.
Capture has not been demonstrated. Read the [current physical testing report](hardware-2026-10-23.md)
and [kernel build and validation guide](../../../kernel/ports/v7.3/README.md) for exact scope.

| 7.3 observation | Result and limit |
|---|---|
| Boot, root filesystem, Wi-Fi/SSH | Working on the maintained 7.3 platform kernel; no failed systemd units |
| Internal display and GPU | Operator display checks and Freedreno EGL pass; sustained rendering/thermals remain untested |
| Keyboard, touchpad and touchscreen | Operator checks pass across boots and short resumes; touchscreen resume error `-6` still logs |
| Pen | Motion, pressure, tilt, tip/proximity and one side button report events; app inking/calibration unverified |
| Speakers, microphones, volume buttons | Operator playback, intelligible recording/playback and physical-button checks pass |
| Sensors | Four orientations, ambient light and compass changes captured; calibration and desktop automatic behavior unverified |
| External display | HDMI video through both USB-C ports passes; no HDMI/DP audio route exposed |
| Suspend | Three short deep resumes complete; touchscreen error and Wi-Fi PCIe L2 timeout repeat; completed Wi-Fi activation takes about 16–22 seconds |
| Battery and CPU scaling | Main battery reports energy; SCMI policies expose frequencies; discharge and throttling untested |
| Bluetooth | Connection and short A2DP/LDAC playback pass; reconnection, headset microphone and post-suspend behavior untested |
| RTC | Surface RTC/target UTC agree with independent clock check; PMIC reads about six hours behind; NTP synchronization/persistence unresolved |
| Boot warnings | Early GPU firmware lookup failures recover later; UFS RPMB registration, audio and PMIC deferred-probe warnings need follow-up |

Maintained boot sync is installed on the test device and explicitly selects 7.3
with its matching DTB. Older installations may still have legacy hooks; recheck
before updates. The [original boot report](../../../kernel/ports/v7.3/validation/boot-smoke.json)
is historical, not the current maintenance state.

## Archived 7.2 reference (not maintained)

The following results belong to the **2026-08-13** Ubuntu 26.04 ARM64 setup:
`7.2.0-rc7-sp12-extra-camera`, image package `7.2.0~rc7-6`, Sharp
`LQ120P1JX51` panel, Secure Boot disabled. They are not automatic 7.3 passes.

| Component | State | Notes |
|---|---|---|
| Internal UFS/root | Working | Required before installation |
| Internal display | Working | Sharp `LQ120P1JX51` tested |
| GPU | Working | Freedreno, Adreno X1-45 |
| Wi-Fi/Bluetooth | Working | Requires correct firmware/board data |
| Type Cover/touchpad | Working | Surface Aggregator path |
| Touchscreen/pen | Working | Correct GPIO description required |
| Speakers/microphones | Working | Speaker gain limits are essential |
| Accelerometer/light/compass | Working | Sensor stack required |
| Battery reporting | Working | Do not guess charge-limit values |
| CPU frequency scaling | Working | SCMI modules may need loading |
| IRIS video codec | Working | Exact requested firmware required |
| RTC additions | Static checks passed | Runtime verification required |
| Cameras | DT/kernel support present | Capture not yet proven |
| Suspend | Experimental | Repeated runtime testing required |
| Hibernate | Unsupported | Not validated; swap design insufficient |
| Secure Boot | Unsupported in normal path | Separate experimental design only |
| EL2/KVM | Out of scope | Trades away working daily-driver features |

When opening an issue, include the project release, exact kernel release, device
tree model, DTB checksum, and relevant redacted logs.
