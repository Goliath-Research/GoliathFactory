# CMM import (Phase 4 stub)

GoliathFactory registers uploaded CMM/export files with `mfg.cmm.register_upload`, enqueues `mfg.cmm.import_file`, and parses a **minimal CSV** into `fac_qual.inspection_results`.

## Supported today

| Format | Columns | Notes |
| --- | --- | --- |
| `csv` / `pcdmis_csv` | `characteristic_code`, `piece_number`, `measured_value`, optional `lot_number` | Maps characteristics by code on the target site; pass/fail is set to `pass` (tolerance check deferred). |

Parser: `goliath_factory.cmm.parse_cmm_export`.

## Incomplete edges (documented gaps)

| Edge | Status |
| --- | --- |
| Native PC-DMIS binary / DML output | Not parsed; export to CSV from the CMM first |
| Automatic characteristic creation | Rows with unknown `characteristic_code` are skipped |
| Lot linkage without `lot_number` column | Results stored without `lot_id` |
| Gauge / probe serial traceability | `gauge_id` not populated from file |
| Work order / traveler context | No WO column in stub CSV |
| Tolerance-based pass/fail | Worker sets `pass_fail='pass'`; use inspection entry or future rule engine |
| Object storage fetch | Worker reads `storage_ref` as local path or inline JSON `{"csv": "..."}` only; S3 wiring is deployment-specific |
| Q-DAS / DMIS full grammar | Not implemented |

See [`docs/plan.md`](plan.md) integrations and Phase 4 roadmap.
