import os
from dotenv import load_dotenv

load_dotenv()

# FAST_MODEL= os.getenv("FAST_MODEL", "gemini-3.5-flash")
# SMART_MODEL= os.getenv("SMART_MODEL", "gemini-3.5-flash")
FAST_MODEL = os.getenv("FAST_MODEL", "gemini-3.5-flash-lite")                                                                                                                                                                       
SMART_MODEL = os.getenv("SMART_MODEL", "gemini-3.5-flash")

# MAX_REVISION_ROUNDS= 3
# TARGET_QUALITY_SCORE= 8.5
MAX_REVISION_ROUNDS = 2                                                                                                                                                                                                             
TARGET_QUALITY_SCORE = 8.0

PRICING = {                                                                                                                                                                      
        "gemini-3.5-flash": {                                                                                                                                                        
            "input_per_million": 0.075,   # $0.075 / 1M input tokens                                                                                                                 
            "output_per_million": 0.30,   # $0.30 / 1M output tokens                                                                                                                 
        },                                                                                                                                                                           
        "gemini-3.5-pro": {                                                                                                                                                          
            "input_per_million": 1.25,    # $1.25 / 1M input tokens                                                                                                                  
            "output_per_million": 5.00,   # $5.00 / 1M output tokens                                                                                                                 
        },                                                                                                                                                                           
        # Fallback default                                                                                                                                                           
        "default": {                                                                                                                                                                 
            "input_per_million": 0.10,                                                                                                                                               
            "output_per_million": 0.40,                                                                                                                                              
        }                                                                                                                                                                            
}

def get_text_content(content) -> str:
    """Safely extracts clean string text from AIMessage.content (str or list)."""
    if isinstance(content, str):
        return content.strip()
    elif isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif hasattr(item, "text"):
                parts.append(getattr(item, "text", ""))
            else:
                parts.append(str(item))
        return "".join(parts).strip()
    return str(content).strip()
