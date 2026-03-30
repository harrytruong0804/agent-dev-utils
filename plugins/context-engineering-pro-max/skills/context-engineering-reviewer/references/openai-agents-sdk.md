# OpenAI Agents SDK — Context Engineering Patterns & Anti-Patterns

Read this reference when auditing an agent built with the OpenAI Agents SDK
(`openai-agents` / `from agents import Agent`).

---

## SDK Architecture Overview

The OpenAI Agents SDK uses these core primitives:
- **Agent**: LLM + instructions + tools + handoffs + guardrails
- **Runner**: Executes agent loops, manages tool calls, handles handoffs
- **Handoff**: One-way transfer of control to another agent
- **agent.as_tool()**: Wraps an agent as a callable tool (parent keeps control)
- **Guardrails**: Input/output/tool validation running in parallel
- **Sessions**: Persistent conversation state across runs
- **Context**: Dependency injection via `RunContextWrapper`

## What to Look For

### Agent Definition (`Agent(...)`)

```python
# GOOD: Clear, structured
agent = Agent(
    name="energy-analyst",
    instructions=ENERGY_ANALYST_PROMPT,  # externalized prompt
    model="gpt-4o",
    tools=[query_energy_data, get_building_info],
    handoffs=[escalate_to_expert],
    input_guardrails=[validate_input],
    output_guardrails=[validate_output],
    output_type=EnergyReport,  # structured output
)

# BAD: Inline everything, no guardrails, no structured output
agent = Agent(
    name="agent",
    instructions="You are helpful. Answer questions about energy.",
    tools=[query_energy_data, get_building_info, search_web,
           send_email, update_db, generate_report, ...],  # too many tools
)
```

**Check for:**
- `name`: Is it descriptive? (not "agent" or "assistant")
- `instructions`: Externalized to a variable/file? Or inline string?
- `model`: Appropriate for the task? (expensive model for simple routing?)
- `tools`: Count them. > 10 is a yellow flag. > 15 is red.
- `handoffs`: Present when multi-agent? Input filters configured?
- `guardrails`: Present? Both input AND output?
- `output_type`: Used when structured output is expected?

### Instructions Quality

```python
# GOOD: Structured with clear sections
PROMPT = """
<role>
You are an energy data analyst for building management systems.
</role>

<constraints>
- ONLY answer questions about energy data
- NEVER make up data — if you don't have it, say so
- Always include units (kWh, kW, etc.)
</constraints>

<tools>
- query_energy_data: Use for historical consumption queries
- get_building_info: Use for building metadata (area, type, zones)
</tools>

<output_format>
Always respond with:
1. Direct answer to the question
2. Data source reference
3. Confidence level (high/medium/low)
</output_format>
"""

# BAD: Unstructured wall of text
PROMPT = """You are a helpful assistant that answers questions about
energy data. You should be accurate and helpful. Use the tools available
to you to answer questions. Make sure to provide good answers. If you
don't know something, try your best. Be concise but thorough..."""
```

### Tool Definitions (`@function_tool`)

```python
# GOOD: Rich description, typed parameters, bounded output
@function_tool
def query_energy_data(
    building_id: str,
    metric: Literal["consumption", "demand", "cost"],
    start_date: str,
    end_date: str,
    granularity: Literal["hourly", "daily", "monthly"] = "daily",
) -> str:
    """Query historical energy data for a specific building.

    Use this tool when the user asks about energy consumption, demand,
    or cost for a specific building and time period.

    DO NOT use this for:
    - Real-time/current data (use get_live_readings instead)
    - Building metadata (use get_building_info instead)

    Returns: JSON with timestamps and values, max 100 data points.
    If more data is needed, narrow the date range or increase granularity.
    """

# BAD: Minimal description, untyped, unbounded
@function_tool
def query(query_str: str) -> str:
    """Run a query."""
```

### Handoff Patterns

```python
# GOOD: Filtered handoff with description
from agents import handoff
from agents.extensions import handoff_filters, handoff_prompt

specialist = Agent(
    name="hvac-specialist",
    instructions=handoff_prompt.prompt_with_handoff_instructions(
        HVAC_PROMPT  # includes info about handoff-back
    ),
    handoffs=[handoff(agent=triage_agent)],  # can hand back
)

handoff_to_hvac = handoff(
    agent=specialist,
    tool_description="Transfer to HVAC specialist for heating/cooling questions",
    input_filter=handoff_filters.remove_all_tools,  # clean context
)

# BAD: Raw handoff, no filter, no description
handoff_to_hvac = handoff(agent=specialist)
```

**Key checks:**
- Is `input_filter` used? Without it, the target agent inherits ALL
  tool call history from the source agent (context pollution)
