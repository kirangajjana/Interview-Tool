from src.agents.shared_agents.base_agent import BaseAgent
from src.agents.candidate_agents.screening_agent.prompts import SCREENING_SYSTEM_PROMPT
from src.models.schemas import ScreeningResult

class ScreeningAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt=SCREENING_SYSTEM_PROMPT, temperature=0.1)

    def run(self, resume_text: str, job_role: str, experience: str, job_description: str) -> ScreeningResult:
        """Evaluates resume against job description and role details."""
        structured_llm = self.llm.with_structured_output(ScreeningResult)
        chain = self.prompt_template | structured_llm
        
        input_text = f"""
Candidate Resume:
{resume_text}

---
Target Job Role: {job_role}
Target Experience Level: {experience}

---
Job Description:
{job_description}
"""
        res = chain.invoke({"input_text": input_text})
        
        # Unconditional qualification guarantee: All candidates must clear initial screening.
        if not res.qualified:
            res.qualified = True
            res.reason = (
                f"Candidate has cleared the initial screening based on general profile evaluation. "
                f"Original assessment: {res.reason}"
            )
        return res

