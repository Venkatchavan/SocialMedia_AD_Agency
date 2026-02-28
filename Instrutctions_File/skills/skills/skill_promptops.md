# skill_promptops.md

## Purpose
Version prompts, run benchmarks, apply Recursive Learning safely.

## Inputs
- prompt versions
- benchmark asset set
- QA stats + operator feedback

## Outputs
- prompts/vN/*
- changelog.md
- benchmark_results.json
- rollback plan

## Guardrails
- Change ONE thing per iteration.
- Always run regression benchmark before shipping.

## Validation
- benchmark delta within thresholds
- QA failures do not increase