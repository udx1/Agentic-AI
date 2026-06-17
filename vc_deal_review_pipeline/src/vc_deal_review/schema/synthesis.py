# src/vc_deal_review/schema/synthesis.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SynthesisReport(BaseModel):
    escalation_required: bool = Field(
        description="True if any upstream agent breaches institutional hazard thresholds."
    )
    triggered_reasons: List[str] = Field(
        default=[],
        description="List of specific policy or metric violations that triggered escalation."
    )
    routing_destination: str = Field(
        description="Target UI state destination: 'HUMAN_REVIEW' or 'COMPLETE'."
    )
    executive_summary_draft: str = Field(
        description="AI-generated raw high-density thesis statement synthesizing all agent results."
    )
    suggested_recommendation: str = Field(
        description="Preliminary deal stance: 'PROCEED', 'CONDITIONAL_PROCEED', or 'REJECT'."
    )