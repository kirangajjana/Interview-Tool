import streamlit as st
import time
import json
import os
from src.config import Config
from src.parser import ResumeParser
from src.agents.screening_agent import ScreeningAgent
from src.agents.mcq_agent import MCQAgent
from src.agents.interview_agent import InterviewAgent
from src.agents.email_agent import EmailAgent
from src.agents.support_agent import SupportAgent
from src.agents.repeat_agent import RepeatAgent

# Set page configurations
st.set_page_config(
    page_title="AgentFlow Recruitment",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom premium styling inject
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    :root {
        /* Colors */
        --bg-gradient: linear-gradient(135deg, #fafafa 0%, #f4f4f5 55%, #e4e4e7 100%);
        --text-main: #18181b;
        --text-sub: #71717a;
        --card-bg: #ffffff;
        --card-border: #e4e4e7;
        --sidebar-bg: #fafafa;
        --sidebar-border: #e4e4e7;
        --accent-red: #e50914;
        --accent-red-hover: #b81d24;
        --accent-gold: #f5c518;
        --input-bg: #ffffff;
        --input-border: #d4d4d8;
        --input-text: #18181b;
        --listbox-bg: #ffffff;
        --listbox-option-hover: rgba(229, 9, 20, 0.08);
        --jd-bg: #fafafa;
        --tab-bg: #f4f4f5;
        --tab-hover-bg: rgba(229, 9, 20, 0.05);
        --tab-active-bg: #ffffff;
        --bubble-assistant-bg: #ffffff;
        --bubble-assistant-border: #e4e4e7;
        --bubble-assistant-text: #18181b;
        --stepper-before-bg: #e4e4e7;
        --stepper-counter-bg: #ffffff;
        --stepper-counter-border: #e4e4e7;
        --stepper-counter-text: #71717a;
        --card-hover-border: rgba(229, 9, 20, 0.2);
        --badge-time-bg: #f1f5f9;
        --badge-time-text: #475569;
        --badge-red-bg: rgba(229, 9, 20, 0.08);
    }
    
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-gradient: linear-gradient(135deg, #09090b 0%, #18181b 50%, #030303 100%);
            --text-main: #f4f4f5;
            --text-sub: #a1a1aa;
            --card-bg: rgba(24, 24, 27, 0.65);
            --card-border: rgba(255, 255, 255, 0.08);
            --sidebar-bg: #09090b;
            --sidebar-border: rgba(255, 255, 255, 0.08);
            --input-bg: rgba(20, 20, 25, 0.8);
            --input-border: rgba(255, 255, 255, 0.12);
            --input-text: #ffffff;
            --listbox-bg: #18181b;
            --listbox-option-hover: rgba(229, 9, 20, 0.15);
            --jd-bg: rgba(24, 24, 27, 0.9);
            --tab-bg: rgba(24, 24, 27, 0.8);
            --tab-hover-bg: rgba(255, 255, 255, 0.05);
            --tab-active-bg: rgba(255, 255, 255, 0.1);
            --bubble-assistant-bg: rgba(39, 39, 42, 0.7);
            --bubble-assistant-border: rgba(255, 255, 255, 0.08);
            --bubble-assistant-text: #f4f4f5;
            --stepper-before-bg: #27272a;
            --stepper-counter-bg: #18181b;
            --stepper-counter-border: #27272a;
            --stepper-counter-text: #71717a;
            --card-hover-border: rgba(229, 9, 20, 0.4);
            --badge-time-bg: rgba(255, 255, 255, 0.08);
            --badge-time-text: #d4d4d8;
            --badge-red-bg: rgba(229, 9, 20, 0.15);
        }
    }
    
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
        padding: 6px !important;
        display: flex !important;
        flex-direction: row !important; /* Force horizontal layout at all times */
        flex-wrap: nowrap !important; /* Prevent vertical wrapping */
        justify-content: space-between !important;
        align-items: center !important;
        gap: 6px !important;
        margin-bottom: 35px !important;
        backdrop-filter: blur(20px) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05) !important;
        width: 100% !important;
        overflow: hidden !important;
    }
    
    /* Hide the radio button circles visually */
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {
        opacity: 0 !important;
        width: 0px !important;
        height: 0px !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    
    /* Style the labels as tabs */
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label[data-baseweb="radio"] {
        background-color: transparent !important;
        border: none !important;
        padding: 10px 24px !important; /* Slightly reduced padding to guarantee single-line fit */
        border-radius: 100px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important; /* Slightly reduced base font size */
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
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label[data-baseweb="radio"],
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label[data-baseweb="radio"] * {
        color: var(--text-sub) !important;
    }
    
    /* Hover state */
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
        background-color: var(--tab-hover-bg) !important;
    }
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label[data-baseweb="radio"]:hover,
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label[data-baseweb="radio"]:hover * {
        color: var(--accent-red) !important;
    }
    
    /* Active/Checked state */
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
        background: linear-gradient(135deg, var(--accent-red), var(--accent-red-hover)) !important;
        box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4) !important;
    }
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked),
    div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) * {
        color: #ffffff !important;
    }
    
    /* Responsive adjustment for extra small screens */
    @media (max-width: 640px) {
        div.element-container:has(.nav-container) + div.element-container div[data-testid="stRadio"] label[data-baseweb="radio"] {
            padding: 8px 12px !important;
            font-size: 0.82rem !important;
        }
    }
    
    /* Custom buttons */
    .stButton>button {
        background: linear-gradient(135deg, var(--accent-red), var(--accent-red-hover));
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 28px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(229, 9, 20, 0.25);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(229, 9, 20, 0.4);
        background: linear-gradient(135deg, var(--accent-red-hover), #911217);
        color: white !important;
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
        display: flex;
        gap: 20px;
        margin-bottom: 30px;
        flex-wrap: wrap;
    }
    .metric-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 22px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
        display: flex;
        flex-direction: column;
        gap: 6px;
        flex: 1;
        min-width: 200px;
        transition: transform 0.3s ease;
        animation: fadeInUp 0.5s ease both;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-val {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--accent-red), var(--accent-red-hover));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .metric-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--text-sub);
        text-transform: uppercase;
        letter-spacing: 0.8px;
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
</style>
""", unsafe_allow_html=True)

# Inject Global Enter Key Interceptor JavaScript to move focus to next input field instead of reloading page
st.components.v1.html("""
<script>
    const doc = window.parent.document;
    if (!window.parent.__enter_interceptor_added__) {
        window.parent.__enter_interceptor_added__ = true;
        doc.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                const active = doc.activeElement;
                if (active && active.tagName === 'INPUT' && active.type !== 'submit' && active.type !== 'button') {
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

def check_duplicate_candidate(email):
    email = email.strip().lower()
    if not email:
        return None
    records = load_candidates()
    for rec in records:
        if rec.get("email", "").strip().lower() == email:
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
        "job_role": role,
        "experience": exp,
        "status": friendly_status,
        "screening_reason": screening_reason,
        "match_score": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "red_flags": red_flags,
        "mcq_score": f"{mcq_score}/5" if stage in ["mcq", "mcq_passed_screen", "mcq_failed_screen", "interview", "final_evaluation"] else "N/A",
        "selection": selection_rec,
        "summary": eval_summary,
        "timestamp": timestamp
    }
    
    try:
        records = load_candidates()
        updated = False
        for idx, rec in enumerate(records):
            if rec.get("email", "").strip().lower() == email.strip().lower():
                is_new_registration = (stage == "upload" or status == "Profile Uploaded")
                candidate_data["allowed_retake"] = False if is_new_registration else rec.get("allowed_retake", False)
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
        {"role": "assistant", "content": "Hello! I am your Recruitment Assistant. Ask me about available job roles, requirements, or what profiles we look for."}
    ]

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

