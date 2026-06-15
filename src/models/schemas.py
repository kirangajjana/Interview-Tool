from pydantic import BaseModel, Field
from typing import List, Optional

class ScreeningResult(BaseModel):
    qualified: bool = Field(description="Set to True if the candidate has ANY software, coding, AI, ML, data, or technical knowledge. Set to False ONLY if the resume has absolutely zero relevance to technology/software.")
    reason: str = Field(description="Detailed explanation for the qualification or disqualification decision.")
    match_score: int = Field(description="Score between 0 and 100 representing how well the candidate's resume matches the target job description.")
    matched_skills: List[str] = Field(description="List of core technical skills present in the resume that match the job requirements.")
    missing_skills: List[str] = Field(description="List of technical skills/requirements mentioned in the job description that are missing from the resume.")
    red_flags: List[str] = Field(description="List of concerns or red flags (e.g. short job duration, lack of core experience, gaps) identified from the resume.")

class MCQItem(BaseModel):
    question: str = Field(description="The technical question based on the candidate's skills and the applied role.")
    options: List[str] = Field(description="A list of 4 options for the question.")
    correct_option: str = Field(description="The exact text of the correct option matching one option in the options list.")

class MCQList(BaseModel):
    questions: List[MCQItem] = Field(description="A collection of multiple choice questions.")

class InterviewResponse(BaseModel):
    response: str = Field(description="Your conversational response or follow-up question to the candidate.")
    should_conclude: bool = Field(description="Set to True if you have gathered enough information to make a final decision, False to continue the interview.")

class FinalEvaluation(BaseModel):
    selected: bool = Field(description="True if the candidate passes the interactive interview, False otherwise.")
    overall_feedback: str = Field(description="Detailed technical and behavioral assessment feedback for the hiring team.")
    summary_for_candidate: str = Field(description="Constructive feedback summarizing the candidate's performance.")

class SupportDiagnosis(BaseModel):
    diagnosis: str = Field(description="A concise summary/analysis of the issue the candidate is facing, and the root cause.")
    severity: str = Field(description="Severity of the issue. Must be one of: 'Low', 'Medium', 'High'.")
    suggested_action: str = Field(description="Action the recruiter should take (e.g. 'Reset MCQ test access', 'Contact candidate', 'No action needed').")
    is_genuine_technical_issue: bool = Field(description="Set to True if the candidate describes a genuine system, network, interface, or transcription technical disruption. Set to False for vague, spam, or score improvement requests.")
    auto_resolve_eligible: bool = Field(description="Set to True ONLY if this is a genuine technical issue AND resetting candidate access is a safe, recommended remedy. Set to False if manual recruiter human review is preferred.")
    confidence_score: float = Field(description="Confidence rating of this decision between 0.0 and 1.0.")
    justification: str = Field(description="Detailed explanation justifying why this ticket is eligible or ineligible for auto-resolution based on guardrails.")
    candidate_notification: str = Field(description="A friendly, dynamic response message addressed directly to the candidate explaining the resolution outcome (e.g. 'Hello Kiran, we detected your MCQ was interrupted due to a browser crash, so we have automatically reset your access. You can now register and retake the test immediately!' or 'Hello Kiran, your request has been routed to our recruitment team for manual review as we need a bit more detail to verify the issue.')")

class ClarificationResult(BaseModel):
    is_clarification_request: bool = Field(description="Set to True if the candidate is asking to repeat the question, clarify a term, or explain the question again. Set to False if the candidate is answering the question normally.")
    clarified_response: str = Field(description="The repeated question or clarified explanation formulated in a friendly, conversational manner, addressing their request directly.")

class JobAction(BaseModel):
    action: str = Field(description="The action to take: 'add' (if the recruiter wants to add a new job opening), 'update' (if they want to update or modify an existing job), 'delete' (if they want to delete/remove a job), or 'none' (if the query is conversational/unrelated or they ask a general question).")
    job_title: str = Field(description="The exact title of the job role (e.g. 'Machine Learning Engineer', 'DevOps Engineer'). For update/delete, it must match an existing job title.")
    job_description: str = Field("", description="The detailed, professional markdown job description. For 'add', this must be generated based on the recruiter's brief description or notes. For 'update', it must be the updated complete job description containing the requested changes.")
    difficulty: str = Field("Medium", description="The target difficulty level for candidate evaluation: 'Very Easy', 'Easy', 'Medium', or 'Hard'.")
    explanation: str = Field(description="A polite, direct message explaining what the agent did (or why it couldn't do it) and summarizing the final state of the job role.")
