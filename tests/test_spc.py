"""SPC chart computation tests."""

from __future__ import annotations

from goliath_factory.spc import compute_chart, compute_xbar_r


def test_xbar_r_produces_control_limits() -> None:
    values = [10.0, 10.2, 9.8, 10.1, 9.9] * 4
    points = compute_xbar_r(values, subgroup_size=5)
    assert len(points) == 4
    assert points[0].ucl > points[0].center_line > points[0].lcl


def test_imr_chart_runs() -> None:
    values = [1.0, 1.1, 0.95, 1.05, 1.0, 1.02]
    points = compute_chart("imr", values)
    assert len(points) == len(values)


def test_we_rule_flags_outlier() -> None:
    values = [10.0, 10.1, 10.0, 10.2, 9.9] * 3 + [12.0, 12.1, 11.9, 12.2, 11.8]
    points = compute_xbar_r(values, subgroup_size=5)
    assert any("WE1" in p.rule_violations for p in points)