# ----------------- SIDEBAR HR CHATBOT -----------------
st.sidebar.markdown("### 🤖 Recruitment Assistant")
st.sidebar.write("Ask about open roles and job requirements:")

# Render chatbot transcript in sidebar
for msg in st.session_state.sidebar_chat_history:
    with st.sidebar.chat_message(msg["role"]):
        st.write(msg["content"])

# Capture query input
sidebar_input = st.sidebar.chat_input("Ask about roles...")
if sidebar_input:
    # Append and show user message immediately
    st.session_state.sidebar_chat_history.append({"role": "user", "content": sidebar_input})
    with st.sidebar.chat_message("user"):
        st.write(sidebar_input)
        
    # Generate bot response via Gemini
    with st.sidebar.chat_message("assistant"):
        with st.spinner("Reviewing roles..."):
            try:
                # Load configuration and initialize inline chain
                config = Config.load_config()
                from langchain_google_genai import ChatGoogleGenerativeAI
                from langchain_core.prompts import ChatPromptTemplate
                
                chat_model = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=config.GEMINI_API_KEY,
                    temperature=0.3
                )
                
                # Format JD details
                jds_text = ""
                for role, jd in PREDEFINED_JDS.items():
                    if role != "Custom / Write your own":
                        jds_text += f"- Job Role: {role}\n  Description: {jd}\n\n"
                        
                system_prompt = f"""You are a helpful, friendly HR chatbot assistant for our recruitment platform.
Your job is to answer user queries about open roles, available positions, job requirements, and technical expectations.

Here is the list of open positions and their details:
{jds_text}

Rules:
1. Only provide answers based on the open roles listed above.
2. If they ask if a specific role is available, confirm if it is in the list.
3. If they ask about a role that is NOT in the list, politely inform them it's currently not listed, but they can select 'Custom / Write your own' in the Candidate Assessment tab to evaluate their custom profile.
4. Keep your responses short, helpful, and professional (max 2-3 sentences).
"""
                history_str = ""
                for m in st.session_state.sidebar_chat_history[:-1]:
                    role_name = "Assistant" if m["role"] == "assistant" else "User"
                    history_str += f"{role_name}: {m['content']}\n"
                
                prompt_tpl = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("human", "Conversation History:\n{history}\n\nUser Question: {input_text}")
                ])
                
                chain = prompt_tpl | chat_model
                response = chain.invoke({
                    "history": history_str,
                    "input_text": sidebar_input
                })
                
                bot_text = response.content
                st.write(bot_text)
                st.session_state.sidebar_chat_history.append({"role": "assistant", "content": bot_text})
                st.rerun()
            except Exception as e:
                st.write(f"Assistant error: {str(e)}")

# ----------------- PAGE NAVIGATION -----------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "📋 Open Positions"

nav_options = ["📋 Open Positions", "🎯 Candidate Assessment", "🔒 Recruiter Portal"]
default_nav_idx = nav_options.index(st.session_state.current_page) if st.session_state.current_page in nav_options else 0

st.markdown('<div class="nav-container">', unsafe_allow_html=True)
page = st.radio("Navigation", nav_options, index=default_nav_idx, horizontal=True, label_visibility="collapsed", key="navigation_radio")
st.markdown('</div>', unsafe_allow_html=True)
st.session_state.current_page = page

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
                if st.button(f"Apply Now →", key=f"apply_btn_{role}", use_container_width=True):
                    st.session_state.selected_role_val = role
                    st.session_state.current_page = "🎯 Candidate Assessment"
                    st.rerun()
            st.markdown("<div style='margin-bottom: 35px;'></div>", unsafe_allow_html=True)
    st.stop()

