# GoliathApp Phase 0b gaps (e-signatures and audit)

Phase 2 records **signature meaning**, **signer user id**, **timestamp**, and a **record hash** on traveler sign-off and NCR disposition, and appends rows to `fac_audit.audit_log`. This satisfies pilot AS9100-style record keeping alongside paper travelers.

Platform work tracked in [`docs/plan.md`](plan.md) (Workflow Engine findings) remains open on GoliathApp `main`:

| Gap | GoliathFactory interim |
| --- | --- |
| Re-authentication e-signature service | Portal collects meaning text; gateway session user is signer; no Part 11 re-auth prompt yet |
| Generic append-only audit for all domain writes | `fac_audit.audit_log` + `mfg.audit.by_entity` read request |
| Human approval inbox / WAIT_EVENT UX | NCR disposition is a direct signed action; CAPA workflow is Phase 3 |
| Portal task API | Not required for pilot v1 tablet flows |

Replace domain hash helpers with the platform signature service when GoliathApp Phase 0b ships; keep `fac_audit` rows as the manufacturing audit export source or migrate via a one-time backfill script.
