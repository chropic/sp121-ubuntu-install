# Build records and release requirements

Ubuntu 26.10 ARM64 with custom SP12 Linux 7.3 is the main configuration.
**Fresh installation and recovery are experimental and not fully vetted.**
The [user guide](../docs/install.md) is the single installation entry point.

## Records

- [Private live v2](CANDIDATE-26.10-private-live-v2.json): audited maintained-kernel
  image; owner confirmed the kernel and working live hardware.
- [Earlier 26.10 candidate](CANDIDATE-26.10.json): generic live kernel; Wi-Fi and
  sound failed. It is not the main configuration.
- [Historical installer audit](CANDIDATE.json) and [reference build](reference/BUILDINFO.json):
  earlier evidence, not current release artifacts.
- `upgrade-preparation/`: authenticated package/runtime and diagnostic evidence
  for the earlier 26.04 upgrade assessment.

## Before publishing an image

- Complete fresh installation on an explicitly authorized recoverable target.
- Verify installed boot, required device files and the fallback loader.
- Test recovery and record individual hardware results.
- Rebuild from the final source revision and repeat offline and physical checks.
- Publish checksums, build provenance and corresponding kernel source.
- Resolve distribution terms for every included component.

Publish source and tooling while these gates are open. Do not upload the private
image or the third-party firmware/DSP files excluded by the
[device-file policy](../firmware/README.md). Binary ISO, kernel and DTB files do
not belong in Git. Making 26.10 the main configuration does not waive these gates.
