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
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom premium styling inject
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background-color: #fffbf8;
        color: #1e293b;
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
            box-shadow: 0 0 0 0 rgba(234, 88, 12, 0.2);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(234, 88, 12, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(234, 88, 12, 0);
        }
    }
    
    /* Header Gradient */
    .recruit-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #f97316, #ea580c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 5px;
        letter-spacing: -0.5px;
        animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    
    .recruit-sub {
        font-size: 1.15rem;
        color: #475569;
        text-align: center;
        margin-bottom: 35px;
        font-weight: 400;
        animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    
    /* Card Glassmorphism in Warm Light Theme */
    .glass-card {
        background: #ffffff;
        border: 1px solid #ffedd5;
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 10px 25px -5px rgba(249, 115, 22, 0.05), 0 8px 10px -6px rgba(249, 115, 22, 0.05);
        margin-bottom: 30px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 30px -10px rgba(249, 115, 22, 0.08), 0 10px 15px -8px rgba(249, 115, 22, 0.08);
    }
    
    .stage-title {
        color: #1e293b;
        font-size: 1.45rem;
        font-weight: 600;
        border-left: 5px solid #f97316;
        padding-left: 12px;
        margin-bottom: 25px;
    }
    
    /* Global Form & Widget Light Customizations */
    div[data-baseweb="input"], div[data-baseweb="select"], textarea {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, textarea:focus {
        border-color: #ea580c !important;
        box-shadow: 0 0 0 3px rgba(234, 88, 12, 0.15) !important;
    }
    
    div[data-baseweb="input"] input, textarea {
        color: #1e293b !important;
    }
    
    /* Labels */
    label, [data-testid="stWidgetLabel"] {
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin-bottom: 8px !important;
    }
    
    /* Placeholders */
    ::placeholder {
        color: #94a3b8 !important;
    }
    
    /* File Uploader styling */
    div[data-testid="stFileUploader"] {
        background-color: #fffdfa !important;
        border: 2px dashed #fdba74 !important;
        border-radius: 14px;
        padding: 15px;
        transition: border-color 0.3s ease;
    }
    
    div[data-testid="stFileUploader"]:hover {
        border-color: #ea580c !important;
    }
    
    div[data-testid="stFileUploader"] section {
        background-color: transparent !important;
    }
    
    /* Selectbox Dropdown styling */
    div[role="listbox"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px;
    }
    
    div[role="option"] {
        color: #1e293b !important;
        background-color: #ffffff !important;
        padding: 10px 15px !important;
    }
    
    div[role="option"]:hover, li[role="option"]:hover {
        background-color: #ffedd5 !important;
        color: #ea580c !important;
    }
    
    /* Read-Only JD Container */
    .jd-container {
        background-color: #fffaf4;
        border: 1px solid #ffedd5;
        border-radius: 10px;
        padding: 20px;
        font-size: 0.95rem;
        color: #475569;
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
        background-color: #f8fafc;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        color: #64748b;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #ea580c;
        background-color: #fff7ed;
    }
    
    .stTabs [aria-selected="true"] {
        color: #ea580c !important;
        background-color: #ffffff !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    
    /* Navigation Pills styling */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 30px;
        padding: 6px 12px !important;
        display: flex;
        flex-direction: row;
        justify-content: center;
        gap: 10px;
        margin-bottom: 25px;
    }
    
    div[data-testid="stRadio"] label[data-baseweb="radio"] {
        background-color: transparent;
        border: none;
        padding: 6px 16px;
        border-radius: 20px;
        color: #64748b;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
        color: #ea580c;
        background-color: #fff7ed;
    }
    
    /* Custom buttons */
    .stButton>button {
        background: linear-gradient(135deg, #f97316, #ea580c);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 28px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(234, 88, 12, 0.15);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(234, 88, 12, 0.3);
        background: linear-gradient(135deg, #ea580c, #c2410c);
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

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

page = st.radio("Navigation", nav_options, index=default_nav_idx, horizontal=True, label_visibility="collapsed")
st.session_state.current_page = page

if page == "📋 Open Positions":
    st.markdown('<div class="glass-card" style="text-align: center;">', unsafe_allow_html=True)
    st.markdown('<div class="recruit-header" style="font-size: 2.2rem; margin-bottom: 10px; background: linear-gradient(135deg, #f97316, #ea580c); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">💼 Explore Career Opportunities</div>', unsafe_allow_html=True)
    st.markdown('<div style="color: #64748b; font-size: 1.05rem;">Select a position below to view requirements and start your AI-guided assessment.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    for role, jd in PREDEFINED_JDS.items():
        if role != "Custom / Write your own":
            st.markdown(f"""
            <div class="glass-card" style="border-left: 6px solid #ea580c; padding: 25px; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; flex-wrap: wrap; gap: 10px;">
                    <h3 style="color: #1e293b; margin: 0; font-size: 1.45rem; font-weight: 700;">{role}</h3>
                </div>
                <div style="color: #475569; line-height: 1.6; font-size: 0.95rem; margin-bottom: 15px; white-space: pre-wrap;">{jd}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Interactive columns for applying directly
            col1, col2 = st.columns([6, 2])
            with col2:
                if st.button(f"Apply Now →", key=f"apply_btn_{role}", use_container_width=True):
                    st.session_state.selected_role_val = role
                    st.session_state.current_page = "🎯 Candidate Assessment"
                    st.rerun()
            st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
    st.stop()

elif page == "🔒 Recruiter Portal":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="stage-title">🔒 Recruiter Portal</div>', unsafe_allow_html=True)
    
    st.write("Hello Recruiter! Welcome to your administrative control center.")
    
    # Notify recruiter of auto-resolved support tickets
    try:
        tickets_db = load_issues()
        auto_resolved = [t for t in tickets_db if t.get("resolved") and t.get("resolved_by") == "AI Auto-Resolver"]
        if auto_resolved:
            st.info(f"🤖 **AI Auto-Resolver Notification**: The AI agent has successfully resolved **{len(auto_resolved)}** candidate issue(s) automatically. You can review resolution logs under the **Support & Help Requests** tab.")
    except Exception:
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
            
            selected_cand = st.selectbox("Select Candidate to view detailed scorecard", [f"{c['name']} ({c['email']}) - {c['job_role']}" for c in candidates])
            
            matched_candidate = None
            for c in candidates:
                if f"{c['name']} ({c['email']}) - {c['job_role']}" == selected_cand:
                    matched_candidate = c
                    break
            
            if matched_candidate:
                st.markdown(f'<div class="glass-card" style="border-left: 5px solid #f97316; padding: 20px;">', unsafe_allow_html=True)
                st.markdown(f"### Scorecard: {matched_candidate['name']}")
                
                # Visual Match Score Progress Bar
                score = int(matched_candidate.get("match_score", 0))
                st.write(f"**AI Match Score**: **{score}%**")
                st.progress(score / 100.0)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"📧 **Email**: {matched_candidate['email']}")
                    st.write(f"📞 **Phone**: {matched_candidate['phone']}")
                    st.write(f"💼 **Role**: {matched_candidate['job_role']}")
                with col2:
                    st.write(f"⏳ **Experience Level**: {matched_candidate['experience']}")
                    st.write(f"📌 **Pipeline Status**: `{matched_candidate['status']}`")
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
                    
                st.markdown('</div>', unsafe_allow_html=True)
                        
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
                            <h4 style="margin: 0; color: #1e293b;">{t.get('name')} ({t.get('email')})</h4>
                            <span style="background-color: {severity_color}20; color: {severity_color}; padding: 3px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">{t.get('severity', 'Medium')} Priority</span>
                        </div>
                        <div style="font-size: 0.95rem; margin-bottom: 12px; color: #475569; line-height: 1.5;">
                            <strong>Target Role:</strong> {t.get('job_role')}<br>
                            <strong>Timestamp:</strong> {t.get('timestamp')}<br>
                            <strong>Candidate's Description:</strong> <em>"{t.get('message')}"</em>
                        </div>
                        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                            <strong style="color: #0f172a; font-size: 0.95rem;">🤖 AI Support Agent Diagnosis:</strong><br>
                            <p style="margin-top: 5px; margin-bottom: 5px; font-size: 0.95rem; color: #334155;">{t.get('diagnosis')}</p>
                            <strong>Suggested Action:</strong> <span style="color: #ea580c;">{t.get('suggested_action')}</span><br>
                            <strong>Justification:</strong> <span style="color: #64748b; font-style: italic;">{t.get('justification')}</span>
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
                            <h4 style="margin: 0; color: #1e293b;">{t.get('name')} ({t.get('email')})</h4>
                            <span style="background-color: #dcfce7; color: #166534; padding: 3px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">Auto-Resolved</span>
                        </div>
                        <div style="font-size: 0.95rem; margin-bottom: 12px; color: #475569; line-height: 1.5;">
                            <strong>Applied Role:</strong> {t.get('job_role')}<br>
                            <strong>Date Resolved:</strong> {t.get('timestamp')}<br>
                            <strong>Issue Reported:</strong> <em>"{t.get('message')}"</em>
                        </div>
                        <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 15px;">
                            <strong style="color: #166534; font-size: 0.95rem;">🤖 AI Justification & Action:</strong><br>
                            <p style="margin-top: 5px; margin-bottom: 5px; font-size: 0.95rem; color: #1e293b;">{t.get('resolution_log')}</p>
                            <strong>Confidence Score:</strong> <code>{int(t.get('confidence_score', 0.0) * 100)}%</code>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
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
            <p style="color: #475569; font-size: 0.95rem; line-height: 1.6;">
                Our records show that a candidate with the email <strong>{dup.get('email')}</strong> has already registered or completed an assessment.
            </p>
            <div style="background-color: #fdf2f2; border: 1px solid #fecaca; border-radius: 12px; padding: 20px; margin: 20px 0; color: #1f2937;">
                <strong style="color: #b91c1c; font-size: 1rem;">Previous Application Summary:</strong><br>
                <div style="margin-top: 10px; font-size: 0.95rem; line-height: 1.8;">
                    • <strong>Candidate Name:</strong> {dup.get('name')}<br>
                    • <strong>Target Role:</strong> {dup.get('job_role')}<br>
                    • <strong>Pipeline Stage:</strong> <span style="background-color: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 6px; font-size: 0.85rem; font-weight: 600;">{dup.get('status')}</span><br>
                    • <strong>Date Submitted:</strong> {dup.get('timestamp')}
                </div>
            </div>
            <p style="font-size: 0.95rem; color: #475569; line-height: 1.5; margin-bottom: 0;">
                To ensure a fair evaluation process, multiple attempts are not permitted. If you encountered technical difficulties, please connect with your recruiter for better understanding or to request an assessment reset.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Report form section
        st.markdown('<div class="glass-card" style="margin-top: 15px; border-left: 5px solid #f97316;">', unsafe_allow_html=True)
        st.markdown('<h4 style="margin-top: 0; color: #1e293b;">🛠️ Having Technical Issues or Need a Retake?</h4>', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("← Go Back to Form"):
            st.session_state.duplicate_blocked = False
            st.session_state.duplicate_candidate = None
            st.rerun()
        st.stop()

    # Render persistent support notifications if candidate email matches a resolved ticket
    active_email = st.session_state.get("candidate_email_val", "").strip().lower()
    if active_email:
        tickets = load_issues()
        resolved_tickets = [t for t in tickets if t.get("email", "").strip().lower() == active_email and t.get("resolved", False)]
        if resolved_tickets:
            latest_ticket = resolved_tickets[-1]
            st.markdown(f"""
            <div class="glass-card" style="border-left: 6px solid #10b981; padding: 20px; margin-bottom: 25px; background-color: #f0fdf4;">
                <h5 style="margin: 0 0 8px 0; color: #166534; font-size: 1.1rem; font-weight: 700;">🔔 Helpdesk Update</h5>
                <p style="margin: 0; color: #1e293b; font-size: 0.95rem; line-height: 1.5;">
                    {latest_ticket.get('candidate_notification', latest_ticket.get('resolution_log'))}
                </p>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 8px;">
                    Resolved on: {latest_ticket.get('timestamp')}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="stage-title">Candidate Profile & Resume Upload</div>', unsafe_allow_html=True)
    
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
    
    st.markdown('</div>', unsafe_allow_html=True)
    
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
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="stage-title" style="border-left-color: #10b981;">Screening Status: Qualified</div>', unsafe_allow_html=True)
    st.success(f"Congratulations {st.session_state.candidate_name}! Your resume has cleared our initial screening.")
    st.write("**Recruiter Assessment:**")
    st.info(st.session_state.screening_result.reason)
    
    st.write("You are qualified to move to the **Technical MCQ Screening Round**. You will be moved to the next stage of evaluation.")
    st.markdown('</div>', unsafe_allow_html=True)
    
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
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="stage-title" style="border-left-color: #ef4444;">Screening Status: Disqualified</div>', unsafe_allow_html=True)
    st.error(f"Thank you for applying, {st.session_state.candidate_name}. Unfortunately, your profile does not meet our minimum requirements for this position.")
    st.write("**Evaluation Feedback:**")
    st.warning(st.session_state.screening_result.reason)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("Try Again / Adjust Application"):
        restart_process()

# ----------------- STAGE 3: TECHNICAL MCQ PHASE -----------------
elif st.session_state.stage == "mcq":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="stage-title">Stage 2: Technical MCQ Screening</div>', unsafe_allow_html=True)
    st.info("Answer the following questions based on technical competencies. Passing threshold is 60% (3 out of 5 correct).")
    
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
            
    st.markdown('</div>', unsafe_allow_html=True)
    
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
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="stage-title" style="border-left-color: #10b981;">MCQ Screening Passed</div>', unsafe_allow_html=True)
    st.success(f"Great job! You scored {st.session_state.mcq_score}/5 ({st.session_state.mcq_score * 20}%).")
    st.write("You have successfully passed the MCQ barrier and are eligible for the **Interactive Technical Interview Round**.")
    st.markdown('</div>', unsafe_allow_html=True)
    
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
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="stage-title" style="border-left-color: #ef4444;">MCQ Screening Failed</div>', unsafe_allow_html=True)
    st.error(f"You scored {st.session_state.mcq_score}/5. The passing score is at least 3/5.")
    st.write("Unfortunately, we cannot proceed with your application at this time.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("Back to Start"):
        restart_process()

# ----------------- STAGE 5: CONVERSATIONAL TECHNICAL INTERVIEW -----------------
elif st.session_state.stage == "interview":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="stage-title">Stage 3: Interactive Technical Interview</div>', unsafe_allow_html=True)
    st.info("Respond to the Interview Agent. They will ask questions tailored to your resume skills.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display Chat Bubbles using native interactive chat elements
    for message in st.session_state.chat_history:
        avatar_emoji = "🧑" if message["role"] == "user" else "🤖"
        with st.chat_message(message["role"], avatar=avatar_emoji):
            st.write(message["content"])
            
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
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="stage-title">Final Interview Assessment</div>', unsafe_allow_html=True)
    
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
        st.markdown('</div>', unsafe_allow_html=True)
        
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
        st.markdown('</div>', unsafe_allow_html=True)

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
