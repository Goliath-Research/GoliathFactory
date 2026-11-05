-- GoliathFactory Phase 2 — domain write procedures and inv integration hooks
SET client_min_messages = warning;

CREATE SCHEMA IF NOT EXISTS fac_inv_hooks;

COMMENT ON SCHEMA fac_inv_hooks IS
  'Stubs until GoliathApp inv module merges (GoliathApp PR #34). '
  'Replace with calls into inv.* procs when inv is enabled on the deployment.';

CREATE OR REPLACE FUNCTION fac_audit.sp_append(
  p_site_id integer,
  p_entity_type text,
  p_entity_id integer,
  p_action_name text,
  p_actor_user_id integer,
  p_signature_meaning text DEFAULT NULL,
  p_record_hash text DEFAULT NULL,
  p_detail_json jsonb DEFAULT NULL
)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_audit, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_id bigint;
BEGIN
  INSERT INTO fac_audit.audit_log (
    site_id,
    entity_type,
    entity_id,
    action_name,
    actor_user_id,
    signature_meaning,
    record_hash,
    detail_json
  )
  VALUES (
    p_site_id,
    p_entity_type,
    p_entity_id,
    p_action_name,
    p_actor_user_id,
    p_signature_meaning,
    p_record_hash,
    p_detail_json
  )
  RETURNING id INTO v_id;
  RETURN v_id;
END;
$$;

CREATE OR REPLACE FUNCTION fac_prod.sp_work_order_release(
  p_user_id integer,
  p_work_order_id integer
)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_prod, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
  v_status text;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  SELECT wo.site_id, wo.status INTO v_site_id, v_status
  FROM fac_prod.work_orders wo
  WHERE wo.id = p_work_order_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'work order scope denied');
  END IF;
  PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);
  IF v_status NOT IN ('planned', 'released') THEN
    PERFORM portal.fn_semantic_raise('GS409', 'work order cannot be released from current status');
  END IF;
  UPDATE fac_prod.work_orders SET status = 'released' WHERE id = p_work_order_id;
  INSERT INTO fac_prod.travelers (work_order_id)
  SELECT p_work_order_id
  WHERE NOT EXISTS (
    SELECT 1 FROM fac_prod.travelers t WHERE t.work_order_id = p_work_order_id
  );
  INSERT INTO fac_prod.traveler_steps (traveler_id, routing_operation_id, seq, operation_code)
  SELECT t.id, ro.id, ro.seq, ro.operation_code
  FROM fac_prod.travelers t
  JOIN fac_prod.work_orders wo ON wo.id = t.work_order_id
  JOIN fac_eng.routing_operations ro ON ro.routing_id = wo.routing_id
  WHERE t.work_order_id = p_work_order_id
    AND wo.routing_id IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM fac_prod.traveler_steps ts WHERE ts.traveler_id = t.id
    );
  PERFORM fac_audit.sp_append(
    v_site_id,
    'work_order',
    p_work_order_id,
    'mfg.work_order.release',
    p_user_id,
    'Release to shop floor',
    NULL,
    jsonb_build_object('status', 'released')
  );
  RETURN 'released';
END;
$$;

CREATE OR REPLACE FUNCTION fac_prod.sp_traveler_step_start(
  p_user_id integer,
  p_traveler_step_id integer,
  p_machine text DEFAULT NULL
)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_prod, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
  v_status text;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  SELECT wo.site_id, ts.status INTO v_site_id, v_status
  FROM fac_prod.traveler_steps ts
  JOIN fac_prod.travelers t ON t.id = ts.traveler_id
  JOIN fac_prod.work_orders wo ON wo.id = t.work_order_id
  WHERE ts.id = p_traveler_step_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'traveler step scope denied');
  END IF;
  IF v_status NOT IN ('pending', 'in_progress') THEN
    PERFORM portal.fn_semantic_raise('GS409', 'step cannot be started');
  END IF;
  PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);
  UPDATE fac_prod.traveler_steps
  SET
    status = 'in_progress',
    started_at = COALESCE(started_at, now()),
    operator_user_id = p_user_id,
    machine = COALESCE(p_machine, machine)
  WHERE id = p_traveler_step_id;
  PERFORM fac_audit.sp_append(
    v_site_id,
    'traveler_step',
    p_traveler_step_id,
    'mfg.traveler_step.start',
    p_user_id,
    NULL,
    NULL,
    jsonb_build_object('machine', p_machine)
  );
  RETURN 'in_progress';
END;
$$;

