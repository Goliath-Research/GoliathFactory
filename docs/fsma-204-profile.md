# Food-processor profile (FSMA 204)

Set `.goliath/factory-config.json` → `"customerProfile": "food_processor"` at deploy time (see `factory-config.schema.json`). Precision shops keep the default `precision_shop`; FSMA nav and actions remain registered but are intended for food deployments.

## Data model

FSMA **Critical Tracking Events (CTE)** with **Key Data Elements (KDE)** sit on top of existing `fac_trace` lots and `lot_links` genealogy:

| CTE type | Typical use |
| --- | --- |
| `receiving` | Incoming raw/packaging lots |
| `transformation` | Combine/split/process (genealogy link optional) |
| `creation` | New traceability lot produced on line |
| `shipping` | Shipment reference tied to lot TLC |

KDE columns on `fac_trace.fsma_cte_events`: traceability lot code, product description, quantity/UOM, location, reference document type/number, optional `lot_id` / `genealogy_link_id`.

## Semantic layer

| Code | Request |
| --- | --- |
| `mfg.fsma_cte` | `mfg.fsma.cte_by_lot`, `mfg.fsma.cte_in_window` |

## Actions

| Action | Permission |
| --- | --- |
| `mfg.fsma.record_cte` | `mfg.fsma.write` |
| `mfg.fsma.export_24h` | `mfg.fsma.read` |

`mfg.fsma.export_24h` produces a **sortable CSV** (UTC `event_at` first column) for the configured window (default 24 hours, max 168). Exports are stored in `fac_trace.fsma_traceability_exports` for audit.
