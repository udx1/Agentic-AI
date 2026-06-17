from pydantic import BaseModel, Field
from typing import List
from vc_deal_review.schema.report import ReportResult


class ComplianceReport(BaseModel):
    company_name: str
    overall_status: str = Field(..., description="Overall posture: APPROVED, REVIEW_REQUIRED, or BLOCKED.")
    passed_count: int = 0
    warning_count: int = 0
    failed_count: int = 0
    findings: List[ReportResult] = Field(default_factory=list)