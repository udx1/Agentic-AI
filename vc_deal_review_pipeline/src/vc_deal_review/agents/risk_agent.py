# src/vc_deal_review/agents/risk_agent.py
import json
from typing import Annotated, Sequence
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
# 1. Import MemorySaver for state checkpointing/caching
from langgraph.checkpoint.memory import MemorySaver 

from vc_deal_review.agents.base_agent import BaseAgent
from vc_deal_review.schema.risk import RiskQuantifierReport
from vc_deal_review.utils.math_tools import calculate_runway_months, calculate_arr_multiple

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

class RiskAgent(BaseAgent):
    def __init__(self):
        super().__init__(temperature=0.0)
        
        self.tools = [calculate_runway_months, calculate_arr_multiple]
        self.tool_node = ToolNode(self.tools)
        self.tool_bound_llm = self.llm.bind_tools(self.tools)
        self.structured_llm = self.llm.with_structured_output(RiskQuantifierReport)
        
        workflow = StateGraph(AgentState)
        workflow.add_node("reason", self.reason_node)
        workflow.add_node("action", self.tool_node)
        
        workflow.add_edge(START, "reason")
        workflow.add_conditional_edges(
            "reason",
            self.should_continue,
            {"continue": "action", "end": END}
        )
        workflow.add_edge("action", "reason")
        
        # 2. Instantiate the in-memory checkpointer
        self.memory = MemorySaver()
        
        # 3. Compile the graph WITH the checkpointer attached
        self.graph = workflow.compile(checkpointer=self.memory)

    def reason_node(self, state: AgentState) -> dict:
        response = self.tool_bound_llm.invoke(state["messages"])
        return {"messages": [response]}

    def should_continue(self, state: AgentState) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        return "end"


    # --- External Execution Point ---
    def assess_deal_risk(self, deal_data: dict, user_id: str) -> RiskQuantifierReport:
        """Main method called by dashboard.py to run the ReAct loop under a unique user thread session."""
        
        company_name = deal_data.get("metadata", {}).get("company_name", "Unknown Entity")
        
        # Clean the strings to make a bulletproof, unique composite cache key
        safe_company = company_name.lower().replace(" ", "_")
        safe_user = user_id.lower().replace(" ", "_")
        
        # COMPOSITE THREAD ID: Keeps User A and User B completely sandboxed
        thread_id = f"user_{safe_user}_deal_{safe_company}"
        
        # Define the execution configuration thread
        config = {"configurable": {"thread_id": thread_id}}
        
        # Look up if this exact user + deal combo already ran
        existing_state = self.graph.get_state(config)
        
        if existing_state and existing_state.values.get("messages"):
            # Cache Hit for this specific user/deal combo!
            final_messages = existing_state.values["messages"]
        else:
            # Cache Miss: Run the ReAct loop safely sandboxed from other users
            system_instructions = ( """
                You are an elite institutional Venture Capital Risk Officer specializing in 
                late-seed and Series A tech startups. Your mandate is to produce a precise, 
                evidence-based operational risk assessment of the provided investment proposal.

                ═══════════════════════════════════════════
                TOOL USE — NON-NEGOTIABLE RULES
                ═══════════════════════════════════════════
                You have access to two calculation tools. You MUST use them — never estimate 
                or manually compute these values.

                1. `calculate_runway_months`
                → Use: cash_on_hand ÷ monthly_burn_rate
                → Trigger: Always. Extract exact values from the deal profile.
                → Flag: Runway < 18 months = WARNING. Runway < 12 months = CRITICAL.

                2. `calculate_arr_multiple`
                → Use: pre_money_valuation ÷ ARR
                → Trigger: Always. Cross-reference valuation against current ARR.
                → Flag: Multiple > 20x for early-stage = WARNING. > 40x = CRITICAL.

                ═══════════════════════════════════════════
                RISK VECTORS — EVALUATE ALL FOUR
                ═══════════════════════════════════════════
                Assess and assign a severity score (1–10) for each category. 
                A score of 1 is negligible risk, 10 is deal-breaking exposure.

                1. VALUATION RISK
                Evaluate whether the startup's price tag reflects its current 
                performance reality.
                - Use calculate_arr_multiple tool output as your primary signal
                - Flag outsized multiples misaligned with the company's growth stage
                - Assess whether the valuation leaves room for a realistic subsequent 
                    funding round

                2. RUNWAY & BURN RISK
                Uncover structural timing traps hidden in the financials.
                - Use calculate_runway_months tool output as your primary signal
                - Flag discrepancies between the founder's stated runway and the 
                    mathematical reality
                - Assess burn acceleration trends against revenue growth trajectory

                3. STRUCTURAL & TERMS RISK
                Shift focus from numbers to legal protections in the term sheet.
                - Evaluate liquidation preference multiples and participation structures
                - Flag aggressive clauses that disproportionately disadvantage early 
                    investors or founders upon exit
                - Assess voting control structures and exclusivity period risks

                4. MARKET & EXECUTION RISK
                Combine qualitative pitch signals with structural financial timelines.
                - Assess realistic probability of hitting milestones before cash runs out
                - Flag high burn rates paired with slow sales cycles
                - Evaluate hiring velocity projections against available runway

                ═══════════════════════════════════════════
                REACT REASONING METHODOLOGY
                ═══════════════════════════════════════════
                Follow this strict loop for every assessment:

                Thought  → Identify what metric or data point you need to evaluate
                Action   → Call the required tool with exact values from the deal profile
                Observation → Analyse the tool output carefully before drawing conclusions
                Conclusion → Assign severity score with explicit justification

                Never skip the Action step for runway and ARR multiple calculations.
                Never assign a severity score without referencing specific data points 
                from the deal profile.

                ═══════════════════════════════════════════
                OUTPUT FORMAT — STRICTLY ENFORCE
                ═══════════════════════════════════════════
                You MUST return a single JSON object that strictly maps to this schema.
                Do not add extra fields. Do not omit required fields.

                {
                "company_name": "string — exact legal name of the startup from the deal profile",
                
                "overall_status": "string — one of: APPROVED | REVIEW_REQUIRED | BLOCKED
                                    APPROVED        → No findings scored >= 7, zero FAIL grades
                                    REVIEW_REQUIRED → One or more WARNING grades, no FAIL grades
                                    BLOCKED         → One or more FAIL grades OR any score >= 8",

                "passed_count":  "int — count of findings graded PASS",
                "warning_count": "int — count of findings graded WARNING",
                "failed_count":  "int — count of findings graded FAIL",

                "calculated_runway_months": "float — exact output from calculate_runway_months tool. 
                                            Never estimate. Tool call is mandatory.",

                "highest_severity_score": "int (1-10) — the single highest severity score 
                                            across all four risk vector findings",

                "findings": [
                    {
                    "criterion":    "string — risk vector name (e.g. Valuation Risk)",
                    "status":       "string — PASS | WARNING | FAIL",
                    "severity":     "int (1-10) — risk intensity score for this vector",
                    "detail":       "string — concise, data-backed justification referencing 
                                    specific numbers from the deal profile"
                    }
                ]
                }

                ═══════════════════════════════════════════
                GRADING RULES — APPLY TO EVERY FINDING
                ═══════════════════════════════════════════
                Severity Score → Status Mapping:
                1-4   → PASS
                5-7   → WARNING  
                8-10  → FAIL

                Overall Status Derivation:
                ANY finding graded FAIL          → overall_status = "BLOCKED"
                ANY finding graded WARNING       → overall_status = "REVIEW_REQUIRED"
                ALL findings graded PASS         → overall_status = "APPROVED"

                Count Derivation:
                passed_count  = number of findings where status == "PASS"
                warning_count = number of findings where status == "WARNING"
                failed_count  = number of findings where status == "FAIL"
                (passed_count + warning_count + failed_count must always equal 4)

                highest_severity_score = max(severity) across all four findings
                """
            )

            user_prompt = """
                Conduct a full operational risk assessment on the following investment proposal.

                DEAL PROFILE:
                {json.dumps(deal_data, indent=2)}

                INSTRUCTIONS:
                1. Begin with a Thought identifying which metrics require tool execution
                2. Call calculate_runway_months and calculate_arr_multiple using exact 
                values from the deal profile above
                3. Evaluate all four risk vectors using tool outputs and deal data
                4. Grade each finding as PASS (1-4), WARNING (5-7), or FAIL (8-10)
                5. Derive overall_status, counts, and highest_severity_score per grading rules
                6. Return output strictly matching the RiskQuantifierReport JSON schema —
                four findings, no extra fields, no omissions

                Do not estimate. Do not skip tool calls. Every score must reference 
                specific numbers from the deal profile.
                """
            
            initial_messages = [
                SystemMessage(content=system_instructions),
                HumanMessage(content=user_prompt)
            ]
            
            final_state = self.graph.invoke({"messages": initial_messages}, config=config)
            final_messages = final_state["messages"]

        # --- Structured Handoff ---
        history_summary = []
        for msg in final_messages:
            if msg.type in ["ai", "tool"]:
                history_summary.append(f"[{msg.type.upper()}]: {msg.content}")

        synthesis_prompt = (
            f"Review the full audit history and tool outcomes below, and structure the final report "
            f"exactly according to the required RiskQuantifierReport schema.\n\n"
            f"Execution History:\n" + "\n".join(history_summary)
        )
        
        final_input = [
            SystemMessage(content="Format the audited matrix cleanly into structural schemas."),
            HumanMessage(content=synthesis_prompt)
        ]
        
        report = self.structured_llm.invoke(final_input)
        report.company_name = company_name
        
        return report