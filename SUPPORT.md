# Support matrix

This matrix describes the tested 2026-08-13 reference build, not every future
release.

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
