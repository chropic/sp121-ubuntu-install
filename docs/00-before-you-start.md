# Before you start

## What the installer changes

The intended installation creates Linux filesystems on the selected disk and a
fallback ARM64 bootloader on the EFI System Partition (ESP). The fallback loader
reads a fixed kernel, initramfs, and device tree from the FAT ESP, then mounts the
Linux root filesystem by UUID.

An incorrect disk selection can destroy another operating system and its data.

## Required backups

Back up personal files to storage that will not be attached while partitioning.
If preserving Windows, also create Microsoft's recovery media and save any
BitLocker recovery key before changing firmware or partitions.

Verify the backup by opening several files from the backup device.

## Required equipment

- Surface Pro 12-inch, 1st Edition (`X1P42100`)
- Surface charger
- reliable USB installer drive
- separate backup or recovery drive
- USB keyboard if the Type Cover is unavailable in the live environment
- another internet-connected computer

## Stop conditions

Stop immediately if any of these is true:

- `scripts/sp12-preflight` reports the wrong model or architecture;
- the internal UFS disk is not visible;
- the installer cannot mount its target root and ESP;
- the download checksum does not match;
- any command names a disk you did not intentionally select;
- the known-good recovery files have not been preserved;
- power is unreliable.

Do not “try anyway.” A missing UFS device or mismatched DTB is a platform problem,
not an installer prompt to click through.

## Current limitations

- Secure Boot is disabled in the tested setup.
- Hibernate is not validated.
- Camera nodes in a DTB do not prove that camera capture works.
- Suspend must be tested repeatedly with saved work.
- Linux charge-threshold attributes must not be written until their meaning and
  valid range are known.
