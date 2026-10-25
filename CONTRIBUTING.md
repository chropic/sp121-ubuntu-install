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

Keep user steps in the [installation](docs/install.md) or
[maintenance](docs/maintenance.md) guide. Put technical explanations and dated
test records under [developer references](docs/developer/README.md). Keep kernel
build inputs beside the [kernel guide](kernel/ports/v7.3/README.md).
Link to an existing procedure instead of copying it. Use short sentences and
explain new technical terms. Keep the README focused on status and navigation.
Preserve historical source notes and patch authorship.

Run `scripts/check-repository` before submitting changes. Record which checks
ran and distinguish build checks from physical tests.
