import ollama

def evaluate(prompt: str):
    client = ollama.Client(host="http://localhost:11434")

    response = client.generate(
        model="mistral",   # replace with exact output from `ollama list`
        prompt=prompt,
        options={
            "num_gpu": 0,      # ← force CPU
            "num_ctx": 2048,   # ← max context for Mistral
            "num_thread": 4
        }
    
    )

    return response["response"]

