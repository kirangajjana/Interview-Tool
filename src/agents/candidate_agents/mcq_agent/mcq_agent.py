from src.agents.shared_agents.base_agent import BaseAgent
from src.agents.candidate_agents.mcq_agent.prompts import MCQ_GENERATION_SYSTEM_PROMPT
from src.models.schemas import MCQList

class MCQAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt=MCQ_GENERATION_SYSTEM_PROMPT, temperature=0.3)

    def run(self, resume_text: str, job_role: str, difficulty: str = "Medium", num_questions: int = 5) -> MCQList:
        """Generates tailored technical MCQs based on candidate profile."""
        structured_llm = self.llm.with_structured_output(MCQList)
        chain = self.prompt_template | structured_llm
        
        input_text = f"""
Candidate Resume:
{resume_text}
"""
        return chain.invoke({
            "num_questions": str(num_questions),
            "job_role": job_role,
            "difficulty": difficulty,
            "input_text": input_text
        })
        
    @staticmethod
    def grade_answers(questions: list, user_answers: dict) -> tuple:
        """
        Grades user answers deterministically using Python code.
        Returns:
            (score, percentage, results_list)
        """
        score = 0
        total = len(questions)
        results = []
        for i, q in enumerate(questions):
            correct = q.correct_option.strip()
            user_ans = user_answers.get(i, "").strip()
            is_correct = (user_ans == correct)
            if is_correct:
                score += 1
            results.append({
                "question": q.question,
                "options": q.options,
                "correct_option": correct,
                "user_answer": user_ans,
                "is_correct": is_correct
            })
        percentage = (score / total) * 100 if total > 0 else 0
        return score, percentage, results