CREATE OR REPLACE FUNCTION fac_prod.sp_traveler_step_sign_off(
  p_user_id integer,
  p_traveler_step_id integer,
  p_qty_good numeric,
  p_qty_scrap numeric DEFAULT 0,
  p_machine text DEFAULT NULL,
  p_signature_meaning text DEFAULT 'Operation complete',
  p_record_hash text DEFAULT NULL
)
RETURNS timestamptz
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_prod, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
  v_status text;
  v_signed timestamptz;
  v_hash text;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  SELECT wo.site_id, ts.status INTO v_site_id, v_status
  FROM fac_prod.traveler_steps ts
  JOIN fac_prod.travelers t ON t.id = ts.traveler_id
  JOIN fac_prod.work_orders wo ON wo.id = t.work_order_id
  WHERE ts.id = p_traveler_step_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'traveler step scope denied');
  END IF;
  IF v_status NOT IN ('in_progress', 'pending') THEN
    PERFORM portal.fn_semantic_raise('GS409', 'step already signed or held');
  END IF;
  PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);
  v_signed := now();
  v_hash := COALESCE(
    p_record_hash,
    encode(public.digest(
      p_traveler_step_id::text || '|' || p_qty_good::text || '|' || v_signed::text,
      'sha256'
    ), 'hex')
  );
  UPDATE fac_prod.traveler_steps
  SET
    status = 'complete',
    qty_good = p_qty_good,
    qty_scrap = COALESCE(p_qty_scrap, 0),
    machine = COALESCE(p_machine, machine),
    signed_at = v_signed,
    signer_user_id = p_user_id,
    signature_meaning = p_signature_meaning,
    record_hash = v_hash
  WHERE id = p_traveler_step_id;
  PERFORM fac_audit.sp_append(
    v_site_id,
    'traveler_step',
    p_traveler_step_id,
    'mfg.traveler_step.sign_off',
    p_user_id,
    p_signature_meaning,
    v_hash,
    jsonb_build_object(
      'qty_good', p_qty_good,
      'qty_scrap', COALESCE(p_qty_scrap, 0),
      'machine', p_machine
    )
  );
  RETURN v_signed;
END;
$$;

CREATE OR REPLACE FUNCTION fac_qual.sp_inspection_result_record(
  p_user_id integer,
  p_characteristic_id integer,
  p_lot_id integer DEFAULT NULL,
  p_work_order_id integer DEFAULT NULL,
  p_piece_number integer DEFAULT 1,
  p_measured_value numeric DEFAULT NULL,
  p_pass_fail text DEFAULT NULL,
  p_gauge_id integer DEFAULT NULL,
  p_signature_meaning text DEFAULT 'Inspection recorded',
  p_record_hash text DEFAULT NULL
)
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_qual, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
  v_result_id integer;
  v_pass text;
  v_hash text;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  SELECT ip.site_id INTO v_site_id
  FROM fac_qual.inspection_characteristics ic
  JOIN fac_qual.inspection_plans ip ON ip.id = ic.inspection_plan_id
  WHERE ic.id = p_characteristic_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'characteristic scope denied');
  END IF;
  v_pass := COALESCE(p_pass_fail, 'pass');
  PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);
  INSERT INTO fac_qual.inspection_results (
    characteristic_id,
    lot_id,
    work_order_id,
    piece_number,
    measured_value,
    pass_fail,
    inspector_user_id,
    gauge_id
  )
  VALUES (
    p_characteristic_id,
    p_lot_id,
    p_work_order_id,
    COALESCE(p_piece_number, 1),
    p_measured_value,
    v_pass,
    p_user_id,
    p_gauge_id
  )
  RETURNING id INTO v_result_id;
  v_hash := COALESCE(
    p_record_hash,
    encode(public.digest(v_result_id::text || '|' || v_pass, 'sha256'), 'hex')
  );
  PERFORM fac_audit.sp_append(
    v_site_id,
    'inspection_result',
    v_result_id,
    'mfg.inspection_result.record',
    p_user_id,
    p_signature_meaning,
    v_hash,
    jsonb_build_object(
      'characteristic_id', p_characteristic_id,
      'lot_id', p_lot_id,
      'pass_fail', v_pass
    )
  );
  RETURN v_result_id;
END;
$$;

CREATE OR REPLACE FUNCTION fac_qual.sp_ncr_open(
  p_user_id integer,
  p_site_id integer,
  p_defect_code text,
  p_description text,
  p_part_revision_id integer DEFAULT NULL,
  p_lot_id integer DEFAULT NULL,
  p_work_order_id integer DEFAULT NULL,
  p_containment text DEFAULT NULL
)
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_qual, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_ncr_id integer;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  IF NOT fac_eng.fn_user_can_access_site(p_user_id, p_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'site scope denied');
  END IF;
  PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);
  INSERT INTO fac_qual.ncrs (
    site_id,
    part_revision_id,
    lot_id,
    work_order_id,
    defect_code,
    description,
    containment,
    status,
    opened_by_user_id
  )
  VALUES (
    p_site_id,
    p_part_revision_id,
    p_lot_id,
    p_work_order_id,
    p_defect_code,
    p_description,
    p_containment,
    'open',
    p_user_id
  )
  RETURNING id INTO v_ncr_id;
  PERFORM fac_audit.sp_append(
    p_site_id,
    'ncr',
    v_ncr_id,
    'mfg.ncr.open',
    p_user_id,
    'Open nonconformance',
    NULL,
    jsonb_build_object('defect_code', p_defect_code)
  );
  RETURN v_ncr_id;
