# ADR-001 — Pagination Strategy for Billing Export

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-09-01 |
| **Deciders** | Backend team |
| **Related incident** | INC-001 |

## Context

The billing export pipeline fetches records in pages to limit memory usage.
The number of pages must be computed before the fetch loop begins.

## Decision

Use **ceiling integer division** for total-page count:

```
total_pages = ceil(count / page_size)
```

This ensures that a trailing partial page (when `count % page_size != 0`) is
always included.

## Alternatives Considered

| Option | Reason rejected |
|---|---|
| Integer truncation `count / page_size` | Silently drops the last partial page — **root cause of INC-001** |
| Always over-fetch by 1 page | Unnecessary extra API call when data divides evenly |

## Consequences

- All partial pages are included in the export.
- The fetch loop must handle empty results gracefully (already implemented in `Get-PagedItems`).
