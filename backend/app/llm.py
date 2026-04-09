# import requests
# from langchain_core.runnables import RunnableLambda

# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "mistral:latest"

# def local_llm(prompt: str) -> str:
#     payload = {
#         "model": MODEL_NAME,
#         "prompt": prompt,
#         "stream": False,
#         "options": {
#             "temperature": 0.2,
#             "num_predict": 128
#         }
#     }

#     response = requests.post(OLLAMA_URL, json=payload)
#     response.raise_for_status()

#     return response.json()["response"]

# llm = RunnableLambda(local_llm)
# try:
#     print(
#         llm.invoke("Translate English to French: Hello, how are you?")
#     )
# except Exception as e:
#     print("Error invoking local LLM:", e)


import os
from dotenv import load_dotenv
from google import genai
from langchain_core.runnables import RunnableLambda
import json

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-3-flash-preview"


def gemini_llm(prompt: str) -> str:
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )
    return response.text


llm = RunnableLambda(gemini_llm)

try:
    print(
        llm.invoke("Translate English to French: Hello, how are you?")
    )
except Exception as e:
    print("Error invoking Gemini LLM:", e)