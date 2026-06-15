from src.agents.shared_agents.base_agent import BaseAgent
from src.models.schemas import JobAction
import json

class JobAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt="You are a Job Description AI Assistant.", temperature=0.2)

    def run(self, command: str, active_jobs: dict) -> JobAction:
        """Processes recruiter job management commands and produces a structured JobAction."""
        formatted_jobs = json.dumps(active_jobs, indent=2)
        
        system_prompt = """You are a specialized Job Description & Posting Management AI Agent.
Your job is to assist recruiters in managing the active job openings listed on the platform.

You can perform four main actions:
1. 'add': Create and draft a new job description from brief recruiter notes or criteria. You must write a detailed, highly professional, markdown-formatted job description including: Job Title/Role, Key Responsibilities, and Required Skills.
2. 'update': Edit or rewrite an existing job description. Retrieve the current description from the provided active job list, apply the recruiter's requested changes, and return the FULL, updated description.
3. 'delete': Remove a job opening from the list.
4. 'none': For general chat, help requests, or if the recruiter's instructions are too vague/unrelated to job postings.

Here is the current dictionary of active job postings:
{active_jobs}

Rules:
- For 'add': Generate a detailed description with distinct markdown headers for Key Responsibilities and Required Skills.
- For 'update': Make sure you do NOT delete existing essential requirements unless explicitly requested. Return the entire modified description.
- For 'delete': The job title must exactly match one of the keys in the active jobs.
- If the instruction is ambiguous (e.g. "change software"), set action to 'none' and ask for clarification in the explanation.
- Always provide a clear, professional, and friendly explanation of the action you took.
"""

        # Set up prompts dynamically for the run
        self.system_prompt = system_prompt
        from langchain_core.prompts import ChatPromptTemplate
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input_text}")
        ])
        
        structured_llm = self.llm.with_structured_output(JobAction)
        chain = self.prompt_template | structured_llm
        
        return chain.invoke({
            "active_jobs": formatted_jobs,
            "input_text": command
        })
