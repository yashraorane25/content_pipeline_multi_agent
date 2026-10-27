import random
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.config import SMART_MODEL
from src.tracker import TelemetryTracker


console= Console()

class PostScore(BaseModel):                                                                                                                                                        
        hook_score: float = Field(ge=1, le=10, description="Hook stop-the-scroll power (1-10)")                                                                                        
        depth_score: float = Field(ge=1, le=10, description="Depth of insights, data, and substance (1-10)")                                                                           
        readability_score: float = Field(ge=1, le=10, description="Visual rhythm, whitespace, and formatting (1-10)")                                                                  
        total_score: float = Field(ge=1, le=10, description="Overall post quality (1-10)") 

class BindEvaluation(BaseModel):
        score_a: PostScore = Field(description="Scores for Draft A")                                                                                                                   
        score_b: PostScore = Field(description="Scores for Draft B")                                                                                                                   
        winner: str = Field(description="Must be exactly 'Draft A', 'Draft B', or 'Tie'")                                                                                              
        detailed_critique: str = Field(description="Objective comparative analysis explaining the winner")

JUDGE_SYSTEM_PROMPT=  """You are an impartial, highly discerning judge of executive thought leadership.                                                                            
    You are evaluating two anonymized LinkedIn posts on the same topic: 'Draft A' and 'Draft B'.                                                                                       
                                                                                                                                                                                       
    Grade each draft rigorously on:                                                                                                                                                    
    1. Hook Strength (1-10): First 2 lines. Does it create intense curiosity without clickbait?                                                                                        
    2. Depth of Substance (1-10): Does it provide specific data, frameworks, or counter-intuitive value vs. generic platitudes?                                                        
    3. Formatting & Rhythm (1-10): Line spacing, punchiness, skimmability.                                                                                                             
                                                                                                                                                                                       
    Identify the clear winner based on overall quality. Return your evaluation adhering to the BlindEvaluation schema.                                                                 
    """ 

def evaluate_posts(multi_agent_post:str, baseline_posts:str)-> dict:
        "Conducts a blink randomized evaluation between Multi-Agent and Baseline posts."
        #Randomize order to remove position bias (A vs B)
        multi_is_a= random.choice([True, False])
        draft_a = multi_agent_post if multi_is_a else baseline_posts
        draft_b= baseline_posts if multi_is_a else multi_agent_post
        llm = ChatGoogleGenerativeAI(model= SMART_MODEL, temperature=0.1)
        structured_llm= llm .with_structured_output(BindEvaluation)

        messages=[
                SystemMessage(content=JUDGE_SYSTEM_PROMPT),
                HumanMessage(
                        content=f"--- DRAFT A ---\n{draft_a}\n\n"   
                        f"--- DRAFT B ---\n{draft_b}"
                )
        ]

        evaluation: BindEvaluation= structured_llm.invoke(messages)

        if multi_is_a:                                                                                                                                                                 
            multi_score = evaluation.score_a                                                                                                                                           
            baseline_score = evaluation.score_b                                                                                                                                        
            winner_name = "Multi-Agent Pipeline" if evaluation.winner == "Draft A" else ("Baseline" if evaluation.winner == "Draft B" else "Tie")                                      
        else:                                                                                                                                                                          
            multi_score = evaluation.score_b                                                                                                                                           
            baseline_score = evaluation.score_a                                                                                                                                        
            winner_name = "Multi-Agent Pipeline" if evaluation.winner == "Draft B" else ("Baseline" if evaluation.winner == "Draft A" else "Tie")                                      
                                                                                                                                                                                       
        return {                                                                                                                                                                       
            "multi_score": multi_score,                                                                                                                                                
            "baseline_score": baseline_score,                                                                                                                                          
            "winner": winner_name,                                                                                                                                                     
            "critique": evaluation.detailed_critique                                                                                                                                   
        }
