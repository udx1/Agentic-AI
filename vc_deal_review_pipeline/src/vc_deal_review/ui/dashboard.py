import os
import sys
from pathlib import Path

# Force Python to recognize the 'src' root directory relative to this file
src_path = str(Path(__file__).resolve().parents[2])
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import streamlit as strl
import json
import io
from pypdf import PdfReader
from vc_deal_review.agents.extractor_agent import ExtractorAgent
from vc_deal_review.Compliance.engine import ComplianceEngine 
from vc_deal_review.Financial.engine import FinancialEngine

strl.set_page_config(
    page_title="Venture Capital Deal Review Intelligence Pipeline",
    page_icon="💼",
    layout="wide"
)

# Setup a local cache directory
CACHE_DIR = Path("src/vc_deal_review/.cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

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
        
        /* =========================================================
           TOP LEVEL MAIN WORKSPACE TABS (Pills Container Style)
           ========================================================= */
        /* Target the outer tab navigation wrapper bar */
        div[data-testid="stMainBlockContainer"] > div > div > div[data-testid="stTabs"] > div:first-child {
            background-color: #f8fafc !important; 
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            padding: 4px !important;
            margin-bottom: 0.5rem !important;
            width: 100% !important;
        }
        
        /* FORCE EXPLICIT REMOVAL of native underline inside the pill container */
        div[data-testid="stMainBlockContainer"] > div > div > div[data-testid="stTabs"] > div:first-child div[data-baseweb="tab-list"] {
            border-bottom: none !important;
            border-bottom-width: 0px !important;
        }
        
        /* Style buttons inside the outer main tab bar container ONLY */
        div[data-testid="stMainBlockContainer"] > div > div > div[data-testid="stTabs"] > div:first-child button {
            background-color: transparent !important;
            color: #64748b !important; 
            border: none !important;
            border-radius: 6px !important;
            padding: 0.5rem 1.5rem !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            margin-right: 4px !important;
            transition: all 0.2s ease-in-out !important;
        }
        
        div[data-testid="stMainBlockContainer"] > div > div > div[data-testid="stTabs"] > div:first-child button[aria-selected="true"] {
            background-color: #eff6ff !important; 
            color: #1e40af !important; 
            border: none !important;
        }
        
        /* Kill moving line highlight under the outer pills layer */
        div[data-testid="stMainBlockContainer"] > div > div > div[data-testid="stTabs"] > div:first-child div[data-baseweb="tab-highlight"] {
            display: none !important;
        }
        
        /* =========================================================
           NESTED SUB-TABS (Clean Horizontal Underline Style)
           ========================================================= */
        /* Target ONLY the inner sub-tab navigation wrapper container */
        div[data-testid="stTabs"] div[data-testid="stTabs"] > div:first-child {
            background-color: transparent !important;
            border: none !important;
            border-radius: 0px !important;
            padding: 0px !important;
            margin-top: -0.5rem !important;
            margin-bottom: 0.75rem !important;
            width: 100% !important;
        }
        
        /* Confine the thin horizontal baseline line strictly to the inner sub-tab list layer */
        div[data-testid="stTabs"] div[data-testid="stTabs"] > div:first-child div[data-baseweb="tab-list"] {
            border-bottom: 1px solid #e2e8f0 !important;
            gap: 24px !important;
        }
        
        /* Text items style for inner sub-tabs navigation items */
        div[data-testid="stTabs"] div[data-testid="stTabs"] > div:first-child button {
            background-color: transparent !important;
            color: #64748b !important;
            border: none !important;
            border-radius: 0px !important;
            padding: 0.4rem 1rem !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            margin-right: 8px !important;
        }
        
        div[data-testid="stTabs"] div[data-testid="stTabs"] > div:first-child button[aria-selected="true"] {
            background-color: transparent !important;
            color: #1e40af !important;
            border: none !important;
        }

        /* Thins down and handles the active tab moving indicator strip for nested tabs */
        div[data-testid="stTabs"] div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] {
            display: block !important;
            height: 2px !important; 
            background-color: #2563eb !important;
        }
        
        /* Pad alignment corrections */
        div[data-baseweb="tab"] {
            padding-bottom: 6px !important;
            padding-top: 6px !important;
        }

        /* Global catch-all override to strip unintentional browser fallback styling accents */
        .stTabs button, .stTabs button[aria-selected="true"] {
            border-bottom: none !important;
            border-bottom-width: 0px !important;
            box-shadow: none !important;
        }

        /* =========================================================
           PREMIUM STATUS TRACKER STYLING
           ========================================================= */
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

        /* Report Tab Findings Typography & Padding Optimization */
        .report-finding-header {
            font-size: 14px !important;
            font-weight: 600 !important;
            color: #0f172a !important;
            margin-bottom: 4px !important;
            line-height: 1.3 !important;
        }
        .report-finding-details {
            font-size: 13.5px !important;
            color: #334155 !important;
            line-height: 1.5 !important;
            margin-bottom: 4px !important;
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

# FIXED EXPLICIT LINE-HEIGHT TO PREVENT TYPOGRAPHY CUTOFF
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
    for key in ["compliance_report", "financial_report", "active_deal_data", "analysis_triggered"]:
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
# MAIN DASHBOARD RENDER FRAME
# -------------------------------------------------------------
if "active_deal_data" in strl.session_state:
    deal_dict = strl.session_state["active_deal_data"]
    
    company_name = deal_dict.get("metadata", {}).get("company_name", "Unknown Company")
    sector = deal_dict.get("metadata", {}).get("sector", "N/A")
    location = deal_dict.get("metadata", {}).get("location", "N/A")
    inc_type = deal_dict.get("metadata", {}).get("incorporation_type", "N/A")
    fin_dict = deal_dict.get("financials", {})

    fin_cache_file = CACHE_DIR / "nexushealth_ai_cached_financials.json"
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
                    <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 0.5rem 1rem; margin-bottom: 6px;">
                        <span style="font-size: 12.5px; font-weight: 700; color: #166534;">⚡ Deep Analysis Sweep Available</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if strl.button("Execute Intelligence Run", type="primary", use_container_width=True):
                    with strl.container():
                        strl.markdown(
                            """
                            <div style="background-color: #f8fafc; border: 2px dashed #3b82f6; border-radius: 12px; padding: 3rem; text-align: center; margin: 2rem 0; width: 100%;">
                                <div style="font-size: 40px; margin-bottom: 1rem; animation: pulse 1.5s infinite;">⚙️</div>
                                <div style="font-size: 20px; font-weight: 700; color: #1e3a8a; margin-bottom: 0.5rem;">Executing Multi-Agent Evaluation Tracks</div>
                                <div style="font-size: 14px; color: #64748b; max-width: 500px; margin: 0 auto; line-height: 1.5;">
                                    Parsing structural deal packages, verifying compliance metrics, and auditing financial models via Claude Sonnet...
                                </div>
                            </div>
                            <style>
                                @keyframes pulse {
                                    0% { transform: scale(1); opacity: 0.6; }
                                    50% { transform: scale(1.2); opacity: 1; }
                                    100% { transform: scale(1); opacity: 0.6; }
                                }
                            </style>
                            """, 
                            unsafe_allow_html=True
                        )
                        
                        with strl.spinner("Processing framework matrices..."):
                            comp_engine = ComplianceEngine()
                            strl.session_state["compliance_report"] = comp_engine.evaluate_deal(deal_dict)
                            
                            if use_cache and fin_cache_file.exists():
                                with open(fin_cache_file, "r") as f:
                                    cached_fin_data = json.load(f)
                                try:
                                    from vc_deal_review.Financial.models import FinancialAnalysisReport
                                    strl.session_state["financial_report"] = FinancialAnalysisReport.model_validate(cached_fin_data)
                                except Exception:
                                    fin_engine = FinancialEngine()
                                    fin_report = fin_engine.analyze_financial_performance(deal_dict)
                                    strl.session_state["financial_report"] = fin_report
                                    with open(fin_cache_file, "w") as f:
                                        json.dump(fin_report.model_dump(), f, indent=4)
                            else:
                                fin_engine = FinancialEngine()
                                fin_report = fin_engine.analyze_financial_performance(deal_dict)
                                strl.session_state["financial_report"] = fin_report
                                with open(fin_cache_file, "w") as f:
                                    json.dump(fin_report.model_dump(), f, indent=4)

                            strl.session_state["analysis_triggered"] = True
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
    # EXPANDED DATA DISPLAY RENDERING CARDS (FIXED EQUAL HEIGHT FLEX COLS)
    # -------------------------------------------------------------
    # Dropped 'min-height' and added 'height: 100%' to ensure equal flex mapping
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
        
        # Injecting a flex wrapper enclosing the row to guarantee matching card sizing
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
            strl.info("Trigger 'Run Deal Analysis Sweep' above to activate Risk Engine grading.")

    strl.markdown("<br>", unsafe_allow_html=True)
    with strl.expander("🔍 View Raw Validated Schema JSON"):
        strl.json(deal_dict)
else:
    strl.info("Upload documents and click 'Execute Extractor Pipeline' to begin.")