# Phase 4 status — maintenance and SPC

| Area | Status | Notes |
| --- | --- | --- |
| `fac_maint` schema | Done | `19_fac_maint.sql`, `21_fac_maint_api.sql`, `fac_maint.v_asset` |
| PM due semantic + portal | Done | `mfg.asset`, `mfg.asset.pm_due`, Maintenance nav + `portal/views/maintenance.html` |
| PM complete / downtime actions | Done | `mfg.asset.pm_complete`, `mfg.downtime.log` |
| Dual-activation PM scan | Done | `20_fac_mfg_wf_wake.sql`, `fac_maint.sp_enqueue_pm_due_backlog`, wake on PM complete |
| SPC charts | Done | `goliath_factory.spc`, `mfg.spc.summarize`, `mfg.spc.series`, portal chart view |
| CMM import stub | Done | `mfg.cmm.register_upload`, worker parser; gaps in [`cmm-import.md`](cmm-import.md) |
| DomainPrograms doc | Done | [`domain_programs/README.md`](../domain_programs/README.md) |

Phase 5: FSMA food profile, offline tablets, MTConnect/OPC UA — see [`phase5-status.md`](phase5-status.md).
