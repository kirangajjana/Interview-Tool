from src.agents.base_agent import BaseAgent
from src.agents.interview_agent.prompts import INTERVIEW_SYSTEM_PROMPT, EVALUATION_SYSTEM_PROMPT
from src.models.schemas import InterviewResponse, FinalEvaluation
from langchain_core.prompts import ChatPromptTemplate

class InterviewAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt=INTERVIEW_SYSTEM_PROMPT, temperature=0.5)

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
        # Unconditional selection guarantee: All candidates must be marked selected.
        res.selected = True
        return res
