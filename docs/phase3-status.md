# Phase 3 — Quality and purchasing checklist

Tracking against [`plan.md`](plan.md) Phase 3 scope (Nov 2026).

| Item | Status | Notes |
| --- | --- | --- |
| CAPA tables / `mfg.capa` / `mfg.capa.close` | Done | `11_fac_qual_capa.sql`, portal `capa.html` |
| Gauge calibration / lockout | Done | `12_fac_gauge.sql`, `mfg.gauge.due_calibration`, hidden `mfg.gauge.lockout_check` |
| Document control stubs | Done | `13_fac_doc.sql`, submit/approve actions |
| FAI (AS9102) | Done | `14_fac_fai.sql`, start/approve actions |
| CoC export | Done | `15_fac_trace_coc.sql`, enriched CoC generator |
| GoliathApp `inv` on `main` (`1a0fe26`) | Done | Overrides + `fac_mfg_inv`; portal receiving/purchasing |
| ASL / price breaks / reorder / cycle count / MA costing | In `inv` | Portal uses `inv.*` semantics; adjust via `inv.stock.adjust` |
| Accounting adapter interface | Done | [`accounting-adapters.md`](accounting-adapters.md) |
| `product.json` status | `in_development` | Pilot deployment validation still open |

Remaining before pilot-ready status: end-to-end test on a database with GoliathApp platform + `inv` seed data, RBAC grants, and optional accounting adapter credentials.
