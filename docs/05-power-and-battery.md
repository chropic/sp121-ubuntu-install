# Power and battery policy

The reference policy reduced a light active discharge measurement from roughly
13.5–13.8 W to a five-sample average of 5.08 W. That result is a measurement from
one workload, not a guaranteed battery-life claim.

Preview the policy without changing the system:

```bash
scripts/install-power-policy
```

The installer requires a second invocation with `sudo` and `--apply`. It installs
the measured CPU/GPU limits, SCMI module loading, AC/battery event handling, and
the GNOME automatic-brightness override.

The repository deliberately omits the reference owner's USB receiver and dock
IDs. Autosuspend external devices only after testing each one for reliable wake,
input, and network behavior.

## Verification

```bash
systemctl is-enabled sp12-power-tune.service
systemctl show sp12-power-tune.service -p Result -p ExecMainStatus
cat /sys/devices/system/cpu/cpufreq/boost
cat /sys/class/devfreq/3d00000.gpu/min_freq
cat /sys/class/devfreq/3d00000.gpu/max_freq
cat /sys/module/pcie_aspm/parameters/policy
powerprofilesctl get
```

A successful `Type=oneshot` unit normally becomes inactive afterward. Judge it by
`Result=success` and `ExecMainStatus=0`, not by whether it remains active.

Do not add `After=power-profiles-daemon.service` to the unit. That creates an
ordering cycle because the daemon itself starts after `multi-user.target`.

For frequent AC operation, prefer the Surface UEFI battery-limit option. Do not
write Linux charge-threshold attributes that report unknown or zero ranges.
