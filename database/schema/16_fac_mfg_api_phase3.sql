-- GoliathFactory Phase 3 — domain write APIs (CAPA, gauge, document, FAI, CoC, inv bridge)
SET client_min_messages = warning;

CREATE OR REPLACE FUNCTION fac_qual.sp_capa_close(
  p_user_id integer,
  p_capa_id integer,
  p_effectiveness_notes text,
  p_signature_meaning text DEFAULT 'CAPA closed — effectiveness verified',
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
  v_open_actions integer;
  v_hash text;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  SELECT c.site_id, c.status INTO v_site_id, v_status
  FROM fac_qual.capas c
  WHERE c.id = p_capa_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'CAPA scope denied');
  END IF;
  IF v_status = 'closed' THEN
    PERFORM portal.fn_semantic_raise('GS409', 'CAPA already closed');
  END IF;
  SELECT count(*) INTO v_open_actions
  FROM fac_qual.capa_actions ca
  WHERE ca.capa_id = p_capa_id AND ca.status <> 'complete';
  IF v_open_actions > 0 THEN
    PERFORM portal.fn_semantic_raise('GS409', 'complete CAPA actions before closure');
  END IF;
  PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);
  v_hash := COALESCE(
    p_record_hash,
    encode(public.digest(p_capa_id::text || '|close|' || now()::text, 'sha256'), 'hex')
  );
  UPDATE fac_qual.capas
  SET
    status = 'closed',
    effectiveness_notes = p_effectiveness_notes,
    closed_at = now(),
    closed_by_user_id = p_user_id
  WHERE id = p_capa_id;
  PERFORM fac_audit.sp_append(
    v_site_id,
    'capa',
    p_capa_id,
    'mfg.capa.close',
    p_user_id,
    p_signature_meaning,
    v_hash,
    jsonb_build_object('effectiveness_notes', p_effectiveness_notes)
  );
  RETURN 'closed';
END;
$$;

CREATE OR REPLACE FUNCTION fac_gauge.sp_lockout_check(
  p_gauge_id integer
)
RETURNS boolean
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = fac_gauge, pg_temp
AS $$
DECLARE
  v_locked boolean;
BEGIN
  SELECT v.locked_out INTO v_locked
  FROM fac_gauge.v_gauge v
  WHERE v.gauge_id = p_gauge_id;
  IF v_locked IS NULL THEN
    RETURN true;
  END IF;
  RETURN v_locked;
END;
$$;

CREATE OR REPLACE FUNCTION fac_doc.sp_document_submit_review(
  p_user_id integer,
  p_revision_id integer,
  p_change_summary text DEFAULT NULL
)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_doc, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
  v_status text;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  SELECT d.site_id, dr.status INTO v_site_id, v_status
  FROM fac_doc.document_revisions dr
  JOIN fac_doc.documents d ON d.id = dr.document_id
  WHERE dr.id = p_revision_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'document scope denied');
  END IF;
  IF v_status NOT IN ('draft', 'review') THEN
    PERFORM portal.fn_semantic_raise('GS409', 'revision not in draft/review');
  END IF;
  PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);
  UPDATE fac_doc.document_revisions
  SET
    status = 'review',
    change_summary = COALESCE(p_change_summary, change_summary),
    submitted_at = now()
  WHERE id = p_revision_id;
  PERFORM fac_audit.sp_append(
    v_site_id,
    'document_revision',
    p_revision_id,
    'mfg.document.submit_review',
    p_user_id,
    NULL,
    NULL,
    jsonb_build_object('status', 'review')
  );
  RETURN 'review';
END;
$$;

