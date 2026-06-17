from vc_deal_review.Compliance.models import ComplianceReport, RuleResult

class ComplianceEngine:
    def __init__(self, target_max_ask: float = 5_000_000.0, 
                 target_max_valuation: float = 25_000_000.0,
                 min_runway_months: int = 12):
        """
        Initialize the compliance ruleset with your fund's specific thresholds.
        """
        self.target_max_ask = target_max_ask
        self.target_max_valuation = target_max_valuation
        self.min_runway_months = min_runway_months

    def evaluate_deal(self, deal_data: dict) -> ComplianceReport:
        metadata = deal_data.get("metadata", {})
        financials = deal_data.get("financials", {})
        
        company_name = metadata.get("company_name", "Unknown Entity")
        findings = []
        
        # 1. Check Size Cap Rule
        ask_amt = financials.get("ask_amount", 0.0)
        if ask_amt <= self.target_max_ask:
            findings.append(RuleResult(
                rule_name="Check Size Cap", status="PASS",
                extracted_value=f"${ask_amt:,.2f}", threshold_applied=f"≤ ${self.target_max_ask:,.2f}",
                details="The target ask amount fits comfortably within our fund's core check allotment limits."
            ))
        else:
            findings.append(RuleResult(
                rule_name="Check Size Cap", status="WARNING",
                extracted_value=f"${ask_amt:,.2f}", threshold_applied=f"≤ ${self.target_max_ask:,.2f}",
                details="Requested capital allocation exceeds our standard target cap. Requires partner override approval."
            ))

        # 2. Valuation Boundary Rule
        pre_money = financials.get("pre_money_valuation", 0.0)
        if pre_money <= self.target_max_valuation:
            findings.append(RuleResult(
                rule_name="Valuation Boundary", status="PASS",
                extracted_value=f"${pre_money:,.2f}", threshold_applied=f"≤ ${self.target_max_valuation:,.2f}",
                details="Valuation meets our fund's entry multiples parameters."
            ))
        else:
            findings.append(RuleResult(
                rule_name="Valuation Boundary", status="FAIL",
                extracted_value=f"${pre_money:,.2f}", threshold_applied=f"≤ ${self.target_max_valuation:,.2f}",
                details="The round entry pricing is above our top-line valuation parameters for this stage."
            ))

        # 3. Cash Runway Safety Margin Rule
        cash_bal = financials.get("current_cash_balance", 0.0)
        burn_rate = financials.get("monthly_burn_rate", 1.0)
        runway = (cash_bal / burn_rate) if burn_rate > 0 else 999.0
        
        if runway >= self.min_runway_months:
            findings.append(RuleResult(
                rule_name="Cash Runway Safety Margin", status="PASS",
                extracted_value=f"{runway:.1f} months", threshold_applied=f"≥ {self.min_runway_months} months",
                details="Current capital structures offer sufficient operational runway prior to the close of this round."
            ))
        else:
            findings.append(RuleResult(
                rule_name="Cash Runway Safety Margin", status="WARNING",
                extracted_value=f"{runway:.1f} months", threshold_applied=f"≥ {self.min_runway_months} months",
                details="Low existing capital balances present a structural timing risk for deal execution."
            ))

        # 4. Jurisdiction Alignment Rule
        jurisdiction = metadata.get("location", "Unknown").lower()
        if "delaware" in jurisdiction or "de" == jurisdiction.strip():
            findings.append(RuleResult(
                rule_name="Jurisdiction Alignment", status="PASS",
                extracted_value=metadata.get("location", "N/A"), threshold_applied="Delaware Corporation",
                details="Company matches institutional preferences for corporate legal frameworks."
            ))
        else:
            findings.append(RuleResult(
                rule_name="Jurisdiction Alignment", status="WARNING",
                extracted_value=metadata.get("location", "N/A"), threshold_applied="Delaware Corporation",
                details="Non-standard regional entity registration structure may complicate standard deal docs."
            ))

        # Aggregate metrics scores
        passed = sum(1 for f in findings if f.status == "PASS")
        warnings = sum(1 for f in findings if f.status == "WARNING")
        failed = sum(1 for f in findings if f.status == "FAIL")
        
        overall = "BLOCKED" if failed > 0 else ("REVIEW_REQUIRED" if warnings > 0 else "APPROVED")

        return ComplianceReport(
            company_name=company_name, overall_status=overall,
            passed_count=passed, warning_count=warnings, failed_count=failed,
            findings=findings
        )