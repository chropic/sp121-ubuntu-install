# Security policy

## Supported versions

No public release is supported yet. Security support will begin with the first
release explicitly marked supported.

## Reporting a vulnerability

Do not open a public issue for a vulnerability that could enable arbitrary code
execution, malicious release substitution, unsafe disk selection, or boot-chain
compromise. Contact the repository owner privately through GitHub Security
Advisories once the public repository is created.

## Trust model

The current tested boot path is unsigned and requires Secure Boot to be disabled.
Checksums detect accidental corruption but do not authenticate an untrusted mirror.
Release signing and provenance must be implemented before binaries are presented
as a stable installation path.

Never upload proprietary firmware, private Secure Boot keys, Wi-Fi credentials,
BitLocker recovery keys, or unredacted diagnostic archives.
