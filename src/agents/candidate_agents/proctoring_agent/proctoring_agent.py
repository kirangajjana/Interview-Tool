from src.agents.shared_agents.base_agent import BaseAgent
from src.agents.candidate_agents.proctoring_agent.prompts import PROCTORING_SYSTEM_PROMPT
from src.models.schemas import ProctoringReport

class ProctoringAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt=PROCTORING_SYSTEM_PROMPT, temperature=0.1)

    def run(self, candidate_name: str, email: str, job_role: str, tab_switches: int, warnings_timestamps: list, stage: str) -> ProctoringReport:
        structured_llm = self.llm.with_structured_output(ProctoringReport)
        chain = self.prompt_template | structured_llm
        
        timestamps_str = ", ".join(warnings_timestamps) if warnings_timestamps else "None"
        input_text = f"""
Candidate Name: {candidate_name}
Candidate Email: {email}
Job Role: {job_role}
Total Tab Switches: {tab_switches}
Warning Timestamps: {timestamps_str}
Assessment Stage when finished: {stage}
"""
        return chain.invoke({"input_text": input_text})
