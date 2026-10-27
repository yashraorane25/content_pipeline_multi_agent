import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import PipelineState, AngleOptions
from src.config import FAST_MODEL
from src.tracker import pipeline_tracker

IDEATOR_SYSTEM_PROPT="""You are a world-class LinkedIn content strategist  
  and viral ghostwriter.                                                          
    Your job is to take a raw idea or topic and produce 3 DISTINCT angles for a   
  LinkedIn post:                                                                  
                                                                                  
    1. 'Contrarian / Hot Take': Challenges conventional wisdom or common bad      
  advice.                                                                         
    2. 'Actionable Framework': A step-by-step blueprint or checklist leaders can  
  apply today.                                                                    
    3. 'Personal Narrative / Story': A relatable journey of a mistake made and the
  lesson learned.                                                                 
                                                                                  
    Return the result strictly adhering to the AngleOptions schema.               
    """ 

def ideator_node(state: PipelineState)-> dict:
    """Generate 3 distinct LinkedIn angles from the raw topic"""
    topic= state["topic"]
    start_time= time.time()

    #initialize gemini with structured output
    llm= ChatGoogleGenerativeAI(model= FAST_MODEL, temperature= 0.7)
    structured_llm= llm.with_structured_output(AngleOptions, include_raw=True)

    messages=[SystemMessage(content=IDEATOR_SYSTEM_PROPT), HumanMessage(content=f"Generate 3 distinct angles for this topic:\n\n{topic}")]
    resposne= structured_llm.invoke(messages)

    # parse the structured output and the raw message for usage metadata
    parsed_angles: AngleOptions= resposne["parsed"]
    raw_message= resposne["raw"]

    #record telemetry
    pipeline_tracker.record_call(
        agent_name="Ideator",
        model=FAST_MODEL,
        usage_metadata=getattr(raw_message,"usage_metadata",{}),
        start_time=start_time
    )


    #by default select the first angle to develop into a post
    selected= parsed_angles.angles[0] if parsed_angles.angles else None

    return {
        "angles": parsed_angles.angles,
        "selected_angle": selected,
        "status": "ideated"
    }