# Ubuntu 26.10 release-upgrade assessment

Last updated 2026-10-23 after read-only SSH checks on `cs-sp12`, the
non-rebooting GRUB/shim package rehearsal and ESP restoration, installation of
the local GRUB fallback guard, and the latest root preflight output.

## Current decision: do not run the release upgrade

Ubuntu 26.10 was released on 2026-10-15 ([release announcement][announcement]).
Ubuntu documents the 26.04-to-26.10 path for systems following interim
releases ([upgrade guide][upgrade]). This custom Surface installation
is not yet ready: its release track is now `Prompt=normal`, but the device's
stable [`meta-release` data][metadata] still has no supported 26.10
`UpgradeTool` entry. Before the track was changed, the read-only
`do-release-upgrade --check-dist-upgrade-only` reported no development version
of an LTS available and advised `Prompt=normal` for the latest non-LTS release.
Ubuntu says interim upgrades are usually offered a few days after release
([upgrade guide][upgrade]); stable metadata still must be rechecked. Do not
bypass it with `-d`.

The user instructed us to bypass the recovery-media gate while starting other
checks. That direction was followed for read-only inspection. It does not waive
the need for an independent full-system backup and separate user-data backup
before an actual OS upgrade. No recovery-media boot test or shim boot test was
performed. No reboot or release upgrade was performed.

## Device and package state

- Ubuntu 26.04.1 LTS, ARM64, running `7.3.0-sp12-v7.3-platform`.
- Maintained boot config selects `KVER=7.3.0-sp12-v7.3-platform` and
  `DTB=/boot/dtb-7.3.0-sp12-v7.3-platform`. Three historical 7.2 SP12 kernel
  image packages and the maintained 7.3 package are installed. The 26.10
  release-upgrader removal plan is not available, so retention through upgrade
  is unverified.
- `dpkg --audit` is clean. `iio-sensor-proxy` 3.8-1 remains held; the current
  26.04 candidate is also 3.8-1. The public 26.10 (`stonking`) catalogue lists
  the Ubuntu source package `iio-sensor-proxy` 3.9-1ubuntu1. The locally tested
  sensor stack instead documents Harrison's fork at commit
  `fcd5b5cf431bc053375350c57064b8b13dd961b4`, built with
  `-Dssc-support=enabled` and installed under `/usr/local`. Matching upstream
  version numbers do not establish equivalent source, build flags, or service
  integration. Keep the hold until the real upgrader plan and installed path
  ownership are reviewed, then retest sensors. The catalogue lists
  `grub2-common` 2.14-2ubuntu3, compared with the installed 26.04-updates
  version 2.14-2ubuntu2.1; `shim-signed` remains 1.59+15.8-0ubuntu2. This is
  not the target's release-upgrader plan and does not replace package-hook
  review. See the [26.10 sensor package][sensor-2610],
  [GRUB common package][grub-common-2610], and [shim package][shim-2610].
- The operator applied the three reviewed 26.04 updates: `ubuntu-pro-client`
  and `ubuntu-pro-client-l10n` 38ubuntu0~26.04, and `chatgpt` 26.1021.22027.
  The transaction installed no packages and removed none. The ten phased
  packages were deferred. These updates did not include kernel, GRUB, shim, or
  the held sensor package. The current-release APT simulation now proposes no
  package changes; this is not the 26.10 release-upgrader plan.
- `Prompt=normal` is now confirmed by the latest root preflight. The operator
  applied the reviewed ordinary 26.04 updates. No 26.10 release-upgrader
  removal plan is available yet.
- Only internal disk `sda` is attached: 476.7 GB total, 186 GiB free on `/`,
  and 810 MiB free on the ESP. No separate backup disk or network filesystem is
  mounted. The same-disk ESP image is not full-system recovery.
- Third-party APT sources need review: R (`cloud.r-project.org`), ChatGPT,
  Tailscale, Microsoft VS Code, and Waydroid. Ubuntu Pro ESM sources are also
  configured. Their upgrade compatibility has not been reviewed.

## GRUB/shim rehearsal: performed; ESP and NVRAM restored

