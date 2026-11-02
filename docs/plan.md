# GoliathFactory — Manufacturing Operations plan

GoliathFactory is a GoliathApp child app for travelers, QC, lot genealogy, NCR/CAPA and maintenance at 10–50 person Florida manufacturers. Phase 0 is one pilot shop, not code.

## Vision and buyer

A manufacturing-operations specialization: work orders and travelers, QC inspections, lot traceability and genealogy, nonconformances/CAPA, and maintenance, with every operator, QA and manager action typed, signed and recorded.

| Buyer | Detail | Priority |
| --- | --- | --- |
| Precision shops | 10–50 person CNC, machining and stamping shops in Florida serving aerospace and medical (AS9100, ISO 13485, ISO 9001) | Primary |
| Food processors | Packinghouses and processors needing lot traceability (FSMA 204) and audit records | Secondary |
| Not the buyer | Plants large enough for SAP, Plex or MasterControl, or that decide by committee | — |

The name is GoliathFactory: every factory includes QC, so quality is part of it, not a separate product.

## Why this specialization

- **Most workflow-shaped market.** A shop's day is travelers, inspection steps, approvals, nonconformances and audit records: typed actions by operators, QA and managers with a record kept. That is exactly what GoliathApp's Workflow Engine and RBAC do, more purely than Crop.
- **David's credibility.** GE Transportation locomotive software and hardware-in-the-loop validation, Bombardier, IQMS ERP, MISRA firmware: he talks to a shop owner as a peer who has lived their systems.
- **Dense, right-sized buyers.** Florida has many 10–50 person precision shops and food processors, too small for SAP/Plex/MasterControl pricing, big enough to pay for custom work and decide without a committee.
- **Daily, auditable pain.** AS9100/ISO 9001 audits, customer lot-genealogy demands and lost travelers hurt now, which shortens sales cycles versus a nice-to-have analytics platform.
- **Live threads.** Space Coast aerospace suppliers in Vaya's ecosystem; Dundee packinghouses and Wish's berry operation as food-traceability buyers. One specialization serves both.

## Runners-up

| Option | Verdict |
| --- | --- |
| Test operations | Generalizes the Vaya angle (campaigns, procedures, anomaly review); hold until an aerospace buyer validates it, or it is a market of one |
| Packhouse / post-harvest | Natural GoliathCrop extension using the Dundee and Wish conversations; same buyer pool, not better targets |
| Lab / sample management | Overlaps GoliathOmics; would split focus rather than open a market |

> **Discipline.** Each specialization multiplies maintenance and the scarcest resource is one real deployment. Do not build speculatively: find one shop willing to pilot around its traveler and QC flow, and let its process define v1.

## Architecture fit

| Aspect | Plan |
| --- | --- |
| Parent | GoliathApp (knows nothing about GoliathFactory) |
| Auth | Inherit GoliathApp auth and `RBAC.Sessions`; e-signature re-authentication comes from GoliathApp (work item below) |
| API | Neon PostgreSQL stored procedures; portal connects over private network |
| Workflows | GoliathApp Workflow Engine runs travelers, NCR/CAPA, approvals; any missing engine feature is built in GoliathApp for every child |
| Accounting | Pluggable accounting adapter (QuickBooks Online, ERPNext, others) |
| Workers | Claim through goliath-gateway only; Postgres pub/sub wakes event tasks |
| Storage | Documents, photos, certs on S3-compatible storage; references in Postgres |
| Defaults | Free tools first, CPU-only workers (as GoliathCrop) |
| Status | planned |

## Users and roles

| Role | Can |
| --- | --- |
| Owner / plant manager | Everything; approve releases, CAPA closure, users |
| Production supervisor | Release work orders, assign operations, disposition holds |
| Operator | Run traveler steps, record measurements, sign off own operations |
| Quality inspector | First-article and in-process inspections, gauge use, open NCRs |
| Quality manager | Approve plans and documents, MRB disposition, CAPA, audits |
| Maintenance tech | Work PMs and repairs, log downtime |
| Buyer / storekeeper | Items, supplier items, POs, receiving, issues, counts |
| Auditor / customer (read) | Read-only certs, genealogy, audit trail for scoped lots |
| Worker (service) | Gateway claim scopes only |

## Domain model

