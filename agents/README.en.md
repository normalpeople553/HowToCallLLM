# Agent Guide

[中文](README.md) · English · [Home](../README.en.md) · [Human guide](../human/README.en.md)

For coding agents performing integration, migration, debugging and verification. The [model-manual skill](../skills/model-manual/SKILL.en.md) is the execution entry point; this page provides task routing and usage prompts. Concepts belong in the [human guide](../human/README.en.md), which need not be read in full first.

## Start a task

Project defaults and maintained examples use paid models only. Read the card's `billing.type` and official pricing source; do not silently fall back to a free model after an error. [Selection policy](../en/docs/evidence-policy.md)

Read [SKILL.en.md](../skills/model-manual/SKILL.en.md) completely, then read only the relevant [workflow](../skills/model-manual/references/workflows.en.md). Do not load every model by default.

| User task | What matters |
|---|---|
| Integrate a provider or add JSON, streaming, tools or images | Existing project → exact model card → capabilities/parameters → matching complete example or generator |
| Change provider, model or SDK | Source and target cards, message/thinking/budget/tool differences, preserved business behavior and regression checks |
| Empty answers, truncation, interrupted streams, errors or tool loops | Sanitized request, real statuses, finish reasons, usage and official evidence; never ask for a full key |
| Use an unlisted model | Check that exact model's official identity and support; do not rename the default card |
| Review evidence or run a real test | Exact file, current hashes, report scope and user authorization; mocks are not online success |

These are project workflows, not provider guarantees. See [workflows](../skills/model-manual/references/workflows.en.md) for details and delivery requirements.

## Resource map

| Resource | Canonical location | Use |
|---|---|---|
| Provider routing | [vendors.json](../skills/model-manual/references/vendors.json) | Locate defaults without applying them to every model from that provider |
| Exact-model facts | [references/models](../skills/model-manual/references/models/) | Read identity, capabilities and generation; resolve each source reference |
| Parameter explanations | [Parameter navigation](../en/docs/parameters.md) | Read the relevant model only; distinguish SDK options, server parameters and local safety limits |
| Existing feature code | [example_catalog.py](../skills/model-manual/scripts/example_catalog.py) | Query exact model/capability, provenance, inputs, commands and evidence |
| New combinations | [generate_snippet.py](../skills/model-manual/scripts/generate_snippet.py) | Generate supported language/task combinations without inheriting old passing evidence |
| Current per-file results | [Execution status](../en/docs/example-status.md) · [Raw reports](../verification/examples/) | Check identity, date, source/support hashes, normal completion and evidence scope |
| Older capability checks | [Historical workflow status](../en/docs/verification-status.md) | Use only for its fixed test cases, not as per-file execution proof |

Run queries and generation from the repository root. These commands do not send model requests:

```bash
python skills/model-manual/scripts/example_catalog.py --model deepseek-flash --capability vision
python skills/model-manual/scripts/generate_snippet.py --help
python skills/model-manual/scripts/generate_snippet.py --vendor kimi --task tool --thinking off
```

## Prompts for your coding agent

**Integrate:** Read skills/model-manual/SKILL.en.md in this repository and integrate Kimi into my project. First inspect its language, dependencies and call sites; read the exact model's documentation, then provide implementation, run instructions and verification scope. Do not echo keys.

**Migrate:** Follow this repository's skill to migrate my Kimi calls to Qwen. Compare thinking, output budgets, JSON, streaming and complete tool messages. Preserve business behavior rather than only replacing the URL and model name.

**Debug:** Follow this repository's skill to investigate my sanitized error and minimal call. Use the actual response to distinguish authentication, rate limiting, budgets and protocol issues, then provide a minimal fix and a way to check it. Label unsupported explanations as hypotheses.

## Delivery and evidence boundaries

Provide the exact model and official sources, code or project changes, dependencies and variable names, run commands, and checks actually completed or still outstanding. Add behavior differences for migration and supporting evidence for debugging. [Contract](../skills/model-manual/SKILL.en.md)

- Read keys from the required environment variable or an ignored local file, never from hard-coded examples or output. A normal coding task does not automatically authorize billable real requests or uploading material.
- Generation and offline tests are not online verification. Historical evidence covers its model, parameters, inputs and date. Changed source or dependencies need new evidence.
- Explicitly label simulated tool data. Do not remove completion checks, tool-result round trips or required thinking history to manufacture a pass.
- No model-level workflow report does not imply no real file execution; conversely, one passing file does not verify the entire model card.

See [evidence workflow](../skills/model-manual/references/workflows.en.md#evidence-and-verification) and [verification](../en/docs/verification.md) for boundaries and authorized execution. Machine JSON, CLI options and example paths are shared contracts: do not translate keys or silently change API regions.

## Chinese and compatibility entry points

The [Chinese guide](README.md) reads [SKILL.md](../skills/model-manual/SKILL.md) and the [Chinese workflow](../skills/model-manual/references/workflows.md), backed by the same cards, code and reports.

The old [agents/SKILL.md](SKILL.md) is a compatibility redirect. The old vendors/snippets directories contain deprecation notices, not separate authoritative facts or source templates. The maintained resources are the canonical paths in the table above.
