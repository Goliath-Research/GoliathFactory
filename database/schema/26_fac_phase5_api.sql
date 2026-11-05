-- GoliathFactory Phase 5 — FSMA semantic functions, write APIs, offline enqueue
SET client_min_messages = warning;

CREATE OR REPLACE FUNCTION fac_trace.fn_semantic_fsma_cte_by_lot(
  p_lot_id integer
)
RETURNS SETOF fac_trace.v_fsma_cte
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = fac_trace, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
  v_user_id integer;
BEGIN
  v_user_id := NULLIF(current_setting('goliath.mfg.user_id', true), '')::integer;
  SELECT l.site_id INTO v_site_id FROM fac_trace.lots l WHERE l.id = p_lot_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(v_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'lot scope denied');
  END IF;
  RETURN QUERY
  SELECT v.*
  FROM fac_trace.v_fsma_cte v
  WHERE v.lot_id = p_lot_id
  ORDER BY v.event_at DESC, v.cte_event_id DESC;
END;
$$;

CREATE OR REPLACE FUNCTION fac_trace.fn_semantic_fsma_cte_in_window(
  p_site_id integer,
  p_hours integer DEFAULT 24
)
RETURNS SETOF fac_trace.v_fsma_cte
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = fac_trace, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_user_id integer;
  v_hours integer;
BEGIN
  v_user_id := NULLIF(current_setting('goliath.mfg.user_id', true), '')::integer;
  IF p_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(v_user_id, p_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'site scope denied');
  END IF;
  v_hours := GREATEST(1, LEAST(COALESCE(p_hours, 24), 168));
  RETURN QUERY
  SELECT v.*
  FROM fac_trace.v_fsma_cte v
  WHERE v.site_id = p_site_id
    AND v.event_at >= (now() - (v_hours || ' hours')::interval)
  ORDER BY v.event_at ASC, v.cte_event_id ASC;
END;
$$;

CREATE OR REPLACE FUNCTION fac_trace.sp_fsma_record_cte(
  p_user_id integer,
  p_site_id integer,
  p_cte_type text,
  p_event_at timestamptz,
  p_traceability_lot_code text,
  p_product_description text,
  p_lot_id integer DEFAULT NULL,
  p_quantity numeric DEFAULT NULL,
  p_quantity_uom text DEFAULT NULL,
  p_location_code text DEFAULT NULL,
  p_reference_doc_type text DEFAULT NULL,
  p_reference_doc_number text DEFAULT NULL,
  p_genealogy_link_id integer DEFAULT NULL,
  p_source text DEFAULT 'manual'
)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_trace, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_id bigint;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  IF p_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, p_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'site scope denied');
  END IF;
  IF p_cte_type NOT IN ('receiving', 'transformation', 'creation', 'shipping') THEN
    PERFORM portal.fn_semantic_raise('GS400', 'invalid cte_type');
  END IF;
  IF p_lot_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM fac_trace.lots l WHERE l.id = p_lot_id AND l.site_id = p_site_id
  ) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'lot site mismatch');
  END IF;
  PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);

  INSERT INTO fac_trace.fsma_cte_events (
    site_id,
    cte_type,
    event_at,
    lot_id,
    traceability_lot_code,
    product_description,
    quantity,
    quantity_uom,
    location_code,
    reference_doc_type,
    reference_doc_number,
    genealogy_link_id,
    recorded_by_user_id,
    source
  )
  VALUES (
    p_site_id,
    p_cte_type,
    p_event_at,
    p_lot_id,
    p_traceability_lot_code,
    p_product_description,
    p_quantity,
    p_quantity_uom,
    p_location_code,
    p_reference_doc_type,
    p_reference_doc_number,
    p_genealogy_link_id,
    p_user_id,
    COALESCE(p_source, 'manual')
  )
  RETURNING id INTO v_id;

  PERFORM fac_audit.sp_append(
    p_site_id,
    'fsma_cte',
    v_id::integer,
    'mfg.fsma.record_cte',
    p_user_id,
    NULL,
    NULL,
    jsonb_build_object(
      'cte_type', p_cte_type,
      'traceability_lot_code', p_traceability_lot_code,
      'lot_id', p_lot_id
    )
  );
  RETURN v_id;
END;
$$;

