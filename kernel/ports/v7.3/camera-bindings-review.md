# Camera binding review

Reviewed on 2026-10-22 against the complete Linux 7.3 source, the reconciled
camera files in `.cache/camera-reconciled`, and the preserved Surface 0012
board patch. The resulting `patches/0012-camera-bindings.patch` changes only
camera bindings. It supplies no new patch author or DCO sign-off.

## Existing upstream coverage

- `media/qcom,x1e80100-camss.yaml` already exists. Its X1E resource names,
  resource counts, direct-PHY supply requirements and existing example are
  preserved. The patch adds conditional X1P constraints and the new generic
  PHY child representation instead of replacing the original binding.
- `i2c/qcom,i2c-cci.yaml` already accepts `qcom,x1e80100-cci` followed by
  `qcom,msm8996-cci`, with `camnoc_axi`, `cpas_ahb` and `cci` clocks. This
  matches both reconciled CCI nodes. No CCI schema change is necessary.
- `ovti,ov02e10.yaml` already documents both `ovti,ov02e10` and
  `ovti,ov02c10`. The patch extends its OV02C10 constraints conditionally,
  preserving OV02E10 behavior. OV13858 and the generic PHY compatible need
  new schemas. No second schema matching OV02C10 is introduced.

## Resource constraints

The CAMSS extension specifies X1P's 14 register regions, 22 clocks, 10
interrupts, two power domains and two PHY providers using the exact ordered
names in the reconciled `purwa.dtsi`. X1E retains its 17 regions, 29 clocks,
13 interrupts and three power domains. Its generic-PHY form has four PHY
providers. Both generic-PHY forms use the five IOMMU entries in the current
reference layout. The legacy X1E form retains its existing eight-entry rule.
Interconnect names and counts remain unchanged.

When `phys` is present, CAMSS requires `phy-names`, child address/size cells
and `ranges`; its PHY children are validated against the dedicated PHY
schema. When `phys` is absent, the original parent analog supplies remain
required. Existing unnumbered CAMSS endpoints retain their original schema.
The new numbered endpoint form permits unconnected SoC placeholders, and
requires data lanes when a remote endpoint is specified.

The PHY schema matches the actual new driver's three clock names
(`core`, `timer`, `ahb`), its three power domains (`top`, `mmcx`, `mx`),
its OPP-table reference, its two analog supplies and its one-cell D-PHY
specifier. It describes input graph ports 0/1 and output port 2. Input lane
indices are zero-based, matching the reference PHY nodes. Sensor lane
indices are one-based, matching their separate sensor endpoints.

The OV13858 and conditional OV02C10 schemas require their actual power supplies, one clock, an I2C
address and a CSI2 endpoint. OV13858 supports the driver's four data lanes
and 540/270 MHz link frequencies; OV02C10 supports one or two lanes and
400 MHz. Shared video-device properties cover rotation, orientation and
the privacy LED reference without adding private properties.

Both drivers reject an external clock rate other than 19.2 MHz. The schemas
document that rate and constrain `assigned-clock-rates`, if present, to
19200000. They also declare the corresponding optional `assigned-clocks`
property as required by the DT clock meta-schema.

## Architectural and hardware limits

1. The reconstructed reference already contains an OV02C10 mismatch: its
   driver requires 19.2 MHz, while its board node assigns 12 MHz. This is not
   a new merge regression. A 12 MHz board assignment must not be accepted
   by widening the schema. Correcting the assignment to match the driver
   is a local candidate delta; it does not establish sensor PLL or capture
   correctness. Keep the sensor disabled until physical testing validates
   the clock and actual capture. No PLL register values were invented.
2. The CAMSS parent retains redundant `csiphy*` regions and interrupts
   while child PHY nodes describe those same hardware resources. In the
   reconciled driver, the generic-PHY path skips the legacy CSIPHY register
   mapping and delegates PHY control to providers. The binding documents
   that current representation; it does not prove exclusive resource
   ownership during boot or establish that this ABI is suitable upstream.
3. Purwa deletes PHY1/2 but initially inherits Hamoa ports 2/3. Its actual
   two-PHY topology requires those stale ports to be deleted. The X1P
   schema rejects ports 2/3. Parent DTS reconciliation owns that correction.
4. The reference X1P register list contains TPG regions although the X1P
   CAMSS resource structure does not register TPG subdevices. They are
   retained as the supplied layout; their hardware functionality is not
   asserted. The binding does not enable TPG support.
5. YAML validation establishes schema correctness and catches described
   resource mismatches. It cannot establish analog voltages, physical
   wiring, sensor reset timing, privacy behavior, frame capture, or PM
   correctness. Hardware validation and the full kernel build remain
   separate gates.

Maintainer entries refer to existing upstream subsystem or driver owners
(Bryan O'Donoghue and Sakari Ailus); they are not new author
identities, sign-offs or claims of maintainer acceptance. Resolve originating
patch provenance and submission review before publication.

## Validation

The patch applied with `git apply --whitespace=error` to a complete isolated
copy of the upstream binding tree at `/var/tmp/sp12-bindings-review`. The
shared kernel source tree was not modified by this review.

All four changed/new YAML documents passed `dt-doc-validate` with reference
resolution against that complete copy, using the parent's installed dtschema
environment `/tmp/sp12-dt-tools`. An earlier validation against only the new
files reported missing references; that incomplete test was replaced by
validation against the complete tree. Full-tree schema preprocessing also
identified the existing combined OV02E10/OV02C10 binding, so an initial
duplicate standalone OV02C10 draft was discarded before integration.

An initial full schema compilation ran out of space on WSL's memory-backed
`/tmp`; its truncated JSON output was discarded. This review's temporary
copies were removed, and subsequent validation uses disk-backed `/var/tmp`.
The final complete-tree `dt-mk-schema -j` run completed successfully without
diagnostics and wrote `/var/tmp/sp12-bindings-review-processed.json`. The final
patch also passed `git apply --check --whitespace=error` against pristine 7.3.

Run the integrated candidate's targeted `dt_binding_check` and `dtbs_check`
after applying the board correction and ordered patches. Compare results
against pristine 7.3 so existing board warnings are distinguishable from
candidate regressions. Document validation is not a claim that those
integrated checks, compilation or physical camera testing have passed.

## Integrated follow-up

The integrated driver-object and SP12 DTB builds subsequently passed. Targeted
`dt_binding_check` initially exposed the existing sensor examples' standard
`assigned-clock-parents` property as unevaluated; the combined OV02E10/OV02C10
schema now declares that property alongside assigned clocks/rates. The final
binding-example, document, YAML lint/style and candidate DT schema checks pass.
This preserves existing OV02E10 example behavior and does not change clock wiring.
Camera runtime nodes remain disabled and hardware validation remains outstanding.
