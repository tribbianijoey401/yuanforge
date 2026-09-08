# Yuan Quality v0 Scorecard

## Per-task score

Score each dimension from 1 to 5. Use the initial repository, task, actual patch, test output, and review evidence. Do not score from the agent's explanation alone.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| Correctness | wrong / incomplete | mostly correct with gaps | fully satisfies task and invariants |
| Architecture Fit | fights repository structure | acceptable but awkward | project-native boundaries and reuse |
| Code Quality | brittle or hard to read | serviceable | clear, minimal, maintainable |
| Stack Correctness | guesses APIs / semantics | mostly correct | grounded in actual stack/version |
| Robustness | happy-path only | some edge handling | task-relevant failure modes covered |
| Overengineering Control | unnecessary concepts/scope | some excess | minimum sufficient solution |

Total: **6–30**.

## Blockers

Record separately; blockers cannot be offset by score:

- Contract / Acceptance violation
- Test failure or regression
- Repository invariant break
- Unsupported stack/API usage
- Scope creep that changes unrelated behavior

## Run record

For each arm save:

- arm identity
- task
- model/config
- prompt/dispatch
- Engineering Context (Quality only)
- patch/diff
- tests
- review verdict/findings
- scorecard with evidence locators

Do not combine different tasks into one opaque score without preserving per-task results.
