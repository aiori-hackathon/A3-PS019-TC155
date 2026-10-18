"""Validated purpose/retention metadata mappings for source columns.

Metadata is treated as user-provided governance context. This module does not
judge whether a stated purpose or retention period is legally sufficient.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MetadataConfigError(ValueError):
    """Safe-to-display metadata configuration error without uploaded values."""


class ColumnMetadata(BaseModel):
    """One metadata entry for a source column; contains no source cell values."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    column_name: str = Field(min_length=1, max_length=256)
    business_purpose: str = Field(min_length=1, max_length=1024)
    retention_period: str = Field(min_length=1, max_length=256)
    data_owner: str = Field(default="", max_length=256)
    review_status: Literal["draft", "reviewed"] = "draft"

    @field_validator("column_name", "business_purpose", "retention_period", "data_owner", mode="before")
    @classmethod
    def strip_strings(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("column_name", "business_purpose", "retention_period")
    @classmethod
    def require_nonblank(cls, value: str) -> str:
        if not value:
            raise ValueError("value must not be blank")
        return value

    @field_validator("review_status", mode="before")
    @classmethod
    def normalize_review_status(cls, value: object) -> object:
        if value is None or (isinstance(value, str) and not value.strip()):
            return "draft"
        return value.strip().casefold() if isinstance(value, str) else value


def normalize_column_name(column_name: str) -> str:
    """Return a case-insensitive lookup key for a column name."""
    return column_name.strip().casefold()


def parse_column_metadata_csv(text: str) -> dict[str, ColumnMetadata]:
    """Parse CSV metadata text into a case-insensitive map keyed by column name.

    Required headers: column_name, business_purpose, retention_period.
    Optional headers: data_owner, review_status.
    """
    if not isinstance(text, str) or not text.strip():
        raise MetadataConfigError("Metadata CSV is empty.")
    if len(text.encode("utf-8")) > 1_000_000:
        raise MetadataConfigError("Metadata CSV exceeds the 1 MB limit.")

    required = {"column_name", "business_purpose", "retention_period"}
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        headers = reader.fieldnames or []
        if not required.issubset(set(headers)):
            raise MetadataConfigError(
                "Metadata CSV must include column_name, business_purpose, and retention_period headers."
            )

        result: dict[str, ColumnMetadata] = {}
        row_count = 0
        for row in reader:
            if not row or not any((value or "").strip() for value in row.values() if isinstance(value, str)):
                continue
            row_count += 1
            try:
                item = ColumnMetadata.model_validate(
                    {
                        "column_name": row.get("column_name"),
                        "business_purpose": row.get("business_purpose"),
                        "retention_period": row.get("retention_period"),
                        "data_owner": row.get("data_owner") or "",
                        "review_status": row.get("review_status") or "draft",
                    }
                )
            except Exception:
                # Do not expose the validation exception: it may contain the supplied value.
                raise MetadataConfigError("Metadata CSV contains an invalid field or row.") from None

            key = normalize_column_name(item.column_name)
            if key in result:
                raise MetadataConfigError("Metadata CSV contains duplicate column mappings.")
            result[key] = item

        if row_count == 0:
            raise MetadataConfigError("Metadata CSV has headers but no metadata rows.")
        return result
    except MetadataConfigError:
        raise
    except (csv.Error, UnicodeError, TypeError):
        raise MetadataConfigError("Metadata CSV could not be parsed. Check its structure and encoding.") from None


def load_column_metadata_csv(path: str | Path) -> dict[str, ColumnMetadata]:
    """Load a metadata CSV from disk without including supplied content in errors."""
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            content = handle.read(1_000_001)
        if len(content) > 1_000_000:
            raise MetadataConfigError("Metadata CSV exceeds the 1 MB limit.")
        return parse_column_metadata_csv(content)
    except MetadataConfigError:
        raise
    except (OSError, UnicodeError):
        raise MetadataConfigError("Metadata CSV could not be read. Check the file and encoding.") from None


def metadata_for_column(
    column_name: str,
    metadata_map: dict[str, ColumnMetadata],
) -> ColumnMetadata | None:
    """Look up metadata using a case-insensitive exact column-name match."""
    return metadata_map.get(normalize_column_name(column_name))


def metadata_coverage_rows(
    columns: list[str],
    metadata_map: dict[str, ColumnMetadata],
) -> list[dict[str, str]]:
    """Return a display-safe coverage table for all source columns."""
    rows: list[dict[str, str]] = []
    for column in columns:
        item = metadata_for_column(column, metadata_map)
        rows.append(
            {
                "column_name": column,
                "metadata_status": (
                    "Missing mapping" if item is None else item.review_status.capitalize()
                ),
                "business_purpose": item.business_purpose if item else "",
                "retention_period": item.retention_period if item else "",
                "data_owner": item.data_owner if item else "",
            }
        )
    return rows
