from pydantic import BaseModel, Field
from typing import List

# SYNTHESIZER OUTPUT SCHEMA (Matches the "Synthesizer Structured Output" block)
class SynthesisRoutingPayload(BaseModel):
    escalation_needed: bool = Field(description="True if any institutional thresholds or policies are breached.")
    routing_destination: str = Field(description="Either 'HUMAN_REVIEW' or 'REPORT_GENERATION'")
    triggered_reasons: List[str] = Field(default=[], description="List of specific flags triggering the escalation state.")
    raw_evaluation_summary: str = Field(description="High-level structured data summary passing into the generator.")

# REPORT GENERATOR OUTPUT SCHEMA (Matches the "Report Generator" block)
class FinalMemoOutput(BaseModel):
    executive_summary_draft: str = Field(description="Comprehensive multi-agent synthesized memo body text.")
    closing_conditions: List[str] = Field(default=[], description="Legal/financial mitigation conditions required for closing.")