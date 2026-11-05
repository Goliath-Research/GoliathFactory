# Machine monitoring (MTConnect / OPC UA stubs)

Phase 5 adds **adapter stubs** that normalize shop-floor machine samples into `fac_maint.machine_observations` and optionally open `fac_maint.downtime_events` when availability is down.

| Protocol | Module | Input |
| --- | --- | --- |
| MTConnect | `goliath_factory.machine.mtconnect` | Sample XML (`DeviceStream`, `Availability`, `Execution`) |
| OPC UA | `goliath_factory.machine.opcua` | JSON payload from an edge collector |

DomainProgram action: `mfg.machine.ingest_observation` (hidden; dispatched via `goliath_factory.workers.dispatch`).

## `incomplete_edges`

Each parse returns an `incomplete_edges` string list when required mapping is missing, for example:

| Edge | Meaning |
| --- | --- |
| `device_id` / `asset_tag` | Could not map stream to `fac_maint.assets` |
| `availability` | No availability sample in payload |
| `execution_state` | No execution/program state |
| `opc_node_ids` | OPC payload omitted node identifiers |

Stubs still persist the observation with partial fields so integrators can see gaps in Postgres. Full asset matching, bidirectional OPC subscriptions, and automatic downtime **close** events are **not** implemented (documented gaps).

## Downtime linkage

When normalized availability is `unavailable` / `not_available` / `down`, `fac_maint.sp_machine_record_observation` inserts a downtime row with reason `machine_monitor` and links it on the observation.
