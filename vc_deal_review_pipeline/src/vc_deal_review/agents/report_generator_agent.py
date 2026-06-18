# src/vc_deal_review/agents/report_generator_agent.py
from typing import Any, List
import json
from vc_deal_review.agents.base_agent import BaseAgent
from vc_deal_review.schema.synthesis import FinalMemoOutput


class ReportGeneratorAgent(BaseAgent):
    """
    Acts as the final writing engine in the pipeline. Transforms structured 
    routing outputs, upstream technical feeds, and human review modifications 
    into a premium institutional Investment Committee Memo.
    """
    def __init__(self):
        # Temperature 0.3 allows the CIO persona to compose fluid, natural, 
        # and premium executive prose while strictly adhering to data bounds.
        super().__init__(temperature=0.3)
        self.structured_llm = self.llm.with_structured_output(FinalMemoOutput)

    def generate_final_memo(self, routing_payload: Any, comp: Any, fin: Any, risk: Any, human_notes: str = "") -> FinalMemoOutput:
        
        # 1. Safely extract values from upstream objects to build clean text representations
        compliance_summary = getattr(comp, "overall_status", "UNKNOWN")
        financial_summary = getattr(fin, "overall_status", "UNKNOWN")
        risk_summary = f"Status: {getattr(risk, 'overall_status', 'UNKNOWN')}, Runway: {getattr(risk, 'calculated_runway_months', 'N/A')} months, Max Risk Score: {getattr(risk, 'highest_severity_score', 'N/A')}/10"

        # 2. Define the strategic CIO system persona and background parameters
        system_instructions = f"""
        You are a Chief Investment Officer synthesizing specialized multi-agent diligence feeds 
        and structural gatekeeper payloads into a high-density, institutional executive memo draft.

        Review the Upstream Structured Exception Payload:
        {getattr(routing_payload, "raw_evaluation_summary", "No raw summary provided.")}

        Review the Technical Appendices:
        - Compliance Track Status: {compliance_summary}
        - Financial Performance Track Status: {financial_summary}
        - Risk Quantification Matrix Status: {risk_summary}
        - Human Committee Override/Reviewer Notes (If Any): {human_notes if human_notes else "None provided."}

        Task:
        Generate a premium, multi-paragraph Investment Thesis and Executive Summary for the FinalMemoOutput schema. 
        Ensure every single flagged warning, exception, or risk highlighted in the technical benchmarks above is 
        explicitly accounted for and paired with a matching strategic corporate mitigation narrative.
        
        Tone:
        Authoritative, professional, deeply analytical, and balanced.
        """
        
        # 3. Formulate the explicit invocation prompt
        user_prompt = f"""
        Please compile the comprehensive text layout for the final memorandum. 
        Incorporate any human override instructions directly into your mitigation strategy formatting:
        
        Reviewer Notes: {human_notes if human_notes else "No specific overrides provided. Standard synthesis rules apply."}
        """

        # 4. Invoke the structured model pipeline (returns a Pydantic object directly)
        final_memo_report = self.structured_llm.invoke([
            ("system", system_instructions),
            ("user", user_prompt)
        ])
        
        return final_memo_report