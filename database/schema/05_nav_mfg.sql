-- GoliathFactory NavTree nodes (idempotent; does not mutate foundation menus)

CREATE OR REPLACE FUNCTION fac_eng.sp_register_mfg_nav_child(
  p_parent_id integer,
  p_caption text,
  p_seq smallint,
  p_info_name text,
  p_frame_key text
)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
  v_info integer;
  v_exists integer;
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

  SELECT n."ID" INTO v_exists
  FROM portal."NavTree" n
  WHERE n."ParentID" = p_parent_id AND n."Caption" = p_caption;

  IF v_exists IS NULL THEN
    PERFORM portal.sp_nav_register_node(p_parent_id, p_caption, p_seq, v_info);
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION fac_eng.sp_register_mfg_nav()
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
  v_root_info integer;
  v_root_id integer;
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
  PERFORM fac_eng.sp_register_mfg_nav_child(
    v_root_id, 'Traceability', 30, 'mfg_traceability', 'mfg.lot.genealogy'
  );
END;
$$;

SELECT fac_eng.sp_register_mfg_nav();
