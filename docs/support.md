# Support matrix

Support depends on the exact kernel, DTB, firmware and userspace setup. A boot
result does not establish support for every peripheral.

## Linux 7.3 candidate

The platform profile has booted on the supported SP12 and reports
`7.3.0-sp12-v7.3-platform`. Both platform and camera profiles pass full
image/module/package builds. Target installation and initramfs inspection pass;
rollback and broader hardware regression testing remain pending.

The camera profile keeps sensor, CCI, PHY, CAMSS and privacy-LED nodes disabled.
Capture has not been demonstrated. RTC, suspend, volume buttons, DP audio and
charge-limit changes require their own runtime tests. Read the
[port evidence](../kernel/ports/v7.3/README.md) for exact scope.

| 7.3 observation | Result and limit |
|---|---|
| Boot, root filesystem, Wi-Fi/SSH | Running on the platform candidate; no failed systemd units |
| Internal display and GPU | eDP connected; headless EGL reports Freedreno Adreno X1-45, OpenGL 4.6 and ES 3.2; visual quality and sustained rendering untested |
| Keyboard, touchpad, touch, pen | Input devices enumerate; physical interaction untested |
| Battery and CPU scaling | Main battery reports energy; SCMI policies expose frequencies; discharge and throttling untested |
| Bluetooth | Controller enumerates; pairing and traffic untested |
| RTC | Both clocks readable; Surface RTC is about six hours ahead of PMIC RTC; accuracy/persistence unresolved |
| Boot warnings | Early GPU firmware lookup failures recover later; UFS RPMB registration, audio and PMIC deferred-probe warnings need follow-up |

See the [sanitized boot report](../kernel/ports/v7.3/validation/boot-smoke.json).
The test device still has a legacy sync hook pinned to 7.2. Package/initramfs
updates must wait until that pin and hook are deliberately migrated; they could
otherwise replace the trial ESP set with 7.2.

## Historical working reference

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