The operator reinstalled the currently installed `shim-signed`,
`grub2-common`, and `grub-efi-arm64` packages without rebooting. During the
reinstall, `grub2/update_nvram` had been set to `false`; package hooks still
created `Boot0005 Ubuntu` and moved it to the front of BootOrder. The operator
removed that entry and restored the baseline NVRAM state:

- `BootCurrent=0003` (`MsTemp`)
- `BootOrder=0001,0004,0000,0002`
- No Ubuntu NVRAM entry

The package hooks replaced fallback `EFI/BOOT/BOOTAA64.EFI` with shim and
created package files under `EFI/ubuntu` plus `EFI/BOOT/fbaa64.efi`. The ESP
was then restored from `/var/backups/cs-sp12-esp-20261023.img` while unmounted.
The operator verified the restored ESP and image hashes match:

`ed80966d73a481d03c3e0ea5f07589b92ba0f632822afa0ea5cdbee4e023a573`

`/boot/efi` is mounted read-only. Follow-up inspection confirms the original
fallback GRUB and active payload hashes, and `grub-file --is-arm64-efi`
passes. No reboot occurred; shim acceptance of the custom GRUB remains untested.
The ESP image is on the same disk and is not independent full-system recovery.

The package behavior is now directly explained by the installed scripts:

- `grub-efi-arm64.postinst` passes `--no-extra-removable` only when
  `grub2/no_efi_extra_removable=true`; its current value is `false`.
- That postinst passes `--no-nvram` only when `grub2/update_nvram=false`; its
  current value is `true`.
- `shim-signed.postinst` invokes `/usr/lib/grub/grub-multi-install
  --target=arm64-efi` directly, without those arguments. This explains why the
  package run changed NVRAM despite the temporary debconf change.
- The successful scratch-image install showed the package's default fallback
  output is shim. It did not test shim loading this device's custom GRUB.

Installed versions: `grub-efi-arm64` and `grub-efi-arm64-bin` 2.14-2ubuntu1,
`grub2-common` 2.14-2ubuntu2.1, `shim-signed` 1.59+15.8-0ubuntu2, and
`ubuntu-release-upgrader-core` 1:26.04.27. Secure Boot is disabled; firmware
is in Setup Mode and the custom GRUB has no signature table. These facts do
not establish that shim will load the custom GRUB.

## Fallback-path guard

Read-only inspection of the installed `shim-signed.postinst` confirms its only
GRUB-install calls are two direct invocations of
`/usr/lib/grub/grub-multi-install --target=arm64-efi`; it contains no separate
`efibootmgr` call. The helper forwards its arguments to `grub-install`. This
gives a precise interception point: a local `dpkg-divert` can preserve the
package helper under `/usr/lib/grub/grub-multi-install.sp12-original` and route
package-hook calls through
`system/usr-local-sbin/sp12-grub-multi-install-guard`. The guard removes any
caller-supplied removable/NVRAM options and appends `--no-extra-removable` and
`--no-nvram`. It fails closed if either option is no longer supported. It also
handles `--help` itself, so that option cannot fall through into an install.

`scripts/install-grub-fallback-guard` provides a dry run by default, an
explicit `--apply`, and a reversible `--remove`. Its installation does not run
GRUB, write the ESP, or update NVRAM. The updated preflight verifies the
diversion and guard before treating fallback protection as active. The guard
and installer are staged under `/tmp/sp12-grub-fallback-guard` on `cs-sp12`;
SHA-256 matches the repository copies, `bash -n`/`sh -n` passed, and the
installer's default dry run reported the expected diversion without changes.
The operator then applied the staged installer as root. It confirmed the
diversion, preserved helper and support for both safety options; it did not run
GRUB, write the ESP or update NVRAM. The subsequent root preflight passed the
verified-guard check. This clears the fallback-path preflight failure; the
debconf value `grub2/no_efi_extra_removable=false` is no longer the protection
decision because the verified guard forces safe options for package-hook calls.
The operator reinstalled `shim-signed`, `grub2-common` and `grub-efi-arm64`
with the guard active. All three packages configured; both GRUB post-install
runs reported `Installation finished. No error reported.`, and GRUB
configuration generation completed. Post-run checks confirmed `/boot/efi` is
read-only again; `BootCurrent=0003`, `BootOrder=0001,0004,0000,0002`, and no
Ubuntu NVRAM entry; unchanged fallback hashes (`8575b891a807b311bbb266a47bfff4f4605b8a15102898a1214c9fe2d5425637` for both
`BOOTAA64.EFI` and `grubaa64.efi`, `9736c90ebd7a7680419f8755f0e722c1c442225aa6dcea0612e65016a1588af0` for
`mmaa64.efi`); and unchanged SP12 kernel, initramfs and DTB hashes. The
diverted helper's `--verify` passes. This completes the guarded package-hook
rehearsal: fallback files, active SP12 payloads, NVRAM boot order and ESP mount
protection were preserved. Firmware boot compatibility remains untested; do
not infer that shim will accept the custom GRUB or reboot solely on this test.

