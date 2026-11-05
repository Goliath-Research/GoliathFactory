-- GoliathFactory Phase 3 — wire GoliathApp inv module to fac_trace genealogy
SET client_min_messages = warning;

CREATE SCHEMA IF NOT EXISTS fac_mfg_inv;

COMMENT ON SCHEMA fac_mfg_inv IS
  'Factory inventory integration: wraps inv.* writes and maps stock lots to fac_trace lots.';

CREATE TABLE IF NOT EXISTS fac_mfg_inv.stock_lot_trace (
  stock_lot_id integer PRIMARY KEY,
  organization_id integer NOT NULL,
  site_id integer NOT NULL REFERENCES fac_eng.sites (id) ON DELETE RESTRICT,
  trace_lot_id integer NOT NULL REFERENCES fac_trace.lots (id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION fac_mfg_inv.sp_receive_with_inspection(
  p_organization_id integer,
  p_user_id integer,
  p_po_line_id integer,
  p_bin_id integer,
  p_qty numeric,
  p_lot_number text DEFAULT NULL,
  p_unit_price_override numeric DEFAULT NULL,
  p_site_id integer DEFAULT NULL,
  OUT receipt_id integer,
  OUT stock_lot_id integer,
  OUT avg_unit_cost numeric,
  OUT trace_lot_id integer
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_mfg_inv, inv, fac_trace, fac_eng, fac_audit, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
  v_lot_label text;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;

  SELECT r.receipt_id, r.stock_lot_id, r.avg_unit_cost
  INTO receipt_id, stock_lot_id, avg_unit_cost
  FROM inv.sp_stock_receive(
    p_organization_id,
    p_user_id,
    p_po_line_id,
    p_bin_id,
    p_qty,
    p_lot_number,
    p_unit_price_override
  ) AS r;

  trace_lot_id := NULL;
  v_site_id := p_site_id;
  IF v_site_id IS NULL THEN
    SELECT s.id INTO v_site_id
    FROM fac_eng.sites s
    WHERE s.organization_id = p_organization_id
    ORDER BY s.id
    LIMIT 1;
  END IF;

  IF v_site_id IS NOT NULL AND fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);
    v_lot_label := COALESCE(NULLIF(btrim(p_lot_number), ''), 'SL-' || stock_lot_id::text);
    INSERT INTO fac_trace.lots (site_id, lot_number, kind, heat_number)
    VALUES (v_site_id, v_lot_label, 'material', NULLIF(btrim(p_lot_number), ''))
    ON CONFLICT (site_id, lot_number) DO UPDATE SET kind = EXCLUDED.kind
    RETURNING id INTO trace_lot_id;

    INSERT INTO fac_mfg_inv.stock_lot_trace (
      stock_lot_id,
      organization_id,
      site_id,
      trace_lot_id
    )
    VALUES (stock_lot_id, p_organization_id, v_site_id, trace_lot_id)
    ON CONFLICT (stock_lot_id) DO UPDATE
    SET trace_lot_id = EXCLUDED.trace_lot_id;

    PERFORM fac_audit.sp_append(
      v_site_id,
      'lot',
      trace_lot_id,
      'inv.stock.receive',
      p_user_id,
      'Receive to stock with trace lot',
      NULL,
      jsonb_build_object(
        'receipt_id', receipt_id,
        'stock_lot_id', stock_lot_id,
        'po_line_id', p_po_line_id
      )
    );
  END IF;

  RETURN;
END;
$$;

CREATE OR REPLACE FUNCTION fac_mfg_inv.sp_issue_to_work_order(
  p_organization_id integer,
  p_user_id integer,
  p_work_order_id integer,
  p_stock_lot_id integer,
  p_qty numeric,
  OUT stock_move_id bigint,
  OUT qty_on_hand numeric,
  OUT genealogy_link_id integer
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_mfg_inv, inv, fac_trace, fac_prod, fac_eng, fac_audit, portal, pg_temp
AS $$
DECLARE
  v_site_id integer;
  v_output_lot_id integer;
  v_trace_lot_id integer;
BEGIN
  IF p_user_id IS NULL THEN
    PERFORM portal.fn_semantic_raise('GS401', 'user required');
  END IF;

  SELECT wo.site_id, wo.output_lot_id
  INTO v_site_id, v_output_lot_id
  FROM fac_prod.work_orders wo
  WHERE wo.id = p_work_order_id;

  IF v_site_id IS NULL OR NOT fac_eng.fn_user_can_access_site(p_user_id, v_site_id) THEN
    PERFORM portal.fn_semantic_raise('GS403', 'work order scope denied');
  END IF;

  SELECT i.stock_move_id, i.qty_on_hand
  INTO stock_move_id, qty_on_hand
  FROM inv.sp_stock_issue_stub(
    p_organization_id,
    p_user_id,
    p_stock_lot_id,
    p_qty,
    'work_order',
    p_work_order_id::text
  ) AS i;

  genealogy_link_id := NULL;
  SELECT t.trace_lot_id INTO v_trace_lot_id
  FROM fac_mfg_inv.stock_lot_trace t
  WHERE t.stock_lot_id = p_stock_lot_id;

  IF v_trace_lot_id IS NOT NULL AND v_output_lot_id IS NOT NULL THEN
    PERFORM set_config('goliath.mfg.user_id', p_user_id::text, true);
    INSERT INTO fac_trace.lot_links (parent_lot_id, child_lot_id, link_kind)
    VALUES (v_trace_lot_id, v_output_lot_id, 'consume')
    ON CONFLICT (parent_lot_id, child_lot_id, link_kind) DO NOTHING
    RETURNING id INTO genealogy_link_id;

    PERFORM fac_audit.sp_append(
      v_site_id,
      'work_order',
      p_work_order_id,
      'inv.stock.issue',
      p_user_id,
      'Issue material to work order',
      NULL,
      jsonb_build_object(
        'stock_lot_id', p_stock_lot_id,
        'trace_lot_id', v_trace_lot_id,
        'output_lot_id', v_output_lot_id,
        'genealogy_link_id', genealogy_link_id
      )
    );
  END IF;

  RETURN;
END;
$$;

CREATE OR REPLACE FUNCTION fac_mfg_inv.sp_issue_with_genealogy(
  p_organization_id integer,
  p_user_id integer,
  p_stock_lot_id integer,
  p_qty numeric,
  p_ref_type text,
  p_ref_id text,
  OUT stock_move_id bigint,
  OUT qty_on_hand numeric,
  OUT genealogy_link_id integer
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = fac_mfg_inv, inv, portal, pg_temp
AS $$
BEGIN
  IF p_ref_type = 'work_order' THEN
    SELECT g.stock_move_id, g.qty_on_hand, g.genealogy_link_id
    INTO stock_move_id, qty_on_hand, genealogy_link_id
    FROM fac_mfg_inv.sp_issue_to_work_order(
      p_organization_id,
      p_user_id,
      p_ref_id::integer,
      p_stock_lot_id,
      p_qty
    ) AS g;
    RETURN;
  END IF;

  SELECT i.stock_move_id, i.qty_on_hand
  INTO stock_move_id, qty_on_hand
  FROM inv.sp_stock_issue_stub(
    p_organization_id,
    p_user_id,
    p_stock_lot_id,
    p_qty,
    p_ref_type,
    p_ref_id
  ) AS i;
  genealogy_link_id := NULL;
END;
$$;
