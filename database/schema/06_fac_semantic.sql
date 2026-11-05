-- GoliathFactory Phase 1 — semantic read functions
SET client_min_messages = warning;

CREATE OR REPLACE FUNCTION fac_prod.fn_semantic_work_order_list_open(
  p_user_id integer,
  p_params jsonb,
  p_limit integer
)
RETURNS TABLE (
  work_order_id integer,
  site_id integer,
  part_number text,
  part_revision text,
  part_revision_id integer,
  routing_id integer,
  quantity numeric,
  output_lot_id integer,
  due_date date,
  status text
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = fac_prod, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
  v_status text;
  v_due_before date;
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
  v_status := NULLIF(p_params->>'status', '');
  v_due_before := NULLIF(p_params->>'due_before', '')::date;
  v_lim := GREATEST(0, COALESCE(p_limit, 500));
  RETURN QUERY
  SELECT
    v.work_order_id,
    v.site_id,
    v.part_number,
    v.part_revision,
    v.part_revision_id,
    v.routing_id,
    v.quantity,
    v.output_lot_id,
    v.due_date,
    v.status
  FROM fac_prod.v_work_order v
  WHERE v.site_id = v_site_id
    AND (v_status IS NULL OR v.status = v_status)
    AND (v_due_before IS NULL OR v.due_date <= v_due_before)
    AND v.status <> 'closed'
  ORDER BY v.due_date NULLS LAST, v.work_order_id
  LIMIT v_lim;
END;
$$;

CREATE OR REPLACE FUNCTION fac_prod.fn_semantic_traveler_step_by_work_order(
  p_user_id integer,
  p_params jsonb,
  p_limit integer
)
RETURNS TABLE (
  traveler_step_id integer,
  work_order_id integer,
  traveler_id integer,
  routing_operation_id integer,
  seq integer,
  operation_code text,
  status text,
  operator_user_id integer,
  machine text,
  qty_good numeric,
  qty_scrap numeric,
  signed_at timestamptz,
  started_at timestamptz,
  signer_user_id integer,
  signature_meaning text,
  record_hash text,
  site_id integer
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = fac_prod, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_work_order_id integer;
  v_site_id integer;
  v_lim integer;
BEGIN
  IF p_user_id IS NULL THEN
    RETURN;
  END IF;
  v_work_order_id := (p_params->>'work_order_id')::integer;
  IF v_work_order_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS501', 'work_order_id is required');
  END IF;
  SELECT wo.site_id INTO v_site_id FROM fac_prod.work_orders wo WHERE wo.id = v_work_order_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'work order scope denied');
  END IF;
  v_lim := GREATEST(0, COALESCE(p_limit, 500));
  RETURN QUERY
  SELECT
    v.traveler_step_id,
    v.work_order_id,
    v.traveler_id,
    v.routing_operation_id,
    v.seq,
    v.operation_code,
    v.status,
    v.operator_user_id,
    v.machine,
    v.qty_good,
    v.qty_scrap,
    v.signed_at,
    v.started_at,
    v.signer_user_id,
    v.signature_meaning,
    v.record_hash,
    v.site_id
  FROM fac_prod.v_traveler_step v
  WHERE v.work_order_id = v_work_order_id
  ORDER BY v.seq, v.traveler_step_id
  LIMIT v_lim;
END;
$$;

CREATE OR REPLACE FUNCTION fac_trace.fn_semantic_lot_genealogy(
  p_user_id integer,
  p_params jsonb,
  p_limit integer
)
RETURNS TABLE (
  lot_id integer,
  lot_number text,
  kind text,
  depth integer,
  direction text,
  link_kind text,
  related_lot_id integer,
  related_lot_number text
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = fac_trace, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_lot_id integer;
  v_direction text;
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
  v_direction := COALESCE(NULLIF(p_params->>'direction', ''), 'forward');
  SELECT l.site_id INTO v_site_id FROM fac_trace.lots l WHERE l.id = v_lot_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'lot scope denied');
  END IF;
  v_lim := GREATEST(0, COALESCE(p_limit, 500));
  RETURN QUERY
  SELECT g.*
  FROM fac_trace.fn_genealogy(v_lot_id, v_direction) g
  LIMIT v_lim;
END;
$$;
