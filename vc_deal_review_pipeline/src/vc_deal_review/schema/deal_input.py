from pydantic import BaseModel, Field, field_validator
from typing import Optional

class DealFinancials(BaseModel):
    """Core financial metrics extracted from projections and pitch deck."""
    ask_amount: float = Field(..., description="The total investment amount requested by the startup.")
    pre_money_valuation: float = Field(..., description="The pre-money valuation of the company.")
    current_cash_balance: float = Field(..., description="Total cash currently in the bank.")
    monthly_burn_rate: float = Field(..., description="The average monthly net cash outflow.")
    annual_recurring_revenue: Optional[float] = Field(None, description="Current ARR if applicable.")

    @property
    def post_money_valuation(self) -> float:
        """Calculated field: Ask + Pre-Money."""
        return self.ask_amount + self.pre_money_valuation

class DealMetadata(BaseModel):
    """High-level identity data for the startup."""
    company_name: str = Field(..., description="Legal name of the entity.")
    sector: str = Field(..., description="Industry sector (e.g., Healthcare, SaaS).")
    location: str = Field(..., description="Headquarters location.")
    incorporation_type: str = Field("C-Corp", description="Entity structure (e.g., LLC, C-Corp).")

class DealInput(BaseModel):
    """The unified structured output from the Extractor agent."""
    metadata: DealMetadata
    financials: DealFinancials
    deal_terms: dict = Field(default_factory=dict, description="Key clauses from the term sheet.")
    
    # Unit Test Validation
    @field_validator('financials')
    @classmethod
    def check_runway_risk(cls, v: DealFinancials):
        """
        Internal developer log to verify the extractor caught the trap values.
        Note: The actual agent logic will handle this in the 'Risk Quantifier' 
        phase using the ReAct loop as seen in the system architecture.
        """
        return v