import json
from vc_deal_review.agents.base_agent import BaseAgent # Adjust import path to match your base agent location
from vc_deal_review.Financial.models import FinancialAnalysisReport

class FinancialEngine(BaseAgent):
    def __init__(self):
        # Initializes the underlying self.llm using your centralized config parameters
        super().__init__(temperature=0.1)
        
        # Bind the Pydantic schema for structured output streaming
        self.structured_llm = self.llm.with_structured_output(FinancialAnalysisReport)

    def analyze_financial_performance(self, deal_data: dict) -> FinancialAnalysisReport:
        """
        Runs financial performance vetting using the inherited structured LangChain framework.
        """
        system_instructions = (
            "You are an elite institutional Venture Capital Forensic CFO and L.P. Auditor. "
            "Your mandate is to run an exhaustive financial performance sanity analysis. "
            "Evaluate growth velocity vs market standards, verify cash runway mathematically, "
            "assess capital efficiency, and provide an unvarnished sanity check on forward-looking projections."
        )
        
        prompt = f"Analyze the following extracted deal profile data package:\n\n{json.dumps(deal_data, indent=2)}"

        # Invoke using LangChain's system/user message framework
        response = self.structured_llm.invoke([
            ("system", system_instructions),
            ("user", prompt)
        ])

        # LangChain automatically returns a validated Pydantic object
        return response