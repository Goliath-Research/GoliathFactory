"""Manufacturing semantic entity and request specifications (namespace ``mfg``)."""

from __future__ import annotations

from goliath_app.semantic.spec import SemanticAttributeSpec, SemanticEntitySpec, SemanticRequestSpec

from goliath_factory.semantic.models import (
    GenealogyRow,
    LotGenealogyParams,
    LotRow,
    PartRevisionRow,
    RoutingRow,
    TravelerStepByWorkOrderParams,
    TravelerStepRow,
    WorkOrderListParams,
    WorkOrderRow,
)

PART_ENTITY = SemanticEntitySpec(
    namespace="mfg",
    code="part",
    display_name="Part revision",
    description="Released part number and revision with material spec and effectivity.",
    schema_version="1",
    row_model=PartRevisionRow,
    storage_relation="fac_eng.v_part_revision",
    attributes=(
        SemanticAttributeSpec("part_revision_id", "part_revision_id", "integer", "key", ()),
        SemanticAttributeSpec(
            "organization_id",
            "organization_id",
            "integer",
            "filter",
            ("eq",),
        ),
        SemanticAttributeSpec(
            "part_number",
            "part_number",
            "string",
            "label",
            ("eq", "ilike"),
        ),
        SemanticAttributeSpec("revision", "revision", "string", "attribute", ("eq",)),
        SemanticAttributeSpec("material_spec", "material_spec", "string", "attribute", ()),
        SemanticAttributeSpec("customer", "customer", "string", "attribute", ("eq",)),
        SemanticAttributeSpec(
            "effectivity_start",
            "effectivity_start",
            "date",
            "attribute",
            ("lte", "gte"),
        ),
        SemanticAttributeSpec(
            "effectivity_end",
            "effectivity_end",
            "date",
            "attribute",
            ("lte", "gte"),
        ),
    ),
)

ROUTING_ENTITY = SemanticEntitySpec(
    namespace="mfg",
    code="routing",
    display_name="Routing",
    description="Part revision routing with ordered operations and work centers.",
    schema_version="1",
    row_model=RoutingRow,
    storage_relation="fac_eng.v_routing",
    attributes=(
        SemanticAttributeSpec("routing_id", "routing_id", "integer", "key", ()),
        SemanticAttributeSpec(
            "part_revision_id",
            "part_revision_id",
            "integer",
            "filter",
            ("eq",),
        ),
        SemanticAttributeSpec("part_number", "part_number", "string", "label", ("eq",)),
        SemanticAttributeSpec("status", "status", "string", "attribute", ("eq",)),
        SemanticAttributeSpec("seq", "seq", "integer", "attribute", ()),
        SemanticAttributeSpec("operation_code", "operation_code", "string", "attribute", ("eq",)),
        SemanticAttributeSpec("site_id", "site_id", "integer", "filter", ("eq",)),
    ),
)

WORK_ORDER_ENTITY = SemanticEntitySpec(
    namespace="mfg",
    code="work_order",
    display_name="Work order",
    description="A released or planned production order with its traveler.",
    schema_version="1",
    row_model=WorkOrderRow,
    storage_relation="fac_prod.v_work_order",
    attributes=(
        SemanticAttributeSpec("work_order_id", "work_order_id", "integer", "key", ()),
        SemanticAttributeSpec("site_id", "site_id", "integer", "filter", ("eq",)),
        SemanticAttributeSpec(
            "part_number",
            "part_number",
            "string",
            "label",
            ("eq", "ilike"),
        ),
        SemanticAttributeSpec("status", "status", "string", "attribute", ("eq", "in")),
        SemanticAttributeSpec(
            "due_date",
            "due_date",
            "date",
            "attribute",
            ("lte", "gte"),
        ),
    ),
)

TRAVELER_STEP_ENTITY = SemanticEntitySpec(
    namespace="mfg",
    code="traveler_step",
    display_name="Traveler step",
    description="Signed operation step on a work-order traveler.",
    schema_version="1",
    row_model=TravelerStepRow,
    storage_relation="fac_prod.v_traveler_step",
    attributes=(
        SemanticAttributeSpec("traveler_step_id", "traveler_step_id", "integer", "key", ()),
        SemanticAttributeSpec(
            "work_order_id",
            "work_order_id",
            "integer",
            "filter",
            ("eq",),
        ),
        SemanticAttributeSpec("seq", "seq", "integer", "attribute", ()),
        SemanticAttributeSpec("operation_code", "operation_code", "string", "attribute", ("eq",)),
        SemanticAttributeSpec("status", "status", "string", "attribute", ("eq",)),
        SemanticAttributeSpec("site_id", "site_id", "integer", "filter", ("eq",)),
    ),
)

LOT_ENTITY = SemanticEntitySpec(
    namespace="mfg",
    code="lot",
    display_name="Lot",
    description="Production or material lot with heat/cert references and genealogy links.",
    schema_version="1",
    row_model=LotRow,
    storage_relation="fac_trace.v_lot",
    attributes=(
        SemanticAttributeSpec("lot_id", "lot_id", "integer", "key", ()),
        SemanticAttributeSpec("site_id", "site_id", "integer", "filter", ("eq",)),
        SemanticAttributeSpec("lot_number", "lot_number", "string", "label", ("eq", "ilike")),
        SemanticAttributeSpec("kind", "kind", "string", "attribute", ("eq",)),
        SemanticAttributeSpec("heat_number", "heat_number", "string", "attribute", ("eq",)),
    ),
)

SEMANTIC_CATALOG: list[SemanticEntitySpec] = [
    PART_ENTITY,
    ROUTING_ENTITY,
    WORK_ORDER_ENTITY,
    TRAVELER_STEP_ENTITY,
    LOT_ENTITY,
]

SEMANTIC_REQUESTS: list[SemanticRequestSpec] = [
    SemanticRequestSpec(
        request_code="mfg.work_order.list_open",
        version="1",
        namespace="mfg",
        entity_code="work_order",
        target_kind="function",
        target_name="fac_prod.fn_semantic_work_order_list_open",
        params_model=WorkOrderListParams,
        result_row_model=WorkOrderRow,
        required_permission="mfg.work_order.read",
        max_rows=500,
    ),
    SemanticRequestSpec(
        request_code="mfg.traveler_step.by_work_order",
        version="1",
        namespace="mfg",
        entity_code="traveler_step",
        target_kind="function",
        target_name="fac_prod.fn_semantic_traveler_step_by_work_order",
        params_model=TravelerStepByWorkOrderParams,
        result_row_model=TravelerStepRow,
        required_permission="mfg.traveler.read",
        max_rows=500,
    ),
    SemanticRequestSpec(
        request_code="mfg.lot.genealogy",
        version="1",
        namespace="mfg",
        entity_code="lot",
        target_kind="function",
        target_name="fac_trace.fn_semantic_lot_genealogy",
        params_model=LotGenealogyParams,
        result_row_model=GenealogyRow,
        required_permission="mfg.trace.read",
        max_rows=500,
    ),
]
