# INC-002 — Billing Rounding: Midpoint Prices Rounded to Even Instead of Away-from-Zero

| Field | Value |
|---|---|
| **ID** | INC-002 |
| **Severity** | Medium |
| **Status** | OPEN (bug present, no fix applied) |
| **Component** | `app/Invoke-Calculator.ps1` -> `ConvertTo-DiscountedPrice` |
| **Reporter** | BobGuard MVP demo (Prompt 3) |
| **Environment** | PowerShell 5.1 / .NET 8 runtime, local dev (synthetic) |
| **Independent of** | INC-001 (different function, different root cause) |

## Summary

`ConvertTo-DiscountedPrice` uses `[Math]::Round($value, 2)` without specifying a
`MidpointRounding` mode. .NET's default is `MidpointRounding.ToEven` (Banker's
Rounding): when the value is exactly halfway between two representable decimals, it
rounds to the nearest *even* digit.

A billing pipeline requires standard arithmetic rounding (`AwayFromZero`): midpoint
values must always round up. Using Banker's Rounding causes invoice line items to be
under-billed by $0.01 for any price/discount combination that produces an exact
half-cent intermediate value.

## Reproduction

```powershell
# From workspace root -- no fix applied
. .\app\Invoke-Calculator.ps1

# Case 1: $0.25 at 10% discount -> $0.225 -> should be $0.23, gets $0.22
ConvertTo-DiscountedPrice -UnitPrice 0.25 -DiscountPct 10
# Expected: 0.23   (AwayFromZero)
# Actual:   0.22   (ToEven -- 2 is even)

# Case 2: $0.05 at 50% discount -> $0.025 -> should be $0.03, gets $0.02
ConvertTo-DiscountedPrice -UnitPrice 0.05 -DiscountPct 50
# Expected: 0.03   (AwayFromZero)
# Actual:   0.02   (ToEven -- 2 is even)
```

## Stack Trace

> SYNTHETIC / LABELED -- constructed to match the implemented source.
> No production deployment or real financial impact occurred.

```
ConvertTo-DiscountedPrice: return [Math]::Round($UnitPrice * (1 - $DiscountPct / 100), 2)
  <- app/Invoke-Calculator.ps1 line 49
  UnitPrice=0.25, DiscountPct=10
  Intermediate: 0.25 * 0.90 = 0.225  (exact half-cent)
  [Math]::Round(0.225, 2) = 0.22     <- MidpointRounding.ToEven (rounds to even digit)
  Expected result: 0.23              <- MidpointRounding.AwayFromZero
  Effect: invoice line item under-billed by $0.01
```

## Root Cause

`[Math]::Round(value, digits)` in .NET uses `MidpointRounding.ToEven` by default.
The two-argument overload does not accept a rounding mode.
The fix requires the three-argument overload:

```powershell
# Buggy (current):
return [Math]::Round($UnitPrice * (1 - $DiscountPct / 100), 2)

# Fixed (NOT applied -- INC-002 is open):
return [Math]::Round($UnitPrice * (1 - $DiscountPct / 100), 2, [System.MidpointRounding]::AwayFromZero)
```

## Deployment History

> NOT APPLICABLE -- local dev workspace, no CI/CD pipeline.

## Rollback Plan

> NOT APPLICABLE -- bug has never been fixed; rollback would mean keeping the
> current behavior, which is intentionally left in place for INC-002 demonstration.

## Affected Cases

Only midpoint values (where `intermediate % 0.01 == 0.005`) are affected.
Non-midpoint values round identically under both modes.

| Input | Intermediate | ToEven (buggy) | AwayFromZero (expected) | Delta |
|---|---|---|---|---|
| $0.25 @ 10% | $0.225 | $0.22 | $0.23 | -$0.01 |
| $0.05 @ 50% | $0.025 | $0.02 | $0.03 | -$0.01 |
| $1.00 @ 10% | $0.90  | $0.90 | $0.90 | $0.00  |
| $99.99 @ 33.33% | $66.6600... | $66.66 | $66.66 | $0.00 |
