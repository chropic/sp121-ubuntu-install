# Surface Pro 12 Linux guide (Snapdragon ARM64)

Updated 2026-08-13 for the tested Microsoft Surface Pro 12-inch, 1st Edition (`qcom,x1p42100`) running Ubuntu 26.04 ARM64.

## 1. Current tested state

Current kernel and package:

```text
7.2.0-rc7-sp12-extra-camera
linux-image-7.2.0-rc7-sp12-extra-camera 7.2.0~rc7-6
```

Retained recovery kernel:

```text
7.2.0-rc7-sp12-panel
```

Working: Surface DTB/model detection, UFS/root, fallback ESP boot, Wi-Fi, Freedreno GPU acceleration, Sharp `LQ120P1JX51` panel, audio, accelerometer, ambient-light sensor, compass, battery reporting, IRIS video codec, and SCMI CPU frequency scaling.

The extra-feature kernel and DTB contain RTC, suspend, volume-button, DisplayPort-audio, charge-limit NVMEM, CAMSS, OV13858, and OV02C10 support. Static package/DTB checks passed; each physical feature still needs runtime verification before being called reliable. Hibernate is not validated.

Important machine-specific facts:

- Secure Boot is disabled; the fallback loader and custom kernels are unsigned.
- GRUB cannot reliably read this installation's ext4 filesystem. Boot files therefore live on the FAT ESP.
- `/usr/local/sbin/sp12-sync-boot` is pinned to the exact current kernel and versioned DTB. Never replace those paths with generic `/boot/vmlinuz` or `/boot/initrd.img` symlinks.
- The ESP is normally mounted read-only.
- CPU DVFS is present through SCMI. The two policies appear only after `scmi_perf_domain` and `scmi_cpufreq` load.

Primary resources:

- <https://github.com/harrisonvanderbyl/surface-pro-12-inch-linux>
- <https://github.com/miasvanklei/Gentoo-overlay/tree/master/sys-kernel/vanilla-kernel/files/surface>
- <https://discourse.ubuntu.com/t/ubuntu-concept-snapdragon-x-elite/48800>

## 2. Boot architecture—preserve this

```text
Surface UEFI
  -> FAT ESP: /EFI/BOOT/BOOTAA64.EFI
  -> /sp12/vmlinuz
  -> /sp12/initrd.img
  -> /sp12/dtb
  -> Linux mounts ext4 root by UUID
```

Do not depend on EFI NVRAM entries, `efibootmgr`, GRUB reading ext4, or `/boot/grub/grub.cfg` being available after firmware starts GRUB.

Ubuntu may finish installation and then report `EFI variables are not supported on this system`. This does not necessarily mean the OS copy failed. Verify `/target`, `/target/boot/efi`, `/target/etc/os-release`, and `/target/boot` before reinstalling.

## 3. Create the installer

On another Linux system, download the official Ubuntu 26.04 ARM64 Desktop ISO and `SHA256SUMS`, then verify it:

```bash
sha256sum -c SHA256SUMS --ignore-missing
git clone https://github.com/harrisonvanderbyl/surface-pro-12-inch-linux.git
cp surface-pro-12-inch-linux/boot/dtb x1p42100-microsoft-sp12in.dtb
tar -C surface-pro-12-inch-linux -czf surface-pro-12-linux.tar.gz .
sudo apt install -y xorriso
```

Extract and modify the ISO's GRUB configuration:

```bash
xorriso -osirrox on -indev ubuntu-26.04-desktop-arm64.iso \
  -extract /boot/grub/grub.cfg ./grub.cfg
cp grub.cfg grub.cfg.original
sed -i '/^[[:space:]]*linux[[:space:]]/ {/stubble\.dtb_override=true/! s/$/ stubble.dtb_override=true/}' grub.cfg
sed -i '/^[[:space:]]*initrd[[:space:]]/a\    devicetree /casper/x1p42100-microsoft-sp12in.dtb' grub.cfg
grep -n -E 'linux |initrd |devicetree' grub.cfg
```

Build the custom ISO:

```bash
xorriso -indev ubuntu-26.04-desktop-arm64.iso \
  -outdev ubuntu-26.04-desktop-arm64-surface-pro-12.iso \
  -boot_image any replay \
  -update grub.cfg /boot/grub/grub.cfg \
  -update x1p42100-microsoft-sp12in.dtb /casper/x1p42100-microsoft-sp12in.dtb \
  -update surface-pro-12-linux.tar.gz /surface-pro-12-linux.tar.gz \
  -commit
```

Write that ISO to USB. In Surface UEFI (hold Volume Up while powering on), disable Secure Boot and enable USB boot. To boot USB directly, hold Volume Down while powering on.

Before installation, confirm:

```bash
cat /proc/device-tree/model
tr '\0' '\n' < /proc/device-tree/compatible
lsblk
```

Expected model/compatibles include `Surface Pro 12in 1st Edition`, `microsoft,surface-pro-12in`, and `qcom,x1p42100`. Do not install if internal UFS storage is absent. The tested initial install used “Erase disk and install Ubuntu” without encryption; add encryption only after proving the boot path.

## 4. Build the fallback ESP boot path

From the live installer after Ubuntu has populated `/target`:

