# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open Deep Research is an automated research assistant that generates comprehensive reports on any topic. It searches multiple sources (web, academic papers, databases) and produces well-structured, cited markdown reports.

## Development Commands

```bash
# Start the development server (primary command)
uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --allow-blocking

# Run evaluation tests
python tests/run_evaluate.py

# Test specific agent implementations
python tests/run_test.py --agent multi_agent
python tests/run_test.py --agent graph

# Linting and type checking
ruff check .
mypy .
```

## Architecture Overview

The codebase has two main implementation approaches:

### Current Implementation (`src/open_deep_research/`)
- **Supervisor-Researcher Pattern**: A supervisor agent manages multiple researcher agents that work concurrently
- **Key Components**:
  - `deep_researcher.py`: Main workflow orchestration
  - `configuration.py`: Model and API configuration (supports OpenAI, Anthropic, Google, DeepSeek, Groq)
  - `state.py`: Workflow state management
  - Multiple search API support: Tavily, OpenAI Native, Anthropic Native

### Legacy Implementations (`src/legacy/`)
- **Graph-based**: Plan-and-execute with human-in-the-loop (`graph.py`)
- **Multi-Agent**: Parallel processing with multiple researchers (`multi_agent.py`)

## Key Development Patterns

1. **State Management**: Uses LangGraph's state pattern - always check `state.py` for the current state structure
2. **Model Configuration**: All model settings are in `configuration.py` - supports different models for different tasks
3. **Structured Output**: Uses Pydantic models with retry mechanisms for reliable LLM outputs
4. **Search Integration**: Abstracted search functionality in `utils.py` with multiple provider support

## Testing Approach

The project uses comprehensive evaluation:
- Tests evaluate reports on 9 quality dimensions (topic relevance, structure, citations, etc.)
- Use `python tests/run_evaluate.py` to run batch evaluations
- Evaluation datasets are managed in LangSmith

## Important Notes

- The project uses `uv` as the package manager (not pip directly)
- Python 3.11 is required
- Environment variables must be set in `.env` file (copy from `.env.example`)
- LangGraph Studio provides visual workflow debugging at `http://localhost:8123`
- MCP (Model Context Protocol) support allows extending capabilities through external tools