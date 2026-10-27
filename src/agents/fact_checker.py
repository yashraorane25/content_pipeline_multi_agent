import time
from langchain_google_genai import ChatGoogleGenerativeAI                     
from langchain_core.messages import SystemMessage, HumanMessage               
from src.state import PipelineState, FactCheckReport                          
from src.config import FAST_MODEL                                             
from src.tracker import pipeline_tracker   

FACT_CHECKER_SYSTEM_PROMPT = """You are a rigorous, skeptical fact-checker for
  executive thought leadership.                                                   
    Your task is to examine the LinkedIn draft against the provided Research      
  Notes:                                                                          
                                                                                  
    1. Extract all specific claims, statistics, percentages, and factual          
  assertions made in the draft.                                                   
    2. For each claim, determine status:                                          
       - 'VERIFIED': Supported by the research notes or undisputed common domain  
  knowledge.                                                                      
       - 'UNVERIFIED': Plausible but not mentioned in the research notes.         
       - 'CONTRADICTED': Directly contradicts research notes or makes up fake     
  numbers.                                                                        
    3. If any claim is CONTRADICTED or wildly unsubstantiated, set                
  has_hallucinations = True.                                                      
    4. Provide clear, direct corrections for the writer to fix in                 
  corrections_needed.                                                             
                                                                                  
    Return the result strictly adhering to the FactCheckReport schema.            
    """  

def fact_checker_node(state: PipelineState)-> dict:
    """Verifies all factual assertions and stats in the draft"""
    current_draft= state["current_draft"]
    research_summary= state.get("research_summary","")

    start_time= time.time()
    llm= ChatGoogleGenerativeAI(model=FAST_MODEL, temperature= 0.1)
    structured_llm= llm.with_structured_output(FactCheckReport, include_raw=True)

    messages=[SystemMessage(content=FACT_CHECKER_SYSTEM_PROMPT),
              HumanMessage(
                  content=f"RESEARCH NOTES:\n{research_summary}\n\n"
                  f"DRAFT TO AUDIT: \n{current_draft}"
              )]

    resposne= structured_llm.invoke(messages)
    report: FactCheckReport= resposne["parsed"]
    raw_message= resposne["raw"]

    pipeline_tracker.record_call(                                             
            agent_name="FactChecker",                                             
            model=FAST_MODEL,                                                     
            usage_metadata=getattr(raw_message, "usage_metadata", {}),            
            start_time=start_time                                                 
    ) 

    return{
          "fact_check_report": report,                                          
            "status": "fact_checked"                                               
        } 
    

