-- GoliathFactory Phase 1 — RBAC notes
--
-- Semantic requests reference these permission names (register via GoliathApp RBAC admin
-- or a future mfg permission seeder aligned with Meta ObjValues):
--   mfg.work_order.read, mfg.work_order.release
--   mfg.traveler.read, mfg.traveler.sign
--   mfg.trace.read, mfg.trace.write
--   mfg.quality.read, mfg.quality.inspect, mfg.quality.mrb, mfg.quality.approve
--   mfg.gauge.read
--   mfg.maint.read, mfg.maint.write
--   mfg.document.read, mfg.document.write, mfg.document.approve
--   mfg.audit.read
--   mfg.inv.issue (domain issue-to-work-order)
--   inv.stock.receive, inv.stock.adjust, inv.stock.issue (GoliathApp inv module; Factory overrides receive/issue)
-- Planned factory roles

SELECT 1;
