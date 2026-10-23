# Contributing

Changes should make the supported installation safer, more reproducible, or more
accurate on physical Surface Pro 12 hardware.

## Requirements

- Separate observations from assumptions.
- Record exact hardware, kernel, DTB, and package versions.
- Preserve original authorship and DCO trailers on patches.
- Never force a conflicting patch involving regulators, reserved memory, firmware,
  power domains, or device-tree wiring.
- Add a rollback procedure for boot, storage, power, or firmware changes.
- Redact personal and secret data from logs.
- Do not add proprietary firmware or Microsoft binaries.

Documentation should define unfamiliar terms, show expected output, and include a
clear stop condition wherever continuing could damage data or make the device
unbootable.

## Find the right place

User procedures belong in [`docs/`](docs/README.md); detailed kernel review and
validation belong beside the [port](kernel/ports/v7.3/README.md). Keep the root
README focused on scope, status and navigation. Preserve historical reference
notes and patch authorship; update current status where users enter the project.

Run `scripts/check-repository` before submitting changes. Record which checks
ran and distinguish build checks from physical tests.
