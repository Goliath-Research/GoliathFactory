-- GoliathFactory Phase 3 — semantic read functions
SET client_min_messages = warning;

CREATE OR REPLACE FUNCTION fac_qual.fn_semantic_capa_list_open(
  p_user_id integer,
  p_params jsonb,
  p_limit integer
)
RETURNS TABLE (
  capa_id integer,
  site_id integer,
  capa_number text,
  title text,
  root_cause text,
  status text,
  opened_at timestamptz,
  source_ncr_count integer,
  open_action_count integer
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
  v_status := NULLIF(p_params->>'status', '');
  v_lim := GREATEST(0, COALESCE(p_limit, 500));
  RETURN QUERY
  SELECT
    v.capa_id,
    v.site_id,
    v.capa_number,
    v.title,
    v.root_cause,
    v.status,
    v.opened_at,
    v.source_ncr_count,
    v.open_action_count
  FROM fac_qual.v_capa v
  WHERE v.site_id = v_site_id
    AND (v_status IS NULL OR v.status = v_status)
  ORDER BY v.opened_at DESC, v.capa_id DESC
  LIMIT v_lim;
END;
$$;

CREATE OR REPLACE FUNCTION fac_gauge.fn_semantic_gauge_due_calibration(
  p_user_id integer,
  p_params jsonb,
  p_limit integer
)
RETURNS TABLE (
  gauge_id integer,
  site_id integer,
  gauge_tag text,
  gauge_type text,
  location text,
  next_cal_due_on date,
  locked_out boolean,
  status text
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = fac_gauge, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
  v_within_days integer;
  v_cutoff date;
  v_lim integer;
BEGIN
  IF p_user_id IS NULL THEN
    RETURN;
  END IF;
  v_site_id := (p_params->>'site_id')::integer;
  v_within_days := COALESCE((p_params->>'within_days')::integer, 30);
  IF v_site_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS501', 'site_id is required');
  END IF;
  IF NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'site scope denied');
  END IF;
  v_cutoff := CURRENT_DATE + v_within_days;
  v_lim := GREATEST(0, COALESCE(p_limit, 500));
  RETURN QUERY
  SELECT
    v.gauge_id,
    v.site_id,
    v.gauge_tag,
    v.gauge_type,
    v.location,
    v.next_cal_due_on,
    v.locked_out,
    v.status
  FROM fac_gauge.v_gauge v
  WHERE v.site_id = v_site_id
    AND (
      v.locked_out
      OR v.next_cal_due_on IS NULL
      OR v.next_cal_due_on <= v_cutoff
    )
  ORDER BY v.next_cal_due_on NULLS FIRST, v.gauge_tag
  LIMIT v_lim;
END;
$$;

CREATE OR REPLACE FUNCTION fac_doc.fn_semantic_document_list(
  p_user_id integer,
  p_params jsonb,
  p_limit integer
)
RETURNS TABLE (
  document_id integer,
  site_id integer,
  doc_number text,
  title text,
  doc_type text,
  revision_id integer,
  revision text,
  status text,
  effective_on date
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = fac_doc, fac_eng, portal, pg_temp
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
  v_status := NULLIF(p_params->>'status', '');
  v_lim := GREATEST(0, COALESCE(p_limit, 500));
  RETURN QUERY
  SELECT
    v.document_id,
    v.site_id,
    v.doc_number,
    v.title,
    v.doc_type,
    v.revision_id,
    v.revision,
    v.status,
    v.effective_on
  FROM fac_doc.v_document v
  WHERE v.site_id = v_site_id
    AND (v_status IS NULL OR v.status = v_status)
  ORDER BY v.doc_number, v.revision DESC NULLS LAST
  LIMIT v_lim;
END;
$$;

CREATE OR REPLACE FUNCTION fac_qual.fn_semantic_fai_by_work_order(
  p_user_id integer,
  p_params jsonb,
  p_limit integer
)
RETURNS TABLE (
  first_article_id integer,
  site_id integer,
  work_order_id integer,
  part_number text,
  part_revision text,
  status text,
  result_count integer,
  qa_approved_at timestamptz
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = fac_qual, fac_eng, portal, pg_temp
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
    v.first_article_id,
    v.site_id,
    v.work_order_id,
    v.part_number,
    v.part_revision,
    v.status,
    v.result_count,
    v.qa_approved_at
  FROM fac_qual.v_first_article v
  WHERE v.work_order_id = v_work_order_id
  LIMIT v_lim;
END;
$$;
