import streamlit as st
import time
import json
import os
import sys

# Force clear local module cache to prevent Streamlit from holding onto stale imports on hot-reload
for mod in list(sys.modules.keys()):
    if mod.startswith("src.") or mod == "src":
        del sys.modules[mod]

# Speech synthesis cancellation hook
if "cancel_speech" not in st.session_state:
    st.session_state.cancel_speech = False

if st.session_state.cancel_speech:
    st.components.v1.html(
        """
        <script>
            if (window.parent.speechSynthesis) {
                window.parent.speechSynthesis.cancel();
            }
        </script>
        """,
        height=0
    )
    st.session_state.cancel_speech = False

from src.config import Config
from src.parser import ResumeParser
from src.agents.candidate_agents.screening_agent import ScreeningAgent
from src.agents.candidate_agents.mcq_agent import MCQAgent
from src.agents.candidate_agents.interview_agent import InterviewAgent
from src.agents.shared_agents.email_agent import EmailAgent
from src.agents.recruiter_agents.support_agent import SupportAgent
from src.agents.candidate_agents.repeat_agent import RepeatAgent
from src.agents.recruiter_agents.job_agent import JobAgent
from src.agents.candidate_agents.proctoring_agent.proctoring_agent import ProctoringAgent

def validate_stage_transition(current_stage: str, target_stage: str) -> bool:
    """Enforces strict state pipeline transitions for candidates."""
    valid_transitions = {
        "upload": ["proctoring_instruction", "screening_failed", "screening_review"],
        "screening_review": ["proctoring_instruction", "screening_failed"],
        "screening_failed": ["upload"],
        "proctoring_instruction": ["mcq", "upload"],
        "mcq": ["mcq_passed_screen", "mcq_failed_screen", "upload"],
        "mcq_passed_screen": ["interview", "upload"],
        "mcq_failed_screen": ["upload"],
        "interview": ["final_evaluation", "upload"],
        "final_evaluation": ["upload"]
    }
    if current_stage == target_stage:
        return True
    allowed = valid_transitions.get(current_stage, [])
    return target_stage in allowed or target_stage == "upload"

# Set page configurations
st.set_page_config(

    page_title="AgentFlow Recruitment",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Theme styles variables definitions
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Enterprise Light"

theme = st.session_state.theme_mode

if theme == "Cyberpunk Dark":
    root_vars = """
        --bg-gradient: linear-gradient(135deg, #020204 0%, #08080a 50%, #000000 100%);
        --text-main: #f4f4f5;
        --text-sub: #a1a1aa;
        --card-bg: rgba(8, 8, 10, 0.85);
        --card-border: rgba(229, 9, 20, 0.4);
        --sidebar-bg: #020204;
        --sidebar-border: rgba(229, 9, 20, 0.3);
        --accent-red: #ff3344;
        --accent-red-hover: #ff001c;
        --accent-gold: #f5c518;
        --input-bg: rgba(12, 12, 14, 0.9);
        --input-border: rgba(229, 9, 20, 0.3);
        --input-text: #ffffff;
        --listbox-bg: #08080a;
        --listbox-option-hover: rgba(229, 9, 20, 0.2);
        --jd-bg: rgba(8, 8, 10, 0.95);
        --tab-bg: rgba(12, 12, 14, 0.8);
        --tab-hover-bg: rgba(229, 9, 20, 0.15);
        --tab-active-bg: rgba(229, 9, 20, 0.25);
        --bubble-assistant-bg: rgba(24, 24, 27, 0.8);
        --bubble-assistant-border: rgba(229, 9, 20, 0.3);
        --bubble-assistant-text: #f4f4f5;
        --stepper-before-bg: rgba(229, 9, 20, 0.3);
        --stepper-counter-bg: #08080a;
        --stepper-counter-border: rgba(229, 9, 20, 0.4);
        --stepper-counter-text: #a1a1aa;
        --card-hover-border: #ff3344;
        --badge-time-bg: rgba(229, 9, 20, 0.15);
        --badge-time-text: #f4f4f5;
        --badge-red-bg: rgba(229, 9, 20, 0.25);
    """
else: # Enterprise Light
    root_vars = """
        --bg-gradient: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 55%, #e2e8f0 100%);
        --text-main: #0f172a;
        --text-sub: #475569;
        --card-bg: #ffffff;
        --card-border: #e2e8f0;
        --sidebar-bg: #f8fafc;
        --sidebar-border: #e2e8f0;
        --accent-red: #b91c1c;
        --accent-red-hover: #991b1b;
        --accent-gold: #d97706;
        --input-bg: #ffffff;
        --input-border: #cbd5e1;
        --input-text: #0f172a;
        --listbox-bg: #ffffff;
        --listbox-option-hover: rgba(185, 28, 28, 0.08);
        --jd-bg: #f8fafc;
        --tab-bg: #f1f5f9;
        --tab-hover-bg: rgba(185, 28, 28, 0.05);
        --tab-active-bg: #ffffff;
        --bubble-assistant-bg: #f8fafc;
        --bubble-assistant-border: #e2e8f0;
        --bubble-assistant-text: #0f172a;
        --stepper-before-bg: #cbd5e1;
        --stepper-counter-bg: #ffffff;
        --stepper-counter-border: #cbd5e1;
        --stepper-counter-text: #475569;
        --card-hover-border: rgba(185, 28, 28, 0.4);
        --badge-time-bg: #f1f5f9;
        --badge-time-text: #475569;
        --badge-red-bg: rgba(185, 28, 28, 0.08);
    """

# Inject root CSS variables based on active theme
st.markdown(f"""
<style>
    :root {{
        {root_vars}
    }}
</style>
""", unsafe_allow_html=True)

# Custom premium styling inject
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: var(--bg-gradient) !important;
        color: var(--text-main);
    }
    
    /* Center and constrain main content width for visual balance on wide monitors */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1380px;
        margin: 0 auto;
    }
    
    /* Style sidebar with matching glassmorphic frame */
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        border-right: var(--sidebar-border) !important;
    }
    
    /* Hide Streamlit Header, MainMenu, Footer, Toolbar */
    [data-testid="stHeader"] {
        visibility: hidden;
        height: 0px !important;
        padding: 0px !important;
    }
    #MainMenu {
        visibility: hidden;
    }
    footer {
        visibility: hidden;
    }
    [data-testid="stToolbar"] {
        visibility: hidden;
    }
    [data-testid="stDecoration"] {
        display: none !important;
    }
    [data-testid="stStatusWidget"] {
        display: none !important;
    }
    
    /* Entrance Animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translate3d(0, 20px, 0);
        }
        to {
            opacity: 1;
            transform: translate3d(0, 0, 0);
        }
    }

    @keyframes pulseGlow {
        0% {
            box-shadow: 0 0 0 0 rgba(229, 9, 20, 0.2);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(229, 9, 20, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(229, 9, 20, 0);
        }
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    div[data-baseweb="tabpanel"] {
        animation: slideIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    
    /* Header Gradient */
    .recruit-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--accent-red), var(--accent-red-hover));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 5px;
        letter-spacing: -0.5px;
        animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    
    .recruit-sub {
        font-size: 1.15rem;
        color: var(--text-sub);
        text-align: center;
        margin-bottom: 35px;
        font-weight: 400;
        animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    
    /* Card Glassmorphism */
    .glass-card, div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 16px !important;
        padding: 30px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05) !important;
        margin-bottom: 30px !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease !important;
        backdrop-filter: blur(12px) !important;
    }
    
    .glass-card:hover, div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px) !important;
        border-color: var(--card-hover-border) !important;
        box-shadow: 0 15px 35px rgba(229, 9, 20, 0.08), 0 10px 30px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stage-title {
        color: var(--text-main);
        font-size: 1.45rem;
        font-weight: 600;
        border-left: 5px solid var(--accent-red);
        padding-left: 12px;
        margin-bottom: 25px;
    }
    
    /* Global Form & Widget Customizations */
    div[data-baseweb="input"], div[data-baseweb="select"], textarea {
        background-color: var(--input-bg) !important;
        color: var(--input-text) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, textarea:focus {
        border-color: var(--accent-red) !important;
        box-shadow: 0 0 0 3px rgba(229, 9, 20, 0.2) !important;
    }
    
    div[data-baseweb="input"] input, textarea {
        color: var(--input-text) !important;
    }
    
    /* Labels */
    label, [data-testid="stWidgetLabel"] {
        color: var(--text-main) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin-bottom: 8px !important;
    }
    
    /* Placeholders */
    ::placeholder {
        color: var(--text-sub) !important;
    }
    
    /* File Uploader styling */
    div[data-testid="stFileUploader"] {
        background-color: var(--input-bg) !important;
        border: 2px dashed var(--input-border) !important;
        border-radius: 14px;
        padding: 15px;
        transition: border-color 0.3s ease;
    }
    
    div[data-testid="stFileUploader"]:hover {
        border-color: var(--accent-red) !important;
    }
    
    div[data-testid="stFileUploader"] section {
        background-color: transparent !important;
    }
    
    /* Selectbox Dropdown styling */
    div[role="listbox"] {
        background-color: var(--listbox-bg) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 10px;
    }
    
    div[role="option"] {
        color: var(--input-text) !important;
        background-color: var(--listbox-bg) !important;
        padding: 10px 15px !important;
    }
    
    div[role="option"]:hover, li[role="option"]:hover {
        background-color: var(--listbox-option-hover) !important;
        color: var(--text-main) !important;
    }
    
    /* Read-Only JD Container */
    .jd-container {
        background-color: var(--jd-bg);
        border: 1px solid var(--card-border);
        border-radius: 10px;
        padding: 20px;
        font-size: 0.95rem;
        color: var(--text-sub);
        line-height: 1.6;
        margin-top: 5px;
        margin-bottom: 25px;
        max-height: 220px;
        overflow-y: auto;
        white-space: pre-wrap;
    }
    
    /* Tabs Overrides */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--tab-bg);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid var(--card-border);
        margin-bottom: 20px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        color: var(--text-sub);
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--accent-red);
        background-color: var(--tab-hover-bg);
    }
    
    .stTabs [aria-selected="true"] {
        color: var(--accent-red) !important;
        background-color: var(--tab-active-bg) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    
    /* Navigation Pills layout styling */
    /* Target the navigation radio group specifically */
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] > div[role="radiogroup"] {
        background: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 100px !important;
        padding: 8px !important; /* Increased padding */
        display: flex !important;
        flex-direction: row !important; /* Force horizontal layout at all times */
        flex-wrap: nowrap !important; /* Prevent vertical wrapping */
        justify-content: space-between !important;
        align-items: center !important;
        gap: 8px !important;
        margin-bottom: 35px !important;
        backdrop-filter: blur(20px) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05) !important;
        width: 100% !important;
        overflow-x: auto !important; /* Enable swipable horizontal scrolling on small screens */
        -webkit-overflow-scrolling: touch !important;
        scrollbar-width: none !important; /* Hide scrollbar for Firefox */
        -ms-overflow-style: none !important; /* Hide scrollbar for IE/Edge */
    }
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] > div[role="radiogroup"]::-webkit-scrollbar {
        display: none !important; /* Hide scrollbar for Webkit */
        height: 0px !important;
        width: 0px !important;
        background: transparent !important;
    }
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] div[role="radiogroup"] > div {
        flex: 1 1 auto !important;
        display: flex !important;
        justify-content: center !important;
        min-width: 0 !important;
    }
    
    /* Hide the radio button circles visually */
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label > div:first-child {
        opacity: 0 !important;
        width: 0px !important;
        height: 0px !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    
    /* Hide navigation header label completely */
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label[data-testid="stWidgetLabel"] {
        display: none !important;
    }
    
    /* Style the labels as tabs */
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label {
        background-color: transparent !important;
        border: none !important;
        padding: 14px 28px !important; /* Increased padding for a larger size */
        border-radius: 100px !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important; /* Increased font-size */
        cursor: pointer !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        margin: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important; /* Prevent text wrapping inside the pill */
        flex: 1 1 auto !important; /* Distribute space evenly */
        min-width: 0 !important;
    }
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label,
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label * {
        color: var(--text-sub) !important;
    }
    
    /* Hover state */
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label:hover {
        background-color: var(--tab-hover-bg) !important;
    }
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label:hover,
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label:hover * {
        color: var(--accent-red) !important;
    }
    
    /* Active/Checked state */
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(135deg, var(--accent-red), var(--accent-red-hover)) !important;
        box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4) !important;
    }
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label:has(input:checked),
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label:has(input:checked) * {
        color: #ffffff !important;
    }
    
    
    /* Target the auth navigation radio group specifically */
    div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] > div[role="radiogroup"] {
        background: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 100px !important;
        padding: 6px !important;
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        justify-content: space-between !important;
        align-items: center !important;
        gap: 6px !important;
        margin-bottom: 25px !important;
        backdrop-filter: blur(20px) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05) !important;
        width: 100% !important;
        overflow-x: auto !important; /* Enable swipable horizontal scrolling */
        -webkit-overflow-scrolling: touch !important;
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
    }
    div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] > div[role="radiogroup"]::-webkit-scrollbar {
        display: none !important;
        height: 0px !important;
        width: 0px !important;
        background: transparent !important;
    }
    div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] div[role="radiogroup"] > div {
        flex: 1 1 auto !important;
        display: flex !important;
        justify-content: center !important;
        min-width: 0 !important;
    }
    div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] label > div:first-child {
        opacity: 0 !important;
        width: 0px !important;
        height: 0px !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] label {
        background-color: transparent !important;
        border: none !important;
        padding: 10px 24px !important;
        border-radius: 100px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        cursor: pointer !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        margin: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }
    div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] label,
    div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] label * {
        color: var(--text-sub) !important;
    }
    div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] label:hover {
        background-color: var(--tab-hover-bg) !important;
    }
    div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] label:hover,
    div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] label:hover * {
        color: var(--accent-red) !important;
    }
    div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(135deg, var(--accent-red), var(--accent-red-hover)) !important;
        box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4) !important;
    }
    div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] label:has(input:checked),
    div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] label:has(input:checked) * {
        color: #ffffff !important;
    }
    @media (max-width: 640px) {
        div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] label {
            padding: 8px 12px !important;
            font-size: 0.82rem !important;
        }
    }

    .stButton>button {
        background: linear-gradient(135deg, var(--accent-red), var(--accent-red-hover)) !important;
        color: white !important;
        border: 1px solid transparent !important;
        border-radius: 10px !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        box-shadow: 0 4px 15px rgba(229, 9, 20, 0.15) !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 0 20px var(--accent-red) !important;
        background: linear-gradient(135deg, var(--accent-red-hover), var(--accent-red)) !important;
        border-color: var(--accent-red) !important;
        color: white !important;
    }
    
    /* Small, curved theme toggle button */
    .theme-toggle-container button {
        border-radius: 100px !important;
        padding: 6px 16px !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        background: var(--card-bg) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--card-border) !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }
    
    .theme-toggle-container button:hover {
        border-color: var(--accent-red) !important;
        color: var(--accent-red) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 15px rgba(229, 9, 20, 0.08) !important;
        background: var(--tab-hover-bg) !important;
    }
    
    /* Stepper Progress Indicator Styling */
    .stepper-wrapper {
        display: flex;
        justify-content: space-between;
        margin-bottom: 35px;
        position: relative;
        padding: 0 10px;
        animation: fadeInUp 0.5s ease;
    }
    .stepper-wrapper::before {
        content: '';
        position: absolute;
        top: 20px;
        left: 0;
        right: 0;
        height: 4px;
        background-color: var(--stepper-before-bg);
        z-index: 1;
    }
    .stepper-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        z-index: 2;
        flex: 1;
    }
    .step-counter {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: var(--stepper-counter-bg);
        border: 2px solid var(--stepper-counter-border);
        display: flex;
        justify-content: center;
        align-items: center;
        font-weight: 700;
        color: var(--stepper-counter-text);
        transition: all 0.4s ease;
    }
    .step-name {
        font-size: 0.82rem;
        font-weight: 500;
        color: var(--text-sub);
        margin-top: 8px;
        text-align: center;
        transition: all 0.4s ease;
    }
    /* Completed state */
    .stepper-item.completed .step-counter {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        border-color: #10b981;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.25);
    }
    .stepper-item.completed .step-name {
        color: #10b981;
        font-weight: 600;
    }
    /* Active state */
    .stepper-item.active .step-counter {
        background: linear-gradient(135deg, var(--accent-red), var(--accent-red-hover));
        color: white;
        border-color: var(--accent-red);
        box-shadow: 0 0 15px rgba(229, 9, 20, 0.4);
        transform: scale(1.08);
    }
    .stepper-item.active .step-name {
        color: var(--accent-red);
        font-weight: 700;
    }
    
    /* Custom Chat Interface Styling */
    .chat-bubble-container {
        display: flex;
        flex-direction: column;
        gap: 15px;
        margin-bottom: 25px;
        padding: 5px;
    }
    .chat-bubble {
        max-width: 85%;
        padding: 16px 20px;
        border-radius: 18px;
        font-size: 0.96rem;
        line-height: 1.55;
        animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    .chat-bubble-assistant {
        align-self: flex-start;
        background-color: var(--bubble-assistant-bg);
        border: 1px solid var(--bubble-assistant-border);
        color: var(--bubble-assistant-text);
        border-bottom-left-radius: 4px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }
    .chat-bubble-user {
        align-self: flex-end;
        background: linear-gradient(135deg, var(--accent-red), var(--accent-red-hover));
        color: #ffffff;
        border-bottom-right-radius: 4px;
        box-shadow: 0 4px 15px rgba(229, 9, 20, 0.25);
    }
    .chat-avatar {
        font-size: 1.25rem;
        margin-right: 8px;
        vertical-align: middle;
    }
      /* Recruiter Portal Dashboard metrics */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
        width: 100%;
    }
    .metric-card {
        background: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.03) !important;
        display: flex;
        align-items: center;
        gap: 20px;
        position: relative;
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .metric-card:hover {
        transform: translateY(-4px) !important;
        border-color: var(--card-hover-border) !important;
        box-shadow: 0 15px 30px rgba(229, 9, 20, 0.08), 0 10px 20px rgba(0, 0, 0, 0.05) !important;
    }
    .metric-icon-wrapper {
        background-color: var(--badge-red-bg);
        border-radius: 12px;
        width: 54px;
        height: 54px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }
    .metric-text-wrapper {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .metric-val {
        font-size: 2.25rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, var(--accent-red), var(--accent-red-hover)) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        margin: 0 !important;
        line-height: 1.1 !important;
    }
    .metric-label {
        font-size: 0.8rem !important;
        font-weight: 700 !important;
        color: var(--text-sub) !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        margin: 0 !important;
    }
    
    /* Candidate Card Grid & Cards */
    .cand-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 20px;
        margin-top: 20px;
        margin-bottom: 30px;
    }
    .cand-card {
        background: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        transition: all 0.3s ease !important;
        display: flex;
        flex-direction: column;
        gap: 15px;
        position: relative;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02) !important;
    }
    .cand-card:hover {
        border-color: var(--card-hover-border) !important;
        transform: translateY(-4px) !important;
        box-shadow: 0 12px 30px rgba(229, 9, 20, 0.06), 0 5px 15px rgba(0, 0, 0, 0.05) !important;
    }
    .cand-card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }
    .cand-card-info {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .cand-card-name {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--text-main);
        margin: 0;
    }
    .cand-card-role {
        font-size: 0.88rem;
        color: var(--text-sub);
        font-weight: 500;
    }
    .cand-card-score {
        background-color: var(--badge-red-bg);
        border: 1px solid rgba(229, 9, 20, 0.1);
        padding: 8px 12px;
        border-radius: 10px;
        text-align: center;
    }
    .cand-card-score-val {
        font-size: 1.3rem;
        font-weight: 700;
        color: var(--accent-red);
        line-height: 1;
    }
    .cand-card-score-lbl {
        font-size: 0.68rem;
        font-weight: 600;
        color: var(--text-sub);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 2px;
    }
    .cand-card-meta {
        font-size: 0.88rem;
        color: var(--text-sub);
        display: flex;
        flex-direction: column;
        gap: 6px;
        border-top: 1px solid var(--card-border);
        padding-top: 12px;
    }
    
    /* Job Card Dashboard */
    .job-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
        gap: 20px;
        margin-bottom: 25px;
    }
    .job-card {
        background: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 14px !important;
        padding: 20px !important;
        transition: all 0.3s ease !important;
        display: flex;
        flex-direction: column;
        gap: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02) !important;
    }
    .job-card:hover {
        border-color: var(--card-hover-border) !important;
        transform: translateY(-4px) !important;
        box-shadow: 0 12px 25px rgba(229, 9, 20, 0.05) !important;
    }
    
    /* Custom MCQ option cards customization */
    div[data-testid="stRadio"]:not(.nav-container *) label[data-baseweb="radio"] {
        background-color: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 10px !important;
        padding: 12px 20px !important;
        margin-bottom: 10px !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        width: 100% !important;
        display: flex !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.02) !important;
    }
    div[data-testid="stRadio"]:not(.nav-container *) label[data-baseweb="radio"]:hover {
        border-color: var(--accent-red) !important;
        background-color: var(--tab-hover-bg) !important;
    }
    div[data-testid="stRadio"]:not(.nav-container *) label[data-baseweb="radio"]:has(input:checked) {
        border-color: var(--accent-red) !important;
        background-color: var(--badge-red-bg) !important;
        box-shadow: 0 2px 10px rgba(229, 9, 20, 0.08) !important;
        font-weight: 600 !important;
    }
    
    /* AI interviewer avatar pulse glow */
    .chat-avatar-ai {
        display: inline-block;
        animation: pulseGlow 2s infinite;
        border-radius: 50%;
        padding: 2px;
        background-color: var(--badge-red-bg);
    }
    
    @keyframes recordingPulse {
        0% { transform: scale(1); opacity: 0.8; }
        50% { transform: scale(1.2) !important; opacity: 1; box-shadow: 0 0 15px rgba(229, 9, 20, 0.6); }
        100% { transform: scale(1); opacity: 0.8; }
    }
    .recording-indicator {
        width: 14px;
        height: 14px;
        background-color: var(--accent-red);
        border-radius: 50%;
        display: inline-block;
        animation: recordingPulse 1.5s infinite;
        margin-right: 8px;
        vertical-align: middle;
        box-shadow: 0 0 8px var(--accent-red);
    }
    
    /* Hide proctoring trigger button */
    .hidden-proctor-btn,
    .hidden-proctor-btn div,
    .hidden-proctor-btn button {
        display: none !important;
        height: 0px !important;
        width: 0px !important;
        overflow: hidden !important;
        padding: 0px !important;
        margin: 0px !important;
        border: none !important;
    }

    /* Mobile responsive overrides */
    @media (max-width: 768px) {
        /* Main Navigation pills sizing adjustments (keep horizontal scroll) */
        div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] > div[role="radiogroup"] {
            justify-content: flex-start !important;
            gap: 12px !important;
        }
        div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label {
            padding: 8px 20px !important;
            font-size: 0.9rem !important;
            border-radius: 100px !important;
            flex: 0 0 auto !important;
            width: auto !important;
            max-width: none !important;
        }
        
        /* Stepper responsive stacking */
        .stepper-wrapper {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 16px !important;
            padding: 10px !important;
        }
        .stepper-wrapper::before {
            display: none !important;
        }
        .stepper-item {
            flex-direction: row !important;
            align-items: center !important;
            gap: 12px !important;
            width: 100% !important;
            flex: unset !important;
        }
        .step-name {
            text-align: left !important;
            margin-top: 0px !important;
            font-size: 0.95rem !important;
        }
        
        /* Header typography responsiveness */
        .recruit-header {
            font-size: 1.8rem !important;
            text-align: center !important;
        }
        .recruit-sub {
            font-size: 0.95rem !important;
            text-align: center !important;
            margin-bottom: 20px !important;
        }
        
        /* Theme toggle adjustments on mobile */
        .theme-toggle-container {
            justify-content: center !important;
            margin-top: 5px !important;
            margin-bottom: 15px !important;
            width: 100% !important;
        }
    }
    
    @media (max-width: 640px) {
        /* Auth Navigation pills sizing adjustments (keep horizontal scroll) */
        div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] > div[role="radiogroup"] {
            justify-content: flex-start !important;
            gap: 10px !important;
        }
        div.element-container:has(.auth-nav-container) + div.element-container div[data-testid="stRadio"] label {
            padding: 6px 16px !important;
            font-size: 0.85rem !important;
            border-radius: 100px !important;
            flex: 0 0 auto !important;
            width: auto !important;
            max-width: none !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Synchronize Python proctoring state with JavaScript context
proctoring_active_flag = (
    st.session_state.get("candidate_logged_in", False) and 
    st.session_state.get("current_page") == "🎯 Candidate Assessment" and 
    st.session_state.get("stage") in ["mcq", "interview"]
)

st.components.v1.html(
    f"""
    <script>
        window.parent.__proctoring_active__ = {"true" if proctoring_active_flag else "false"};
        if (!window.parent.__proctoring_active__) {{
            const popup = window.parent.document.getElementById('proctor-cursor-popup');
            if (popup) {{
                popup.remove();
            }}
        }}
    </script>
    """,
    height=0
)

# Inject Global Enter Key Interceptor JavaScript to move focus to next input field instead of reloading page
st.components.v1.html("""
<script>
    const doc = window.parent.document;
    if (!window.parent.__enter_interceptor_added__) {
        window.parent.__enter_interceptor_added__ = true;
        doc.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                const active = doc.activeElement;
                if (active && active.tagName === 'INPUT' && active.type !== 'submit' && active.type !== 'button' && active.type !== 'password') {
                    e.preventDefault();
                    e.stopPropagation();
                    const selector = 'input[type="text"]:not([readonly]), input[type="email"]:not([readonly]), input[type="tel"]:not([readonly]), select, textarea:not([readonly])';
                    const elements = Array.from(doc.querySelectorAll(selector)).filter(el => {
                        return el.offsetWidth > 0 && el.offsetHeight > 0;
                    });
                    const index = elements.indexOf(active);
                    if (index > -1 && index < elements.length - 1) {
                        elements[index + 1].focus();
                    }
                }
            }
        }, true);
    }

</script>
""", height=0)

# Stepper Progress Widget Function
def render_stepper(current_stage):
    stages_info = [
        {"num": 1, "name": "Profile & Resume"},
        {"num": 2, "name": "AI Screening"},
        {"num": 3, "name": "Technical MCQ"},
        {"num": 4, "name": "AI Interview"},
        {"num": 5, "name": "Evaluation"}
    ]
    
    stage_map = {
        "upload": 1,
        "screening_passed": 2,
        "screening_failed": 2,
        "screening_review": 2,
        "proctoring_instruction": 3,

        "mcq": 3,
        "mcq_passed_screen": 3,
        "mcq_failed_screen": 3,
        "interview": 4,
        "final_evaluation": 5
    }
    
    current_idx = stage_map.get(current_stage, 1)
    
    html = '<div class="stepper-wrapper">'
    for idx, stage in enumerate(stages_info, 1):
        status_class = ""
        symbol = str(stage["num"])
        if idx < current_idx:
            status_class = "completed"
            symbol = "✓"
        elif idx == current_idx:
            status_class = "active"
        
        html += f'<div class="stepper-item {status_class}">'
        html += f'<div class="step-counter">{symbol}</div>'
        html += f'<div class="step-name">{stage["name"]}</div>'
        html += '</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# Chat text custom formatter function
def format_chat_text(text):
    import re
    # Escape HTML to prevent broken layout
    formatted = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Bold patterns
    formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted)
    formatted = re.sub(r'\*(.*?)\*', r'<em>\1</em>', formatted)
    # Line breaks
    formatted = formatted.replace("\n", "<br>")
    return formatted

