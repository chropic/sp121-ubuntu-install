# Updating and maintenance

Ordinary package updates are permitted, but the ESP payload remains explicitly
pinned.

```bash
sudo apt update
sudo apt upgrade
```

Before removing any kernel:

```bash
uname -r
dpkg-query -W 'linux-image*' 'linux-headers*' 2>/dev/null
```

Never purge the release printed by `uname -r` or the retained recovery release.
Do not install `-dbg` kernel packages unless kernel symbol debugging is intentional;
they consume several gigabytes.

## Kernel release sets

Changing the active custom kernel requires all of the following:

1. install the exact image and header packages;
2. generate the matching initramfs;
3. select the matching compiled DTB;
4. update both the pinned kernel release and DTB path in the ESP synchronization
   helper;
5. synchronize the three files;
6. compare all three source and destination files;
7. preserve the previous recovery set;
8. reboot and complete the hardware verification checklist.

APT's generic kernel symlinks must never choose the ESP payload automatically.
