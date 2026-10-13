"""
robvis-cli: Cochrane Risk of Bias Assessment Data Models & Enums.
Supports RoB 2, ROBINS-I, QUADAS-2, and custom bias assessment tools.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class Judgment(str, Enum):
    LOW = "Low"
    SOME_CONCERNS = "Some concerns"
    HIGH = "High"
    MODERATE = "Moderate"
    SERIOUS = "Serious"
    CRITICAL = "Critical"
    NO_INFO = "No information"

    @classmethod
    def from_str(cls, value: str) -> "Judgment":
        """Normalize free-text user judgment strings into standard Judgment enum."""
        v = value.strip().lower()
        if v in ("l", "low", "+", "green", "low risk", "low risk of bias"):
            return cls.LOW
        elif v in ("s", "sc", "some concerns", "moderate", "m", "?", "yellow", "unclear"):
            return cls.SOME_CONCERNS
        elif v in ("h", "high", "-", "red", "high risk", "high risk of bias", "serious"):
            return cls.HIGH
        elif v in ("c", "crit", "critical", "x", "purple", "critical risk"):
            return cls.CRITICAL
        elif v in ("ni", "no info", "no information", "na", "n/a", "missing", "unknown", ""):
            return cls.NO_INFO
        else:
            raise ValueError(f"Unrecognized risk of bias judgment value: '{value}'")

    @property
    def symbol(self) -> str:
        """Visual symbol for the traffic light icon."""
        if self == Judgment.LOW:
            return "+"
        elif self == Judgment.SOME_CONCERNS:
            return "?"
        elif self in (Judgment.HIGH, Judgment.SERIOUS):
            return "−"
        elif self == Judgment.MODERATE:
            return "?"
        elif self == Judgment.CRITICAL:
            return "✕"
        else:
            return " "

    @property
    def color_hex(self) -> str:
        """Standard Cochrane / McGuinness color palette."""
        if self == Judgment.LOW:
            return "#4daf4a"  # Crisp Green
        elif self in (Judgment.SOME_CONCERNS, Judgment.MODERATE):
            return "#fdbf6f"  # Crisp Ochre/Yellow
        elif self in (Judgment.HIGH, Judgment.SERIOUS):
            return "#e41a1c"  # Crisp Crimson Red
        elif self == Judgment.CRITICAL:
            return "#6a3d9a"  # Dark Purple (ROBINS-I)
        else:
            return "#cccccc"  # Neutral Light Gray


class ToolType(str, Enum):
    ROB2 = "ROB2"
    ROBINS_I = "ROBINS_I"
    QUADAS_2 = "QUADAS_2"
    CUSTOM = "CUSTOM"


# Standard domain definitions according to official Cochrane Guidelines
ROB2_DOMAINS = [
    ("D1", "Randomization process"),
    ("D2", "Deviations from intended interventions"),
    ("D3", "Missing outcome data"),
    ("D4", "Measurement of the outcome"),
    ("D5", "Selection of the reported result"),
]

ROBINS_I_DOMAINS = [
    ("D1", "Bias due to confounding"),
    ("D2", "Bias in selection of participants"),
    ("D3", "Bias in classification of interventions"),
    ("D4", "Bias due to deviations from intended interventions"),
    ("D5", "Bias due to missing data"),
    ("D6", "Bias in measurement of outcomes"),
    ("D7", "Bias in selection of the reported result"),
]

QUADAS_2_DOMAINS = [
    ("D1", "Patient selection"),
    ("D2", "Index test"),
    ("D3", "Reference standard"),
    ("D4", "Flow and timing"),
]


@dataclass
class StudyAssessment:
    study_id: str
    judgments: Dict[str, Judgment]  # domain_key -> Judgment (e.g. 'D1': Judgment.LOW)
    overall: Judgment
    weight: float = 1.0
    year: Optional[int] = None
    subgroup: Optional[str] = None


@dataclass
class MetaAssessment:
    tool_type: ToolType
    domains: List[Tuple[str, str]]  # list of (key, title)
    assessments: List[StudyAssessment]
    include_overall: bool = True

    def domain_keys(self) -> List[str]:
        return [k for k, _ in self.domains]

    def domain_title(self, key: str) -> str:
        for k, title in self.domains:
            if k == key:
                return title
        return key