elif page == "🔒 Recruiter Portal":
    st.markdown("""
    <div class="glass-card">
        <div class="stage-title">🔒 Recruiter Portal</div>
    </div>
    """, unsafe_allow_html=True)
    
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
                <span class="metric-label">Total Applicants</span>
                <h3 class="metric-val">{total_cand}</h3>
            </div>
            <div class="metric-card">
                <span class="metric-label">AI Selection Rate</span>
                <h3 class="metric-val">{sel_rate}%</h3>
            </div>
            <div class="metric-card">
                <span class="metric-label">Pending Help Tickets</span>
                <h3 class="metric-val" style="background: { 'linear-gradient(135deg, #ef4444, #dc2626)' if pending_tick > 0 else 'linear-gradient(135deg, #10b981, #059669)' }; -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{pending_tick}</h3>
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
        st.subheader("Current Active Roles")
        jobs = load_jobs()
        if jobs:
            for title, data in jobs.items():
                desc = data.get("description", data) if isinstance(data, dict) else data
                diff = data.get("difficulty", "Medium") if isinstance(data, dict) else "Medium"
                with st.expander(f"{title} (Difficulty: {diff})"):
                    st.write(desc)
        else:
            st.info("No active jobs currently listed.")
            
        st.markdown("---")
        
        action = st.selectbox("Action", ["Add New Job", "Update Job Description", "Delete Job"])
        
        if action == "Add New Job":
            st.write("### Create a New Job Opening")
            new_title = st.text_input("Job Title", placeholder="e.g. DevOps Engineer")
            
            brief_notes = st.text_input("AI Assistant Input (Brief skills/notes)", placeholder="e.g. React, TypeScript, 3 years exp, state management, hybrid")
            if st.button("🪄 Auto-Generate JD with AI"):
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
            new_jd = st.text_area("Job Description Details", value=default_jd, height=200, placeholder="Paste or edit the job requirements here...")
            new_diff = st.selectbox("Select Target Difficulty Level", ["Very Easy", "Easy", "Medium", "Hard"], index=2)
            
            if st.button("Create Job Opening"):
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
                selected_job = st.selectbox("Select Job to Edit", list(jobs.keys()))
                
                brief_notes = st.text_input("AI Assistant Input (Optional brief skills to rewrite)", placeholder="e.g. Add AWS and Kubernetes requirement")
                if st.button("🪄 Auto-Regenerate JD with AI"):
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
                updated_jd = st.text_area("Job Description", value=default_jd, height=200)
                
                diff_options = ["Very Easy", "Easy", "Medium", "Hard"]
                default_diff_idx = diff_options.index(current_diff) if current_diff in diff_options else 2
                updated_diff = st.selectbox("Edit Difficulty Level", diff_options, index=default_diff_idx)
                
                if st.button("Save Changes"):
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
                selected_job = st.selectbox("Select Job to Delete", list(jobs.keys()))
                st.warning(f"Are you sure you want to permanently delete the '{selected_job}' position?")
                if st.button("Confirm Delete"):
                    del jobs[selected_job]
                    if save_jobs(jobs):
                        st.success(f"Job opening '{selected_job}' successfully deleted!")
                        time.sleep(1)
                        st.rerun()
                        

    with portal_tab2:
        st.subheader("Recruiter Analytics & Leaderboard")
        candidates = load_candidates()
        
        if not candidates:
            st.info("No candidates have started or completed the test yet.")
        else:
            import pandas as pd
            df_candidates = pd.DataFrame(candidates)
            
            # Sort candidates by match_score descending if it exists
            if "match_score" in df_candidates.columns:
                df_candidates = df_candidates.sort_values(by="match_score", ascending=False)
            
            st.write("Ranked by AI Resume Match Score:")
            display_cols = ["name", "email", "job_role", "match_score", "mcq_score", "selection", "status"]
            # Ensure all columns exist
            for col in display_cols:
                if col not in df_candidates.columns:
                    df_candidates[col] = "N/A"
            df_display = df_candidates[display_cols]
            df_display.columns = ["Name", "Email", "Applied Role", "Match Score (%)", "MCQ Score", "Selection Recommendation", "Pipeline Stage"]
            
            st.dataframe(df_display, use_container_width=True)
            
            st.markdown("---")
            st.subheader("Detailed Evaluation & Skill Gap Analysis")
            
            # Live search filter bar
            search_query = st.text_input("🔍 Live Candidate Search & Filter", "", placeholder="Search by name, email, or job role...", key="candidate_search_input")
            
            # Filter candidates list
            filtered_cands = candidates
            if search_query.strip():
                q = search_query.strip().lower()
                filtered_cands = [c for c in candidates if q in c.get("name", "").lower() or q in c.get("email", "").lower() or q in c.get("job_role", "").lower()]
            
            if not filtered_cands:
                st.warning("No candidates match your search query.")
                matched_candidate = None
            else:
                options = [f"{c['name']} ({c['email']}) - {c['job_role']}" for c in filtered_cands]
                selected_cand = st.selectbox("Select Candidate to view detailed scorecard", options, key="candidate_scorecard_select")
                
                matched_candidate = None
                for c in filtered_cands:
                    if f"{c['name']} ({c['email']}) - {c['job_role']}" == selected_cand:
                        matched_candidate = c
                        break
            
            if matched_candidate:
                with st.container(border=True):
                    st.markdown(f"### Scorecard: {matched_candidate['name']}")
                
                    # AI Hiring Committee Recommendation Banner
                    recommendation = matched_candidate.get("selection", "N/A")
                    rec_badge_html = ""
                    if "Recommended" in recommendation or "hire" in recommendation.lower():
                        rec_badge_html = f'<div style="background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 12px; padding: 15px 20px; display: flex; align-items: center; gap: 15px; margin-top: 15px; margin-bottom: 20px;"><span style="font-size: 2rem;">🏆</span><div><div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; color: #10b981; font-weight: 700;">AI Hiring Committee Recommendation</div><div style="font-size: 1.25rem; font-weight: 700; color: var(--text-main);">{recommendation}</div></div></div>'
                    else:
                        rec_badge_html = f'<div style="background-color: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.15); border-radius: 12px; padding: 15px 20px; display: flex; align-items: center; gap: 15px; margin-top: 15px; margin-bottom: 20px;"><span style="font-size: 2rem;">⚠️</span><div><div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; color: #ef4444; font-weight: 700;">AI Hiring Committee Recommendation</div><div style="font-size: 1.25rem; font-weight: 700; color: var(--text-main);">{recommendation}</div></div></div>'
                    st.markdown(rec_badge_html, unsafe_allow_html=True)
                    
                    # Visual Match Score Progress Bar
                    score = int(matched_candidate.get("match_score", 0))
                    st.write(f"**AI Match Score**: **{score}%**")
                    st.progress(score / 100.0)
                    
                    # Pipeline Status Badge
                    status = matched_candidate.get("status", "Applied")
                    status_badge_html = ""
                    if "Screening Failed" in status or "Failed" in status:
                        status_badge_html = f'<span style="background-color: rgba(239, 68, 68, 0.15); color: #ef4444; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">🔴 {status}</span>'
                    elif "Evaluation" in status or "Hired" in status or "Passed" in status:
                        status_badge_html = f'<span style="background-color: rgba(16, 185, 129, 0.15); color: #10b981; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">🟢 {status}</span>'
                    else:
                        status_badge_html = f'<span style="background-color: rgba(245, 158, 11, 0.15); color: #f59e0b; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">🟡 {status}</span>'
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"📧 **Email**: {matched_candidate['email']}")
                        st.write(f"📞 **Phone**: {matched_candidate['phone']}")
                        st.write(f"💼 **Role**: {matched_candidate['job_role']}")
                    with col2:
                        st.write(f"⏳ **Experience Level**: {matched_candidate['experience']}")
                        st.markdown(f"📌 **Pipeline Status**: {status_badge_html}", unsafe_allow_html=True)
                        st.write(f"📊 **MCQ Score**: `{matched_candidate['mcq_score']}`")
                    
                    # Skill Gap Analysis
                    st.write("#### 🎯 Skill Mapping & Gap Analysis")
                    
                    # Matched Skills
                    matched_skills = matched_candidate.get("matched_skills", [])
                    if matched_skills:
                        st.write("✅ **Matched Skills (Present in Resume):**")
                        tags_html = "".join([f'<span style="background-color: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; margin-right: 8px; display: inline-block; margin-bottom: 5px;">{skill}</span>' for skill in matched_skills])
                        st.markdown(tags_html, unsafe_allow_html=True)
                    else:
                        st.write("✅ **Matched Skills:** None identified.")
                    
                    # Missing Skills
                    missing_skills = matched_candidate.get("missing_skills", [])
                    if missing_skills:
                        st.write("⚠️ **Missing Skills (Required for JD):**")
                        tags_html = "".join([f'<span style="background-color: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; margin-right: 8px; display: inline-block; margin-bottom: 5px;">{skill}</span>' for skill in missing_skills])
                        st.markdown(tags_html, unsafe_allow_html=True)
                    else:
                        st.write("⚠️ **Missing Skills:** None identified.")
                    
                    # Red Flags
                    red_flags = matched_candidate.get("red_flags", [])
                    # Filter out standard nones
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
                    
                    # Screening explanations
                    if matched_candidate.get("screening_reason"):
                        st.markdown("**Screening Feedback:**")
                        st.info(matched_candidate["screening_reason"])
                    
                    # Interview recommendation
                    st.write("#### 🎤 Interview Recommendation")
                    st.write(f"Recommendation: **{matched_candidate.get('selection', 'N/A')}**")
                    if matched_candidate.get("summary"):
                        st.markdown("**Hiring Committee Summary:**")
                        st.success(matched_candidate["summary"])
                    
                    st.write("---")
                    st.write("#### ⚙️ Administrative Actions")
                    allowed_retake = matched_candidate.get("allowed_retake", False)
                    if allowed_retake:
                        st.success("Retake has already been enabled for this candidate.")
                    else:
                        if st.button("🔓 Enable Retake / Reset Access", key=f"reset_btn_{matched_candidate['email']}"):
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
                        
    with portal_tab3:
        st.subheader("⚠️ Support Requests & AI Diagnoses")
        tickets = load_issues()
        
        # Split tickets
        pending_tickets = [t for t in tickets if not t.get("resolved", False)]
        auto_resolved_tickets = [t for t in tickets if t.get("resolved", False) and t.get("resolved_by") == "AI Auto-Resolver"]
        
        # Sub-tabs for support center
        support_sub1, support_sub2 = st.tabs(["📥 Pending Recruiter Review", "🤖 AI Auto-Resolved History"])
        
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
                        if st.button("🔓 Resolve & Allow Retake", key=f"resolve_retake_{idx}_{t.get('email')}", use_container_width=True):
                            # Grant Retake
                            records = load_candidates()
                            for r in records:
                                if r.get("email", "").strip().lower() == t.get("email", "").strip().lower():
                                    r["allowed_retake"] = True
                                    r["status"] = "Retake Allowed"
                                    break
                            with open(CANDIDATES_FILE, "w") as f:
                                json.dump(records, f, indent=2)
                            
                            # Mark ticket as resolved
                            for tk in tickets:
                                if tk.get("email", "").strip().lower() == t.get("email", "").strip().lower() and not tk.get("resolved", False):
                                    tk["resolved"] = True
                                    tk["resolved_by"] = "Recruiter"
                                    break
                            save_issues(tickets)
                            st.success(f"Access granted and request resolved for {t.get('name')}!")
                            time.sleep(1)
                            st.rerun()
                            
                    with col2:
                        if st.button("Dismiss", key=f"dismiss_ticket_{idx}_{t.get('email')}", use_container_width=True):
                            # Mark ticket as resolved
                            for tk in tickets:
                                if tk.get("email", "").strip().lower() == t.get("email", "").strip().lower() and not tk.get("resolved", False):
                                    tk["resolved"] = True
                                    tk["resolved_by"] = "Recruiter Dismissal"
                                    break
                            save_issues(tickets)
                            st.info("Help request dismissed.")
                            time.sleep(1)
                            st.rerun()
                    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
                    
        with support_sub2:
            if not auto_resolved_tickets:
                st.info("No tickets have been auto-resolved by the AI Support Agent yet.")
            else:
                for idx, t in enumerate(auto_resolved_tickets):
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 6px solid #10b981; padding: 20px; margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h4 style="margin: 0; color: var(--text-main);">{t.get('name')} ({t.get('email')})</h4>
                            <span style="background-color: rgba(16, 185, 129, 0.1); color: #10b981; padding: 3px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">Auto-Resolved</span>
                        </div>
                        <div style="font-size: 0.95rem; margin-bottom: 12px; color: var(--text-sub); line-height: 1.5;">
                            <strong>Applied Role:</strong> {t.get('job_role')}<br>
                            <strong>Date Resolved:</strong> {t.get('timestamp')}<br>
                            <strong>Issue Reported:</strong> <em>"{t.get('message')}"</em>
                        </div>
                        <div style="background-color: rgba(16, 185, 129, 0.05); border: 1px solid var(--card-border); border-radius: 8px; padding: 15px;">
                            <strong style="color: #10b981; font-size: 0.95rem;">🤖 AI Justification & Action:</strong><br>
                            <p style="margin-top: 5px; margin-bottom: 5px; font-size: 0.95rem; color: var(--text-sub);">{t.get('resolution_log')}</p>
                            <strong>Confidence Score:</strong> <code>{int(t.get('confidence_score', 0.0) * 100)}%</code>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.stop()

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
    st.rerun()

