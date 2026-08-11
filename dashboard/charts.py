"""
Server-rendered inline SVG chart helpers for the dashboard.

Charts are hand-built SVG strings rather than a JS charting library so
the dashboard has no external/CDN dependency and renders identically
whether it is opened on the machine running it or from a phone's
browser over the local network.
"""

from __future__ import annotations

from html import escape
from typing import Sequence

BAR_COLOR = "#3b82f6"
BAR_COLOR_MISSING = "#cbd5e1"

DONUT_COLOR_MAP = {
    "problem_identification": "#3b82f6",
    "experimentation": "#10b981",
    "reflection": "#f59e0b",
    "refinement": "#8b5cf6",
    "none": "#94a3b8",
}
DONUT_FALLBACK_COLOR = "#cbd5e1"


def donut_color(label: str) -> str:
    """Look up the fixed colour for an NLP category label."""
    return DONUT_COLOR_MAP.get(label, DONUT_FALLBACK_COLOR)


def format_category_label(label: str) -> str:
    """Turn a raw category key like 'problem_identification' into 'Problem Identification'."""
    return label.replace("_", " ").title()


def render_bar_chart(
    items: Sequence[tuple[str, float | None]],
    width: int = 420,
    height: int = 200,
) -> str:
    """Render a horizontal 0-1 bar chart (e.g. the four sub-scores)."""
    if not items:
        return f'<svg viewBox="0 0 {width} {height}" class="chart chart-bar"></svg>'

    label_width = 120
    value_width = 50
    chart_width = width - label_width - value_width
    row_height = height / len(items)
    parts: list[str] = []

    for index, (label, value) in enumerate(items):
        y = index * row_height + row_height * 0.28
        bar_height = row_height * 0.44

        display_value = 0.0 if value is None else max(0.0, min(1.0, value))
        bar_width = chart_width * display_value
        color = BAR_COLOR_MISSING if value is None else BAR_COLOR
        value_text = "N/A" if value is None else f"{value:.2f}"

        parts.append(
            f'<text x="0" y="{y + bar_height * 0.75:.1f}" '
            f'class="chart-label">{escape(label)}</text>'
            f'<rect x="{label_width}" y="{y:.1f}" '
            f'width="{chart_width}" height="{bar_height:.1f}" '
            f'class="chart-track" rx="3" />'
            f'<rect x="{label_width}" y="{y:.1f}" '
            f'width="{bar_width:.1f}" height="{bar_height:.1f}" '
            f'fill="{color}" rx="3" />'
            f'<text x="{label_width + chart_width + 8}" '
            f'y="{y + bar_height * 0.75:.1f}" '
            f'class="chart-value">{value_text}</text>'
        )

    return (
        f'<svg viewBox="0 0 {width} {height}" class="chart chart-bar" '
        f'role="img" aria-label="Experimentation sub-score bar chart">'
        + "".join(parts)
        + "</svg>"
    )


def render_donut_chart(
    distribution: dict[str, int],
    size: int = 220,
) -> str:
    """Render an NLP category-distribution donut chart."""
    total = sum(distribution.values())
    center = size / 2
    radius = size * 0.36
    stroke_width = size * 0.22

    if total == 0:
        return (
            f'<svg viewBox="0 0 {size} {size}" class="chart chart-donut">'
            f'<circle cx="{center}" cy="{center}" r="{radius}" '
            f'fill="none" class="chart-track" stroke-width="{stroke_width}" />'
            f'<text x="{center}" y="{center}" class="chart-center-label" '
            f'text-anchor="middle">No data</text>'
            f"</svg>"
        )

    circumference = 2 * 3.141592653589793 * radius
    active_segments = [
        (label, count) for label, count in distribution.items() if count > 0
    ]
    # A small visible gap between segments, matching a "spoked" donut look.
    gap = circumference * 0.012 if len(active_segments) > 1 else 0.0

    offset = 0.0
    segments: list[str] = []

    for label, count in active_segments:
        fraction = count / total
        raw_length = circumference * fraction
        segment_length = max(raw_length - gap, 0.0)
        color = donut_color(label)

        segments.append(
            f'<circle cx="{center}" cy="{center}" r="{radius}" '
            f'fill="none" stroke="{color}" stroke-width="{stroke_width}" '
            f'stroke-linecap="round" '
            f'stroke-dasharray="{segment_length:.2f} '
            f'{circumference - segment_length:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" '
            f'transform="rotate(-90 {center} {center})">'
            f"<title>{escape(format_category_label(label))}: {count}</title>"
            f"</circle>"
        )
        offset += raw_length

    return (
        f'<svg viewBox="0 0 {size} {size}" class="chart chart-donut" '
        f'role="img" aria-label="NLP category distribution donut chart">'
        + "".join(segments)
        + f'<text x="{center}" y="{center - size * 0.045:.1f}" '
        f'class="chart-center-value" text-anchor="middle">{total}</text>'
        + f'<text x="{center}" y="{center + size * 0.085:.1f}" '
        f'class="chart-center-caption" text-anchor="middle">Total</text>'
        + "</svg>"
    )


def render_sparkline(
    values: Sequence[int],
    width: int = 360,
    height: int = 80,
) -> str:
    """Render a weekly commit-activity sparkline (area + line)."""
    if not values:
        return (
            f'<svg viewBox="0 0 {width} {height}" class="chart chart-sparkline">'
            f'<text x="{width / 2}" y="{height / 2}" text-anchor="middle" '
            f'class="chart-center-label">No commit data</text>'
            f"</svg>"
        )

    maximum = max(values) or 1
    step = width / (len(values) - 1) if len(values) > 1 else 0
    points: list[tuple[float, float]] = []

    for index, value in enumerate(values):
        x = index * step if len(values) > 1 else width / 2
        y = height - (value / maximum) * (height * 0.8) - 6
        points.append((x, y))

    line_points = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area_points = f"0,{height} " + line_points + f" {width},{height}"

    return (
        f'<svg viewBox="0 0 {width} {height}" class="chart chart-sparkline" '
        f'role="img" aria-label="Commit activity over time">'
        f'<polygon points="{area_points}" class="sparkline-area" />'
        f'<polyline points="{line_points}" class="sparkline-line" fill="none" />'
        f"</svg>"
    )
