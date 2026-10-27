import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import SMART_MODEL, get_text_content
from src.tracker import TelemetryTracker

BASELINE_SYSTEM_PROMPT= """You are an elite LinkedIn content  
  creator and ghostwriter for tech executives.                     
    Write a top-tier LinkedIn post on the requested topic.         
                                                                   
    Guidelines:                                                    
    - Start with a scroll-stopping 1-2 line hook (no greetings).   
    - Use clean formatting with 1-2 sentence paragraphs and ample  
  whitespace.                                                      
    - Include concrete, actionable insights, real-world examples,  
  or frameworks.                                                   
    - Avoid corporate cliches and buzzwords.                       
    - Conclude with a strong punchline and a thought-provoking     
  question for the comments.                                       
    """

def run_baseline(topic: str)->dict:
    """Executes a single prompt generation for the same topic and tracks latency, token usage and cost"""
    tracker= TelemetryTracker("Single-Prompt Baseline")
    start_time= time.time()
    llm= ChatGoogleGenerativeAI(model= SMART_MODEL, temperature= 0.7)
    messages=[
        SystemMessage(content=BASELINE_SYSTEM_PROMPT),
        HumanMessage(content=f"Write an insightful LinkedIn post about :\n\n{topic}")
    ]

    response= llm.invoke(messages)
    content= get_text_content(response.content)

    tracker.record_call(
        agent_name="SinglePromptBaseline",                     
            model=SMART_MODEL,                                     
            usage_metadata=getattr(response, "usage_metadata", {}),
            start_time=start_time   
    )

    return{
        "post": content,
        "tracker": tracker
    }