-- GoliathFactory NavTree nodes (idempotent; does not mutate foundation menus)

CREATE OR REPLACE FUNCTION fac_eng.sp_register_mfg_nav_child(
  p_parent_id integer,
  p_caption text,
  p_seq smallint,
  p_info_name text,
  p_frame_key text
)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
  v_info integer;
  v_node_id integer;
BEGIN
  SELECT ni."Id" INTO v_info FROM portal."NodeInfos" ni WHERE ni."Name" = p_info_name;
  IF v_info IS NULL THEN
    INSERT INTO portal."NodeInfos" ("Name", "Singleton", "TypeId", "FrameKey")
    VALUES (p_info_name, true, 1, p_frame_key)
    RETURNING "Id" INTO v_info;
  ELSE
    UPDATE portal."NodeInfos"
    SET "FrameKey" = p_frame_key
    WHERE "Id" = v_info AND "FrameKey" IS DISTINCT FROM p_frame_key;
  END IF;

  SELECT n."ID" INTO v_node_id
  FROM portal."NavTree" n
  WHERE n."ParentID" IS NOT DISTINCT FROM p_parent_id AND n."Caption" = p_caption;

  IF v_node_id IS NULL THEN
    SELECT node_id INTO v_node_id
    FROM portal.sp_nav_register_node(p_parent_id, p_caption, p_seq, v_info);
  END IF;
  RETURN v_node_id;
END;
$$;

CREATE OR REPLACE FUNCTION fac_eng.sp_register_mfg_nav()
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
  v_root_info integer;
  v_root_id integer;
  v_quality_id integer;
BEGIN
  SELECT ni."Id" INTO v_root_info FROM portal."NodeInfos" ni WHERE ni."Name" = 'mfg_root';
  IF v_root_info IS NULL THEN
    INSERT INTO portal."NodeInfos" ("Name", "Singleton", "TypeId", "FrameKey")
    VALUES ('mfg_root', true, 1, 'mfg')
    RETURNING "Id" INTO v_root_info;
  END IF;

  SELECT n."ID" INTO v_root_id
  FROM portal."NavTree" n
  WHERE n."Caption" = 'Factory' AND n."ParentID" IS NULL;

  IF v_root_id IS NULL THEN
    SELECT node_id INTO v_root_id
    FROM portal.sp_nav_register_node(NULL, 'Factory', 25::smallint, v_root_info);
  END IF;

  PERFORM fac_eng.sp_register_mfg_nav_child(
    v_root_id, 'Work orders', 10, 'mfg_work_orders', 'mfg.work_order.list_open'
  );
  PERFORM fac_eng.sp_register_mfg_nav_child(
    v_root_id, 'Shop floor (traveler)', 20, 'mfg_shop_floor', 'mfg.traveler_step.by_work_order'
  );

  v_quality_id := fac_eng.sp_register_mfg_nav_child(
    v_root_id, 'Quality', 25, 'mfg_quality', 'mfg'
  );
  PERFORM fac_eng.sp_register_mfg_nav_child(
    v_quality_id, 'Inspections', 10, 'mfg_inspections', 'mfg.inspection_result.by_lot'
  );
  PERFORM fac_eng.sp_register_mfg_nav_child(
    v_quality_id, 'NCR / CAPA', 20, 'mfg_ncr', 'mfg.ncr.list_open'
  );
  PERFORM fac_eng.sp_register_mfg_nav_child(
    v_quality_id, 'First article (FAI)', 30, 'mfg_fai', 'mfg.fai.by_work_order'
  );
  PERFORM fac_eng.sp_register_mfg_nav_child(
    v_quality_id, 'Document control', 40, 'mfg_documents', 'mfg.document.list'
  );

  PERFORM fac_eng.sp_register_mfg_nav_child(
    v_root_id, 'Gauges', 28, 'mfg_gauges', 'mfg.gauge.due_calibration'
  );
  PERFORM fac_eng.sp_register_mfg_nav_child(
    v_root_id, 'Maintenance', 29, 'mfg_maintenance', 'mfg.asset.pm_due'
  );
  PERFORM fac_eng.sp_register_mfg_nav_child(
    v_quality_id, 'SPC', 35, 'mfg_spc', 'mfg.spc.series'
  );
  PERFORM fac_eng.sp_register_mfg_nav_child(
    v_root_id, 'Traceability', 30, 'mfg_traceability', 'mfg.lot.genealogy'
  );
  PERFORM fac_eng.sp_register_mfg_nav_child(
    v_root_id, 'Inventory & purchasing', 35, 'mfg_inv', 'inv.item.list'
  );
  PERFORM fac_eng.sp_register_mfg_nav_child(
    v_root_id, 'Receiving', 36, 'mfg_receiving', 'inv.stock.receive'
  );
END;
$$;

SELECT fac_eng.sp_register_mfg_nav();