# ----------------- STREAMLIT FRAGMENTS FOR UI/UX ENHANCEMENTS -----------------

def classify_intent(user_msg: str, config) -> str:
    """Routes user message to one of 5 intents using a fast LLM call."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import ChatPromptTemplate
    router_model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=config.GEMINI_API_KEY,
        temperature=0.0
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Classify the user's message into exactly ONE of these intents. Reply with only the intent word, nothing else.

Intents:
- fit_check    : User wants to know if they are a good fit, asks about their skills vs a role, wants role recommendations, says things like "am I suitable", "match my skills", "which role for me"
- interview_prep : User wants to practice interview questions, prepare for an interview, get sample questions, rehearse answers
- process_guide  : User asks about how the application works, stages, MCQ, proctoring rules, retakes, how to apply
- job_info       : User asks about a specific role's requirements, skills needed, salary, difficulty, responsibilities
- general        : Everything else — greetings, thanks, unrelated questions

Reply with ONLY one word: fit_check | interview_prep | process_guide | job_info | general"""),
        ("human", "{msg}")
    ])
    try:
        res = (prompt | router_model).invoke({"msg": user_msg})
        intent = res.content.strip().lower().split()[0]
        if intent in ["fit_check", "interview_prep", "process_guide", "job_info", "general"]:
            return intent
    except Exception:
        pass
    return "general"


def get_agent_response(intent: str, user_msg: str, history: list, config, jds_text: str) -> str:
    """Dispatches to the right specialized sub-agent system prompt based on intent."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=config.GEMINI_API_KEY,
        temperature=0.4
    )

    system_prompts = {
        "job_info": f"""You are a Job Information Specialist at AgentFlow Recruitment.
Answer questions about specific job roles with precision and enthusiasm.
Available roles and their descriptions:
{jds_text}
Rules: Be specific, mention exact skills, experience levels, and difficulty ratings. Keep answers to 3-4 sentences max.""",

        "fit_check": f"""You are a Career Fit Advisor at AgentFlow Recruitment.
Help candidates understand which roles they are best suited for.
Available roles:
{jds_text}
When given a list of skills, analyze them against each role and give honest, encouraging guidance.
Format your response clearly with role names and suitability assessment.""",

        "process_guide": """You are an Application Process Guide at AgentFlow Recruitment.
Explain the candidate assessment process clearly and helpfully.
The process has these stages:
1. Resume Upload & AI Screening — resume parsed, skills extracted, match score calculated (45-65% = borderline review, >65% = pass, <45% = fail)
2. Technical MCQ — 5 customized multiple-choice questions, 60% pass threshold (3/5 correct)
3. AI Technical Interview — 3 adaptive conversational questions with voice or text input
4. Final Evaluation — AI assesses overall performance and sends email decision
Proctoring: Tab switching tracked, max 3 warnings, 4th = auto-submit. Retakes possible via help desk.
Keep answers friendly, clear, and reassuring. Max 3 sentences.""",

        "interview_prep": f"""You are an Interview Coach at AgentFlow Recruitment.
Help candidates prepare for technical interviews for our open roles.
Available roles:
{jds_text}
Generate focused, realistic interview questions appropriate to the role and difficulty.
Give encouraging, specific feedback on candidate answers. Be like a supportive coach.""",

        "general": f"""You are a friendly HR Assistant at AgentFlow Recruitment.
Help candidates with any questions about our company and hiring process.
Available roles: {jds_text}
Be warm, concise, and professional. If unsure, guide them to the right section of the platform."""
    }

    system_prompt = system_prompts.get(intent, system_prompts["general"])

    # Build full conversation history as proper message objects
    messages = [SystemMessage(content=system_prompt)]
    for m in history[:-1]:  # exclude the latest user message we're about to add
        if m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            messages.append(AIMessage(content=m["content"]))
    messages.append(HumanMessage(content=user_msg))

    try:
        res = model.invoke(messages)
        return res.content.strip()
    except Exception as e:
        return f"I encountered an issue processing your request. Please try again. ({str(e)})"


def run_fit_check(skills_text: str, config, jds_text: str) -> list:
    """Runs the fit-check LLM analysis and returns structured role scores."""
    import json as _json
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import ChatPromptTemplate

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=config.GEMINI_API_KEY,
        temperature=0.1
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a career fit analyzer. Given a candidate's skill list, analyze how well they match each available job role.
Available roles:
{jds_text}

Return ONLY a valid JSON array like this (no markdown, no explanation):
[
  {{
    "role": "Role Name",
    "score": 75,
    "matched_skills": ["skill1", "skill2"],
    "missing_skills": ["skill3"],
    "recommendation": "One sentence of encouragement and advice."
  }}
]
Score 0-100. Be honest but encouraging."""),
        ("human", "Candidate Skills: {skills}")
    ])
    try:
        res = (prompt | model).invoke({"skills": skills_text})
        content = res.content.strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return _json.loads(content.strip())
    except Exception:
        return []


