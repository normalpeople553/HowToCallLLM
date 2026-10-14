# 00 · How to read this manual

[中文](../../docs/00-前言.md) · [Human guide](../../human/README.en.md) · [Agent guide](../../agents/README.en.md)

Model Manual has two reading paths: the [human guide](../../human/README.en.md) explains how to use it, compare models, and interpret test coverage; the [Agent guide](../../agents/README.en.md) routes a coding agent to the material needed for an implementation task. The [repository README](../../README.en.md) is the common gateway. Both paths share the same model cards and original reports rather than maintaining separate sets of model facts. These are role-based paths, not separate beginner and expert editions. [Evidence policy](evidence-policy.md)

## For agents

Start with [SKILL.en.md](../../skills/model-manual/SKILL.en.md), identify the task and exact model, then read the relevant integration, migration, troubleshooting, unknown-model, or verification section in the [task workflows](../../skills/model-manual/references/workflows.en.md).

Locate material in this order: vendor directory → exact model card → corresponding manual and examples → relevant verification reports. The vendor directory only routes to a default model; its defaults must not be applied automatically to other models from the same vendor. The Agent entry explains the workflow and path conventions.

## For humans

Copy a task instruction from the [human guide](../../human/README.en.md) to your agent, or look up the question you need to answer:

- Capabilities and limits: use the [model manuals](../../models/README.en.md) and their official sources.
- Calling differences and failures: read the [compatible-API pattern](compatible-api.md), [troubleshooting](troubleshooting.md), and [production pitfalls](production-pitfalls.md).
- Pricing and quotas: use the [official pricing links](pricing.md).
- Whether tests cover your needs: read the [unified verification status](verification-status.md) and original reports; use [verification and reproduction](verification.md) when rerunning tests yourself.

The [first-call tutorial](first-call.md) remains an optional walkthrough for running code manually. There is no requirement to read the chapters in order.

## Evidence labels

| Label | Meaning in this project |
|---|---|
| Official | A vendor's official source is linked in the same paragraph or table row. |
| Tested | A date, test scope, redacted report, and corresponding script are provided. |
| Project recommendation | An editorial recommendation about workflow, safety, or selection. |
| Unknown | Official documentation or repository tests do not provide enough evidence; no conclusion is inferred. |

An official support statement and one successful request are different kinds of evidence. A timeout, rate limit, or skipped test does not establish lack of support; one passing request does not establish reliability for other models or every business task. Prices, quotas, model names, and parameters can change. See the [evidence and maintenance policy](evidence-policy.md).

## Current scope

This repository covers Chat Completions, streaming, and explicitly documented thinking controls for collected models. Use JSON, Tool Calling, multimodal inputs, and other APIs only within each exact card's recorded scope; do not infer compatibility with every OpenAI API. [Skill boundaries](../../skills/model-manual/SKILL.en.md)

Examples require Python 3.10+. Standalone reproduction uses [requirements-lock.txt](../../requirements-lock.txt). Installation and testing are documented in [verification and reproduction](verification.md); see [API key safety](troubleshooting.md#api-key-safety) for credential handling.
