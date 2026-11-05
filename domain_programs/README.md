# GoliathFactory DomainPrograms (Phase 4)

| Program | Action | Capability | Activation |
| --- | --- | --- | --- |
| PM due scan | `mfg.maint.pm_due_scan` | `mfg.maint` | Claim (`fac_maint.sp_enqueue_pm_due_backlog`) + wake (`fac_maint.sp_wake_pm_scan_for_site` on PM complete) |
| SPC summarize | `mfg.spc.summarize` | `mfg.spc` | Claim (`fac_qual.sp_enqueue_spc_backlog` nightly backlog) |
| CMM import | `mfg.cmm.import_file` | `mfg.cmm` | Wake + claim (`fac_qual.sp_register_cmm_upload` → `fac_wf.sp_enqueue_processing_task`) |

Workers claim through **goliath-gateway**, then call `goliath_factory.workers.dispatch.handle`. Wake hints use Postgres `NOTIFY` on `gw1_capability_*` channels (GoliathApp [dual activation](https://github.com/Goliath-Research/GoliathApp/blob/main/docs/dual-activation.md), same pattern as GoliathCrop `crop_wf.sp_publish_capability_wake`).

```python
from goliath_factory.workers.dispatch import handle

handle("mfg.maint.pm_due_scan", {"site_id": 1})
handle("mfg.spc.summarize", {"characteristic_id": 12, "chart_type": "xbar_r"})
```

User-facing writes: `mfg.asset.pm_complete`, `mfg.downtime.log`, and `mfg.cmm.register_upload` (RBAC) via action handlers in `goliath_factory.actions.handlers`.
