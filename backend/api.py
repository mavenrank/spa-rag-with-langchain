from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.agent import create_pagila_agent

import traceback
import time
import requests
import os
import openai
from typing import Optional

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. In production, specify ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    model: Optional[str] = "mistralai/mistral-7b-instruct:free"

class QueryResponse(BaseModel):
    response: str
    metadata: Optional[dict] = None

# Global agent cache
agent_cache = {}

def get_agent_for_model(model_name: str):
    if model_name in agent_cache:
        return agent_cache[model_name]
    
    try:
        print(f"Initializing agent for model: {model_name}")
        agent = create_pagila_agent(model_name)
        agent_cache[model_name] = agent
        return agent
    except Exception as e:
        print(f"Failed to initialize agent for {model_name}: {e}")
        return None

# Initialize default agent
get_agent_for_model("mistralai/mistral-7b-instruct:free")

@app.get("/")
def read_root():
    return {"message": "Pagila RAG API is running"}

@app.get("/models")
def get_models():
    """Fetch free models from OpenRouter and add OpenAI models."""
    models_list = []
    
    # 1. Add OpenAI Models (Hardcoded for now as we know we support them)
    openai_models = [
        {"id": "gpt-4o-mini", "name": "OpenAI GPT-4o Mini"},
        {"id": "gpt-3.5-turbo", "name": "OpenAI GPT-3.5 Turbo"},
        {"id": "gpt-4o", "name": "OpenAI GPT-4o"}
    ]
    models_list.extend(openai_models)

    # 2. Fetch OpenRouter Models
    try:
        response = requests.get("https://openrouter.ai/api/v1/models")
        if response.status_code == 200:
            data = response.json().get("data", [])
            # Filter for free models (prompt and completion pricing is 0)
            free_models = [
                model for model in data 
                if model.get("pricing", {}).get("prompt") == "0" 
                and model.get("pricing", {}).get("completion") == "0"
            ]
            # Sort by name
            free_models.sort(key=lambda x: x.get("name", ""))
            models_list.extend(free_models)
        else:
            print(f"Warning: Failed to fetch OpenRouter models: {response.status_code}")
    except Exception as e:
        print(f"Warning: Could not connect to OpenRouter: {e}")

    return {"models": models_list}

@app.post("/chat", response_model=QueryResponse)
def chat(request: QueryRequest):
    model_name = request.model or "mistralai/mistral-7b-instruct:free"
    agent = get_agent_for_model(model_name)
    
    if not agent:
        raise HTTPException(status_code=500, detail=f"Failed to initialize agent for model {model_name}")
    
    try:
        start_time = time.time()
        # invoke is the modern method, run is deprecated but works for now. 
        # Since we saw a deprecation warning, let's try invoke if possible, or stick to run for compatibility with current agent setup.
        response = agent.run(request.query)
        duration = time.time() - start_time
        
        # Try to extract the model name from the user choice, as extracting it from the agent instance is unreliable
        # agent.agent.llm_chain.llm.model_name
        model_name = request.model or "Unknown Model"

        return QueryResponse(
            response=response,
            metadata={
                "model": model_name,
                "duration": round(duration, 2)
            }
        )
    except Exception as e:
        # Print the full stack trace irrespective of the error type
        print("------------- ERROR IN CHAT ENDPOINT -------------")
        traceback.print_exc()
        print("--------------------------------------------------")
        
        # Check specifically for Rate Limit errors to give a better frontend experience
        if isinstance(e, openai.RateLimitError):
            print("The LLM Provider (OpenRouter) returned a 429 Rate Limit Error.")
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded (429). The AI model is busy or you have run out of credits. Please try again in 10-20 seconds."
            )
            
        # Default 500 behavior for other crashes
        raise HTTPException(status_code=500, detail=str(e))