```bash
findmnt /target
findmnt /target/boot/efi
test -f /target/etc/os-release && cat /target/etc/os-release
sudo install -m 0644 /cdrom/casper/x1p42100-microsoft-sp12in.dtb /target/boot/dtb
sudo mkdir -p /target/opt/surface-pro-12-linux
sudo tar -xzf /cdrom/surface-pro-12-linux.tar.gz -C /target/opt/surface-pro-12-linux
sudo mkdir -p /target/boot/efi/sp12
sudo cp -L /target/boot/vmlinuz /target/boot/efi/sp12/vmlinuz
sudo cp -L /target/boot/initrd.img /target/boot/efi/sp12/initrd.img
sudo cp /target/boot/dtb /target/boot/efi/sp12/dtb
sudo touch /target/boot/efi/sp12/SP12BOOT
```

Record the root UUID:

```bash
sudo blkid -s UUID -o value "$(findmnt -no SOURCE /target)"
```

Bind system directories and verify required GRUB modules:

```bash
for d in dev proc sys run; do
  sudo mount --rbind "/$d" "/target/$d"
  sudo mount --make-rslave "/target/$d"
done
sudo chroot /target test -f /usr/lib/grub/arm64-efi/fat.mod
sudo chroot /target test -f /usr/lib/grub/arm64-efi/linux.mod
sudo chroot /target test -f /usr/lib/grub/arm64-efi/search_fs_file.mod
```

Create `/target/tmp/sp12-fat.cfg`, replacing `YOUR_ROOT_UUID`:

```grub
insmod part_gpt
insmod fat
insmod search_fs_file
search --no-floppy --file --set=root /sp12/SP12BOOT
linux /sp12/vmlinuz root=UUID=YOUR_ROOT_UUID ro clk_ignore_unused pd_ignore_unused cma=128M efi=noruntime quiet splash console=tty0 stubble.dtb_override=true
initrd /sp12/initrd.img
devicetree /sp12/dtb
boot
```

Build and install the standalone ARM64 fallback loader:

```bash
sudo mkdir -p /target/boot/efi/EFI/BOOT
sudo chroot /target grub-mkstandalone --format=arm64-efi \
  --modules="part_gpt fat search search_fs_file linux" \
  --output=/boot/efi/EFI/BOOT/BOOTAA64.NEW \
  boot/grub/grub.cfg=/tmp/sp12-fat.cfg
sudo chroot /target grub-file --is-arm64-efi \
  /boot/efi/EFI/BOOT/BOOTAA64.NEW && echo ARM64-EFI-OK
sudo cp -a /target/boot/efi/EFI/BOOT/BOOTAA64.EFI \
  /target/boot/efi/EFI/BOOT/BOOTAA64.EFI.old 2>/dev/null || true
sudo mv /target/boot/efi/EFI/BOOT/BOOTAA64.NEW \
  /target/boot/efi/EFI/BOOT/BOOTAA64.EFI
sync
```

Rebuild `BOOTAA64.EFI` only if its embedded boot logic or the root UUID changes. Kernel, initramfs, and DTB updates only require replacing the fixed `/sp12/*` payload.

## 5. First-boot platform support

Verify the system:

```bash
cat /proc/device-tree/model
uname -r
lsblk
findmnt /boot/efi
ls -lh /boot/efi/sp12
```

Install common tools and Harrison's firmware overlay:

```bash
cd /opt/surface-pro-12-linux
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y git curl wget python3 python3-pip zstd build-essential \
  cmake meson ninja-build pkg-config libudev-dev libgudev-1.0-dev \
  systemd-dev libpolkit-gobject-1-dev libgtk-3-dev alsa-utils \
  v4l-utils mesa-utils pciutils
sudo cp -a ./lib/. /lib/
sudo update-initramfs -u -k all
```

### Wi-Fi

```bash
cd /opt/surface-pro-12-linux
sudo bash ./fixwifi.sh
ls -lh /lib/firmware/ath12k/WCN7850/hw2.0/board.bin
```

Rebuild and stage the exact active initramfs; do not use a generic symlink.

### Audio

```bash
sudo apt install -y git curl cmake make gcc g++ alsa-ucm-conf alsa-utils
cd /opt/surface-pro-12-linux
sudo git pull --ff-only
sudo cp -a ./lib/. /lib/
sudo bash ./installaudio.sh
```

The Surface topology should exist at:

```text
/lib/firmware/qcom/x1e80100/X1P42100-Microsoft-Surface-Pro-12in-tplg.bin
```

The user audio session must be able to read the Surface UCM file:

```bash
sudo chmod 0644 /usr/share/alsa/ucm2/Qualcomm/x1e80100/Surface12in-HiFi.conf
systemctl --user restart pipewire.service pipewire-pulse.service wireplumber.service
wpctl status
aplay -l
arecord -l
```

Mode `0600` caused the practical audio failure on this machine; `0644` restored sound. If kernel logs show `bus clsh`, open `alsamixer`, mute `SpkrLeft CPS` and `SpkrRight CPS`, then reboot.

### Sensors

Build `libssc` first:

