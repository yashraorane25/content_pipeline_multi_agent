from langgraph.graph import StateGraph ,END
from src.state import PipelineState
from src.config import MAX_REVISION_ROUNDS
from src.agents.ideator import ideator_node
from src.agents.researcher import researcher_node
from src.agents.writer import writer_node
from src.agents.fact_checker import fact_checker_node
from src.agents.editor import editor_node

def should_continue(state: PipelineState)-> str:
    """Evaluates whether to cycle back for another revision round or finalize output"""
    iteration = state.get("iteration",0)
    max_rounds= state.get("max_iterations", MAX_REVISION_ROUNDS)
    critique= state.get("critique")

    #condition 1: passed qualifying rubric
    if critique and critique.ready_to_publish:
        print(f"\n[Stopping Condition Met] Critique score: {critique.overall_score}/10 -> Ready to publish!")
        return "finalize"

    #condiiton2: max iteration limit reached
    if iteration >= max_rounds:
         print(f"\n[Stopping Condition Met] Reached maximum allowed revision rounds ({max_rounds}). Stopping.") 
         return "finalize"

    #condition3: needs revision
    print(f"\n[Feedback Loop] Iteration {iteration}/{max_rounds} scored {critique.overall_score if  critique else 'N/A'}/10. Routing back to Writer with feedback...") 
    return "revise"

def finalize_node(state: PipelineState) -> dict:
    """Final node that sets the final post output"""
    return {
        "final_post": state.get("current_draft", ""),
        "status": "completed"
    }

def build_graph():
    "Builds and compiles the multi-agent content pipeline graph"
    workflow= StateGraph(PipelineState)

    # add all agent nodes
    workflow.add_node("ideator", ideator_node)
    workflow.add_node("researcher", researcher_node)           
    workflow.add_node("writer", writer_node)                   
    workflow.add_node("fact_checker", fact_checker_node)       
    workflow.add_node("editor", editor_node)                   
    workflow.add_node("finalize", finalize_node)

    #add linear edges
    workflow.set_entry_point("ideator")                        
    workflow.add_edge("ideator", "researcher")                 
    workflow.add_edge("researcher", "writer")                  
    workflow.add_edge("writer", "fact_checker")                
    workflow.add_edge("fact_checker", "editor")

    #add cyclic conditional edge
    workflow.add_conditional_edges("editor", should_continue,{
       "revise": "writer",    
        "finalize": "finalize"  
    })

    workflow.add_edge("finalize",END)
    return workflow.compile()

app= build_graph()

     