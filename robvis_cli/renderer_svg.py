"""
Pure Python Zero-Dependency Publication-Grade SVG Rendering Engine for Cochrane Risk of Bias Plots.
Generates:
1. Traffic Light Matrices (Per-study domain judgments)
2. Weighted / Unweighted Summary Bar Charts (Domain risk proportions)
"""

import html
from typing import Dict, List, Optional
from .models import Judgment, MetaAssessment


def _escape(text: str) -> str:
    return html.escape(str(text), quote=True)


def render_traffic_light_svg(
    meta: MetaAssessment,
    title: str = "Risk of Bias Assessment",
    circle_radius: int = 14,
    cell_width: int = 44,
    row_height: int = 36,
    show_symbols: bool = True,
    show_tooltips: bool = True,
) -> str:
    """
    Renders publication-ready Traffic Light matrix SVG.
    """
    num_studies = len(meta.assessments)
    num_domains = len(meta.domains)
    include_overall = meta.include_overall

    # Dynamic layout calculations
    max_study_len = max([len(a.study_id) for a in meta.assessments] + [10])
    label_col_width = max(180, min(360, max_study_len * 9 + 30))
    matrix_cols = num_domains + (1 if include_overall else 0)
    matrix_width = matrix_cols * cell_width
    total_width = label_col_width + matrix_width + 40

    header_height = 80
    matrix_height = num_studies * row_height
    legend_height = 50 + (num_domains * 22) + 60
    total_height = header_height + matrix_height + legend_height + 40

    svg_parts = []
    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_width} {total_height}" '
        f'width="{total_width}" height="{total_height}" style="background-color:#ffffff; font-family:-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif;">'
    )
    
    # Embedded Styles
    svg_parts.append("""
    <style>
      .title { font-size: 16px; font-weight: 700; fill: #1a1a1a; text-anchor: middle; }
      .header-label { font-size: 12px; font-weight: 600; fill: #333333; text-anchor: middle; }
      .study-label { font-size: 12px; font-weight: 500; fill: #222222; }
      .symbol { font-size: 14px; font-weight: 900; fill: #ffffff; text-anchor: middle; dominant-baseline: central; font-family: monospace, sans-serif; }
      .legend-title { font-size: 13px; font-weight: 700; fill: #222222; }
      .legend-item { font-size: 11.5px; font-weight: 400; fill: #333333; }
      .grid-line { stroke: #eaeaea; stroke-width: 1; }
      .traffic-circle { transition: transform 0.2s; cursor: pointer; }
      .traffic-circle:hover { stroke: #222222; stroke-width: 2; }
    </style>
    """)

    # Main Title
    if title:
        svg_parts.append(f'<text x="{total_width/2:.1f}" y="32" class="title">{_escape(title)}</text>')

    # Column Headers (D1, D2, ..., Overall)
    y_header = header_height - 15
    for i, (key, _) in enumerate(meta.domains):
        x_center = label_col_width + (i * cell_width) + (cell_width / 2)
        svg_parts.append(f'<text x="{x_center:.1f}" y="{y_header}" class="header-label">{_escape(key)}</text>')

    if include_overall:
        x_center = label_col_width + (num_domains * cell_width) + (cell_width / 2)
        svg_parts.append(f'<text x="{x_center:.1f}" y="{y_header}" class="header-label">Overall</text>')

    # Grid & Rows
    y_start = header_height
    for row_idx, assessment in enumerate(meta.assessments):
        y_row = y_start + (row_idx * row_height)
        y_text = y_row + (row_height / 2) + 4
        y_circle = y_row + (row_height / 2)

        # Alternating subtle row background
        if row_idx % 2 == 1:
            svg_parts.append(
                f'<rect x="20" y="{y_row}" width="{total_width - 40}" height="{row_height}" fill="#f9fafb" />'
            )

        # Bottom row line
        svg_parts.append(
            f'<line x1="20" y1="{y_row + row_height}" x2="{total_width - 20}" y2="{y_row + row_height}" class="grid-line" />'
        )

        # Study Name
        study_display = assessment.study_id
        if assessment.year:
            study_display += f" ({assessment.year})"
        svg_parts.append(
            f'<text x="24" y="{y_text:.1f}" class="study-label">{_escape(study_display)}</text>'
        )

        # Domain Circles
        for col_idx, (dom_key, dom_title) in enumerate(meta.domains):
            judgment = assessment.judgments.get(dom_key, Judgment.NO_INFO)
            x_circle = label_col_width + (col_idx * cell_width) + (cell_width / 2)

            tooltip_content = f"{_escape(assessment.study_id)} | {_escape(dom_key)}: {_escape(dom_title)} -> {judgment.value}"
            
            circle_svg = (
                f'<circle cx="{x_circle:.1f}" cy="{y_circle:.1f}" r="{circle_radius}" '
                f'fill="{judgment.color_hex}" stroke="#ffffff" stroke-width="1.5" class="traffic-circle">'
            )
            if show_tooltips:
                circle_svg += f'<title>{tooltip_content}</title>'
            circle_svg += '</circle>'
            svg_parts.append(circle_svg)

            if show_symbols and judgment.symbol != " ":
                svg_parts.append(
                    f'<text x="{x_circle:.1f}" y="{y_circle:.1f}" class="symbol" pointer-events="none">{judgment.symbol}</text>'
                )

        # Overall Circle
        if include_overall:
            overall_j = assessment.overall
            x_circle = label_col_width + (num_domains * cell_width) + (cell_width / 2)
            tooltip_content = f"{_escape(assessment.study_id)} | Overall Risk -> {overall_j.value}"

            circle_svg = (
                f'<circle cx="{x_circle:.1f}" cy="{y_circle:.1f}" r="{circle_radius}" '
                f'fill="{overall_j.color_hex}" stroke="#ffffff" stroke-width="1.5" class="traffic-circle">'
            )
            if show_tooltips:
                circle_svg += f'<title>{tooltip_content}</title>'
            circle_svg += '</circle>'
            svg_parts.append(circle_svg)

            if show_symbols and overall_j.symbol != " ":
                svg_parts.append(
                    f'<text x="{x_circle:.1f}" y="{y_circle:.1f}" class="symbol" pointer-events="none">{overall_j.symbol}</text>'
                )

    # Domain Legend & Color Key
    y_legend_start = header_height + matrix_height + 25
    svg_parts.append(f'<line x1="20" y1="{y_legend_start}" x2="{total_width - 20}" y2="{y_legend_start}" stroke="#cccccc" stroke-width="1.5" />')
    
    # Judgments Key
    y_key = y_legend_start + 26
    svg_parts.append(f'<text x="24" y="{y_key}" class="legend-title">Judgments:</text>')
    
    key_items = [
        (Judgment.LOW, "Low risk"),
        (Judgment.SOME_CONCERNS, "Some concerns"),
        (Judgment.HIGH, "High risk"),
    ]
    # Include Critical if present in data or ROBINS-I
    has_crit = any(
        a.overall == Judgment.CRITICAL or any(j == Judgment.CRITICAL for j in a.judgments.values())
        for a in meta.assessments
    )
    if has_crit or meta.tool_type == "ROBINS_I":
        key_items.append((Judgment.CRITICAL, "Critical risk"))
    key_items.append((Judgment.NO_INFO, "No info"))

    x_cursor = 110
    for j_enum, j_label in key_items:
        svg_parts.append(
            f'<circle cx="{x_cursor}" cy="{y_key - 4}" r="8" fill="{j_enum.color_hex}" stroke="#ffffff" stroke-width="1"/>'
        )
        if show_symbols and j_enum.symbol != " ":
            svg_parts.append(
                f'<text x="{x_cursor}" y="{y_key - 4}" class="symbol" style="font-size:9px;" pointer-events="none">{j_enum.symbol}</text>'
            )
        svg_parts.append(
            f'<text x="{x_cursor + 14}" y="{y_key}" class="legend-item">{_escape(j_label)}</text>'
        )
        x_cursor += len(j_label) * 8 + 40

    # Domain Glossary
    y_glossary = y_key + 28
    svg_parts.append(f'<text x="24" y="{y_glossary}" class="legend-title">Domains ({meta.tool_type.value}):</text>')
    
    for i, (key, title_text) in enumerate(meta.domains):
        y_dom = y_glossary + 20 + (i * 20)
        svg_parts.append(
            f'<text x="28" y="{y_dom}" class="legend-item"><tspan font-weight="600">{_escape(key)}:</tspan> {_escape(title_text)}</text>'
        )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def render_summary_bar_svg(
    meta: MetaAssessment,
    title: str = "Risk of Bias Summary by Domain",
    weighted: bool = False,
    bar_height: int = 28,
    bar_gap: int = 16,
    chart_width: int = 500,
) -> str:
    """
    Renders publication-ready Summary Bar Chart SVG (percentage stacked bars per domain).
    """
    domains_to_plot = [(k, t) for k, t in meta.domains]
    if meta.include_overall:
        domains_to_plot.append(("Overall", "Overall Risk of Bias"))

    num_bars = len(domains_to_plot)
    max_label_len = max([len(t) for _, t in domains_to_plot] + [15])
    label_width = max(240, min(380, max_label_len * 7 + 30))
    total_width = label_width + chart_width + 80

    header_height = 70
    plot_height = num_bars * (bar_height + bar_gap)
    legend_height = 80
    total_height = header_height + plot_height + legend_height + 30

    svg_parts = []
    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_width} {total_height}" '
        f'width="{total_width}" height="{total_height}" style="background-color:#ffffff; font-family:-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif;">'
    )

    svg_parts.append("""
    <style>
      .title { font-size: 16px; font-weight: 700; fill: #1a1a1a; text-anchor: middle; }
      .bar-label { font-size: 12px; font-weight: 500; fill: #222222; text-anchor: end; }
      .axis-label { font-size: 11px; font-weight: 400; fill: #666666; text-anchor: middle; }
      .bar-text { font-size: 11px; font-weight: 700; fill: #ffffff; text-anchor: middle; dominant-baseline: central; }
      .legend-title { font-size: 12.5px; font-weight: 700; fill: #222222; }
      .legend-item { font-size: 11.5px; font-weight: 400; fill: #333333; }
      .axis-line { stroke: #cccccc; stroke-width: 1; }
      .grid-line { stroke: #f0f0f0; stroke-width: 1; stroke-dasharray: 3,3; }
    </style>
    """)

    # Main Title
    if title:
        weight_note = " (Weighted by sample weight)" if weighted else " (Unweighted count %)"
        svg_parts.append(f'<text x="{total_width/2:.1f}" y="32" class="title">{_escape(title + weight_note)}</text>')

    # Axis Grid Lines (0%, 25%, 50%, 75%, 100%)
    chart_x_start = label_width + 20
    for pct in [0, 25, 50, 75, 100]:
        x_pct = chart_x_start + (pct / 100.0) * chart_width
        svg_parts.append(
            f'<line x1="{x_pct:.1f}" y1="{header_height - 10}" x2="{x_pct:.1f}" y2="{header_height + plot_height}" class="grid-line" />'
        )
        svg_parts.append(
            f'<text x="{x_pct:.1f}" y="{header_height + plot_height + 18}" class="axis-label">{pct}%</text>'
        )

    # Base Axis Line
    svg_parts.append(
        f'<line x1="{chart_x_start}" y1="{header_height + plot_height + 4}" x2="{chart_x_start + chart_width}" y2="{header_height + plot_height + 4}" class="axis-line" />'
    )

    # Categories to compute in stack order: Low -> Some concerns -> High -> Critical -> No Info
    judgment_order = [
        Judgment.LOW,
        Judgment.SOME_CONCERNS,
        Judgment.HIGH,
        Judgment.CRITICAL,
        Judgment.NO_INFO,
    ]

    total_weight = sum(a.weight if weighted else 1.0 for a in meta.assessments)
    if total_weight <= 0:
        total_weight = 1.0

    for i, (d_key, d_title) in enumerate(domains_to_plot):
        y_bar = header_height + i * (bar_height + bar_gap)
        y_text = y_bar + (bar_height / 2) + 4

        # Compute counts/weights
        scores: Dict[Judgment, float] = {j: 0.0 for j in judgment_order}
        for assessment in meta.assessments:
            w = assessment.weight if weighted else 1.0
            if d_key == "Overall":
                j_val = assessment.overall
            else:
                j_val = assessment.judgments.get(d_key, Judgment.NO_INFO)
            scores[j_val] += w

        # Draw Label
        display_label = f"{d_key}: {d_title}" if d_key != "Overall" else "Overall Bias"
        svg_parts.append(
            f'<text x="{chart_x_start - 12}" y="{y_text:.1f}" class="bar-label">{_escape(display_label)}</text>'
        )

        # Draw Stacked Bar Segments
        curr_x = chart_x_start
        for j_val in judgment_order:
            frac = scores[j_val] / total_weight
            seg_width = frac * chart_width
            if seg_width > 0.001:
                pct_str = f"{frac * 100:.0f}%"
                svg_parts.append(
                    f'<rect x="{curr_x:.1f}" y="{y_bar}" width="{seg_width:.1f}" height="{bar_height}" '
                    f'fill="{j_val.color_hex}" rx="2">'
                    f'<title>{_escape(display_label)} - {j_val.value}: {frac*100:.1f}% ({scores[j_val]:.1f})</title>'
                    f'</rect>'
                )
                # Show percentage text if segment is wide enough
                if seg_width >= 28:
                    svg_parts.append(
                        f'<text x="{curr_x + seg_width/2:.1f}" y="{y_bar + bar_height/2:.1f}" class="bar-text">{pct_str}</text>'
                    )
                curr_x += seg_width

    # Legend
    y_legend = header_height + plot_height + 45
    svg_parts.append(
        f'<text x="{total_width/2 - 190:.1f}" y="{y_legend}" class="legend-title">Risk of bias judgments:</text>'
    )

    legend_keys = [
        (Judgment.LOW, "Low risk"),
        (Judgment.SOME_CONCERNS, "Some concerns"),
        (Judgment.HIGH, "High risk"),
    ]
    if any(a.overall == Judgment.CRITICAL for a in meta.assessments) or meta.tool_type == "ROBINS_I":
        legend_keys.append((Judgment.CRITICAL, "Critical risk"))
    legend_keys.append((Judgment.NO_INFO, "No information"))

    x_leg_cursor = total_width/2 - 50
    for j_enum, label in legend_keys:
        svg_parts.append(
            f'<rect x="{x_leg_cursor}" y="{y_legend - 12}" width="14" height="14" fill="{j_enum.color_hex}" rx="2"/>'
        )
        svg_parts.append(
            f'<text x="{x_leg_cursor + 20}" y="{y_legend}" class="legend-item">{_escape(label)}</text>'
        )
        x_leg_cursor += len(label) * 7.5 + 32

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)