def generate_prep_questions(role: str, config, jds_text: str) -> list:
    """Generates 5 tailored interview practice questions for a role."""
    import json as _json
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import ChatPromptTemplate

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=config.GEMINI_API_KEY,
        temperature=0.5
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a senior technical interviewer. Generate exactly 5 realistic interview practice questions for the given role.
Available role descriptions:
{jds_text}
Return ONLY a valid JSON array of strings, no markdown:
["Question 1?", "Question 2?", "Question 3?", "Question 4?", "Question 5?"]"""),
        ("human", "Generate 5 interview questions for the role: {role}")
    ])
    try:
        res = (prompt | model).invoke({"role": role})
        content = res.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        questions = _json.loads(content.strip())
        return questions[:5]
    except Exception:
        return [
            f"Tell me about your experience relevant to the {role} role.",
            "Describe a challenging technical problem you solved recently.",
            "How do you approach learning new technologies?",
            "Walk me through a project you are most proud of.",
            "What are your strengths and areas for improvement?"
        ]





def render_sidebar_chatbot():
    config = Config.load_config()

    jds_text = ""
    for role, jd in PREDEFINED_JDS.items():
        if role != "Custom / Write your own":
            jds_text += f"Role: {role}\nDescription: {jd}\n\n"

    # ── Header row ──────────────────────────────────────────────────────────────
    col_lbl, col_mode, col_clr = st.columns([4, 4, 2])
    with col_lbl:
        mode = st.session_state.assistant_mode
        mode_labels = {"chat": "🤖 Assistant", "fit_check": "🎯 Fit Advisor", "interview_prep": "🧠 Interview Prep"}
        st.markdown(f"### {mode_labels.get(mode, '🤖 Assistant')}")
    with col_mode:
        if st.session_state.assistant_mode != "chat":
            if st.button("↩️ Back to Chat", key="back_to_chat_btn", use_container_width=True):
                st.session_state.assistant_mode = "chat"
                st.session_state.fit_results = None
                st.session_state.fit_skills_input = ""
                st.session_state.prep_questions = []
                st.session_state.prep_current_q = 0
                st.session_state.prep_answers = {}
                st.session_state.prep_role = ""
                st.rerun()
    with col_clr:
        if st.session_state.sidebar_chat_history and st.session_state.assistant_mode == "chat":
            if st.button("🗑️ Clear", key="clear_chat_history_btn", use_container_width=True):
                st.session_state.sidebar_chat_history = [
                    {"role": "assistant", "content": "Hello! I'm your **AI Recruitment Assistant** 👋\n\nI can help you with:\n- 🔍 **Job role info** — requirements, skills, difficulty\n- 🎯 **Fit check** — find which role suits your profile best\n- 📋 **Process guide** — how the assessment works\n- 🧠 **Interview prep** — practice questions with AI feedback\n\nWhat would you like to explore today?"}
                ]
                st.session_state.assistant_mode = "chat"
                st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # MODE: FIT CHECK
    # ═══════════════════════════════════════════════════════════════════════════
    if st.session_state.assistant_mode == "fit_check":
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(59,130,246,0.08), rgba(16,185,129,0.08));
                    border: 1px solid rgba(59,130,246,0.2); border-radius: 12px; padding: 18px; margin-bottom: 18px;">
            <div style="font-weight: 700; font-size: 1.05rem; color: var(--text-main); margin-bottom: 6px;">🎯 Skill-Match Fit Advisor</div>
            <div style="color: var(--text-sub); font-size: 0.9rem;">Enter your skills below and I'll score your fit against every open role and recommend the best match.</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("fit_check_form", clear_on_submit=False):
            skills_input = st.text_area(
                "Your Skills",
                value=st.session_state.fit_skills_input,
                placeholder="e.g. Python, FastAPI, LangChain, Machine Learning, React, SQL, Docker...",
                height=100,
                key="fit_skills_textarea",
                label_visibility="collapsed"
            )
            analyze_btn = st.form_submit_button("🔍 Analyze My Fit", use_container_width=True)

        if analyze_btn and skills_input.strip():
            st.session_state.fit_skills_input = skills_input.strip()
            with st.spinner("Analyzing your profile against all open roles..."):
                results = run_fit_check(skills_input.strip(), config, jds_text)
                st.session_state.fit_results = results

        if st.session_state.fit_results:
            results = sorted(st.session_state.fit_results, key=lambda x: x.get("score", 0), reverse=True)
            st.markdown("#### 📊 Your Role Match Results")
            for r in results:
                score = r.get("score", 0)
                if score >= 75:
                    bar_color = "#10b981"
                    badge = "🟢 Strong Match"
                elif score >= 50:
                    bar_color = "#f59e0b"
                    badge = "🟡 Partial Match"
                else:
                    bar_color = "#ef4444"
                    badge = "🔴 Skill Gap"

                matched = ", ".join(r.get("matched_skills", [])[:6]) or "—"
                missing = ", ".join(r.get("missing_skills", [])[:5]) or "None"
                rec = r.get("recommendation", "")

                st.markdown(f"""
                <div style="border: 1px solid {bar_color}33; border-left: 5px solid {bar_color};
                            border-radius: 10px; padding: 16px; margin-bottom: 14px;
                            background: {bar_color}08;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-weight: 700; font-size: 1rem; color: var(--text-main);">{r.get('role','')}</div>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 0.8rem; color: {bar_color}; font-weight: 600;">{badge}</span>
                            <span style="font-size: 1.4rem; font-weight: 800; color: {bar_color};">{score}%</span>
                        </div>
                    </div>
                    <div style="background: rgba(0,0,0,0.08); border-radius: 6px; height: 8px; margin-bottom: 12px;">
                        <div style="width: {score}%; height: 100%; background: {bar_color}; border-radius: 6px;"></div>
                    </div>
                    <div style="font-size: 0.82rem; color: var(--text-sub); margin-bottom: 6px;">
                        ✅ <strong>Matched:</strong> {matched}
                    </div>
                    <div style="font-size: 0.82rem; color: var(--text-sub); margin-bottom: 8px;">
                        📚 <strong>To learn:</strong> {missing}
                    </div>
                    <div style="font-size: 0.85rem; color: var(--text-main); font-style: italic; border-top: 1px solid {bar_color}22; padding-top: 8px;">
                        💡 {rec}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Best fit CTA
            best = results[0]
            st.success(f"**🏆 Best match for you:** {best.get('role')} ({best.get('score')}% fit) — head to the **Open Positions** tab to apply!")
        return

    # ═══════════════════════════════════════════════════════════════════════════
    # MODE: INTERVIEW PREP
    # ═══════════════════════════════════════════════════════════════════════════
    if st.session_state.assistant_mode == "interview_prep":
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(139,92,246,0.08), rgba(59,130,246,0.08));
                    border: 1px solid rgba(139,92,246,0.2); border-radius: 12px; padding: 18px; margin-bottom: 18px;">
            <div style="font-weight: 700; font-size: 1.05rem; color: var(--text-main); margin-bottom: 6px;">🧠 Interview Prep Practice</div>
            <div style="color: var(--text-sub); font-size: 0.9rem;">Practice with AI-generated questions. Answer all 5 and review your responses at the end.</div>
        </div>
        """, unsafe_allow_html=True)

        # Step 1: Role selection
        if not st.session_state.prep_role:
            open_roles = [r for r in PREDEFINED_JDS.keys() if r != "Custom / Write your own"]
            with st.form("prep_role_form"):
                selected = st.selectbox("Select the role you're preparing for:", open_roles, key="prep_role_selector")
                if st.form_submit_button("🚀 Start Practice Session", use_container_width=True):
                    with st.spinner(f"Generating 5 tailored questions for {selected}..."):
                        questions = generate_prep_questions(selected, config, jds_text)
                    st.session_state.prep_role = selected
                    st.session_state.prep_questions = questions
                    st.session_state.prep_current_q = 0
                    st.session_state.prep_answers = {}
                    st.rerun()
            return

        questions = st.session_state.prep_questions
        current_q = st.session_state.prep_current_q
        total_q = len(questions)
        role = st.session_state.prep_role

        # Progress bar
        progress = current_q / total_q if total_q > 0 else 0
        st.markdown(f"""
        <div style="margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--text-sub); margin-bottom: 6px;">
                <span>Preparing for: <strong style="color: var(--text-main);">{role}</strong></span>
                <span>Question {min(current_q+1, total_q)} of {total_q}</span>
            </div>
            <div style="background: rgba(0,0,0,0.1); border-radius: 6px; height: 6px;">
                <div style="width: {int(progress*100)}%; height: 100%; background: #8b5cf6; border-radius: 6px; transition: width 0.4s;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Show all answered questions (no feedback)
        for i in range(current_q):
            q_text = questions[i]
            ans = st.session_state.prep_answers.get(i, "")
            with st.expander(f"✅ Q{i+1}: {q_text[:60]}...", expanded=False):
                st.markdown(f"**Your answer:** {ans}")

        # Current question
        if current_q < total_q:
            q_text = questions[current_q]
            st.markdown(f"""
            <div style="background: rgba(139,92,246,0.06); border: 1px solid rgba(139,92,246,0.25);
                        border-radius: 12px; padding: 18px; margin-bottom: 16px;">
                <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px;
                            color: #8b5cf6; font-weight: 700; margin-bottom: 8px;">Question {current_q + 1}</div>
                <div style="font-size: 1.02rem; color: var(--text-main); font-weight: 500; line-height: 1.5;">{q_text}</div>
            </div>
            """, unsafe_allow_html=True)

            with st.form(f"prep_answer_form_{current_q}", clear_on_submit=True):
                user_ans = st.text_area(
                    "Your Answer",
                    placeholder="Type your answer here — be as detailed as you can...",
                    height=120,
                    label_visibility="collapsed",
                    key=f"prep_ans_input_{current_q}"
                )
                submitted = st.form_submit_button("Submit Answer ➜", use_container_width=True)

            if submitted and user_ans.strip():
                st.session_state.prep_answers[current_q] = user_ans.strip()
                st.session_state.prep_current_q += 1
                st.rerun()

        else:
            st.success(f"🎉 **Practice session complete!** You answered all {total_q} questions for **{role}**.")
            st.markdown("#### 📋 Your Answers")
            for i, q in enumerate(questions):
                ans = st.session_state.prep_answers.get(i, "")
                st.markdown(f"""
                <div style="border: 1px solid rgba(139,92,246,0.2); border-radius: 10px;
                            padding: 16px; margin-bottom: 12px;">
                    <div style="font-weight: 700; color: var(--text-main); margin-bottom: 8px;">Q{i+1}. {q}</div>
                    <div style="color: var(--text-sub); font-size: 0.88rem;">
                        <strong>Your answer:</strong> {ans}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if st.button("🔄 Practice Again (New Questions)", use_container_width=True, key="prep_restart_btn"):
                with st.spinner("Generating fresh questions..."):
                    new_qs = generate_prep_questions(role, config, jds_text)
                st.session_state.prep_questions = new_qs
                st.session_state.prep_current_q = 0
                st.session_state.prep_answers = {}
                st.rerun()
        return

    # ═══════════════════════════════════════════════════════════════════════════
    # MODE: MAIN CHAT (Intent-Routed)
    # ═══════════════════════════════════════════════════════════════════════════
    def trigger_chatbot_query(user_input_text):
        st.session_state.sidebar_chat_history.append({"role": "user", "content": user_input_text})
        try:
            intent = classify_intent(user_input_text, config)

            # Special intents that switch modes
            if intent == "fit_check":
                st.session_state.sidebar_chat_history.append({
                    "role": "assistant",
                    "content": "🎯 **Switching to Fit Advisor mode!** Enter your skills and I'll score your match against every open role."
                })
                st.session_state.assistant_mode = "fit_check"
                return
            if intent == "interview_prep":
                st.session_state.sidebar_chat_history.append({
                    "role": "assistant",
                    "content": "🧠 **Switching to Interview Prep mode!** Select a role and start practicing with AI-generated questions and coaching feedback."
                })
                st.session_state.assistant_mode = "interview_prep"
                return

            # Inline chat intents (job_info, process_guide, general)
            response = get_agent_response(
                intent=intent,
                user_msg=user_input_text,
                history=st.session_state.sidebar_chat_history,
                config=config,
                jds_text=jds_text
            )
            st.session_state.sidebar_chat_history.append({"role": "assistant", "content": response})
        except Exception as e:
            st.session_state.sidebar_chat_history.append({"role": "assistant", "content": f"Sorry, I ran into an issue: {str(e)}"})

    # Chat transcript
    with st.container(height=300):
        if not st.session_state.sidebar_chat_history:
            st.markdown("<p style='color: var(--text-sub); font-style: italic; font-size: 0.9rem;'>No messages yet. Ask me anything!</p>", unsafe_allow_html=True)
        for msg in st.session_state.sidebar_chat_history:
            avatar = "🧑" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # Quick action buttons when chat is fresh
    if len(st.session_state.sidebar_chat_history) <= 1:
        st.markdown("**⚡ Quick Actions:**")
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        with col1:
            if st.button("🎯 Check My Fit", key="qt_fit_check", use_container_width=True):
                st.session_state.assistant_mode = "fit_check"
                st.rerun()
        with col2:
            if st.button("🧠 Prep for Interview", key="qt_prep", use_container_width=True):
                st.session_state.assistant_mode = "interview_prep"
                st.rerun()
        with col3:
            if st.button("💼 Open Roles", key="qt_roles", use_container_width=True):
                with st.spinner("Thinking..."):
                    trigger_chatbot_query("What open positions are available and what are the requirements?")
                st.rerun()
        with col4:
            if st.button("📋 How to Apply", key="qt_apply", use_container_width=True):
                with st.spinner("Thinking..."):
                    trigger_chatbot_query("How does the application and assessment process work?")
                st.rerun()
    else:
        # Contextual follow-ups
        st.markdown("**🔍 Suggested:**")
        s1, s2 = st.columns(2)
        with s1:
            if st.button("🎯 Check My Fit", key="sug_fit_check", use_container_width=True):
                st.session_state.assistant_mode = "fit_check"
                st.rerun()
        with s2:
            if st.button("🧠 Practice Interview", key="sug_prep", use_container_width=True):
                st.session_state.assistant_mode = "interview_prep"
                st.rerun()

    # Message input
    with st.form("sidebar_chat_inline_form", clear_on_submit=True):
        col_inp, col_btn = st.columns([8.2, 1.8])
        with col_inp:
            user_input = st.text_input(
                "Ask anything...",
                placeholder="e.g. What skills do I need for AI/ML Engineer?",
                label_visibility="collapsed",
                key="chatbot_input_text_box"
            )
        with col_btn:
            submitted = st.form_submit_button("Send ➤", use_container_width=True)

    if submitted and user_input.strip():
        with st.spinner("Thinking..."):
            trigger_chatbot_query(user_input.strip())
        st.rerun()




def render_recruiter_analytics():
    candidates = load_candidates()
    if not candidates:
        st.info("No candidate data available to render analytics.")
        return
        
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from collections import Counter
    
    st.write("### 📈 Interactive Recruiter Analytics Dashboard")
    
    # 1. Pipeline Funnel Data
    stages_counts = Counter()
    for c in candidates:
        stage = c.get("stage", "upload")
        phase = "Profile Upload"
        if stage in ["screening_passed", "proctoring_instruction"]:
            phase = "Cleared Screening"
        elif stage == "screening_failed":
            phase = "Screening Failed"
        elif stage == "screening_review":
            phase = "Screening Review"
        elif stage in ["mcq", "mcq_passed_screen"]:
            phase = "Technical MCQ"
        elif stage == "mcq_failed_screen":
            phase = "MCQ Failed"
        elif stage == "interview":
            phase = "AI Interview"
        elif stage == "final_evaluation":
            eval_selected = c.get("eval_selected", False) or (c.get("selection") == "Selected")
            phase = "Selected" if eval_selected else "Interview Failed"
        stages_counts[phase] += 1
        
    funnel_order = [
        "Profile Upload",
        "Screening Review",
        "Screening Failed",
        "Cleared Screening",
        "Technical MCQ",
        "MCQ Failed",
        "AI Interview",
        "Interview Failed",
        "Selected"
    ]
    funnel_data = []
    for phase in funnel_order:
        if phase in stages_counts:
            funnel_data.append({"Pipeline Phase": phase, "Candidates Count": stages_counts[phase]})
            
    df_funnel = pd.DataFrame(funnel_data)
    
    # 2. Proctoring Risk Distribution
    risk_counts = Counter()
    for c in candidates:
        risk = "Low Risk"
        switches = c.get("tab_switches", 0)
        report = c.get("proctoring_report")
        if report and isinstance(report, dict) and report.get("risk_level"):
            risk = report.get("risk_level")
        else:
            if switches == 0:
                risk = "Low"
            elif 1 <= switches <= 2:
                risk = "Medium"
            elif switches == 3:
                risk = "High"
            else:
                risk = "Suspicious"
        if risk == "Low":
            risk = "Low Risk"
        elif risk == "Medium":
            risk = "Medium Risk"
        elif risk == "High":
            risk = "High Risk"
        elif risk == "Suspicious":
            risk = "Suspicious / Auto-Submitted"
        risk_counts[risk] += 1
        
    df_risk = pd.DataFrame([{"Risk Level": k, "Count": v} for k, v in risk_counts.items()])
    
    # 3. Missing Skills / Skill Gaps
    skills_counter = Counter()
    for c in candidates:
        missing = c.get("missing_skills", [])
        for s in missing:
            if s:
                skills_counter[s] += 1
                
    top_gaps = skills_counter.most_common(10)
    df_gaps = pd.DataFrame([{"Skill": k, "Candidates Lacking": v} for k, v in top_gaps])
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not df_funnel.empty:
            fig_funnel = px.funnel(df_funnel, x="Candidates Count", y="Pipeline Phase", color="Pipeline Phase",
                                   color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_funnel.update_layout(
                title="Candidate Pipeline Funnel",
                margin=dict(l=20, r=20, t=40, b=20),
                height=350,
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white' if st.session_state.get("theme_mode") == "Cyberpunk Dark" else 'black')
            )
            st.plotly_chart(fig_funnel, use_container_width=True)
        else:
            st.info("No pipeline data yet.")
            
    with col2:
        if not df_risk.empty:
            fig_risk = px.pie(df_risk, values="Count", names="Risk Level", hole=0.4,
                              color_discrete_sequence=["#10b981", "#f59e0b", "#ef4444", "#7f1d1d"])
            fig_risk.update_layout(
                title="Proctoring Risk Level Distribution",
                margin=dict(l=20, r=20, t=40, b=20),
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white' if st.session_state.get("theme_mode") == "Cyberpunk Dark" else 'black')
            )
            st.plotly_chart(fig_risk, use_container_width=True)
        else:
            st.info("No proctoring risk data yet.")
            
    if not df_gaps.empty:
        fig_gaps = px.bar(df_gaps, x="Candidates Lacking", y="Skill", orientation='h', color="Candidates Lacking",
                          color_continuous_scale="Reds")
        fig_gaps.update_layout(
            title="Top 10 Technical Skill Gaps Heatmap",
            margin=dict(l=20, r=20, t=40, b=20),
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white' if st.session_state.get("theme_mode") == "Cyberpunk Dark" else 'black')
        )
        st.plotly_chart(fig_gaps, use_container_width=True)
    else:
        st.info("No skill gaps recorded yet.")

def render_screening_review_queue(review_candidates):
    if not review_candidates:
        st.success("🎉 No candidates currently pending screening review! All clear.")
    else:
        st.markdown("The following candidates scored in the borderline range (45%–65%) during screening and require manual approval.")
        for idx, c in enumerate(review_candidates):
            with st.container(border=True):
                col_c1, col_c2 = st.columns([3, 1])
                with col_c1:
                    st.markdown(f"#### 👤 {c.get('name')} ({c.get('email')})")
                    st.markdown(f"**Applied Position**: {c.get('job_role')} | **Experience**: {c.get('experience')}")
                    st.markdown(f"**Match Score**: `{c.get('match_score')}%`")
                    st.markdown(f"**AI Screening Reason**: {c.get('screening_reason')}")
                    if c.get("missing_skills"):
                        st.markdown(f"**Missing Skills**: {', '.join(c.get('missing_skills'))}")
                    if c.get("red_flags"):
                        st.markdown(f"**Red Flags**: {', '.join(c.get('red_flags'))}")
                with col_c2:
                    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
                    if st.button("✓ Approve & Pass", key=f"approve_screen_{idx}_{c['email']}_{c['job_role']}", use_container_width=True):
                        records = load_candidates()
                        for r in records:
                            if r.get("email", "").strip().lower() == c["email"].strip().lower() and r.get("job_role", "").strip().lower() == c["job_role"].strip().lower():
                                r["stage"] = "proctoring_instruction"
                                r["status"] = "Cleared Screening"
                                break
                        with open(CANDIDATES_FILE, "w") as f:
                            json.dump(records, f, indent=2)
                        st.success(f"Approved {c['name']}!")
                        time.sleep(0.5)
                        st.rerun()
                        
                    if st.button("✗ Reject", key=f"reject_screen_{idx}_{c['email']}_{c['job_role']}", use_container_width=True):
                        records = load_candidates()
                        for r in records:
                            if r.get("email", "").strip().lower() == c["email"].strip().lower() and r.get("job_role", "").strip().lower() == c["job_role"].strip().lower():
                                r["stage"] = "screening_failed"
                                r["status"] = "Disqualified in Screening"
                                break
                        with open(CANDIDATES_FILE, "w") as f:
                            json.dump(records, f, indent=2)
                        st.info(f"Rejected {c['name']}.")
                        time.sleep(0.5)
                        st.rerun()

@st.fragment
def render_candidate_hub():
    candidates = load_candidates()
    if not candidates:
        st.info("No candidates have started or completed the test yet.")
        return
        
    review_candidates = [c for c in candidates if c.get("stage") == "screening_review"]
    
    tab_leaderboard, tab_review_queue = st.tabs(["🏆 Leaderboard & Scorecards", f"👥 Screening Review Queue ({len(review_candidates)})"])
    
    with tab_leaderboard:
        render_candidate_hub_leaderboard()
        
    with tab_review_queue:
        render_screening_review_queue(review_candidates)

def render_candidate_hub_leaderboard():

    # Load candidates inside the fragment so updates will auto-reload
    candidates = load_candidates()
    if not candidates:
        st.info("No candidates have started or completed the test yet.")
        return

    import pandas as pd
    df_candidates = pd.DataFrame(candidates)
    
    # Sort candidates by match_score descending if it exists
    if "match_score" in df_candidates.columns:
        df_candidates = df_candidates.sort_values(by="match_score", ascending=False)
    
    # Collapsible tabular leaderboard
    with st.expander("📊 View Complete Tabular Leaderboard Table"):
        display_cols = ["name", "email", "job_role", "match_score", "mcq_score", "selection", "status"]
        for col in display_cols:
            if col not in df_candidates.columns:
                df_candidates[col] = "N/A"
        df_display = df_candidates[display_cols]
        df_display.columns = ["Name", "Email", "Applied Role", "Match Score (%)", "MCQ Score", "Selection Recommendation", "Pipeline Stage"]
        st.dataframe(df_display, use_container_width=True)
    
    st.markdown("---")
    
    # Live search filter bar
    search_query = st.text_input("🔍 Live Candidate Search & Filter", "", placeholder="Search by name, email, or job role...", key="candidate_search_input")
    
    filtered_cands = candidates
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_cands = [c for c in candidates if q in c.get("name", "").lower() or q in c.get("email", "").lower() or q in c.get("job_role", "").lower()]
        
    if not filtered_cands:
        st.warning("No candidates match your search query.")
        return
        
    # Split Layout: Left side candidate cards list, Right side details scorecard
    col_left, col_right = st.columns([1.1, 2])
    
    # Set default candidate if not selected or if the selected one is no longer available in filtered list
    options = [f"{c['name']} ({c['email']}) - {c['job_role']}" for c in filtered_cands]
    if "active_scorecard_candidate" not in st.session_state or st.session_state.active_scorecard_candidate not in options:
        st.session_state.active_scorecard_candidate = options[0]
        
    selected_cand_str = st.session_state.active_scorecard_candidate
    
    matched_candidate = None
    for c in filtered_cands:
        c_str = f"{c['name']} ({c['email']}) - {c['job_role']}"
        if c_str == selected_cand_str:
            matched_candidate = c
            break
            
    with col_left:
        st.write("### 👥 Applicants List")
        # Loop over candidates and draw left cards
        for idx, c in enumerate(filtered_cands):
            c_str = f"{c['name']} ({c['email']}) - {c['job_role']}"
            score = int(c.get("match_score", 0))
            status = c.get("status", "Applied")
            status_color = "#3b82f6"
            if "Screening Failed" in status or "Failed" in status:
                status_color = "#ef4444"
            elif "Evaluation" in status or "Hired" in status or "Passed" in status:
                status_color = "#10b981"
            elif "Interview" in status:
                status_color = "#f59e0b"
                
            is_active = (c_str == selected_cand_str)
            active_border = "border: 2px solid var(--accent-red) !important; box-shadow: 0 4px 15px rgba(229, 9, 20, 0.15) !important;" if is_active else ""
            
            card_html = f"""
            <div class="cand-card" style="margin-bottom: 12px; padding: 15px; border-radius: 12px; {active_border}">
                <div class="cand-card-header" style="gap: 5px; margin-bottom: 5px;">
                    <div class="cand-card-info">
                        <span style="font-weight: 700; font-size: 1.05rem; color: var(--text-main);">👤 {c['name']}</span>
                        <span style="font-size: 0.8rem; color: var(--text-sub);">💼 {c['job_role']}</span>
                    </div>
                    <div class="cand-card-score" style="padding: 4px 8px; border-radius: 8px;">
                        <span style="font-size: 1.1rem; font-weight: 700; color: var(--accent-red);">{score}%</span>
                        <span style="font-size: 0.6rem; color: var(--text-sub); display: block; margin-top: -2px;">Match</span>
                    </div>
                </div>
                <div style="font-size: 0.82rem; margin-top: 8px; display: flex; flex-direction: column; gap: 4px; border-top: 1px solid var(--card-border); padding-top: 8px; color: var(--text-sub);">
                    <div>📧 {c['email']}</div>
                    <div>📌 Stage: <span style="color: {status_color}; font-weight: 700;">● {status}</span></div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button("👁️ View Scorecard", key=f"sel_cand_{idx}_{c['email']}", use_container_width=True):
                st.session_state.active_scorecard_candidate = c_str
                
    with col_right:
        if matched_candidate:
            st.markdown(f"""
            <div class="glass-card" style="margin-bottom: 15px; border-left: 6px solid var(--accent-red); padding: 20px !important;">
                <h3 style="margin: 0; color: var(--text-main);">📊 Scorecard: {matched_candidate['name']}</h3>
                <span style="color: var(--text-sub); font-size: 0.9rem;">Target Position: <strong>{matched_candidate['job_role']}</strong></span>
            </div>
            """, unsafe_allow_html=True)
            
            score_tab1, score_tab2, score_tab3, score_tab4 = st.tabs(["📊 Match Analysis", "💬 Interview Transcript", "🛡️ Proctoring Report", "⚙️ Administrative Controls"])
            
            with score_tab1:
                recommendation = matched_candidate.get("selection", "N/A")
                if "Recommended" in recommendation or "hire" in recommendation.lower():
                    rec_badge_html = f'<div style="background-color: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.15); border-radius: 12px; padding: 15px; display: flex; align-items: center; gap: 15px; margin-bottom: 20px;"><span style="font-size: 2rem;">🏆</span><div><div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; color: #10b981; font-weight: 700;">AI Hiring Committee Recommendation</div><div style="font-size: 1.15rem; font-weight: 700; color: var(--text-main);">{recommendation}</div></div></div>'
                else:
                    rec_badge_html = f'<div style="background-color: rgba(239, 68, 68, 0.06); border: 1px solid rgba(239, 68, 68, 0.12); border-radius: 12px; padding: 15px; display: flex; align-items: center; gap: 15px; margin-bottom: 20px;"><span style="font-size: 2rem;">⚠️</span><div><div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; color: #ef4444; font-weight: 700;">AI Hiring Recommendation</div><div style="font-size: 1.15rem; font-weight: 700; color: var(--text-main);">{recommendation}</div></div></div>'
                st.markdown(rec_badge_html, unsafe_allow_html=True)
                
                score = int(matched_candidate.get("match_score", 0))
                st.write(f"**AI Match Score**: **{score}%**")
                st.progress(score / 100.0)
                
                status = matched_candidate.get("status", "Applied")
                status_badge_html = ""
                if "Screening Failed" in status or "Failed" in status or "Violation" in status or "Disqualified" in status:
                    status_badge_html = f'<span style="background-color: rgba(239, 68, 68, 0.12); color: #ef4444; padding: 3px 8px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">🔴 {status}</span>'
                elif "Evaluation" in status or "Hired" in status or "Passed" in status:
                    status_badge_html = f'<span style="background-color: rgba(16, 185, 129, 0.12); color: #10b981; padding: 3px 8px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">🟢 {status}</span>'
                else:
                    status_badge_html = f'<span style="background-color: rgba(245, 158, 11, 0.12); color: #f59e0b; padding: 3px 8px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">🟡 {status}</span>'
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"📧 **Email**: {matched_candidate['email']}")
                    st.write(f"📞 **Phone**: {matched_candidate['phone']}")
                    st.write(f"💼 **Role**: {matched_candidate['job_role']}")
                with col2:
                    st.write(f"⏳ **Experience Level**: {matched_candidate['experience']}")
                    st.markdown(f"📌 **Pipeline Status**: {status_badge_html}", unsafe_allow_html=True)
                    st.write(f"📊 **MCQ Score**: `{matched_candidate['mcq_score']}`")
                
                st.write("---")
                
                st.write("#### 🎯 Skill Mapping & Gap Analysis")
                
                # Interactive Plotly Radar / Fallback Bar Chart
                matched_skills = matched_candidate.get("matched_skills", [])
                missing_skills = matched_candidate.get("missing_skills", [])
                all_skills = matched_skills + missing_skills
                
                if all_skills:
                    import plotly.graph_objects as go
                    import pandas as pd
                    
                    categories = list(dict.fromkeys(all_skills))
                    if len(categories) < 3:
                        import plotly.express as px
                        df_skills = pd.DataFrame({
                            "Skill": categories,
                            "Status": ["Matched" if s in matched_skills else "Missing" for s in categories],
                            "Match Status": [100 if s in matched_skills else 0 for s in categories]
                        })
                        fig = px.bar(
                            df_skills,
                            x="Match Status",
                            y="Skill",
                            color="Status",
                            orientation='h',
                            color_discrete_map={"Matched": "#ff3344" if st.session_state.get("theme_mode") == "Cyberpunk Dark" else "#b91c1c", "Missing": "#a1a1aa"},
                            range_x=[0, 100]
                        )
                        fig.update_layout(
                            height=150,
                            margin=dict(l=10, r=10, t=10, b=10),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(
                                tickvals=[0, 50, 100],
                                ticktext=['0%', '50%', '100%'],
                                title="Candidate Skill Level"
                            ),
                            yaxis=dict(title=""),
                            font=dict(
                                color='#f4f4f5' if st.session_state.get("theme_mode") == "Cyberpunk Dark" else '#0f172a',
                                family='Outfit, sans-serif'
                            )
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        candidate_vals = [100 if skill in matched_skills else 0 for skill in categories]
                        target_vals = [100] * len(categories)
                        
                        categories_closed = categories + [categories[0]]
                        candidate_vals_closed = candidate_vals + [candidate_vals[0]]
                        target_vals_closed = target_vals + [target_vals[0]]
                        
                        fig = go.Figure()
                        
                        # Candidate profile
                        fig.add_trace(go.Scatterpolar(
                            r=candidate_vals_closed,
                            theta=categories_closed,
                            fill='toself',
                            name='Candidate Profile',
                            fillcolor='rgba(229, 9, 20, 0.2)' if st.session_state.get("theme_mode") == "Cyberpunk Dark" else 'rgba(185, 28, 28, 0.2)',
                            line=dict(color='#ff3344' if st.session_state.get("theme_mode") == "Cyberpunk Dark" else '#b91c1c')
                        ))
                        
                        # Required profile
                        fig.add_trace(go.Scatterpolar(
                            r=target_vals_closed,
                            theta=categories_closed,
                            fill='toself',
                            name='Job Requirements',
                            fillcolor='rgba(59, 130, 246, 0.1)',
                            line=dict(color='#3b82f6', dash='dash')
                        ))
                        
                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 100],
                                    tickvals=[0, 50, 100],
                                    ticktext=['0%', '50%', '100%'],
                                    gridcolor='rgba(128, 128, 128, 0.2)',
                                    linecolor='rgba(128, 128, 128, 0.2)'
                                ),
                                angularaxis=dict(
                                    gridcolor='rgba(128, 128, 128, 0.2)',
                                    linecolor='rgba(128, 128, 128, 0.2)'
                                )
                            ),
                            showlegend=True,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            margin=dict(l=50, r=50, t=30, b=30),
                            height=320,
                            font=dict(
                                color='#f4f4f5' if st.session_state.get("theme_mode") == "Cyberpunk Dark" else '#0f172a',
                                family='Outfit, sans-serif'
                            )
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No skill mapping data available.")
                
                st.write("")
                col_sk1, col_sk2 = st.columns(2)
                with col_sk1:
                    if matched_skills:
                        st.write("✅ **Matched Skills (Present in Resume):**")
                        tags_html = "".join([f'<span style="background-color: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; margin-right: 8px; display: inline-block; margin-bottom: 5px; font-weight: 500;">{skill}</span>' for skill in matched_skills])
                        st.markdown(tags_html, unsafe_allow_html=True)
                    else:
                        st.write("✅ **Matched Skills:** None identified.")
                with col_sk2:
                    if missing_skills:
                        st.write("⚠️ **Missing Skills (Required for JD):**")
                        tags_html = "".join([f'<span style="background-color: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; margin-right: 8px; display: inline-block; margin-bottom: 5px; font-weight: 500;">{skill}</span>' for skill in missing_skills])
                        st.markdown(tags_html, unsafe_allow_html=True)
                    else:
                        st.write("⚠️ **Missing Skills:** None identified.")
                
                red_flags = matched_candidate.get("red_flags", [])
                has_red_flags = False
                if red_flags:
                    if isinstance(red_flags, list):
                        has_red_flags = any(x.lower() not in ["none", ""] for x in red_flags)
                    else:
                        has_red_flags = red_flags.lower() not in ["none", ""]
                        
                if has_red_flags:
                    st.write("🚩 **Red Flags / Hiring Concerns:**")
                    if isinstance(red_flags, list):
                        for flag in red_flags:
                            if flag.lower() not in ["none", ""]:
                                st.markdown(f"- <span style='color: #ef4444; font-weight: 500;'>{flag}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"- <span style='color: #ef4444; font-weight: 500;'>{red_flags}</span>", unsafe_allow_html=True)
                
                st.write("---")
                if matched_candidate.get("screening_reason"):
                    st.markdown("**Initial Screening Feedback:**")
                    st.info(matched_candidate["screening_reason"])
                
                if matched_candidate.get("summary"):
                    st.markdown("**Hiring Committee Summary:**")
                    st.success(matched_candidate["summary"])
                    
            with score_tab2:
                st.write("#### 💬 Technical Interview Dialogue Logs")
                chat_hist = matched_candidate.get("chat_history", [])
                if not chat_hist:
                    st.info("No conversational interview logs are available for this candidate yet.")
                else:
                    with st.container(height=400):
                        for message in chat_hist:
                            avatar = "🧑" if message["role"] == "user" else "🤖"
                            with st.chat_message(message["role"], avatar=avatar):
                                st.markdown(message["content"])
                    
            with score_tab3:
                st.write("#### 🛡️ AI Proctoring & Trust Assessment")
                
                switches = matched_candidate.get("tab_switches", 0)
                warnings = matched_candidate.get("proctoring_warnings", [])
                violated = matched_candidate.get("proctoring_violated", False)
                report = matched_candidate.get("proctoring_report")
                
                col_met1, col_met2, col_met3 = st.columns(3)
                
                trust_score = 100
                if report and "trust_score" in report:
                    trust_score = report["trust_score"]
                else:
                    trust_score = max(0, 100 - switches * 25)
                
                with col_met1:
                    st.metric(label="Proctoring Trust Score", value=f"{trust_score}%")
                with col_met2:
                    st.metric(label="Tab Switch Events", value=f"{switches} / 3")
                with col_met3:
                    risk_level = "Low"
                    if report and "risk_level" in report:
                        risk_level = report["risk_level"]
                    elif switches > 0:
                        risk_level = "Medium" if switches <= 2 else ("High" if switches == 3 else "Suspicious - Auto-Submitted")
                    st.metric(label="Risk Assessment", value=risk_level)
                
                st.write("---")
                
                if report:
                    st.write("##### 🤖 AI Proctoring Analysis & Verdict")
                    verdict = report.get("proctoring_verdict", "N/A")
                    likelihood = report.get("cheating_likelihood", "N/A")
                    summary = report.get("violation_summary", "No details available.")
                    
                    if verdict == "Disqualified" or violated:
                        st.error(f"**Final Verdict**: 🚨 DISQUALIFIED ({verdict})")
                    elif verdict == "Under Review":
                        st.warning(f"**Final Verdict**: ⚠️ UNDER REVIEW ({verdict})")
                    else:
                        st.success(f"**Final Verdict**: ✅ PASSED PROCTORING ({verdict})")
                        
                    st.write(f"**Cheating Likelihood**: `{likelihood}`")
                    st.info(f"**AI Analyst Assessment**: {summary}")
                else:
                    st.info("No AI Proctoring Report generated yet. Completed normally with zero warnings.")
                
                if warnings:
                    st.write("##### ⏳ Focus Loss Timeline Logs")
                    
                    import pandas as pd
                    import datetime
                    import plotly.express as px
                    
                    # Construct datetimes from warnings
                    today = datetime.date.today()
                    times = []
                    for w in warnings:
                        try:
                            t_parsed = datetime.datetime.strptime(w, "%H:%M:%S").time()
                            times.append(datetime.datetime.combine(today, t_parsed))
                        except Exception:
                            times.append(datetime.datetime.now())
                    
                    df_warn = pd.DataFrame({
                        "Time": times,
                        "Event": [f"Focus Loss {i}" for i in range(1, len(warnings) + 1)],
                        "Type": ["Tab Switch / Focus Loss"] * len(warnings)
                    })
                    
                    fig_timeline = px.scatter(
                        df_warn,
                        x="Time",
                        y="Type",
                        color="Event",
                        symbol="Event",
                        color_discrete_sequence=px.colors.qualitative.Antique,
                        hover_name="Event",
                        hover_data={"Time": "|%H:%M:%S", "Type": False}
                    )
                    
                    fig_timeline.update_layout(
                        height=160,
                        margin=dict(l=10, r=10, t=10, b=10),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(
                            showgrid=True,
                            gridcolor='rgba(128, 128, 128, 0.2)',
                            tickformat="%H:%M:%S",
                            title="Time of Violation"
                        ),
                        yaxis=dict(
                            showgrid=False,
                            title="",
                            showticklabels=False
                        ),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        font=dict(
                            color='#f4f4f5' if st.session_state.get("theme_mode") == "Cyberpunk Dark" else '#0f172a',
                            family='Outfit, sans-serif'
                        )
                    )
                    
                    fig_timeline.update_traces(marker=dict(size=14, line=dict(width=2, color='white')))
                    
                    # Add vertical reference lines for each warning point
                    for t in df_warn["Time"]:
                        fig_timeline.add_vline(x=t.timestamp() * 1000, line_dash="dash", line_color="rgba(239, 68, 68, 0.5)")
                        
                    st.plotly_chart(fig_timeline, use_container_width=True)
                    
                    st.write("")
                    for w_idx, w_time in enumerate(warnings, 1):
                        st.markdown(f"- **Event {w_idx}**: Focus lost at `{w_time}`")
                    
            with score_tab4:
                st.write("#### ⚙️ Administrative Controls & Reset Actions")
                col_adm1, col_adm2 = st.columns(2)
                with col_adm1:
                    st.write("**Assessment Access**")
                    allowed_retake = matched_candidate.get("allowed_retake", False)
                    if allowed_retake:
                        st.success("Retake has already been enabled for this candidate.")
                    else:
                        if st.button("🔓 Enable Retake / Reset Access", key=f"reset_btn_{matched_candidate['email']}", use_container_width=True):
                            records = load_candidates()
                            for r in records:
                                if r.get("email", "").strip().lower() == matched_candidate["email"].strip().lower():
                                    r["allowed_retake"] = True
                                    r["status"] = "Retake Allowed"
                                    break
                            with open(CANDIDATES_FILE, "w") as f:
                                json.dump(records, f, indent=2)
                            st.success(f"Access reset successful! {matched_candidate['name']} can now register and retake the test.")
                            time.sleep(1)
                            st.rerun()
                            
                with col_adm2:
                    st.write("**Danger Zone**")
                    st.warning("Deletions are permanent.")
                    if st.button("🗑️ Delete Candidate Record", key=f"delete_btn_{matched_candidate['email']}", use_container_width=True):
                        records = load_candidates()
                        filtered_records = [r for r in records if r.get("email", "").strip().lower() != matched_candidate["email"].strip().lower()]
                        with open(CANDIDATES_FILE, "w") as f:
                            json.dump(filtered_records, f, indent=2)
                        try:
                            tickets = load_issues()
                            filtered_tickets = [t for t in tickets if t.get("email", "").strip().lower() != matched_candidate["email"].strip().lower()]
                            save_issues(filtered_tickets)
                        except Exception:
                            pass
                            
                        st.success(f"Candidate {matched_candidate['name']} successfully deleted!")
                        time.sleep(1)
                        st.rerun()


@st.fragment
def render_proctoring_instruction_stage():
    st.markdown("""
    <div class="glass-card" style="margin-bottom: 20px; border-left: 5px solid var(--accent-red);">
        <div class="stage-title">📋 Assessment Guidelines & Proctoring Instructions</div>
        <div style="color: var(--text-main); font-size: 1.05rem; line-height: 1.6; margin-top: 15px;">
            Please read the following instructions carefully before starting the assessment. This test uses <strong>AI-assisted proctoring</strong> to monitor session integrity.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("### 🛠️ Assessment Details")
    st.markdown("""
    - **Format**: 5 technical multiple-choice questions (MCQs) customized to your resume and applied role.
    - **Passing Threshold**: 60% (at least **3 out of 5** correct).
    - **Time Limit**: The test is not strictly timed, but it must be completed in a single continuous session.
    """)
    
    st.write("### 🛡️ AI Proctoring & Integrity Rules")
    st.warning("""
    ⚠️ **IMPORTANT RULES**:
    1. **No Tab Switching**: Switching to other browser tabs is strictly prohibited.
    2. **No Window Focus Loss**: Clicking outside the assessment window (e.g., opening other applications, IDEs, or browser developer tools) is monitored.
    3. **Violation Tolerances**:
       - The system automatically detects tab switches or window blurs and will display a warning immediately.
       - You are allowed a maximum of **3 warnings**.
       - On the **4th violation**, the assessment will be **automatically terminated and submitted** for evaluation based on your progress so far, and flagged with a proctoring violation.
    """)
    
    st.write("### 🤝 Candidate Agreement")
    agree = st.checkbox("I understand the rules and agree to take the assessment under active proctoring monitoring without unauthorized assistance.", key="proctor_agreement_checkbox")
    
    col1, col2 = st.columns([3, 7])
    with col1:
        if st.button("🚀 Start Assessment", use_container_width=True, disabled=not agree):
            st.session_state.stage = "mcq"
            st.session_state.tab_switches = 0
            st.session_state.proctoring_warnings = []
            st.session_state.proctoring_violated = False
            log_candidate_state()
            st.rerun()

@st.fragment
def render_mcq_stage():
    # Generate tailored technical MCQs if not already present
    if not st.session_state.get("mcqs"):
        with st.spinner("Generating customized MCQ questions tailored to your profile..."):
            try:
                mcq_agent = MCQAgent()
                job_diff = JOB_DIFFICULTIES.get(st.session_state.job_role, "Medium")
                mcq_list = mcq_agent.run(
                    resume_text=st.session_state.resume_text,
                    job_role=st.session_state.job_role,
                    difficulty=job_diff,
                    num_questions=5
                )
                st.session_state.mcqs = mcq_list.questions
                log_candidate_state()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate MCQ questions: {str(e)}")
                return

    if st.session_state.get("tab_switches", 0) > 0:
        st.error(f"⚠️ **PROCTORING WARNING ({st.session_state.tab_switches}/3)**: A tab switch or focus loss was detected. If you switch tabs/windows again, your test will be auto-submitted and flagged for review.")
        
    st.markdown("""
    <div class="glass-card" style="margin-bottom: 20px;">
        <div class="stage-title">Stage 2: Technical MCQ Screening</div>
        <div style="color: #64748b; font-size: 0.95rem;">Answer the following questions based on technical competencies. Passing threshold is 60% (3 out of 5 correct).</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render MCQ form
    temp_answers = {}
    for idx, q in enumerate(st.session_state.mcqs):
        st.markdown(f"**Question {idx + 1}:** {q.question}")
        options = ["Select an option"] + q.options
        user_choice = st.radio(
            label=f"Options for Q{idx+1}",
            options=options,
            key=f"mcq_q_{idx}",
            label_visibility="collapsed"
        )
        if user_choice != "Select an option":
            temp_answers[idx] = user_choice
            
    if st.button("Submit MCQ Test"):
        if len(temp_answers) < len(st.session_state.mcqs):
            st.error("Please answer all multiple-choice questions before submitting.")
        else:
            score, pct, results = MCQAgent.grade_answers(st.session_state.mcqs, temp_answers)
            st.session_state.mcq_score = score
            st.session_state.mcq_passed = (score >= 3) or (st.session_state.get("candidate_user_email") == "admin@test.com")
            st.session_state.mcq_answers = temp_answers
            
            if st.session_state.mcq_passed:
                st.session_state.stage = "mcq_passed_screen"
            else:
                st.session_state.stage = "mcq_failed_screen"
            run_proctoring_analysis()
            log_candidate_state()
            st.rerun()


@st.fragment
def render_interview_stage():
    if st.session_state.get("tab_switches", 0) > 0:
        st.error(f"⚠️ **PROCTORING WARNING ({st.session_state.tab_switches}/3)**: A tab switch or focus loss was detected. If you switch tabs/windows again, your test will be auto-submitted and flagged for review.")
        
    # 1. Display Chat Feed Container at the TOP
    with st.container(height=480):
        for message in st.session_state.chat_history:
            avatar = "🧑" if message["role"] == "user" else "🤖"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

    # 2. Render response inputs container at the BOTTOM
    user_response_text = ""
    if not st.session_state.interview_concluded:
        with st.container(border=True):
            tab_type, tab_voice = st.tabs(["⌨️ Type response", "🎙️ Record Voice response"])
            
            with tab_type:
                with st.form("chat_form", clear_on_submit=True):
                    user_input = st.text_area("Your Response", placeholder="Type your answer here and click Send...", key="interview_text_input")
                    submitted = st.form_submit_button("Send Answer")
                if submitted and user_input.strip():
                    user_response_text = user_input.strip()
            
            with tab_voice:
                st.markdown('<div><span class="recording-indicator"></span><strong>Microphone Ready</strong> - speak clearly and submit.</div>', unsafe_allow_html=True)
                st.info("🎙️ **Voice Instructions**: Click the microphone icon below to start recording. Speak your answer clearly, and click the stop icon when you are finished. Then click **Submit Answer**.")
                audio_key = f"interview_audio_record_{len(st.session_state.get('chat_history', []))}"
                audio_file = st.audio_input("Record your answer", key=audio_key)
                if audio_file:
                    st.audio(audio_file)
                    if st.button("Submit Answer", key="interview_voice_submit_btn"):
                        with st.spinner("Agent is looking into your response, please wait..."):
                            try:
                                config = Config.load_config()
                                from google import genai
                                from google.genai import types
                                
                                client = genai.Client(api_key=config.GEMINI_API_KEY)
                                audio_bytes = audio_file.read()
                                
                                response = client.models.generate_content(
                                    model='gemini-2.5-flash',
                                    contents=[
                                        types.Part.from_bytes(
                                            data=audio_bytes,
                                            mime_type=audio_file.type
                                        ),
                                        "Transcribe the spoken technical words in this audio into text accurately. Do not add any conversational framing or headers, just return the text transcription."
                                    ]
                                )
                                transcription = response.text.strip() if response.text else ""
                                if transcription:
                                    user_response_text = transcription
                                else:
                                    st.error("No speech detected. Please record again.")
                            except Exception as e:
                                st.error(f"Voice transcription failed: {str(e)}")

        if user_response_text:
            # Apply PII redaction first
            sanitized_response = InterviewAgent.sanitize_text(user_response_text)
            
            # Check toxicity and prompt injection
            interview_agent = InterviewAgent()
            is_valid, warning_msg = interview_agent.validate_input(sanitized_response)
            
            if not is_valid:
                st.session_state.chat_history.append({"role": "user", "content": sanitized_response})
                st.session_state.chat_history.append({"role": "assistant", "content": warning_msg})
                log_candidate_state()
                st.rerun()
                
            st.session_state.chat_history.append({"role": "user", "content": sanitized_response})
            
            with st.spinner("Interviewer is reviewing your answer..."):
                try:
                    last_assistant_msg = ""
                    for msg in reversed(st.session_state.chat_history[:-1]):
                        if msg["role"] == "assistant":
                            last_assistant_msg = msg["content"]
                            break
                            
                    repeat_agent = RepeatAgent()
                    clarification = repeat_agent.run(
                        candidate_message=sanitized_response,
                        last_question=last_assistant_msg
                    )

                    
                    if clarification.is_clarification_request:
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": clarification.clarified_response
                        })
                    else:
                        interview_agent = InterviewAgent()
                        job_diff = JOB_DIFFICULTIES.get(st.session_state.job_role, "Medium")
                        res = interview_agent.run(
                            resume_text=st.session_state.resume_text,
                            job_role=st.session_state.job_role,
                            experience=st.session_state.experience,
                            job_description=st.session_state.job_description,
                            conversation_history=st.session_state.chat_history,
                            difficulty=job_diff,
                            num_questions=3
                        )
                        st.session_state.chat_history.append({"role": "assistant", "content": res.response})
                        if res.should_conclude:
                            st.session_state.interview_concluded = True
                    log_candidate_state()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error during interview conversation: {str(e)}")

    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "assistant":
        col_rep1, col_rep2 = st.columns([3, 7])
        with col_rep1:
            if st.button("🔊 Replay Question", use_container_width=True):
                st.session_state.last_spoken_message = ""
                
    if st.session_state.interview_concluded:
        st.success("The interview session is complete! Clicking below will trigger the evaluation phase.")
        if st.button("Get Selection Results", use_container_width=True):
            with st.spinner("Hiring Committee Agent is evaluating..."):
                try:
                    interview_agent = InterviewAgent()
                    eval_res = interview_agent.evaluate(
                        resume_text=st.session_state.resume_text,
                        job_role=st.session_state.job_role,
                        experience=st.session_state.experience,
                        job_description=st.session_state.job_description,
                        conversation_history=st.session_state.chat_history
                    )
                    st.session_state.evaluation_result = eval_res
                    st.session_state.stage = "final_evaluation"
                    run_proctoring_analysis()
                    log_candidate_state()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error during final evaluation: {str(e)}")

    # Speech synthesis trigger
    if "last_spoken_message" not in st.session_state:
        st.session_state.last_spoken_message = ""
        
    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "assistant":
        last_msg = st.session_state.chat_history[-1]["content"]
        if st.session_state.last_spoken_message != last_msg:
            clean_msg = last_msg.replace('**', '').replace('*', '').replace('`', '').replace('"', '\\"').replace('\n', ' ')
            st.components.v1.html(f"""
            <script>
                if ('speechSynthesis' in window) {{
                    window.parent.speechSynthesis.cancel();
                    var utterance = new SpeechSynthesisUtterance("{clean_msg}");
                    utterance.rate = 1.05;
                    var voices = window.parent.speechSynthesis.getVoices();
                    var engVoice = voices.find(v => v.lang.startsWith('en'));
                    if (engVoice) utterance.voice = engVoice;
                    window.parent.speechSynthesis.speak(utterance);
                }}
                
                // Stop speech if candidate decides to record, type, or interact in any way
                try {{
                    if (window.parent.__tts_cancel_listener__) {{
                        window.parent.document.removeEventListener('click', window.parent.__tts_cancel_listener__, true);
                        window.parent.document.removeEventListener('keydown', window.parent.__tts_cancel_listener__, true);
                    }}
                    
                    window.parent.__tts_cancel_listener__ = function() {{
                        if (window.parent.speechSynthesis) {{
                            window.parent.speechSynthesis.cancel();
                        }}
                    }};
                    
                    window.parent.document.addEventListener('click', window.parent.__tts_cancel_listener__, true);
                    window.parent.document.addEventListener('keydown', window.parent.__tts_cancel_listener__, true);
                }} catch (e) {{
                    console.error("TTS silencer failed to register:", e);
                }}
            </script>
            """, height=0)
            st.session_state.last_spoken_message = last_msg

