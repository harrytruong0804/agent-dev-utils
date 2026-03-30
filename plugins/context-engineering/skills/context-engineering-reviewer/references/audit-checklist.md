# Context Engineering Audit Checklist

Detailed criteria for each audit dimension. Read this file when performing
the deep analysis phase.

---

## Dimension 1: System Prompt Design

### Structure & Organization
- [ ] Uses clear section separators (XML tags, markdown headers, or delimiters)
- [ ] Sections are ordered by priority (identity → constraints → instructions → examples → output format)
- [ ] Critical constraints are placed at the TOP or BOTTOM of the prompt (not buried in the middle — the U-shaped attention curve means middle content gets 10-40% less recall)
- [ ] No mixing of "instruction altitudes" — hyper-specific rules and vague directives are grouped separately
- [ ] Prompt length is proportional to task complexity (not bloated with unnecessary content)

### Clarity & Specificity
- [ ] Agent role/identity is clearly defined in the first few lines
- [ ] Instructions use imperative language ("Do X" not "You might want to X")
- [ ] Ambiguous terms are defined (e.g., what counts as "relevant" or "important")
- [ ] Edge cases are explicitly addressed
- [ ] Output format is specified when structured output is expected

### Dynamic vs Static Content
- [ ] Frequently changing content (timestamps, user state) is NOT at the start of the prompt (breaks KV-cache)
- [ ] Static instructions come first, dynamic context comes after
- [ ] Template variables are used for personalization rather than full prompt rewrites

### Anti-patterns to flag
- Prompt > 4000 tokens without progressive disclosure
- Copy-pasted documentation dumps instead of curated instructions
- Contradictory instructions in different sections
- "Be helpful and accurate" type filler that adds no signal
- Instructions that the model would follow anyway (waste of tokens)

---

## Dimension 2: Tool Schema Quality

### Schema Design
- [ ] Tool names are descriptive and use consistent naming convention (e.g., all prefixed by domain: `booking_create`, `booking_cancel`)
- [ ] Tool descriptions clearly explain WHEN to use the tool, not just what it does
- [ ] Parameters have descriptions, types, and constraints (enums where applicable)
- [ ] Required vs optional parameters are correctly set
- [ ] Return type/format is documented in the description

### Tool Surface Area
- [ ] Number of tools is appropriate (10 tools with moderate schemas ≈ 5,000-8,000 tokens)
- [ ] No redundant tools that could be merged
- [ ] No overly generic tools that try to do everything
- [ ] Tools are grouped by domain for consistent prefix-based selection
- [ ] Consider: could tools be reduced by using a filesystem/bash approach instead?

### Tool Descriptions for LLM Selection
- [ ] Description includes negative examples ("Do NOT use this for X")
- [ ] Description includes the expected input format with an example
- [ ] Descriptions are unique enough that the LLM can distinguish between similar tools

