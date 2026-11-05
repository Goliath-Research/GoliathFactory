"""Statistical process control helpers (CPU-only)."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Literal, Sequence

ChartType = Literal["xbar_r", "imr"]

# A2 constants for X-bar/R charts (subgroup sizes 2–10)
_A2: dict[int, float] = {2: 1.880, 3: 1.023, 4: 0.729, 5: 0.577, 6: 0.483, 7: 0.419, 8: 0.373, 9: 0.337, 10: 0.308}
_D3: dict[int, float] = {2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.076, 8: 0.136, 9: 0.184, 10: 0.223}
_D4: dict[int, float] = {2: 3.267, 3: 2.574, 4: 2.282, 5: 2.114, 6: 2.004, 7: 1.924, 8: 1.864, 9: 1.816, 10: 1.777}


@dataclass(frozen=True)
class SpcPoint:
    point_index: int
    subgroup_label: str
    primary_value: float
    secondary_value: float | None
    center_line: float
    ucl: float
    lcl: float
    rule_violations: tuple[str, ...]


def _chunk(values: Sequence[float], size: int) -> list[list[float]]:
    if size < 1:
        raise ValueError("subgroup size must be positive")
    groups: list[list[float]] = []
    buf: list[float] = []
    for value in values:
        buf.append(value)
        if len(buf) == size:
            groups.append(buf)
            buf = []
    return groups


def compute_xbar_r(
    values: Sequence[float],
    *,
    subgroup_size: int = 5,
) -> list[SpcPoint]:
    groups = _chunk(list(values), subgroup_size)
    if not groups:
        return []
    if subgroup_size not in _A2:
        raise ValueError(f"unsupported subgroup size {subgroup_size} for X-bar/R")
    xbars = [mean(g) for g in groups]
    ranges = [max(g) - min(g) for g in groups]
    xbar_bar = mean(xbars)
    r_bar = mean(ranges)
    a2 = _A2[subgroup_size]
    d3 = _D3[subgroup_size]
    d4 = _D4[subgroup_size]
    ucl_x = xbar_bar + a2 * r_bar
    lcl_x = xbar_bar - a2 * r_bar
    ucl_r = d4 * r_bar
    lcl_r = d3 * r_bar
    we2 = _we2_flags(xbars, center=xbar_bar, ucl=ucl_x, lcl=lcl_x)
    points: list[SpcPoint] = []
    for idx, (xb, r) in enumerate(zip(xbars, ranges, strict=True), start=1):
        violations = list(
            western_electric_basic(
                primary=xb,
                secondary=r,
                center=xbar_bar,
                ucl=ucl_x,
                lcl=lcl_x,
                sec_center=r_bar,
                sec_ucl=ucl_r,
                sec_lcl=lcl_r,
            )
        )
        if we2[idx - 1]:
            violations.append("WE2")
        violations = tuple(dict.fromkeys(violations))
        points.append(
            SpcPoint(
                point_index=idx,
                subgroup_label=str(idx),
                primary_value=xb,
                secondary_value=r,
                center_line=xbar_bar,
                ucl=ucl_x,
                lcl=lcl_x,
                rule_violations=violations,
            )
        )
    return points


def compute_imr(values: Sequence[float]) -> list[SpcPoint]:
    seq = list(values)
    if len(seq) < 2:
        return []
    moving_ranges = [abs(seq[i] - seq[i - 1]) for i in range(1, len(seq))]
    i_bar = mean(seq)
    mr_bar = mean(moving_ranges)
    ucl_i = i_bar + 2.66 * mr_bar
    lcl_i = i_bar - 2.66 * mr_bar
    ucl_mr = 3.267 * mr_bar
    we2 = _we2_flags(seq, center=i_bar, ucl=ucl_i, lcl=lcl_i)
    points: list[SpcPoint] = []
    for idx, individual in enumerate(seq, start=1):
        mr = None if idx == 1 else moving_ranges[idx - 2]
        violations = list(
            western_electric_basic(
                primary=individual,
                secondary=mr,
                center=i_bar,
                ucl=ucl_i,
                lcl=lcl_i,
                sec_center=mr_bar,
                sec_ucl=ucl_mr,
                sec_lcl=0.0,
            )
        )
        if we2[idx - 1]:
            violations.append("WE2")
        violations = tuple(dict.fromkeys(violations))
        points.append(
            SpcPoint(
                point_index=idx,
                subgroup_label=str(idx),
                primary_value=individual,
                secondary_value=mr,
                center_line=i_bar,
                ucl=ucl_i,
                lcl=lcl_i,
                rule_violations=violations,
            )
        )
    return points


def _we2_flags(
    primary_values: Sequence[float],
    *,
    center: float,
    ucl: float,
    lcl: float,
) -> list[bool]:
    """Rule 2: two of three consecutive points beyond 2σ on the same side."""
    n = len(primary_values)
    if n == 0:
        return []
    sigma = (ucl - center) / 3.0 if ucl != center else 0.0
    if sigma == 0.0:
        return [False] * n
    upper2 = center + 2 * sigma
    lower2 = center - 2 * sigma
    sides: list[int] = []
    for value in primary_values:
        if value > upper2:
            sides.append(1)
        elif value < lower2:
            sides.append(-1)
        else:
            sides.append(0)
    flags = [False] * n
    for i in range(2, n):
        window = sides[i - 2 : i + 1]
        if sum(1 for s in window if s == 1) >= 2 or sum(1 for s in window if s == -1) >= 2:
            flags[i] = True
    return flags


def western_electric_basic(
    *,
    primary: float,
    secondary: float | None,
    center: float,
    ucl: float,
    lcl: float,
    sec_center: float,
    sec_ucl: float,
    sec_lcl: float,
) -> tuple[str, ...]:
    """Western Electric rules 1–4 (simplified zone-free implementation)."""
    violations: list[str] = []
    sigma = (ucl - center) / 3.0 if ucl != center else 0.0
    if sigma == 0.0:
        return tuple()
    if primary > ucl or primary < lcl:
        violations.append("WE1")
    if secondary is not None:
        if secondary > sec_ucl or secondary < sec_lcl:
            violations.append("WE_R1")
        sec_sigma = (sec_ucl - sec_center) / 3.0 if sec_ucl != sec_center else 0.0
        if sec_sigma > 0 and (secondary > sec_center + 2 * sec_sigma or secondary < sec_center - 2 * sec_sigma):
            violations.append("WE_R2")
    return tuple(dict.fromkeys(violations))


def compute_chart(
    chart_type: ChartType,
    values: Sequence[float],
    *,
    subgroup_size: int = 5,
) -> list[SpcPoint]:
    if chart_type == "xbar_r":
        return compute_xbar_r(values, subgroup_size=subgroup_size)
    if chart_type == "imr":
        return compute_imr(values)
    raise ValueError(f"unknown chart_type {chart_type!r}")
