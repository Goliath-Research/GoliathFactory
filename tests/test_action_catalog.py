"""ActionSpec catalog tests."""

from __future__ import annotations

from goliath_app.actions.spec import ActionExposure, ActionLevel

from goliath_factory.actions.catalog import ACTIONS


def test_phase1_domain_actions_typed() -> None:
    for spec in ACTIONS:
        assert spec.level == ActionLevel.DOMAIN
        assert spec.input_model.model_json_schema()
        assert spec.output_model.model_json_schema()
        assert spec.resolved_exposure == ActionExposure.RBAC
        assert spec.required_permission


def test_work_order_release_metadata() -> None:
    spec = next(a for a in ACTIONS if a.action_name == "mfg.work_order.release")
    assert spec.capability == "mfg.prod"
    assert spec.entity_code == "work_order"


def test_traveler_sign_off_metadata() -> None:
    spec = next(a for a in ACTIONS if a.action_name == "mfg.traveler_step.sign_off")
    assert spec.capability == "mfg.prod"
    assert spec.entity_code == "traveler_step"
