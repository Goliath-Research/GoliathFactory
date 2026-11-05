# GoliathApp `inv` module dependency

GoliathFactory **does not** ship an `inv` schema. Item master, stock, POs, and receipts are owned by GoliathApp ([inventory module plan](https://github.com/Goliath-Research/GoliathApp/pull/34)).

| Status (Nov 2026) | Detail |
| --- | --- |
| GoliathApp PR | [#34 — domain-neutral inventory and purchasing](https://github.com/Goliath-Research/GoliathApp/pull/34) — **not merged** on `main` |
| GoliathFactory hooks | `fac_inv_hooks.sp_receive_with_inspection`, `fac_inv_hooks.sp_issue_to_work_order` |
| Actions | `mfg.inv.receive_stub`, `mfg.inv.issue_to_work_order_stub` |
| Portal | Factory › Receiving (pilot) → `views/receiving.html` |

When `inv` is enabled on a deployment:

1. Replace stub procs with calls to `inv` receive/issue APIs and map stock lots to `fac_trace.lot_links` for genealogy.
2. Enable GoliathApp inventory NavTree nodes (Factory › Inventory & purchasing in [`docs/plan.md`](plan.md)); do not duplicate nodes in this repo.
3. Drop or narrow stub actions once real handlers are registered in the platform catalog.
