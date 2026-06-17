# src/vc_deal_review/agents/synthesizer_agent.py
from typing import Any, List
import json
from vc_deal_review.agents.base_agent import BaseAgent
from vc_deal_review.schema.synthesis import SynthesisReport

class SynthesizerAgent(BaseAgent):
    """
    Coordinates final multi-agent payload collation, handles conditional 
    routing based on institutional thresholds, and leverages Claude to
    synthesize multi-agent findings into high-density memo drafts.
    """
    def __init__(self):
        # Initialize BaseAgent to inherit centralized model settings and self.llm
        super().__init__(temperature=0.0)

    def evaluate_and_route(
        self, 
        compliance_report: Any, 
        financial_report: Any, 
        risk_report: Any
    ) -> SynthesisReport:
        """
        Aggregates upstream multi-agent reports, evaluates deterministic 
        escalation triggers, and invokes Claude to generate a sophisticated narrative draft.
        """
        escalation_reasons: List[str] = []

        # 1. Evaluate Deterministic Gating Rules
        if compliance_report.overall_status != "APPROVED":
            escalation_reasons.append(
                f"Compliance Mandate Violation: Overall status is '{compliance_report.overall_status}'"
            )

        if financial_report.overall_status != "APPROVED":
            escalation_reasons.append(
                f"Financial Performance Deficit: Overall status is '{financial_report.overall_status}'"
            )

        if risk_report.highest_severity_score >= 7:
            escalation_reasons.append(
                f"Critical Risk Threat: Max Flagged Severity hits {risk_report.highest_severity_score}/10"
            )
        
        if risk_report.calculated_runway_months < 12.0:
            escalation_reasons.append(
                f"Capital Runway Alert: Verified operational runway is low ({risk_report.calculated_runway_months:.1f} Months)"
            )

        # 2. Assign Routing Pathway Block
        escalation_required = len(escalation_reasons) > 0
        routing_destination = "HUMAN_REVIEW" if escalation_required else "COMPLETE"

        # 3. Formulate Preliminary Deal Stance
        if compliance_report.overall_status == "BLOCKED" or risk_report.highest_severity_score >= 9:
            suggested_rec = "REJECT"
        elif escalation_required:
            suggested_rec = "CONDITIONAL_PROCEED"
        else:
            suggested_rec = "PROCEED"

        # 4. Invoke Claude via self.llm to Synthesize a High-Density Executive Narrative
        summary_draft = self._generate_llm_executive_thesis(
            compliance_report=compliance_report,
            financial_report=financial_report,
            risk_report=risk_report,
            suggested_rec=suggested_rec
        )

        return SynthesisReport(
            escalation_required=escalation_required,
            triggered_reasons=escalation_reasons,
            routing_destination=routing_destination,
            executive_summary_draft=summary_draft,
            suggested_recommendation=suggested_rec
        )

    def _generate_llm_executive_thesis(
        self, 
        compliance_report: Any, 
        financial_report: Any, 
        risk_report: Any, 
        suggested_rec: str
    ) -> str:
        """
        Leverages Claude to synthesize raw agent parameters into a professional, 
        clinical, high-density venture capital thesis statement.
        """
        # Format a highly structured data payload context for the LLM
        context_payload = {
            "preliminary_recommendation": suggested_rec,
            "compliance_findings": [f"{f.rule_name}: {f.status} ({f.details})" for f in compliance_report.findings],
            "financial_findings": [f"{f.rule_name}: {f.status} ({f.details})" for f in financial_report.findings],
            "financial_sanity_audit": financial_report.projections_sanity_check,
            "risk_findings": [f"{f.rule_name}: {f.status} ({f.details})" for f in risk_report.findings],
            "calculated_runway_months": risk_report.calculated_runway_months,
            "max_flagged_severity": risk_report.highest_severity_score
        }

        prompt = (
            "You are a Chief Investment Officer synthesizing specialized multi-agent diligence feeds "
            "into a high-density, institutional executive memo draft.\n\n"
            "Review the raw multi-agent findings data below:\n"
            f"{json.dumps(context_payload, indent=2)}\n\n"
            "Generate a crisp, multi-paragraph Investment Thesis and Executive Summary. "
            "Adhere to these strict guidelines:\n"
            "- Tone must be clinical, precise, and completely devoid of generic corporate fluff or promotional language.\n"
            "- Explicitly contrast operational strengths against any critical failure flags or structural friction points.\n"
            "- Incorporate raw data markers directly (e.g., specify exact severity scores, runway timelines, or model anomalies).\n"
            "- Conclude with a clear perspective on the viability of the current deal package based on the facts provided.\n"
            "Output your text directly without introductory conversational fillers."
        )

        try:
            # Execute the synchronous prompt string call directly against self.llm
            response = self.llm.invoke(prompt)
            return str(response.content).strip()
        except Exception as e:
            # Safe operational fallback if connection or model exceptions occur
            return (
                f"System Fallback Executive Thesis [Stance: {suggested_rec}]: "
                f"Compliance status verified as '{compliance_report.overall_status}'. "
                f"Financial evaluations tracked as '{financial_report.overall_status}'. "
                f"Risk models indicate an operational cash runway of {risk_report.calculated_runway_months:.1f} months "
                f"with a maximum individual category risk exposure ceiling of {risk_report.highest_severity_score}/10."
            )