CREATE OR REPLACE FUNCTION fac_doc.sp_document_approve(
  p_user_id integer,
  p_revision_id integer,
  p_signature_meaning text DEFAULT 'Controlled document approved',
  p_record_hash text DEFAULT NULL,
  p_effective_on date DEFAULT NULL
)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_doc, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
  v_status text;
  v_hash text;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  SELECT d.site_id, dr.status INTO v_site_id, v_status
  FROM fac_doc.document_revisions dr
  JOIN fac_doc.documents d ON d.id = dr.document_id
  WHERE dr.id = p_revision_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'document scope denied');
  END IF;
  IF v_status <> 'review' THEN
    PERFORM portal.fn_semantic_raise('GS409', 'revision must be in review');
  END IF;
  PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);
  v_hash := COALESCE(
    p_record_hash,
    encode(public.digest(p_revision_id::text || '|approve', 'sha256'), 'hex')
  );
  UPDATE fac_doc.document_revisions
  SET
    status = 'effective',
    approved_at = now(),
    effective_on = COALESCE(p_effective_on, CURRENT_DATE)
  WHERE id = p_revision_id;
  INSERT INTO fac_doc.document_approvals (
    revision_id,
    approver_user_id,
    signature_meaning,
    record_hash
  )
  VALUES (p_revision_id, p_user_id, p_signature_meaning, v_hash);
  PERFORM fac_audit.sp_append(
    v_site_id,
    'document_revision',
    p_revision_id,
    'mfg.document.approve',
    p_user_id,
    p_signature_meaning,
    v_hash,
    jsonb_build_object('effective_on', COALESCE(p_effective_on, CURRENT_DATE))
  );
  RETURN 'effective';
END;
$$;

CREATE OR REPLACE FUNCTION fac_qual.sp_fai_start(
  p_user_id integer,
  p_work_order_id integer,
  p_inspection_plan_id integer DEFAULT NULL
)
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_qual, fac_prod, fac_eng, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
  v_part_revision_id integer;
  v_plan_id integer;
  v_fai_id integer;
  v_existing_status text;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  SELECT wo.site_id, wo.part_revision_id INTO v_site_id, v_part_revision_id
  FROM fac_prod.work_orders wo
  WHERE wo.id = p_work_order_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'work order scope denied');
  END IF;
  v_plan_id := COALESCE(
    p_inspection_plan_id,
    (
      SELECT ip.id
      FROM fac_qual.inspection_plans ip
      WHERE ip.part_revision_id = v_part_revision_id
        AND ip.site_id = v_site_id
        AND ip.status = 'active'
      ORDER BY ip.id
      LIMIT 1
    )
  );
  IF v_plan_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS409', 'active inspection plan required to start FAI');
  END IF;
  SELECT f.status INTO v_existing_status
  FROM fac_qual.first_article_reports f
  WHERE f.work_order_id = p_work_order_id;
  IF v_existing_status IS NOT NULL THEN
    PERFORM portal.fn_semantic_raise('GS409', 'FAI already exists for work order');
  END IF;
  PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);
  INSERT INTO fac_qual.first_article_reports (
    site_id,
    work_order_id,
    part_revision_id,
    inspection_plan_id,
    status,
    as9102_form_ref
  )
  VALUES (
    v_site_id,
    p_work_order_id,
    v_part_revision_id,
    v_plan_id,
    'in_progress',
    'AS9102-1'
  )
  RETURNING id INTO v_fai_id;
  PERFORM fac_audit.sp_append(
    v_site_id,
    'first_article',
    v_fai_id,
    'mfg.fai.start',
    p_user_id,
    NULL,
    NULL,
    jsonb_build_object('work_order_id', p_work_order_id)
  );
  RETURN v_fai_id;
END;
$$;

