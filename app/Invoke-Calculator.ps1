<#
.SYNOPSIS
    Minimal sample calculator module for BobGuard MVP.
    Provides arithmetic helpers used by a hypothetical billing pipeline.

.DESCRIPTION
    Functions:
      Get-PagedItems  - returns a page-slice of a list (zero-based page index)
      Get-TotalPages  - returns the total number of pages for a list and page size
      ConvertTo-DiscountedPrice - applies a percentage discount to a unit price

    INC-001 FIX APPLIED: Get-TotalPages now uses [Math]::Ceiling for correct
    ceiling division, ensuring trailing partial pages are never dropped.
#>

function Get-PagedItems {
    param(
        [object[]] $Items,
        [int]      $PageIndex,   # zero-based
        [int]      $PageSize = 10
    )
    if ($PageSize -le 0) { throw "PageSize must be positive." }
    if ($null -eq $Items -or $Items.Count -eq 0) { return [object[]]@() }
    $start = $PageIndex * $PageSize
    if ($start -ge $Items.Count) { return [object[]]@() }
    $end   = [Math]::Min($start + $PageSize, $Items.Count)
    return [object[]]($Items[$start..($end - 1)])
}

function Get-TotalPages {
    param(
        [int] $Count,
        [int] $PageSize = 10
    )
    if ($PageSize -le 0) { throw "PageSize must be positive." }

    # FIX (INC-001): use ceiling division to include the trailing partial page.
    return [Math]::Ceiling($Count / $PageSize)
}

function ConvertTo-DiscountedPrice {
    param(
        [decimal] $UnitPrice,
        [decimal] $DiscountPct   # 0-100
    )
    if ($DiscountPct -lt 0 -or $DiscountPct -gt 100) {
        throw "DiscountPct must be between 0 and 100."
    }
    return [Math]::Round($UnitPrice * (1 - $DiscountPct / 100), 2)
}
