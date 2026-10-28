import time
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import PipelineState
from src.config import FAST_MODEL, get_text_content
from src.tracker import pipeline_tracker


RESEARCHER_SYSTEM_PROMPT = """You are an elite research analyst for executive 
  thought leaders.                                                                
    Your job is to synthesize raw search results into high-signal research notes: 
    - Extract 2-3 specific statistics, percentages, or research data points.      
    - Identify real company examples or concrete case studies.                    
    - Avoid vague platitudes; focus on concrete evidence and hard facts.          
    - List the sources used.                                                      
    """

def search_web(query: str, max_results: int=2)-> list[dict]:
    """saftley queries DuckDuckGo will fallback if rate limited"""
    try:
        ddgs = DDGS(timeout=3)
        results= list(ddgs.text(query, max_results=max_results))
        return results
    except Exception as e:
        print(f"[Warning] Web search failed: {e}. Falling back to internal knowledge.")
        return[]

def researcher_node(state: PipelineState)-> dict:
    """Gathers real-world data and statistics for the chosen post angle"""
    topic= state["topic"]
    selected_angle= state.get("selected_angle")
    angle_title=selected_angle.hook_concept if selected_angle else topic
    start_time= time.time()

    #search the web for stats and insights
    search_query= f"{topic} {angle_title} statistics insights industry trends"
    raw_results= search_web(search_query, max_results=4)
    sources = [r.get("href", "") for r in raw_results if "href" in r]
    search_context= "\n\n".join([f"Title: {r.get('title')}\nSnippet: {r.get('body')}\nURL: {r.        
    get('href')}" for r in raw_results] )

    #2. Synthesize using Gemini
    #llm= ChatGoogleGenerativeAI(model= FAST_MODEL, temperature= 0.3)
    llm= ChatGoogleGenerativeAI(model= FAST_MODEL)
    messages = [                                                              
            SystemMessage(content=RESEARCHER_SYSTEM_PROMPT),                      
            HumanMessage(                                                         
                content=f"Topic: {topic}\n"                                       
                        f"Angle: {angle_title}\n\n"                               
                        f"Search Results:\n{search_context if search_context else 
            'No external search results found. Synthesize key industry facts and benchmarks from memory.'}"                                                                 
            )                                                                     
        ]

    response= llm.invoke(messages)

    #record telemetry
    pipeline_tracker.record_call(
        agent_name='Researcher',
        model=FAST_MODEL,
        usage_metadata=getattr(response,'usage_metadata',{}),
        start_time=start_time
    )

    return {
            "research_summary": get_text_content(response.content),                                 
            "sources": sources,                                                   
            "status": "researched"
    }