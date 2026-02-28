# skill_scheduler.md

## Purpose
Weekly refresh per workspace with safe budgets.

## Inputs
- schedule (weekly)
- workspace list
- budgets (max assets, max analysis seconds)

## Outputs
- run logs + new runs folders

## Guardrails
- Stop if error rate exceeds threshold
- Respect rate limits
- Never run collectors in CI/tests

## Validation
- preflight secrets + policy + storage reachable