CREATE OR REPLACE FUNCTION fac_qual.sp_fai_approve(
  p_user_id integer,
  p_first_article_id integer,
  p_signature_meaning text DEFAULT 'First article approved — run released',
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
  v_plan_id integer;
  v_work_order_id integer;
  v_required integer;
  v_recorded integer;
  v_hash text;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  SELECT f.site_id, f.status, f.inspection_plan_id, f.work_order_id
  INTO v_site_id, v_status, v_plan_id, v_work_order_id
  FROM fac_qual.first_article_reports f
  WHERE f.id = p_first_article_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'FAI scope denied');
  END IF;
  IF v_status = 'approved' THEN
    PERFORM portal.fn_semantic_raise('GS409', 'FAI already approved');
  END IF;
  IF v_plan_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS409', 'inspection plan required before FAI approval');
  END IF;
  SELECT count(*) INTO v_required
  FROM fac_qual.inspection_characteristics ic
  WHERE ic.inspection_plan_id = v_plan_id;
  SELECT count(DISTINCT ir.characteristic_id) INTO v_recorded
  FROM fac_qual.inspection_results ir
  JOIN fac_qual.inspection_characteristics ic ON ic.id = ir.characteristic_id
  WHERE ic.inspection_plan_id = v_plan_id
    AND ir.work_order_id = v_work_order_id
    AND ir.pass_fail = 'pass';
  IF v_required > 0 AND v_recorded < v_required THEN
    PERFORM portal.fn_semantic_raise(
      'GS409',
      'record passing results for all plan characteristics before FAI approval'
    );
  END IF;
  PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);
  v_hash := COALESCE(
    p_record_hash,
    encode(public.digest(v_work_order_id::text || '|fai', 'sha256'), 'hex')
  );
  UPDATE fac_qual.first_article_reports
  SET
    status = 'approved',
    qa_approved_at = now(),
    qa_approver_user_id = p_user_id
  WHERE id = p_first_article_id;
  PERFORM fac_audit.sp_append(
    v_site_id,
    'first_article',
    p_first_article_id,
    'mfg.fai.approve',
    p_user_id,
    p_signature_meaning,
    v_hash,
    jsonb_build_object('work_order_id', v_work_order_id)
  );
  RETURN 'approved';
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
  v_kind text;
  v_heat text;
  v_doc jsonb;
  v_hash text;
  v_coc_number text;
  v_genealogy jsonb;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  SELECT l.site_id, l.lot_number, l.kind, l.heat_number
  INTO v_site_id, v_lot_number, v_kind, v_heat
  FROM fac_trace.lots l
  WHERE l.id = p_lot_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'lot scope denied');
  END IF;
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
    'lot_id', g.lot_id,
    'lot_number', g.lot_number,
    'kind', g.kind,
    'depth', g.depth,
    'link_kind', g.link_kind
  ) ORDER BY g.depth), '[]'::jsonb)
  INTO v_genealogy
  FROM fac_trace.fn_genealogy(p_lot_id, 'backward') g
  WHERE g.depth > 0;

  v_doc := jsonb_build_object(
    'kind', 'certificate_of_conformance',
    'schema_version', '1',
    'standard_refs', jsonb_build_array('AS9100', 'customer CoC'),
    'lot_id', p_lot_id,
    'lot_number', v_lot_number,
    'lot_kind', v_kind,
    'heat_number', v_heat,
    'generated_at', now(),
    'material_genealogy', v_genealogy,
    'inspection_summary', (
      SELECT COALESCE(jsonb_agg(jsonb_build_object(
        'characteristic_code', ir.characteristic_code,
        'pass_fail', ir.pass_fail,
        'recorded_at', ir.recorded_at
      ) ORDER BY ir.recorded_at), '[]'::jsonb)
      FROM fac_qual.v_inspection_result ir
      WHERE ir.lot_id = p_lot_id
    )
  );
  v_hash := encode(public.digest(v_doc::text, 'sha256'), 'hex');
  v_coc_number := 'COC-' || v_lot_number || '-' || to_char(now(), 'YYYYMMDD');
  INSERT INTO fac_trace.certificates_of_conformance (
    site_id,
    lot_id,
    coc_number,
    document_json,
    record_hash,
    generated_by_user_id
  )
  VALUES (
    v_site_id,
    p_lot_id,
    v_coc_number,
    v_doc || jsonb_build_object('coc_number', v_coc_number, 'record_hash', v_hash),
    v_hash,
    p_user_id
  )
  ON CONFLICT (site_id, coc_number) DO UPDATE
  SET
    document_json = EXCLUDED.document_json,
    record_hash = EXCLUDED.record_hash,
    generated_at = now(),
    generated_by_user_id = EXCLUDED.generated_by_user_id;
  PERFORM fac_audit.sp_append(
    v_site_id,
    'lot',
    p_lot_id,
    'mfg.lot.coc_generate',
    p_user_id,
    'Certificate of conformance issued',
    v_hash,
    v_doc || jsonb_build_object('coc_number', v_coc_number)
  );
  RETURN v_doc || jsonb_build_object('coc_number', v_coc_number, 'record_hash', v_hash);
