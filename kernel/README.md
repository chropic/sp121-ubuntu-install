# SP12 kernel

The tested release is based on Linux `v7.2-rc7`, commit
`db2ddb87143519e20a95aa36c60b36107b736a58`.

## Reproduction inputs

- `config/config-7.2.0-rc7-sp12-extra-camera` — byte-identical to the running
  kernel configuration.
- `patches/release/0001-...working-tree.patch` — exact aggregate difference
  between pristine `v7.2-rc7` and the source tree that produced the tested build.
- `patches/vendor/mias/` — the original patch corpus at Gentoo-overlay commit
  `877e0707f816b83ef8ce66a23277febdc2ff6448`, retained for authorship,
  review history, and reconstruction of a clean series.

The aggregate snapshot is presently the reproducible release input. It is not a
claim that one person authored the combined changes. Original authorship belongs
to the metadata in the vendor patches and their upstream submissions.

## Prepare and build

Start with a clean checkout of the exact base, then preview:

```bash
kernel/prepare-tree --source /path/to/linux-v7.2-rc7
```

Apply only after reviewing the base commit and snapshot hash:

```bash
kernel/prepare-tree --source /path/to/linux-v7.2-rc7 --apply
kernel/build-packages --source /path/to/linux-v7.2-rc7
```

Compilation is parallel; Debian packaging is deliberately serial to avoid the
observed DTB installation race. The scripts never install the resulting packages.

Do not distribute a kernel binary without the base reference, aggregate snapshot,
config, original patch corpus, build information, and checksums.
