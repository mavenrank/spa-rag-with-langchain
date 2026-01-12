# Full Stack SQL RAG with LangChain (SPA)

This Single Page Application (SPA) enables natural language interaction with an SQL database. The project implements a retrieval-augmented generation (RAG) architecture specialized for Text-to-SQL workflows. It bridges the gap between raw data and user intent by utilizing LangChain agents to dynamically construct, validate, and execute SQL queries against a PostgreSQL database.

## External Dependencies

This project relies on external repositories for the database schema and core logic patterns. These must be present in the project root for the environment to function correctly.

1.  **Pagila Dataset** (`pagila`)

    -   **Repository**: [devrimgunduz/pagila](https://github.com/devrimgunduz/pagila)
    -   **Purpose**: A ported version of the Sakila database for PostgreSQL, providing the DVD rental store schema (films, actors, rentals, customers).
    -   **Requirement**: The `pagila` folder must exist in the root workspace. The `docker-compose.yml` configuration mounts SQL files directly from this folder to initialize the database container.
    -   **Installation**: `git clone https://github.com/devrimgunduz/pagila.git`

2.  **LangChain Essentials** (`lca-langchainV1-essentials`)
    -   **Source**: Course Material
    -   **Purpose**: The agentic patterns, specifically the SQL agent implementation and tool usage, were adapted from the course's Python examples.

## System Architecture

The application follows a standard three-tier architecture:

1.  **Frontend (UI Layer)**:

    -   **React 18 + Vite**: Provides high-performance client-side routing.
    -   **UI Design**: Custom CSS implementing an edge-to-edge chat interface.
    -   **State Management**: Manages chat history, loading states, and model selection.

2.  **Backend (API Layer)**:

    -   **FastAPI**: Asynchronous Python web framework.
    -   **Endpoints**: `/chat` for interaction, `/models` for configuration.
    -   **Middleware**: Configured CORS for secure SPA communication.

3.  **Orchestration (AI Layer)**:
    -   **LangChain**: Manages the agent execution loop (Thought -> Action -> Observation).
    -   **SQLToolkit**: Provides tools for schema inspection (`list_tables`, `schema`) and query execution (`query_sql`).
    -   **Hybrid LLM Engine**: Supports strategy switching between OpenAI (production) and OpenRouter (testing).

## Key Features

-   **Intelligent Text-to-SQL Agent**: Capable of interpreting complex queries involving aggregations, joins, and filtering. Includes self-correction mechanisms to retry failed SQL queries.
-   **Hybrid and Dynamic LLM Support**:
    -   **Native OpenAI**: Integration with `gpt-4o` and `gpt-4o-mini`.
    -   **OpenRouter**: Access to open-source models (e.g., Mistral, Llama 3).
    -   **Dynamic Switching**: Users can toggle between models during a session.
-   **Error Handling**:
    -   **Rate Limit Protection**: Handles HTTP 429 errors from providers.
    -   **Fallback Handling**: Parses malformed LLM responses to ensure continuity.
-   **Developer Tooling**:
    -   **Containerization**: Docker-based setup for PostgreSQL and PgAdmin.
    -   **Metadata**: Interface displays model usage and inference duration.

## Prerequisites

-   **Docker Desktop**: Required for the database container.
-   **Python 3.10+**: Required for the backend API.
-   **Node.js 18+**: Required for the frontend application.

## Installation and Setup

### 1. Database Initialization

**Important**: Ensure the `pagila` repository is cloned in the root directory before starting Docker. The container initialization relies on these files.

```bash
# In the project root
git clone https://github.com/devrimgunduz/pagila.git
```

Start the PostgreSQL database and PgAdmin services:

```bash
docker-compose up -d
```

-   **Postgres**: `localhost:5432`
-   **PgAdmin**: `localhost:5050` (Credentials: `admin@admin.com` / `root`)

### 2. Backend Configuration

Setting up the Python environment and dependencies:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory with the following configuration:

```env
# Database Connection
POSTGRES_DB_URI=postgresql://postgres:postgres@localhost:5432/pagila

# LLM Providers
OPENAI_API_KEY=sk-...               # Required for OpenAI models
OPENROUTER_API_KEY=sk-or-...        # Required for OpenRouter models
```

Start the API server:

```bash
uvicorn api:app --reload
```

Documentation available at `http://localhost:8000/docs`.

### 3. Frontend Configuration

Setting up the React application:

```bash
cd frontend
npm install
npm run dev
```

Access the application at `http://localhost:5173`.

## Usage Guide

1.  **Model Selection**:
    -   **OpenAI GPT-4o Mini**: Recommended for reliable SQL generation.
    -   **Mistral 7B (Free)**: Suitable for cost-free testing.
2.  **Query Execution**:
    -   Examples: "How many films are in the database?", "List the top 5 customers by total payment amount.", "What tables contain address information?"
3.  **Result Inspection**:
    -   The interface displays the agent's thought process, the synthesized answer, and execution metadata.

## Project Structure

```text
.
├── backend/
│   ├── agent.py            # Logic: LangChain Agent factory and LLM routing
│   ├── api.py              # API: FastAPI endpoints and caching
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── Chat.jsx        # UI: Main chat component
│   │   └── App.jsx         # Application entry point
├── lca-langchainV1-essentials/ # Reference: Learning materials
├── docker-compose.yml      # Infrastructure: Postgres and PgAdmin configuration
└── README.md               # Documentation
```
