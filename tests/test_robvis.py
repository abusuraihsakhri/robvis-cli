import io
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from robvis_cli.models import Judgment, ToolType, StudyAssessment, MetaAssessment
from robvis_cli.parser import parse_rob_csv, _compute_default_overall
from robvis_cli.renderer_svg import render_traffic_light_svg, render_summary_bar_svg
from robvis_cli.cli import main


def test_judgment_normalization():
    assert Judgment.from_str("Low") == Judgment.LOW
    assert Judgment.from_str("l") == Judgment.LOW
    assert Judgment.from_str("+") == Judgment.LOW
    assert Judgment.from_str("Some concerns") == Judgment.SOME_CONCERNS
    assert Judgment.from_str("moderate") == Judgment.SOME_CONCERNS
    assert Judgment.from_str("?") == Judgment.SOME_CONCERNS
    assert Judgment.from_str("High") == Judgment.HIGH
    assert Judgment.from_str("-") == Judgment.HIGH
    assert Judgment.from_str("serious") == Judgment.HIGH
    assert Judgment.from_str("Critical") == Judgment.CRITICAL
    assert Judgment.from_str("no info") == Judgment.NO_INFO


def test_default_overall_logic():
    # Low overall
    assert _compute_default_overall({"D1": Judgment.LOW, "D2": Judgment.LOW}) == Judgment.LOW
    # Some concerns overall
    assert _compute_default_overall({"D1": Judgment.LOW, "D2": Judgment.SOME_CONCERNS}) == Judgment.SOME_CONCERNS
    # High overall
    assert _compute_default_overall({"D1": Judgment.LOW, "D2": Judgment.HIGH}) == Judgment.HIGH
    # Critical overall
    assert _compute_default_overall({"D1": Judgment.HIGH, "D2": Judgment.CRITICAL}) == Judgment.CRITICAL


def test_parse_rob2_csv_content():
    csv_data = """Study,D1,D2,D3,D4,D5
Smith 2020,Low,Low,Low,Low,Low
Jones 2021,High,Low,Low,Some concerns,Low
Taylor 2022,Low,Some concerns,Low,Low,Low
"""
    meta = parse_rob_csv(csv_data)
    assert meta.tool_type == ToolType.ROB2
    assert len(meta.assessments) == 3
    assert meta.assessments[0].overall == Judgment.LOW
    assert meta.assessments[1].overall == Judgment.HIGH
    assert meta.assessments[2].overall == Judgment.SOME_CONCERNS


def test_render_traffic_light_svg():
    csv_data = """Study,D1,D2,D3,D4,D5
Trial A,Low,Low,Low,Low,Low
Trial B,High,Low,Low,Low,Low
"""
    meta = parse_rob_csv(csv_data)
    svg = render_traffic_light_svg(meta, title="Test RoB 2 Traffic Light")
    assert "<svg" in svg
    assert "Trial A" in svg
    assert "Trial B" in svg
    assert "Test RoB 2 Traffic Light" in svg
    assert "Randomization process" in svg


def test_render_summary_bar_svg():
    csv_data = """Study,D1,D2,D3,D4,D5,Weight
Trial 1,Low,Low,Low,Low,Low,100
Trial 2,High,High,High,High,High,100
"""
    meta = parse_rob_csv(csv_data)
    svg_unweighted = render_summary_bar_svg(meta, weighted=False)
    assert "<svg" in svg_unweighted
    assert "50%" in svg_unweighted

    svg_weighted = render_summary_bar_svg(meta, weighted=True)
    assert "<svg" in svg_weighted


def test_cli_execution(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Study,D1,D2,D3,D4,D5\nTrial 1,Low,Low,Low,Low,Low\n", encoding="utf-8")
    
    tl_out = str(tmp_path / "tl.svg")
    sum_out = str(tmp_path / "sum.svg")

    assert main(["validate", "-i", str(csv_file)]) == 0
    assert main(["traffic-light", "-i", str(csv_file), "-o", tl_out]) == 0
    assert main(["summary", "-i", str(csv_file), "-o", sum_out]) == 0
    assert (tmp_path / "tl.svg").exists()
    assert (tmp_path / "sum.svg").exists()
