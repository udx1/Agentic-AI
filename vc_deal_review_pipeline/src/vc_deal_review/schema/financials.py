from pydantic import BaseModel, Field
from typing import List, Optional
from vc_deal_review.schema.report import ReportResult


class FinancialAnalysisReport(BaseModel):
    company_name: str = Field(description="Name of the startup target entity evaluated")
    overall_status: str = Field(description="Aggregated status flag: APPROVED, REVIEW_REQUIRED, or BLOCKED")
    passed_count: int = Field(description="Total count of financial metrics that graded as a PASS")
    warning_count: int = Field(description="Total count of financial metrics that graded as a WARNING")
    failed_count: int = Field(description="Total count of financial metrics that graded as a FAIL")
    
    # Mirroring the exact name 'findings' and type used by ComplianceReport
    findings: List[ReportResult] = Field(description="Detailed breakdown of structured financial health criteria rule metrics")
    
    projections_sanity_check: str = Field(description="High-level narrative critique of the forward-looking financial projections model")