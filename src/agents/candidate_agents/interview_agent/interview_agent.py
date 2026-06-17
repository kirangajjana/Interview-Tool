from src.agents.shared_agents.base_agent import BaseAgent
from src.agents.candidate_agents.interview_agent.prompts import INTERVIEW_SYSTEM_PROMPT, EVALUATION_SYSTEM_PROMPT
from src.models.schemas import InterviewResponse, FinalEvaluation
from langchain_core.prompts import ChatPromptTemplate
import re

class InterviewAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt=INTERVIEW_SYSTEM_PROMPT, temperature=0.5)

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Redacts PII (email, phone numbers, addresses) from candidate messages."""
        # Redact emails
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        text = re.sub(email_pattern, '[REDACTED_EMAIL]', text)
        
        # Redact phone numbers
        phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{10,12}\b'
        text = re.sub(phone_pattern, '[REDACTED_PHONE]', text)
        
        # Redact postal / zip codes
        zip_pattern = r'\b\d{5}(?:-\d{4})?\b|\b\d{6}\b'
        text = re.sub(zip_pattern, '[REDACTED_POSTAL_CODE]', text)
        
        # Redact street addresses
        address_pattern = r'\b\d+\s+[A-Za-z0-9\s,.-]+?\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Circle|Cir|Way)\b'
        text = re.sub(address_pattern, '[REDACTED_ADDRESS]', text, flags=re.IGNORECASE)
        
        return text

    def validate_input(self, text: str) -> tuple[bool, str]:
        """
        Validates candidate inputs against prompt injection and toxicity.
        Returns (is_valid, warning_message).
        """
        text_lower = text.lower()
        
        # 1. Prompt Injection Detection
        injection_keywords = [
            "ignore previous instructions", 
            "ignore previous",
            "system prompt", 
            "system instructions", 
            "you are now a", 
            "developer mode", 
            "override instructions",
            "ignore the instructions",
            "disregard all previous"
        ]
        for kw in injection_keywords:
            if kw in text_lower:
                return False, "⚠️ **System Guardrail Alert**: Prompt injection or system overwrite attempt detected. Please focus on answering the interview questions professionally."
        
        # 2. Toxicity Detection
        toxic_keywords = [
            "fuck", "shit", "asshole", "bitch", "cunt", "bastard", "dick", "pussy", "idiot", "stupid", "crap"
        ]
        for kw in toxic_keywords:
            pattern = rf"\b{kw}s?\b"
            if re.search(pattern, text_lower):
                return False, "⚠️ **System Guardrail Alert**: Offensive or unprofessional language detected. Please keep your responses professional and polite."
                
        return True, ""

    def run(self, resume_text: str, job_role: str, experience: str, job_description: str, conversation_history: list, difficulty: str = "Medium", num_questions: int = 3) -> InterviewResponse:
        """Determines the next conversation turn and whether to conclude the chat."""
        structured_llm = self.llm.with_structured_output(InterviewResponse)
        chain = self.prompt_template | structured_llm
        
        # Format conversation transcript
        formatted_history = ""
        for msg in conversation_history:
            role_name = "Interviewer" if msg["role"] == "assistant" else "Candidate"
            formatted_history += f"{role_name}: {msg['content']}\n"
            
        input_text = f"""
Candidate Resume:
{resume_text}

---
Job Description:
{job_description}

---
Conversation History:
{formatted_history}
"""
        return chain.invoke({
            "job_role": job_role,
            "experience": experience,
            "difficulty": difficulty,
            "num_questions": str(num_questions),
            "input_text": input_text
        })

    def evaluate(self, resume_text: str, job_role: str, experience: str, job_description: str, conversation_history: list) -> FinalEvaluation:
        """Performs a comprehensive evaluation of the interview transcript."""
        eval_prompt = ChatPromptTemplate.from_messages([
            ("system", EVALUATION_SYSTEM_PROMPT),
            ("human", "{input_text}")
        ])
        structured_llm = self.llm.with_structured_output(FinalEvaluation)
        chain = eval_prompt | structured_llm
        
        formatted_history = ""
        for msg in conversation_history:
            role_name = "Interviewer" if msg["role"] == "assistant" else "Candidate"
            formatted_history += f"{role_name}: {msg['content']}\n"
            
        input_text = f"""
Candidate Resume:
{resume_text}

---
Job Details:
Role: {job_role}
Experience: {experience}
Job Description: {job_description}

---
Complete Chat Transcript:
{formatted_history}
"""
        res = chain.invoke({"input_text": input_text})
        return res