```bash
sudo apt install -y git meson ninja-build pkg-config libqmi-glib-dev \
  libglib2.0-dev libprotobuf-c-dev protobuf-c-compiler protobuf-compiler \
  gobject-introspection
cd /tmp
git clone https://codeberg.org/DylanVanAssche/libssc.git
cd libssc
meson setup _build --prefix=/usr/local --buildtype=release
meson compile -C _build
sudo meson install -C _build
sudo ldconfig
pkg-config --modversion libssc
```

Then install Harrison's stack:

```bash
cd /opt/surface-pro-12-linux
sudo bash ./installsensors.sh
systemctl status hexagonrpc.service iio-sensor-proxy.service
monitor-sensor
```

Confirmed: accelerometer, ambient light, and compass.

## 6. Current extra-feature kernel

### Build rules

Required build packages:

```bash
sudo apt install -y git build-essential bc bison flex libssl-dev libelf-dev \
  libdw-dev libncurses-dev dwarves pahole zlib1g-dev rsync cpio kmod \
  dpkg-dev fakeroot python3 debhelper gawk
```

For a clean base:

```bash
mkdir -p ~/src
cd ~/src
git clone --depth=1 --branch v7.2-rc7 \
  https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git linux-7.2-sp12
cd linux-7.2-sp12
cp "/boot/config-$(uname -r)" .config
make olddefconfig
scripts/config --set-str SYSTEM_TRUSTED_KEYS ""
scripts/config --set-str SYSTEM_REVOCATION_KEYS ""
make olddefconfig
```

Compile in parallel but package serially; parallel `bindeb-pkg` produced a DTB installation race:

```bash
make -j"$(nproc)"
make -j1 bindeb-pkg LOCALVERSION=-sp12-extra-camera
```

Use a disposable worktree for patching. Validate every patch with `git apply --check`, apply only patches still needed, and stop rather than forcing conflicts in DTS, regulator, reserved-memory, power, or firmware changes.

The final extra-feature tree integrated:

```text
0003       Sharp LQ120P1JX51 panel
0004-0005 Surface RTC driver and DT node
0006       suspend workaround
0007       Surface Pro 12 DTS base
0008       volume-button GPIO swap
0010       DisplayPort audio routing
0011       charge-limit NVMEM cells
0012       camera DT support
```

The cleanly applicable CAMSS/CSI PHY/camera-clock/sensor dependencies were also integrated. A later camera dependency patch (`0022`) did not apply cleanly and was deliberately not forced. The X1P-specific multimedia compatibles must remain:

```text
qcom,x1p42100-iris
qcom,x1p42100-videocc
```

Do not substitute X1E compatibles. RFKill, unrelated regulator changes, IR remote work, and reserved-memory changes were not claimed as part of this build.

### Package verification

`bindeb-pkg` increments the Debian revision even when `LOCALVERSION` is unchanged. An older `~rc7-2` image lacked `rtc-surface.ko`; the final `~rc7-6` image contains it. Never install via an ambiguous wildcard. Inspect the exact newest package:

```bash
dpkg-deb -c ./linux-image-7.2.0-rc7-sp12-extra-camera_7.2.0~rc7-6_arm64.deb |
  rg 'rtc-surface\.ko|qcom-camss\.ko|phy-qcom-mipi-csi2\.ko'
sudo apt install \
  ./linux-image-7.2.0-rc7-sp12-extra-camera_7.2.0~rc7-6_arm64.deb \
  ./linux-headers-7.2.0-rc7-sp12-extra-camera_7.2.0~rc7-6_arm64.deb
dpkg -s linux-image-7.2.0-rc7-sp12-extra-camera | rg '^(Status|Version):'
modinfo -k 7.2.0-rc7-sp12-extra-camera rtc-surface
```

Install normal image and headers only. A `-dbg` image can consume several gigabytes and is unnecessary unless kernel symbol debugging is intentional. A module's `sig_id: PKCS#7` is a build-time signature, not proof of a Secure Boot trust chain.

The final compiled DTB was statically confirmed to contain the Sharp panel, X1P IRIS/VideoCC, X1P CAMSS, OV13858, OV02C10, DisplayPort0–3 audio links, and charge-limit NVMEM cells. Existing duplicate-unit-address/media-graph `dtc` warnings did not prevent compilation.

## 7. Exact ESP synchronization and recovery

Current stable sources:

```text
/boot/vmlinuz-7.2.0-rc7-sp12-extra-camera
/boot/initrd.img-7.2.0-rc7-sp12-extra-camera
/boot/dtb-7.2.0-rc7-sp12-extra-camera
```

Current `/usr/local/sbin/sp12-sync-boot`:

```sh
#!/bin/sh
set -eu

KVER=7.2.0-rc7-sp12-extra-camera
DTB=/boot/dtb-7.2.0-rc7-sp12-extra-camera
ESP=/boot/efi
DEST=$ESP/sp12
KERNEL=/boot/vmlinuz-$KVER
INITRD=/boot/initrd.img-$KVER

for source in "$KERNEL" "$INITRD" "$DTB"; do
    [ -f "$source" ] || { echo "missing: $source" >&2; exit 1; }
done

mountpoint -q "$ESP" || mount "$ESP"
mount -o remount,rw "$ESP"
trap 'sync; mount -o remount,ro "$ESP" || true' EXIT HUP INT TERM
mkdir -p "$DEST"

cp -f "$KERNEL" "$DEST/vmlinuz.new"
cp -f "$INITRD" "$DEST/initrd.img.new"
cp -f "$DTB" "$DEST/dtb.new"
cmp -s "$KERNEL" "$DEST/vmlinuz.new"
cmp -s "$INITRD" "$DEST/initrd.img.new"
cmp -s "$DTB" "$DEST/dtb.new"
mv -f "$DEST/vmlinuz.new" "$DEST/vmlinuz"
mv -f "$DEST/initrd.img.new" "$DEST/initrd.img"
mv -f "$DEST/dtb.new" "$DEST/dtb"
touch "$DEST/SP12BOOT"
sync
```

