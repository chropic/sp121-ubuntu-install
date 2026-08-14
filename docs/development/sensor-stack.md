# Reproducible sensor stack

The working reference system uses three separately maintained GPL components:

1. `libssc` 0.4.4 at `f6dfbfa5f34ef22f3d47ef346c22834e79c60df1`;
2. Harrison van der Byl's Hexagon RPC 0.4.0 fork at
   `78b67e2f00df0455f0c0282183b1b1b8b219447d`;
3. Harrison's IIO Sensor Proxy 3.9 fork at
   `fcd5b5cf431bc053375350c57064b8b13dd961b4`, built with
   `-Dssc-support=enabled` and prefix `/usr/local`.

These revisions predate the 2026-08-13 reference installation, remain the heads
of their respective tested branches, and report the same versions as the live
installed artifacts. Exact reference binary hashes are recorded in
[`firmware/sources.yaml`](../../firmware/sources.yaml).

## Why the original installer is not used

The original support script cloned three moving branches, recursively copied a
large `usr/` tree, removed its build checkouts, wrote service files with shell
heredocs, and held a distribution package. That proved the stack could work, but
it cannot establish which source built a future binary or make partial failures
easy to recover from.

The replacement must:

- verify all three origins and commits before compiling;
- build in the order `libssc`, Hexagon RPC, then IIO Sensor Proxy;
- use `/usr/local` consistently and run `ldconfig` only after successful install;
- install the service and udev files from reviewed repository templates;
- use `/dev/fastrpc-adsp`, not the older `/dev/fastrpc-adsp-secure` spelling;
- add the `ssc-accel` udev tag needed by the tested fork;
- never embed the Qualcomm DSP binaries in this repository or its releases;
- provide a preview and staged destination before writing the live root;
- verify accelerometer, ambient light, and compass independently after reboot.

Until that builder and its clean-machine test exist, the numbered beginner guide
intentionally treats a fresh sensor installation as unfinished. This is a release
gate, not an invitation to run the old moving-branch script.
