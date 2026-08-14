# Credits and acknowledgements

This project exists because multiple people and communities did the difficult
platform-enablement work first. Attribution belongs beside the work, not hidden
at the bottom of a release archive.

## Primary Surface Pro 12 enablement

- **Harrison van der Byl** — device tree, firmware layout, Wi-Fi, audio, sensors,
  cameras, Surface Aggregator work, and extensive hardware testing:
  <https://github.com/harrisonvanderbyl/surface-pro-12-inch-linux>
- **Mias van Klei** — Surface-specific kernel patches maintained through the
  Gentoo overlay:
  <https://github.com/miasvanklei/Gentoo-overlay/tree/master/sys-kernel/vanilla-kernel/files/surface>
- **François Roux / franzelverbier** — careful SP12 experiments and documentation,
  including panel, RTC, persistent-crash, and EL2/KVM investigations:
  <https://github.com/franzelverbier/surface-pro-12-linux>

## Upstream communities

We gratefully acknowledge the authors, reviewers, testers, and maintainers in the
Linux kernel DRM, ARM64, Qualcomm, ASoC, remoteproc, media, RTC, Surface Aggregator,
and device-tree communities. Every redistributed patch must retain its complete
author, review, test, sign-off, origin, and upstream-status metadata.

The Ubuntu Concept Snapdragon X Elite community supplied essential installation
and platform context:
<https://discourse.ubuntu.com/t/ubuntu-concept-snapdragon-x-elite/48800>

## Audio, Wi-Fi, and sensors

- **linux-msm audioreach-topology contributors** — open AudioReach topology
  compiler inputs and X1E80100 platform support:
  <https://github.com/linux-msm/audioreach-topology>
- **ALSA UCM configuration contributors** — the Surface Pro 12 UCM profile and
  corrected device routing:
  <https://github.com/alsa-project/alsa-ucm-conf>
- **Dylan Van Assche and libssc contributors** — userspace access to Qualcomm's
  sensor subsystem:
  <https://codeberg.org/DylanVanAssche/libssc>
- **Harrison van der Byl's Hexagon RPC and IIO Sensor Proxy forks** — the tested
  FastRPC daemon and SSC-enabled desktop sensor integration:
  <https://github.com/harrisonvanderbyl/hexagonrpc> and
  <https://github.com/harrisonvanderbyl/iio-sensor-proxy>
- **Daniel Whinham and Surface Pro 11 contributors** — the Wi-Fi board extraction
  approach adapted by the SP12 work:
  <https://github.com/dwhinham/linux-surface-pro-11>
- **Qualcomm Atheros open-source contributors** — `ath12k-bdencoder` in the QCA
  Swiss Army Knife, used to inspect and extract ath12k board bundles:
  <https://github.com/qca/qca-swiss-army-knife>
- **linux-firmware maintainers and firmware submitters** — the distribution
  firmware collection used by Ubuntu:
  <https://gitlab.com/kernel-firmware/linux-firmware>

Firmware and hardware names remain the property of their respective owners.
Microsoft, Qualcomm, Canonical, and the Linux kernel project do not endorse this
independent community project.

## Project testing

The original machine-specific guide and its measurements were assembled through
hands-on testing by the project owner with research and drafting assistance from
OpenAI Codex. Future contributors should add themselves here only for concrete
authorship, testing, review, documentation, or release work.
