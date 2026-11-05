# GoliathFactory database schema

Apply **after** the GoliathApp platform schema is present on the database.

## Prerequisites

- PostgreSQL 14+
- GoliathApp portal semantic registry and RBAC (`workflow_engine/sql_pg/apply_schema.sh`)

## Apply

```bash
export PGHOST=localhost PGPORT=5432 PGDATABASE=goliath_factory PGUSER=postgres PGPASSWORD='...'
./scripts/apply_domain_schema.sh
```

Scripts under `database/schema/` are idempotent (`CREATE IF NOT EXISTS`, `CREATE OR REPLACE`).

## Layout

| Schema | Purpose |
| --- | --- |
| `fac_eng` | Sites, parts, part revisions, routings, routing operations, work centers |
| `fac_prod` | Work orders, travelers, traveler steps, offline outbox |
| `fac_qual` | Inspection, NCR, CAPA, first article, SPC/CMM batches |
| `fac_gauge` | Gauges and calibrations |
| `fac_doc` | Controlled documents and revision workflow stubs |
| `fac_trace` | Lots, genealogy, CoC, FSMA CTE/KDE events and export audit |
| `fac_audit` | Append-only `audit_log`; e-sign columns on traveler steps |
| `fac_mfg_inv` | `inv` receive/issue wrappers + stock-lot → trace-lot map |
| `fac_maint` | Assets, PM schedules, maintenance orders, downtime, machine observations |
| `fac_wf` | DomainProgram task queue and capability NOTIFY wakes |
| `fac_inv_hooks` | Legacy Phase 2 stubs (superseded by `fac_mfg_inv`) |

Phase 3 adds `11`–`18`; Phase 4 adds `19`–`22`; Phase 5 adds `23`–`26` (FSMA trace, offline queue, machine ingest, APIs). Semantic **views** (`v_*`) back `storage_relation` on entities. Named reads use **functions** scoped to the session user (organization membership and site).

**Inventory:** item master, stock, and purchasing live in the GoliathApp `inv` module (built in parallel). GoliathFactory does not define an `inv` schema here; enable inventory NavTree nodes from the platform module when deployed.
