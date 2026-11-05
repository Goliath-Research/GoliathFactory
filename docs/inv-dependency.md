# GoliathApp `inv` module dependency

GoliathFactory **does not** ship an `inv` schema. Item master, stock, POs, ASL, cycle counts, and costing are owned by GoliathApp ([inventory module](https://github.com/Goliath-Research/GoliathApp/blob/main/docs/inventory-module.md), merged on `main` as **`1a0fe26`** / PR [#34](https://github.com/Goliath-Research/GoliathApp/pull/34)).

| Integration | Detail |
| --- | --- |
| Schema | Apply GoliathApp `inv_*.sql` before Factory domain DDL |
| Reads | `inv.item.list`, `inv.purchase_order.list`, `inv.stock_lot.by_item`, `inv.supplier_item.list` |
| Writes (core) | `inv.stock.receive`, `inv.stock.adjust`, `inv.stock.issue` → `inv.sp_*` |
| Factory bridge | `fac_mfg_inv` (`18_fac_mfg_inv.sql`) wraps receive/issue and maps `inv.stock_lot` → `fac_trace.lots` |
| Action overrides | Factory catalog overrides `inv.stock.receive` and `inv.stock.issue` (`overrides="inv"`) |
| Domain action | `mfg.inv.issue_to_work_order` → `fac_mfg_inv.sp_issue_to_work_order` |

## Factory receive / issue flow

1. **Receive:** `inv.stock.receive` (override) calls `inv.sp_stock_receive`, then creates a material lot in `fac_trace` and row in `fac_mfg_inv.stock_lot_trace`.
2. **Issue to WO:** `mfg.inv.issue_to_work_order` or `inv.stock.issue` with `ref_type=work_order` calls `inv.sp_stock_issue_stub` and inserts `fac_trace.lot_links` (consume) when the work order has an `output_lot_id`.
3. **Incoming inspection:** record results with `mfg.inspection_result.record` after receipt (QC hold rules are deployment-specific).

ASL enforcement and moving-average costing remain inside **`inv.sp_stock_receive`**; Factory does not duplicate those rules.

## Permissions

Grant storekeeper roles GoliathApp permissions `inv.stock.receive`, `inv.stock.adjust`, `inv.stock.issue`, plus Factory `mfg.inv.issue` for the domain issue action. See `database/schema/04_rbac_mfg.sql` notes.

## Legacy `fac_inv_hooks`

Phase 2 stub schema `fac_inv_hooks` in `09_fac_mfg_api.sql` is superseded by `fac_mfg_inv`. New deployments should rely on overrides; hooks are not called from Factory handlers after Phase 3 wiring.