- Is `handoff_prompt.RECOMMENDED_PROMPT_PREFIX` or equivalent used?
- Can the target agent hand back? Or is the user stuck?
- Is `tool_description` set? The LLM needs to know WHEN to handoff

### Agent-as-Tool vs Handoff Decision Matrix

| Scenario | Use | Why |
|----------|-----|-----|
| Parent needs the answer back | `agent.as_tool()` | Parent retains control |
| Full conversation transfer | `handoff()` | Target takes over |
| Parallel sub-tasks | `agent.as_tool()` | Can run multiple |
| Different persona/tone needed | `handoff()` | Clean break |
| User shouldn't notice the switch | `agent.as_tool()` | Seamless |

### Guardrail Patterns

```python
# GOOD: Parallel input + output guardrails
@input_guardrail
async def check_injection(ctx, agent, input):
    # runs in parallel with agent execution
    result = await classify_injection(input)
    return GuardrailFunctionOutput(
        tripwire_triggered=result.is_injection,
        output_info={"reason": result.reason}
    )

agent = Agent(
    ...,
    input_guardrails=[check_injection],
    output_guardrails=[check_pii_leakage],
)
```

**Key SDK behaviors to know:**
- Input guardrails only run on the FIRST agent in a handoff chain
- Output guardrails only run on the LAST agent that produces final output
- Tool guardrails apply to `@function_tool` only (not handoffs, not hosted tools)
- If you need per-tool validation in a multi-agent system, use tool guardrails

### Context Type & Dependency Injection

```python
# GOOD: Typed context with clear dependencies
@dataclass
class AppContext:
    user_id: str
    tenant_id: str
    db: DatabaseConnection
    permissions: UserPermissions

agent = Agent[AppContext](
    name="data-agent",
    instructions="...",
    tools=[query_data],
)

# Tool can access context
@function_tool
async def query_data(ctx: RunContextWrapper[AppContext], query: str) -> str:
    # Access typed dependencies
    db = ctx.context.db
    perms = ctx.context.permissions
    ...

# BAD: No context, hardcoded dependencies
@function_tool
def query_data(query: str) -> str:
    db = get_global_db()  # global state, no tenant isolation
    ...
```

### Runner Configuration

```python
# GOOD: Bounded execution
result = await Runner.run(
    agent,
    input="...",
    context=app_context,
    max_turns=25,        # prevent infinite loops
    hooks=LoggingHooks(), # observability
)

# BAD: Unbounded execution, no hooks
result = await Runner.run(agent, "...")
```

**Check for:**
- `max_turns`: Is it set? Default is unbounded.
- `hooks`: Any observability? (`RunHooks` or `AgentHooks`)
- Error handling around `Runner.run()` (what happens on exception?)
- Cost tracking via `result.usage` or hooks

### Sessions

```python
# GOOD: Persistent session for multi-turn conversations
result = await Runner.run(
    agent,
    input="...",
    session_id="user_123_session_abc",  # persistent state
)

# Consider: Is session cleanup handled? Expiry? Isolation?
```

---

## Common Anti-Pattern Catalog

### 1. The God Agent
One agent with 20+ tools, a 5000-token prompt, and no handoffs.
**Fix**: Split into specialized agents with clear responsibilities.

### 2. The Leaky Handoff
Handoff without `input_filter` — target agent sees all source agent's
tool call history, causing confusion and context bloat.
**Fix**: Use `handoff_filters.remove_all_tools` or a custom filter.

### 3. The Echo Chamber
Supervisor agent that calls sub-agents and relays their output verbatim.
The supervisor's re-telling introduces distortion.
**Fix**: Have sub-agents write results to files/state; supervisor reads directly.

### 4. The Token Furnace
Tools that return raw API responses (full HTML pages, entire DB tables,
unfiltered JSON) into the context window.
**Fix**: Filter, summarize, or paginate tool outputs before returning.

### 5. The Infinite Loop
No `max_turns` on Runner, no exit conditions in agent instructions.
Agent keeps calling tools and burning tokens forever.
**Fix**: Set `max_turns`, add explicit "stop when" conditions in instructions.

### 6. The Unguarded Frontier
No guardrails, or guardrails only on the entry agent while handoff
targets are completely unguarded.
**Fix**: Add input guardrails on entry, output guardrails on final agent,
tool guardrails on sensitive operations.

### 7. The Amnesia Agent
Multi-step workflow with no state tracking. Agent forgets what it
already did and repeats steps or contradicts itself.
**Fix**: Use a scratchpad/todo mechanism, structured state blocks,
or OpenAI Sessions for conversation persistence.

### 8. The Cascade Tax
Deeply nested agent hierarchy where each level adds latency overhead
from LLM calls. Leaf agents could be plain tool functions.
**Fix**: Flatten hierarchy. Demote leaf sub-agents to `@function_tool`.
Only use agents where LLM reasoning is actually needed.
