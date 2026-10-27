import operator
from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

class PostAngle(BaseModel):
    angle_type: str= Field(description="Type of angle: e.g. 'Contrarian / Hot Take', 'Actionable Framework', or 'Personal Story / Narrative'")
    hook_concept: str= Field(description="The primary hook idea for the opening lines")
    target_audience: str= Field(description="Who will benefit most from this post")
    core_thesis: str= Field(description="The 1-2 sentence core insight")


class AngleOptions(BaseModel):
    angles: List[PostAngle] = Field(description="List of 3 distinct LinkedIn post angles")

class ClaimVerification(BaseModel):
    claim: str= Field(description="The factual claim extracted from the draft")
    status: str= Field(description="One of : 'VERIFIED','UNVERIFIED','CONTRADICTED'")
    notes: str= Field(description='Evidence or reasoning behind the status')

class FactCheckReport(BaseModel):
    claims: List[ClaimVerification] = Field(description="All extracted factual claims and their statuses")                                                                       
    has_hallucinations: bool = Field(description="True if any claim is CONTRADICTED or egregiously inaccurate")                                                                  
    corrections_needed: List[str] = Field(default_factory=list, description="Specific corrections the writer must make")

class EditorCritique(BaseModel):
    hook_score: int = Field(ge=1, le=10, description="Hook strength (1-10): Does it stop the scroll?")                                                                           
    value_score: int = Field(ge=1, le=10, description="Actionable depth (1-10): Is it high signal, low fluff?")                                                                  
    formatting_score: int = Field(ge=1, le=10, description="Readability (1-10): Line breaks, skim-friendliness")                                                                 
    overall_score: float = Field(ge=1.0, le=10.0, description="Average overall score (1.0 to 10.0)")                                                                             
                                                                                                                                                                                     
        # Stopping condition flag                                                                                                                                                    
    ready_to_publish: bool = Field(                                                                                                                                              
        description="True if overall_score >= 8.5 AND no fact-check failures; False otherwise"                                                                                   
    )                                                                                                                                                                            
                                                                                                                                                                                     
    actionable_feedback: List[str] = Field(                                                                                                                                      
            description="Specific instructions for the writer on what to improve in the next revision"                                                                               
    ) 

class PipelineState(TypedDict):
    topic: str
    angles: List[PostAngle]
    selected_angle: Optional[PostAngle]

    research_summary: str
    sources: List[str]

    current_draft: str

    draft_history: Annotated[List[str], operator.add]

    fact_check_report: Optional[FactCheckReport]
    critique: Optional[EditorCritique]
    critique_history: Annotated[List[EditorCritique], operator.add]

    iteration: int
    max_iterations: int
    final_post: str
    status: str
