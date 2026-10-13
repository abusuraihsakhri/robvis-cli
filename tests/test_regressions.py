"""Regressions for scientific classification, CSV validation, and audit integrity."""
import io
import xml.etree.ElementTree as ET

import pytest

from robvis_cli.models import Judgment, ToolType
from robvis_cli.parser import parse_rob_csv
from robvis_cli.renderer_svg import render_summary_bar_svg, render_traffic_light_svg
from robvis_cli.cli import main
from agents.base import AuditTrail


ROBINS = """Study,D1,D2,D3,D4,D5,D6,D7,Overall,Weight
A,Moderate,Low,Low,Low,Low,Low,Low,Moderate,2
B,Serious,Low,Low,Low,Low,Low,Low,Serious,3
"""


def test_robins_judgments_are_not_rob2_categories():
    meta = parse_rob_csv(ROBINS)
    assert meta.tool_type == ToolType.ROBINS_I
    assert meta.assessments[0].judgments["D1"] == Judgment.MODERATE
    assert meta.assessments[1].overall == Judgment.SERIOUS
    traffic = render_traffic_light_svg(meta)
    summary = render_summary_bar_svg(meta, weighted=True)
    for svg in (traffic, summary):
        ET.fromstring(svg)
        assert "Moderate risk" in svg and "Serious risk" in svg
        assert "Some concerns" not in svg


def test_robins_without_overall_uses_tool_specific_rules():
    csv = "Study,D1,D2,D3,D4,D5,D6,D7\nA,Moderate,Low,Low,Low,Low,Low,Low\n"
    meta = parse_rob_csv(csv)
    assert meta.assessments[0].overall == Judgment.MODERATE


@pytest.mark.parametrize("weight", ["", "-1", "0", "NaN", "inf", "bogus"])
def test_weight_rejects_nonpositive_or_nonfinite_values(weight):
    csv = f"Study,D1,D2,Weight\nA,Low,Low,{weight}\n"
    with pytest.raises(ValueError, match="Weight"):
        parse_rob_csv(csv)


def test_invalid_overall_cannot_silently_be_recomputed():
    with pytest.raises(ValueError, match="Overall"):
        parse_rob_csv("Study,D1,D2,Overall\nA,Low,High,invalid\n")


def test_malformed_row_and_empty_studies_are_rejected():
    with pytest.raises(ValueError, match="expected 3 columns"):
        parse_rob_csv("Study,D1,D2\nA,Low\n")
    with pytest.raises(ValueError, match="at least one study"):
        parse_rob_csv("Study,D1,D2\n")


def test_quadas2_no_implicit_overall():
    csv = "Study,D1,D2,D3,D4\nA,Low,Low,Low,Low\n"
    meta = parse_rob_csv(csv)
    assert meta.tool_type == ToolType.QUADAS_2
    assert meta.include_overall is False
    assert "Overall Bias" not in render_summary_bar_svg(meta)


def test_svg_escapes_user_supplied_labels():
    csv = "Study,D1,D2\n<trial>,Low,High\n"
    svg = render_traffic_light_svg(parse_rob_csv(csv), title="<script>alert(1)</script>")
    ET.fromstring(svg)
    assert "<script>" not in svg and "<trial>" not in svg


def test_cli_does_not_overwrite_input(tmp_path):
    path = tmp_path / "assessment.csv"
    original = "Study,D1,D2\nA,Low,High\n"
    path.write_text(original, encoding="utf-8")
    assert main(["summary", "-i", str(path), "-o", str(path)]) == 1
    assert path.read_text(encoding="utf-8") == original


def test_audit_integrity_recomputes_signatures():
    trail = AuditTrail(secret_key="a-unique-test-key-long-enough")
    trail.log("actor", "test", "event", {"safe": True})
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "attacker"
    assert not trail.verify_integrity()


def test_audit_trail_getter_is_defensive():
    trail = AuditTrail(secret_key="a-unique-test-key-long-enough")
    trail.log("actor", "test", "event", {"safe": True})
    trail.get_trail()[0]["actor"] = "attacker"
    assert trail.verify_integrity()