END;
$$;

CREATE OR REPLACE FUNCTION fac_qual.sp_ncr_disposition(
  p_user_id integer,
  p_ncr_id integer,
  p_disposition text,
  p_signature_meaning text,
  p_record_hash text DEFAULT NULL
)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_qual, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
  v_status text;
  v_hash text;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  SELECT n.site_id, n.status INTO v_site_id, v_status
  FROM fac_qual.ncrs n
  WHERE n.id = p_ncr_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'ncr scope denied');
  END IF;
  IF v_status <> 'open' THEN
    PERFORM portal.fn_semantic_raise('GS409', 'ncr is not open');
  END IF;
  PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);
  v_hash := COALESCE(
    p_record_hash,
    encode(public.digest(p_ncr_id::text || '|' || p_disposition, 'sha256'), 'hex')
  );
  INSERT INTO fac_qual.mrb_dispositions (
    ncr_id,
    disposition,
    signer_user_id,
    signature_meaning,
    record_hash
  )
  VALUES (
    p_ncr_id,
    p_disposition,
    p_user_id,
    p_signature_meaning,
    v_hash
  );
  UPDATE fac_qual.ncrs SET status = 'dispositioned' WHERE id = p_ncr_id;
  PERFORM fac_audit.sp_append(
    v_site_id,
    'ncr',
    p_ncr_id,
    'mfg.ncr.disposition',
    p_user_id,
    p_signature_meaning,
    v_hash,
    jsonb_build_object('disposition', p_disposition)
  );
  RETURN p_disposition;
END;
$$;

CREATE OR REPLACE FUNCTION fac_trace.sp_lot_coc_generate(
  p_user_id integer,
  p_lot_id integer
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_trace, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
  v_lot_number text;
  v_doc jsonb;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  SELECT l.site_id, l.lot_number INTO v_site_id, v_lot_number
  FROM fac_trace.lots l
  WHERE l.id = p_lot_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'lot scope denied');
  END IF;
  v_doc := jsonb_build_object(
    'kind', 'certificate_of_conformance_stub',
    'lot_id', p_lot_id,
    'lot_number', v_lot_number,
    'generated_at', now(),
    'note', 'Pilot stub — full CoC export lands in Phase 3'
  );
  PERFORM fac_audit.sp_append(
    v_site_id,
    'lot',
    p_lot_id,
    'mfg.lot.coc_generate',
    p_user_id,
    'Generate CoC (stub)',
    encode(public.digest(v_doc::text, 'sha256'), 'hex'),
    v_doc
  );
  RETURN v_doc;
END;
$$;

CREATE OR REPLACE FUNCTION fac_inv_hooks.sp_receive_with_inspection(
  p_user_id integer,
  p_site_id integer,
  p_item_ref text,
  p_quantity numeric,
  p_lot_number text DEFAULT NULL
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_inv_hooks, fac_eng, portal, pg_temp
AS $$
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  IF NOT fac_eng.fn_user_can_access_site(p_user_id, p_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'site scope denied');
  END IF;
  RETURN jsonb_build_object(
    'status', 'stub',
    'dependency', 'GoliathApp inv module (PR #34)',
    'next_steps', jsonb_build_array(
      'inv.sp_receive_po_line',
      'fac_qual incoming inspection hook',
      'mfg.inspection_result.record on accept'
    ),
    'item_ref', p_item_ref,
    'quantity', p_quantity,
    'lot_number', p_lot_number
  );
END;
$$;

CREATE OR REPLACE FUNCTION fac_inv_hooks.sp_issue_to_work_order(
  p_user_id integer,
  p_work_order_id integer,
  p_stock_lot_ref text,
  p_quantity numeric
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_inv_hooks, fac_trace, fac_prod, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  SELECT wo.site_id INTO v_site_id FROM fac_prod.work_orders wo WHERE wo.id = p_work_order_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'work order scope denied');
  END IF;
  RETURN jsonb_build_object(
    'status', 'stub',
    'dependency', 'GoliathApp inv module (PR #34)',
    'next_steps', jsonb_build_array(
      'inv.sp_issue_to_work_order',
      'fac_trace.lot_links consume edge for genealogy'
    ),
    'work_order_id', p_work_order_id,
    'stock_lot_ref', p_stock_lot_ref,
    'quantity', p_quantity
  );
END;
$$;