| Entity | Key facts |
| --- | --- |
| Part / revision | Part number, revision, drawing, material spec, customer, effectivity |
| Routing | Ordered operations per part revision: work center, setup, instructions, inspection points |
| Work order / traveler | Part rev, quantity, lot, due date, status; the traveler is its live, signed step record |
| Operation | Step on a traveler: operator, machine, start/end, quantity good/scrap, sign-off |
| Inspection plan / characteristic | Ballooned characteristics with nominal, tolerances, method, gauge type, sampling (AQL/FAI) |
| Inspection result | Measured values per characteristic and piece; pass/fail; inspector signature |
| Gauge / calibration | Gauge ID, type, location, calibration interval, certs, due date, out-of-cal lockout |
| Lot and genealogy | Material lots, heat/cert numbers, WIP and finished lots; parent-child links for forward and backward trace |
| Item / supplier item | Internal item master plus per-supplier names, part numbers, prices and lead times |
| Stock / PO | On-hand by location and lot, reservations, purchase orders and receipts |
| NCR / CAPA | Nonconformance, containment, MRB disposition (use-as-is, rework, scrap, RTV), root cause, corrective action, effectiveness check |
| Maintenance asset / PM | Machines and equipment, PM schedules (time or cycle), work requests, downtime |
| Document / approval | Controlled documents and revisions, approval routing, training acknowledgements |
| Audit trail / e-signature | Append-only change log; signatures with meaning, signer, time, re-auth (21 CFR Part 11 for medical/food where relevant; AS9100 records) |

## Inventory & Purchasing

> **Build once in GoliathApp.** GoliathCrop (seed, fertilizer, chemicals) and GoliathOmics (reagents, kits) need the same thing. A generic, domain-neutral inventory/purchasing module in GoliathApp that knows nothing about child apps; GoliathFactory, Crop and Omics each extend it with their own item attributes and rules.

| Area | What it covers |
| --- | --- |
| Item master | One internal item: internal part number, description, base unit, category, make/buy, lot/serial control, shelf life |
| Supplier items | Supplier part number and name/description, MPN (distributor vs manufacturer), pack size and unit conversion, price breaks with effective dates and currency, lead time, MOQ, preferred/approved flag |
| Approved Supplier List | AS9100 ASL; supplier items only purchasable from approved suppliers |
| Customer cross-refs | Optional customer part numbers per item |
| Alternates | Equivalent items; substitution needs a signed approval in regulated work |
| Stock | Locations/bins, on-hand by lot, reservations, adjustments, cycle counts, reorder points |
| Purchasing | Simple POs and receipts; receiving with incoming inspection feeding QC/NCR |
| Issue to work order | Consumes lots onto the traveler, feeding genealogy |
| Costing | Moving average default, standard optional; FIFO lot cost later |
| Catalog / invoice matching | Import supplier catalogs and invoices with different names; fuzzy match to the item master with a human confirmation queue |

## Workflows on the Workflow Engine

| Workflow | Typed actions |
| --- | --- |
| Work order release | Create from routing → review → release → print traveler/labels |
| Traveler execution | Start op → record qty/measurements → sign off → next op or hold |
| First article (AS9102) | Plan → measure all characteristics → QA approve → release run |
| In-process / final inspection | Sample → measure → pass, or auto-open NCR on fail |
| NCR / MRB | Open → contain → disposition (signed) → close or escalate to CAPA |
| CAPA | Root cause → action plan → implement → verify effectiveness → close |
| Gauge calibration | Due → pull from service → calibrate/attach cert → return or retire |
| Preventive maintenance | Due → assign → complete checklist → sign → next due |
| Document change | Draft → review → approve (signed) → effective → retrain |
| Shipment / CoC | Final QC → genealogy check → certificate of conformance → ship |
| Purchase and receive | Reorder suggestion → PO (approved supplier) → receive lot → incoming inspection → accept to stock or NCR |
| Issue to work order | Reserve → pick lot from bin → issue to traveler step (genealogy link) |
| Substitution | Request alternate item → QA/engineering approve (signed) → issue |
| Cycle count | Generate count → count bin → variance review → signed adjustment |

## Workers and DomainPrograms

| Program | Activation | Trigger |
| --- | --- | --- |
| Calibration / PM due scan | Claim | Daily backlog |
| Out-of-tolerance alert | Wake + claim | Inspection result inserted out of spec |
| NCR notification / escalation | Wake + claim | NCR opened or overdue |
| Label and traveler printing | Wake + claim | Work order released, lot created |
| CMM / gauge import | Wake + claim | Result file uploaded or gauge push |
| CoC / genealogy report | Claim | User request queued |
| Accounting adapter sync | Claim | Scheduled backlog |
| SPC summaries | Claim | Nightly backlog |
| Reorder point scan | Claim | Daily backlog |
| Catalog / invoice matching | Wake + claim | File uploaded; fuzzy matches go to a human confirmation queue |

Same pattern as GoliathCrop: a stored procedure inserts the task and issues `pg_notify`; idle workers wake, then own it with a gateway claim. All CPU-only.

## Database schema sketch

