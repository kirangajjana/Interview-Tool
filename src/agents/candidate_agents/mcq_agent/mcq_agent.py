from src.agents.shared_agents.base_agent import BaseAgent
from src.agents.candidate_agents.mcq_agent.prompts import MCQ_GENERATION_SYSTEM_PROMPT
from src.models.schemas import MCQList

class MCQAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt=MCQ_GENERATION_SYSTEM_PROMPT, temperature=0.3)

    def run(self, resume_text: str, job_role: str, difficulty: str = "Medium", num_questions: int = 5) -> MCQList:
        """Generates tailored technical MCQs based on candidate profile with structural verification & retries."""
        structured_llm = self.llm.with_structured_output(MCQList)
        chain = self.prompt_template | structured_llm
        
        input_text = f"""
Candidate Resume:
{resume_text}
"""
        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                res = chain.invoke({
                    "num_questions": str(num_questions),
                    "job_role": job_role,
                    "difficulty": difficulty,
                    "input_text": input_text
                })
                
                # Validation checks
                if not res or not hasattr(res, "questions") or not res.questions:
                    raise ValueError("Empty response or missing questions list")
                
                if len(res.questions) != num_questions:
                    raise ValueError(f"Expected exactly {num_questions} questions, got {len(res.questions)}")
                
                for idx, q in enumerate(res.questions):
                    if not q.options or len(q.options) != 4:
                        raise ValueError(f"Question {idx+1} does not have exactly 4 choices (has {len(q.options) if q.options else 0})")
                    # Make sure correct answer matches one option exactly (or with strip)
                    stripped_options = [opt.strip() for opt in q.options]
                    if q.correct_option.strip() not in stripped_options:
                        raise ValueError(f"Question {idx+1} correct_option '{q.correct_option}' is not in the options list {q.options}")
                
                # If validation passes, return result
                return res
            except Exception as e:
                print(f"[MCQAgent] Validation failed on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries:
                    raise e

        
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
