# Installed-system templates

This directory mirrors files installed under `/etc` and `/usr/local`. Files here
are reviewed templates; copying the directory wholesale is not supported.

Use the guarded installers under `scripts/`. They validate the exact SP12 model,
required source files, file ownership context, and explicit `--apply` consent.

## Boot synchronization

`/etc/sp12-linux/boot.conf` pins an exact kernel release and DTB. The synchronization
helper never consults Ubuntu's generic kernel symlinks.

After selecting a new custom kernel, update both values together and run:

```bash
sudo /usr/local/sbin/sp12-sync-boot
sudo scripts/sp12-verify
```

Keep a separately named recovery payload until all hardware checks pass.

## Power policy

The included power policy reproduces settings measured on the reference tablet.
It does not install the reference owner's device-specific USB receiver rules.
Users should add autosuspend rules only for devices they have tested.