During this audit, I mistakenly invoked the package helper with `--help` while
trying to inspect it. The helper has no help handler and reached its inner
`grub-install --help` path while `/boot/efi` was read-only. The subsequent
read-only check found all six recorded ESP payload hashes unchanged and the
ESP still read-only. NVRAM was not independently checked at that point because
SSH `sudo` had no terminal. Before the later guarded package-hook rehearsal,
the operator captured the NVRAM/ESP baseline and verified it remained unchanged
after reinstall.

## Latest preflight results

The initial root run of `scripts/sp12-upgrade-preflight` returned `NOT READY`
with three failures:

1. `Prompt=lts`; the interim track has not been selected.
2. Stable metadata has no supported 26.10 upgrade tool.
3. `grub2/no_efi_extra_removable=false`.

The root run passed OS/architecture, `dpkg --audit`, configured/running kernel,
kernel/initramfs/DTB ESP content comparisons, active payload presence and
ARM64 fallback-loader checks. It reported seven manual gates: review the held
sensor package and pending 26.04 updates; validate GRUB/shim behavior and
loader protection; obtain the actual 26.10 removal plan and kernel-retention
decision; verify full-system and user-data backups and recovery readiness;
review disk-space requirements; and review non-Ubuntu sources. The reported
space is 186 GiB free on `/` and 810 MiB on the ESP. Installed GRUB and shim
maintainer scripts show package hooks can replace the fallback loader and
change NVRAM, so that safety gate remains open.

The operator then applied the three reviewed ordinary updates: `ubuntu-pro-client`
and `ubuntu-pro-client-l10n` 38ubuntu0~26.04, and `chatgpt` 26.1021.22027. The
transaction removed no packages and touched no kernel, GRUB, shim or held sensor
package. A subsequent root preflight confirms `Prompt=normal`, clean
`dpkg --audit`, no current-release package changes pending, and the same kernel,
initramfs, DTB and ARM64 fallback-loader passes. It returns two failed checks:
stable metadata still has no supported 26.10 `UpgradeTool`, and
`grub2/no_efi_extra_removable=false`. Six manual gates remain: held sensor
compatibility, GRUB/shim loader protection, the actual upgrader removal plan and
kernel retention, full-system and user-data backups/recovery, free-space
requirements, and third-party source compatibility.

After the operator ran `sudo apt update`, all configured `resolute` indexes
refreshed successfully, including R and Waydroid's current-release endpoints.
The initial `apt-get -s full-upgrade` listed three updates and no removals;
ten other packages were deferred due to phasing. These are not a 26.10 upgrade
plan. After applying the three updates, the latest preflight simulation reports
no current-release package changes. Current-suite index success does not establish that these
third-party vendors support `stonking`; the earlier `stonking` endpoint checks
remain the relevant target-suite evidence. The stable metadata request succeeded
but contained no supported 26.10 entry with an `UpgradeTool`. The operator has not
found any matching cache files under `/var/lib/update-manager`. A read-only
inspection of other updater paths found only the empty
`/var/lib/ubuntu-release-upgrader/release-upgrade-available` marker; there are
no files in `/var/log/dist-upgrade`. The installed update-manager source
confirms the configured stable endpoint is `https://changelogs.ubuntu.com/meta-release`
and stores its cache as `/var/lib/update-manager/meta-release` when writable.
Therefore the 26.10 failure is not explained by a stale root cache; stable
metadata fetched by the preflight itself currently has no supported entry. A
second direct fetch from `cs-sp12` listed the stable endpoint's versions
through 26.04.1 LTS and again found no 26.10 stanza. Ubuntu's official release
announcement confirms 26.10 was released on 2026-10-15; the missing upgrader
entry is a metadata/availability issue, not evidence that the OS release has
not been published. A no-cache HTTP header check from `cs-sp12` returned
`200 OK`, `Date: 2026-10-24`, and `Last-Modified: 2026-09-11` for
`meta-release` (the `Prompt=normal` endpoint). This supports an upstream
metadata-publication delay; local cache state is not the cause.

