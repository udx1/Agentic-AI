def calculate_runway(current_cash: float, monthly_burn: float) -> float:
    """
    Calculates the number of months of runway remaining.
    Formula: Current Cash / Monthly Burn
    """
    if monthly_burn <= 0:
        return float('inf')  # Infinite runway if burn is zero or negative (profitable)
    
    return round(current_cash / monthly_burn, 2)

def calculate_post_money_valuation(ask_amount: float, pre_money_valuation: float) -> float:
    """
    Calculates the post-money valuation.
    Formula: Ask + Pre-Money Valuation
    """
    return ask_amount + pre_money_valuation

def assess_risk_level(runway_months: float) -> str:
    """
    Returns a risk categorization based on remaining runway.
    """
    if runway_months < 6:
        return "CRITICAL: Immediate insolvency risk."
    elif runway_months < 12:
        return "HIGH: Raising capital is urgent."
    elif runway_months < 18:
        return "MODERATE: Standard runway for growth."
    else:
        return "LOW: Healthy capital reserves."