Kernel and optional initramfs hooks execute this helper:

```text
/etc/kernel/postinst.d/zzzz-sp12-sync
/etc/initramfs/post-update.d/zzzz-sp12-sync
```

After deliberately selecting a new custom kernel, first update both `KVER` and `DTB`, run the helper, and compare all three files. Never let Ubuntu's generic symlinks select the ESP payload.

```bash
sudo /usr/local/sbin/sp12-sync-boot
sudo cmp -s /boot/vmlinuz-7.2.0-rc7-sp12-extra-camera \
  /boot/efi/sp12/vmlinuz && echo 'kernel: OK'
sudo cmp -s /boot/initrd.img-7.2.0-rc7-sp12-extra-camera \
  /boot/efi/sp12/initrd.img && echo 'initrd: OK'
sudo cmp -s /boot/dtb-7.2.0-rc7-sp12-extra-camera \
  /boot/efi/sp12/dtb && echo 'dtb: OK'
```

Use `sudo` for initramfs comparisons; an unprivileged failure may only mean the source is root-readable. If a hook leaves package configuration incomplete, repair the helper and run `sudo dpkg --configure -a`.

The panel recovery payload is preserved at `/boot/efi/sp12-recovery-panel/`. To roll back from a bootable system:

```bash
sudo mount -o remount,rw /boot/efi
sudo cp -f /boot/efi/sp12-recovery-panel/vmlinuz /boot/efi/sp12/vmlinuz
sudo cp -f /boot/efi/sp12-recovery-panel/initrd.img /boot/efi/sp12/initrd.img
sudo cp -f /boot/efi/sp12-recovery-panel/dtb /boot/efi/sp12/dtb
sudo touch /boot/efi/sp12/SP12BOOT
sync
sudo mount -o remount,ro /boot/efi
```

If no installed kernel boots, use the custom installer USB, mount root and ESP, and restore matching kernel/initramfs/DTB files to `/boot/efi/sp12/`. Keep `7.2.0-rc7-sp12-panel` and its ESP recovery payload until the extra-feature kernel passes every runtime test.

## 8. CPU frequency scaling and measured battery policy

### What was actually missing

CPUfreq device-tree support was never absent. The Harrison/live DTB gives each CPU `power-domain-names = "psci", "perf"`, and SCMI protocol `0x13` supplies the performance levels. The kernel builds the consumers as modules:

```text
CONFIG_ARM_SCMI_CPUFREQ=m
CONFIG_ARM_SCMI_PERF_DOMAIN=m
```

Loading them creates:

```text
/sys/devices/system/cpu/cpufreq/policy0  # CPUs 0-3
/sys/devices/system/cpu/cpufreq/policy4  # CPUs 4-7
```

Persist `/etc/modules-load.d/sp12-cpufreq.conf`:

```text
scmi_perf_domain
scmi_cpufreq
```

Verify without `cpupower`:

```bash
for p in /sys/devices/system/cpu/cpufreq/policy*; do
  printf '%s cpus=%s driver=%s governor=%s min=%s max=%s\n' \
    "${p##*/}" "$(cat "$p/affected_cpus")" \
    "$(cat "$p/scaling_driver")" "$(cat "$p/scaling_governor")" \
    "$(cat "$p/scaling_min_freq")" "$(cat "$p/scaling_max_freq")"
done
```

The custom-kernel `cpupower` wrapper complains that matching `linux-tools` packages do not exist. It is not required; sysfs is authoritative.

The firmware may log:

```text
Failed to add opps_by_lvl at 3244800 for NCC1 - ret:-16
```

This duplicate top-level OPP warning is nonfatal: both SCMI policies and energy-model domains initialize.

### Installed power policy

`/usr/local/sbin/sp12-power-tune` is run by `sp12-power-tune.service` at boot and by `/etc/udev/rules.d/80-sp12-power.rules` when Qualcomm AC/USB power state changes.

Battery settings:

- both CPU clusters: `schedutil`, 710.4 MHz–2.1888 GHz, boost off;
- GPU ceiling: 550 MHz (280 MHz remains an available idle OPP; active driver QoS may temporarily report floor=ceiling);
- PCIe ASPM: `powersave`;
- USB autosuspend for the tested controllers/dock devices;
- `power-saver` profile;
- backlight clamped to 50% only when it is above that level.

GNOME automatic brightness is disabled systemwide without disabling the sensor proxy. `/etc/dconf/profile/user` includes `system-db:local`; `/etc/dconf/db/local.d/00-sp12-display` sets `org.gnome.settings-daemon.plugins.power ambient-enabled=false`; and `/etc/dconf/db/local.d/locks/sp12-display` locks that key. Run `sudo dconf update` after changing these files. This preserves accelerometer rotation and compass access while keeping display brightness under manual control.