| Schema | Key tables |
| --- | --- |
| `fac_eng` | parts, part_revisions, routings, routing_operations, work_centers |
| `fac_prod` | work_orders, travelers, traveler_steps, operation_records |
| `fac_qual` | inspection_plans, characteristics, inspection_results, ncrs, mrb_dispositions, capas |
| `fac_gauge` | gauges, calibrations, calibration_certs |
| `fac_trace` | material_lots, lots, lot_links (genealogy), shipments, cocs |
| `fac_maint` | assets, pm_schedules, maintenance_orders, downtime_events |
| `fac_doc` | documents, document_revisions, approvals, training_records |
| `fac_audit` | audit_log (append-only), signatures |
| `inv` (GoliathApp module) | items, units, unit_conversions, suppliers, approved_suppliers, supplier_items, price_breaks, item_alternates, customer_item_refs, locations, bins, stock_lots, stock_moves, reservations, cycle_counts, purchase_orders, po_lines, receipts, item_costs, match_candidates |
| `fac_api` | stored procedures only; the portal's surface |

Row-level security by site and role. Genealogy queries use recursive CTEs; no extra extensions required for v1.

## Portal and shop-floor views

1. Shop-floor traveler (tablet): current step, instructions, record and sign, big touch targets
2. Inspection entry: characteristic list with tolerance bands, gauge scan, pass/fail
3. Work order board: released, in progress, on hold, by work center
4. Lot genealogy: forward and backward trace tree with certs
5. NCR/CAPA queue and MRB review
6. Gauge and PM calendars with due/overdue
7. Inventory: items with supplier items and prices, stock by bin/lot, receiving (tablet), POs, cycle counts, match-confirmation queue
8. Document control and approvals
9. Audit trail viewer and audit-ready export

## Integrations

- **Accounting / ERP adapter.** One adapter interface: customers, vendors, items, sales orders and invoices, POs, receipts, vendor bills, payments. Adapters: QuickBooks Online, ERPNext; IQMS/others by pilot need. If the pilot's ERP owns inventory, sync it instead of duplicating.
- **Supplier catalogs and invoices.** CSV/PDF import into the matching queue; distributor catalogs carry MPNs.
- **CMM and gauges.** CSV/DMIS/Q-DAS file import; USB/Bluetooth gauge input on tablets.
- **Label printing.** ZPL to Zebra printers for lot, traveler and gauge labels.
- **Machine monitoring (later).** MTConnect and OPC UA, reusing GoliathGroundStation's OPC UA experience.
- **Ecosystem.** GoliathCrop for packhouse lots; standalone utilities stay unaware of GoliathApp.

## Architecture diagram

```mermaid
flowchart LR
  subgraph ShopFloor[Shop floor]
    T[Tablets: travelers, inspections] --> P
    CMM[CMM / gauges] --> I
    M[Machines: MTConnect / OPC UA - later] -.-> I
  end
  P[GoliathFactory portal<br/>extends GoliathApp UI] -->|private network| DB[(Neon PostgreSQL<br/>stored procedures + Workflow Engine)]
  I[Ingest workers] -->|claim| G[goliath-gateway]
  G --> DB
  DB -->|pg NOTIFY wake| WK[DomainPrograms:<br/>alerts, calibration due, labels, exports]
  WK -->|claim / complete| G
  WK --> S3[(S3-compatible storage<br/>docs, photos, certs)]
  WK --> ERP[Accounting adapter:<br/>QuickBooks Online / ERPNext]
  A[GoliathApp<br/>auth, RBAC.Sessions, Workflow Engine, workers] -.inherited by.-> P
```

## Roadmap

1. **Phase 0 — Find the pilot (no code).** Walk 5–10 shops via Vaya's Space Coast network and the Dundee/Wish threads; pick one; map its paper traveler, inspection and NCR flow; agree on v1 scope and a discounted first-buyer price (never free). Aerospace/medical or food, whichever answers first.
2. **Phase 0b — GoliathApp prerequisites.** Human task/approval step, e-signatures and a generic audit trail in GoliathApp (see Workflow Engine findings), plus the shared `inv` module, usable by every child app.
3. **Phase 1 — Repo and core data.** Public MIT repo, `.goliath/product.json`, GoliathWeb page; parts/routings/work orders/lots schemas shaped by the pilot; generic `inv` module in GoliathApp (items, supplier items, locations, stock lots).
4. **Phase 2 — Pilot v1.** Tablet traveler, inspection entry, receiving with incoming inspection, issue to work order, lot genealogy, NCR, audit trail and e-signatures, label printing; run alongside paper.
5. **Phase 3 — Quality and purchasing.** CAPA, gauge calibration, document control, FAI (AS9102), CoC export; POs, ASL, price breaks, reorder points, cycle counts, costing, catalog/invoice matching, accounting adapter (QuickBooks Online and ERPNext).
6. **Phase 4 — Maintenance and SPC.** Assets, PMs, downtime, SPC charts, CMM import.
7. **Phase 5 — Second customer and beyond.** Food-processor profile (FSMA 204), offline tablet mode, MTConnect/OPC UA machine monitoring, other ERPs.

