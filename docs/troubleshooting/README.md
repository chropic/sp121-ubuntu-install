# Troubleshooting

Start by creating the privacy-conscious inventory report:

```bash
scripts/sp12-diagnostics --output ~/sp12-diagnostics.txt
```

The report excludes journals, filesystem UUIDs, MAC addresses, hostnames, and
firmware contents by design. Review it manually before sharing it.

## Device will not boot

Use [Recovery](../../GUIDE.md#9-recover). Restore a matching kernel, initramfs, and DTB
as a set. Do not start by rebuilding the kernel.

## Internal storage is missing

Stop installation. Confirm the exact device tree and inspect kernel messages from
the live environment. No partitioning command can repair a UFS controller that
never appeared.

## Display remains black

Confirm the DTB matches the tablet and kernel. Do not replace compressed GPU
firmware merely because an early uncompressed lookup failed; the kernel may load
the `.zst` file successfully afterward.

## Wi-Fi is absent

Confirm the WCN7850 board file exists, then inspect `ath12k` messages. Do not use a
board file from a different model simply because its filename is similar.

## Audio card exists but applications are silent

Confirm the exact topology, UCM file mode `0644`, PipeWire/WirePlumber state, and
speaker CPS controls. Do not remove speaker volume limits.

## Cameras are absent

List media entities first. Camera wiring scripts cannot create missing CAMSS,
CSIPHY, sensor, media, or video devices.

## A service says inactive

The power policy is a `Type=oneshot` service and normally becomes inactive after
success. Check `Result` and `ExecMainStatus` instead.
