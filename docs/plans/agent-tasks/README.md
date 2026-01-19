# Agent Task Files

This folder contains work packages split for parallel agent execution.

## Overview

Based on `CODEBASE_IMPROVEMENT_PLAN.md` and `PARALLEL_EXECUTION_PLAN.md`, work is divided into 6 independent streams that can be executed in parallel by different agents/developers.

## Streams

| Stream | File | Priority | Duration | Dependencies |
|--------|------|----------|----------|--------------|
| A | [STREAM_A_SECURITY.md](STREAM_A_SECURITY.md) | CRITICAL | 3 weeks | None |
| B | [STREAM_B_BACKEND.md](STREAM_B_BACKEND.md) | HIGH | 5 weeks | None |
| C | [STREAM_C_FRONTEND.md](STREAM_C_FRONTEND.md) | HIGH | 5 weeks | Stream B (partial) |
| D | [STREAM_D_TESTING.md](STREAM_D_TESTING.md) | HIGH | 5 weeks | Streams A, B |
| E | [STREAM_E_OPERATIONS.md](STREAM_E_OPERATIONS.md) | MEDIUM | 3 weeks | None |
| F | [STREAM_F_QUICKWINS.md](STREAM_F_QUICKWINS.md) | LOW effort | 1-3 days | None |

## Recommended Start Order

1. **Day 1-3**: Start Stream F (Quick Wins) - any available agent
2. **Day 1**: Start Stream A (Security) - critical path
3. **Day 1**: Start Stream E (Operations) - independent
4. **Day 2**: Start Stream B (Backend) - enables frontend
5. **Day 2**: Start Stream C (Frontend) - can mock APIs initially
6. **Week 2+**: Start Stream D (Testing) - as features complete

## Parallel Execution Diagram

```
Day 1-3     Week 1-2      Week 2-3      Week 3-4      Week 4-5
────────────────────────────────────────────────────────────────
Stream F ══►
Stream A ═══════════════════════════════►
Stream E ═══════════════════════►
Stream B ═══════════════════════════════════════════════════════►
Stream C ═══════════════════════════════════════════════════════►
Stream D      ═══════════════════════════════════════════════════►
```

## How to Use These Files

### For Claude Code Agents

Each file is self-contained with:
- Task breakdown by week
- Specific file paths to modify
- Code snippets and implementation hints
- Exit criteria/checklist
- Related files for reference

### Assignment Example

```
Agent 1: Read STREAM_A_SECURITY.md, implement auth
Agent 2: Read STREAM_B_BACKEND.md, implement insights
Agent 3: Read STREAM_C_FRONTEND.md, split components
Agent 4: Read STREAM_F_QUICKWINS.md, do all quick fixes
```

### Progress Tracking

Each stream file has checkboxes. Update them as tasks complete:
- [ ] Pending
- [x] Complete

## Exit Criteria (All Streams)

When all streams complete:
- [ ] All endpoints require authentication (Stream A)
- [ ] All stubbed features implemented (Stream B)
- [ ] No component > 500 lines (Stream C)
- [ ] Test coverage > 70% (Stream D)
- [ ] Notifications working (Stream E)
- [ ] Quick wins complete (Stream F)

## Related Documents

- [CODEBASE_IMPROVEMENT_PLAN.md](../CODEBASE_IMPROVEMENT_PLAN.md) - Full assessment
- [PARALLEL_EXECUTION_PLAN.md](../PARALLEL_EXECUTION_PLAN.md) - Timeline and dependencies
- [FEATURE_STATUS.md](../FEATURE_STATUS.md) - Current feature status
