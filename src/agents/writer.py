import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import PipelineState
from src.config import SMART_MODEL, get_text_content
from src.tracker import pipeline_tracker

WRITER_SYSTEM_PROMPT = """You are an elite ghostwriter for top tech founders  
  and executive creators.                                                         
    Your LinkedIn posts generate massive engagement, shares, and high-value       
  conversations.                                                                  
                                                                                  
    Follow these strict writing rules:                                            
    1. Hook: The first 1-2 lines MUST compel the reader to click 'see more'. No   
  boring greetings.                                                               
    2. White space: Use short paragraphs (1-2 sentences max). Highly skimmable.   
    3. Concrete value: Use specific frameworks, data points, or counter-intuitive 
  lessons.                                                                        
    4. No generic corporate buzzwords (avoid: 'game-changer', 'delve', 'testament',
  'tapestry', 'synergy').                                                         
    5. Ending: End with a strong punchline and a genuine discussion prompt        
  (question).                                                                     
    """   

def writer_node(state: PipelineState)-> dict:
    """Drafts or revises the LinkedIn post"""
    topic= state["topic"]
    selected_angle= state.get("selected_angle")
    research_summary= state.get("research_summary","")
    current_draft= state.get("current_draft")
    critique= state.get("critique")
    fact_check= state.get("fact_check_report")
    iteration= state.get("iteration",0)+1

    start_time= time.time()
    llm= ChatGoogleGenerativeAI(model= SMART_MODEL, temperature=0.7)

    #initial draft
    if not current_draft:
        user_prompt=f"""Write a compeling LinkedIn post based on this outline:
        Topic:{topic}
        Angle type:{selected_angle.angle_type if selected_angle else 'General'}
        Core Thesis:{selected_angle.core_thesis if selected_angle else topic}
        Hook Idea: {selected_angle.hook_concept if selected_angle else ''}

        Research & Facts to incorporate:
        {research_summary}
        """
    else:
        critique_feedback = "\n".join(f"- {f}" for f in critique.actionable_feedback) if critique else "Polish hook and flow."
        fact_corrections = "\n".join(f"- {c}" for c in fact_check.corrections_needed) if fact_check else "None."
        user_prompt = f"""Revise and improve the following LinkedIn post: 
CURRENT_DRAFT:
{current_draft}

EDITOR FEEDBACK (Address every point):
{critique_feedback}

FACT-CHECK CORRECTIONS NEEDED:
{fact_corrections}

Output ONLY the revised LinkedIn post."""

    messages = [
        SystemMessage(content=WRITER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt)
    ]

    response = llm.invoke(messages)
    draft_content = get_text_content(response.content)

    # record telemetry
    pipeline_tracker.record_call(
        agent_name=f"Writer (Round {iteration})",
        model=SMART_MODEL,
        usage_metadata=getattr(response, "usage_metadata", {}),
        start_time=start_time
    )

    return {
        "current_draft": draft_content,
        "draft_history": [draft_content],  # LangGraph reducer appends this
        "iteration": iteration,
        "status": f"drafted_round_{iteration}"
    }
