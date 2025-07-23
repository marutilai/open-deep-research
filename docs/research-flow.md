# Open Deep Research - Research Flow Architecture

## Overview

Open Deep Research uses a sophisticated multi-agent architecture with iterative refinement to produce comprehensive research reports. The system employs a supervisor-researcher pattern with multiple levels of iteration and quality control.

## Architecture Diagram

```
┌─────────────────┐
│   User Input    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Clarification?  │ ──── Optional: Ask clarifying questions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Research Brief  │ ──── Transform input into detailed research question
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│          Research Supervisor                     │
│  ┌─────────────────────────────────────────┐   │
│  │  Iteration Loop (max 3 rounds)          │   │
│  │  ┌─────────────────────────────────┐    │   │
│  │  │ Spawn Concurrent Researchers     │    │   │
│  │  │ (up to 5 parallel)              │    │   │
│  │  └──────────┬──────────────────────┘    │   │
│  │             ▼                           │   │
│  │  ┌──────────────────┐  ┌────────────┐  │   │
│  │  │  Researcher 1    │  │Researcher N│  │   │
│  │  │  ┌────────────┐  │  │ ┌────────┐│  │   │
│  │  │  │Search Loop │  │  │ │Search  ││  │   │
│  │  │  │(max 5 iter)│  │  │ │Loop    ││  │   │
│  │  │  └────────────┘  │  │ └────────┘│  │   │
│  │  └──────────────────┘  └────────────┘  │   │
│  │             ▼                           │   │
│  │  ┌─────────────────────────────────┐    │   │
│  │  │ Compress & Review Results       │    │   │
│  │  └──────────┬──────────────────────┘    │   │
│  │             ▼                           │   │
│  │  ┌─────────────────────────────────┐    │   │
│  │  │ Continue Research? OR Complete? │    │   │
│  │  └─────────────────────────────────┘    │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Final Report   │ ──── Generate comprehensive report from all findings
└─────────────────┘
```

## Detailed Flow

### 1. Input Processing & Clarification

**File**: `deep_researcher.py:48-65`

- **Purpose**: Ensure clear understanding of research scope
- **Process**:
  - Analyzes user input for ambiguity
  - Checks for undefined acronyms or unclear terms
  - Can ask clarifying questions (if enabled)
- **Configuration**: `allow_clarification` (default: true)

### 2. Research Brief Generation

**File**: `deep_researcher.py:67-96`

- **Purpose**: Transform user input into detailed research question
- **Process**:
  - Converts conversation history into structured research brief
  - Provides context and specific guidance for researchers
  - Initializes supervisor with research parameters

### 3. Research Supervisor

**File**: `deep_researcher.py:98-188`

The supervisor orchestrates the entire research process:

#### Key Responsibilities:
- Decides what topics to research
- Manages concurrent researcher agents
- Reviews research quality
- Determines when research is complete

#### Iteration Loop:
```python
for iteration in range(max_researcher_iterations):  # default: 3
    # 1. Analyze current research state
    # 2. Identify knowledge gaps
    # 3. Spawn researchers for new topics
    # 4. Review compressed results
    # 5. Decide: Continue or Complete?
```

#### Exit Criteria:
- Maximum iterations reached
- No new research topics identified
- `ResearchComplete` tool called
- Token limit exceeded

### 4. Individual Researcher Agents

**File**: `deep_researcher.py:197-263`

Each researcher operates independently with:

#### ReAct Loop:
```python
for tool_iteration in range(max_react_tool_calls):  # default: 5
    # 1. Analyze research topic
    # 2. Select best tool (web search, MCP tools, etc.)
    # 3. Execute search/tool
    # 4. Process results
    # 5. Decide: Need more info or sufficient?
```

#### Available Tools:
- **Web Search APIs**:
  - OpenAI Native Search
  - Anthropic Native Search
  - Tavily Search
- **MCP Tools**: Configurable external tools
- **Custom Tools**: Database queries, APIs, etc.

#### Search Strategy:
1. Start with broad searches for context
2. Progressively narrow based on findings
3. Avoid duplicate searches
4. Consider tool limitations

### 5. Research Compression

**File**: `deep_researcher.py:266-296`

- **Purpose**: Distill findings to essential information
- **Process**:
  - Remove redundant information
  - Preserve all sources and citations
  - Maintain key facts and insights
  - Handle token limits gracefully

### 6. Final Report Generation

**File**: `deep_researcher.py:308-360`

- **Purpose**: Create comprehensive, well-structured report
- **Features**:
  - Markdown formatting
  - Proper citations
  - Logical flow and structure
  - Token limit handling with progressive summarization

## Configuration Parameters

### Performance Tuning

```python
# Concurrency
max_concurrent_research_units = 5  # Parallel researchers

# Iteration Limits
max_researcher_iterations = 3      # Supervisor rounds
max_react_tool_calls = 5          # Per researcher
max_structured_output_retries = 3  # API retries

# Model Selection
research_model = "openai:gpt-4.1"
compression_model = "openai:gpt-4.1-mini"
final_report_model = "openai:gpt-4.1"
```

### Search Configuration

```python
search_api = SearchAPI.OPENAI  # or ANTHROPIC, TAVILY
```

## Quality Control Mechanisms

### 1. Multi-Level Iteration
- **Supervisor Level**: Multiple research rounds
- **Researcher Level**: Multiple tool calls per topic
- **Compression Level**: Retry on token limits

### 2. Structured Output Validation
- Pydantic models for all outputs
- Automatic retries on schema violations
- Type safety throughout pipeline

### 3. Token Limit Management
- Progressive content reduction
- Graceful degradation
- Model-specific limits

### 4. Research Depth Control
- Configurable iteration limits
- Cost-aware parallelization
- Explicit effort levels in prompts

## Best Practices

### 1. Cost Optimization
- Balance parallelization vs sequential research
- Set appropriate iteration limits
- Use cheaper models for compression

### 2. Quality Enhancement
- Enable clarification for ambiguous queries
- Increase iterations for "comprehensive" requests
- Configure multiple search APIs for redundancy

### 3. Performance Tuning
- Set `BG_JOB_ISOLATED_LOOPS=true` for better isolation
- Adjust concurrent units based on rate limits
- Monitor token usage across models

## Example Research Flow

```
User: "Research the latest developments in quantum computing"
↓
Clarification: "Would you like focus on hardware, algorithms, or applications?"
↓
User: "Focus on hardware breakthroughs in 2024"
↓
Research Brief: "Comprehensive analysis of quantum computing hardware developments in 2024..."
↓
Supervisor Round 1:
  - Researcher 1: "Major quantum processor announcements 2024"
  - Researcher 2: "Qubit coherence time improvements"
  - Researcher 3: "Error correction advances"
↓
Supervisor Round 2:
  - Researcher 4: "IBM quantum roadmap updates"
  - Researcher 5: "Google quantum supremacy claims"
↓
Final Report: Comprehensive markdown with citations
```

## Monitoring & Debugging

### Key Files to Watch:
- `deep_researcher.py`: Main orchestration logic
- `state.py`: State definitions and transitions
- `prompts.py`: System prompts for each agent
- `utils.py`: Tool implementations

### Common Issues:
1. **Token Limits**: Reduce model max_tokens or iteration counts
2. **Rate Limits**: Decrease max_concurrent_research_units
3. **Search API Errors**: Configure fallback search providers
4. **Quality Issues**: Increase iteration limits or adjust prompts