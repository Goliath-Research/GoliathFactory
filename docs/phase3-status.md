# Phase 3 — Quality and purchasing checklist

Tracking against [`plan.md`](plan.md) Phase 3 scope (Nov 2026).

| Item | Status | Notes |
| --- | --- | --- |
| CAPA tables / `mfg.capa` / `mfg.capa.close` | Done | `11_fac_qual_capa.sql`, portal `capa.html` |
| Gauge calibration / lockout | Done | `12_fac_gauge.sql`, `mfg.gauge.due_calibration`, hidden `mfg.gauge.lockout_check`, inspection SP guard |
| Document control stubs | Done | `13_fac_doc.sql`, submit/approve actions |
| FAI (AS9102) | Done | `14_fac_fai.sql`, start/approve actions, portal `fai.html` |
| CoC export | Done | `15_fac_trace_coc.sql`, enriched `fac_trace.sp_lot_coc_generate` |
| GoliathApp `inv` merge | **Blocked** | PR [#34](https://github.com/Goliath-Research/GoliathApp/pull/34) still open — hooks + purchasing UI against published `inv.*` shapes |
| ASL / price breaks / reorder / cycle count / MA costing | **In `inv`** | Documented in [`inv-dependency.md`](inv-dependency.md); no Factory tables |
| Accounting adapter interface | Done | QBO + ERPNext stubs, [`accounting-adapters.md`](accounting-adapters.md) |
| `product.json` status | `in_development` | Remains until `inv` merges and Factory overrides land |

Next after GoliathApp PR #34 merges: action overrides for receive/issue, genealogy links, retire stub actions, flip checklist row and consider pilot-ready status.