AC settings restore the full 3.2448 GHz CPU and 1.107 GHz GPU ranges, default ASPM, and the balanced profile.

Measured battery discharge fell from roughly 13.5–13.8 W before tuning to a five-sample 5.08 W under a light active workload. With about 35.9 Wh usable capacity, 5.08 W is a theoretical seven hours; real runtime depends on display brightness and workload. Battery health measured approximately 95.8%.

Reproducible form of the current `/usr/local/sbin/sp12-power-tune` policy:

```sh
#!/bin/sh
set -eu

write_value() {
    path=$1
    value=$2
    [ ! -w "$path" ] || printf '%s\n' "$value" > "$path"
}

on_ac=0
for supply in qcom-battmgr-ac qcom-battmgr-usb; do
    path="/sys/class/power_supply/$supply/online"
    if [ -r "$path" ] && [ "$(cat "$path")" = 1 ]; then
        on_ac=1
    fi
done

modprobe scmi_perf_domain >/dev/null 2>&1 || true
modprobe scmi_cpufreq >/dev/null 2>&1 || true

for device in 1-1.2.3 1-1.2.4 2-1.1; do
    write_value "/sys/bus/usb/devices/$device/power/autosuspend_delay_ms" 2000
    write_value "/sys/bus/usb/devices/$device/power/control" auto
done
for device in a600000.usb a800000.usb xhci-hcd.1.auto xhci-hcd.2.auto; do
    write_value "/sys/bus/platform/devices/$device/power/control" auto
done

gpu=/sys/class/devfreq/3d00000.gpu
aspm=/sys/module/pcie_aspm/parameters/policy
boost=/sys/devices/system/cpu/cpufreq/boost

for policy in /sys/devices/system/cpu/cpufreq/policy*; do
    [ -d "$policy" ] || continue
    write_value "$policy/scaling_governor" schedutil
    write_value "$policy/scaling_min_freq" 710400
done
write_value "$boost" 0

if [ "$on_ac" = 1 ]; then
    powerprofilesctl set balanced >/dev/null 2>&1 || true
    for policy in /sys/devices/system/cpu/cpufreq/policy*; do
        [ -d "$policy" ] || continue
        write_value "$policy/scaling_max_freq" 3244800
    done
    write_value "$gpu/max_freq" 1107000000
    write_value "$gpu/min_freq" 280000000
    write_value "$aspm" default
else
    powerprofilesctl set power-saver >/dev/null 2>&1 || true
    for policy in /sys/devices/system/cpu/cpufreq/policy*; do
        [ -d "$policy" ] || continue
        write_value "$policy/scaling_max_freq" 2188800
    done
    write_value "$gpu/min_freq" 280000000
    write_value "$gpu/max_freq" 550000000
    write_value "$aspm" powersave

    backlight=/sys/class/backlight/backlight
    if [ -r "$backlight/brightness" ] &&
       [ "$(cat "$backlight/brightness")" -gt 2048 ]; then
        write_value "$backlight/brightness" 2048
    fi
fi
```

Install it mode `0755`. Create `/etc/systemd/system/sp12-power-tune.service`:

```ini
[Unit]
Description=Surface Pro 12 measured power tuning
After=systemd-modules-load.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/sp12-power-tune

[Install]
WantedBy=multi-user.target
```

The relevant `/etc/udev/rules.d/80-sp12-power.rules` entries are:

```udev
ACTION=="add|change", SUBSYSTEM=="power_supply", KERNEL=="qcom-battmgr-*", RUN+="/usr/local/sbin/sp12-power-tune"
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="046d", ATTR{idProduct}=="c52b", TEST=="power/control", ATTR{power/control}="auto"
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="046d", ATTR{idProduct}=="c548", TEST=="power/control", ATTR{power/control}="auto"
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="0b95", ATTR{idProduct}=="1790", TEST=="power/control", ATTR{power/control}="auto"
```

The three USB IDs are devices verified to autosuspend safely on this particular machine; omit or retest them on different hardware. Activate changes with:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sp12-power-tune.service
sudo udevadm control --reload
```

Live verification:

```bash
systemctl is-enabled sp12-power-tune.service
systemctl show sp12-power-tune.service -p Result -p ExecMainStatus
cat /sys/devices/system/cpu/cpufreq/boost
for p in /sys/devices/system/cpu/cpufreq/policy*; do
  cat "$p/scaling_governor" "$p/scaling_min_freq" "$p/scaling_max_freq"
