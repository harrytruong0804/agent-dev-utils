# Context Engineering Audit Report Template

Use this template to structure the final audit report.

---

## Header

```
# Context Engineering Audit Report
**Project**: [project name]
**Framework**: [OpenAI Agents SDK / LangGraph / Custom / ...]
**Date**: [audit date]
**Auditor**: Claude Code — context-engineering-reviewer skill
```

---

## 1. Architecture Summary

Brief description of the agent system:
- Number of agents
- Agent topology (text diagram)
- Primary use case
- Estimated total prompt tokens (system prompts + tool schemas)

Example topology:

```
┌─────────────────┐
│  Triage Agent    │ ← Entry point
│  (gpt-4o-mini)  │
└───────┬─────────┘
        │ handoff
  ┌─────┴──────┐
  │            │
  ▼            ▼
┌──────┐  ┌──────────┐
│ FAQ  │  │ Booking  │
│Agent │  │  Agent   │
└──────┘  └──────────┘
```

---

## 2. Scorecard

| Dimension | Rating | Summary |
|-----------|--------|---------|
| 1. System Prompt Design | 🟢/🟡/🔴 | one-line summary |
| 2. Tool Schema Quality | 🟢/🟡/🔴 | one-line summary |
| 3. Agent Orchestration | 🟢/🟡/🔴 | one-line summary |
| 4. Context Window Mgmt | 🟢/🟡/🔴 | one-line summary |
| 5. Guardrails & Safety | 🟢/🟡/🔴 | one-line summary |
| 6. Memory & State | 🟢/🟡/🔴 | one-line summary |
| 7. Error Handling | 🟢/🟡/🔴 | one-line summary |

**Overall**: X/7 dimensions green, Y/7 yellow, Z/7 red

---

## 3. Top 3 Critical Findings

### Finding 1: [Title]
- **Impact**: [What goes wrong because of this]
- **Location**: `path/to/file.py:L42-L58`
- **Evidence**: [code snippet showing the problem]
- **Fix**: [concrete code change or approach]
- **Effort**: [quick win / medium / significant refactor]

### Finding 2: [Title]
...

### Finding 3: [Title]
...

---

## 4. Detailed Findings by Dimension

### Dimension 1: System Prompt Design

**Rating**: 🟡 Needs Attention

**What's Good:**
- ...

**Issues Found:**
1. **[Issue title]** — [description with code reference]
2. ...

**Recommendations:**
- ...

[Repeat for each dimension]

---

## 5. Token Budget Analysis

| Component | Estimated Tokens | % of Context |
|-----------|-----------------|--------------|
| System prompt (Agent A) | ~X,XXX | X% |
| System prompt (Agent B) | ~X,XXX | X% |
| Tool schemas (N tools) | ~X,XXX | X% |
| Guardrail overhead | ~XXX | X% |
| **Total static context** | **~XX,XXX** | **X%** |
| Available for conversation | ~XX,XXX | X% |

**Context window**: [model's max context]
**Risk level**: [Low/Medium/High — based on static context ratio]

---

## 6. Prioritized Action Items

### Quick Wins (< 30 minutes)
1. [ ] ...
2. [ ] ...

### Medium Effort (1-4 hours)
1. [ ] ...
2. [ ] ...

### Significant Refactors (1+ days)
1. [ ] ...

---

## 7. Reference

Context engineering principles applied in this audit:
- U-shaped attention curve (lost-in-the-middle)
- Token budget awareness
- Context isolation in multi-agent systems
- Progressive disclosure
- KV-cache optimization
- Observation masking
- Structured state management

Sources:
- Manus: "Context Engineering for AI Agents"
- OpenAI: "A Practical Guide to Building Agents"
- Anthropic: Claude Code context engineering patterns
- Augment Code: "11 Prompting Techniques for Better AI Agents"
