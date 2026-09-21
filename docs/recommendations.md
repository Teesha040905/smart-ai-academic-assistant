# Recommendation engine

Rules are **deterministic** and unit-testable. LLM wording is optional and not required for priority scoring.

## Scoring signals

| Signal | Effect |
|--------|--------|
| Knowledge level < 60 | Strong priority boost |
| Quiz average < 60 | Boost + practice actions |
| Exam within 7 days | Urgency boost `(8 - days) * 12` |
| Not revised ≥ 4 days | Decay penalty |
| Topic importance | Multiplier |
| Assignment due ≤ 3 days | High-priority assignment card |

## Example (demo)

Backpropagation @ 44% + ML exam in 6 days → high score → actions:

- 30 min revision
- 20 min practice quiz
- 15 min flashcards

## Exam readiness

Not a mark prediction. Weighted blend of syllabus coverage, quiz performance, revision activity, and practice volume — explained in API `readiness.explanation`.