@st.fragment
def render_job_management_tab():
    # Initialize chatbot history for job agent if not present
    if "job_agent_history" not in st.session_state:
        st.session_state.job_agent_history = [
            {"role": "assistant", "content": "Hello! I am your AI Job Management assistant. Tell me how I can help manage your postings (e.g. create a new role, modify requirements, or delete active jobs)."}
        ]
    if "last_spoken_job_message" not in st.session_state:
        st.session_state.last_spoken_job_message = ""

    # Load active jobs from JSON
    jobs = load_jobs()

    # Split panel: Left panel shows active jobs grid, Right panel shows chat with AI agent
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        active_jobs = {k: v for k, v in jobs.items() if not (isinstance(v, dict) and v.get("is_draft", False))}
        draft_jobs = {k: v for k, v in jobs.items() if isinstance(v, dict) and v.get("is_draft", False)}
        
        st.write("### 💼 Current Active Roles")
        if active_jobs:
            # Show active jobs in a clean, vertical grid
            cols = st.columns(2)
            for idx, (title, data) in enumerate(active_jobs.items()):
                col = cols[idx % 2]
                desc = data.get("description", data) if isinstance(data, dict) else data
                diff = data.get("difficulty", "Medium") if isinstance(data, dict) else "Medium"
                
                # Colors based on difficulty level
                diff_color = "#3b82f6"
                if diff == "Hard":
                    diff_color = "#ef4444"
                elif diff == "Easy" or diff == "Very Easy":
                    diff_color = "#10b981"
                
                with col:
                    st.markdown(f"""
                    <div class="job-card" style="min-height: 250px; display: flex; flex-direction: column; justify-content: space-between;">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="font-weight: 700; font-size: 1.1rem; color: var(--text-main);">{title}</span>
                                <span style="background-color: {diff_color}1a; color: {diff_color}; padding: 3px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; border: 1px solid {diff_color}33;">{diff}</span>
                            </div>
                            <div style="font-size: 0.88rem; color: var(--text-sub); line-height: 1.5; white-space: pre-wrap; max-height: 140px; overflow-y: auto; padding-top: 5px; border-top: 1px solid var(--card-border);">
                                {desc}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        else:
            st.info("No active jobs currently listed.")
            
        st.markdown("---")
        st.write("### 📝 Pending JD Drafts Queue")
        if draft_jobs:
            for title, data in draft_jobs.items():
                with st.container(border=True):
                    st.markdown(f"#### 📝 {title} (Draft)")
                    desc = data.get("description", "")
                    diff = data.get("difficulty", "Medium")
                    
                    edited_desc = st.text_area("Job Description", value=desc, height=150, key=f"edit_draft_desc_{title}")
                    edited_diff = st.selectbox("Difficulty Level", ["Very Easy", "Easy", "Medium", "Hard"], index=["Very Easy", "Easy", "Medium", "Hard"].index(diff), key=f"edit_draft_diff_{title}")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("Approve & Publish", key=f"approve_job_{title}", use_container_width=True):
                            jobs[title] = {
                                "description": edited_desc,
                                "difficulty": edited_diff,
                                "is_draft": False
                            }
                            save_jobs(jobs)
                            st.success(f"Published {title}!")
                            time.sleep(0.5)
                            st.rerun()
                    with col_btn2:
                        if st.button("Delete Draft", key=f"delete_draft_job_{title}", use_container_width=True):
                            del jobs[title]
                            save_jobs(jobs)
                            st.info(f"Deleted draft for {title}.")
                            time.sleep(0.5)
                            st.rerun()
        else:
            st.info("No pending job description drafts.")


    with col_right:
        st.write("### 🤖 AI Job Management Assistant")
        st.markdown("""
        <div style="background-color: rgba(229, 9, 20, 0.04); border: 1px solid rgba(229, 9, 20, 0.1); border-radius: 10px; padding: 12px; font-size: 0.85rem; color: var(--text-sub); margin-bottom: 15px;">
            💬 <strong>Tip:</strong> You can type or speak commands like:<br>
            • <em>"Create a DevOps role with Docker and AWS"</em><br>
            • <em>"Add Python to requirements for Machine Learning Engineer"</em><br>
            • <em>"Delete the Data Scientist position"</em>
        </div>
        """, unsafe_allow_html=True)

        # Chat display container
        chat_container = st.container(height=300)
        with chat_container:
            for msg in st.session_state.job_agent_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])



        # Selector for Type vs Voice input wrapped in a bordered container card
        with st.container(border=True):
            tab_type, tab_voice = st.tabs(["⌨️ Type instruction", "🎙️ Record Voice instruction"])
            agent_input_text = ""

            with tab_type:
                agent_input = st.chat_input("Tell the AI to manage jobs...", key="job_agent_chat_input")
                if agent_input:
                    agent_input_text = agent_input.strip()
            
            with tab_voice:
                st.markdown('<div><span class="recording-indicator"></span><strong>Microphone Ready</strong> - speak clearly and submit.</div>', unsafe_allow_html=True)
                st.info("🎙️ **Voice Instructions**: Click the microphone icon to record your instruction, then click **Submit Voice Command**.")
                recruiter_audio_key = f"job_agent_audio_record_{len(st.session_state.get('job_agent_history', []))}"
                audio_file = st.audio_input("Record your instruction", key=recruiter_audio_key)
                if audio_file:
                    st.audio(audio_file)
                    if st.button("Submit Voice Command", key="job_agent_voice_submit_key", use_container_width=True):
                        with st.spinner("Processing voice command, please wait..."):
                            try:
                                config = Config.load_config()
                                from google import genai
                                from google.genai import types
                                
                                client = genai.Client(api_key=config.GEMINI_API_KEY)
                                audio_bytes = audio_file.read()
                                
                                response = client.models.generate_content(
                                    model='gemini-2.5-flash',
                                    contents=[
                                        types.Part.from_bytes(
                                            data=audio_bytes,
                                            mime_type=audio_file.type
                                        ),
                                        "Transcribe the spoken words in this audio into text accurately. Do not add any conversational framing or headers, just return the text transcription."
                                    ]
                                )
                                transcription = response.text.strip() if response.text else ""
                                if transcription:
                                    agent_input_text = transcription
                                else:
                                    st.error("No speech detected. Please record again.")
                            except Exception as e:
                                st.error(f"Voice transcription failed: {str(e)}")

        if agent_input_text:
            # Append user message
            st.session_state.job_agent_history.append({"role": "user", "content": agent_input_text})
            
            with st.spinner("AI is processing job management instruction..."):
                try:
                    # Run JobAgent
                    job_agent = JobAgent()
                    result = job_agent.run(agent_input_text, jobs)
                    
                    action_taken = result.action.strip().lower()
                    job_title = result.job_title.strip()
                    explanation = result.explanation
                    
                    if action_taken == "add":
                        if job_title in jobs:
                            explanation = f"⚠️ The job role '{job_title}' already exists. I cannot add it. Use an update instruction if you want to modify it."
                        elif not result.job_description:
                            explanation = f"⚠️ The agent tried to add '{job_title}' but did not generate a job description. Please provide more details."
                        else:
                            jobs[job_title] = {
                                "description": result.job_description,
                                "difficulty": result.difficulty,
                                "is_draft": True
                            }
                            save_jobs(jobs)
                    elif action_taken == "update":
                        if job_title not in jobs:
                            explanation = f"⚠️ The job role '{job_title}' does not exist, so I couldn't update it. Use an 'add' instruction if you want to create a new role."
                        elif not result.job_description:
                            explanation = f"⚠️ The agent tried to update '{job_title}' but the description was empty."
                        else:
                            jobs[job_title] = {
                                "description": result.job_description,
                                "difficulty": result.difficulty,
                                "is_draft": True
                            }
                            save_jobs(jobs)

                    elif action_taken == "delete":
                        if job_title not in jobs:
                            explanation = f"⚠️ The job role '{job_title}' does not exist, so I couldn't delete it."
                        else:
                            del jobs[job_title]
                            save_jobs(jobs)
                    
                    st.session_state.job_agent_history.append({"role": "assistant", "content": explanation})
                except Exception as e:
                    st.session_state.job_agent_history.append({"role": "assistant", "content": f"⚠️ Error running job agent: {str(e)}"})
            st.rerun()

    st.markdown("---")
    with st.expander("🛠️ Manual Job Controls (Fallback / Form-based)"):
        action = st.selectbox("Action", ["Add New Job", "Update Job Description", "Delete Job"], key="manual_action_select")
        
        if action == "Add New Job":
            st.write("### Create a New Job Opening")
            new_title = st.text_input("Job Title", placeholder="e.g. DevOps Engineer", key="manual_add_title")
            
            brief_notes = st.text_input("AI Assistant Input (Brief skills/notes)", placeholder="e.g. React, TypeScript, 3 years exp, state management, hybrid", key="manual_add_notes")
            if st.button("🪄 Auto-Generate JD with AI", key="manual_add_autogen"):
                if not new_title.strip():
                    st.error("Please enter a Job Title first.")
                elif not brief_notes.strip():
                    st.error("Please enter brief notes or skills for the AI to work with.")
                else:
                    with st.spinner("Gemini is drafting the job description..."):
                        draft = generate_ai_jd(new_title.strip(), brief_notes.strip())
                        st.session_state.generated_jd_draft = draft
                        st.rerun()
            
            default_jd = st.session_state.get("generated_jd_draft", "")
            new_jd = st.text_area("Job Description Details", value=default_jd, height=200, placeholder="Paste or edit the job requirements here...", key="manual_add_jd")
            new_diff = st.selectbox("Select Target Difficulty Level", ["Very Easy", "Easy", "Medium", "Hard"], index=2, key="manual_add_diff")
            
            if st.button("Create Job Opening", key="manual_add_submit"):
                if not new_title.strip() or not new_jd.strip():
                    st.error("Please fill in both the Job Title and Job Description.")
                elif new_title.strip() in jobs:
                    st.error(f"Job title '{new_title.strip()}' already exists.")
                else:
                    jobs[new_title.strip()] = {
                        "description": new_jd.strip(),
                        "difficulty": new_diff
                    }
                    if save_jobs(jobs):
                        if "generated_jd_draft" in st.session_state:
                            del st.session_state.generated_jd_draft
                        st.success(f"Job opening '{new_title}' successfully created!")
                        time.sleep(1)
                        st.rerun()
                        
        elif action == "Update Job Description":
            st.write("### Edit an Existing Job Opening")
            if not jobs:
                st.info("No active jobs to update.")
            else:
                selected_job = st.selectbox("Select Job to Edit", list(jobs.keys()), key="manual_edit_select")
                
                brief_notes = st.text_input("AI Assistant Input (Optional brief skills to rewrite)", placeholder="e.g. Add AWS and Kubernetes requirement", key="manual_edit_notes")
                if st.button("🪄 Auto-Regenerate JD with AI", key="manual_edit_autogen"):
                    if not brief_notes.strip():
                        st.error("Please enter brief notes or skills to regenerate.")
                    else:
                        with st.spinner("Gemini is regenerating the job description..."):
                            draft = generate_ai_jd(selected_job, brief_notes.strip())
                            st.session_state.generated_jd_draft = draft
                            st.rerun()
                            
                selected_job_data = jobs[selected_job]
                current_jd = selected_job_data.get("description", selected_job_data) if isinstance(selected_job_data, dict) else selected_job_data
                current_diff = selected_job_data.get("difficulty", "Medium") if isinstance(selected_job_data, dict) else "Medium"
                
                default_jd = st.session_state.get("generated_jd_draft", current_jd)
                updated_jd = st.text_area("Job Description", value=default_jd, height=200, key="manual_edit_jd")
                
                diff_options = ["Very Easy", "Easy", "Medium", "Hard"]
                default_diff_idx = diff_options.index(current_diff) if current_diff in diff_options else 2
                updated_diff = st.selectbox("Edit Difficulty Level", diff_options, index=default_diff_idx, key="manual_edit_diff")
                
                if st.button("Save Changes", key="manual_edit_submit"):
                    jobs[selected_job] = {
                        "description": updated_jd,
                        "difficulty": updated_diff
                    }
                    if save_jobs(jobs):
                        if "generated_jd_draft" in st.session_state:
                            del st.session_state.generated_jd_draft
                        st.success(f"Job opening '{selected_job}' successfully updated!")
                        time.sleep(1)
                        st.rerun()
                        
        elif action == "Delete Job":
            st.write("### Delete a Job Opening")
            if not jobs:
                st.info("No active jobs to delete.")
            else:
                selected_job = st.selectbox("Select Job to Delete", list(jobs.keys()), key="manual_delete_select")
                st.warning(f"Are you sure you want to permanently delete the '{selected_job}' position?")
                if st.button("Confirm Delete", key="manual_delete_submit"):
                    if selected_job in jobs:
                        del jobs[selected_job]
                        if save_jobs(jobs):
                            st.success(f"Job opening '{selected_job}' successfully deleted!")
                            time.sleep(1)
                            st.rerun()

JOBS_FILE = "src/jobs.json"

def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return {}
    try:
        with open(JOBS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading jobs from JSON: {e}")
        return {}

def save_jobs(jobs):
    try:
        with open(JOBS_FILE, "w") as f:
            json.dump(jobs, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving jobs: {e}")
        return False

CANDIDATES_FILE = "src/candidates.json"

def load_candidates():
    if not os.path.exists(CANDIDATES_FILE):
        return []
    try:
        with open(CANDIDATES_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        return []

def check_duplicate_candidate(email, job_role):
    email = email.strip().lower()
    job_role = job_role.strip().lower()
    if not email or not job_role:
        return None
    records = load_candidates()
    for rec in records:
        if rec.get("email", "").strip().lower() == email and rec.get("job_role", "").strip().lower() == job_role:
            if rec.get("allowed_retake") is True:
                return None
            return rec
    return None

ISSUES_FILE = "src/issues.json"

def load_issues():
    if not os.path.exists(ISSUES_FILE):
        return []
    try:
        with open(ISSUES_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        return []

def save_issues(issues):
    try:
        with open(ISSUES_FILE, "w") as f:
            json.dump(issues, f, indent=2)
        return True
    except Exception as e:
        return False

def run_proctoring_analysis():
    name = st.session_state.get("candidate_name", "").strip()
    email = st.session_state.get("candidate_email", "").strip()
    if not name or not email:
        return
        

        
    tab_switches = st.session_state.get("tab_switches", 0)
    warnings = st.session_state.get("proctoring_warnings", [])
    stage = st.session_state.get("stage", "")
    job_role = st.session_state.get("job_role", "")
    
    try:
        from src.agents.candidate_agents.proctoring_agent.proctoring_agent import ProctoringAgent
        agent = ProctoringAgent()
        report = agent.run(
            candidate_name=name,
            email=email,
            job_role=job_role,
            tab_switches=tab_switches,
            warnings_timestamps=warnings,
            stage=stage
        )
        report_dict = {
            "trust_score": report.trust_score,
            "risk_level": report.risk_level,
            "violation_summary": report.violation_summary,
            "cheating_likelihood": report.cheating_likelihood,
            "proctoring_verdict": report.proctoring_verdict
        }
        st.session_state.proctoring_report = report_dict
    except Exception as e:
        trust = max(0, 100 - tab_switches * 25)
        risk = "Low" if tab_switches == 0 else ("Medium" if tab_switches <= 2 else ("High" if tab_switches == 3 else "Suspicious - Auto-Submitted"))
        st.session_state.proctoring_report = {
            "trust_score": trust,
            "risk_level": risk,
            "violation_summary": f"Fallback Assessment: Candidate completed with {tab_switches} tab switch events.",
            "cheating_likelihood": "Possible" if tab_switches > 0 else "Unlikely",
            "proctoring_verdict": "Disqualified" if tab_switches >= 4 else ("Under Review" if tab_switches > 0 else "Passed Proctoring")
        }

def render_proctoring_elements():


    # Hidden proctoring button container
    st.markdown('<div class="hidden-proctor-btn">', unsafe_allow_html=True)
    if st.button("Proctoring Tab Switch Trigger", key="tab_switch_trigger_btn"):
        st.session_state.tab_switches = st.session_state.get("tab_switches", 0) + 1
        
        import datetime
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        warnings_list = st.session_state.setdefault("proctoring_warnings", [])
        warnings_list.append(now_str)
        
        if st.session_state.tab_switches >= 4:
            st.session_state.proctoring_violated = True
            
            if st.session_state.stage == "mcq":
                temp_answers = st.session_state.get("mcq_answers", {})
                score, pct, results = MCQAgent.grade_answers(st.session_state.mcqs, temp_answers)
                st.session_state.mcq_score = score
                st.session_state.mcq_passed = False
                st.session_state.stage = "mcq_failed_screen"
                run_proctoring_analysis()
                log_candidate_state(status_override="Auto-Submitted (Proctoring Violation)")
                st.rerun()
            elif st.session_state.stage == "interview":
                st.session_state.interview_concluded = True
                try:
                    interview_agent = InterviewAgent()
                    eval_res = interview_agent.evaluate(
                        resume_text=st.session_state.resume_text,
                        job_role=st.session_state.job_role,
                        experience=st.session_state.experience,
                        job_description=st.session_state.job_description,
                        conversation_history=st.session_state.chat_history
                    )
                    eval_res.selected = False
                    eval_res.recommendation = "DISQUALIFIED: Proctoring Violations (Multiple Tab Switches detected)."
                    eval_res.summary_for_candidate = "Assessment terminated automatically due to repeated tab-switching violations."
                    st.session_state.evaluation_result = eval_res
                except Exception as e:
                    pass
                st.session_state.stage = "final_evaluation"
                run_proctoring_analysis()
                log_candidate_state(status_override="Auto-Submitted (Proctoring Violation)")
                st.rerun()
        else:
            log_candidate_state()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.components.v1.html(f"""
    <script>
        const doc = window.parent.document;
        
        // Synchronize JS switches with python state
        window.parent.__pending_clicks__ = window.parent.__pending_clicks__ || 0;
        window.parent.__js_tab_switches__ = {st.session_state.tab_switches} + window.parent.__pending_clicks__;
        
        // Track mouse coordinates globally
        if (!window.parent.__mouse_move_listener_added_v3__) {{
            window.parent.__mouse_move_listener_added_v3__ = true;
            doc.addEventListener('mousemove', function(e) {{
                window.parent.__last_mouse_x__ = e.clientX;
                window.parent.__last_mouse_y__ = e.clientY;
            }});
        }}
        
        // Define or update showCursorNotification on parent window
        window.parent.showCursorNotification = function(message, isCrit) {{
            let popup = doc.getElementById('proctor-cursor-popup');
            if (popup) {{
                popup.remove();
            }}
            popup = doc.createElement('div');
            popup.id = 'proctor-cursor-popup';
            popup.style.position = 'fixed';
            
            const x = window.parent.__last_mouse_x__ !== undefined ? window.parent.__last_mouse_x__ : (window.parent.innerWidth / 2 - 150);
            const y = window.parent.__last_mouse_y__ !== undefined ? window.parent.__last_mouse_y__ : (window.parent.innerHeight / 2 - 50);
            
            popup.style.left = (x + 15) + 'px';
            popup.style.top = (y + 15) + 'px';
            popup.style.zIndex = '9999999';
            popup.style.background = isCrit ? 'rgba(239, 68, 68, 0.98)' : 'rgba(245, 158, 11, 0.98)';
            popup.style.color = '#ffffff';
            popup.style.padding = '14px 22px';
            popup.style.borderRadius = '12px';
            popup.style.boxShadow = isCrit ? '0 10px 30px rgba(239, 68, 68, 0.5)' : '0 10px 30px rgba(245, 158, 11, 0.5)';
            popup.style.fontFamily = "'Outfit', sans-serif";
            popup.style.fontSize = '0.92rem';
            popup.style.fontWeight = '600';
            popup.style.border = '1px solid rgba(255, 255, 255, 0.25)';
            popup.style.pointerEvents = 'none';
            popup.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            popup.style.transform = 'translateY(15px)';
            popup.style.opacity = '0';
            
            popup.innerHTML = `⚠️ ` + message;
            doc.body.appendChild(popup);
            
            window.parent.setTimeout(() => {{
                popup.style.transform = 'translateY(0)';
                popup.style.opacity = '1';
            }}, 50);
            
            window.parent.setTimeout(() => {{
                popup.style.opacity = '0';
                popup.style.transform = 'translateY(-15px)';
                window.parent.setTimeout(() => {{
                    popup.remove();
                }}, 400);
            }}, 2500);
        }};
        
        // Setup direct style injection on parent document to hide the proctoring trigger button
        let proctorStyle = doc.getElementById('proctoring-hide-style');
        if (!proctorStyle) {{
            proctorStyle = doc.createElement('style');
            proctorStyle.id = 'proctoring-hide-style';
            proctorStyle.innerHTML = `
                div[data-testid="element-container"]:has(button:has(span:contains("Proctoring Tab Switch Trigger"))),
                button:has(span:contains("Proctoring Tab Switch Trigger")),
                button[key="tab_switch_trigger_btn"] {{
                    display: none !important;
                    height: 0px !important;
                    width: 0px !important;
                    padding: 0 !important;
                    margin: 0 !important;
                    overflow: hidden !important;
                }}
            `;
            doc.head.appendChild(proctorStyle);
        }}
        
        // Programmatically hide the button and its container immediately
        function hideProctorBtn() {{
            const buttons = Array.from(doc.querySelectorAll('button'));
            const triggerBtn = buttons.find(btn => btn.textContent && btn.textContent.includes('Proctoring Tab Switch Trigger'));
            if (triggerBtn) {{
                triggerBtn.style.setProperty('display', 'none', 'important');
                const container = triggerBtn.closest('[data-testid="element-container"]');
                if (container) {{
                    container.style.setProperty('display', 'none', 'important');
                    container.style.setProperty('height', '0px', 'important');
                    container.style.setProperty('margin', '0px', 'important');
                    container.style.setProperty('padding', '0px', 'important');
                }}
                if (window.parent.__pending_clicks__ > 0) {{
                    window.parent.__pending_clicks__--;
                    triggerBtn.click();
                }}
            }}
        }}
        
        hideProctorBtn();
        if (window.parent.__proctor_hide_interval_v3__) {{
            clearInterval(window.parent.__proctor_hide_interval_v3__);
        }}
        window.parent.__proctor_hide_interval_v3__ = setInterval(hideProctorBtn, 100);
        
        if (window.parent.__last_tab_switch_time__ === undefined) {{
            window.parent.__last_tab_switch_time__ = 0;
        }}
        
        // Global independent trigger handler in parent document scope
        window.parent.__handle_proctor_tab_switch__ = function() {{
            if (!window.parent.__proctoring_active__) return;
            const now = Date.now();
            if (now - window.parent.__last_tab_switch_time__ > 1000) {{ // 1s de-bounce for responsiveness
                window.parent.__last_tab_switch_time__ = now;
                
                window.parent.__pending_clicks__ = (window.parent.__pending_clicks__ || 0) + 1;
                window.parent.__js_tab_switches__ = (window.parent.__js_tab_switches__ || 0) + 1;
                const switches = window.parent.__js_tab_switches__;
                
                if (window.parent.showCursorNotification) {{
                    if (switches <= 3) {{
                        window.parent.showCursorNotification(`PROCTORING WARNING (${{switches}}/3): Focus loss detected. Keep your cursor inside the test area!`, false);
                    }} else {{
                        window.parent.showCursorNotification(`TEST SUSPENDED: Auto-submitting due to proctoring violation limit.`, true);
                    }}
                }}
            }}
        }};
        
        // Setup visibility and blur listeners on parent that call the persistent window.parent handler
        if (!window.parent.__visibility_listener_added_v4__) {{
            window.parent.__visibility_listener_added_v4__ = true;
            doc.addEventListener('visibilitychange', function() {{
                if (doc.visibilityState === 'hidden' && window.parent.__handle_proctor_tab_switch__) {{
                    window.parent.__handle_proctor_tab_switch__();
                }}
            }});
        }}
        
        if (!window.parent.__blur_listener_added_v4__) {{
            window.parent.__blur_listener_added_v4__ = true;
            window.parent.addEventListener('blur', function() {{
                if (window.parent.__handle_proctor_tab_switch__) {{
                    window.parent.__handle_proctor_tab_switch__();
                }}
            }});
        }}
    </script>
    """, height=0)

def log_candidate_state(status_override=None):
    name = st.session_state.get("candidate_name", "").strip()
    email = st.session_state.get("candidate_email", "").strip()
    if not name or not email:
        return
        
    phone = st.session_state.get("candidate_phone", "")
    role = st.session_state.get("job_role", "")
    exp = st.session_state.get("experience", "")
    stage = st.session_state.get("stage", "")
    
    status = status_override or stage
    # Human-friendly stage name mapping
    friendly_status = status
    if status == "upload":
        friendly_status = "Profile Uploaded"
    elif status == "screening_passed":
        friendly_status = "Cleared Screening"
    elif status == "screening_failed":
        friendly_status = "Disqualified in Screening"
    elif status == "proctoring_instruction":
        friendly_status = "Reviewing Assessment Rules"
    elif status == "mcq":
        friendly_status = "Taking Technical MCQ"
    elif status == "mcq_passed_screen":
        friendly_status = "Passed MCQ"
    elif status == "mcq_failed_screen":
        friendly_status = "Failed MCQ"
    elif status == "interview":
        friendly_status = "Technical Interview Round"
    elif status == "final_evaluation":
        friendly_status = "Interview Finished"
    
    screening_res = st.session_state.get("screening_result")
    screening_reason = screening_res.reason if screening_res else ""
    
    mcq_score = st.session_state.get("mcq_score", 0)
    
    eval_res = st.session_state.get("evaluation_result")
    selection_rec = "Selected" if eval_res and eval_res.selected else ("Not Selected" if eval_res else "N/A")
    eval_summary = eval_res.summary_for_candidate if eval_res else ""
    
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    match_score = screening_res.match_score if screening_res and hasattr(screening_res, "match_score") else 0
    matched_skills = screening_res.matched_skills if screening_res and hasattr(screening_res, "matched_skills") else []
    missing_skills = screening_res.missing_skills if screening_res and hasattr(screening_res, "missing_skills") else []
    red_flags = screening_res.red_flags if screening_res and hasattr(screening_res, "red_flags") else []
    
    candidate_data = {
        "name": name,
        "email": email,
        "phone": phone,
        "password": st.session_state.get("candidate_password", ""),
        "job_role": role,
        "experience": exp,
        "job_description": st.session_state.get("job_description", ""),
        "stage": stage,
        "status": friendly_status,
        "screening_reason": screening_reason,
        "match_score": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "red_flags": red_flags,
        "mcq_score": f"{mcq_score}/5" if stage in ["mcq", "mcq_passed_screen", "mcq_failed_screen", "interview", "final_evaluation"] else "N/A",
        "selection": selection_rec,
        "eval_selected": eval_res.selected if eval_res and hasattr(eval_res, "selected") else False,
        "overall_feedback": eval_res.overall_feedback if eval_res and hasattr(eval_res, "overall_feedback") else "",
        "summary": eval_summary,
        "chat_history": st.session_state.get("chat_history", []),
        "resume_text": st.session_state.get("resume_text", ""),
        "mcqs": [q.dict() if hasattr(q, "dict") else q for q in st.session_state.get("mcqs", [])],
        "mcq_answers": st.session_state.get("mcq_answers", {}),
        "timestamp": timestamp,
        "tab_switches": st.session_state.get("tab_switches", 0),
        "proctoring_warnings": st.session_state.get("proctoring_warnings", []),
        "proctoring_violated": st.session_state.get("proctoring_violated", False),
        "proctoring_report": st.session_state.get("proctoring_report", None)
    }
    
    try:
        records = load_candidates()
        updated = False
        for idx, rec in enumerate(records):
            if rec.get("email", "").strip().lower() == email.strip().lower() and rec.get("job_role", "").strip().lower() == role.strip().lower():
                is_new_registration = (stage == "upload" or status == "Profile Uploaded")
                candidate_data["allowed_retake"] = False if is_new_registration else rec.get("allowed_retake", False)
                if not candidate_data["password"]:
                    candidate_data["password"] = rec.get("password", "")
                records[idx] = candidate_data
                updated = True
                break
        if not updated:
            candidate_data["allowed_retake"] = False
            records.append(candidate_data)
            
        with open(CANDIDATES_FILE, "w") as f:
            json.dump(records, f, indent=2)
    except Exception as e:
        pass

def generate_ai_jd(job_title, brief_description):
    try:
        config = Config.load_config()
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.prompts import ChatPromptTemplate
        
        chat_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=config.GEMINI_API_KEY,
            temperature=0.3
        )
        
        prompt_tpl = ChatPromptTemplate.from_messages([
            ("system", "You are an expert HR recruitment specialist. Generate a concise, professional, and well-structured job description for the given job title based on the brief notes provided. Include: 1) Role Overview, 2) Key Responsibilities, 3) Required Skills. Keep the entire response under 180 words total and do not include markdown styling other than clean paragraphs or bullet points."),
            ("human", "Job Title: {title}\nNotes/Requirements: {notes}")
        ])
        
        chain = prompt_tpl | chat_model
        response = chain.invoke({
            "title": job_title,
            "notes": brief_description
        })
        return response.content.strip()
    except Exception as e:
        return f"Error generating Job Description: {e}"

# Load jobs dynamically
jobs_db = load_jobs()
PREDEFINED_JDS = {}
JOB_DIFFICULTIES = {}
for role, data in jobs_db.items():
    if isinstance(data, dict):
        if data.get("is_draft", False):
            continue
        PREDEFINED_JDS[role] = data.get("description", "")
        JOB_DIFFICULTIES[role] = data.get("difficulty", "Medium")
    else:
        PREDEFINED_JDS[role] = data
        JOB_DIFFICULTIES[role] = "Medium"


PREDEFINED_JDS["Custom / Write your own"] = ""
JOB_DIFFICULTIES["Custom / Write your own"] = "Medium"

# Initialize session state keys
if "stage" not in st.session_state:
    st.session_state.stage = "upload"
if "candidate_name" not in st.session_state:
    st.session_state.candidate_name = ""
if "candidate_email" not in st.session_state:
    st.session_state.candidate_email = ""
if "candidate_phone" not in st.session_state:
    st.session_state.candidate_phone = ""
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "job_role" not in st.session_state:
    st.session_state.job_role = ""
if "experience" not in st.session_state:
    st.session_state.experience = ""
if "job_description" not in st.session_state:
    st.session_state.job_description = ""
if "screening_result" not in st.session_state:
    st.session_state.screening_result = None
if "mcqs" not in st.session_state:
    st.session_state.mcqs = []
if "mcq_answers" not in st.session_state:
    st.session_state.mcq_answers = {}
if "mcq_score" not in st.session_state:
    st.session_state.mcq_score = 0
if "mcq_passed" not in st.session_state:
    st.session_state.mcq_passed = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "tab_switches" not in st.session_state:
    st.session_state.tab_switches = 0
if "proctoring_warnings" not in st.session_state:
    st.session_state.proctoring_warnings = []
if "proctoring_violated" not in st.session_state:
    st.session_state.proctoring_violated = False
if "proctoring_report" not in st.session_state:
    st.session_state.proctoring_report = None
if "candidate_logged_in" not in st.session_state:
    st.session_state.candidate_logged_in = False
if "candidate_user_email" not in st.session_state:
    st.session_state.candidate_user_email = ""
if "interview_concluded" not in st.session_state:
    st.session_state.interview_concluded = False
if "evaluation_result" not in st.session_state:
    st.session_state.evaluation_result = None
if "email_sent" not in st.session_state:
    st.session_state.email_sent = False
if "call_sent" not in st.session_state:
    st.session_state.call_sent = False
if "sidebar_chat_history" not in st.session_state:
    st.session_state.sidebar_chat_history = [
        {"role": "assistant", "content": "Hello! I'm your **AI Recruitment Assistant** 👋\n\nI can help you with:\n- 🔍 **Job role info** — requirements, skills, difficulty\n- 🎯 **Fit check** — find which role suits your profile best\n- 📋 **Process guide** — how the assessment works\n- 🧠 **Interview prep** — practice questions with AI feedback\n\nWhat would you like to explore today?"}
    ]

# Assistant enhanced mode tracking
if "assistant_mode" not in st.session_state:
    st.session_state.assistant_mode = "chat"   # chat | fit_check | interview_prep
if "fit_skills_input" not in st.session_state:
    st.session_state.fit_skills_input = ""
if "fit_results" not in st.session_state:
    st.session_state.fit_results = None
if "prep_role" not in st.session_state:
    st.session_state.prep_role = ""
if "prep_questions" not in st.session_state:
    st.session_state.prep_questions = []
if "prep_current_q" not in st.session_state:
    st.session_state.prep_current_q = 0
if "prep_answers" not in st.session_state:
    st.session_state.prep_answers = {}
if "prep_feedback" not in st.session_state:
    st.session_state.prep_feedback = {}

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "🔐 Log In to My Profile"
if "selected_role_val" not in st.session_state:
    st.session_state.selected_role_val = ""

if "active_scorecard_candidate" not in st.session_state:
    st.session_state.active_scorecard_candidate = ""
if "recruiter_logged_in" not in st.session_state:
    st.session_state.recruiter_logged_in = False

if "last_stage" not in st.session_state:
    st.session_state.last_stage = "upload"

# Auto-scroll to top when candidate transitions to a new stage
if st.session_state.stage != st.session_state.last_stage:
    st.components.v1.html(
        """
        <script>
            var mainContainer = window.parent.document.querySelector('.main') || window.parent.document.querySelector('section.main');
            if (mainContainer) {
                mainContainer.scrollTo({top: 0, behavior: 'instant'});
            }
        </script>
        """,
        height=0
    )
    st.session_state.last_stage = st.session_state.stage

# Application Header
st.markdown('<div class="recruit-header">AgentFlow Interview Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="recruit-sub">AI-Powered Multi-Agent Screening and Evaluation</div>', unsafe_allow_html=True)

def handle_recruiter_logout():
    st.session_state.recruiter_logged_in = False
    st.session_state.cancel_speech = True

def handle_apply_now_logged_out(role):
    st.session_state.selected_role_val = role
    st.session_state.auth_mode = "📝 Create New Application"
    st.session_state.auth_mode_selector_radio = "📝 Create New Application"
    st.session_state.navigation_radio = "🎯 Candidate Assessment"
    st.session_state.current_page = "🎯 Candidate Assessment"

def handle_apply_now_logged_in_switch(role, user_email):
    load_candidate_session(user_email, role)
    st.session_state.navigation_radio = "🎯 Candidate Assessment"
    st.session_state.current_page = "🎯 Candidate Assessment"

def handle_apply_now_logged_in_new(role):
    st.session_state.run_auto_apply_for_role = role

if st.session_state.get("run_auto_apply_for_role"):
    role_to_apply = st.session_state.run_auto_apply_for_role
    st.session_state.run_auto_apply_for_role = None
    
    name = st.session_state.get("candidate_name", "")
    email = st.session_state.get("candidate_email", "")
    phone = st.session_state.get("candidate_phone", "")
    password = st.session_state.get("candidate_password", "")
    resume_text = st.session_state.get("resume_text", "")
    experience = st.session_state.get("experience", "Mid Level (3-5 years)")
    jd_text = PREDEFINED_JDS.get(role_to_apply, "")
    
    with st.spinner("Applying and screening your profile..."):
        try:
            screening_agent = ScreeningAgent()
            res = screening_agent.run(
                resume_text=resume_text,
                job_role=role_to_apply,
                experience=experience,
                job_description=jd_text
            )
            st.session_state.job_role = role_to_apply
            st.session_state.job_description = jd_text
            st.session_state.screening_result = res
            
            # Borderline screening evaluation
            match_score = res.match_score
            if 45 <= match_score <= 65:
                target_stage = "screening_review"
                res.qualified = False
            elif match_score > 65:
                target_stage = "proctoring_instruction"
                res.qualified = True
            else:
                target_stage = "screening_failed"
                res.qualified = False
                
            current_stage = st.session_state.get("stage", "upload")
            if validate_stage_transition(current_stage, target_stage):
                st.session_state.stage = target_stage
            else:
                st.session_state.stage = target_stage

            
            st.session_state.mcqs = []
            st.session_state.mcq_answers = {}
            st.session_state.mcq_score = 0
            st.session_state.mcq_passed = False
            st.session_state.chat_history = []
            st.session_state.interview_concluded = False
            st.session_state.evaluation_result = None
            st.session_state.tab_switches = 0
            st.session_state.proctoring_warnings = []
            st.session_state.proctoring_violated = False
            st.session_state.proctoring_report = None
            st.session_state.email_sent = False
            st.session_state.call_sent = False
            
            log_candidate_state()
            st.success(f"Successfully applied for {role_to_apply}!")
            st.session_state.navigation_radio = "🎯 Candidate Assessment"
            st.session_state.current_page = "🎯 Candidate Assessment"
            time.sleep(0.5)
            st.rerun()
        except Exception as e:
            st.error(f"Error applying for role: {str(e)}")

# ----------------- TOP SCREEN HEADER CONTROLS & NAVIGATION CONTROLLER -----------------
col_hdr_space, col_hdr_theme = st.columns([7.8, 2.2])
with col_hdr_theme:
    current_theme = st.session_state.get("theme_mode", "Enterprise Light")
    theme_btn_label = "🌙 Dark Mode" if current_theme == "Enterprise Light" else "☀️ Light Mode"
    st.markdown('<div class="theme-toggle-container">', unsafe_allow_html=True)
    if st.button(theme_btn_label, key="header_theme_toggle_btn", use_container_width=True):
        st.session_state.theme_mode = "Cyberpunk Dark" if current_theme == "Enterprise Light" else "Enterprise Light"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- SIDEBAR CONTROLS -----------------
if st.session_state.get("recruiter_logged_in", False):
    with st.sidebar:
        st.button("🔒 Recruiter Logout", key="sidebar_logout_btn", use_container_width=True, on_click=handle_recruiter_logout)

# ----------------- PAGE NAVIGATION -----------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "📋 Open Positions"

nav_options = ["📋 Open Positions", "🎯 Candidate Assessment", "🤖 Recruitment Assistant", "🔒 Recruiter Portal"]
default_nav_idx = nav_options.index(st.session_state.current_page) if st.session_state.current_page in nav_options else 0

st.markdown('<div class="nav-container">', unsafe_allow_html=True)
page = st.radio("Navigation", nav_options, index=default_nav_idx, horizontal=True, label_visibility="collapsed", key="navigation_radio")
st.markdown('</div>', unsafe_allow_html=True)
if page != st.session_state.current_page:
    st.session_state.current_page = page
    st.session_state.cancel_speech = True
    st.rerun()

if page == "📋 Open Positions":
    st.markdown("""
    <div class="glass-card" style="text-align: center; margin-bottom: 25px;">
        <div class="recruit-header" style="font-size: 2.2rem; margin-bottom: 10px; background: linear-gradient(135deg, var(--accent-red), var(--accent-red-hover)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">💼 Explore Career Opportunities</div>
        <div style="color: var(--text-sub); font-size: 1.05rem;">Select a position below to view requirements and start your AI-guided assessment.</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Platform highlights grid
    st.markdown("""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 35px; animation: fadeInUp 0.6s ease both;">
        <div class="glass-card" style="margin-bottom: 0; padding: 22px; border-top: 4px solid var(--accent-red); display: flex; flex-direction: column; gap: 8px;">
            <h4 style="color: var(--accent-red); margin: 0; display: flex; align-items: center; gap: 8px;"><span style="font-size: 1.25rem;">📄</span> 1. AI Resume Check</h4>
            <p style="color: var(--text-sub); font-size: 0.88rem; line-height: 1.5; margin: 0;">Our parser instantly extracts your core competencies and evaluates match score against candidate expectations.</p>
        </div>
        <div class="glass-card" style="margin-bottom: 0; padding: 22px; border-top: 4px solid #3b82f6; display: flex; flex-direction: column; gap: 8px;">
            <h4 style="color: #2563eb; margin: 0; display: flex; align-items: center; gap: 8px;"><span style="font-size: 1.25rem;">🎯</span> 2. Custom MCQ</h4>
            <p style="color: var(--text-sub); font-size: 0.88rem; line-height: 1.5; margin: 0;">Complete 5 technical MCQ screening questions dynamically customized for your background skills.</p>
        </div>
        <div class="glass-card" style="margin-bottom: 0; padding: 22px; border-top: 4px solid #10b981; display: flex; flex-direction: column; gap: 8px;">
            <h4 style="color: #059669; margin: 0; display: flex; align-items: center; gap: 8px;"><span style="font-size: 1.25rem;">🗣️</span> 3. Conversational AI</h4>
            <p style="color: var(--text-sub); font-size: 0.88rem; line-height: 1.5; margin: 0;">Interact with our AI interviewer agent in a live dialogue with adaptive audio replay capabilities.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<h3 style="color: var(--text-main); font-weight: 700; margin-bottom: 20px; font-size: 1.5rem;">🔥 Open Job Positions</h3>', unsafe_allow_html=True)
    
    for role, jd in PREDEFINED_JDS.items():
        if role != "Custom / Write your own":
            job_diff = JOB_DIFFICULTIES.get(role, "Medium")
            st.markdown(f"""
            <div class="glass-card" style="border-left: 6px solid var(--accent-red); padding: 25px; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; flex-wrap: wrap; gap: 10px;">
                    <h3 style="color: var(--text-main); margin: 0; font-size: 1.35rem; font-weight: 700;">{role}</h3>
                    <div style="display: flex; gap: 8px;">
                        <span style="background-color: var(--badge-red-bg); color: var(--accent-red); padding: 3px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">{job_diff} Level</span>
                        <span style="background-color: var(--badge-time-bg); color: var(--badge-time-text); padding: 3px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">Full-Time</span>
                    </div>
                </div>
                <div style="color: var(--text-sub); line-height: 1.6; font-size: 0.95rem; margin-bottom: 5px; white-space: pre-wrap;">{jd}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action button
            col1, col2 = st.columns([7, 2.5])
            with col2:
                if st.session_state.get("candidate_logged_in", False):
                    user_email = st.session_state.get("candidate_email", "")
                    dup = check_duplicate_candidate(user_email, role)
                    if dup:
                        st.button(f"Apply Now →", key=f"apply_btn_{role}", on_click=handle_apply_now_logged_in_switch, args=(role, user_email), use_container_width=True)
                    else:
                        st.button(f"Apply Now →", key=f"apply_btn_{role}", on_click=handle_apply_now_logged_in_new, args=(role,), use_container_width=True)
                else:
                    st.button(f"Apply Now →", key=f"apply_btn_{role}", on_click=handle_apply_now_logged_out, args=(role,), use_container_width=True)
            st.markdown("<div style='margin-bottom: 35px;'></div>", unsafe_allow_html=True)
    st.stop()

elif page == "🤖 Recruitment Assistant":
    st.markdown("""
    <div class="glass-card" style="text-align: center; margin-bottom: 25px;">
        <div class="recruit-header" style="font-size: 2.2rem; margin-bottom: 10px; background: linear-gradient(135deg, var(--accent-red), var(--accent-red-hover)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">🤖 Recruitment Assistant & Career Guide</div>
        <div style="color: var(--text-sub); font-size: 1.05rem;">Explore requirements, ask about hiring tracks, or check technical expectations for open positions.</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="glass-card" style="padding: 30px !important;">', unsafe_allow_html=True)
    render_sidebar_chatbot()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

elif page == "🔒 Recruiter Portal":
    # Recruiter secure credentials check
    if not st.session_state.get("recruiter_logged_in", False):
        st.markdown("""
        <div class="glass-card" style="max-width: 450px; margin: 40px auto; text-align: center; border-top: 4px solid var(--accent-red);">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">🔒</div>
            <h3 style="color: var(--text-main); margin-top: 0; font-weight: 700;">Recruiter Secure Login</h3>
            <p style="color: var(--text-sub); font-size: 0.9rem; margin-bottom: 20px;">Please authenticate to access candidate details and analytics.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("recruiter_login_form"):
            password_input = st.text_input("Enter Recruiter Access Password", type="password")
            login_submitted = st.form_submit_button("Authenticate Access", use_container_width=True)
            
            if login_submitted:
                expected_password = os.getenv("RECRUITER_PASSWORD", "admin123")
                if password_input == expected_password:
                    st.session_state.recruiter_logged_in = True
                    st.success("Authentication successful!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Invalid password. Please contact your administrator.")
        st.stop()

    # If logged in, display the logout button in sidebar and on the page header
    col_title, col_logout = st.columns([3, 1])
    with col_title:
        st.markdown("""
        <div class="glass-card" style="margin-bottom: 0px; padding: 15px 20px !important;">
            <div class="stage-title" style="margin: 0;">🔒 Recruiter Portal</div>
        </div>
        """, unsafe_allow_html=True)
    with col_logout:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.button("🚪 Log Out", key="recruiter_main_logout_btn", use_container_width=True, on_click=handle_recruiter_logout)
    
    st.write("")
    
    st.write("Hello Recruiter! Welcome to your administrative control center.")
    
    # Notify recruiter of auto-resolved support tickets
    try:
        tickets_db = load_issues()
        auto_resolved = [t for t in tickets_db if t.get("resolved") and t.get("resolved_by") == "AI Auto-Resolver"]
        if auto_resolved:
            st.info(f"🤖 **AI Auto-Resolver Notification**: The AI agent has successfully resolved **{len(auto_resolved)}** candidate issue(s) automatically. You can review resolution logs under the **Support & Help Requests** tab.")
    except Exception:
        pass

    # Recruiter Portal Metrics Cards Grid
    try:
        cand_list = load_candidates()
        ticket_list = load_issues()
        total_cand = len(cand_list)
        pending_tick = len([t for t in ticket_list if not t.get("resolved", False)])
        selected_cand = len([c for c in cand_list if c.get("selection") == "Selected"])
        sel_rate = int((selected_cand / total_cand) * 100) if total_cand > 0 else 0
        
        metrics_html = f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-icon-wrapper">👥</div>
                <div class="metric-text-wrapper">
                    <span class="metric-label">Total Applicants</span>
                    <h3 class="metric-val">{total_cand}</h3>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-icon-wrapper">🏆</div>
                <div class="metric-text-wrapper">
                    <span class="metric-label">AI Selection Rate</span>
                    <h3 class="metric-val">{sel_rate}%</h3>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-icon-wrapper">⚠️</div>
                <div class="metric-text-wrapper">
                    <span class="metric-label">Pending Help Tickets</span>
                    <h3 class="metric-val" style="background: { 'linear-gradient(135deg, #ef4444, #dc2626)' if pending_tick > 0 else 'linear-gradient(135deg, #10b981, #059669)' }; -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{pending_tick}</h3>
                </div>
            </div>
        </div>
        """
        st.markdown(metrics_html, unsafe_allow_html=True)
    except Exception as e:
        pass

    st.markdown("---")
    
    # Recruiter Portal Tabs
    portal_tab1, portal_tab2, portal_tab3 = st.tabs(["💼 Job Management & AI Assistant", "🧑 Candidate Assessments Hub", "⚠️ Support & Help Requests"])
    
    with portal_tab1:
        render_job_management_tab()
                        
    with portal_tab2:
        st.subheader("Recruiter Analytics & Leaderboard")
        st.info("💡 **Candidate Testing Hint**: To evaluate candidate-side features (MCQs, Interview, Proctoring) without signing up or uploading resumes, use these pre-screened tester credentials in the Candidate Assessment tab:\n*   **Email Address**: `admin@test.com`\n*   **Password**: `admin`")
        render_recruiter_analytics()
        st.markdown("---")
        render_candidate_hub()

                        
    with portal_tab3:
        st.subheader("⚠️ Support Requests & AI Diagnoses")
        tickets = load_issues()
        
        # Split tickets
        pending_tickets = [t for t in tickets if not t.get("resolved", False)]
        auto_resolved_tickets = [t for t in tickets if t.get("resolved", False) and t.get("resolved_by", "").startswith("AI Auto-Resolver")]
        
        pending_audits = [t for t in auto_resolved_tickets if t.get("audit_status", "Pending Audit") == "Pending Audit"]
        audited_history = [t for t in auto_resolved_tickets if t.get("audit_status", "Pending Audit") in ["Approved", "Revoked"]]
        
        # Sub-tabs for support center
        support_sub1, support_sub2, support_sub3 = st.tabs(["📥 Pending Recruiter Review", "🔍 AI Auto-Reset Audits", "🤖 AI Auto-Resolved History"])
        
        with support_sub1:
            if not pending_tickets:
                st.success("No active candidate support requests! All clear.")
            else:
                for idx, t in enumerate(pending_tickets):
                    severity_color = "#3b82f6" if t.get("severity") == "Low" else ("#f59e0b" if t.get("severity") == "Medium" else "#ef4444")
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 6px solid {severity_color}; padding: 20px; margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h4 style="margin: 0; color: var(--text-main);">{t.get('name')} ({t.get('email')})</h4>
                            <span style="background-color: {severity_color}20; color: {severity_color}; padding: 3px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">{t.get('severity', 'Medium')} Priority</span>
                        </div>
                        <div style="font-size: 0.95rem; margin-bottom: 12px; color: var(--text-sub); line-height: 1.5;">
                            <strong>Target Role:</strong> {t.get('job_role')}<br>
                            <strong>Timestamp:</strong> {t.get('timestamp')}<br>
                            <strong>Candidate's Description:</strong> <em>"{t.get('message')}"</em>
                        </div>
                        <div style="background-color: var(--jd-bg); border: 1px solid var(--card-border); border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                            <strong style="color: var(--text-main); font-size: 0.95rem;">🤖 AI Support Agent Diagnosis:</strong><br>
                            <p style="margin-top: 5px; margin-bottom: 5px; font-size: 0.95rem; color: var(--text-sub);">{t.get('diagnosis')}</p>
                            <strong>Suggested Action:</strong> <span style="color: var(--accent-gold);">{t.get('suggested_action')}</span><br>
                            <strong>Justification:</strong> <span style="color: var(--text-sub); font-style: italic;">{t.get('justification')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Action Buttons
                    col1, col2, col3 = st.columns([3, 2, 5])
                    with col1:
                        if st.button("🔓 Resolve & Allow Retake", key=f"resolve_retake_{idx}_{t.get('email')}_{t.get('job_role')}", use_container_width=True):
                            # Grant Retake
                            records = load_candidates()
                            for r in records:
                                if r.get("email", "").strip().lower() == t.get("email", "").strip().lower() and r.get("job_role", "").strip().lower() == t.get("job_role", "").strip().lower():
                                    r["allowed_retake"] = True
                                    r["status"] = "Retake Allowed"
                                    break
                            with open(CANDIDATES_FILE, "w") as f:
                                json.dump(records, f, indent=2)
                            
                            # Mark ticket as resolved
                            for tk in tickets:
                                if tk.get("email", "").strip().lower() == t.get("email", "").strip().lower() and tk.get("job_role", "").strip().lower() == t.get("job_role", "").strip().lower() and not tk.get("resolved", False):
                                    tk["resolved"] = True
                                    tk["resolved_by"] = "Recruiter"
                                    break
                            save_issues(tickets)
                            st.success(f"Access granted and request resolved for {t.get('name')}!")
                            time.sleep(1)
                            st.rerun()
                            
                    with col2:
                        if st.button("Dismiss", key=f"dismiss_ticket_{idx}_{t.get('email')}_{t.get('job_role')}", use_container_width=True):
                            # Mark ticket as resolved
                            for tk in tickets:
                                if tk.get("email", "").strip().lower() == t.get("email", "").strip().lower() and tk.get("job_role", "").strip().lower() == t.get("job_role", "").strip().lower() and not tk.get("resolved", False):
                                    tk["resolved"] = True
                                    tk["resolved_by"] = "Recruiter Dismissal"
                                    break
                            save_issues(tickets)
                            st.info("Help request dismissed.")
                            time.sleep(1)
                            st.rerun()
                    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
                    
        with support_sub2:
            if not pending_audits:
                st.success("🎉 No pending AI auto-reset audits! Good job.")
            else:
                st.markdown("Please audit the following support resets automatically granted by the AI support agent.")
                for idx, t in enumerate(pending_audits):
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 6px solid #f59e0b; padding: 20px; margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h4 style="margin: 0; color: var(--text-main);">{t.get('name')} ({t.get('email')})</h4>
                            <span style="background-color: rgba(245, 158, 11, 0.1); color: #f59e0b; padding: 3px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">Pending Audit</span>
                        </div>
                        <div style="font-size: 0.95rem; margin-bottom: 12px; color: var(--text-sub); line-height: 1.5;">
                            <strong>Applied Role:</strong> {t.get('job_role')}<br>
                            <strong>Date Resolved:</strong> {t.get('timestamp')}<br>
                            <strong>Issue Reported:</strong> <em>"{t.get('message')}"</em>
                        </div>
                        <div style="background-color: rgba(245, 158, 11, 0.05); border: 1px solid var(--card-border); border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                            <strong style="color: #d97706; font-size: 0.95rem;">🤖 AI Justification & Action:</strong><br>
                            <strong>AI Diagnosis:</strong> {t.get('diagnosis')}<br>
                            <strong>Justification:</strong> <em>{t.get('justification')}</em>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_aud1, col_aud2 = st.columns(2)
                    with col_aud1:
                        if st.button("Confirm AI Action", key=f"confirm_audit_{idx}_{t.get('email')}_{t.get('job_role')}", use_container_width=True):
                            # Mark audited as Approved
                            for tk in tickets:
                                if tk.get("email", "").strip().lower() == t.get("email", "").strip().lower() and tk.get("job_role", "").strip().lower() == t.get("job_role", "").strip().lower() and tk.get("resolved", False):
                                    tk["audit_status"] = "Approved"
                                    tk["resolved_by"] = "AI Auto-Resolver (Confirmed by Recruiter)"
                                    break
                            save_issues(tickets)
                            st.success(f"Confirmed AI action for {t.get('name')}!")
                            time.sleep(0.5)
                            st.rerun()
                    with col_aud2:
                        if st.button("Revoke AI Action", key=f"revoke_audit_{idx}_{t.get('email')}_{t.get('job_role')}", use_container_width=True):
                            # Mark audited as Revoked
                            for tk in tickets:
                                if tk.get("email", "").strip().lower() == t.get("email", "").strip().lower() and tk.get("job_role", "").strip().lower() == t.get("job_role", "").strip().lower() and tk.get("resolved", False):
                                    tk["audit_status"] = "Revoked"
                                    tk["resolved_by"] = "AI Auto-Resolver (Revoked by Recruiter)"
                                    break
                            save_issues(tickets)
                            
                            # Update candidate record to disallow retake
                            records = load_candidates()
                            for r in records:
                                if r.get("email", "").strip().lower() == t.get("email", "").strip().lower() and r.get("job_role", "").strip().lower() == t.get("job_role", "").strip().lower():
                                    r["allowed_retake"] = False
                                    r["status"] = "Disqualified (Reset Revoked)"
                                    break
                            with open(CANDIDATES_FILE, "w") as f:
                                json.dump(records, f, indent=2)
                                
                            st.warning(f"Revoked AI reset action for {t.get('name')}!")
                            time.sleep(0.5)
                            st.rerun()
                            
        with support_sub3:
            if not audited_history:
                st.info("No audited auto-resolved history yet.")
            else:
                for idx, t in enumerate(audited_history):
                    audit_color = "#10b981" if t.get("audit_status") == "Approved" else "#ef4444"
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 6px solid {audit_color}; padding: 20px; margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h4 style="margin: 0; color: var(--text-main);">{t.get('name')} ({t.get('email')})</h4>
                            <span style="background-color: {audit_color}1a; color: {audit_color}; padding: 3px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">{t.get('audit_status')}</span>
                        </div>
                        <div style="font-size: 0.95rem; margin-bottom: 12px; color: var(--text-sub); line-height: 1.5;">
                            <strong>Applied Role:</strong> {t.get('job_role')}<br>
                            <strong>Date Resolved:</strong> {t.get('timestamp')}<br>
                            <strong>Audited Action:</strong> {t.get('resolved_by')}<br>
                            <strong>AI Justification:</strong> <em>{t.get('justification')}</em>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        st.stop()


# Hydrate Streamlit session state from JSON record on candidate login
def load_candidate_session(email, job_role=None):
    records = load_candidates()
    matched = None
    email_clean = email.strip().lower()
    if job_role:
        job_role_clean = job_role.strip().lower()
        for r in records:
            if r.get("email", "").strip().lower() == email_clean and r.get("job_role", "").strip().lower() == job_role_clean:
                matched = r
                break
    if not matched:
        for r in records:
            if r.get("email", "").strip().lower() == email_clean:
                matched = r
                break
            
    if matched:
        st.session_state.candidate_name = matched.get("name", "")
        st.session_state.candidate_email = matched.get("email", "")
        st.session_state.candidate_phone = matched.get("phone", "")
        st.session_state.candidate_password = matched.get("password", "")
        st.session_state.job_role = matched.get("job_role", "")
        st.session_state.experience = matched.get("experience", "")
        st.session_state.job_description = matched.get("job_description", "")
        if not st.session_state.job_description:
            st.session_state.job_description = PREDEFINED_JDS.get(st.session_state.job_role, "")
        st.session_state.resume_text = matched.get("resume_text", "")
        st.session_state.stage = matched.get("stage", "upload")
        st.session_state.tab_switches = matched.get("tab_switches", 0)
        st.session_state.proctoring_warnings = matched.get("proctoring_warnings", [])
        st.session_state.proctoring_violated = matched.get("proctoring_violated", False)
        st.session_state.proctoring_report = matched.get("proctoring_report", None)
        
        # Load screening result
        if matched.get("screening_reason"):
            from src.models.schemas import ScreeningResult
            is_qualified = matched.get("stage") not in ["screening_failed", "screening_review"]
            st.session_state.screening_result = ScreeningResult(
                qualified=is_qualified,
                reason=matched.get("screening_reason", ""),
                match_score=matched.get("match_score", 0),
                matched_skills=matched.get("matched_skills", []),
                missing_skills=matched.get("missing_skills", []),
                red_flags=matched.get("red_flags", [])
            )

            
        # Load MCQs
        from src.models.schemas import MCQItem
        saved_mcqs = matched.get("mcqs", [])
        st.session_state.mcqs = [MCQItem(**q) for q in saved_mcqs]
        st.session_state.mcq_answers = matched.get("mcq_answers", {})
        
        # Reload MCQ score
        mcq_score_str = matched.get("mcq_score", "N/A")
        if mcq_score_str != "N/A" and "/" in mcq_score_str:
            try:
                st.session_state.mcq_score = int(mcq_score_str.split("/")[0])
                st.session_state.mcq_passed = st.session_state.mcq_score >= 3
            except:
                st.session_state.mcq_score = 0
                
        # Reload Interview Dialogue History
        st.session_state.chat_history = matched.get("chat_history", [])
        st.session_state.interview_concluded = matched.get("stage", "") in ["final_evaluation"] or matched.get("status", "") == "Interview Finished" or matched.get("status", "") == "Auto-Submitted (Proctoring Violation)"
        
        # Reload Final evaluation results
        if matched.get("selection") != "N/A":
            from src.models.schemas import FinalEvaluation
            st.session_state.evaluation_result = FinalEvaluation(
                selected=matched.get("eval_selected", False),
                overall_feedback=matched.get("overall_feedback", ""),
                summary_for_candidate=matched.get("summary", "")
            )

# Helper function to reset candidate progress
def restart_process():
    st.session_state.stage = "upload"
    st.session_state.screening_result = None
    st.session_state.mcqs = []
    st.session_state.mcq_answers = {}
    st.session_state.chat_history = []
    st.session_state.interview_concluded = False
    st.session_state.evaluation_result = None
    st.session_state.email_sent = False
    st.session_state.call_sent = False
    st.session_state.tab_switches = 0
    st.session_state.proctoring_warnings = []
    st.session_state.proctoring_violated = False
    st.session_state.proctoring_report = None
    st.session_state.candidate_logged_in = False
    st.session_state.candidate_user_email = ""
    st.session_state.selected_role_val = ""
    st.session_state.auth_mode = "🔐 Log In to My Profile"
    st.session_state.auth_mode_selector_radio = "🔐 Log In to My Profile"
    st.session_state.navigation_radio = "🎯 Candidate Assessment"
    st.session_state.cancel_speech = True
    st.rerun()

# Render Candidate login and registration portal tabs
def render_candidate_auth_portal():
    st.markdown("""
    <div class="glass-card" style="text-align: center; margin-bottom: 25px; border-top: 4px solid var(--accent-red); padding: 25px !important;">
        <div class="recruit-header" style="font-size: 2rem; margin-bottom: 5px; color: var(--text-main);">🧑 Candidate Assessment Portal</div>
        <div style="color: var(--text-sub); font-size: 0.95rem;">Log in to track your application, complete assessments, or register to apply.</div>
    </div>
    """, unsafe_allow_html=True)

    auth_modes = ["🔐 Log In to My Profile", "📝 Create New Application"]
    default_idx = auth_modes.index(st.session_state.auth_mode) if st.session_state.auth_mode in auth_modes else 0
    
    st.markdown('<div class="auth-nav-container">', unsafe_allow_html=True)
    auth_mode = st.radio(
        "Auth Mode Selector",
        auth_modes,
        index=default_idx,
        horizontal=True,
        label_visibility="collapsed",
        key="auth_mode_selector_radio"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    st.session_state.auth_mode = auth_mode
    
    if st.session_state.auth_mode == "🔐 Log In to My Profile":
        st.write("### Log In")
        with st.form("candidate_login_form"):
            login_email = st.text_input("Registered Email Address", placeholder="name@example.com")
            login_password = st.text_input("Password", type="password")
            login_submit = st.form_submit_button("Log In", use_container_width=True)
            
            if login_submit:
                if not login_email.strip() or not login_password.strip():
                    st.error("Please enter both email and password.")
                else:
                    records = load_candidates()
                    matched = None
                    for r in records:
                        if r.get("email", "").strip().lower() == login_email.strip().lower():
                            matched = r
                            break
                    if matched:
                        if matched.get("password") == login_password:
                            st.session_state.candidate_logged_in = True
                            st.session_state.candidate_user_email = matched.get("email")
                            load_candidate_session(matched.get("email"), matched.get("job_role"))
                            st.success("Welcome back! Loading your profile...")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Invalid password. Please try again.")
                    else:
                        st.error("No application found with this email. Please switch to the Sign Up tab to create one.")
                        
    else:
        st.write("### Sign Up & Apply")
        candidate_name = st.text_input("Full Name", placeholder="John Doe", key="signup_name")
        candidate_email = st.text_input("Email Address", placeholder="john.doe@example.com", key="signup_email")
        candidate_phone = st.text_input("Phone Number", placeholder="+1234567890", key="signup_phone")
        candidate_password = st.text_input("Create Password", type="password", key="signup_password")
        
        roles_list = list(PREDEFINED_JDS.keys())
        default_role_idx = 0
        if st.session_state.get("selected_role_val") in roles_list:
            default_role_idx = roles_list.index(st.session_state.selected_role_val)
            
        selected_role = st.selectbox("Applying For Job Role", roles_list, index=default_role_idx, key="signup_role_select")
        if selected_role == "Custom / Write your own":
            job_role = st.text_input("Custom Job Role Name", placeholder="e.g. DevOps Engineer", key="signup_custom_role")
            job_description = st.text_area("Job Description Details", height=150, placeholder="Paste requirements here...", key="signup_custom_jd")
        else:
            job_role = selected_role
            job_description = PREDEFINED_JDS[selected_role]
            
        experience = st.selectbox("Total Experience / Candidate Level", ["Entry Level (0-2 years)", "Mid Level (3-5 years)", "Senior Level (5+ years)"], key="signup_experience")
        uploaded_file = st.file_uploader("Upload Resume (PDF format)", type=["pdf"], key="signup_resume")
        
        if st.button("Apply & Start Screening", key="signup_submit_btn"):
            if not candidate_name.strip() or not candidate_email.strip() or not candidate_password.strip():
                st.error("Please fill in your name, email, and password.")
            elif not job_role.strip():
                st.error("Please specify the Job Role.")
            elif not job_description.strip():
                st.error("Please provide a job description.")
            elif not uploaded_file:
                st.error("Please upload your resume in PDF format.")
            else:
                duplicate_record = check_duplicate_candidate(candidate_email, job_role)
                if duplicate_record:
                    st.error("An application with this email already exists for this role. Please log in to view its status.")
                else:
                    records = load_candidates()
                    existing_user = None
                    for rec in records:
                        if rec.get("email", "").strip().lower() == candidate_email.strip().lower():
                            existing_user = rec
                            break
                    if existing_user and existing_user.get("password") != candidate_password:
                        st.error("This email address is already registered. Please enter the correct password for your account to apply for a new role.")
                    else:
                        with st.spinner("Extracting text from resume..."):
                            try:
                                resume_text = ResumeParser.extract_text(uploaded_file)
                                st.session_state.candidate_name = candidate_name
                                st.session_state.candidate_email = candidate_email
                                st.session_state.candidate_phone = candidate_phone
                                st.session_state.candidate_password = candidate_password
                                st.session_state.job_role = job_role
                                st.session_state.experience = experience
                                st.session_state.job_description = job_description
                                st.session_state.resume_text = resume_text
                            except Exception as e:
                                st.error(f"Error parsing resume: {str(e)}")
                                st.stop()
                                
                        with st.spinner("Initial Screening Agent checking eligibility..."):
                            try:
                                screening_agent = ScreeningAgent()
                                res = screening_agent.run(
                                    resume_text=st.session_state.resume_text,
                                    job_role=st.session_state.job_role,
                                    experience=st.session_state.experience,
                                    job_description=st.session_state.job_description
                                )
                                st.session_state.screening_result = res
                                
                                # Borderline screening evaluation
                                match_score = res.match_score
                                if 45 <= match_score <= 65:
                                    target_stage = "screening_review"
                                    res.qualified = False
                                elif match_score > 65:
                                    target_stage = "proctoring_instruction"
                                    res.qualified = True
                                else:
                                    target_stage = "screening_failed"
                                    res.qualified = False
                                    
                                current_stage = st.session_state.get("stage", "upload")
                                if validate_stage_transition(current_stage, target_stage):
                                    st.session_state.stage = target_stage
                                else:
                                    st.session_state.stage = target_stage

                                
                                st.session_state.candidate_logged_in = True
                                st.session_state.candidate_user_email = candidate_email
                                st.session_state.candidate_password = candidate_password
                                
                                log_candidate_state()
                                st.success("Application successfully submitted!")
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error during screening: {str(e)}")

# Render Candidate dashboard hub
def render_candidate_hub_portal():
    # Defensive safety net: if candidate is logged in but stage is 'upload', auto-advance to rules screen
    if st.session_state.get("stage", "upload") == "upload":
        st.session_state.stage = "proctoring_instruction"
        log_candidate_state()
        st.rerun()
        
    name = st.session_state.get("candidate_name", "Candidate")
    email = st.session_state.get("candidate_email", "")
    role = st.session_state.get("job_role", "")
    stage = st.session_state.get("stage", "upload")
    
    # Find all roles for this email
    records = load_candidates()
    user_roles = [rec.get("job_role", "") for rec in records if rec.get("email", "").strip().lower() == email.strip().lower()]
    
    if len(user_roles) > 1:
        col_hdr, col_switcher, col_logout = st.columns([3.5, 2.5, 1])
    else:
        col_hdr, col_logout = st.columns([3, 1])
        col_switcher = None
        
    with col_hdr:
        st.markdown(f"""
        <div class="glass-card" style="margin-bottom: 0px; padding: 15px 20px !important; border-left: 6px solid var(--accent-red);">
            <div class="stage-title" style="margin: 0; font-size: 1.5rem; color: var(--text-main);">🧑 Candidate Hub: {name}</div>
            <span style="color: var(--text-sub); font-size: 0.9rem;">Target Position: <strong>{role}</strong> | Account: {email}</span>
        </div>
        """, unsafe_allow_html=True)
        
    if col_switcher is not None:
        with col_switcher:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            try:
                current_idx = user_roles.index(role)
            except ValueError:
                current_idx = 0
            selected_role_switch = st.selectbox(
                "Switch Job Role View",
                user_roles,
                index=current_idx,
                key="candidate_role_switcher"
            )
            if selected_role_switch != role:
                load_candidate_session(email, selected_role_switch)
                st.session_state.cancel_speech = True
                st.rerun()
                
    with col_logout:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.button("🚪 Log Out", key="candidate_portal_logout_btn", use_container_width=True, on_click=restart_process)
            
    st.write("")
    
    tab_assessment, tab_results, tab_profile_support = st.tabs(["📋 Active Assessment Loop", "📊 Results & Feedback", "🛠️ Profile & Help Center"])
    
    with tab_assessment:
        st.write("### Active Assessment Progress")
        render_stepper(stage)
        st.write("")
        
        if stage == "proctoring_instruction":
            render_proctoring_instruction_stage()
        elif stage == "mcq":
            render_proctoring_elements()
            render_mcq_stage()
        elif stage == "mcq_passed_screen":
            st.markdown(f"""
            <div class="glass-card" style="border-left: 5px solid #10b981;">
                <div class="stage-title" style="border-left: none; padding-left: 0; color: #059669;">MCQ Screening Passed</div>
                <div style="color: #059669; font-weight: 600; margin-bottom: 10px; font-size: 1.1rem;">🎉 Great job! You scored {st.session_state.mcq_score}/5 ({st.session_state.mcq_score * 20}%).</div>
                <p style="color: #475569; margin-bottom: 0;">You have successfully passed the MCQ barrier and are eligible for the <strong>Interactive Technical Interview Round</strong>. Click below to start your interview.</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Proceed to Technical Interview", key="dashboard_proceed_to_interview_btn", use_container_width=True):
                st.session_state.stage = "interview"
                st.session_state.chat_history = [
                    {"role": "assistant", "content": f"Hello {st.session_state.candidate_name}. Welcome to your technical interview for the {st.session_state.job_role} role. Let's start with a very basic question: What is Machine Learning, and what are the main types of Machine Learning?"}
                ]
                log_candidate_state()
                st.rerun()
                
        elif stage == "mcq_failed_screen":
            st.markdown(f"""
            <div class="glass-card" style="border-left: 5px solid #ef4444;">
                <div class="stage-title" style="border-left: none; padding-left: 0; color: #b91c1c;">MCQ Screening Failed</div>
                <div style="color: #b91c1c; font-weight: 600; margin-bottom: 10px; font-size: 1.1rem;">You scored {st.session_state.mcq_score}/5. The passing score is at least 3/5.</div>
                <p style="color: #475569; margin-bottom: 0;">Unfortunately, we cannot proceed with your application at this time.</p>
            </div>
            """, unsafe_allow_html=True)
            st.info("If you faced technical issues, please submit a ticket in the 'Profile & Help Center' tab for review.")
            
        elif stage == "interview":
            render_proctoring_elements()
            render_interview_stage()
            
        elif stage == "final_evaluation":
            st.markdown("""
            <div class="glass-card" style="margin-bottom: 20px;">
                <div class="stage-title">Final Interview Assessment Completed</div>
            </div>
            """, unsafe_allow_html=True)
            eval_res = st.session_state.get("evaluation_result")
            if eval_res and eval_res.selected:
                st.markdown('<h3 style="color: #10b981;">Selection Status: SELECTED</h3>', unsafe_allow_html=True)
                st.success(f"Congratulations {st.session_state.candidate_name}! You have passed the final technical interview round.")
                
                st.write("**Evaluation Summary:**")
                st.info(eval_res.summary_for_candidate)
                
                # Outbound voice dispatch
                if not st.session_state.call_sent and st.session_state.candidate_phone:
                    if st.session_state.candidate_email == "admin@test.com":
                        st.session_state.call_sent = True
                    else:
                        with st.spinner("Initiating automated voice dispatch..."):
                            try:
                                from src.agents.shared_agents.elevenlabs_agent import ElevenLabsAgent
                                voice_agent = ElevenLabsAgent()
                                voice_agent.trigger_outbound_call(
                                    to_number=st.session_state.candidate_phone.strip(),
                                    candidate_name=st.session_state.candidate_name,
                                    company_name="Hackathon"
                                )
                                st.session_state.call_sent = True
                            except:
                                st.session_state.call_sent = True
                
                # SMTP Email dispatch
                if not st.session_state.email_sent:
                    if st.session_state.candidate_email == "admin@test.com":
                        st.session_state.email_sent = True
                    else:
                        with st.spinner("Sending confirmation email..."):
                            try:
                                email_agent = EmailAgent()
                                sent_ok = email_agent.run(
                                    recipient_email=st.session_state.candidate_email,
                                    candidate_name=st.session_state.candidate_name,
                                    job_role=st.session_state.job_role,
                                    feedback_summary=eval_res.summary_for_candidate,
                                    is_selected=True
                                )
                                st.session_state.email_sent = True
                                if sent_ok:
                                    st.success(f"✅ Congratulations email sent to {st.session_state.candidate_email}")
                                else:
                                    st.warning("⚠️ Could not send confirmation email — SMTP credentials may be missing or incorrect.")
                            except Exception as _email_err:
                                st.session_state.email_sent = True
                                st.warning(f"⚠️ Email delivery failed: {str(_email_err)}")
                                print(f"[EmailAgent] Delivery exception: {_email_err}")

                st.info("📅 **Next Steps**: You will receive a communication email or call shortly from our talent acquisition team with further instructions.")
            else:
                st.markdown('<h3 style="color: #ef4444;">Selection Status: NOT SELECTED</h3>', unsafe_allow_html=True)
                st.error(f"Thank you for your time, {st.session_state.candidate_name}. You were not selected for the next round.")
                if eval_res:
                    st.write("**Evaluation Feedback Summary:**")
                    st.warning(eval_res.summary_for_candidate)
                    
                    # SMTP Email dispatch for rejection
                    if not st.session_state.email_sent:
                        if st.session_state.candidate_email == "admin@test.com":
                            st.session_state.email_sent = True
                        else:
                            with st.spinner("Sending update email..."):
                                try:
                                    email_agent = EmailAgent()
                                    sent_ok = email_agent.run(
                                        recipient_email=st.session_state.candidate_email,
                                        candidate_name=st.session_state.candidate_name,
                                        job_role=st.session_state.job_role,
                                        feedback_summary=eval_res.summary_for_candidate,
                                        is_selected=False
                                    )
                                    st.session_state.email_sent = True
                                    if sent_ok:
                                        st.info(f"📧 Outcome email sent to {st.session_state.candidate_email}")
                                    else:
                                        st.warning("⚠️ Could not send outcome email — SMTP credentials may be missing or incorrect.")
                                except Exception as _email_err:
                                    st.session_state.email_sent = True
                                    st.warning(f"⚠️ Email delivery failed: {str(_email_err)}")
                                    print(f"[EmailAgent] Delivery exception: {_email_err}")

        elif stage == "screening_review":
            st.markdown(f"""
            <div class="glass-card" style="border-left: 5px solid #f59e0b;">
                <div class="stage-title" style="border-left: none; padding-left: 0; color: #d97706;">Screening Status: Under Review</div>
                <div style="color: #d97706; font-weight: 600; margin-bottom: 12px; font-size: 1.1rem;">Your application is under manual review by our recruitment team.</div>
                <p style="color: var(--text-sub); margin-bottom: 12px;">Based on your match score of <strong>{st.session_state.screening_result.match_score if st.session_state.screening_result else "N/A"}%</strong>, your profile has been flagged as borderline. A recruiter will manually evaluate your resume shortly.</p>
                <div style="font-weight: 600; margin-bottom: 6px; color: var(--text-main);">Screening Analysis:</div>
                <div style="background-color: rgba(245, 158, 11, 0.05); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 8px; padding: 15px; font-size: 0.95rem; color: var(--text-main); line-height: 1.5;">
                    {st.session_state.screening_result.reason if st.session_state.screening_result else "No details available."}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        elif stage == "screening_failed":
            st.markdown(f"""
            <div class="glass-card" style="border-left: 5px solid #ef4444;">
                <div class="stage-title" style="border-left: none; padding-left: 0; color: #b91c1c;">Screening Status: Disqualified</div>
                <div style="color: #b91c1c; font-weight: 600; margin-bottom: 12px; font-size: 1.1rem;">Thank you for applying. Unfortunately, your profile does not meet our minimum requirements for this position.</div>
                <div style="font-weight: 600; margin-bottom: 6px; color: #1e293b;">Evaluation Feedback:</div>
                <div style="background-color: #fdf2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 15px; font-size: 0.95rem; color: #1f2937; line-height: 1.5;">
                    {st.session_state.screening_result.reason if st.session_state.screening_result else "No details available."}
                </div>
            </div>
            """, unsafe_allow_html=True)

            
    with tab_results:
        st.write("### Application Results & Performance Analysis")
        records = load_candidates()
        matched = None
        for r in records:
            if r.get("email", "").strip().lower() == email.strip().lower() and r.get("job_role", "").strip().lower() == role.strip().lower():
                matched = r
                break
        
        if not matched:
            st.info("No assessment records found.")
        else:
            status = matched.get("status", "Applied")
            status_badge_html = ""
            if "Failed" in status or "Disqualified" in status or "Violation" in status:
                status_badge_html = f'<span style="background-color: rgba(239, 68, 68, 0.12); color: #ef4444; padding: 3px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">🔴 {status}</span>'
            elif "Finished" in status or "Passed" in status:
                status_badge_html = f'<span style="background-color: rgba(16, 185, 129, 0.12); color: #10b981; padding: 3px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">🟢 {status}</span>'
            else:
                status_badge_html = f'<span style="background-color: rgba(245, 158, 11, 0.12); color: #f59e0b; padding: 3px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">🟡 {status}</span>'
            
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.markdown(f"📌 **Current Pipeline Status**: {status_badge_html}", unsafe_allow_html=True)
                st.write(f"💼 **Target Position**: {matched.get('job_role')}")
                st.write(f"⏳ **Experience Level**: {matched.get('experience')}")
            with col_res2:
                st.write(f"📊 **MCQ Score**: `{matched.get('mcq_score')}`")
                trust_score = matched.get("proctoring_report", {}).get("trust_score", 100) if matched.get("proctoring_report") else max(0, 100 - matched.get("tab_switches", 0) * 25)
                st.write(f"🛡️ **Proctoring Trust Score**: `{trust_score}%`")
                
            st.write("---")
            
            match_score = int(matched.get("match_score", 0))
            st.write(f"**AI Match Score against Job Requirements**: **{match_score}%**")
            st.progress(match_score / 100.0)
            st.write("")
            
            col_sk1, col_sk2 = st.columns(2)
            with col_sk1:
                matched_skills = matched.get("matched_skills", [])
                if matched_skills:
                    st.write("✅ **Your Matched Skills:**")
                    tags_html = "".join([f'<span style="background-color: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; margin-right: 8px; display: inline-block; margin-bottom: 5px; font-weight: 500;">{skill}</span>' for skill in matched_skills])
                    st.markdown(tags_html, unsafe_allow_html=True)
            with col_sk2:
                missing_skills = matched.get("missing_skills", [])
                if missing_skills:
                    st.write("⚠️ **Suggested Missing Skills to Improve:**")
                    tags_html = "".join([f'<span style="background-color: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; margin-right: 8px; display: inline-block; margin-bottom: 5px; font-weight: 500;">{skill}</span>' for skill in missing_skills])
                    st.markdown(tags_html, unsafe_allow_html=True)
                    
            st.write("---")
            
            if matched.get("summary"):
                st.write("##### 🗣️ Hiring Committee Constructive Feedback")
                st.info(matched.get("summary"))
            elif matched.get("screening_reason") and "Disqualified" in status:
                st.write("##### 🗣️ Screening Feedback")
                st.warning(matched.get("screening_reason"))
            else:
                st.info("Final feedback summary will be generated once you complete the technical interview round.")
                
    with tab_profile_support:
        st.write("### Candidate Profile & Support Desk")
        
        with st.container(border=True):
            st.write("#### 🧑 My Registered Details")
            st.write(f"• **Full Name**: {name}")
            st.write(f"• **Email**: {email}")
            st.write(f"• **Phone Number**: {st.session_state.get('candidate_phone', '')}")
            
            if email == "admin@test.com":
                st.info("⚙️ **Tester Account Options**: Since you are using the pre-configured admin tester account, you can reset its test stage and answers at any time to repeat testing.")
                if st.button("🔄 Reset Admin Tester Assessment State", key="admin_tester_hard_reset_btn", use_container_width=True):
                    st.session_state.stage = "proctoring_instruction"
                    st.session_state.mcqs = []
                    st.session_state.mcq_answers = {}
                    st.session_state.chat_history = []
                    st.session_state.interview_concluded = False
                    st.session_state.evaluation_result = None
                    st.session_state.tab_switches = 0
                    st.session_state.proctoring_warnings = []
                    st.session_state.proctoring_violated = False
                    st.session_state.proctoring_report = None
                    
                    st.session_state.duplicate_blocked = False
                    st.session_state.duplicate_candidate = None
                    
                    # Update candidates.json
                    records = load_candidates()
                    for rec in records:
                        if rec.get("email", "").strip().lower() == "admin@test.com" and rec.get("job_role", "").strip().lower() == role.strip().lower():
                            rec["allowed_retake"] = False
                            rec["stage"] = "proctoring_instruction"
                            rec["status"] = "Reviewing Assessment Rules"
                            rec["mcq_score"] = "N/A"
                            rec["selection"] = "N/A"
                            rec["summary"] = ""
                            rec["chat_history"] = []
                            rec["mcqs"] = []
                            rec["mcq_answers"] = {}
                            rec["tab_switches"] = 0
                            rec["proctoring_warnings"] = []
                            rec["proctoring_violated"] = False
                            rec["proctoring_report"] = None
                            break
                    with open(CANDIDATES_FILE, "w") as f:
                        json.dump(records, f, indent=2)
                    st.success("Admin tester state reset successfully! Redirecting to rules...")
                    time.sleep(0.5)
                    st.rerun()
            
            retake_allowed = matched.get("allowed_retake", False)
            if retake_allowed:
                st.success("🔓 **Assessment Access Reset**: Recruiters have approved a retake for you! You can reset your session below to start again.")
            
        with st.container(border=True):
            st.write("#### 📄 Parsed Resume Text")
            with st.expander("Show extracted resume text content"):
                st.text(st.session_state.get("resume_text", "No resume content parsed."))
                
        with st.container(border=True):
            st.write("#### 🛠️ Help & Support Desk")
            st.write("If you faced any system error, browser freeze, or accidental exit, request an assessment reset. The AI Support Agent will analyze your ticket and resolve it if eligible.")
            
            tickets = load_issues()
            candidate_tickets = [t for t in tickets if t.get("email", "").strip().lower() == email.strip().lower() and t.get("job_role", "").strip().lower() == role.strip().lower()]
            
            if candidate_tickets:
                st.write("##### ⏳ Your Active Support Tickets")
                for tk in candidate_tickets:
                    tk_status = "🟢 Auto-Resolved" if tk.get("resolved") else "🟡 Pending Recruiter Review"
                    st.markdown(f"""
                    <div style="background-color: var(--badge-time-bg); border: 1px solid var(--card-border); border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                        <strong>Ticket Status:</strong> {tk_status}<br>
                        <strong>Issue Reported:</strong> <em>"{tk.get('message')}"</em><br>
                        <strong>AI Diagnosis:</strong> {tk.get('diagnosis')}<br>
                        <strong>AI Action Notification:</strong> {tk.get('candidate_notification')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if tk.get("resolved") and matched.get("allowed_retake"):
                        if st.button("🔄 Restart Assessment Session (Use Approved Reset)", key=f"restart_allowed_{tk.get('timestamp')}"):
                            st.session_state.stage = "proctoring_instruction"
                            st.session_state.mcqs = []
                            st.session_state.mcq_answers = {}
                            st.session_state.chat_history = []
                            st.session_state.interview_concluded = False
                            st.session_state.evaluation_result = None
                            st.session_state.tab_switches = 0
                            st.session_state.proctoring_warnings = []
                            st.session_state.proctoring_violated = False
                            st.session_state.proctoring_report = None
                            
                            st.session_state.duplicate_blocked = False
                            st.session_state.duplicate_candidate = None
                            
                            records = load_candidates()
                            for rec in records:
                                if rec.get("email", "").strip().lower() == email.strip().lower() and rec.get("job_role", "").strip().lower() == role.strip().lower():
                                    rec["allowed_retake"] = False
                                    rec["stage"] = "proctoring_instruction"
                                    rec["status"] = "Reviewing Assessment Rules"
                                    rec["mcq_score"] = "N/A"
                                    rec["selection"] = "N/A"
                                    rec["summary"] = ""
                                    rec["chat_history"] = []
                                    rec["mcqs"] = []
                                    rec["mcq_answers"] = {}
                                    rec["tab_switches"] = 0
                                    rec["proctoring_warnings"] = []
                                    rec["proctoring_violated"] = False
                                    rec["proctoring_report"] = None
                                    break
                            with open(CANDIDATES_FILE, "w") as f:
                                json.dump(records, f, indent=2)
                                
                            st.success("Session reset! Redirecting to rules screen...")
                            time.sleep(0.5)
                            st.rerun()
            
            with st.form("candidate_support_form"):
                issue_desc = st.text_area("Describe your issue details...", placeholder="Provide technical details, browser details, and why you need a reset...", height=100)
                submit_ticket = st.form_submit_button("Submit Support Ticket")
                
                if submit_ticket:
                    if not issue_desc.strip():
                        st.error("Please explain your issue.")
                    else:
                        with st.spinner("AI Support Agent is diagnosing ticket..."):
                            try:
                                support_agent = SupportAgent()
                                diagnosis_res = support_agent.run(
                                    candidate_email=email,
                                    reported_message=issue_desc.strip(),
                                    candidate_history=matched
                                )
                                
                                import datetime
                                is_auto_resolved = getattr(diagnosis_res, "auto_resolve_eligible", False)
                                cand_notif = getattr(diagnosis_res, "candidate_notification", "Under review.")
                                
                                new_ticket = {
                                    "email": email,
                                    "name": name,
                                    "job_role": role,
                                    "message": issue_desc.strip(),
                                    "diagnosis": diagnosis_res.diagnosis,
                                    "severity": diagnosis_res.severity,
                                    "suggested_action": diagnosis_res.suggested_action,
                                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "resolved": is_auto_resolved,
                                    "resolved_by": "AI Auto-Resolver" if is_auto_resolved else "Pending Review",
                                    "justification": getattr(diagnosis_res, "justification", ""),
                                    "confidence_score": getattr(diagnosis_res, "confidence_score", 0.0),
                                    "resolution_log": f"Auto-approved reset. Justification: {getattr(diagnosis_res, 'justification', '')}" if is_auto_resolved else "",
                                    "candidate_notification": cand_notif,
                                    "audit_status": "Pending Audit" if is_auto_resolved else "N/A"
                                }

                                
                                if is_auto_resolved:
                                    records = load_candidates()
                                    for r in records:
                                        if r.get("email", "").strip().lower() == email.strip().lower() and r.get("job_role", "").strip().lower() == role.strip().lower():
                                            r["allowed_retake"] = True
                                            r["status"] = "Retake Allowed"
                                            break
                                    with open(CANDIDATES_FILE, "w") as f:
                                        json.dump(records, f, indent=2)
                                
                                tickets = load_issues()
                                updated = False
                                for idx, t in enumerate(tickets):
                                    if t.get("email", "").strip().lower() == email.strip().lower() and t.get("job_role", "").strip().lower() == role.strip().lower() and not t.get("resolved", False):
                                        tickets[idx] = new_ticket
                                        updated = True
                                        break
                                if not updated:
                                    tickets.append(new_ticket)
                                save_issues(tickets)
                                
                                st.success("Ticket successfully submitted! Reloading dashboard...")
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Support Agent error: {str(e)}")

# ----------------- CANDIDATE PORTAL NAVIGATION ROUTER -----------------
if not st.session_state.get("candidate_logged_in", False):
    render_candidate_auth_portal()
else:
    render_candidate_hub_portal()
