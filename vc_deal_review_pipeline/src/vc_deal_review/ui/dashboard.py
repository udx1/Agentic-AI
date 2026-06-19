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

    _ProactorBasePipeTransport._call_connection_lost = silence_connection_lost_noise( # type: ignore[attr-defined]
        _ProactorBasePipeTransport._call_connection_lost # type: ignore[attr-defined]
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

if "active_sub_tab" not in strl.session_state:
    strl.session_state["active_sub_tab"] = 0

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

    # 1. Cleanly purge ALL legacy and new synthesis state variables to clear out stale memory
    purged_keys = [
        "compliance_report", 
        "financial_report", 
        "risk_report", 
        "synthesis_report", # Clear new router metrics
        "edited_memo",       # Clear human text area overrides
        "active_deal_data", 
        "analysis_triggered", 
        "pipeline_stage"
    ]

    for key in purged_keys:
        if key in strl.session_state:
            del strl.session_state[key]

    deal_dict = None

    # 2. Modernize and scope the raw text data cache path explicitly to the active user
    CACHE_DIR.mkdir(exist_ok=True)
    user_extraction_cache = CACHE_DIR / f"extracted_deal_{current_user}.json"    

    if use_cache and user_extraction_cache.exists():
        with open(user_extraction_cache, "r") as f:
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
                
                with open(user_extraction_cache, "w") as f:
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
if "pipeline_stage" in strl.session_state \
    and strl.session_state["pipeline_stage"] in ["PARALLEL_EXECUTION", "SYNTHESIZE", "GENERATING_REPORT"]:
    current_stage = strl.session_state["pipeline_stage"]
    deal_dict = strl.session_state["active_deal_data"]


    # Define visual render helper function for the full takeover screen
    def draw_progress_screen(active_step: int, step_desc: str):
        # State styling definitions for a unified 4-stage tracking layout
        s1_num, s1_bg, s1_txt, s1_pulse = ("✓", "#059669", "color: #059669; font-weight: 600;", "") if active_step > 1 else ("1", "#2563eb", "color: #2563eb; font-weight: 600;", "pulse-node")
        s2_num, s2_bg, s2_txt, s2_pulse = ("✓", "#059669", "color: #059669; font-weight: 600;", "") if active_step > 2 else (("2", "#2563eb", "color: #2563eb; font-weight: 600;", "pulse-node") if active_step == 2 else ("2", "#f1f5f9", "color: #64748b;", ""))
        s3_num, s3_bg, s3_txt, s3_pulse = ("✓", "#059669", "color: #059669; font-weight: 600;", "") if active_step > 3 else (("3", "#2563eb", "color: #2563eb; font-weight: 600;", "pulse-node") if active_step == 3 else ("3", "#f1f5f9", "color: #64748b;", ""))
        s4_num, s4_bg, s4_txt, s4_pulse = ("4", "#2563eb", "color: #2563eb; font-weight: 600;", "pulse-node") if active_step == 4 else ("4", "#f1f5f9", "color: #64748b;", "")

        strl.html(
            f"""
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 2.5rem 2rem; text-align: center; margin: 1.5rem auto; max-width: 950px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05); font-family: 'Inter', sans-serif;">
                <div style="font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom: 0.5rem; letter-spacing: -0.01em;">Orchestrating Multi-Agent Intelligence Tracks</div>
                <div style="font-size: 13.5px; color: #475569; max-width: 600px; margin: 0 auto 2rem auto; line-height: 1.5;">
                    Current Status: <span style="color:#2563eb; font-weight:600;">{step_desc}</span>
                </div>
                
                <div style="display: flex; justify-content: space-between; max-width: 850px; margin: 0 auto; position: relative;">
                    <div style="position: absolute; top: 15px; left: 5%; right: 5%; height: 2px; background: #e2e8f0; z-index: 1;"></div>
                    
                    <div style="z-index: 2; text-align: center; width: 22%;">
                        <div class="{s1_pulse}" style="width: 32px; height: 32px; border-radius: 50%; background: {s1_bg}; color: white; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px auto; font-size: 12px; font-weight: 700;">{s1_num}</div>
                        <div style="font-size: 11.5px; {s1_txt}">Compliance Review</div>
                    </div>
                    <div style="z-index: 2; text-align: center; width: 22%;">
                        <div class="{s2_pulse}" style="width: 32px; height: 32px; border-radius: 50%; background: {s2_bg}; color: {'white' if active_step >= 2 else '#94a3b8'}; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px auto; font-size: 12px; font-weight: 700; {'border: 2px solid #e2e8f0;' if active_step < 2 else ''}">{s2_num}</div>
                        <div style="font-size: 11.5px; {s2_txt}">Financial Audit</div>
                    </div>
                    <div style="z-index: 2; text-align: center; width: 22%;">
                        <div class="{s3_pulse}" style="width: 32px; height: 32px; border-radius: 50%; background: {s3_bg}; color: {'white' if active_step >= 3 else '#94a3b8'}; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px auto; font-size: 12px; font-weight: 700; {'border: 2px solid #e2e8f0;' if active_step < 3 else ''}">{s3_num}</div>
                        <div style="font-size: 11.5px; {s3_txt}">Risk Quantification</div>
                    </div>
                    <div style="z-index: 2; text-align: center; width: 22%;">
                        <div class="{s4_pulse}" style="width: 32px; height: 32px; border-radius: 50%; background: {s4_bg}; color: {'white' if active_step == 4 else '#94a3b8'}; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px auto; font-size: 12px; font-weight: 700; {'border: 2px solid #e2e8f0;' if active_step < 4 else ''}">{s4_num}</div>
                        <div style="font-size: 11.5px; {s4_txt}">Memo Synthesis</div>
                    </div>
                </div>
            </div>
            <style>
                @keyframes pulse-ring {{
                    0% {{ box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.5); }}
                    70% {{ box-shadow: 0 0 0 8px rgba(37, 99, 235, 0); }}
                    100% {{ box-shadow: 0 0 0 0 rgba(37, 99, 235, 0); }}
                }}
                .pulse-node {{ animation: pulse-ring 1.5s infinite; }}
            </style>
            """
        )

    if current_stage == "PARALLEL_EXECUTION":
        
        import concurrent.futures
        import threading
        from streamlit.runtime.scriptrunner import get_script_run_ctx, add_script_run_ctx
        
        from vc_deal_review.agents.compliance_agent import ComplianceAgent
        from vc_deal_review.agents.financial_agent import FinancialAgent
        from vc_deal_review.agents.risk_agent import RiskAgent
        
        from vc_deal_review.schema.compliance import ComplianceReport
        from vc_deal_review.schema.financials import FinancialAnalysisReport
        from vc_deal_review.schema.risk import RiskQuantifierReport

        # 1. Capture the parent thread's active Streamlit context
        ctx = get_script_run_ctx()

        # 2. Define self-registering wrappers that run INSIDE the background threads
        def run_compliance_with_ctx():
            add_script_run_ctx(threading.current_thread(), ctx)
            
            user_comp_cache = CACHE_DIR / f"compliance_report_{current_user}.json"
            if use_cache and user_comp_cache.exists():
                try:
                    with open(user_comp_cache, "r") as f:
                        return ComplianceReport.model_validate(json.load(f))
                except Exception:
                    pass
            
            agent = ComplianceAgent()
            report = agent.assess_deal_compliance(deal_dict)
            with open(user_comp_cache, "w") as f:
                json.dump(report.model_dump(), f, indent=4)
            return report

        def run_financial_with_ctx():
            add_script_run_ctx(threading.current_thread(), ctx)
            
            user_fin_cache = CACHE_DIR / f"financial_report_{current_user}.json"
            if use_cache and user_fin_cache.exists():
                try:
                    with open(user_fin_cache, "r") as f:
                        return FinancialAnalysisReport.model_validate(json.load(f))
                except Exception:
                    pass
            
            agent = FinancialAgent()
            report = agent.analyze_financial_performance(deal_dict)
            with open(user_fin_cache, "w") as f:
                json.dump(report.model_dump(), f, indent=4)
            return report

        def run_risk_with_ctx():
            add_script_run_ctx(threading.current_thread(), ctx)
            
            user_risk_cache = CACHE_DIR / f"risk_report_{current_user}.json"
            if use_cache and user_risk_cache.exists():
                try:
                    with open(user_risk_cache, "r") as f:
                        return RiskQuantifierReport.model_validate(json.load(f))
                except Exception:
                    pass
            
            agent = RiskAgent()
            report = agent.assess_deal_risk(deal_dict, user_id=current_user)
            with open(user_risk_cache, "w") as f:
                json.dump(report.model_dump(), f, indent=4)
            return report

        # 3. Concurrent Execution Layer
        try:

            draw_progress_screen(2, "Spawning concurrent Compliance, Financial, and Risk intelligence engines...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                # Submit the self-registering context functions instead
                future_comp = executor.submit(run_compliance_with_ctx)
                future_fin = executor.submit(run_financial_with_ctx)
                future_risk = executor.submit(run_risk_with_ctx)
                
                # Resolve thread block results synchronously (completely avoiding internal ._thread access)
                strl.session_state["compliance_report"] = future_comp.result()
                strl.session_state["financial_report"] = future_fin.result()
                strl.session_state["risk_report"] = future_risk.result()
            draw_progress_screen(4, "Parallel checks complete. Transferring payloads to Synthesis agent...")

        except Exception as e:
            strl.error(f"Critical error occurred in parallel intelligence thread pool: {str(e)}")
            strl.stop()

        # Route immediately forward to narrative parsing
        strl.session_state["pipeline_stage"] = "SYNTHESIZE"
        strl.rerun()

    # STATE STEP 4: ROUTING EVALUATION (Pure Gatekeeper Logic)
    elif current_stage == "SYNTHESIZE":
        draw_progress_screen(4, "Evaluating institutional thresholds and exception parameters...")
        
        from vc_deal_review.agents.synthesizer_agent import SynthesizerAgent
        
        comp_report = strl.session_state["compliance_report"]
        fin_report = strl.session_state["financial_report"]
        risk_report = strl.session_state["risk_report"]
        
        # Ingest payloads and evaluate escalation rules
        synthesizer = SynthesizerAgent()
        synthesis_result = synthesizer.evaluate_and_route(comp_report, fin_report, risk_report)
        
        strl.session_state["synthesis_report"] = synthesis_result
    
        # Branch architecture based on evaluation
        if synthesis_result.escalation_needed:
            strl.session_state["edited_memo"] = {
                "executive_summary": "Drafting investment thesis details based on multi-agent feeds... Reviewer adjustments can be entered here.",
                "remediation_notes": "Enter mandated mitigations or closing conditions here..."
            }    
            strl.session_state["analysis_triggered"] = True
            strl.session_state["pipeline_stage"] = "HUMAN_REVIEW"  # Drops down into interactive dashboard tabs
        else:
            strl.session_state["pipeline_stage"] = "GENERATING_REPORT" # Keeps running in background loop
        strl.rerun()

    # NEW STATE STEP 5: AUTOMATED NARRATIVE GENERATION (Bypassed Escalation Path)
    elif current_stage == "GENERATING_REPORT":
        draw_progress_screen(4, "Bypassing escalation. Chief Investment Officer compiling final memorandum narrative...")
        
        from vc_deal_review.agents.report_generator_agent import ReportGeneratorAgent
        
        comp_report = strl.session_state["compliance_report"]
        fin_report = strl.session_state["financial_report"]
        risk_report = strl.session_state["risk_report"]
        synthesis_result = strl.session_state["synthesis_report"]
        
        # Fire the writer agent with zero human modifications
        generator = ReportGeneratorAgent()
        final_memo = generator.generate_final_memo(
            routing_payload=synthesis_result,
            comp=comp_report,
            fin=fin_report,
            risk=risk_report,
            human_notes=""
        )
        
        # Save narrative strings into layout state structures
        strl.session_state["edited_memo"] = {
            "executive_summary": final_memo.executive_summary_draft,
            "remediation_notes": "\n".join(final_memo.closing_conditions) if final_memo.closing_conditions else ""
        }
        
        strl.session_state["synthesis_report"].suggested_recommendation = "PROCEED (AUTOMATED PASS)"
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
                    strl.session_state["pipeline_stage"] = "PARALLEL_EXECUTION"
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



    # Helper layout container for the metric profile cards
    def render_extracted_profile_workspace(fin_html: str, struct_html: str):
        strl.markdown("<br>", unsafe_allow_html=True)
        strl.markdown(
            f"""
            <div style="display: flex; flex-direction: row; gap: 1.5rem; width: 100%; align-items: stretch;">
                <div style="flex: 1;">{fin_html}</div>
                <div style="flex: 1;">{struct_html}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Helper layout container for the multi-agent sub-tabs
    def render_analysis_report_workspace():
        current_stage = strl.session_state.get("pipeline_stage", "COMPLETE")
        
        if current_stage == "HUMAN_REVIEW":
            strl.markdown(
                """
                <div style="background-color: #fff7ed; border-left: 5px solid #f97316; padding: 1rem; border-radius: 6px; margin-bottom: 1.5rem;">
                    <strong style="color: #c2410c; font-size: 15px;">⚠️ Attention Required:</strong> 
                    This deal has triggered institutional escalation parameters. Please review the <b>Investment Committee Memo</b> workspace below to authorize or decline.
                </div>
                """, unsafe_allow_html=True
            )

        sub_tab1, sub_tab2, sub_tab3, sub_tab4 = strl.tabs([
            "📋 Investment Committee Memo",
            "Compliance Mandates",
            "Financial Performance",
            "Risk Quantification"
        ])
        
        # --- SUB-TAB 1: INVESTMENT COMMITTEE MEMO & SIGN-OFF ---
        with sub_tab1:
            strl.markdown("<br>", unsafe_allow_html=True)
            if "synthesis_report" in strl.session_state and strl.session_state["synthesis_report"] is not None:
                synth = strl.session_state["synthesis_report"]
                
                if current_stage == "HUMAN_REVIEW":
                    strl.markdown("### ⚡ Executive Escalation & Sign-Off Desk")
                    strl.error("#### 🛑 Triggered Exceptions Requiring Committee Review:")
                    for reason in synth.triggered_reasons:
                        strl.markdown(f"- **{reason}**")
                        
                    strl.markdown("#### Select Final Authorization Stance:")
                    col_b1, col_b2 = strl.columns(2)
                    
                    with col_b1:
                        if strl.button("💚 Approve Escalation & Proceed", type="primary", use_container_width=True):
                            with strl.spinner("Incorporate override contexts and rewriting final report..."):
                                from vc_deal_review.agents.report_generator_agent import ReportGeneratorAgent
                                
                                # Gather the live state inputs edited by the user in the text areas below
                                memo_data = strl.session_state.get("edited_memo", {})
                                text_thesis = memo_data.get("executive_summary", "")
                                text_remediations = memo_data.get("remediation_notes", "")
                                
                                compiled_notes = (
                                    f"Authorized Exception. User override edits applied to thesis content: '{text_thesis}'. "
                                    f"Mandated mitigations added: '{text_remediations}'."
                                )
                                
                                # Run generation pass using the collected notes
                                generator = ReportGeneratorAgent()
                                final_memo = generator.generate_final_memo(
                                    routing_payload=strl.session_state["synthesis_report"],
                                    comp=strl.session_state["compliance_report"],
                                    fin=strl.session_state["financial_report"],
                                    risk=strl.session_state["risk_report"],
                                    human_notes=compiled_notes
                                )
                                
                                # Re-commit structural updates back to state
                                strl.session_state["edited_memo"] = {
                                    "executive_summary": final_memo.executive_summary_draft,
                                    "remediation_notes": f"COMMITTEE OVERRIDE MIGRATIONS:\n" + "\n".join(final_memo.closing_conditions)
                                }
                                
                                strl.session_state["final_deal_stance"] = "PROCEED (AUTHORIZED OVERRIDE)"
                                strl.session_state["pipeline_stage"] = "COMPLETE"
                                strl.success("Diligence authorization committed successfully!")
                                strl.rerun()
                    with col_b2:
                        if strl.button("🛑 Decline / Strategic Hold", type="secondary", use_container_width=True):
                            strl.session_state["edited_memo"] = {
                                "executive_summary": "Deal evaluation terminated by Investment Committee review. Strategic Hold mandated due to identified exception parameters.",
                                "remediation_notes": "ARCHIVED ON COMMITTE REVIEW: Deal stance finalized as REJECTED / STRATEGIC_HOLD."
                            }
                           
                            strl.session_state["final_deal_stance"] = "REJECTED / STRATEGIC_HOLD"                            
                            strl.session_state["pipeline_stage"] = "COMPLETE"
                            strl.error("Deal closure committed to historical audit records.")
                            strl.rerun()

                    strl.markdown("---")
                    strl.markdown("#### 📝 Edit Draft Memorandum Text")
                    user_summary = strl.text_area("Executive Summary & Investment Thesis", value=strl.session_state["edited_memo"]["executive_summary"], height=250)
                    strl.session_state["edited_memo"]["executive_summary"] = user_summary
                    
                    user_remediation = strl.text_area("Diligence Mitigations / Closing Comments", value=strl.session_state["edited_memo"]["remediation_notes"], placeholder="Provide executive commentary...", height=120)
                    strl.session_state["edited_memo"]["remediation_notes"] = user_remediation
                else:
                    final_rec = strl.session_state.get("final_deal_stance", "PROCEED")
                    banner_style = "background-color: #ecfdf5; border-left: 5px solid #10b981; color: #065f46;" if "PROCEED" in final_rec else "background-color: #fef2f2; border-left: 5px solid #ef4444; color: #991b1b;"
                    title_text = "✅ LOCKED INVESTMENT COMMITTEE MEMORANDUM" if "PROCEED" in final_rec else "🛑 ARCHIVED AUDIT TRAIL REJECTION RECORD"
                        
                    strl.markdown(f'<div style="{banner_style} padding: 1.5rem; border-radius: 4px; margin-bottom: 1.5rem;"><h3 style="margin-top:0; color: inherit; font-size:18px;">{title_text}</h3><b>Authorized Deal Stance:</b> {final_rec}<br><b>Pipeline Lifecycle:</b> Verified & Archived</div>', unsafe_allow_html=True)
                    strl.markdown("#### 📖 Executive Summary & Thesis Narrative")
                    strl.write(strl.session_state["edited_memo"]["executive_summary"])
                    if strl.session_state["edited_memo"]["remediation_notes"]:
                        strl.markdown("#### 📝 Reviewer Diligence Remediation Notes")
                        strl.info(strl.session_state["edited_memo"]["remediation_notes"])
            else:
                strl.info("Execute the Intelligence Run pipeline above to compile the final Synthesis Memorandum.")

        # --- SUB-TAB 2: COMPLIANCE ---
        with sub_tab2:
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
                    col_f2.markdown(f"<div class='report-finding-details'><i>{finding.details}</i></div><div class='report-finding-meta'>Extracted: {finding.extracted_value} | Required: {finding.threshold_applied}</div>", unsafe_allow_html=True)
            else:
                strl.info("Trigger 'Execute Intelligence Run' above to activate analysis tracks.")

        # --- SUB-TAB 3: FINANCIALS ---
        with sub_tab3:
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
                    col_f2.markdown(f"<div class='report-finding-details'><i>{finding.details}</i></div><div class='report-finding-meta'>Extracted: {finding.extracted_value} | Benchmark Target: {finding.threshold_applied}</div>", unsafe_allow_html=True)
                strl.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
                strl.markdown("#### 🔍 Forward Model Sanity Audit")
                strl.info(fin_report.projections_sanity_check)
            else:
                strl.info("Trigger 'Execute Intelligence Run' above to evaluate financial track performance mechanics.")

        # --- SUB-TAB 4: RISK ---
        with sub_tab4:
            strl.markdown("<br>", unsafe_allow_html=True)
            if "risk_report" in strl.session_state:
                risk_report = strl.session_state["risk_report"]
                color_hex = {"APPROVED": "#22c55e", "REVIEW_REQUIRED": "#f97316", "BLOCKED": "#ef4444"}
                stance_color = color_hex.get(risk_report.overall_status, "#64748b")
                strl.markdown(f'<div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;"><div style="flex: 1; background-color: {stance_color}10; border-left: 4px solid {stance_color}; padding: 12px; border-radius: 4px; font-size: 14px;"><b>Risk Exposure Tier:</b> {risk_report.overall_status}</div><div style="flex: 1; background-color: #f1f5f9; border-left: 4px solid #475569; padding: 12px; border-radius: 4px; font-size: 14px;"><b>Verified Operational Runway:</b> {risk_report.calculated_runway_months:.1f} Months</div><div style="flex: 1; background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 12px; border-radius: 4px; font-size: 14px;"><b>Max Flagged Severity:</b> {risk_report.highest_severity_score} / 10</div></div>', unsafe_allow_html=True)
                for finding in risk_report.findings:
                    f_icon = "✅" if finding.status == "PASS" else ("⚠️" if finding.status == "WARNING" else "🛑")
                    col_f1, col_f2 = strl.columns([0.25, 0.75])
                    col_f1.markdown(f"<div class='report-finding-header'>{f_icon} {finding.rule_name}</div>", unsafe_allow_html=True)
                    col_f2.markdown(f"<div class='report-finding-details'>{finding.details}</div><div class='report-finding-meta'>Calculated Metric: {finding.extracted_value} | Threshold Constraint: {finding.threshold_applied}</div>", unsafe_allow_html=True)
            else:
                strl.info("Trigger 'Execute Intelligence Run' above to run the ReAct risk loop tracker.")

    
    # # -------------------------------------------------------------
    # DYNAMIC MAIN WORKSPACE TAB FOCUS CONTROL
    # -------------------------------------------------------------
    has_run = strl.session_state.get("analysis_triggered", False)

    if has_run:
        main_tab1, main_tab2 = strl.tabs(
            ["📝 Analysis Report", "📊 Extracted Profile"],
            key="tabs_post_run"
        )
        with main_tab1:
            render_analysis_report_workspace()
        with main_tab2:
            render_extracted_profile_workspace(financial_html, structural_html)
    else:
        main_tab1 = strl.tabs(
            ["📊 Extracted Profile"],
            key="tabs_pre_run"
        )[0]
        with main_tab1:
            render_extracted_profile_workspace(financial_html, structural_html)

    
    strl.markdown("<br>", unsafe_allow_html=True)
    with strl.expander("🔍 View Raw Validated Schema JSON"):
        strl.json(deal_dict)
else:
    strl.info("Upload documents and click 'Execute Extractor Pipeline' to begin.")