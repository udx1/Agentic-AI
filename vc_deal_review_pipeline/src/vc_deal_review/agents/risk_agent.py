from vc_deal_review.agents.base_agent import BaseAgent
from vc_deal_review.compliance import ComplianceEngine

class RiskAgent(BaseAgent):
    def __init__(self):
        # Ensure BaseAgent is initialized if it requires arguments
        super().__init__()
        self.engine = ComplianceEngine()
        
    def assess_deal_risk(self, deal_data: dict):
        try:
            return self.engine.evaluate_deal(deal_data)
        except Exception as e:
            # This print will show in your terminal, preventing the silent crash
            print(f"DEBUG: Compliance Engine Error: {e}")
            raise e