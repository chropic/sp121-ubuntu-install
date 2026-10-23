# Surface RTC and suspend review

Reviewed on 2026-10-22 against Linux `v7.3`, commit
`c03c1a14507dfaf8b856c2608f9ac216021fc222`, the preserved vendor Surface
0004/0005/0006 files, and the tested-reference aggregate patch.

## Selected candidate changes

1. `patches/0002-rtc-surface-port-reference-driver.patch` adds the reference
   RTC driver and refreshes its Kconfig/Makefile context for 7.3. The driver's
   129-line content is identical to both vendor 0004 and the aggregate new-file
   postimage (`f6c17c4e98d5f15a529a2f808226fbb25974ee9c`). Its Kconfig help
   replaces the vendor `TODO`; dependencies and module name are unchanged.
2. `patches/0003-surface-register-sp12-rtc.patch` adds software node
   `ssam:01:01:01:00:00` only to `ssam_node_group_sp12in`, preserving vendor
   0005 and the aggregate registration semantics. No new DT property or
   binding is needed for this software node.
3. `patches/0004-surface-scope-sp12-suspend-workaround.patch` preserves the
   reference's `d3_closes_handle = false` only when the root DT compatible
   contains `microsoft,surface-pro-12in`. Every other OF model retains the
   upstream `true` default. The ACPI capability loader is unchanged.

These are development changes; successful patch application does not establish
that the RTC firmware protocol or suspend behavior works on this kernel.

## RTC API and protocol review

- Linux 7.3 `include/linux/surface_aggregator/device.h` includes the controller
  API, provides `ssam_device_set_drvdata()`, and retains the `int probe` and
  `void remove` callbacks used here. The empty managed-resource remove callback
  is permitted by the current bus implementation.
- `SSAM_DEFINE_SYNC_REQUEST_R/W` in the pinned controller header accepts
  `struct ssam_controller *` and a typed response/argument pointer. The read
  macro verifies the returned payload size. The reference calls match these
  signatures and retain error propagation and little-endian conversion.
- `SSAM_SDEV(SAM, SAM, 0x00, 0x00)` matches the registry UID's serial-hub
  domain, SAM category, SAM target, instance zero and function zero. Read
  command `0x10` and write command `0x0f` remain the supplied reference values;
  no independent firmware specification or fresh hardware trace was available.
- `include/linux/rtc.h` retains `devm_rtc_allocate_device()`,
  `devm_rtc_register_device()`, the read/set callback signatures and
  `rtc_time64_to_tm()`/`rtc_tm_to_time64()`. Managed allocation and registration
  match the upstream driver pattern.
- The driver exposes the unsigned 32-bit Unix-second range, with the default
  zero minimum and `U32_MAX` maximum. `drivers/rtc/interface.c` validates the
  range before the set callback, so its reference cast to `u32` follows the
  RTC core range check. The 32-bit firmware limit remains unchanged.
- No alarm, wake-alarm or correction support is implemented. The 7.3 RTC core
  clears `RTC_FEATURE_ALARM` when `set_alarm` is absent, so no invented alarm
  implementation or duplicate feature clearing was added.

The copied source still has the original misleading introductory phrase
`AC driver for 7th-generation` in its comment. It is retained with the rest of
the byte-identical historical driver; it is not a reviewed hardware-support
claim. Registration is limited to the SP12 group in this candidate.

## Suspend scope and limitations

Vendor 0006 and the aggregate change the OF default globally. The supplied
reference concerns SP12, and that evidence does not justify changing other
Surface models. The scoped port adds `<linux/of.h>` and uses the same root
compatible already selected by the SP12 registry and board DTS. It needs no
new DT binding. An unrelated OF machine does not match; a controller with an
ACPI handle follows the existing ACPI path before the OF loader is entered.

`ssam_ctrl_notif_d0_exit()` and `ssam_ctrl_notif_d0_entry()` return immediately
when this capability is false. Thus this port suppresses both corresponding
EC notifications on SP12, just as the aggregate did. Upstream comments state
that the notifications' exact EC effects are unknown. The change therefore
preserves a reference workaround, not a newly established explanation or fix
for 7.3 suspend. Repeated suspend/resume, keyboard reattachment, battery state,
wake behavior and power consumption require physical verification. Revisit
or remove the workaround if controlled hardware testing establishes that 7.3
does not need it.

## Provenance

Vendor 0004 contains `Signed-off-by: Maximilian Luz <luzmaximilian@gmail.com>`
and a `Patchset: surface-sam` marker; its source contains the original copyright
and module author. Those source notices are preserved. The input lacks a
complete originating commit/message, and vendor 0005/0006 lack author/DCO
trailers. No new author identity or sign-off is asserted for the regenerated
patches. Preserve the original vendor files and resolve publication provenance
before releasing the series or binaries.

## Verification performed

All three patches passed, as one ordered invocation, from the repository root:

```sh
git -C .cache/linux-7.3 apply --check --whitespace=error \
  ../../kernel/ports/v7.3/patches/0002-rtc-surface-port-reference-driver.patch \
  ../../kernel/ports/v7.3/patches/0003-surface-register-sp12-rtc.patch \
  ../../kernel/ports/v7.3/patches/0004-surface-scope-sp12-suspend-workaround.patch
```

A script extracted the RTC additions from vendor 0004 and the aggregate and
asserted byte equality and the 129-line count before producing the patch.
The pinned upstream SSAM/RTC headers, RTC core range/alarm handling and SSAM
bus removal path were read directly; missing header blobs were fetched through
`git show` without checking them out. The source checkout was not modified by
this review; its pre-existing volume-button DTS change was left in place.

This static review did not itself compile or run hardware. Subsequent integration
authenticated the source tag, migrated configuration and compiled the RTC/SAM
objects in the complete candidate source. Integrated build results are recorded
under `validation/`. Physical RTC persistence, suspend/resume and suspend power
tests remain required; compilation does not establish those results.
