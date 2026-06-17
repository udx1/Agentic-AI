from pydantic import BaseModel, Field
from typing import List

class RuleResult(BaseModel):
    rule_name: str = Field(..., description="The name of the screening rule evaluated.")
    status: str = Field(..., description="PASS, WARNING, or FAIL.")
    extracted_value: str = Field(..., description="The actual value found in the source documents.")
    threshold_applied: str = Field(..., description="The criteria baseline applied.")
    details: str = Field(..., description="Detailed context explaining the flag or pass reason.")

class ComplianceReport(BaseModel):
    company_name: str
    overall_status: str = Field(..., description="Overall posture: APPROVED, REVIEW_REQUIRED, or BLOCKED.")
    passed_count: int = 0
    warning_count: int = 0
    failed_count: int = 0
    findings: List[RuleResult] = Field(default_factory=list)