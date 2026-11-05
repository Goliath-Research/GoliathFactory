-- GoliathFactory Phase 2 — semantic read functions (quality)
SET client_min_messages = warning;

CREATE OR REPLACE FUNCTION fac_qual.fn_semantic_inspection_plan_by_part(
  p_user_id integer,
  p_params jsonb,
  p_limit integer
)
RETURNS TABLE (
  inspection_plan_id integer,
  site_id integer,
  part_revision_id integer,
  part_number text,
  part_revision text,
  plan_name text,
  plan_status text,
  characteristic_id integer,
  seq integer,
  characteristic_code text,
  description text,
  nominal numeric,
  tolerance_plus numeric,
  tolerance_minus numeric,
  unit text
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = fac_qual, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_part_revision_id integer;
  v_site_id integer;
  v_lim integer;
BEGIN
  IF p_user_id IS NULL THEN
    RETURN;
  END IF;
  v_part_revision_id := (p_params->>'part_revision_id')::integer;
  v_site_id := (p_params->>'site_id')::integer;
  IF v_part_revision_id IS NULL OR v_site_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS501', 'site_id and part_revision_id are required');
  END IF;
  IF NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'site scope denied');
  END IF;
  v_lim := GREATEST(0, COALESCE(p_limit, 500));
  RETURN QUERY
  SELECT
    ip.id,
    ip.site_id,
    ip.part_revision_id,
    p.part_number,
    pr.revision,
    ip.name,
    ip.status,
    ic.id,
    ic.seq,
    ic.characteristic_code,
    ic.description,
    ic.nominal,
    ic.tolerance_plus,
    ic.tolerance_minus,
    ic.unit
  FROM fac_qual.inspection_plans ip
  JOIN fac_eng.part_revisions pr ON pr.id = ip.part_revision_id
  JOIN fac_eng.parts p ON p.id = pr.part_id
  LEFT JOIN fac_qual.inspection_characteristics ic ON ic.inspection_plan_id = ip.id
  WHERE ip.part_revision_id = v_part_revision_id
    AND ip.site_id = v_site_id
    AND ip.status = 'active'
  ORDER BY ic.seq NULLS LAST, ic.id
  LIMIT v_lim;
END;
$$;

CREATE OR REPLACE FUNCTION fac_qual.fn_semantic_inspection_result_by_lot(
  p_user_id integer,
  p_params jsonb,
  p_limit integer
)
RETURNS TABLE (
  inspection_result_id integer,
  characteristic_id integer,
  characteristic_code text,
  lot_id integer,
  lot_number text,
  piece_number integer,
  measured_value numeric,
  pass_fail text,
  inspector_user_id integer,
  recorded_at timestamptz,
  site_id integer
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = fac_qual, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_lot_id integer;
  v_site_id integer;
  v_lim integer;
BEGIN
  IF p_user_id IS NULL THEN
    RETURN;
  END IF;
  v_lot_id := (p_params->>'lot_id')::integer;
  IF v_lot_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS501', 'lot_id is required');
  END IF;
  SELECT l.site_id INTO v_site_id FROM fac_trace.lots l WHERE l.id = v_lot_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'lot scope denied');
  END IF;
  v_lim := GREATEST(0, COALESCE(p_limit, 500));
  RETURN QUERY
  SELECT
    v.inspection_result_id,
    v.characteristic_id,
    v.characteristic_code,
    v.lot_id,
    v.lot_number,
    v.piece_number,
    v.measured_value,
    v.pass_fail,
    v.inspector_user_id,
    v.recorded_at,
    v.site_id
  FROM fac_qual.v_inspection_result v
  WHERE v.lot_id = v_lot_id
  ORDER BY v.recorded_at DESC, v.inspection_result_id DESC
  LIMIT v_lim;
END;
$$;

CREATE OR REPLACE FUNCTION fac_qual.fn_semantic_ncr_list_open(
  p_user_id integer,
  p_params jsonb,
  p_limit integer
)
RETURNS TABLE (
  ncr_id integer,
  site_id integer,
  lot_id integer,
  lot_number text,
  work_order_id integer,
  defect_code text,
  description text,
  containment text,
  status text,
  opened_at timestamptz,
  disposition text
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = fac_qual, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
  v_status text;
  v_lim integer;
BEGIN
  IF p_user_id IS NULL THEN
    RETURN;
  END IF;
  v_site_id := (p_params->>'site_id')::integer;
  IF v_site_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS501', 'site_id is required');
  END IF;
  IF NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'site scope denied');
  END IF;
  v_status := COALESCE(NULLIF(p_params->>'status', ''), 'open');
  v_lim := GREATEST(0, COALESCE(p_limit, 500));
  RETURN QUERY
  SELECT
    v.ncr_id,
    v.site_id,
    v.lot_id,
    v.lot_number,
    v.work_order_id,
    v.defect_code,
    v.description,
    v.containment,
    v.status,
    v.opened_at,
    v.disposition
  FROM fac_qual.v_ncr v
  WHERE v.site_id = v_site_id
    AND (v_status IS NULL OR v.status = v_status)
  ORDER BY v.opened_at DESC, v.ncr_id DESC
  LIMIT v_lim;
END;
$$;

CREATE OR REPLACE FUNCTION fac_audit.fn_semantic_audit_by_entity(
  p_user_id integer,
  p_params jsonb,
  p_limit integer
)
RETURNS TABLE (
  audit_id bigint,
  site_id integer,
  entity_type text,
  entity_id integer,
  action_name text,
  actor_user_id integer,
  signature_meaning text,
  record_hash text,
  created_at timestamptz
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = fac_audit, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_entity_type text;
  v_entity_id integer;
  v_site_id integer;
  v_lim integer;
BEGIN
  IF p_user_id IS NULL THEN
    RETURN;
  END IF;
  v_entity_type := NULLIF(p_params->>'entity_type', '');
  v_entity_id := (p_params->>'entity_id')::integer;
  v_site_id := (p_params->>'site_id')::integer;
  IF v_entity_type IS NULL OR v_entity_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS501', 'entity_type and entity_id are required');
  END IF;
  IF v_site_id IS NOT NULL AND NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'site scope denied');
  END IF;
  v_lim := GREATEST(0, COALESCE(p_limit, 500));
  RETURN QUERY
  SELECT
    a.id,
    a.site_id,
    a.entity_type,
    a.entity_id,
    a.action_name,
    a.actor_user_id,
    a.signature_meaning,
    a.record_hash,
    a.created_at
  FROM fac_audit.audit_log a
  WHERE a.entity_type = v_entity_type
    AND a.entity_id = v_entity_id
    AND (v_site_id IS NULL OR a.site_id = v_site_id)
    AND fac_eng.fn_user_can_access_site(p_user_id, a.site_id)
  ORDER BY a.created_at DESC, a.id DESC
  LIMIT v_lim;
END;
$$;
