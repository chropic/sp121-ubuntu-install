# Kernel patch provenance

## `release/`

The release snapshot was generated from the exact worktree that built
`7.2.0-rc7-sp12-extra-camera` package revision `7.2.0~rc7-6`. Applying it to the
documented base recreates every tracked modified file and every required new file
byte-for-byte. Generated `.orig` files and the patch-tool `err` file are excluded.

This snapshot exists because the tested worktree recorded applied and manually
reconciled patches as uncommitted changes. A falsely tidy series would be worse
than an honest aggregate diff.

## `vendor/mias/`

These are unmodified patch files copied from Mias van Klei's Gentoo overlay at:

```text
repository: https://github.com/miasvanklei/Gentoo-overlay
commit:     877e0707f816b83ef8ce66a23277febdc2ff6448
```

The Surface directory contains hardware enablement patches. The camera directory
contains the dependency and sensor series considered during the build. Not every
vendor patch is active: some were already present, some conflicted after earlier
patches, one OV13858 patch was deliberately not forced, and unrelated Surface Go
work is not part of the SP12 release.

Future work should split the exact release snapshot into a reviewed series while
preserving original authorship and demonstrating a byte-identical final tree.

