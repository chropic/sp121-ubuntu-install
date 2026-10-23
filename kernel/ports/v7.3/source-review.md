# Reconciled source decisions

The reference is the aggregate at SHA-256
`02450df6b1996572e1d76571b10cb279d4f8b7b2a0c5d777a6243623ecc3744d`,
not a sequential application of the 37 vendor files. All 25 postimages were
reconstructed and verified against the supplied audit before reconciliation.

## Platform profile

The upstream board, SAM registration, QSEECOM allowlist and Sharp panel entry
replace their duplicate reference additions. The original volume patch keeps
GPIO and pinctrl mappings together. DP audio and charge NVMEM reproduce the
reference board additions without enabling a userspace charge policy or writing
an unknown threshold interface. Their runtime status remains experimental.

RTC source and registration are separate patches. The driver is byte-identical
to the reference; its Kconfig help is completed. The suspend workaround is scoped
to `microsoft,surface-pro-12in`, preserving the reference behavior on SP12 while
keeping other OF models and ACPI unchanged. See `rtc-suspend-review.md` for the
firmware/API review and remaining physical tests.

The display regulator rewrite, RF-kill flag, explicit IRIS override and CMA
removal in the vendor corpus are absent from the reconstructed reference and
are not imported. Upstream display wiring and the board's 512 MiB CMA reservation
are preserved. Touchscreen GPIOs remain 38/48. No proprietary firmware is added.

## Camera profile

Camera patches are an additional, explicit profile. Existing files were merged
three ways using pristine 7.3 as the retained side, pristine 7.2-rc7 as the base,
and verified reference postimages as the downstream side. New reference PHY
files retain their notices. No upstream file was replaced with an old postimage.

PHY, CAMSS and sensor code merged without textual conflicts. The two DT conflicts
were upstream CAMCC nodes alongside larger reference camera additions. The
merged result keeps the upstream CAMCC text and adds the camera nodes. Purwa's
duplicated video-clock include is removed. Inherited CAMSS ports 2/3 are deleted
on X1P, whose reference PHY list contains only PHY0 and PHY4; properties precede
delete directives as required by DTC. Three unused locals exposed by compilation
are removed in a separate patch without changing runtime behavior.

The CAMCC driver was already present in the exact 7.2 reference base and is not
modified by the aggregate. Its change from that base to 7.3 consists only of
three `const` qualifications (critical-CBCR array, driver data and descriptor).
The vendor CAMCC submission is therefore not the tested driver's postimage.
Keep the upstream driver; no clock frequencies, PLL settings, reset IDs or GDSC
assignments are replaced by the older vendor submission.

The OV13858 delta is taken from the reconciled aggregate. Rejected individual
sensor patches are not forced. OV02C10 retains the reference exposure/selection
changes on top of upstream. Both sensor drivers, the new PHY and CAMSS are
compiled for the camera profile; this does not establish a working media graph
or capture.

The reference board requests 12 MHz for OV02C10 while both the reference and
merged driver reject everything except 19.2 MHz. The staged board requests
19.2 MHz to match that driver; no PLL register tables are invented. Sensor,
CCI, CAMSS, PHY and privacy-LED nodes remain disabled in this profile. Actual
clocking, supply behavior, graph/capture, start/stop and privacy indication must
be verified on hardware before runtime enablement. The unused commented VD55G1
sketch remains inactive; it is not an enabled third camera.

Read-only inspection of the actual 7.2 SP12 subsequently found OV02C10 bound
with the 12 MHz DT request and matching source still checking 19.2 MHz. Thus
the requested DT rate alone does not prove the actual provider rate or a probe
failure. The user's privileged debugfs readback subsequently reported
`cam_cc_mclk4_clk_src` at 19.2 MHz, with enable/prepare/protect counts all zero.
This establishes the idle source rate on the existing 7.2 system; active sensor
clocking and capture remain untested. Do not interpret the staged 19.2 MHz
request as a capture-proven fix.

The new/extended schemas describe the candidate ABI without relaxing unrelated
bindings. Existing CCI support already covers the reference compatible. See
`camera-bindings-review.md` for exact schema decisions, including the redundant
parent descriptions of PHY resources; the generic PHY path obtains its own
provider and does not map the parent's legacy PHY ranges.

## Source and publication identity

The full official source tarball was verified with Greg Kroah-Hartman's key;
the Git tag was verified with Linus Torvalds's key. Keys were obtained through
Kernel.org WKD and their fingerprints matched Kernel.org's HTTPS signature
documentation. The extracted source tree also matched the signed tag tree
`30fd2ef82912c26cf3a58ad0ba6afc375fa851ac`. No personal Web-of-Trust
certification is asserted by these checks.

Original vendor files and source copyright/module-author notices remain intact.
Regenerated patches identify their reference derivation without inventing an
author or a DCO sign-off. Missing origin metadata remains a publication task;
local candidate compilation does not establish permission to publish under an
invented identity or prove hardware support.
