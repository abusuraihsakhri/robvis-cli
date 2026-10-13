"""
Parser for Cochrane Risk of Bias CSV files.
Supports automated tool detection, alias matching, auto-overall computation, and weights.
"""

import csv
import io
import math
import os
from typing import Dict, List, Optional, Tuple, Union
from .models import (
    Judgment,
    MetaAssessment,
    StudyAssessment,
    ToolType,
    ROB2_DOMAINS,
    ROBINS_I_DOMAINS,
    QUADAS_2_DOMAINS,
)


def _compute_default_overall(judgments: Dict[str, Judgment]) -> Judgment:
    """
    Computes Cochrane default overall algorithm:
    - High if ANY domain is High or Critical
    - Some concerns if ANY domain is Some concerns and none are High/Critical
    - Low if ALL domains are Low
    """
    values = list(judgments.values())
    if any(j == Judgment.CRITICAL for j in values):
        return Judgment.CRITICAL
    if any(j == Judgment.SERIOUS for j in values):
        return Judgment.SERIOUS
    if any(j == Judgment.HIGH for j in values):
        return Judgment.HIGH
    if any(j == Judgment.NO_INFO for j in values):
        return Judgment.NO_INFO
    if any(j == Judgment.MODERATE for j in values):
        return Judgment.MODERATE
    if any(j == Judgment.SOME_CONCERNS for j in values):
        return Judgment.SOME_CONCERNS
    if values and all(j == Judgment.LOW for j in values):
        return Judgment.LOW
    return Judgment.NO_INFO


