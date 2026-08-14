# Quick start

This page assumes you have never installed Linux before. Read it once before
running anything.

> [!CAUTION]
> Installing an operating system can erase every file on the tablet. The first
> public installer has not been released yet. This page currently takes you only
> through safe preparation and hardware identification.

## 1. Confirm you have the correct tablet

You need the **Surface Pro 12-inch, 1st Edition with Snapdragon X Plus**. A
Surface with an Intel processor is not supported by these instructions.

When booted into a Linux live environment, open Terminal and run:

```bash
./scripts/sp12-preflight
```

Continue only if the final line says:

```text
RESULT: PASS -- supported Surface Pro 12 hardware detected
```

## 2. Prepare recovery before installation

You need:

- another computer with Linux and internet access;
- one USB drive for the installer;
- a second USB drive or external disk for backups;
- the tablet's charger;
- a copy of every personal file you care about;
- enough uninterrupted time to recover if the first boot fails.

Do not use the only copy of an important file as installation media.

## 3. Know the firmware controls

With the tablet powered off:

- hold **Volume Up** while pressing Power to enter Surface UEFI;
- hold **Volume Down** while pressing Power to boot from USB.

The tested unsigned boot path requires Secure Boot to be disabled. Record the
original setting before changing it.

## 4. Stop here for now

The reproducible installer builder and signed release manifest are still being
prepared. Until the project publishes a release marked **installation-tested**,
use the detailed source guide only if you are comfortable recovering the ESP by
hand.

Next reading: [Before you start](docs/00-before-you-start.md).
