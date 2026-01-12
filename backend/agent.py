import os
import sys
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.agent_toolkits import create_sql_agent

# Load environment variables
load_dotenv()

import random

def get_llm(model_name: str = "mistralai/mistral-7b-instruct:free"):
    """Initialize the LLM using OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found in .env")
        sys.exit(1)
    
    return ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0
    )

def get_openai_llm(model_name: str):
    """Initialize the LLM using OpenAI directly."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # For now, just print an error, but in a real app better exception handling
        print("Error: OPENAI_API_KEY not found in .env")
        raise ValueError("OPENAI_API_KEY not set in environment")
    
    return ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        temperature=0
    )


# Global DB instance
_db_instance = None

def get_db():
    """Connect to the PostgreSQL database."""
    global _db_instance
    if _db_instance:
        return _db_instance

    db_uri = os.getenv("POSTGRES_DB_URI")
    if not db_uri:
        print("Error: POSTGRES_DB_URI not found in .env")
        sys.exit(1)
    
    # Verify connection
    try:
        db = SQLDatabase.from_uri(db_uri)
        print("Successfully connected to the database.")
        print(f"Dialect: {db.dialect}")
        print(f"Usable tables: {len(db.get_usable_table_names())}")
        _db_instance = db
        return db
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def fallback_handler(error: Exception) -> str:
    """
    Fallback for when the LLM effectively answers but fails the ReAct format.
    If the LLM just chats (e.g. 'The answer is 5') without 'Final Answer:',
    we catch it here and return it as the final answer.
    """
    error_str = str(error)
    try:
        # LangChain's OutputParserException stringifies to "Could not parse LLM output: `...`"
        if "Could not parse LLM output:" in error_str:
            # Try to split by the standard error marker
            parts = error_str.split("Could not parse LLM output: `")
            if len(parts) > 1:
                response = parts[1]
                # Remove the trailing backtick if present
                if response.endswith("`"):
                    response = response[:-1]
                # Check if the response effectively IS the answer (i.e. chatting)
                # We return it as an observation hoping the LLM will just repeat it as Final Answer
                return f"Output parsed but format incorrect. Please repeat this EXACT answer with the prefix 'Final Answer:': {response}"
    except Exception:
        pass
    
    # If it's a different error or extraction failed, return a safe message
    return f"Error: {str(error)}. Please check your output format. If you have the answer, output it as 'Final Answer: [your answer]'."

def create_pagila_agent(model_name: str = "mistralai/mistral-7b-instruct:free"):
    """Create the SQL Agent for Pagila."""
    # Determine which provider to use based on model name prefix
    if model_name.startswith("gpt-"):
        print(f"Using OpenAI provider for model: {model_name}")
        llm = get_openai_llm(model_name)
    else:
        print(f"Using OpenRouter provider for model: {model_name}")
        llm = get_llm(model_name)

    db = get_db()
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    
    # Printing tools to understand what the agent has access to
    # The 'sql_db_schema' tool is what the agent uses to fetch table definitions dynamically!
    tools = toolkit.get_tools()
    print(f"\n--- Agent Tools ({len(tools)}) ---")
    for tool in tools:
        print(f"- {tool.name}: {tool.description.strip().split('.')[0]}")
    print("----------------------------\n")

    # Custom instructions to give the agent personality and handle greetings
    custom_prefix = """You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for the relevant columns given the question.
You have access to tools for interacting with the database.
Only use the below tools. Only use the information returned by the below tools to construct your final answer.
You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

IMPORTANT:
- If the user greets you (e.g., "hi", "hello"), reply with: "Final Answer: Hello! I am your Pagila Database Assistant. I can help you find movies, actors, and rental information."
- If the user asks what this is or what you can do (e.g., "what is this about?", "explain this database", "what tables are there?"), reply with: "Final Answer: This is the Pagila database, which models a DVD rental store. It contains 1000 films, along with actors, customers, and rental history. You can ask me questions like 'How many movies are rated PG?' or 'Who is the most popular actor?'."
- If the question is not related to the database (e.g., "what is the capital of France?"), reply with: "Final Answer: I can only answer questions related to the movie database. Please ask about films, actors, or store inventory."

"""

    agent = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        agent_type="zero-shot-react-description",
        agent_executor_kwargs={"handle_parsing_errors": True},
        prefix=custom_prefix
    )
    return agent

if __name__ == "__main__":
    # Test the agent
    print("Initializing Pagila Agent...")
    try:
        agent = create_pagila_agent()
        
        question = "How many films are there in the database?"
        print(f"\nProcessing query: {question}")
        
        response = agent.run(question)
        print(f"\nFinal Answer: {response}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
