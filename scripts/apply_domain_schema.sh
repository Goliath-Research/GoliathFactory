#!/usr/bin/env bash
# Apply GoliathFactory domain PostgreSQL DDL (Phase 1–3 schemas).
#
# Run after GoliathApp platform schema is present on the database.
#
# Example:
#   export PGHOST=localhost PGPORT=5432 PGDATABASE=goliath_factory PGUSER=postgres
#   export PGPASSWORD='...'
#   ./scripts/apply_domain_schema.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SCHEMA_DIR="$REPO_ROOT/database/schema"

: "${PGHOST:?Set PGHOST (libpq host)}"
export PGPORT="${PGPORT:-5432}"
: "${PGDATABASE:?Set PGDATABASE (libpq database name)}"
: "${PGUSER:?Set PGUSER (libpq user)}"
export PGSSLMODE="${PGSSLMODE:-prefer}"

if [[ -z "${PGPASSWORD:-}" && -z "${PGPASSFILE:-}" ]]; then
  echo "Set PGPASSWORD or PGPASSFILE for database authentication." >&2
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "psql is not on PATH; install postgresql-client." >&2
  exit 1
fi

SCRIPTS=(
  00_extensions.sql
  portal_semantic_row_types.sql
  01_fac_eng.sql
  02_fac_prod.sql
  03_fac_trace.sql
  04_rbac_mfg.sql
  05_nav_mfg.sql
  06_fac_semantic.sql
  07_fac_qual.sql
  08_fac_audit.sql
  09_fac_mfg_api.sql
  10_fac_semantic_phase2.sql
  11_fac_qual_capa.sql
  12_fac_gauge.sql
  13_fac_doc.sql
  14_fac_fai.sql
  15_fac_trace_coc.sql
  16_fac_mfg_api_phase3.sql
  17_fac_semantic_phase3.sql
)

for name in "${SCRIPTS[@]}"; do
  path="$SCHEMA_DIR/$name"
  if [[ ! -f "$path" ]]; then
    echo "missing domain schema file: $path" >&2
    exit 1
  fi
done

echo "[INFO] GoliathFactory domain schema: database=${PGDATABASE} host=${PGHOST}"
psql -X -q -v ON_ERROR_STOP=1 -c "SELECT current_user AS db_user, version();"

for name in "${SCRIPTS[@]}"; do
  echo "[INFO] applying database/schema/${name}"
  psql -X -q -v ON_ERROR_STOP=1 -f "$SCHEMA_DIR/$name"
done

echo "[INFO] domain schema apply complete (${#SCRIPTS[@]} files)"
