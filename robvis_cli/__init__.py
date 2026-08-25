"""
robvis-cli: Publication-Ready Cochrane Risk of Bias Visualizer (RoB 2, ROBINS-I, QUADAS-2)
Zero runtime dependencies for SVG generation.
"""

from .models import Judgment, ToolType, StudyAssessment, MetaAssessment, ROB2_DOMAINS, ROBINS_I_DOMAINS
from .parser import parse_rob_csv
from .renderer_svg import render_traffic_light_svg, render_summary_bar_svg

__version__ = "1.0.0"
__all__ = [
    "Judgment",
    "ToolType",
    "StudyAssessment",
    "MetaAssessment",
    "ROB2_DOMAINS",
    "ROBINS_I_DOMAINS",
    "parse_rob_csv",
    "render_traffic_light_svg",
    "render_summary_bar_svg",
]
