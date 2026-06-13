from src.agents.base_agent import BaseAgent
from src.agents.repeat_agent.prompts import CLARIFICATION_SYSTEM_PROMPT
from src.models.schemas import ClarificationResult

class RepeatAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt=CLARIFICATION_SYSTEM_PROMPT, temperature=0.1)

    def run(self, candidate_message: str, last_question: str) -> ClarificationResult:
        """Diagnoses if the candidate is asking for clarification/repetition and handles it."""
        structured_llm = self.llm.with_structured_output(ClarificationResult)
        chain = self.prompt_template | structured_llm
        
        input_text = f"""
AI Interviewer Last Question/Statement:
"{last_question}"

Candidate Latest Message:
"{candidate_message}"
"""
        return chain.invoke({"input_text": input_text})
