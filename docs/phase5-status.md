# Phase 5 status — second customer profile and beyond

| Area | Status | Notes |
| --- | --- | --- |
| Food-processor profile flag | Done | `.goliath/factory-config.json` + [`fsma-204-profile.md`](fsma-204-profile.md) |
| FSMA 204 CTE/KDE on genealogy | Done | `23_fac_fsma_trace.sql`, semantic `mfg.fsma_cte`, actions `mfg.fsma.record_cte`, `mfg.fsma.export_24h` |
| 24h traceability CSV export | Done | Sortable spreadsheet via `fac_trace.sp_fsma_export_traceability_csv` |
| Offline tablet queue | Done | `24_fac_offline_queue.sql`, `mfg.offline.enqueue` / `mfg.offline.sync`, [`offline-tablet.md`](offline-tablet.md) |
| MTConnect / OPC UA stubs | Done | `goliath_factory.machine.*`, `mfg.machine.ingest_observation`, [`machine-monitoring.md`](machine-monitoring.md) |
| Extra ERP adapters | N/A | Plan keeps QuickBooks Online + ERPNext only |
| Roadmap / product status | Done | `docs/plan.md`, `.goliath/product.json` → `stable` |