Pilot criteria:

- [ ] 10–50 people, AS9100/ISO 9001/13485 or FSMA exposure
- [ ] Paper or spreadsheet travelers today, real pain (audit finding, lost traveler, genealogy request)
- [ ] Owner or quality manager who decides and gives weekly access
- [ ] Pays a discounted first-buyer build (never free) and agrees to be a reference
- [ ] Shop-floor Wi-Fi at the stations that will use tablets
- [ ] Within driving distance in Florida

## Risks

| Risk | Mitigation |
| --- | --- |
| Building for nobody | No code before a signed pilot |
| Compliance claims | Part 11 / AS9100 support is controls plus the shop's procedures; never claim certification. Validate e-signature design early |
| Shop-floor adoption | Operators reject slow screens; tablet-first, assume shop Wi-Fi for v1 (offline mode later), pilot alongside paper |
| Scope creep into ERP/MES | Stay quality and traceability; integrate with ERP rather than replace it |
| Maintenance load | Another child app to keep current with GoliathApp; keep domain logic in stored procedures and workflows |

## Decisions

| Question | Decision |
| --- | --- |
| 1. First shops and introducers | Depends on replies from the prospects; does not change the plan |
| 2. Aerospace/medical or food first | Both are targets; little impact on plan or implementation |
| 3. Pilot commercial shape | Discounted build for the first buyer, never free |
| 4. Workflow Engine readiness | Conditions exist; human approval, e-signature and audit gaps are GoliathApp work items (below) |
| 5. E-signature scope | AS9100 records in v1 with Part 11-style controls built in (re-auth, signature meaning, signer, time, linked hash); formal Part 11 validation only when a medical/food buyer requires it |
| 6. Offline tablets | Assume shop Wi-Fi; offline tablet mode later (Phase 5) |
| 7. Accounting | Pluggable accounting adapter; free option preferred (below) |
| 8. Name | GoliathFactory; every factory includes QC, GoliathQuality dropped |
| 9. Inventory module location | Recommendation: a GoliathApp-owned optional module (own `inv` schema and stored procedures, domain-neutral) that a child app enables, not always-on core |
| 10. Default costing | Recommendation: moving average by default, standard cost optional per item; FIFO lot cost later, only if a buyer needs it |

### Workflow Engine findings

Checked in Goliath-Research/GoliathApp `main` (read-only).

| Exists | Where |
| --- | --- |
| IF / SWITCH / WHILE nodes branch on scope variables set by earlier action outputs | `workflow_engine/sql_pg/03_engine_core.sql`, `workflow_engine/contract/workflow_definition_spec.py` (`condition_var`, `condition_expr`), `docs/workflow-compiler.md` |
| WAIT_EVENT node parks an instance until a matching event arrives (`signal_wait`) | `workflow_engine/sql_pg/wf_event_plane.sql`, `wf.sp_ingest_event` / `wf.sp_signal_wait` in `workflow_engine/contract/db_objects.md`, `docs/workflow-engine.md` |
| Approval rows only for RBAC bypass-scope roles | `portal.sp_*_bypass_scope_approval` in `workflow_engine/sql_pg/rbac_api_parity.sql`, `docs/rbac.md` |
| Instance extension for optional domain audit metadata; onboarding-only AuditLog | `workflow_engine/sql_pg/00_schema.sql`, `workflow_engine/sql_pg/onboarding_schema.sql` |

Conditional steps work: an action sets a variable and IF branches on it. A conditional approval can be built today as IF → WAIT_EVENT → event from the portal. What is missing is a first-class human step. GoliathApp work items:

- [ ] Human task / approval step (assignee role, inbox, approve/reject outcome, due time and escalation) on top of WAIT_EVENT
- [ ] E-signature service (re-auth, meaning, signer, time, record hash) callable from any step
- [ ] Generic append-only audit trail for domain records and workflow actions
- [ ] Portal API to list and act on pending human tasks, scoped by RBAC

### Accounting adapter

| Option | Fit for a small US manufacturer |
| --- | --- |
| ERPNext (Frappe) | Free, GPL; full GL, AP/AR, US taxes, multi-currency; REST API. Has manufacturing too, so use it for accounting only |
| Odoo Community | Free, LGPL; JSON-RPC API; full accounting reports are mostly in paid Enterprise |
| Akaunting | Free, GPL; REST API; simple invoicing and bills, light for AP/inventory costing |
| GnuCash | Free desktop app; no server API, not a fit for sync |
| QuickBooks Online | Paid; what David and most shops already use; good REST API |

**Recommendation:** build the adapter interface with QuickBooks Online first, since the pilot shop most likely already runs it, and ERPNext as the first free adapter for buyers with no accounting system.
