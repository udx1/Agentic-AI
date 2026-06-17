# src/vc_deal_review/ui/dashboard.py
import os
import sys
from pathlib import Path

# Silence the Windows-specific Proactor asyncio connection teardown noise
if sys.platform == "win32":
    from functools import wraps
    from asyncio.proactor_events import _ProactorBasePipeTransport

    def silence_connection_lost_noise(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (ConnectionResetError, ConnectionAbortedError):
                pass  # Safely ignore harmless socket drops during client reloads
        return wrapper

    _ProactorBasePipeTransport._call_connection_lost = silence_connection_lost_noise(
        _ProactorBasePipeTransport._call_connection_lost
    )

# Force Python to recognize the 'src' root directory relative to this file
src_path = str(Path(__file__).resolve().parents[2])
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import streamlit as strl
import json
import io
from pypdf import PdfReader
from vc_deal_review.agents.extractor_agent import ExtractorAgent
from vc_deal_review.agents.compliance_agent import ComplianceAgent
from vc_deal_review.agents.financial_agent import FinancialAgent
from vc_deal_review.agents.risk_agent import RiskAgent  # <-- Included natively

strl.set_page_config(
    page_title="Venture Capital Deal Review Intelligence Pipeline",
    page_icon="💼",
    layout="wide"
)

# Setup a local cache directory
CACHE_DIR = Path("src/vc_deal_review/.cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Get a unique token for the current browser session
current_user = strl.context.headers.get("X-Forwarded-User", "local_developer")

# -------------------------------------------------------------
# GLOBAL STYLING FRAMEWORK & SPACE OPTIMIZATION
# -------------------------------------------------------------
strl.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [data-testid="stWidgetLabel"] p, .stMarkdown p {
            font-family: 'Inter', sans-serif !important;
        }
        
        div[data-testid="stMainBlockContainer"] {
            max-width: 100% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            padding-top: 1.5rem !important;
            padding-bottom: 1rem !important;
        }
        
        div[data-testid="stFileUploader"] {
            margin-bottom: -0.5rem !important;
        }
        
        /* TOP LEVEL MAIN WORKSPACE TABS */
        div[data-testid="stMainBlockContainer"] > div > div > div[data-testid="stTabs"] > div:first-child {
            background-color: #f8fafc !important; 
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            padding: 4px !important;
            margin-bottom: 0.5rem !important;
            width: 100% !important;
        }
        
        div[data-testid="stMainBlockContainer"] > div > div > div[data-testid="stTabs"] > div:first-child button {
            background-color: transparent !important;
            color: #64748b !important; 
            border: none !important;
            border-radius: 6px !important;
            padding: 0.5rem 1.5rem !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease-in-out !important;
        }
        
        div[data-testid="stMainBlockContainer"] > div > div > div[data-testid="stTabs"] > div:first-child button[aria-selected="true"] {
            background-color: #eff6ff !important; 
            color: #1e40af !important; 
        }
        
        div[data-testid="stMainBlockContainer"] > div > div > div[data-testid="stTabs"] > div:first-child div[data-baseweb="tab-highlight"] {
            display: none !important;
        }
        
        /* NESTED SUB-TABS */
        div[data-testid="stTabs"] div[data-testid="stTabs"] > div:first-child {
            background-color: transparent !important;
            border: none !important;
            margin-top: -0.5rem !important;
            margin-bottom: 0.75rem !important;
        }
        
        div[data-testid="stTabs"] div[data-testid="stTabs"] > div:first-child div[data-baseweb="tab-list"] {
            border-bottom: 1px solid #e2e8f0 !important;
            gap: 24px !important;
        }
        
        div[data-testid="stTabs"] div[data-testid="stTabs"] > div:first-child button[aria-selected="true"] {
            color: #1e40af !important;
        }

        div[data-testid="stTabs"] div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] {
            display: block !important;
            height: 2px !important; 
            background-color: #2563eb !important;
        }

        /* PREMIUM STATUS TRACKER STYLING */
        .status-tracker {
            display: flex;
            justify-content: space-between;
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1rem 1.5rem;
            margin-bottom: 1.5rem;
        }
        .status-step {
            display: flex;
            align-items: center;
            font-size: 13px;
            font-weight: 500;
            color: #94a3b8;
        }
        .status-step.active {
            color: #2563eb;
            font-weight: 600;
        }
        .status-step.complete {
            color: #059669;
        }
        .step-num {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background-color: #e2e8f0;
            color: #64748b;
            font-size: 11px;
            font-weight: 700;
            margin-right: 8px;
        }
        .active .step-num {
            background-color: #3b82f6;
            color: white;
        }
        .complete .step-num {
            background-color: #10b981;
            color: white;
        }
        .status-line {
            flex-grow: 1;
            height: 2px;
            background-color: #e2e8f0;
            margin: auto 1.5rem;
        }
        .status-line.complete {
            background-color: #10b981;
        }

        .report-finding-header {
            font-size: 14px !important;
            font-weight: 600 !important;
            color: #0f172a !important;
            margin-bottom: 4px !important;
        }
        .report-finding-details {
            font-size: 13.5px !important;
            color: #334155 !important;
            line-height: 1.5 !important;
        }
        .report-finding-meta {
            font-size: 12px !important;
            color: #64748b !important;
            font-family: monospace !important;
            margin-bottom: 1.25rem !important; 
            display: block !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

strl.markdown(
    """
    <div style="margin-bottom: 1.25rem; margin-top: -0.5rem;">
        <h1 style="margin: 0; font-size: 24px; font-weight: 700; color: #0f172a; line-height: 1.35; padding-bottom: 4px;">💼 Venture Capital Deal Review Pipeline</h1>
        <p style="margin: 4px 0 0 0; font-size: 13.5px; color: #64748b;">Automated multi-agent document profile extraction, policy compliance checking, and financial evaluation tracking framework.</p>
    </div>
    """,
    unsafe_allow_html=True
)
strl.markdown("<div style='border-bottom: 1px solid #e2e8f0; margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# SIDEBAR PANEL: INGESTION CONTROL
# -------------------------------------------------------------
with strl.sidebar:
    strl.header("📁 Ingestion Control")
    pitch_deck = strl.file_uploader("Pitch Deck (.pdf)", type=["pdf"])
    financials = strl.file_uploader("Financial Projections (.pdf)", type=["pdf"])
    term_sheet = strl.file_uploader("Term Sheet Summary (.pdf)", type=["pdf"])
    use_cache = strl.checkbox("Enable Local Extraction Cache", value=True)

    if pitch_deck and financials and term_sheet:
        trigger_analysis = strl.button("🚀 Execute Extractor Pipeline", type="primary", use_container_width=True)
    else:
        strl.button("🚀 Execute Extractor Pipeline", type="primary", use_container_width=True, disabled=True)
        trigger_analysis = False

# -------------------------------------------------------------
# PIPELINE EXECUTION & DATA CACHING
# -------------------------------------------------------------
if trigger_analysis:
    for key in ["compliance_report", "financial_report", "risk_report", "active_deal_data", "analysis_triggered", "pipeline_stage"]:
        if key in strl.session_state:
            del strl.session_state[key]

    cache_file = CACHE_DIR / "nexushealth_ai_cached_extraction.json"
    deal_dict = None

    if use_cache and cache_file.exists():
        with open(cache_file, "r") as f:
            deal_dict = json.load(f)
        strl.session_state["extraction_cached_flag"] = True

    if deal_dict is None:
        strl.session_state["extraction_cached_flag"] = False
        with strl.spinner("Parsing deal package PDFs and extracting schemas via core engine..."):
            try:
                def extract_text_from_pdf(uploaded_file) -> str:
                    pdf_stream = io.BytesIO(uploaded_file.read())
                    reader = PdfReader(pdf_stream)
                    extracted_pages = [page.extract_text() for page in reader.pages if page.extract_text()]
                    uploaded_file.seek(0)
                    return f"\n--- PAGE BREAK ---\n".join(extracted_pages)

                raw_text_package = (
                    f"=== SOURCE FILE: Pitch Deck ===\n{extract_text_from_pdf(pitch_deck)}\n\n"
                    f"=== SOURCE FILE: Financial Projections ===\n{extract_text_from_pdf(financials)}\n\n"
                    f"=== SOURCE FILE: Term Sheet ===\n{extract_text_from_pdf(term_sheet)}"
                )
                
                extractor = ExtractorAgent()
                deal_data = extractor.extract_deal_data(raw_text_package)
                deal_dict = deal_data.model_dump()
                
                with open(cache_file, "w") as f:
                    json.dump(deal_dict, f, indent=4)
                
            except Exception as e:
                strl.error(f"An error occurred during extraction processing: {str(e)}")
                deal_dict = None

    if deal_dict is not None:
        strl.session_state["active_deal_data"] = deal_dict

# -------------------------------------------------------------
# BACKGROUND MULTI-AGENT STATE MACHINE EXECUTION LOOP
# -------------------------------------------------------------
# This intercepts the execution request top-level before horizontal grid layouts render
if "pipeline_stage" in strl.session_state and strl.session_state["pipeline_stage"] != "COMPLETE":
    current_stage = strl.session_state["pipeline_stage"]
    deal_dict = strl.session_state["active_deal_data"]
    fin_cache_file = CACHE_DIR / "nexushealth_ai_cached_financials.json"
    risk_cache_file = CACHE_DIR / "nexushealth_ai_cached_risk.json"

    # Define visual render helper function for the full takeover screen
    def draw_progress_screen(active_step: int, step_desc: str):
        s1_num, s1_bg, s1_txt, s1_pulse = ("✓", "#059669", "color: #059669; font-weight: 600;", "") if active_step > 1 else ("1", "#2563eb", "color: #1e3a8a; font-weight: 600;", "pulse-node")
        s2_num, s2_bg, s2_txt, s2_pulse = ("✓", "#059669", "color: #059669; font-weight: 600;", "") if active_step > 2 else (("2", "#2563eb", "color: #2563eb; font-weight: 600;", "pulse-node") if active_step == 2 else ("2", "#f1f5f9", "color: #64748b;", ""))
        s3_num, s3_bg, s3_txt, s3_pulse = ("3", "#2563eb", "color: #2563eb; font-weight: 600;", "pulse-node") if active_step == 3 else ("3", "#f1f5f9", "color: #64748b;", "")
        
        strl.html(
            f"""
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 4.5rem 2rem; text-align: center; margin: 2rem auto; max-width: 900px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05); font-family: 'Inter', sans-serif;">
                <div class="luxury-spinner"></div>
                <div style="font-size: 24px; font-weight: 700; color: #0f172a; margin-bottom: 0.75rem; letter-spacing: -0.01em;">Orchestrating Multi-Agent Intelligence Tracks</div>
                <div style="font-size: 14.5px; color: #475569; max-width: 540px; margin: 0 auto 2.5rem auto; line-height: 1.6;">
                    Currently executing backend verification pipelines: <span style="color:#2563eb; font-weight:600;">{step_desc}</span>
                </div>
                
                <div style="display: flex; justify-content: space-between; max-width: 650px; margin: 0 auto; position: relative;">
                    <div style="position: absolute; top: 15px; left: 10%; right: 10%; height: 2px; background: #e2e8f0; z-index: 1;"></div>
                    <div style="z-index: 2; text-align: center; width: 30%;">
                        <div class="{s1_pulse}" style="width: 32px; height: 32px; border-radius: 50%; background: {s1_bg}; color: white; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px auto; font-size: 12px; font-weight: 700;">{s1_num}</div>
                        <div style="font-size: 12px; {s1_txt}">Compliance Engine</div>
                    </div>
                    <div style="z-index: 2; text-align: center; width: 30%;">
                        <div class="{s2_pulse}" style="width: 32px; height: 32px; border-radius: 50%; background: {s2_bg}; color: {'white' if active_step >= 2 else '#94a3b8'}; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px auto; font-size: 12px; font-weight: 700; {'border: 2px solid #e2e8f0;' if active_step < 2 else ''}">{s2_num}</div>
                        <div style="font-size: 12px; {s2_txt}">Financial Profile</div>
                    </div>
                    <div style="z-index: 2; text-align: center; width: 30%;">
                        <div class="{s3_pulse}" style="width: 32px; height: 32px; border-radius: 50%; background: {s3_bg}; color: {'white' if active_step == 3 else '#94a3b8'}; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px auto; font-size: 12px; font-weight: 700; {'border: 2px solid #e2e8f0;' if active_step < 3 else ''}">{s3_num}</div>
                        <div style="font-size: 12px; {s3_txt}">Risk Quantification</div>
                    </div>
                </div>
            </div>
            <style>
                .luxury-spinner {{
                    width: 50px;
                    height: 50px;
                    border: 3.5px solid #f1f5f9;
                    border-top: 3.5px solid #2563eb;
                    border-radius: 50%;
                    margin: 0 auto 1.5rem auto;
                    animation: spin 1s cubic-bezier(0.55, 0.055, 0.675, 0.19) infinite;
                }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                @keyframes pulse-ring {{
                    0% {{ box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.4); }}
                    70% {{ box-shadow: 0 0 0 10px rgba(37, 99, 235, 0); }}
                    100% {{ box-shadow: 0 0 0 0 rgba(37, 99, 235, 0); }}
                }}
                .pulse-node {{ animation: pulse-ring 1.5s infinite; }}
            </style>
            """
        )

    # STATE STEP 1: COMPLIANCE
    if current_stage == "COMPLIANCE":
        draw_progress_screen(1, "Evaluating corporate parameters against investment mandate parameters...")
        compliance = ComplianceAgent()
        strl.session_state["compliance_report"] = compliance.assess_deal_compliance(deal_dict)
        strl.session_state["pipeline_stage"] = "FINANCIAL"
        strl.rerun()

    # STATE STEP 2: FINANCIALS
    elif current_stage == "FINANCIAL":
        draw_progress_screen(2, "Auditing dynamic forecasting assumptions and revenue metrics...")
        if use_cache and fin_cache_file.exists():
            with open(fin_cache_file, "r") as f:
                cached_fin_data = json.load(f)
            try:
                from vc_deal_review.schema.financials import FinancialAnalysisReport
                strl.session_state["financial_report"] = FinancialAnalysisReport.model_validate(cached_fin_data)
            except Exception:
                fin_agent = FinancialAgent()
                fin_report = fin_agent.analyze_financial_performance(deal_dict)
                strl.session_state["financial_report"] = fin_report
                with open(fin_cache_file, "w") as f:
                    json.dump(fin_report.model_dump(), f, indent=4)
        else:
            fin_agent = FinancialAgent()
            fin_report = fin_agent.analyze_financial_performance(deal_dict)
            strl.session_state["financial_report"] = fin_report
            with open(fin_cache_file, "w") as f:
                json.dump(fin_report.model_dump(), f, indent=4)
        
        strl.session_state["pipeline_stage"] = "RISK"
        strl.rerun()

    # STATE STEP 3: RISK REACT LOOP
    elif current_stage == "RISK":
        draw_progress_screen(3, "Executing mathematical LangGraph ReAct decision trees...")
        if use_cache and risk_cache_file.exists():
            with open(risk_cache_file, "r") as f:
                cached_risk_data = json.load(f)
            try:
                from vc_deal_review.schema.risk import RiskQuantifierReport
                strl.session_state["risk_report"] = RiskQuantifierReport.model_validate(cached_risk_data)
            except Exception:
                risk_agent = RiskAgent()
                risk_report = risk_agent.assess_deal_risk(deal_dict, user_id=current_user)
                strl.session_state["risk_report"] = risk_report
                with open(risk_cache_file, "w") as f:
                    json.dump(risk_report.model_dump(), f, indent=4)
        else:
            risk_agent = RiskAgent()
            risk_report = risk_agent.assess_deal_risk(deal_dict, user_id=current_user)
            strl.session_state["risk_report"] = risk_report
            with open(risk_cache_file, "w") as f:
                json.dump(risk_report.model_dump(), f, indent=4)

        strl.session_state["analysis_triggered"] = True
        strl.session_state["pipeline_stage"] = "COMPLETE"
        strl.rerun()

# -------------------------------------------------------------
# MAIN DASHBOARD RENDER FRAME
# -------------------------------------------------------------
elif "active_deal_data" in strl.session_state:
    deal_dict = strl.session_state["active_deal_data"]
    
    company_name = deal_dict.get("metadata", {}).get("company_name", "Unknown Company")
    sector = deal_dict.get("metadata", {}).get("sector", "N/A")
    location = deal_dict.get("metadata", {}).get("location", "N/A")
    inc_type = deal_dict.get("metadata", {}).get("incorporation_type", "N/A")
    fin_dict = deal_dict.get("financials", {})

    has_run = strl.session_state.get("analysis_triggered", False)
    is_cached_extraction = strl.session_state.get("extraction_cached_flag", False)

    # DYNAMIC VISUAL PIPELINE STATUS BAR TRACKER
    step1_class = "complete"
    step2_class = "complete" if is_cached_extraction else "active"
    step3_class = "complete" if has_run else ("active" if is_cached_extraction else "")
    step4_class = "complete" if has_run else ""
    
    line2_class = "complete" if is_cached_extraction else ""
    line3_class = "complete" if has_run else ""
    
    step2_label = "2. Schema Extracted (Cache)" if is_cached_extraction else "2. Schema Extracted"
    step3_label = "3. Multi-Agent Audit" if not has_run else "3. Evaluation Run Complete"
    step4_label = "4. Report Ready" if has_run else "4. Review Pending"

    strl.markdown(
        f"""
        <div class="status-tracker" style="margin-bottom: 1.25rem;">
            <div class="status-step {step1_class}"><span class="step-num">1</span>1. Ingestion & OCR</div>
            <div class="status-line complete"></div>
            <div class="status-step {step2_class}"><span class="step-num">2</span>{step2_label}</div>
            <div class="status-line {line2_class}"></div>
            <div class="status-step {step3_class}"><span class="step-num">3</span>{step3_label}</div>
            <div class="status-line {line3_class}"></div>
            <div class="status-step {step4_class}"><span class="step-num">4</span>{step4_label}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # CONSOLIDATED ACTIVE TARGET CONTEXT COMPONENT & ACTION MODULE
    status_badge = "READY FOR SWEEP" if not has_run else "ANALYSIS COMPLETE"
    badge_bg = "#f1f5f9" if not has_run else "#ecfdf5"
    badge_color = "#475569" if not has_run else "#065f46"

    col_target_left, col_target_right = strl.columns([0.65, 0.35])

    with col_target_left:
        strl.markdown(
            f"""
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem 1.5rem; min-height: 80px; display: flex; flex-direction: column; justify-content: center;">
                <h2 style="margin: 0; font-size: 26px; font-weight: 700; color: #0f172a; line-height: 1.2;">🏢 {company_name} <span style="font-size: 11px; font-weight: 600; vertical-align: middle; margin-left: 8px; background-color: {badge_bg}; color: {badge_color}; padding: 3px 8px; border-radius: 12px; letter-spacing: 0.02em;">{status_badge}</span></h2>
                <div style="font-size: 15px; color: #475569; margin-top: 8px; font-weight: 500;">
                    <b>Sector:</b> <span style="color: #0f172a;">{sector}</span> &emsp;•&emsp; <b>Jurisdiction:</b> <span style="color: #0f172a;">{location}</span> &emsp;•&emsp; <b>Structure:</b> <span style="color: #0f172a;">{inc_type}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_target_right:
        if not has_run:
            with strl.container():
                strl.markdown(
                    """
                    <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 0.5rem 1rem; margin-bottom: 6px; text-align: center;">
                        <span style="font-size: 12.5px; font-weight: 700; color: #166534;">⚡ Deep Analysis Sweep Available</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                # Clicking this button initializes our non-blocking state processing track
                if strl.button("Execute Intelligence Run", type="primary", use_container_width=True):
                    strl.session_state["pipeline_stage"] = "COMPLIANCE"
                    strl.rerun()
        else:
            with strl.container():
                strl.markdown(
                    """
                    <div style="background-color: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 0.5rem 1rem; margin-bottom: 6px; text-align: center;">
                        <span style="font-size: 12.5px; font-weight: 700; color: #065f46;">✅ Analysis Metrics Generated</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                strl.button("Analysis Complete", type="secondary", use_container_width=True, disabled=True)

    strl.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # EXPANDED DATA DISPLAY RENDERING CARDS
    # -------------------------------------------------------------
    card_style = "background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; color: #334155; height: 100%; box-sizing: border-box;"
    item_style = "display: flex; justify-content: space-between; margin-bottom: 0.75rem; font-size: 14px; gap: 12px;"
    card_header_style = "margin-top: 0px; margin-bottom: 1.25rem; font-size: 17px; font-weight: 600; color: #1e293b;"

    financial_html = f"""
    <div style="{card_style}">
        <div style="{card_header_style}">💰 Financial Metrics</div>
        <div style="{item_style}"><span><b>Target Ask Amount:</b></span><span style="text-align: right;">${fin_dict.get('ask_amount', 0.0):,.2f}</span></div>
        <div style="{item_style}"><span><b>Pre-Money Valuation:</b></span><span style="text-align: right;">${fin_dict.get('pre_money_valuation', 0.0):,.2f}</span></div>
        <div style="{item_style}"><span><b>Annual Recurring Revenue (ARR):</b></span><span style="text-align: right;">${fin_dict.get('annual_recurring_revenue', 0.0):,.2f}</span></div>
        <div style="{item_style}"><span><b>Current Cash Balance:</b></span><span style="text-align: right;">${fin_dict.get('current_cash_balance', 0.0):,.2f}</span></div>
        <div style="display: flex; justify-content: space-between; font-size: 14px; gap: 12px;"><span><b>Monthly Burn Rate:</b></span><span style="text-align: right;">${fin_dict.get('monthly_burn_rate', 0.0):,.2f}</span></div>
    </div>
    """

    terms_dict = deal_dict.get("deal_terms", {})
    liq_pref_dict = terms_dict.get("liquidation_preference", {})
    liq_display = f"{liq_pref_dict.get('multiple', 'N/A')} ({liq_pref_dict.get('type', 'N/A')})"
    
    structural_html = f"""
    <div style="{card_style}">
        <div style="{card_header_style}">📝 Structural Deal Terms</div>
        <div style="{item_style}"><span><b>Lead Investor:</b></span><span style="text-align: right;">{terms_dict.get('investor', 'N/A')}</span></div>
        <div style="{item_style}"><span><b>Security Type:</b></span><span style="text-align: right;">{terms_dict.get('security_type', 'N/A')}</span></div>
        <div style="{item_style}"><span><b>Equity Allocation:</b></span><span style="text-align: right;">{terms_dict.get('equity_issued_percent', 'N/A')}%</span></div>
        <div style="{item_style}"><span><b>Liquidation Preference:</b></span><span style="text-align: right;">{liq_display}</span></div>
        <div style="{item_style}"><span><b>Exclusivity Period:</b></span><span style="text-align: right;">{terms_dict.get('exclusivity_period_days', 'N/A')} days</span></div>
        <div style="display: flex; justify-content: space-between; font-size: 14px; gap: 12px;"><span><b>Governing Law:</b></span><span style="text-align: right;">{terms_dict.get('governing_law', 'N/A')}</span></div>
    </div>
    """

    main_tab1, main_tab2 = strl.tabs(["📊 Extracted Profile", "📝 Analysis Report"])

    with main_tab1:
        strl.markdown("<br>", unsafe_allow_html=True)
        strl.markdown(
            f"""
            <div style="display: flex; flex-direction: row; gap: 1.5rem; width: 100%; align-items: stretch;">
                <div style="flex: 1;">{financial_html}</div>
                <div style="flex: 1;">{structural_html}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with main_tab2:
        sub_tab1, sub_tab2, sub_tab3 = strl.tabs([
            "Compliance Mandates",
            "Financial Performance",
            "Risk Quantification"
        ])
        
        with sub_tab1:
            strl.markdown("<br>", unsafe_allow_html=True)
            if "compliance_report" in strl.session_state:
                report = strl.session_state["compliance_report"]
                color_hex = {"APPROVED": "#22c55e", "REVIEW_REQUIRED": "#f97316", "BLOCKED": "#ef4444"}
                stance_color = color_hex.get(report.overall_status, "#64748b")
                
                strl.markdown(f'<div style="background-color: {stance_color}10; border-left: 4px solid {stance_color}; padding: 12px; border-radius: 4px; margin-bottom: 1.5rem; font-size: 14px;"><b>Policy Status:</b> {report.overall_status}</div>', unsafe_allow_html=True)
                for finding in report.findings:
                    f_icon = "✅" if finding.status == "PASS" else ("⚠️" if finding.status == "WARNING" else "🛑")
                    col_f1, col_f2 = strl.columns([0.25, 0.75])
                    
                    col_f1.markdown(f"<div class='report-finding-header'>{f_icon} {finding.rule_name}</div>", unsafe_allow_html=True)
                    col_f2.markdown(
                        f"<div class='report-finding-details'><i>{finding.details}</i></div>"
                        f"<div class='report-finding-meta'>Extracted: {finding.extracted_value} | Required: {finding.threshold_applied}</div>", 
                        unsafe_allow_html=True
                    )
            else:
                strl.info("Trigger 'Execute Intelligence Run' above to activate analysis tracks.")

        with sub_tab2:
            strl.markdown("<br>", unsafe_allow_html=True)
            if "financial_report" in strl.session_state:
                fin_report = strl.session_state["financial_report"]
                color_hex = {"APPROVED": "#22c55e", "REVIEW_REQUIRED": "#f97316", "BLOCKED": "#ef4444"}
                stance_color = color_hex.get(fin_report.overall_status, "#64748b")
                
                strl.markdown(f'<div style="background-color: {stance_color}10; border-left: 4px solid {stance_color}; padding: 12px; border-radius: 4px; margin-bottom: 1.5rem; font-size: 14px;"><b>Financial Profile Stance:</b> {fin_report.overall_status}</div>', unsafe_allow_html=True)
                
                for finding in fin_report.findings:
                    f_icon = "✅" if finding.status == "PASS" else ("⚠️" if finding.status == "WARNING" else "🛑")
                    col_f1, col_f2 = strl.columns([0.25, 0.75])
                    
                    col_f1.markdown(f"<div class='report-finding-header'>{f_icon} {finding.rule_name}</div>", unsafe_allow_html=True)
                    col_f2.markdown(
                        f"<div class='report-finding-details'><i>{finding.details}</i></div>"
                        f"<div class='report-finding-meta'>Extracted: {finding.extracted_value} | Benchmark Target: {finding.threshold_applied}</div>", 
                        unsafe_allow_html=True
                    )
                
                strl.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
                strl.markdown("#### 🔍 Forward Model Sanity Audit")
                strl.info(fin_report.projections_sanity_check)
            else:
                strl.info("Trigger 'Execute Intelligence Run' above to evaluate financial track performance mechanics.")

        with sub_tab3:
            strl.markdown("<br>", unsafe_allow_html=True)
            if "risk_report" in strl.session_state:
                risk_report = strl.session_state["risk_report"]
                color_hex = {"APPROVED": "#22c55e", "REVIEW_REQUIRED": "#f97316", "BLOCKED": "#ef4444"}
                stance_color = color_hex.get(risk_report.overall_status, "#64748b")
                
                strl.markdown(
                    f"""
                    <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;">
                        <div style="flex: 1; background-color: {stance_color}10; border-left: 4px solid {stance_color}; padding: 12px; border-radius: 4px; font-size: 14px;">
                            <b>Risk Exposure Tier:</b> {risk_report.overall_status}
                        </div>
                        <div style="flex: 1; background-color: #f1f5f9; border-left: 4px solid #475569; padding: 12px; border-radius: 4px; font-size: 14px;">
                            <b>Verified Operational Runway:</b> {risk_report.calculated_runway_months:.1f} Months
                        </div>
                        <div style="flex: 1; background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 12px; border-radius: 4px; font-size: 14px;">
                            <b>Max Flagged Severity:</b> {risk_report.highest_severity_score} / 10
                        </div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                for finding in risk_report.findings:
                    f_icon = "✅" if finding.status == "PASS" else ("⚠️" if finding.status == "WARNING" else "🛑")
                    col_f1, col_f2 = strl.columns([0.25, 0.75])
                    
                    col_f1.markdown(f"<div class='report-finding-header'>{f_icon} {finding.rule_name}</div>", unsafe_allow_html=True)
                    col_f2.markdown(
                        f"<div class='report-finding-details'>{finding.details}</div>"
                        f"<div class='report-finding-meta'>Calculated Metric: {finding.extracted_value} | Threshold Constraint: {finding.threshold_applied}</div>", 
                        unsafe_allow_html=True
                    )
            else:
                strl.info("Trigger 'Execute Intelligence Run' above to run the ReAct mathematical risk loop tracker.")

    strl.markdown("<br>", unsafe_allow_html=True)
    with strl.expander("🔍 View Raw Validated Schema JSON"):
        strl.json(deal_dict)
else:
    strl.info("Upload documents and click 'Execute Extractor Pipeline' to begin.")