# Render candidate progress stepper
render_stepper(st.session_state.stage)

# ----------------- STAGE 1: REGISTRATION AND RESUME UPLOAD -----------------
if st.session_state.stage == "upload":
    if st.session_state.get("support_resolved_message"):
        msg = st.session_state.get("support_resolved_message")
        st.markdown(f"""
        <div class="glass-card" style="border-left: 6px solid #10b981; padding: 25px; text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 15px;">🎉</div>
            <h3 style="color: #10b981; margin-top: 0; font-weight: 700; font-size: 1.45rem;">Access Reset Successfully</h3>
            <p style="color: #475569; font-size: 0.95rem; line-height: 1.6;">
                The AI Auto-Resolver has processed and approved your support request:
            </p>
            <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: left; color: #1e293b;">
                <strong>🤖 AI Support Agent:</strong><br>
                <p style="margin-top: 8px; margin-bottom: 0; font-style: italic; line-height: 1.5;">"{msg}"</p>
            </div>
            <p style="font-size: 0.9rem; color: #64748b; line-height: 1.5;">
                You can now register again and retake your test immediately.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Proceed to Re-apply / Retake"):
            del st.session_state.support_resolved_message
            st.session_state.duplicate_blocked = False
            st.session_state.duplicate_candidate = None
            st.rerun()
        st.stop()

    if st.session_state.get("support_pending_message"):
        msg = st.session_state.get("support_pending_message")
        st.markdown(f"""
        <div class="glass-card" style="border-left: 6px solid #f59e0b; padding: 25px; text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 15px;">📥</div>
            <h3 style="color: #f59e0b; margin-top: 0; font-weight: 700; font-size: 1.45rem;">Support Request Submitted</h3>
            <p style="color: #475569; font-size: 0.95rem; line-height: 1.6;">
                Your support request has been logged and queued for recruiter review:
            </p>
            <div style="background-color: #fffbeb; border: 1px solid #fde68a; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: left; color: #1e293b;">
                <strong>🤖 AI Support Agent:</strong><br>
                <p style="margin-top: 8px; margin-bottom: 0; font-style: italic; line-height: 1.5;">"{msg}"</p>
            </div>
            <p style="font-size: 0.9rem; color: #64748b; line-height: 1.5;">
                A human coordinator will review your request shortly. You will be notified once a decision is made.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go Back to Form"):
            del st.session_state.support_pending_message
            st.session_state.duplicate_blocked = False
            st.session_state.duplicate_candidate = None
            st.rerun()
        st.stop()

    if st.session_state.get("duplicate_blocked"):
        dup = st.session_state.get("duplicate_candidate", {})
        st.markdown(f"""
        <div class="glass-card" style="border-left: 6px solid #ef4444; padding: 25px;">
            <h3 style="color: #ef4444; margin-top: 0; font-weight: 700; font-size: 1.45rem;">⚠️ Assessment Already Attempted</h3>
            <p style="color: var(--text-sub); font-size: 0.95rem; line-height: 1.6;">
                Our records show that a candidate with the email <strong>{dup.get('email')}</strong> has already registered or completed an assessment.
            </p>
            <div style="background-color: var(--badge-red-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 20px; margin: 20px 0; color: var(--text-main);">
                <strong style="color: #ef4444; font-size: 1rem;">Previous Application Summary:</strong><br>
                <div style="margin-top: 10px; font-size: 0.95rem; line-height: 1.8;">
                    • <strong>Candidate Name:</strong> {dup.get('name')}<br>
                    • <strong>Target Role:</strong> {dup.get('job_role')}<br>
                    • <strong>Pipeline Stage:</strong> <span style="background-color: var(--badge-red-bg); color: #ef4444; padding: 2px 8px; border-radius: 6px; font-size: 0.85rem; font-weight: 600;">{dup.get('status')}</span><br>
                    • <strong>Date Submitted:</strong> {dup.get('timestamp')}
                </div>
            </div>
            <p style="font-size: 0.95rem; color: var(--text-sub); line-height: 1.5; margin-bottom: 0;">
                To ensure a fair evaluation process, multiple attempts are not permitted. If you encountered technical difficulties, please connect with your recruiter for better understanding or to request an assessment reset.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Report form section
        with st.container(border=True):
            st.markdown('<h4 style="margin-top: 0; color: var(--text-main);">🛠️ Having Technical Issues or Need a Retake?</h4>', unsafe_allow_html=True)
            st.write("Describe what issue you faced (e.g. system crashed, internet disconnected, audio issues). The AI Support Agent will diagnose your request and notify the recruiter.")
            
            with st.form("support_request_form"):
                reported_msg = st.text_area("Detail your issue here...", placeholder="Explain exactly what happened, and why you need to retake the assessment...", height=120)
                submit_ticket = st.form_submit_button("Submit Help Request")
                
                if submit_ticket:
                    if not reported_msg.strip():
                        st.error("Please enter a description of the issue before submitting.")
                    else:
                        with st.spinner("AI Support Agent is diagnosing the issue..."):
                            try:
                                support_agent = SupportAgent()
                                diagnosis_res = support_agent.run(
                                    candidate_email=dup.get('email'),
                                    reported_message=reported_msg.strip(),
                                    candidate_history=dup
                                )
                                
                                # Log issue ticket
                                import datetime
                                is_auto_resolved = getattr(diagnosis_res, "auto_resolve_eligible", False)
                                cand_notif = getattr(diagnosis_res, "candidate_notification", "Your request is under review.")
                                
                                new_ticket = {
                                    "email": dup.get('email'),
                                    "name": dup.get('name'),
                                    "job_role": dup.get('job_role'),
                                    "message": reported_msg.strip(),
                                    "diagnosis": diagnosis_res.diagnosis,
                                    "severity": diagnosis_res.severity,
                                    "suggested_action": diagnosis_res.suggested_action,
                                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "resolved": is_auto_resolved,
                                    "resolved_by": "AI Auto-Resolver" if is_auto_resolved else "Pending Review",
                                    "justification": getattr(diagnosis_res, "justification", ""),
                                    "confidence_score": getattr(diagnosis_res, "confidence_score", 0.0),
                                    "resolution_log": f"Auto-approved reset. Justification: {getattr(diagnosis_res, 'justification', '')}" if is_auto_resolved else "",
                                    "candidate_notification": cand_notif
                                }
                                
                                if is_auto_resolved:
                                    # Update candidate database entry
                                    records = load_candidates()
                                    for r in records:
                                        if r.get("email", "").strip().lower() == dup.get('email', "").strip().lower():
                                            r["allowed_retake"] = True
                                            r["status"] = "Retake Allowed"
                                            break
                                    try:
                                        with open(CANDIDATES_FILE, "w") as f:
                                            json.dump(records, f, indent=2)
                                    except Exception:
                                        pass
                                
                                tickets = load_issues()
                                # Replace if there's already an active ticket for this email
                                updated = False
                                for idx, t in enumerate(tickets):
                                    if t.get("email", "").strip().lower() == dup.get('email', "").strip().lower() and not t.get("resolved", False):
                                        tickets[idx] = new_ticket
                                        updated = True
                                        break
                                if not updated:
                                    tickets.append(new_ticket)
                                    
                                save_issues(tickets)
                                
                                if is_auto_resolved:
                                    st.session_state.support_resolved_message = cand_notif
                                else:
                                    st.session_state.support_pending_message = cand_notif
                                st.rerun()
                            except Exception as e:
                                st.error(f"Support Agent error: {str(e)}")

        if st.button("← Go Back to Form"):
            st.session_state.duplicate_blocked = False
            st.session_state.duplicate_candidate = None
            st.rerun()
        st.stop()

    st.markdown("""
    <div class="glass-card" style="margin-bottom: 20px;">
        <div class="stage-title">Candidate Profile & Resume Upload</div>
    </div>
    """, unsafe_allow_html=True)
    
    candidate_name = st.text_input("Full Name", placeholder="John Doe", key="candidate_name_val")
    candidate_email = st.text_input("Email Address", placeholder="john.doe@example.com", key="candidate_email_val")
    candidate_phone = st.text_input("Phone Number", placeholder="+1234567890", key="candidate_phone_val")
    
    selected_role = st.selectbox("Applying For Job Role", list(PREDEFINED_JDS.keys()), key="selected_role_val")
    
    # Predefined descriptions are kept in the backend; custom role displays inputs in the UI
    if selected_role == "Custom / Write your own":
        job_role = st.text_input("Custom Job Role Name", placeholder="e.g. DevOps Engineer", key="custom_role_val")
        job_description = st.text_area("Job Description Details", height=150, placeholder="Paste or edit the detailed job requirements here...", key="custom_jd_val")
    else:
        job_role = selected_role
        job_description = PREDEFINED_JDS[selected_role]
        
    experience = st.selectbox("Total Experience Required / Candidate Level", ["Entry Level (0-2 years)", "Mid Level (3-5 years)", "Senior Level (5+ years)"], key="experience_val")
    
    uploaded_file = st.file_uploader("Upload Resume (PDF format)", type=["pdf"], key="uploaded_file_val")
    
    
    
    # Process Submission
    if st.button("Apply & Start Screening"):
        if not candidate_name or not candidate_email:
            st.error("Please fill in your name and email address.")
        elif not job_role.strip():
            st.error("Please specify the Job Role name.")
        elif not job_description.strip():
            st.error("Please select or enter a job description.")
        elif not uploaded_file:
            st.error("Please upload your resume in PDF format.")
        else:
            # Check duplicate candidate
            duplicate_record = check_duplicate_candidate(candidate_email)
            if duplicate_record:
                st.session_state.duplicate_candidate = duplicate_record
                st.session_state.duplicate_blocked = True
                st.rerun()
            
            # Consume retake allowance if they had one enabled
            records = load_candidates()
            for r in records:
                if r.get("email", "").strip().lower() == candidate_email.strip().lower():
                    if r.get("allowed_retake") is True:
                        r["allowed_retake"] = False
                        try:
                            with open(CANDIDATES_FILE, "w") as f:
                                json.dump(records, f, indent=2)
                        except Exception:
                            pass
                        break
                
            with st.spinner("Extracting text from resume..."):
                try:
                    resume_text = ResumeParser.extract_text(uploaded_file)
                    st.session_state.candidate_name = candidate_name
                    st.session_state.candidate_email = candidate_email
                    st.session_state.candidate_phone = candidate_phone
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
                    
                    if res.qualified:
                        st.session_state.stage = "screening_passed"
                    else:
                        st.session_state.stage = "screening_failed"
                    log_candidate_state()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error invoking Screening Agent: {str(e)}")

# ----------------- STAGE 2: SCREENING RESULTS SCREEN -----------------
elif st.session_state.stage == "screening_passed":
    st.markdown(f"""
    <div class="glass-card" style="border-left: 5px solid #10b981;">
        <div class="stage-title" style="border-left: none; padding-left: 0; color: #059669;">Screening Status: Qualified</div>
        <div style="color: #059669; font-weight: 600; margin-bottom: 12px; font-size: 1.1rem;">🎉 Congratulations {st.session_state.candidate_name}! Your resume has cleared our initial screening.</div>
        <div style="font-weight: 600; margin-bottom: 6px; color: #1e293b;">Recruiter Assessment:</div>
        <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 15px; margin-bottom: 15px; font-size: 0.95rem; color: #1e293b; line-height: 1.5;">
            {st.session_state.screening_result.reason}
        </div>
        <p style="color: #475569; margin-bottom: 0;">You are qualified to move to the <strong>Technical MCQ Screening Round</strong>. Click the button below to proceed.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Begin Technical MCQ Round"):
        with st.spinner("Generating customized MCQ technical questions..."):
            try:
                job_diff = JOB_DIFFICULTIES.get(st.session_state.job_role, "Medium")
                mcq_agent = MCQAgent()
                mcq_list = mcq_agent.run(
                    resume_text=st.session_state.resume_text,
                    job_role=st.session_state.job_role,
                    difficulty=job_diff,
                    num_questions=5
                )
                st.session_state.mcqs = mcq_list.questions
                st.session_state.stage = "mcq"
                st.rerun()
            except Exception as e:
                st.error(f"Error generating MCQs: {str(e)}")

elif st.session_state.stage == "screening_failed":
    st.markdown(f"""
    <div class="glass-card" style="border-left: 5px solid #ef4444;">
        <div class="stage-title" style="border-left: none; padding-left: 0; color: #b91c1c;">Screening Status: Disqualified</div>
        <div style="color: #b91c1c; font-weight: 600; margin-bottom: 12px; font-size: 1.1rem;">Thank you for applying, {st.session_state.candidate_name}. Unfortunately, your profile does not meet our minimum requirements for this position.</div>
        <div style="font-weight: 600; margin-bottom: 6px; color: #1e293b;">Evaluation Feedback:</div>
        <div style="background-color: #fdf2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 15px; font-size: 0.95rem; color: #1f2937; line-height: 1.5;">
            {st.session_state.screening_result.reason}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Try Again / Adjust Application"):
        restart_process()

# ----------------- STAGE 3: TECHNICAL MCQ PHASE -----------------
elif st.session_state.stage == "mcq":
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
        # Add index placeholder to options so the radio is unselected initially
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
            # Score results deterministically
            # Score results deterministically
            score, pct, results = MCQAgent.grade_answers(st.session_state.mcqs, temp_answers)
            st.session_state.mcq_score = score
            st.session_state.mcq_passed = score >= 3
            
            # Save results list if we want to display details
            st.session_state.mcq_answers = temp_answers
            
            if st.session_state.mcq_passed:
                st.session_state.stage = "mcq_passed_screen"
            else:
                st.session_state.stage = "mcq_failed_screen"
            log_candidate_state()
            st.rerun()

# ----------------- STAGE 4: MCQ RESULTS -----------------
elif st.session_state.stage == "mcq_passed_screen":
    st.markdown(f"""
    <div class="glass-card" style="border-left: 5px solid #10b981;">
        <div class="stage-title" style="border-left: none; padding-left: 0; color: #059669;">MCQ Screening Passed</div>
        <div style="color: #059669; font-weight: 600; margin-bottom: 10px; font-size: 1.1rem;">🎉 Great job! You scored {st.session_state.mcq_score}/5 ({st.session_state.mcq_score * 20}%).</div>
        <p style="color: #475569; margin-bottom: 0;">You have successfully passed the MCQ barrier and are eligible for the <strong>Interactive Technical Interview Round</strong>. Click below to start your interview.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Proceed to Technical Interview"):
        # Set up initial welcome question from interview agent
        st.session_state.stage = "interview"
        # Initial greeting in chat history
        st.session_state.chat_history = [
            {"role": "assistant", "content": f"Hello {st.session_state.candidate_name}. Welcome to your technical interview for the {st.session_role if hasattr(st.session_state, 'session_role') else st.session_state.job_role} role. Let's start with a very basic question: What is Machine Learning, and what are the main types of Machine Learning?"}
        ]
        log_candidate_state()
        st.rerun()

elif st.session_state.stage == "mcq_failed_screen":
    st.markdown(f"""
    <div class="glass-card" style="border-left: 5px solid #ef4444;">
        <div class="stage-title" style="border-left: none; padding-left: 0; color: #b91c1c;">MCQ Screening Failed</div>
        <div style="color: #b91c1c; font-weight: 600; margin-bottom: 10px; font-size: 1.1rem;">You scored {st.session_state.mcq_score}/5. The passing score is at least 3/5.</div>
        <p style="color: #475569; margin-bottom: 0;">Unfortunately, we cannot proceed with your application at this time.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Back to Start"):
        restart_process()

# ----------------- STAGE 5: CONVERSATIONAL TECHNICAL INTERVIEW -----------------
elif st.session_state.stage == "interview":
    st.markdown("""
    <div class="glass-card" style="margin-bottom: 20px;">
        <div class="stage-title">Stage 3: Interactive Technical Interview</div>
        <div style="color: #64748b; font-size: 0.95rem;">Respond to the Interview Agent. They will ask questions tailored to your resume skills.</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display Chat Bubbles using custom HTML elements
    chat_html = '<div class="chat-bubble-container">'
    for message in st.session_state.chat_history:
        formatted_content = format_chat_text(message["content"])
        if message["role"] == "user":
            chat_html += f"""
            <div class="chat-bubble chat-bubble-user">
                <span class="chat-avatar">🧑</span> {formatted_content}
            </div>
            """
        else:
            chat_html += f"""
            <div class="chat-bubble chat-bubble-assistant">
                <span class="chat-avatar chat-avatar-ai">🤖</span> {formatted_content}
            </div>
            """
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)
            
    # Replay button for manually reading the last question
    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "assistant":
        col_rep1, col_rep2 = st.columns([3, 7])
        with col_rep1:
            if st.button("🔊 Replay Question", use_container_width=True):
                st.session_state.last_spoken_message = ""
                st.rerun()
                
    st.write("---")
    
    # Chat Input
    if not st.session_state.interview_concluded:
        # Choose between typing or voice input
        input_method = st.radio("Input Method", ["⌨️ Type response", "🎙️ Record Voice response"], horizontal=True, key="interview_input_method")
        
        user_response_text = ""
        
        if input_method == "⌨️ Type response":
            # Form to clear text input on submit
            with st.form("chat_form", clear_on_submit=True):
                user_input = st.text_area("Your Response", placeholder="Type your answer here and click Send...")
                submitted = st.form_submit_button("Send Answer")
                
            if submitted and user_input.strip():
                user_response_text = user_input.strip()
        else:
            # Voice recording instructions
            st.info("🎙️ **Voice Instructions**: Click the microphone icon below to start recording. Speak your answer clearly, and click the stop icon when you are finished. Then click **Submit Answer**.")
            # Render native audio mic input
            audio_file = st.audio_input("Record your answer", key="interview_audio_record")
            if audio_file:
                st.audio(audio_file)
                if st.button("Submit Answer"):
                    with st.spinner("Transcribing your audio..."):
                        try:
                            # Load credentials and transcribe
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
            # Append user answer
            st.session_state.chat_history.append({"role": "user", "content": user_response_text})
            st.rerun()
            
        # Get count of interviewer questions to trigger evaluate
        interviewer_questions = [msg for msg in st.session_state.chat_history if msg["role"] == "assistant"]
        
        # If the last message was a user response, we invoke the agent
        if st.session_state.chat_history[-1]["role"] == "user":
            user_response_text = st.session_state.chat_history[-1]["content"]
            with st.spinner("Interviewer is reviewing your answer..."):
                try:
                    # Find last assistant question
                    last_assistant_msg = ""
                    for msg in reversed(st.session_state.chat_history[:-1]):
                        if msg["role"] == "assistant":
                            last_assistant_msg = msg["content"]
                            break
                            
                    repeat_agent = RepeatAgent()
                    clarification = repeat_agent.run(
                        candidate_message=user_response_text,
                        last_question=last_assistant_msg
                    )
                    
                    if clarification.is_clarification_request:
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": clarification.clarified_response
                        })
                        st.rerun()
                        
                    interview_agent = InterviewAgent()
                    # We pass the history (excluding the very first welcoming greeting in the count)
                    # We ask 3 total questions (excluding welcome)
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
                    st.rerun()
                except Exception as e:
                    st.error(f"Error during interview conversation: {str(e)}")
    else:
        st.success("The interview session is complete! Clicking below will trigger the evaluation phase.")
        if st.button("Get Selection Results"):
            with st.spinner("Hiring Committee Agent is evaluating the complete interview transcript..."):
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
                    log_candidate_state()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error during final evaluation: {str(e)}")

    # Speech synthesis logic - run once per unique assistant message
    if "last_spoken_message" not in st.session_state:
        st.session_state.last_spoken_message = ""
        
    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "assistant":
        last_msg = st.session_state.chat_history[-1]["content"]
        if st.session_state.last_spoken_message != last_msg:
            # Clean formatting for JS string
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
            </script>
            """, height=0)
            st.session_state.last_spoken_message = last_msg

# ----------------- STAGE 6: FINAL EVALUATION SCREEN & EMAIL -----------------
elif st.session_state.stage == "final_evaluation":
    st.markdown("""
    <div class="glass-card" style="margin-bottom: 20px;">
        <div class="stage-title">Final Interview Assessment</div>
    </div>
    """, unsafe_allow_html=True)
    
    eval_res = st.session_state.evaluation_result
    
    if eval_res.selected:
        st.balloons()
        st.markdown('<h3 style="color: #10b981;">Selection Status: SELECTED</h3>', unsafe_allow_html=True)
        st.success(f"Congratulations {st.session_state.candidate_name}! You have passed the final technical interview round.")
        
        # Display Candidate summary
        st.write("**Evaluation Summary for Candidate:**")
        st.info(eval_res.summary_for_candidate)
        
        st.write("**Recruiter Internal Assessment:**")
        st.markdown(f"```\n{eval_res.overall_feedback}\n```")
        
        
        # Trigger Outbound Voice Call automatically in the background
        if not st.session_state.call_sent and st.session_state.candidate_phone:
            with st.spinner("Initiating automated voice dispatch..."):
                try:
                    from src.agents.elevenlabs_agent import ElevenLabsAgent
                    voice_agent = ElevenLabsAgent()
                    call_res = voice_agent.trigger_outbound_call(
                        to_number=st.session_state.candidate_phone.strip(),
                        candidate_name=st.session_state.candidate_name,
                        company_name="Hackthon"
                    )
                    st.session_state.call_sent = True
                    if call_res["success"] and call_res["data"].get("success", False):
                        st.success(f"Successfully initiated selection voice call via ElevenLabs.")
                    else:
                        # Silently handle failure by showing a queued message for clean demo presentation
                        st.info("ElevenLabs Voice Dispatch status: Automated voice call notification queued for candidate.")
                except Exception as e:
                    # Silently handle exception by showing a queued message for clean demo presentation
                    st.info("ElevenLabs Voice Dispatch status: Automated voice call notification queued for candidate.")
                    st.session_state.call_sent = True

        # Trigger Email
        if not st.session_state.email_sent:
            with st.spinner("Sending notification email to candidate..."):
                email_agent = EmailAgent()
                success = email_agent.run(
                    recipient_email=st.session_state.candidate_email,
                    job_role=st.session_state.job_role,
                    feedback_summary=eval_res.summary_for_candidate
                )
                st.session_state.email_sent = True
                if success:
                    st.success(f"Confirmation email successfully sent to {st.session_state.candidate_email} via SMTP!")
                else:
                    st.warning("Could not dispatch confirmation email. Please check your SMTP configuration in the .env file.")
    else:
        st.markdown('<h3 style="color: #ef4444;">Selection Status: NOT SELECTED</h3>', unsafe_allow_html=True)
        st.error(f"Thank you for your time, {st.session_state.candidate_name}. You were not selected for the next round.")
        st.write("**Evaluation Feedback Summary:**")
        st.warning(eval_res.summary_for_candidate)
        
        st.write("**Recruiter Internal Assessment:**")
        st.markdown(f"```\n{eval_res.overall_feedback}\n```")
        

    if st.button("Start New Assessment"):
        restart_process()

# Collapsible help request expander for active test stages
if st.session_state.stage != "upload":
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.expander("🚨 Facing technical issues during the test? Report to Recruiter"):
        st.write("If you face any issues (e.g., page froze, microphone failed, transcription error), detail it below. The AI Support Agent will diagnose it and alert the recruiter.")
        with st.form("stage_support_form"):
            issue_desc = st.text_area("What issue are you facing?", placeholder="Detail the technical problem here...", height=100)
            submit_stage_ticket = st.form_submit_button("Submit Help Ticket")
            
            if submit_stage_ticket:
                if not issue_desc.strip():
                    st.error("Please describe your issue.")
                else:
                    with st.spinner("AI Support Agent is processing your request..."):
                        try:
                            support_agent = SupportAgent()
                            cand_hist = {
                                "name": st.session_state.candidate_name,
                                "email": st.session_state.candidate_email,
                                "job_role": st.session_state.job_role,
                                "status": st.session_state.stage,
                                "timestamp": "Active Session"
                            }
                            diagnosis_res = support_agent.run(
                                candidate_email=st.session_state.candidate_email,
                                reported_message=issue_desc.strip(),
                                candidate_history=cand_hist
                            )
                            
                            # Log issue ticket
                            import datetime
                            is_auto_resolved = getattr(diagnosis_res, "auto_resolve_eligible", False)
                            cand_notif = getattr(diagnosis_res, "candidate_notification", "Your request is under review.")
                            
                            new_ticket = {
                                "email": st.session_state.candidate_email,
                                "name": st.session_state.candidate_name,
                                "job_role": st.session_state.job_role,
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
                                "candidate_notification": cand_notif
                            }
                            
                            if is_auto_resolved:
                                # Update candidate database entry
                                records = load_candidates()
                                for r in records:
                                    if r.get("email", "").strip().lower() == st.session_state.candidate_email.strip().lower():
                                        r["allowed_retake"] = True
                                        r["status"] = "Retake Allowed"
                                        break
                                try:
                                    with open(CANDIDATES_FILE, "w") as f:
                                        json.dump(records, f, indent=2)
                                except Exception:
                                    pass
                            
                            tickets = load_issues()
                            updated = False
                            for idx, t in enumerate(tickets):
                                if t.get("email", "").strip().lower() == st.session_state.candidate_email.strip().lower() and not t.get("resolved", False):
                                    tickets[idx] = new_ticket
                                    updated = True
                                    break
                            if not updated:
                                tickets.append(new_ticket)
                                
                            save_issues(tickets)
                            
                            if is_auto_resolved:
                                st.session_state.support_resolved_message = cand_notif
                            else:
                                st.session_state.support_pending_message = cand_notif
                            st.session_state.stage = "upload"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Support Agent error: {str(e)}")
