"""Validated scanner configuration."""

from pydantic import BaseModel, ConfigDict, Field


class ScannerConfig(BaseModel):
    """Safety and input limits for a scanner run.

    Configuration is immutable so a scan cannot silently change its settings
    halfway through processing a file.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    encoding: str = Field(default="utf-8-sig", min_length=1)
    max_file_bytes: int = Field(default=25 * 1024 * 1024, gt=0)
    max_rows: int | None = Field(default=None, gt=0)
    require_dob_context: bool = True
