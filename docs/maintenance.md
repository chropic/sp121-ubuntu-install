# Maintain an installed system

Keep a [recovery set](recovery.md) before changing boot files or power policy.

## Power and battery

The reference policy reduced one light active-discharge workload from about
13.5–13.8 W to a five-sample 5.08 W average; this is not a battery-life promise.
Preview, then deliberately apply:

```bash
/opt/sp12-linux/scripts/install-power-policy
sudo /opt/sp12-linux/scripts/install-power-policy --apply
```

It installs measured CPU/GPU limits, SCMI module loading, AC/battery event
handling, and the GNOME automatic-brightness override. Reference-owner USB
receiver and dock IDs are omitted; autosuspend external devices only after
testing wake, input, and networking.

```bash
systemctl is-enabled sp12-power-tune.service
systemctl show sp12-power-tune.service -p Result -p ExecMainStatus
cat /sys/devices/system/cpu/cpufreq/boost
cat /sys/class/devfreq/3d00000.gpu/min_freq
cat /sys/class/devfreq/3d00000.gpu/max_freq
cat /sys/module/pcie_aspm/parameters/policy
powerprofilesctl get
```

The successful `Type=oneshot` service normally becomes inactive; require
`Result=success` and `ExecMainStatus=0`. Do not add
`After=power-profiles-daemon.service`, which creates an ordering cycle because
that daemon starts after `multi-user.target`. For frequent AC use, prefer the
Surface UEFI battery-limit option; never write Linux thresholds reporting unknown
or zero ranges.

## Check ESP space before updates

The EFI System Partition (ESP), normally mounted at `/boot/efi`, is separate
from `/boot` on the Linux root filesystem. Free space on `/` does not mean the
ESP has room for a boot update. A safe update stages new payload files alongside
the active files, so it needs temporary free space as well.

From this repository's root, inspect usage without changing anything:

```bash
findmnt /boot/efi
df -h /boot /boot/efi
scripts/sp12-esp-space
```

The report shows the mounted ESP's capacity and top-level directory usage. Review the active
boot set and retained recovery set before removing anything. The sync helper
skips unchanged payloads, checks space for changed files plus a safety margin
before remounting read-write, and reports the required and available space when
an update cannot fit.

An interrupted older update may have left `sp12/vmlinuz.new`,
`sp12/initrd.img.new` or `sp12/dtb.new`. After reviewing the report, remove only
those recognized staging files with:

```bash
sudo scripts/sp12-esp-space --apply-stale-only
scripts/sp12-esp-space
```

Cleanup validates the existing active set and marker, refuses symlinks, and never
removes active payloads, recovery sets, firmware or Windows boot files. It is not
a general ESP cleaner. New installations also provide the same command at
`/usr/local/sbin/sp12-esp-space`.

If space is still insufficient, stop the boot update and keep the current
payload. Removing packages from `/boot` does not necessarily reclaim ESP space.
Do not delete a recovery set to make an update fit. Back up the ESP and recovery
media before planning partition changes; do not resize a mounted ESP. See
[ESP troubleshooting](troubleshooting/README.md#efi-system-partition-is-full).

## Update safely

Verify the maintained sync hook and its exact kernel/DTB configuration before
package or initramfs updates. Older installations may still have a legacy hook
that pins 7.2. The [23 October testing](testing-2026-10-23.md) migrated the trial
device and verified its explicit 7.3 selection; recheck other installations.

Before changing Ubuntu releases, read the
[release-upgrade compatibility and readiness assessment](release-upgrade.md).

Ordinary package updates are permitted, but the ESP payload remains pinned:

```bash
sudo apt update
sudo apt upgrade
uname -r
dpkg-query -W 'linux-image*' 'linux-headers*' 2>/dev/null
```

Never purge the running or retained recovery kernel. Avoid `-dbg` kernel packages
unless symbol debugging is intentional; they consume several gigabytes.

Changing the custom kernel means installing its exact image and headers,
generating its initramfs, choosing its matching DTB, updating both values in the
ESP sync configuration, synchronizing and comparing all three files, preserving
the previous recovery set, rebooting, and completing the [hardware checks](hardware-tests.md). Generic APT
kernel symlinks must never choose the ESP payload automatically. See [the boot
synchronization design](development.md#boot-synchronization).
