import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import Config
from src.agents.shared_agents.email_agent.templates import SELECTION_EMAIL_SUBJECT, SELECTION_EMAIL_BODY

class EmailAgent:
    def __init__(self):
        # Dynamically load configurations
        self.config = Config.load_config()

    def run(self, recipient_email: str, job_role: str, feedback_summary: str) -> bool:
        """Connects to SMTP server and sends candidate notification email."""
        # Safeguard if SMTP parameters are not provided
        if not self.config.SMTP_SENDER_EMAIL or not self.config.SMTP_SENDER_PASSWORD:
            print("[EmailAgent] SMTP_SENDER_EMAIL or SMTP_SENDER_PASSWORD is not set. Skipping email delivery.")
            return False

        try:
            # Set up email structures
            msg = MIMEMultipart()
            msg["From"] = self.config.SMTP_SENDER_EMAIL
            msg["To"] = recipient_email
            msg["Subject"] = SELECTION_EMAIL_SUBJECT.format(job_role=job_role)
            
            body = SELECTION_EMAIL_BODY.format(
                job_role=job_role,
                feedback_summary=feedback_summary
            )
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