The first attempted preflight invocation failed because its local repository
path did not exist on the target. The script was copied to
`/tmp/sp12-upgrade-preflight-20261023`; its SHA-256 matches the local
repository copy (`b1461835bd00d65310e848f5098fd72ee238c6d70e922968ca76016dafaa5993`).
The root run above supersedes the earlier rootless checks, which could not
inspect the root-owned updater cache.

The preflight initially labeled the initramfs comparison as a content failure
when run unprivileged. `/boot/initrd.img-7.3.0-sp12-v7.3-platform` is mode
0600. The script now reports unreadable comparison inputs as a manual root-only
check and distinguishes a missing ESP file from a hash/content mismatch. The
completed root run supersedes the earlier rootless results and passes the
kernel, initramfs and DTB comparisons.

## 26.10 release-note checks

The target is not using TPM-backed full-disk encryption: `/` is directly on
`/dev/sda2` as ext4, `lsblk` shows no crypt mapper, and `/etc/crypttab` has no
active entry. `/lib32` is absent, not a dangling symlink. `/boot` shares the
root ext4 filesystem and the ESP is vfat. These checks clear two specific
26.10 release-note concerns for this device: TPM-backed FDE upgrades are not
enabled on release, and a dangling `/lib32` link can stop upgrades. See the
[26.10 release notes][notes].

The release notes also state that the default `cp`, `mv` and `rm` tools switch
to Rust implementations in 26.10. `sp12-sync-boot` and recovery/install helpers
use these commands for staged ESP updates and rollback (`cp`, `mv`, `rm`); this
workflow has not been exercised with 26.10's uutils on a scratch ESP. Verify
their staging, overwrite, rename and rollback behavior before relying on those
hooks during an OS or kernel package update.

Read-only repository probes from `cs-sp12` found no `stonking-cran40` metadata
for the configured R repository and no `stonking` metadata for Waydroid (HTTP
404). Waydroid is not installed. Tailscale's `stonking` index advertises
ARM64; the stable VS Code and ChatGPT repository indexes respond, and VS Code's
index advertises ARM64. These endpoint checks do not establish package-level
compatibility. The release upgrader's real plan and repository-disable
behavior remain to be reviewed; keep the R source disabled after upgrade
unless its vendor publishes a supported 26.10 suite.

## Preparation before stable metadata appears

These steps do not start a release upgrade. The interim track can be selected
in advance so update-manager uses the correct stable metadata endpoint; the
setting does not install packages or initiate an upgrade. See Ubuntu's
[track-switching guide][switch]. This was selected from `Prompt=lts` and the
latest preflight confirms `Prompt=normal`; that step is complete.

1. **Complete:** the operator changed the exact existing `Prompt=lts` line to
   `Prompt=normal`, and root preflight confirmed it. If it ever needs to be
   repeated, stop unless the file again contains exactly `Prompt=lts`:

   ```sh
   sudo sh -eu -c '
     f=/etc/update-manager/release-upgrades
     grep -qx "Prompt=lts" "$f" || { echo "Unexpected Prompt value; inspect $f" >&2; exit 1; }
     sed -i "s/^Prompt=lts$/Prompt=normal/" "$f"
     grep -qx "Prompt=normal" "$f"
   '
   grep -n '^Prompt=' /etc/update-manager/release-upgrades
   ```

