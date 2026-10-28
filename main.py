import sys                                                                                                                                                                         
from rich.console import Console                                                                                                                                                   
from rich.panel import Panel                                                                                                                                                       
from rich.markdown import Markdown                                                                                                                                                 
                                                                                                                                                                                   
from src.graph import app                                                                                                                                                          
from src.tracker import pipeline_tracker                                                                                                                                           
from src.baseline import run_baseline                                                                                                                                              
from src.evaluate import evaluate_posts, print_comparison_report
from concurrent.futures import ThreadPoolExecutor

console=Console()

def run_pipeline(topic:str):
    console.print(f"\n[bold green]🚀 STARTING MULTI-AGENT CONTENT PIPELINE[/bold green]")                                                                                          
    console.print(f"Topic: [italic cyan]{topic}[/italic cyan]\n")

    initial_state = {                                                                                                                                                              
            "topic": topic,                                                                                                                                                            
            "max_iterations": 3,                                                                                                                                                       
            "draft_history": [],                                                                                                                                                       
            "critique_history": [],                                                                                                                                                    
    }

    #1 kick off the Baseline in the backgroud thread immediately
    with ThreadPoolExecutor(max_workers=1) as executor:
        baseline_future= executor.submit(run_baseline,topic)
        # Stream graph execution so we see every node as it completes
        final_state = None
        latest_draft = ""
        for event in app.stream(initial_state, stream_mode="updates"):
            for node_name, node_output in event.items():
                if node_name == 'ideator':
                    angles = node_output.get("angles", [])
                    selected = node_output.get("selected_angle")
                    console.print(Panel(
                        "\n".join([f"• [{a.angle_type}]: {a.hook_concept}" for a in angles]) +
                        f"\n\n[bold yellow]Selected Angle:[/bold yellow] {selected.angle_type if selected else 'Default'}",
                        title="💡 [bold cyan]Ideator Generated Angles[/bold cyan]",
                        border_style="cyan"
                    ))

                elif node_name == 'researcher':
                    sources = node_output.get("sources", [])
                    console.print(Panel(
                        f"{node_output.get('research_summary', '')[:400]}...\n\n"
                        f"[dim]Sources: {len(sources)} verified web sources found[/dim]",
                        title="🔍 [bold blue]Researcher Findings[/bold blue]",
                        border_style="blue"
                    ))

                elif node_name == 'writer':
                    latest_draft = node_output.get("current_draft", "")
                    console.print(Panel(
                        latest_draft,
                        title=f"✍️ [bold magenta]Writer Draft (Round {node_output.get('iteration', 1)})[/bold magenta]",
                        border_style="magenta"
                    ))

                elif node_name == 'fact_checker':
                    report = node_output.get("fact_check_report")
                    status_color = "red" if report.has_hallucinations else "green"
                    claims_summary = "\n".join([f"• [{c.status}] {c.claim[:80]}..." for c in report.claims[:3]])
                    console.print(Panel(
                        f"[bold {status_color}]Hallucinations: {report.has_hallucinations}[/bold {status_color}]\n\n{claims_summary}",
                        title="🛡️ [bold yellow]Fact-Checker Audit[/bold yellow]",
                        border_style="yellow"
                    ))

                elif node_name == "editor":
                    critique = node_output.get("critique")
                    status_style = "bold green" if critique.ready_to_publish else "bold yellow"
                    console.print(Panel(
                        f"Overall Score: [bold]{critique.overall_score}/10[/bold]\n"
                        f"• Hook: {critique.hook_score}/10 | Value: {critique.value_score}/10 | Formatting: {critique.formatting_score}/10\n"
                        f"Status: [{status_style}]{'READY TO PUBLISH' if critique.ready_to_publish else 'NEEDS REVISION'}[/{status_style}]\n\n"
                        f"[bold]Feedback for next round:[/bold]\n" + "\n".join([f"- {f}" for f in critique.actionable_feedback]),
                        title="📝 [bold red]Editor Critique[/bold red]",
                        border_style="red"
                    ))

                elif node_name == 'finalize':
                    final_state = node_output

        multi_post = (final_state or {}).get("final_post") or latest_draft 

        #print multi-agent telemtry table
        console.print(pipeline_tracker.summary_table()) 

        # # 2. Run the Single-Prompt Baseline                                                                                                                                            
        # console.print("\n[bold yellow]⚡ RUNNING SINGLE-PROMPT BASELINE...[/bold yellow]")                                                                                             
        # baseline_result = run_baseline(topic)                                                                                                                                          
        # base_post = baseline_result["post"]                                                                                                                                            
        # base_tracker = baseline_result["tracker"]
        baseline_result = baseline_future.result()                                                                                                                               
        base_post = baseline_result["post"]                                                                                                                                      
        base_tracker = baseline_result["tracker"]                                                                                                                                     
                                                                                                                                                                                   
    # 3. Print baseline telemetry table                                                                                                                                            
    #console.print(base_tracker.summary_table()) 
        console.print("\n[bold yellow]⚡ SINGLE-PROMPT BASELINE (Ran concurrently in background):[/bold yellow]")                                                                
        console.print(base_tracker.summary_table()) 

    # 4. Run the Blind LLM-as-a-Judge Evaluation                                                                                                                                   
    console.print("\n[bold magenta]⚖️ CONDUCTING BLIND LLM-AS-A-JUDGE EVALUATION...[/bold magenta]")                                                                               
    eval_result = evaluate_posts(multi_post, base_post)                                                                                                                            
                                                                                                                                                                                   
    # 5. Display the final benchmark report                                                                                                                                        
    print_comparison_report(                                                                                                                                                       
        topic=topic,                                                                                                                                                               
        multi_post=multi_post,                                                                                                                                                     
        baseline_post=base_post,                                                                                                                                                   
        multi_tracker=pipeline_tracker,                                                                                                                                            
        base_tracker=base_tracker,                                                                                                                                                 
        eval_result=eval_result                                                                                                                                                    
    )                                                                                                                                                                              
                                                                                                                                                                                   
    # 6. Display Both Final Posts Side-by-Side                                                                                                                                     
    console.print("\n" + "="*80, style="bold cyan")                                                                                                                                
    console.print("FINAL OUTPUTS PREVIEW", style="bold green", justify="center")                                                                                                   
    console.print("="*80 + "\n", style="bold cyan")                                                                                                                                
                                                                                                                                                                                   
    console.print(Panel(multi_post, title="🏆 Multi-Agent Pipeline Output", border_style="green"))                                                                                 
    console.print(Panel(base_post, title="⚡ Single-Prompt Baseline Output", border_style="dim")) 

if __name__=="__main__":
    if len(sys.argv) > 1:                                                                                                                                                          
        topic_input = " ".join(sys.argv[1:])                                                                                                                                       
    else:                                                                                                                                                                          
        topic_input = console.input("[bold yellow]Enter a topic or idea for LinkedIn posts: [/bold yellow]")                                                                       
                                                                                                                                                                                       
    if not topic_input.strip():                                                                                                                                                    
        topic_input = "Why 90% of AI agent startups will fail because they ignore orchestration and evaluation."                                                                   
                                                                                                                                                                                       
    run_pipeline(topic_input)












