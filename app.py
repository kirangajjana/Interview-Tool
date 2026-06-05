import streamlit as st
import time
from src.config import Config
from src.parser import ResumeParser
from src.agents.screening_agent import ScreeningAgent
from src.agents.mcq_agent import MCQAgent
from src.agents.interview_agent import InterviewAgent
from src.agents.email_agent import EmailAgent

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
        background-color: #fffbf7;
        color: #1e293b;
    }
    
    /* Header Gradient */
    .recruit-header {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #f97316, #ea580c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 5px;
    }
    
    .recruit-sub {
        font-size: 1.1rem;
        color: #475569;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* Card Glassmorphism in Warm Light Theme */
    .glass-card {
        background: #ffffff;
        border: 1px solid #ffedd5;
        border-radius: 16px;
        padding: 25px;
        box-shadow: 0 10px 15px -3px rgba(249, 115, 22, 0.05), 0 4px 6px -4px rgba(249, 115, 22, 0.05);
        margin-bottom: 25px;
    }
    
    .stage-title {
        color: #1e293b;
        font-size: 1.4rem;
        font-weight: 600;
        border-left: 4px solid #f97316;
        padding-left: 10px;
        margin-bottom: 20px;
    }
    
    /* Global Form & Widget Light Customizations */
    div[data-baseweb="input"], div[data-baseweb="select"], textarea {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }
    
    div[data-baseweb="input"] input, textarea {
        color: #1e293b !important;
    }
    
    /* Labels */
    label, [data-testid="stWidgetLabel"] {
        color: #334155 !important;
        font-weight: 500 !important;
    }
    
    /* Placeholders */
    ::placeholder {
        color: #94a3b8 !important;
    }
    
    /* File Uploader styling */
    div[data-testid="stFileUploader"] {
        background-color: #fffdfa !important;
        border: 1px dashed #fdba74 !important;
        border-radius: 12px;
        padding: 10px;
    }
    
    div[data-testid="stFileUploader"] section {
        background-color: transparent !important;
    }
    
    /* Selectbox Dropdown styling */
    div[role="listbox"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
    }
    
    div[role="option"] {
        color: #1e293b !important;
        background-color: #ffffff !important;
    }
    
    div[role="option"]:hover, li[role="option"]:hover {
        background-color: #ffedd5 !important;
    }
    
    /* Read-Only JD Container */
    .jd-container {
        background-color: #fffaf4;
        border: 1px solid #ffedd5;
        border-radius: 8px;
        padding: 15px;
        font-size: 0.95rem;
        color: #475569;
        line-height: 1.6;
        margin-top: 5px;
        margin-bottom: 20px;
        max-height: 200px;
        overflow-y: auto;
        white-space: pre-wrap;
    }
    
    /* Chat styling */
    .chat-bubble-user {
        background: linear-gradient(135deg, #f97316, #ea580c);
        color: white;
        border-radius: 15px 15px 0px 15px;
        padding: 12px 18px;
        margin: 5px 0;
        max-width: 80%;
        float: right;
        clear: both;
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.15);
    }
    
    .chat-bubble-agent {
        background-color: #f1f5f9;
        color: #1e293b;
        border-radius: 15px 15px 15px 0px;
        padding: 12px 18px;
        margin: 5px 0;
        max-width: 80%;
        float: left;
        clear: both;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    
    /* Chat Forms */
    form[data-testid="stForm"] {
        background: #fffdfa;
        border: 1px solid #ffedd5;
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
    }
    
    /* MCQ Radio Options */
    div[data-testid="stRadio"] label {
        color: #475569 !important;
    }
    
    /* Navigation Pills styling */
    div[data-testid="stRadio"] > div {
        background-color: #ffffff;
        border: 1px solid #ffedd5;
        border-radius: 30px;
        padding: 5px 15px;
        box-shadow: 0 2px 5px rgba(249, 115, 22, 0.03);
    }
    
    /* Custom buttons */
    .stButton>button {
        background: linear-gradient(135deg, #f97316, #ea580c);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(249, 115, 22, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Predefined job descriptions to make testing easy
PREDEFINED_JDS = {
    "Senior Backend Developer": (
        "We are looking for a Senior Backend Developer with 5+ years of experience in Python. "
        "Key requirements: Expertise in Django/FastAPI, building scalable REST and gRPC APIs. "
        "Experience with SQL (Postgres) and NoSQL databases, Redis, and message brokers like RabbitMQ. "
        "Familiarity with Docker, AWS cloud services, and CI/CD pipelines. Strong understanding of SOLID principles "
        "and clean architecture."
    ),
    "Machine Learning Engineer": (
        "Looking for an ML Engineer with 3+ years of experience. Strong proficiency in Python, PyTorch/TensorFlow, "
        "and Scikit-Learn. Experience in building NLP pipelines, text classification, or LLM-based applications. "
        "Familiarity with Vector databases (Pinecone, Chroma) and LangChain/LlamaIndex. Experience deploying "
        "ML models in production environments using FastAPI and Docker."
    ),
    "Full Stack Developer": (
        "Seeking a Full Stack Developer. Strong skills in Python (FastAPI/Flask) for backend services. "
        "Proficiency in modern frontend frameworks (React or Vue.js), HTML5, CSS3, and JavaScript/TypeScript. "
        "Experience with state management, clean responsive designs, and SQL database management. "
        "Knowledge of cloud platforms (AWS/GCP/Azure) and automated testing frameworks is a big plus."
    ),
    "Data Scientist": (
        "We are seeking a Data Scientist to join our team. Responsibilities include building machine learning models, "
        "analyzing large complex datasets, and presenting actionable insights. Required skills: Python, SQL, "
        "scikit-learn, pandas, numpy, and experience with data visualization tools (Matplotlib, Tableau). "
        "Familiarity with deep learning frameworks is a plus."
    ),
    "Data Engineer": (
        "We are seeking a Data Engineer to design, deploy, and maintain robust data pipelines. "
        "Key skills include Python, SQL, ETL pipelines, warehouse platforms like Snowflake or BigQuery, "
        "and distributed processing frameworks like Apache Spark. "
        "Experience orchestrating workflows using Apache Airflow is highly preferred."
    ),
    "Software Engineer": (
        "We are looking for a Software Engineer to design, develop, and maintain core software applications. "
        "Key requirements: Proficiency in Python, object-oriented programming, standard design patterns, "
        "writing unit tests, and version control using Git. "
        "Strong understanding of software development lifecycles and clean code practices."
    ),
    "Custom / Write your own": ""
}

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
page = st.radio("Navigation", ["📋 Open Positions", "🎯 Candidate Assessment"], horizontal=True, label_visibility="collapsed", key="active_page")

if page == "📋 Open Positions":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="stage-title">Current Job Openings</div>', unsafe_allow_html=True)
    st.write("Browse through our currently open positions. Click the 'Candidate Assessment' tab above to apply!")
    st.markdown('</div>', unsafe_allow_html=True)
    
    for role, jd in PREDEFINED_JDS.items():
        if role != "Custom / Write your own":
            st.markdown(f'<div class="glass-card">', unsafe_allow_html=True)
            st.markdown(f'<h3 style="color: #ea580c; margin-top: 0; font-size: 1.35rem;">{role}</h3>', unsafe_allow_html=True)
            st.markdown(f'<div class="jd-container" style="max-height: none; background-color: #fffaf4;">{jd}</div>', unsafe_allow_html=True)
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
                mcq_agent = MCQAgent()
                mcq_list = mcq_agent.run(
                    resume_text=st.session_state.resume_text,
                    job_role=st.session_state.job_role,
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
            score, pct, results = MCQAgent.grade_answers(st.session_state.mcqs, temp_answers)
            st.session_state.mcq_score = score
            st.session_state.mcq_passed = True
            
            # Save results list if we want to display details
            st.session_state.mcq_answers = temp_answers
            
            if st.session_state.mcq_passed:
                st.session_state.stage = "mcq_passed_screen"
            else:
                st.session_state.stage = "mcq_failed_screen"
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
            {"role": "assistant", "content": f"Hello {st.session_state.candidate_name}. Welcome to your technical interview for the {st.session_state.job_role} role. Let's start with a very basic question: What is Machine Learning, and what are the main types of Machine Learning?"}
        ]
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
            with st.spinner("Interviewer is reviewing your answer and preparing the next question..."):
                try:
                    interview_agent = InterviewAgent()
                    # We pass the history (excluding the very first welcoming greeting in the count)
                    # We ask 3 total questions (excluding welcome)
                    res = interview_agent.run(
                        resume_text=st.session_state.resume_text,
                        job_role=st.session_state.job_role,
                        experience=st.session_state.experience,
                        job_description=st.session_state.job_description,
                        conversation_history=st.session_state.chat_history,
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
                    st.rerun()
                except Exception as e:
                    st.error(f"Error during final evaluation: {str(e)}")

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
            with st.spinner("Placing selection voice call to candidate via ElevenLabs..."):
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
                        st.success(f"Successfully called candidate at {st.session_state.candidate_phone} via ElevenLabs Voice.")
                    else:
                        st.warning(f"Could not connect ElevenLabs voice call: {call_res['message']} (Details: {call_res.get('data', {}).get('message', 'N/A')})")
                except Exception as e:
                    st.warning(f"Failed to initiate ElevenLabs phone call: {str(e)}")
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
