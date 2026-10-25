# Ubuntu 26.04 legacy notes

Ubuntu 26.10 with custom SP12 Linux 7.3 is now the main configuration.
Ubuntu 26.04 remains documented for existing systems and earlier test evidence.
It is not the default for new image builds.

- Keep a working 26.04 system until you have a separate backup and a tested
  installation or upgrade plan. This change in project focus does not upgrade it.
- The custom 7.3 kernel was tested on an existing 26.04 installation. Earlier
  7.2 results are historical, not the maintained kernel line.
- Use `--ubuntu-version 26.04` explicitly with `scripts/build-installer` when
  reproducing the older stock-live image. The maintained-live builder is for 26.10.
- The [maintenance guide](maintenance.md) still describes the guarded boot-file
  tools; verify your exact selected kernel and DTB before using them.

## In-place upgrades

Do not change APT release names to force 26.10. ISO availability does not prove
that Ubuntu's release upgrader offers the same transition.
From a current repository checkout, inspect preparation without querying offers:

```bash
sudo scripts/sp12-upgrade-preflight --skip-release-metadata
```

`MANUAL` or `NOT READY` means more work is required. This option intentionally
does not establish release availability. Later, the default preflight checks
stable metadata; never use `do-release-upgrade -d` to bypass it.
Review the actual package/removal plan, GRUB/shim hooks, held packages, third-party
repositories, space, backups and recovery before allowing an upgrade.

[Earlier hardware results](developer/records/hardware-2026-10-23.md) ·
[Preparation evidence](developer/records/upgrade-preparation-2026-10-24.md)
