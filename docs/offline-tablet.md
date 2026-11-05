# Offline tablet mode

Shop-floor tablets can queue traveler and inspection writes when Wi‑Fi drops, then replay them with **idempotency keys** so retries do not double-post.

## Flow

1. Portal (or PWA) calls `mfg.offline.enqueue` with `client_device_id`, `idempotency_key`, `action_name`, and JSON `payload`.
2. When online, `mfg.offline.sync` replays pending rows in capture order (up to `max_batch`, default 25).
3. Successful replays call the same in-process handlers as live actions; failures mark the row `conflict` or `rejected` with `conflict_reason`.

## Allowed actions

Only these domain actions may be queued offline:

- `mfg.traveler_step.start`
- `mfg.traveler_step.sign_off`
- `mfg.inspection_result.record`

NCR, disposition, and e-signature-heavy steps require live re-authentication and are **not** offline-capable.

## Documented limits

| Limit | Value |
| --- | --- |
| Pending rows per device | 100 |
| Payload size | 64 KiB JSON |
| Sync batch size | 50 max (`max_batch` capped in handler) |
| Queue retention | 7 days (operational cleanup not automated in v1) |
| Conflict handling | Row stays `conflict`; operator must reconcile on tablet |

Domain permissions for queued actions use `portal.fn_semantic_session_has_permission` (same RBAC join as `portal.sp_run_semantic_request`), enforced in Python handlers and in `fac_prod.sp_offline_enqueue` for defense in depth.

Storage: `fac_prod.offline_outbox` with unique `(site_id, client_device_id, idempotency_key)`.
