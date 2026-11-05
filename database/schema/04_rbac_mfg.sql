-- GoliathFactory Phase 1 — RBAC notes
--
-- Semantic requests reference these permission names (register via GoliathApp RBAC admin
-- or a future mfg permission seeder aligned with Meta ObjValues):
--   mfg.work_order.read, mfg.work_order.release
--   mfg.traveler.read, mfg.traveler.sign
--   mfg.trace.read, mfg.trace.write
--   mfg.quality.read, mfg.quality.inspect, mfg.quality.mrb
--   mfg.audit.read
--   mfg.inv.receive, mfg.inv.issue (stub actions until platform inv module)
-- Planned factory roles (plant manager, supervisor, operator, quality, maintenance, buyer,
-- auditor) and Role2Node grants are applied per organization scope after roles exist —
-- see docs/plan.md NavTree.
--
-- Inventory and purchasing permissions live in the GoliathApp `inv` module; do not duplicate here.

SELECT 1;
