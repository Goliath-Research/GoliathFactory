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
| `fac_prod` | Work orders, travelers, traveler steps |
| `fac_trace` | Lots, lot links (genealogy), `fn_genealogy` |

| `fac_qual` | Inspection plans, characteristics, results, NCR, MRB disposition |
| `fac_audit` | Append-only `audit_log`; e-sign columns on traveler steps |
| `fac_inv_hooks` | Receive/issue stubs until GoliathApp `inv` module |

Semantic **views** (`v_*`) back `storage_relation` on entities. Named reads use **functions** scoped to the session user (organization membership and site). Phase 1 registers work-order list, traveler steps by work order, and lot genealogy. Phase 2 adds quality reads, audit-by-entity, and write procs in `09_fac_mfg_api.sql` for portal actions.

**Inventory:** item master, stock, and purchasing live in the GoliathApp `inv` module (built in parallel). GoliathFactory does not define an `inv` schema here; enable inventory NavTree nodes from the platform module when deployed.