done
cat /sys/class/devfreq/3d00000.gpu/{min_freq,max_freq,cur_freq}
cat /sys/module/pcie_aspm/parameters/policy
powerprofilesctl get
```

A successful `Type=oneshot` service normally shows `inactive (dead)` afterward; `Result=success` and `ExecMainStatus=0` are the relevant checks.

Do not order this unit after `power-profiles-daemon.service`: that daemon is ordered after `multi-user.target`, while this unit is wanted by `multi-user.target`, producing a cycle that causes systemd to discard the tuning job. The power script may still call `powerprofilesctl`; the call safely fails or succeeds according to daemon availability, and a later Qualcomm power-supply udev event reapplies the complete policy.

Post-reboot audit on 2026-08-13 found this ordering cycle in the original unit. A power-supply udev event had nevertheless reapplied every intended setting: both SCMI policies were present at 710.4 MHz–2.1888 GHz with `schedutil`, boost was off, GPU was capped at 550 MHz, PCIe was in `powersave`, the platform USB controllers were autosuspended, power-saver was selected, and the backlight remained below 50%. Removing the PPD ordering dependency fixed deterministic boot execution; `systemd-analyze verify` then passed and a manual restart completed with `Result=success` and `ExecMainStatus=0`.

For frequent AC use, use the Surface UEFI battery-limit option. Linux charge-threshold attributes currently report unusable zero values; do not write an unknown threshold interface.

## 9. GPU, video, and camera notes

### GPU

Firmware exists as compressed Zstd files:

```text
/lib/firmware/qcom/gen71500_gmu.bin.zst
/lib/firmware/qcom/gen71500_sqe.fw.zst
/lib/firmware/qcom/gen71500_zap.mbn.zst
```

The kernel has `CONFIG_FW_LOADER_COMPRESS_ZSTD=y`. Early uncompressed lookup failures may be followed by successful compressed loading. Do not decompress these files, force them into initramfs, or rebuild solely because they end in `.zst`.

```bash
glxinfo -B | grep -E 'direct rendering|OpenGL vendor|OpenGL renderer'
```

Confirmed: direct rendering, Freedreno, Adreno X1-45.

### IRIS video codec

The Microsoft Surface driver package supplied the exact requested file:

```text
/lib/firmware/qcom/x1p42100/Microsoft/Surface12/qcvss8380_pa.mbn
SHA-256: 725711497ca962d76f62c4f3309dff51cf9f18b499bc252feb17588b9de3cfb1
```

It came from `SurfacePro_12in_1st_Edition_Win11_26100_26.061.13065.0.msi` at `SurfaceUpdate/qcdx8380/qcvss8380_pa.mbn`. Install only firmware the kernel actually requests. The previous missing-firmware error is gone and `qcom-iris` binds to `aa00000.video-codec`.

### Cameras

The current DTB contains CAMSS and OV13858/OV02C10 nodes, but static presence is not proof of capture. Check first:

```bash
sudo apt install -y v4l-utils mediactl
media-ctl -p
v4l2-ctl --list-devices
ls -l /dev/video* /dev/media* 2>/dev/null
```

Look for CAMSS, CSIPHY/CSID/VFE, both sensors, and media/video nodes. Run Harrison's `wireupcameras.sh` only after those entities exist; it configures links but cannot create missing drivers or DT nodes.

## 10. Extra-feature runtime checklist

Basic inventory:

```bash
uname -r
modinfo rtc-surface | sed -n '1,12p'
lsmod | rg 'rtc_surface|surface_aggregator|qcom_camss|phy_qcom_mipi_csi2' || true
journalctl -b -k --no-pager |
  rg -i 'rtc|surface.*aggregator|camss|csiphy|ov13858|ov02c10|iris|videocc|panel' || true
