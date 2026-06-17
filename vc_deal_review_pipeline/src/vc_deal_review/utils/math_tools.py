from langchain_core.tools import tool

@tool
def calculate_runway_months(current_cash_balance: float, monthly_burn_rate: float) -> float:
    """
    Calculates the exact operational runway of a company in months.
    Use this tool whenever you need to verify or cross-check a company's claimed runway timeline.
    
    Args:
        current_cash_balance: The current total cash the company has in the bank.
        monthly_burn_rate: The average net cash outflow per month.
    
    Returns:
        float: Exact remaining runway in months. Returns 999.0 if burn rate is 0 or negative.
    """
    if monthly_burn_rate <= 0:
        return 999.0  # Safe fallback for infinite runway / cash-flow positive tracking
    
    return round(current_cash_balance / monthly_burn_rate, 2)


@tool
def calculate_arr_multiple(pre_money_valuation: float, annual_recurring_revenue: float) -> float:
    """
    Calculates the Pre-Money Valuation-to-ARR multiple.
    Use this tool to evaluate Valuation Risk and flags if a startup is overpriced relative to revenue velocity.
    
    Args:
        pre_money_valuation: The pre-money valuation stated in the deal terms.
        annual_recurring_revenue: The current Annual Recurring Revenue (ARR) of the startup.
        
    Returns:
        float: The valuation multiple (e.g., 20.5 means valuation is 20.5x ARR). 
               Returns 0.0 if ARR is missing or zero.
    """
    if not annual_recurring_revenue or annual_recurring_revenue <= 0:
        return 0.0
    
    return round(pre_money_valuation / annual_recurring_revenue, 2)