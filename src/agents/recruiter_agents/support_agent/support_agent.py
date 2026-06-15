from src.agents.shared_agents.base_agent import BaseAgent
from src.agents.recruiter_agents.support_agent.prompts import SUPPORT_AGENTS_SYSTEM_PROMPT
from src.models.schemas import SupportDiagnosis

class SupportAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt=SUPPORT_AGENTS_SYSTEM_PROMPT, temperature=0.2)

    def run(self, candidate_email: str, reported_message: str, candidate_history: dict = None) -> SupportDiagnosis:
        """Diagnoses candidate help tickets using their pipeline state."""
        structured_llm = self.llm.with_structured_output(SupportDiagnosis)
        chain = self.prompt_template | structured_llm
        
        history_summary = "No previous candidate record found in system."
        if candidate_history:
            history_summary = f"""
Name: {candidate_history.get('name')}
Applied Role: {candidate_history.get('job_role')}
Pipeline Status: {candidate_history.get('status')}
Date Submitted: {candidate_history.get('timestamp')}
MCQ Score: {candidate_history.get('mcq_score')}
Recommendation: {candidate_history.get('selection')}
Summary: {candidate_history.get('summary')}
"""
            
        input_text = f"""
Candidate Email: {candidate_email}

Reported Issue/Message:
"{reported_message}"

Candidate History Context:
---
{history_summary}
---
"""
        return chain.invoke({"input_text": input_text})
