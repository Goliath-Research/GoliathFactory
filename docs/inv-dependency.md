# GoliathApp `inv` module dependency

GoliathFactory **does not** ship an `inv` schema. Item master, stock, POs, and receipts are owned by GoliathApp ([inventory module plan](https://github.com/Goliath-Research/GoliathApp/pull/34)).

| Status (Nov 2026) | Detail |
| --- | --- |
| GoliathApp PR | [#34 — domain-neutral inventory and purchasing](https://github.com/Goliath-Research/GoliathApp/pull/34) — **open**, not merged on `main` |
| GoliathFactory hooks | `fac_inv_hooks.sp_receive_with_inspection`, `fac_inv_hooks.sp_issue_to_work_order` |
| Detection | `fac_inv_hooks.fn_inv_schema_ready()` → true when `inv.sp_stock_receive` exists |
| Actions (Factory) | `mfg.inv.receive_stub`, `mfg.inv.issue_to_work_order_stub` (until wired overrides) |
| Actions (GoliathApp `inv`) | `inv.stock.receive`, `inv.stock.adjust`, `inv.stock.issue` |
| Portal | Factory › Inventory & purchasing → `inv.item.list` / `inv.purchase_order.list`; Receiving → stub action |

## Published `inv` API shapes (PR branch `cursor/inv-module-1977`)

Semantic reads (namespace `inv`):

| `request_code` | Params | Row highlights |
| --- | --- | --- |
| `inv.item.list` | `organization_id` | `item_id`, `item_number`, `qty_on_hand`, `avg_unit_cost` |
| `inv.purchase_order.list` | `organization_id`, optional `status` | `purchase_order_id`, `status`, supplier fields |
| `inv.stock_lot.by_item` | `organization_id`, `item_id` | bin/lot on-hand |
| `inv.supplier_item.list` | `organization_id`, optional `item_id` | ASL-linked supplier catalog, price breaks |

Write paths use gateway actions backed by `inv.sp_stock_receive`, `inv.sp_stock_adjust`, and issue stub with opaque `ref_type` / `ref_id` for child genealogy.

Factory-specific behavior after merge:

1. Override or wrap `inv.stock.receive` / `inv.stock.issue` to run incoming inspection and `fac_trace.lot_links`.
2. Map `fac_eng.sites.organization_id` to `inv` organization scope (hooks already return `organization_id` when `inv` is present).
3. Enable GoliathApp inventory NavTree nodes; Factory adds Quality/purchasing frames only where domain-specific.
4. Drop or narrow `mfg.inv.*_stub` actions once overrides are registered.

ASL, price breaks, reorder points, cycle counts, and moving-average costing remain in **`inv`**; do not duplicate tables in GoliathFactory.
