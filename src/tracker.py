import time
from dataclasses import dataclass,field
from typing import List, Dict, Any
from rich.table import Table
from rich.console import Console
from src.config import PRICING

@dataclass
class StepTelemetry:
    agent_name: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_sec: float
    cost_usd: float

class TelemetryTracker:
    def __init__(self, name: str = 'Pipeline'): 
        self.name= name
        self.steps: List[StepTelemetry]=[]

    def record_call(                                                                                                                                                             
            self,                                                                                                                                                                    
            agent_name: str,                                                                                                                                                         
            model: str,                                                                                                                                                              
            usage_metadata: Dict[str, Any],                                                                                                                                          
            start_time: float                                                                                                                                                        
        ) -> StepTelemetry:                                                                                                                                                          
            """Calculates latency and costs from usage metadata and stores the record."""                                                                                            
            latency = round(time.time() - start_time, 2) 


            #saftely extract tokens from usage_metadata dictionary
            input_tokens= usage_metadata.get("input_tokens",0) if usage_metadata else 0
            output_tokens = usage_metadata.get("output_tokens", 0) if usage_metadata else 0                                                                                          
            total_tokens = usage_metadata.get("total_tokens", input_tokens + output_tokens) 

            pricing = PRICING.get(model, PRICING["default"])
            cost=(
                (input_tokens / 1_000_000) * pricing["input_per_million"] +                                                                                                          
                    (output_tokens / 1_000_000) * pricing["output_per_million"] 
            )

            record = StepTelemetry(                                                                                                                                                  
                        agent_name=agent_name,                                                                                                                                               
                        model=model,                                                                                                                                                         
                        input_tokens=input_tokens,                                                                                                                                           
                        output_tokens=output_tokens,                                                                                                                                         
                        total_tokens=total_tokens,                                                                                                                                           
                        latency_sec=latency,                                                                                                                                                 
                        cost_usd=round(cost, 6)                                                                                                                                              
                    )                                                                                                                                                                        
            self.steps.append(record)                                                                                                                                                
            return record  

    @property
    def total_tokens(self)-> int:
         return sum(s.total_tokens for s in self.steps)

    @property
    def total_latency(self)-> float:
         return round(sum(s.latency_sec for s in self.steps),2)

    @property
    def total_cost(self)-> float:
         return round(sum(s.cost_usd for s in self.steps),6)

    def summary_table(self)-> Table:
        table = Table(title=f"Telemetry Summary: {self.name}", show_header=True, header_style="bold magenta")                                                                    
        table.add_column("Agent / Node", style="cyan")                                                                                                                           
        table.add_column("Model", style="blue")                                                                                                                                  
        table.add_column("In Tokens", justify="right")                                                                                                                           
        table.add_column("Out Tokens", justify="right")                                                                                                                          
        table.add_column("Total Tokens", justify="right", style="bold")                                                                                                          
        table.add_column("Latency (s)", justify="right")                                                                                                                         
        table.add_column("Cost ($)", justify="right", style="green")

        for s in self.steps:
             table.add_row(
                  s.agent_name,
                  s.model,
                  f"{s.input_tokens:,}",                                                                                                                                           
                  f"{s.output_tokens:,}",                                                                                                                                          
                  f"{s.total_tokens:,}",                                                                                                                                           
                  f"{s.latency_sec:.2f}",                                                                                                                                          
                  f"${s.cost_usd:.5f}" 

             )
        table.add_section()
        table.add_row(
              "[bold]TOTAL[/bold]",                                                                                                                                                
                "-",                                                                                                                                                                 
                f"{sum(s.input_tokens for s in self.steps):,}",                                                                                                                      
                f"{sum(s.output_tokens for s in self.steps):,}",                                                                                                                     
                f"[bold]{self.total_tokens:,}[/bold]",                                                                                                                               
                f"{self.total_latency:.2f}s",                                                                                                                                        
                f"[bold green]${self.total_cost:.5f}[/bold green]"   
        )
        return table
#gloabal instance for pipeline tracker
pipeline_tracker= TelemetryTracker("Multi-Agent Content Pipeline")
