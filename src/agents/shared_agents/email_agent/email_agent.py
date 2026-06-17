import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import Config
from src.agents.shared_agents.email_agent.templates import (
    SELECTION_EMAIL_SUBJECT, SELECTION_EMAIL_BODY,
    REJECTION_EMAIL_SUBJECT, REJECTION_EMAIL_BODY
)

class EmailAgent:
    def __init__(self):
        # Dynamically load configurations
        self.config = Config.load_config()

    def run(self, recipient_email: str, candidate_name: str, job_role: str, feedback_summary: str, is_selected: bool = True) -> bool:
        """Connects to SMTP server and sends candidate notification email."""
        # Safeguard if SMTP parameters are not provided
        if not self.config.SMTP_SENDER_EMAIL or not self.config.SMTP_SENDER_PASSWORD:
            print("[EmailAgent] SMTP_SENDER_EMAIL or SMTP_SENDER_PASSWORD is not set. Skipping email delivery.")
            return False

        subject = ""
        body = ""

        # Try to draft the email dynamically using Gemini LLM if API key is present
        if self.config.GEMINI_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                from langchain_core.prompts import ChatPromptTemplate
                
                chat_model = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=self.config.GEMINI_API_KEY,
                    temperature=0.3
                )
                
                status_str = "SELECTED for the next hiring rounds" if is_selected else "NOT SELECTED / Rejected at this stage"
                
                prompt_tpl = ChatPromptTemplate.from_messages([
                    ("system", """You are an official corporate communications assistant representing the HR and Talent Acquisition Department.
Your job is to draft a highly professional, formal, and official email from our company (AgentFlow Recruitment Platform) to a candidate regarding their interview outcome.

Ensure the email follows these guidelines:
1. Tone must be strictly formal, professional, and corporate as a company.
2. Address the candidate directly by their name.
3. If selected, congratulate the candidate formally and state that HR will reach out shortly for the next steps.
4. If not selected, thank them formally for their time and interest, state that we will keep their profile in our talent pool/database for future consideration, and wish them well.
5. Do NOT include any specific technical interview feedback, score list, or evaluation comments in the email.
6. The output MUST begin with a Subject: header line, followed by a separator line of ---, followed by the email body content.

Format the output strictly as:
Subject: <clear subject line>
---
<email body>
"""),
                    ("human", """Candidate Name: {candidate_name}
Applied Position: {job_role}
Selection Outcome: {status}
""")
                ])
                
                chain = prompt_tpl | chat_model
                response = chain.invoke({
                    "candidate_name": candidate_name,
                    "job_role": job_role,
                    "status": status_str
                })
                
                content = response.content.strip()
                if "Subject:" in content and "---" in content:
                    parts = content.split("---", 1)
                    subj_part = parts[0].replace("Subject:", "").strip()
                    body_part = parts[1].strip()
                    if subj_part and body_part:
                        subject = subj_part
                        body = body_part
                        print("[EmailAgent] Successfully drafted custom official email using AI model.")
            except Exception as e:
                print(f"[EmailAgent] AI email drafting failed: {str(e)}. Falling back to static templates.")

        # Fallback to static templates if dynamic generation was not successful
        if not subject or not body:
            if is_selected:
                subject = SELECTION_EMAIL_SUBJECT.format(job_role=job_role)
                body = SELECTION_EMAIL_BODY.format(
                    candidate_name=candidate_name,
                    job_role=job_role
                )
            else:
                subject = REJECTION_EMAIL_SUBJECT.format(job_role=job_role)
                body = REJECTION_EMAIL_BODY.format(
                    candidate_name=candidate_name,
                    job_role=job_role
                )

        try:
            # Set up email structures
            msg = MIMEMultipart()
            msg["From"] = self.config.SMTP_SENDER_EMAIL
            msg["To"] = recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            
            # Connect to SMTP Server
            server = smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT)
            server.starttls()
            server.login(self.config.SMTP_SENDER_EMAIL, self.config.SMTP_SENDER_PASSWORD)
            
            # Send message and close connection
            server.sendmail(self.config.SMTP_SENDER_EMAIL, recipient_email, msg.as_string())
            server.quit()
            print(f"[EmailAgent] Email successfully sent to {recipient_email}")
            return True
        except Exception as e:
            print(f"[EmailAgent] Failed to send email to {recipient_email}. Error: {str(e)}")
            return False
