# src/vc_deal_review/agents/synthesizer_agent.py
from typing import Any, List
import json
from vc_deal_review.agents.base_agent import BaseAgent
from vc_deal_review.schema.synthesis import SynthesisRoutingPayload


class SynthesizerAgent(BaseAgent):
    """
    Coordinates final multi-agent payload collation, handles conditional 
    routing based on institutional thresholds, and outputs a structured
    routing payload mapping exception flags.
    """
    def __init__(self):
        # Setting temperature to 0.0 for strict deterministic rule evaluation
        super().__init__(temperature=0.0)
        self.structured_llm = self.llm.with_structured_output(SynthesisRoutingPayload)

    def evaluate_and_route(self, compliance: Any, financial: Any, risk: Any) -> SynthesisRoutingPayload:
        # 1. Package upstream reports into a single unified JSON context payload
        context_payload = {
            "compliance_track": {
                "overall_status": getattr(compliance, "overall_status", "UNKNOWN"),
                "findings": [f.model_dump() if hasattr(f, "model_dump") else str(f) for f in getattr(compliance, "findings", [])]
            },
            "financial_track": {
                "overall_status": getattr(financial, "overall_status", "UNKNOWN"),
                "findings": [f.model_dump() if hasattr(f, "model_dump") else str(f) for f in getattr(financial, "findings", [])],
                "projections_sanity_check": getattr(financial, "projections_sanity_check", "")
            },
            "risk_track": {
                "overall_status": getattr(risk, "overall_status", "UNKNOWN"),
                "calculated_runway_months": getattr(risk, "calculated_runway_months", None),
                "highest_severity_score": getattr(risk, "highest_severity_score", 0),
                "findings": [f.model_dump() if hasattr(f, "model_dump") else str(f) for f in getattr(risk, "findings", [])]
            }
        }

        # 2. Define the strict evaluation system boundaries
        system_instructions = """
        You are an Institutional Investment Risk Committee Synthesizer. 
        Your sole job is to ingest multi-agent diligence feeds and flag threshold exceptions.

        CRITERIA FOR ESCALATION:
        1. Compliance Status is BLOCKED or REVIEW_REQUIRED.
        2. Financial Status is BLOCKED or calculated operational runway is under 12 months.
        3. Risk Quantifier identifies any individual risk severity score >= 7/10.

        Your output must perfectly populate the SynthesisRoutingPayload schema. 
        Do not generate narrative summaries, prose, or introductions. 
        Focus entirely on calculating the logical criteria, setting 'escalation_needed', determining 'routing_destination', 
        and extracting the precise text reasons for exception flags.
        """
        
        # 3. Inject the compiled track data into the user message prompt
        user_prompt = f"""
        Please evaluate the following multi-agent intelligence payload:
        
        ```json
        {json.dumps(context_payload, indent=2)}
        ```
        """

        # 4. Invoke the structured model contract
        report = self.structured_llm.invoke([
            ("system", system_instructions),
            ("user", user_prompt)
        ])

        # 5. Inject the raw string version of the context payload into the schema object 
        # so the downstream ReportGeneratorAgent receives the full context automatically.
        if hasattr(report, "raw_evaluation_summary"):
            report.raw_evaluation_summary = json.dumps(context_payload, indent=2)

        return report