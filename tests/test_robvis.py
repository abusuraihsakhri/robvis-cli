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
from robvis_cli.cli import main, _validate_input_file, _validate_output_path


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


def test_cli_missing_input_file(tmp_path):
    """Test that CLI returns error code for missing input file."""
    missing_file = str(tmp_path / "nonexistent.csv")
    assert main(["validate", "-i", missing_file]) == 1
    assert main(["traffic-light", "-i", missing_file, "-o", str(tmp_path / "out.svg")]) == 1
    assert main(["summary", "-i", missing_file, "-o", str(tmp_path / "out.svg")]) == 1


def test_cli_robins_i_csv(tmp_path):
    """Test ROBINS-I CSV parsing and rendering."""
    csv_data = """Study,D1,D2,D3,D4,D5,D6,D7,Overall,Weight
Armstrong 2021,Moderate,Low,Low,Moderate,Low,Low,Low,Moderate,320
Bautista 2020,Serious,Moderate,Low,Low,Low,Moderate,Low,Serious,190
"""
    csv_file = tmp_path / "robins.csv"
    csv_file.write_text(csv_data, encoding="utf-8")

    assert main(["validate", "-i", str(csv_file)]) == 0
    meta = parse_rob_csv(str(csv_file))
    assert meta.tool_type == ToolType.ROBINS_I
    assert len(meta.assessments) == 2


def test_cli_weighted_summary(tmp_path):
    """Test weighted summary bar chart generation."""
    csv_data = """Study,D1,D2,D3,D4,D5,Weight
Trial 1,Low,Low,Low,Low,Low,100
Trial 2,High,High,High,High,High,200
Trial 3,Some concerns,Low,Low,Low,Low,50
"""
    csv_file = tmp_path / "weighted.csv"
    csv_file.write_text(csv_data, encoding="utf-8")

    sum_out = str(tmp_path / "weighted_sum.svg")
    assert main(["summary", "-i", str(csv_file), "-o", sum_out, "--weighted"]) == 0
    assert (tmp_path / "weighted_sum.svg").exists()


def test_judgment_symbol_and_color():
    """Test judgment symbols and colors."""
    assert Judgment.LOW.symbol == "+"
    assert Judgment.SOME_CONCERNS.symbol == "?"
    assert Judgment.HIGH.symbol == "−"
    assert Judgment.CRITICAL.symbol == "✕"
    assert Judgment.NO_INFO.symbol == " "

    assert Judgment.LOW.color_hex == "#4daf4a"
    assert Judgment.SOME_CONCERNS.color_hex == "#fdbf6f"
    assert Judgment.HIGH.color_hex == "#e41a1c"
    assert Judgment.CRITICAL.color_hex == "#6a3d9a"
    assert Judgment.NO_INFO.color_hex == "#cccccc"


def test_parse_robins_i_csv():
    """Test ROBINS-I CSV parsing with 7 domains."""
    csv_data = """Study,D1,D2,D3,D4,D5,D6,D7
Study A,Moderate,Low,Low,Moderate,Low,Low,Low
Study B,Serious,Moderate,Low,Low,Low,Moderate,Low
"""
    meta = parse_rob_csv(csv_data)
    assert meta.tool_type == ToolType.ROBINS_I
    assert len(meta.domains) == 7
    assert len(meta.assessments) == 2


def test_parse_quadas_2_csv():
    """Test QUADAS-2 CSV parsing with 4 domains."""
    csv_data = """Study,D1,D2,D3,D4
Test A,Low,Some concerns,Low,Low
Test B,Low,Low,High,Some concerns
"""
    meta = parse_rob_csv(csv_data)
    assert meta.tool_type == ToolType.QUADAS_2
    assert len(meta.domains) == 4
    assert len(meta.assessments) == 2


def test_parse_custom_csv():
    """Test custom CSV parsing with non-standard domain count."""
    csv_data = """Study,D1,D2
Custom A,Low,High
Custom B,Some concerns,Low
"""
    meta = parse_rob_csv(csv_data)
    assert meta.tool_type == ToolType.CUSTOM
    assert len(meta.domains) == 2


def test_empty_csv_raises_error():
    """Test that empty CSV content raises ValueError."""
    with pytest.raises(ValueError, match="CSV input is empty"):
        parse_rob_csv("\n\n")


def test_invalid_judgment_raises_error():
    """Test that invalid judgment value raises ValueError."""
    csv_data = """Study,D1,D2,D3,D4,D5
Study A,InvalidValue,Low,Low,Low,Low
"""
    with pytest.raises(ValueError, match="Unrecognized risk of bias judgment"):
        parse_rob_csv(csv_data)


def test_sample_csv_command(tmp_path):
    """Test sample-csv command generates valid CSV."""
    sample_out = str(tmp_path / "sample_rob2.csv")
    assert main(["sample-csv", "--tool", "rob2", "-o", sample_out]) == 0
    assert (tmp_path / "sample_rob2.csv").exists()

    # Verify the generated CSV is valid
    meta = parse_rob_csv(sample_out)
    assert meta.tool_type == ToolType.ROB2
    assert len(meta.assessments) > 0


def test_traffic_light_svg_with_critical(tmp_path):
    """Test traffic light SVG includes Critical judgment for ROBINS-I."""
    csv_data = """Study,D1,D2,D3,D4,D5,D6,D7
Study A,Critical,Serious,Moderate,Low,Serious,Low,Low
Study B,Low,Low,Low,Low,Low,Low,Low
"""
    meta = parse_rob_csv(csv_data)
    svg = render_traffic_light_svg(meta, title="Test Critical")
    assert "Critical risk" in svg
    assert "#6a3d9a" in svg  # Critical color


# =============================================================================
# Validation Function Tests
# =============================================================================

def test_validate_input_file_exists(tmp_path):
    """Test _validate_input_file with existing file."""
    test_file = tmp_path / "test.csv"
    test_file.write_text("test content", encoding="utf-8")
    result = _validate_input_file(str(test_file))
    assert result == str(test_file.resolve())


def test_validate_input_file_not_found(tmp_path):
    """Test _validate_input_file raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError, match="Input file not found"):
        _validate_input_file(str(tmp_path / "nonexistent.csv"))


def test_validate_input_file_is_directory(tmp_path):
    """Test _validate_input_file raises ValueError for directory."""
    with pytest.raises(ValueError, match="Input path is not a file"):
        _validate_input_file(str(tmp_path))


def test_validate_output_path_valid(tmp_path):
    """Test _validate_output_path with valid output path."""
    result = _validate_output_path(str(tmp_path / "output.svg"))
    assert result == str((tmp_path / "output.svg").resolve())


def test_validate_output_path_missing_directory(tmp_path):
    """Test _validate_output_path raises FileNotFoundError for missing directory."""
    missing_dir = tmp_path / "nonexistent_dir"
    with pytest.raises(FileNotFoundError, match="Output directory does not exist"):
        _validate_output_path(str(missing_dir / "output.svg"))
