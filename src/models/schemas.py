from pydantic import BaseModel, Field
from typing import List

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
