from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, HttpUrl


class ContactInfo(BaseModel):
    """Contact details extracted from a website."""

    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None


class ResearchReport(BaseModel):
    """Structured research report produced by the website research agent."""

    url: str
    company_name: Optional[str] = None
    description: Optional[str] = None
    products_and_services: list[str] = []
    target_audience: Optional[str] = None
    key_differentiators: list[str] = []
    contact_info: ContactInfo = ContactInfo()
    technologies: list[str] = []
    summary: Optional[str] = None
