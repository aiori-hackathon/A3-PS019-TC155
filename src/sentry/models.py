"""Safe output models. Findings intentionally have no field for raw matched text."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PIIType = Literal["EMAIL", "AADHAAR", "PAN", "DOB"]


class Finding(BaseModel):
    """One validated detection with masked evidence only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str = Field(min_length=1)
    pii_type: PIIType
    source_file: str = Field(min_length=1)
    row_number: int = Field(ge=2)
    column_name: str = Field(min_length=1)
    masked_evidence: str = Field(min_length=1)

    # Do not add a `raw_value`, `matched_text`, or equivalent field here.