def parse_rob_csv(
    file_or_path: Union[str, io.StringIO],
    tool_type: Optional[ToolType] = None,
) -> MetaAssessment:
    """
    Parse a Risk of Bias CSV file.
    
    Expected columns:
    - Study (or 'Study ID', 'Author', 'Trial', 'Name')
    - D1, D2, D3, ... (or domain names)
    - Overall (optional; calculated if missing)
    - Weight (optional; float representing relative study weight)
    - Subgroup (optional)
    """
    if isinstance(file_or_path, io.StringIO):
        content = file_or_path.getvalue()
    elif isinstance(file_or_path, (str, os.PathLike)):
        source = os.fspath(file_or_path)
        if isinstance(file_or_path, os.PathLike) or ("\n" not in source and "," not in source and "\r" not in source):
            with open(source, mode="r", encoding="utf-8-sig") as f:
                content = f.read()
        else:
            content = source
    else:
        raise TypeError("Expected CSV text, a file path, or io.StringIO")
    content = content.lstrip("\ufeff")

    reader = csv.reader(io.StringIO(content))
    rows = [r for r in reader if any(cell.strip() for cell in r)]
    if not rows:
        raise ValueError("CSV input is empty.")

    header = [h.strip() for h in rows[0]]
    if any(not name for name in header):
        raise ValueError("CSV column headers must not be empty.")
    if len({name.casefold() for name in header}) != len(header):
        raise ValueError("CSV column headers must be unique.")
    if len(header) < 2:
        raise ValueError(f"Invalid header with fewer than 2 columns: {header}")

    # Map column roles
    study_col_idx: Optional[int] = None
    overall_col_idx: Optional[int] = None
    weight_col_idx: Optional[int] = None
    subgroup_col_idx: Optional[int] = None
    domain_cols: List[Tuple[int, str]] = []  # (col_idx, domain_key_or_name)

    study_aliases = {"study", "study_id", "study id", "author", "trial", "name", "paper", "id"}
    overall_aliases = {"overall", "overall judgment", "overall_bias", "overall risk", "summary"}
    weight_aliases = {"weight", "sample_size", "n", "sample size", "participants"}
    subgroup_aliases = {"subgroup", "group", "stratum", "category"}

    for idx, col_name in enumerate(header):
        normalized = col_name.strip().lower()
        if normalized in study_aliases and study_col_idx is None:
            study_col_idx = idx
        elif normalized in overall_aliases and overall_col_idx is None:
            overall_col_idx = idx
        elif normalized in weight_aliases and weight_col_idx is None:
            weight_col_idx = idx
        elif normalized in subgroup_aliases and subgroup_col_idx is None:
            subgroup_col_idx = idx
        else:
            domain_cols.append((idx, col_name.strip()))

    # If study column wasn't explicitly matched by name, assume column 0
    if study_col_idx is None:
        study_col_idx = 0
        domain_cols = [(idx, name) for idx, name in domain_cols if idx != 0]

    if not domain_cols:
        raise ValueError("No risk of bias domain columns found in CSV header.")
    if len(rows) < 2:
        raise ValueError("CSV must contain at least one study assessment.")

    # Determine tool type and domain titles
    num_domains = len(domain_cols)
    if tool_type is None:
        if num_domains == 5:
            tool_type = ToolType.ROB2
        elif num_domains == 7:
            tool_type = ToolType.ROBINS_I
        elif num_domains == 4:
            tool_type = ToolType.QUADAS_2
        else:
            tool_type = ToolType.CUSTOM

    domains_catalog: List[Tuple[str, str]] = []
    if tool_type == ToolType.ROB2 and num_domains == 5:
        domains_catalog = list(ROB2_DOMAINS)
    elif tool_type == ToolType.ROBINS_I and num_domains == 7:
        domains_catalog = list(ROBINS_I_DOMAINS)
    elif tool_type == ToolType.QUADAS_2 and num_domains == 4:
        domains_catalog = list(QUADAS_2_DOMAINS)
    else:
        for idx, name in domain_cols:
            key = f"D{idx}" if not name.upper().startswith("D") else name.upper()
            domains_catalog.append((key, name))

    # Parse rows
    assessments: List[StudyAssessment] = []
    for line_num, row in enumerate(rows[1:], start=2):
        if len(row) != len(header):
            raise ValueError(f"Line {line_num}: expected {len(header)} columns, got {len(row)}.")
        
        study_id = row[study_col_idx].strip() if study_col_idx < len(row) else f"Study {line_num-1}"
        if not study_id:
            study_id = f"Study {line_num-1}"

        judgments: Dict[str, Judgment] = {}
        for (col_idx, _), (dom_key, _) in zip(domain_cols, domains_catalog):
            cell_val = row[col_idx].strip() if col_idx < len(row) else ""
            try:
                if tool_type == ToolType.ROBINS_I:
                    normalized = cell_val.strip().lower()
                    if normalized in ("moderate", "m"):
                        j = Judgment.MODERATE
                    elif normalized in ("serious",):
                        j = Judgment.SERIOUS
                    elif normalized in ("some concerns", "high", "sc", "h"):
                        raise ValueError(f"'{cell_val}' is not a ROBINS-I judgment; use Moderate or Serious")
                    else:
                        j = Judgment.from_str(cell_val)
                else:
                    j = Judgment.from_str(cell_val)
            except ValueError as e:
                raise ValueError(f"Line {line_num} ('{study_id}'), column '{header[col_idx]}': {e}")
            judgments[dom_key] = j

        # Overall
        if overall_col_idx is not None and overall_col_idx < len(row) and row[overall_col_idx].strip():
            try:
                overall_j = Judgment.from_str(row[overall_col_idx].strip())
            except ValueError as e:
                raise ValueError(f"Line {line_num} ('{study_id}'), Overall: {e}")
            if tool_type == ToolType.ROBINS_I:
                if row[overall_col_idx].strip().lower() in ("moderate", "m"):
                    overall_j = Judgment.MODERATE
                elif row[overall_col_idx].strip().lower() == "serious":
                    overall_j = Judgment.SERIOUS
                elif overall_j in (Judgment.SOME_CONCERNS, Judgment.HIGH):
                    raise ValueError(f"Line {line_num} ('{study_id}'): invalid ROBINS-I Overall judgment")
        else:
            overall_j = _compute_default_overall(judgments)

        # Weight
        weight = 1.0
        if weight_col_idx is not None:
            w_str = row[weight_col_idx].strip()
            try:
                weight = float(w_str)
            except ValueError:
                raise ValueError(f"Line {line_num} ('{study_id}'): invalid Weight '{w_str}'")
            if not math.isfinite(weight) or weight <= 0:
                raise ValueError(f"Line {line_num} ('{study_id}'): Weight must be positive and finite")

        # Subgroup
        subgroup = None
        if subgroup_col_idx is not None and subgroup_col_idx < len(row):
            s_val = row[subgroup_col_idx].strip()
            if s_val:
                subgroup = s_val

        assessments.append(
            StudyAssessment(
                study_id=study_id,
                judgments=judgments,
                overall=overall_j,
                weight=weight,
                subgroup=subgroup,
            )
        )

    return MetaAssessment(
        tool_type=tool_type,
        domains=domains_catalog,
        assessments=assessments,
        # QUADAS-2 does not prescribe an aggregate overall judgment.
        include_overall=(overall_col_idx is not None or tool_type != ToolType.QUADAS_2),
    )
