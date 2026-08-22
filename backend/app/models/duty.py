"""Pydantic schemas for parsed duty statements."""

from typing import Optional

from pydantic import BaseModel


class DutyRequirement(BaseModel):
    """A single extracted duty statement from a job posting."""

    text: str
    order_index: int = 0
    category: str = "General"
    keywords: list[str] = []


class ParsedDutyStatement(BaseModel):
    """Full result of parsing a job posting's duty statement."""

    title: Optional[str] = None
    requirements: list[DutyRequirement] = []
