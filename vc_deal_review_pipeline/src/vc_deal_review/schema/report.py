from pydantic import BaseModel, Field
from typing import List

class ReportResult(BaseModel):
    rule_name: str = Field(..., description="The name of the screening rule evaluated.")
    status: str = Field(..., description="PASS, WARNING, or FAIL.")
    extracted_value: str = Field(..., description="The actual value found in the source documents.")
    threshold_applied: str = Field(..., description="The criteria baseline applied.")
    details: str = Field(..., description="Detailed context explaining the flag or pass reason.")