```

If needed, `sudo modprobe rtc-surface`; a driver binding is a pass, while a missing/deferred device is diagnostic evidence rather than a reason to rebuild immediately.

- DisplayPort audio: connect a USB-C DP/HDMI display, then run `aplay -l` and `pactl list short sinks`.
- Charge-limit support: inspect `charge_control_*` or `*charge*limit*` under `/sys/class/power_supply`; do not write until the interface and valid range are known.
- Volume buttons: run `sudo libinput debug-events` and confirm one correctly oriented event per button.
- Suspend: only with saved work, run `systemctl suspend`, then inspect `journalctl -b` for suspend/resume failures. Prove repeated cycles.
- Hibernate: unverified. The existing 4 GiB swap image is too small for a dependable 16 GiB RAM hibernation design.

## 11. Maintenance and safe cleanup

Install ordinary Ubuntu updates normally, but keep ESP selection under the exact pinned helper:

```bash
sudo apt update
sudo apt upgrade
```

Before removing kernels, identify the running kernel and installed packages. Never purge `uname -r` or the panel recovery kernel:

```bash
uname -r
dpkg-query -W 'linux-image*' 'linux-headers*' 2>/dev/null
```

The tested cleanup removed obsolete `7.0.0-29-generic` and `7.2.0-rc7-sp12`, retaining only `7.2.0-rc7-sp12-extra-camera` and `7.2.0-rc7-sp12-panel`. APT caches were cleaned, recovering about 2 GiB. Purge only exact package names after checking the running/recovery pair; then use:

```bash
sudo apt autoremove --purge
sudo apt clean
```

Do not install or retain `-dbg` kernels unless needed. `kdump-tools` reserves about 512 MiB on this 16 GiB system; keep it while testing custom kernels, and disable it deliberately only when crash capture is no longer valuable.

The historical installation had a misspelled `cdrom.sources.disabld` file. Its
APT notice was cosmetic because APT ignored that invalid extension. This is not
the current recovery procedure; follow the maintained guide's
[package-repository instructions](../../GUIDE.md#enable-the-ubuntu-package-repositories)
instead.

## 12. Known non-blocking messages

Observed without demonstrated functional failure:

- SCMI duplicate 3.2448 GHz OPP (`ret:-16`) while both CPU policies work;
- repeated ADSP `Handover signaled, but it already happened` while ADSP remains running;
- early uncompressed `gen71500_sqe.fw` lookup followed by working compressed firmware/Freedreno;
- UFS RPMB or inline-encryption registration failures while normal UFS I/O remains stable;
- dummy-regulator and PMIC device-link messages from incomplete platform descriptions;
- existing duplicate-unit-address/media-graph warnings when decompiling the DTB.

Monitor changes after a new kernel/DTB, but do not tune around these messages without an associated failure.

## 13. Compact verification checklist

```bash
cat /proc/device-tree/model
uname -r
lsblk
findmnt /boot/efi
ls -lh /boot/efi/EFI/BOOT/BOOTAA64.EFI /boot/efi/sp12/*
ip link
glxinfo -B
wpctl status
aplay -l
arecord -l
monitor-sensor
upower -e
readlink -f /sys/bus/platform/devices/aa00000.video-codec/driver
systemctl show sp12-power-tune.service -p Result -p ExecMainStatus
```

Expected core state: model `Surface Pro 12in 1st Edition`; kernel `7.2.0-rc7-sp12-extra-camera`; matching ESP kernel/initramfs/DTB; Freedreno Adreno X1-45 acceleration; working Wi-Fi, audio, three sensors, battery reporting, bound IRIS driver, and two SCMI CPUfreq policies.

## 14. Rules that prevent repeat failures

- Preserve the FAT-ESP fallback boot architecture.
- Never mix a kernel, initramfs, and DTB from different releases.
- Never use generic kernel symlinks in the ESP helper.
- Keep the panel recovery kernel and payload until all extra features are proven.
- Compile with `make -j"$(nproc)"`, but package with `make -j1 bindeb-pkg`.
- Inspect the exact newest `.deb`; do not assume equal kernel release means equal package contents.
- Do not install `-dbg` packages by default.
- Do not blindly apply the full overlay or force DTS/power/regulator/reserved-memory conflicts.
- Do not treat compressed GPU firmware as broken.
- Do not treat `wireupcameras.sh` as a substitute for kernel/DT support.
- Do not re-enable Secure Boot until the EFI loader and every booted custom kernel are intentionally signed and enrolled.

## 15. Secure Boot investigation and activation design

### Verified current state

The system was inspected read-only on 2026-08-13:

```text
SecureBoot=0
SetupMode=1
kernel lockdown: none
```

Setup Mode means the firmware currently has no active Platform Key, so merely toggling Secure Boot cannot establish a trust chain. These active boot files contain no PE signature table:

```text
/boot/efi/EFI/BOOT/BOOTAA64.EFI
/boot/efi/sp12/vmlinuz
/boot/vmlinuz-7.2.0-rc7-sp12-extra-camera
```

The current command line includes `efi=noruntime`; therefore do not assume Linux can schedule enrollment with `mokutil --import`. EFI variables are readable, but runtime EFI services are intentionally disabled after boot.

Ubuntu 26.04 already supplies the necessary signed ARM64 first stages:

```text
shim-signed 1.59+15.8-0ubuntu2
grub-efi-arm64-signed 1.215+2.14-2ubuntu1
/usr/lib/shim/shimaa64.efi.signed.latest
/usr/lib/shim/mmaa64.efi
/usr/lib/grub/arm64-efi-signed/grubaa64.efi.signed
```

The installed shim is Microsoft-signed through the Microsoft Corporation UEFI CA 2011; MokManager and signed GRUB are Canonical-signed. Surface certificate policy is transitioning to 2023 authorities during 2026, so confirm the firmware's restored `Windows & 3rd-party UEFI CA` database still accepts this exact shim before replacing the internal loader.

The custom kernel supports an ARM64 EFI/UKI path (`CONFIG_EFI_STUB=y`, `CONFIG_EFI_ZBOOT=y`). Its custom modules, including `scmi_cpufreq`, `scmi_perf_domain`, `rtc-surface`, and `qcom-camss`, are signed with the embedded `Build time autogenerated kernel key`. However, `CONFIG_MODULE_SIG_FORCE` is off, so an enforced deployment must add `module.sig_enforce=1` or rebuild with `CONFIG_MODULE_SIG_FORCE=y`. The kernel supports the Lockdown LSM but currently boots with lockdown disabled.

### Recommended authenticated chain

```text
Surface UEFI factory keys
  -> Microsoft-signed Ubuntu shimaa64.efi
  -> owner-signed ARM64 Unified Kernel Image as grubaa64.efi
       - systemd EFI stub
       - exact custom kernel
       - exact initramfs
       - exact Surface DTB
       - immutable kernel command line
  -> modules signed by the kernel's embedded build key
```

A UKI is preferable to the current standalone GRUB payload because a single PE/COFF signature covers the custom kernel, initramfs, command line, and Surface DTB. Conventional Ubuntu Secure Boot verifies shim, GRUB, and the kernel, but does not authenticate an external initramfs; Secure-Boot GRUB also requires an external device tree to be authenticated. `systemd-ukify` supports an ARM64 `.dtb` section and is available from Ubuntu 26.04, together with `systemd-boot-efi` for the ARM64 stub.

This design preserves the fallback-filesystem advantage: shim loads its same-directory second stage `grubaa64.efi` from FAT and does not need to read ext4. The UKI itself mounts root by the embedded UUID command line.

### Safe staged procedure

Do not activate this directly on the internal ESP. Preserve the current unsigned internal loader, the panel recovery kernel, and a bootable installer USB throughout testing.

1. Install `systemd-ukify` and `systemd-boot-efi`.
2. Generate a dedicated owner Secure Boot key and X.509 certificate. Use a normal code-signing certificate, not a MOK containing the module-signing-only OID `1.3.6.1.4.1.2312.16.1.2`; shim 15.4 and later will not use a module-only MOK to authorize EFI programs.
3. Build a UKI from these exact sources:

   ```text
   /boot/vmlinuz-7.2.0-rc7-sp12-extra-camera
   /boot/initrd.img-7.2.0-rc7-sp12-extra-camera
   /boot/dtb-7.2.0-rc7-sp12-extra-camera
   ```

4. Embed the working root UUID and required platform arguments. For enforcement, append `lockdown=integrity module.sig_enforce=1`:

   ```text
   root=UUID=db48a164-d6cb-4034-8d6f-841867f66757 ro clk_ignore_unused pd_ignore_unused cma=128M efi=noruntime quiet splash console=tty0 stubble.dtb_override=true lockdown=integrity module.sig_enforce=1
   ```

5. Sign the completed UKI with the owner key and verify it with `sbverify --list`. Do not sign only the raw kernel; the completed UKI is the object firmware/shim must authenticate.
6. With Secure Boot still disabled, test the UKI from a USB as `/EFI/BOOT/BOOTAA64.EFI`. This proves systemd-stub correctly supplies the DTB, initramfs, and embedded command line.
7. Prepare a separate enrollment USB:

   ```text
   /EFI/BOOT/BOOTAA64.EFI  Microsoft-signed shimaa64.efi
   /EFI/BOOT/grubaa64.efi  Canonical-signed mmaa64.efi
   /sp12-owner.der         owner public certificate
   ```

   Local inspection confirms shim's ARM64 second-stage names are `grubaa64.efi` and `mmaa64.efi`. MokManager provides **Enroll key from disk**, so enrollment does not require `mokutil` or EFI runtime services.
8. Enter Surface UEFI, install all factory default keys if offered, choose **Windows & 3rd-party UEFI CA**, and enable Secure Boot. Do not select **Microsoft only**, which is expected to reject Ubuntu shim.
9. Boot the enrollment USB and use MokManager's **Enroll key from disk** to enroll `sp12-owner.der`.
10. Test another USB containing Microsoft-signed shim as `BOOTAA64.EFI`, the owner-signed UKI as `grubaa64.efi`, and Canonical-signed MokManager as `mmaa64.efi`.
11. Only after that USB boots and passes all subsystem tests should the same layout replace the internal fallback loader. Keep the old internal files under clearly named recovery paths and retain the option to disable Secure Boot in Surface UEFI.

The ESP has about 810 MiB free. The current kernel, initramfs, and DTB total roughly 119 MiB, so a UKI and recovery copies fit without removing the panel recovery payload.

### Post-activation checks

```bash
mokutil --sb-state
cat /sys/kernel/security/lockdown
cat /sys/module/module/parameters/sig_enforce
journalctl -b -k --no-pager | rg -i 'secure boot|lockdown|integrity|module verification'
```

Expected:

```text
SecureBoot enabled
Platform is not in Setup Mode
[integrity]
module signature enforcement enabled
```

Then verify the exact running kernel, DTB model, Wi-Fi, GPU, audio, sensors, IRIS, both SCMI CPUfreq policies, RTC/cameras, suspend, and battery policy. A Secure Boot success that loses required custom modules is not a usable success.

Secure Boot authenticates the boot components, not the mutable ext4 userspace. Encryption primarily protects confidentiality; use authenticated storage, measured boot with a suitable policy, or dm-verity when offline modification detection is required. Do not conflate a signed boot chain with full-disk integrity.

Authoritative references used for this design:

- Ubuntu Secure Boot architecture and MOK behavior: <https://documentation.ubuntu.com/security/docs/security-features/platform-protections/secure-boot/>
- Surface UEFI and factory-key controls: <https://support.microsoft.com/en-us/surface/drivers-firmware/how-to-use-surface-uefi>
- Surface 2011-to-2023 certificate transition: <https://support.microsoft.com/en-us/surface/drivers-firmware/surface-secure-boot-certificates>
- Unified Kernel Image format, including `.initrd`, `.cmdline`, and `.dtb`: <https://uapi-group.org/specifications/specs/unified_kernel_image/>
- Ubuntu 26.04 `ukify` options: <https://manpages.ubuntu.com/manpages/resolute/man1/ukify.1.html>
- Linux module-signature enforcement: <https://www.kernel.org/doc/html/next/admin-guide/module-signing.html>
- GRUB shim/Secure Boot verification rules: <https://www.gnu.org/software/grub/manual/grub/html_node/UEFI-secure-boot-and-shim.html>