def print_comparison_report(
                topic:str,
                multi_post:str,
                baseline_post: str,
                multi_tracker: TelemetryTracker,                    
                base_tracker: TelemetryTracker,                     
                eval_result: dict
):
    """Prints a beautiful comparison report comparing latency, cost, and quality."""   
    console.print("\n" + "="*80, style="bold cyan")                                                                                                                                
    console.print(f"BENCHMARK REPORT: Multi-Agent Pipeline vs. Single-Prompt Baseline", style="bold yellow", justify="center")                                                     
    console.print(f"Topic: [italic]{topic}[/italic]", justify="center")                                                                                                            
    console.print("="*80 + "\n", style="bold cyan") 

    # 1. Metric Comparison Table                                                                                                                                                   
    table = Table(title="Head-to-Head Performance & Cost Matrix", show_header=True, header_style="bold green")                                                                     
    table.add_column("Metric", style="bold")                                                                                                                                       
    table.add_column("Single-Prompt Baseline", justify="right", style="dim")                                                                                                       
    table.add_column("Multi-Agent Pipeline", justify="right", style="cyan")                                                                                                        
    table.add_column("Delta / Difference", justify="right", style="bold") 

    # Tokens                                                                                                                                                                       
    token_delta = multi_tracker.total_tokens - base_tracker.total_tokens                                                                                                           
    token_ratio = round(multi_tracker.total_tokens / max(base_tracker.total_tokens, 1), 1)                                                                                         
    table.add_row(                                                                                                                                                                 
        "Total Tokens",                                                                                                                                                            
        f"{base_tracker.total_tokens:,}",                                                                                                                                          
        f"{multi_tracker.total_tokens:,}",                                                                                                                                         
        f"+{token_delta:,} ({token_ratio}x)"                                                                                                                                       
    )

    # Latency                                                                                                                                                                      
    latency_delta = round(multi_tracker.total_latency - base_tracker.total_latency, 2)                                                                                             
    latency_ratio = round(multi_tracker.total_latency / max(base_tracker.total_latency, 0.1), 1)                                                                                   
    table.add_row(                                                                                                                                                                 
        "Total Latency",                                                                                                                                                           
        f"{base_tracker.total_latency:.2f}s",                                                                                                                                      
        f"{multi_tracker.total_latency:.2f}s",                                                                                                                                     
        f"+{latency_delta:.2f}s ({latency_ratio}x)"                                                                                                                                
    )                                                                                                                                                                              
                                                                                                                                                                                   
    # Dollar Cost                                                                                                                                                                  
    cost_delta = round(multi_tracker.total_cost - base_tracker.total_cost, 6)                                                                                                      
    table.add_row(                                                                                                                                                                 
        "Total Cost ($)",                                                                                                                                                          
        f"${base_tracker.total_cost:.5f}",                                                                                                                                         
        f"${multi_tracker.total_cost:.5f}",                                                                                                                                        
        f"+${cost_delta:.5f}"                                                                                                                                                      
    )                                                                                                                                                                              
                                                                                                                                                                                   
    # Judge Scores                                                                                                                                                                 
    m_score = eval_result["multi_score"]                                                                                                                                           
    b_score = eval_result["baseline_score"]                                                                                                                                        
    score_delta = round(m_score.total_score - b_score.total_score, 1)                                                                                                              
                                                                                                                                                                                   
    table.add_row(                                                                                                                                                                 
        "Judge Quality Score",                                                                                                                                                     
        f"{b_score.total_score:.1f} / 10",                                                                                                                                         
        f"{m_score.total_score:.1f} / 10",                                                                                                                                         
        f"{'+' if score_delta >= 0 else ''}{score_delta:.1f} pts"                                                                                                                  
    )                                                                                                                                                                              
                                                                                                                                                                                   
    console.print(table)  
     # 2. Winner Panel                                                                                                                                                              
    winner_style = "bold green" if eval_result["winner"] == "Multi-Agent Pipeline" else "bold red"                                                                                 
    console.print(Panel(                                                                                                                                                           
        f"[bold]Winner:[/bold] [{winner_style}]{eval_result['winner']}[/{winner_style}]\n\n"                                                                                       
        f"[bold]Judge Analysis:[/bold]\n{eval_result['critique']}",                                                                                                                
        title="Blind LLM-as-a-Judge Verdict",                                                                                                                                      
        border_style="yellow"                                                                                                                                                      
    ))
