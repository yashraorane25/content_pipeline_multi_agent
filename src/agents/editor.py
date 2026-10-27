import time                                                                   
from langchain_google_genai import ChatGoogleGenerativeAI                     
from langchain_core.messages import SystemMessage, HumanMessage               
from src.state import PipelineState, EditorCritique                           
from src.config import SMART_MODEL, TARGET_QUALITY_SCORE                      
from src.tracker import pipeline_tracker  

EDITOR_SYSTEM_PROMPT = """You are a demanding, elite LinkedIn Editor-in-Chief.
    You hold content to the highest standards. Grade the draft honestly on a 1-10 
  scale across:                                                                   
                                                                                  
    1. Hook Score (1-10): Will this stop a busy executive mid-scroll?             
    2. Value Score (1-10): Is there real insight here, or is it obvious fluff?    
    3. Formatting Score (1-10): Short paragraphs, no walls of text, clean rhythm? 
                                                                                  
    Decision Rules:                                                               
    - Calculate overall_score = (hook_score + value_score + formatting_score) / 3.
  0                                                                               
    - Set ready_to_publish = True ONLY IF:                                        
        a) overall_score >= 8.5 AND                                               
        b) fact_check has NO hallucinations.                                      
    - If not ready to publish, provide 2-3 blunt, highly actionable bullet points 
  for how the writer can improve it.                                              
                                                                                  
    Return the result strictly adhering to the EditorCritique schema.             
    """

def editor_node(state: PipelineState)-> dict:
    """Evaluates the draft and produces a rubric score with revision instructions"""
    current_draft= state["current_draft"]
    selected_angle= state.get("selected_angle")
    fact_check= state.get("fact_check_report")

    start_time= time.time()
    llm= ChatGoogleGenerativeAI(model= SMART_MODEL, temperature=0.2)
    structured_llm= llm.with_structured_output(EditorCritique, include_raw=True)

    fact_status= "PASSED" if (fact_check and not fact_check.has_hallucinations) else "FAILED (Hallucinations detected)"

    messages=[
        SystemMessage(content=EDITOR_SYSTEM_PROMPT),
        HumanMessage(content=f"TARGET ANGLE: {selected_angle.angle_type if selected_angle else 'General'}\n"                                               
                        f"FACT-CHECK AUDIT: {fact_status}\n\n"                    
                        f"DRAFT TO EVALUATE:\n{current_draft}" )
    ]

    response= structured_llm.invoke(messages)
    critique: EditorCritique= response["parsed"]
    raw_message= response["raw"]

    pipeline_tracker.record_call(
        agent_name="Editor",                                                  
        model=SMART_MODEL,                                                    
        usage_metadata=getattr(raw_message, "usage_metadata", {}),            
        start_time=start_time  
    )

    return {                                                                  
            "critique": critique,                                                 
            "critique_history": [critique],  # LangGraph reducer appends this     
            "status": "critiqued"                                                 
    }
                                                                          


