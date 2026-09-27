# INC-002 -- Synthetic Application Log (pre-fix)

> **SYNTHETIC / LABELED** -- These log lines were constructed to match the
> implemented source at `app/Invoke-Calculator.ps1`. They are not from a
> running production system.

```
2026-09-27T09:00:01Z [INFO]  billing-invoice: generating line items  job_id=INV-20260927
2026-09-27T09:00:01Z [INFO]  billing-invoice: processing item  sku=ITEM-042 unit_price=0.25 discount_pct=10
2026-09-27T09:00:01Z [DEBUG] ConvertTo-DiscountedPrice called  unit_price=0.25 discount_pct=10
2026-09-27T09:00:01Z [DEBUG] ConvertTo-DiscountedPrice intermediate=0.225
2026-09-27T09:00:01Z [DEBUG] ConvertTo-DiscountedPrice result=0.22  <-- INCORRECT (should be 0.23)
2026-09-27T09:00:01Z [INFO]  billing-invoice: line item total=0.22  qty=1
2026-09-27T09:00:02Z [WARN]  billing-invoice: reconciliation mismatch  expected=0.23 actual=0.22 delta=-0.01 sku=ITEM-042
2026-09-27T09:00:02Z [ERROR] billing-invoice: audit check FAILED  job_id=INV-20260927 reason=rounding_discrepancy
```

## Analysis

- `ConvertTo-DiscountedPrice(0.25, 10)` returned `0.22` instead of `0.23`.
- Intermediate value `0.225` is an exact half-cent; .NET Banker's Rounding rounds
  to the nearest even digit (2), not away from zero (3).
- The reconciliation audit detected the $0.01 per-item discrepancy.
- Root cause: missing `MidpointRounding.AwayFromZero` argument -- see `incident.md`.