END;
$$;

CREATE OR REPLACE FUNCTION fac_inv_hooks.fn_inv_schema_ready()
RETURNS boolean
LANGUAGE sql
STABLE
SET search_path = pg_catalog, pg_temp
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM pg_namespace n
    JOIN pg_proc p ON p.pronamespace = n.oid
    WHERE n.nspname = 'inv' AND p.proname = 'sp_stock_receive'
  );
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
DECLARE
  v_org_id integer;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  IF NOT fac_eng.fn_user_can_access_site(p_user_id, p_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'site scope denied');
  END IF;
  IF fac_inv_hooks.fn_inv_schema_ready() THEN
    SELECT s.organization_id INTO v_org_id
    FROM fac_eng.sites s
    WHERE s.id = p_site_id;
    RETURN jsonb_build_object(
      'status', 'inv_ready',
      'message',
      'GoliathApp inv module detected — call inv.stock.receive via gateway with organization_id '
      || COALESCE(v_org_id::text, '?')
      || ' and map receipt lot to fac_trace for genealogy.',
      'organization_id', v_org_id,
      'suggested_action', 'inv.stock.receive',
      'item_ref', p_item_ref,
      'quantity', p_quantity,
      'lot_number', p_lot_number
    );
  END IF;
  RETURN jsonb_build_object(
    'status', 'stub',
    'dependency', 'GoliathApp inv module (PR #34)',
    'next_steps', jsonb_build_array(
      'inv.stock.receive (inv.sp_stock_receive)',
      'fac_qual incoming inspection hook',
      'mfg.inspection_result.record on accept'
    ),
    'item_ref', p_item_ref,
    'quantity', p_quantity,
    'lot_number', p_lot_number
  );
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
SET search_path = fac_qual, fac_gauge, fac_eng, portal, pg_temp
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
  IF p_gauge_id IS NOT NULL AND fac_gauge.sp_lockout_check(p_gauge_id) THEN
    PERFORM portal.fn_semantic_raise('GS409', 'gauge locked out — calibration overdue or inactive');
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
    p_piece_number,
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
      'pass_fail', v_pass
    )
  );
  RETURN v_result_id;
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
  v_org_id integer;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;
  SELECT wo.site_id INTO v_site_id FROM fac_prod.work_orders wo WHERE wo.id = p_work_order_id;
  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'work order scope denied');
  END IF;
  IF fac_inv_hooks.fn_inv_schema_ready() THEN
    SELECT s.organization_id INTO v_org_id
    FROM fac_eng.sites s
    WHERE s.id = v_site_id;
    RETURN jsonb_build_object(
      'status', 'inv_ready',
      'message',
      'GoliathApp inv module detected — call inv.stock.issue with ref_type work_order and ref_id '
      || p_work_order_id::text
      || '; then link fac_trace.lot_links for genealogy.',
      'organization_id', v_org_id,
      'suggested_action', 'inv.stock.issue',
      'work_order_id', p_work_order_id,
      'stock_lot_ref', p_stock_lot_ref,
      'quantity', p_quantity
    );
  END IF;
  RETURN jsonb_build_object(
    'status', 'stub',
    'dependency', 'GoliathApp inv module (PR #34)',
    'next_steps', jsonb_build_array(
      'inv.stock.issue',
      'fac_trace.lot_links consume edge for genealogy'
    ),
    'work_order_id', p_work_order_id,
    'stock_lot_ref', p_stock_lot_ref,
    'quantity', p_quantity
  );
END;
$$;
