import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm= ChatGoogleGenerativeAI(model='gemini-3.5-flash', temperature=0.7)
prompt= 'Give a 1-sentence tip on writing great LinkedIn hooks'
response= llm.invoke(prompt)
print('\n Usage metadata (Tokens): ', response.usage_metadata)