CREATE OR REPLACE FUNCTION fac_trace.sp_fsma_export_traceability_csv(
  p_user_id integer,
  p_site_id integer,
  p_hours integer DEFAULT 24
)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_trace, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_hours integer;
  v_csv text;
  v_count integer;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  IF p_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, p_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'site scope denied');
  END IF;
  v_hours := GREATEST(1, LEAST(COALESCE(p_hours, 24), 168));
  PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);

  SELECT string_agg(
    format(
      '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s',
      to_char(v.event_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
      v.cte_type,
      COALESCE(replace(v.traceability_lot_code, ',', ' '), ''),
      COALESCE(replace(v.product_description, ',', ' '), ''),
      COALESCE(v.quantity::text, ''),
      COALESCE(replace(v.quantity_uom, ',', ' '), ''),
      COALESCE(replace(v.location_code, ',', ' '), ''),
      COALESCE(replace(v.reference_doc_type, ',', ' '), ''),
      COALESCE(replace(v.reference_doc_number, ',', ' '), ''),
      COALESCE(v.lot_number, ''),
      COALESCE(v.lot_id::text, ''),
      COALESCE(replace(v.source, ',', ' '), '')
    ),
    E'\n'
    ORDER BY v.event_at ASC, v.cte_event_id ASC
  ),
  count(*)::integer
  INTO v_csv, v_count
  FROM fac_trace.v_fsma_cte v
  WHERE v.site_id = p_site_id
    AND v.event_at >= (now() - (v_hours || ' hours')::interval);

  v_csv := 'event_at_utc,cte_type,traceability_lot_code,product_description,quantity,quantity_uom,location_code,reference_doc_type,reference_doc_number,lot_number,lot_id,source'
    || E'\n'
    || COALESCE(v_csv, '');

  INSERT INTO fac_trace.fsma_traceability_exports (
    site_id,
    window_hours,
    row_count,
    csv_text,
    generated_by_user_id
  )
  VALUES (
    p_site_id,
    v_hours,
    COALESCE(v_count, 0),
    v_csv,
    p_user_id
  );

  RETURN v_csv;
END;
$$;

CREATE OR REPLACE FUNCTION fac_prod.sp_offline_enqueue(
  p_user_id integer,
  p_site_id integer,
  p_client_device_id text,
  p_idempotency_key text,
  p_action_name text,
  p_payload_json jsonb,
  p_captured_at timestamptz DEFAULT NULL
)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_prod, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_id bigint;
  v_pending integer;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  IF p_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, p_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'site scope denied');
  END IF;
  IF length(p_client_device_id) < 3 OR length(p_idempotency_key) < 8 THEN
    PERFORM portal.fn_semantic_raise('GS400', 'device id or idempotency key too short');
  END IF;
  PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);

  SELECT count(*) INTO v_pending
  FROM fac_prod.offline_outbox o
  WHERE o.site_id = p_site_id
    AND o.client_device_id = p_client_device_id
    AND o.status = 'pending';
  IF v_pending >= 100 THEN
    PERFORM portal.fn_semantic_raise('GS409', 'offline queue full for device');
  END IF;

  INSERT INTO fac_prod.offline_outbox (
    site_id,
    client_device_id,
    idempotency_key,
    action_name,
    payload_json,
    captured_at,
    status
  )
  VALUES (
    p_site_id,
    p_client_device_id,
    p_idempotency_key,
    p_action_name,
    p_payload_json,
    COALESCE(p_captured_at, now()),
    'pending'
  )
  ON CONFLICT (site_id, client_device_id, idempotency_key) DO UPDATE
    SET payload_json = EXCLUDED.payload_json,
        captured_at = EXCLUDED.captured_at
  WHERE fac_prod.offline_outbox.status = 'pending'
  RETURNING id INTO v_id;

  IF v_id IS NULL THEN
    SELECT o.id INTO v_id
    FROM fac_prod.offline_outbox o
    WHERE o.site_id = p_site_id
      AND o.client_device_id = p_client_device_id
      AND o.idempotency_key = p_idempotency_key;
  END IF;
  RETURN v_id;
END;
$$;

CREATE OR REPLACE FUNCTION fac_maint.sp_machine_record_observation(
  p_user_id integer,
  p_site_id integer,
  p_asset_id integer,
  p_source_protocol text,
  p_observed_at timestamptz,
  p_availability text DEFAULT NULL,
  p_execution_state text DEFAULT NULL,
  p_raw_payload jsonb DEFAULT '{}'::jsonb,
  p_incomplete_edges text[] DEFAULT '{}'::text[]
)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_maint, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_id bigint;
  v_asset_site integer;
  v_downtime_id integer;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  IF p_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, p_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'site scope denied');
  END IF;
  IF p_source_protocol NOT IN ('mtconnect', 'opcua') THEN
    PERFORM portal.fn_semantic_raise('GS400', 'invalid source_protocol');
  END IF;
  SELECT a.site_id INTO v_asset_site FROM fac_maint.assets a WHERE a.id = p_asset_id;
  IF v_asset_site IS NULL OR v_asset_site <> p_site_id THEN
    PERFORM portal.fn_semantic_raise('GS403', 'asset site mismatch');
  END IF;
  PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);

  INSERT INTO fac_maint.machine_observations (
    site_id,
    asset_id,
    source_protocol,
    observed_at,
    availability,
    execution_state,
    raw_payload,
    incomplete_edges
  )
  VALUES (
    p_site_id,
    p_asset_id,
    p_source_protocol,
    p_observed_at,
    p_availability,
    p_execution_state,
    COALESCE(p_raw_payload, '{}'::jsonb),
    COALESCE(p_incomplete_edges, '{}'::text[])
  )
  RETURNING id INTO v_id;

  IF lower(COALESCE(p_availability, '')) IN ('unavailable', 'not_available', 'down') THEN
    INSERT INTO fac_maint.downtime_events (
      site_id,
      asset_id,
      started_at,
      reason_code,
      comments,
      logged_by_user_id
    )
    VALUES (
      p_site_id,
      p_asset_id,
      p_observed_at,
      'machine_monitor',
      format('auto from %s observation %s', p_source_protocol, v_id),
      p_user_id
    )
    RETURNING id INTO v_downtime_id;
    UPDATE fac_maint.machine_observations
    SET downtime_event_id = v_downtime_id
    WHERE id = v_id;
  END IF;

  RETURN v_id;
END;
$$;