2. **Complete:** refresh 26.04 package indexes and inspect the ordinary-updates
   plan. The reviewed transaction did not touch kernel, GRUB, shim, or held
   `iio-sensor-proxy`. Do not unhold the sensor package as a blanket step.
   Reboot only when an ordinary-update plan requires it and after the
   boot/recovery path is understood:

   ```sh
   sudo apt update
   sudo apt-get -s full-upgrade
   ```

   The reviewed simulation proposed only the three updates listed above. The
   operator applied them interactively; no packages were added or removed. The
   post-update root preflight confirmed the package audit is clean and no
   current-release updates remain pending. The verification commands were:

   ```sh
   sudo dpkg --audit
   sudo sh /tmp/sp12-upgrade-preflight-20261023
   ```

3. Resolve the listed manual gates in this document: compatibility of the
   third-party repositories and held sensor package, actual backups, a tested
   recovery route, free-space requirements, and preservation of the maintained
   7.3 kernel. Keep the R and Waydroid sources disabled unless their vendors
   publish the 26.10 suite. Retain command output and backup locations in the
   handoff; do not record credentials.
4. Test boot-sync staging and rollback on a scratch ESP using 26.10's Rust
   coreutils. The rehearsal must verify that active files are unchanged on
   injected failures and that the ESP returns to read-only. Do not use the
   installed ESP as the scratch target. No such test has been run yet.
5. **Complete: guarded package-hook reinstall.** Post-run ESP hashes match the
   pre-run fallback and SP12 payload hashes, `efibootmgr -v` matches the
   baseline, the ESP is read-only, and the diverted helper verifies. The prior
   unguarded rehearsal demonstrated that package hooks can rewrite fallback
   files and create an NVRAM entry. This guarded rehearsal does not verify that
   firmware can boot this custom GRUB.

## Latest operator result after guard installation

The operator installed the local diversion as root and reran the staged
preflight. Installation confirmed the diverted package helper exists and
`grub-install` supports both forced safety options; the installer did not run
GRUB, write the ESP or update NVRAM. Preflight passed the verified-guard check,
along with the current release, ARM64, package audit, current-suite simulation,
kernel, initramfs, DTB and ESP payload checks. It returned one failure: stable
metadata still has no supported 26.10 `UpgradeTool`. Six manual gates remain:
held sensor compatibility; review of the actual 26.10 GRUB/shim maintainer
scripts and package plan; kernel retention; full-system/user-data backups and
recovery; release-upgrader space requirements; and third-party source
compatibility. The guarded reinstall of the three packages completed, and
post-run checks confirmed unchanged fallback/SP12 payload hashes, unchanged
NVRAM boot order, a read-only ESP mount and a passing guard verification.
Firmware boot compatibility remains untested.

The pre- and post-rehearsal baselines match: `BootCurrent=0003`,
`BootOrder=0001,0004,0000,0002`, no Ubuntu entry, a read-only ESP, and unchanged
fallback/SP12 payload hashes. The guard verification passes. This confirms
package-hook preservation, not firmware boot compatibility. Do not run the
release upgrade until stable metadata appears and all manual gates are resolved.

## Handoff checklist

### Completed

- Set the interim release track to `Prompt=normal` and applied reviewed
  ordinary 26.04 updates; `dpkg --audit` is clean and the current-suite APT
  simulation proposes no changes.
- Verified the maintained 7.3 kernel, initramfs and DTB against the active ESP
  payloads.
- Installed the local diversion guard. Reinstalled `shim-signed`,
  `grub2-common` and `grub-efi-arm64`; post-checks confirmed unchanged fallback
  and SP12 payload hashes, unchanged NVRAM, and a read-only ESP. The helper
  verification passes.

### Remaining before starting the release upgrade

1. Create and verify an independent full-system backup and a separate user-data
   backup; establish and test a recovery route. The ESP image is on the same
   disk and is not a system backup.
2. Review `iio-sensor-proxy`'s hold against the local sensor fork/build and the
   actual target plan. Preserve the working sensor integration or arrange a
   tested replacement; verify sensors after upgrading.