### Anti-patterns to flag
- Tools with no description or single-word descriptions
- > 15 tools without dynamic loading or tool filtering
- Tool parameters that accept free-form strings when an enum would work
- Tools that return entire database tables instead of filtered results
- Missing error descriptions (LLM doesn't know what failures look like)

---

## Dimension 3: Agent Orchestration & Handoffs

### Architecture
- [ ] Agent topology matches task complexity (single agent for simple tasks, multi-agent for complex)
- [ ] Each agent has a clear, single responsibility
- [ ] Orchestration pattern is intentional (centralized manager vs decentralized handoffs)
- [ ] No unnecessary agent hierarchy depth (each level adds latency + token cost)

### Handoff Design (OpenAI Agents SDK specific)
- [ ] Handoff descriptions clearly explain WHEN handoff should occur
- [ ] Input filters are used to prevent context pollution across agents (`handoff_filters.remove_all_tools`)
- [ ] Handoff prompts include `RECOMMENDED_PROMPT_PREFIX` or equivalent
- [ ] Circular handoff loops are prevented or have explicit exit conditions
- [ ] Each agent's `instructions` mention what other agents exist and when to delegate

### Agent-as-Tool vs Handoff Decision
- [ ] `agent.as_tool()` is used when the parent needs the result back
- [ ] `handoff()` is used when control should fully transfer
- [ ] The choice is consistent and intentional throughout the codebase

### Context Isolation
- [ ] Each agent's context window contains only what it needs
- [ ] Sub-agents don't inherit irrelevant conversation history
- [ ] File system or external state is used for inter-agent data sharing (not stuffing into context)

### Anti-patterns to flag
- Deeply nested agent hierarchies (> 3 levels deep)
- Agents that are just thin wrappers around a single tool
- "God agent" that has all tools and all instructions
- Handoffs without input filters (context pollution)
- Missing handoff-back mechanism (user gets stuck with wrong agent)
- Supervisor agents that relay sub-agent conclusions verbatim (distortion risk)

---

## Dimension 4: Context Window Management

### Token Budget Awareness
- [ ] System prompt + tool schemas fit within a reasonable fraction of context window (< 30%)
- [ ] Tool call responses are bounded (no unbounded database query results)
- [ ] Conversation history has a compaction or summarization strategy
- [ ] Long documents are chunked or summarized before injection

### Progressive Disclosure
- [ ] Not all context is loaded upfront
- [ ] Additional context is loaded on-demand based on task requirements
- [ ] RAG/retrieval results are filtered for relevance before injection

### History Management
- [ ] Conversation history has a maximum length or token budget
- [ ] Old tool call results are summarized or removed
- [ ] In agentic loops, history compaction triggers before quality degrades (typically after 20-30 iterations)

### Anti-patterns to flag
- Stuffing entire documents into system prompt
- No limit on conversation history length
- Returning raw API responses without filtering/summarizing
- Loading all tools/skills at startup regardless of relevance
- No observation masking (raw HTML, full stack traces in context)

---

## Dimension 5: Guardrails & Safety

### Input Validation
- [ ] Input guardrails validate user input before agent processing
- [ ] Guardrails run in parallel with agent execution (not blocking)
- [ ] Tripwire mechanism is properly configured to halt on violations
- [ ] Guardrails cover: prompt injection, off-topic detection, PII detection

### Output Validation
- [ ] Output guardrails check agent responses before returning to user
- [ ] Structured output validation uses Pydantic models or equivalent
- [ ] Output format is enforced (not just requested in the prompt)

### Tool Safety
- [ ] Destructive operations require confirmation
- [ ] Tool inputs are validated before execution
- [ ] Tool guardrails are applied to function tools
- [ ] Rate limiting or budget caps exist for expensive operations

### Anti-patterns to flag
- No guardrails at all
- Guardrails only on the first agent (handoff targets are unguarded)
- Guardrails that block execution instead of running in parallel
- Over-reliance on prompt-based safety ("please don't do bad things")
- Missing error handling when guardrail check itself fails

---

## Dimension 6: Memory & State Management

### Session Management
- [ ] Conversation state is persisted appropriately for the use case
- [ ] Session isolation prevents cross-user data leakage
- [ ] Session has a defined lifecycle (creation, expiry, cleanup)

### Working Memory
- [ ] Agent has a mechanism to track progress on multi-step tasks (todo list, scratchpad)
- [ ] Key decisions and intermediate results are recorded (not just in context)
- [ ] Context includes structured state blocks, not just raw conversation history

### Long-term Memory
- [ ] If needed, agent can recall information from past sessions
- [ ] Memory retrieval is selective (not dumping all memories into context)
- [ ] Memory updates are validated before storage

### Anti-patterns to flag
- No state management in multi-step workflows
- Relying solely on conversation history for state
- Memory that grows unboundedly
- No mechanism to correct or forget incorrect memories
- Storing sensitive data in plain-text memory

---

## Dimension 7: Error Handling & Resilience

### Tool Failures
- [ ] Agent handles tool execution errors gracefully
- [ ] Retry logic exists for transient failures
- [ ] Fallback behavior is defined when tools are unavailable
- [ ] Error messages provide enough context for the LLM to recover

### Agent Loop Safety
- [ ] Maximum iteration count prevents infinite loops
- [ ] Timeout exists for long-running operations
- [ ] Budget/cost caps prevent runaway token usage
- [ ] Agent can recognize when it's stuck and ask for help

### Graceful Degradation
- [ ] Agent can function with reduced capabilities (some tools down)
- [ ] Clear error messages to user when agent can't complete a task
- [ ] Escalation path to human when agent confidence is low

### Anti-patterns to flag
- No max iterations on agent loop
- Silent failures (errors swallowed without informing user or LLM)
- Retry without backoff or jitter
- No cost tracking or budget limits
- Agent continues generating after hitting context limit (degraded quality)
