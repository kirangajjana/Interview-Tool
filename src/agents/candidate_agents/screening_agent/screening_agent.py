from src.agents.shared_agents.base_agent import BaseAgent
from src.agents.candidate_agents.screening_agent.prompts import SCREENING_SYSTEM_PROMPT
from src.models.schemas import ScreeningResult
import re

class ScreeningAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt=SCREENING_SYSTEM_PROMPT, temperature=0.1)

    @staticmethod
    def sanitize_resume(text: str) -> str:
        """Redacts candidate email, phone numbers, and street addresses using regex."""
        # Redact emails
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        text = re.sub(email_pattern, '[REDACTED_EMAIL]', text)
        
        # Redact phone numbers (standard formats)
        phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{10,12}\b'
        text = re.sub(phone_pattern, '[REDACTED_PHONE]', text)
        
        # Redact zip / postal codes
        zip_pattern = r'\b\d{5}(?:-\d{4})?\b|\b\d{6}\b'
        text = re.sub(zip_pattern, '[REDACTED_POSTAL_CODE]', text)
        
        # Redact street addresses
        address_pattern = r'\b\d+\s+[A-Za-z0-9\s,.-]+?\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Circle|Cir|Way)\b'
        text = re.sub(address_pattern, '[REDACTED_ADDRESS]', text, flags=re.IGNORECASE)
        
        return text

    def run(self, resume_text: str, job_role: str, experience: str, job_description: str) -> ScreeningResult:
        """Evaluates resume against job description and role details."""
        # Sanitize resume text
        sanitized_resume = self.sanitize_resume(resume_text)
        print(f"[ScreeningAgent] Sanitized Resume (PII Redacted):\n{sanitized_resume}\n")
        
        structured_llm = self.llm.with_structured_output(ScreeningResult)
        chain = self.prompt_template | structured_llm
        
        input_text = f"""
Candidate Resume:
{sanitized_resume}

---
Target Job Role: {job_role}
Target Experience Level: {experience}

---
Job Description:
{job_description}
"""
        res = chain.invoke({"input_text": input_text})
        return res


