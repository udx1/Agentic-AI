# src/vc_deal_review/schema/risk.py
from pydantic import BaseModel, Field
from typing import List
from vc_deal_review.schema.report import ReportResult

class RiskQuantifierReport(BaseModel):
    company_name: str = Field(description="Name of the startup target entity evaluated")
    overall_status: str = Field(description="Aggregated status flag: APPROVED, REVIEW_REQUIRED, or BLOCKED")
    passed_count: int = Field(description="Total count of risk vectors that graded as a PASS")
    warning_count: int = Field(description="Total count of risk vectors that graded as a WARNING")
    failed_count: int = Field(description="Total count of risk vectors that graded as a FAIL")
    
    # Mirroring the exact name 'findings' and type used by ComplianceReport & FinancialAnalysisReport
    findings: List[ReportResult] = Field(description="Detailed breakdown of structured risk criteria rule metrics")
    
    # Specialized top-level risk metadata fields for your Synthesizer and metrics components
    calculated_runway_months: float = Field(
        ..., description="The precise operational runway verified mathematically by the agent's math tools"
    )
    highest_severity_score: int = Field(
        ..., ge=1, le=10, description="The top risk intensity score flagged during the audit on a scale of 1-10"
    )