3. Review compatibility for R, ChatGPT, Tailscale, VS Code and Waydroid APT
   sources. R and Waydroid had no 26.10 suite metadata in the recorded checks;
   Waydroid is not installed. Decide which unsupported sources must be disabled
   for the upgrade and when they can be restored.
4. Test boot-sync ESP staging and rollback on a scratch ESP using the 26.10
   Rust `cp`, `mv` and `rm` implementations. Do not use the installed ESP.
5. After stable metadata advertises the supported 26.10 `UpgradeTool`, run the
   preflight and inspect the device's actual upgrader plan. Confirm it retains
   the maintained 7.3 kernel, recovery path and SP12 hooks; review every
   removal, repository change and configuration prompt; and validate free space
   against the actual plan.
6. Review the target 26.10 GRUB/shim maintainer scripts and confirm package
   hooks still use the diverted helper. The 26.04 guarded reinstall succeeded,
   but cannot validate target-version hooks.
7. Validate firmware boot compatibility for the custom GRUB through an agreed
   safe boot/recovery procedure. Package-hook preservation has passed; no
   firmware-to-shim-to-custom-GRUB boot test has been performed.

Do not run `do-release-upgrade` until the supported metadata is present and
these gates are closed. Do not use `-d` to bypass the metadata gate.

## When stable 26.10 metadata appears

1. Run `sudo sh scripts/sp12-upgrade-preflight`. Require the stable metadata
   check to pass. It validates a supported `Version: 26.10` stanza with an
   `UpgradeTool`; do not use `-d` or a development metadata endpoint.
2. Run `do-release-upgrade --check-dist-upgrade-only` and review its output.
   If it does not offer 26.10, stop. Never infer availability solely from the
   release date, package catalogue, or `Prompt=normal`.
3. Start the supported upgrader's preparation phase and inspect the complete
   proposed plan before accepting it. Confirm it retains the running kernel,
   recovery kernel, custom boot hooks, GRUB fallback loader strategy, required
   SP12 packages, and a usable local login/network path. Review every removal,
   third-party source disablement, and configuration-file prompt. Abort if the
   plan is truncated, unexpected, or cannot be restored from backup.
4. Start the release upgrade only after all manual gates above are closed and
   there is an independent full-system backup plus separate user-data backup.
   Keep power stable and a recovery route available throughout. After the
   upgrade, verify firmware-to-GRUB-to-kernel boot, display/touch/sensors,
   networking, storage, suspend/resume, package consistency, and the checks in
   [hardware-tests.md](hardware-tests.md).

The public package catalogue and metadata checks are supporting evidence only;
the release-upgrader's device-specific plan remains authoritative. Metadata
publication removes only one blocker and does not make this device ready by
itself.

Fresh 26.10 installer support is a separate task. `scripts/inspect-install-target`
currently accepts only 26.04; changing that guard alone would not establish
fresh-installer support. The in-place upgrade path is also not yet validated.

## Read-only command set

From the repository root on the Surface, after the updated script is present:

```bash
sudo sh scripts/sp12-upgrade-preflight
sudo cmp -s /boot/initrd.img-7.3.0-sp12-v7.3-platform /boot/efi/sp12/initrd.img \
  && echo 'initramfs ESP copy matches' || echo 'initramfs ESP copy differs'
do-release-upgrade --check-dist-upgrade-only
apt-get -s full-upgrade
```

The upgrader check is only meaningful for the desired interim track. Do not
start `do-release-upgrade` until every applicable gate above is resolved.

[announcement]: https://lists.ubuntu.com/archives/ubuntu-announce/2026-October/000330.html
[switch]: https://ubuntu.com/desktop/docs/en/latest/how-to/switch-between-an-lts-and-interim-release/
[metadata]: https://changelogs.ubuntu.com/meta-release
[upgrade]: https://ubuntu.com/desktop/docs/en/latest/how-to/upgrade-ubuntu-desktop/
[notes]: https://documentation.ubuntu.com/release-notes/26.10/
[sensor-2610]: https://packages.ubuntu.com/stonking/iio-sensor-proxy
[grub-common-2610]: https://packages.ubuntu.com/stonking/arm64/grub2-common
[shim-2610]: https://packages.ubuntu.com/stonking/shim-signed
