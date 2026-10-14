# Model Manual

[中文](README.md) · English

A model API handbook for people, and an implementation guide for coding agents. The human guide explains concepts, parameters and pitfalls; the agent guide routes integration, migration and debugging tasks. Both use the same model cards, executable examples and real execution reports. [Evidence policy](en/docs/evidence-policy.md)

## Choose your guide

| What you want to do | English | 中文 |
|---|---|---|
| Understand, call and troubleshoot models yourself | [Human guide](human/README.en.md) | [人类篇](human/README.md) |
| Have a coding agent integrate, migrate or debug calls | [Agent guide](agents/README.en.md) | [Agent 篇](agents/README.md) |

For an agent, start with [SKILL.en.md](skills/model-manual/SKILL.en.md); Chinese instructions are in [SKILL.md](skills/model-manual/SKILL.md). Agents do not need to read the entire human guide first.

## What is included

| Material | Entry point |
|---|---|
| First call, compatible APIs, environment variables, pricing links and common errors | [Human reading path](human/README.en.md#reading-path) |
| Exact model identities, endpoints, capabilities, limits, lifecycle and official sources across six providers | [Model manuals](models/README.en.md) |
| Context versus output budgets, temperature/top-p, thinking, streaming, JSON, tools and multimodal fields | [Parameter guide](en/docs/parameters.md) |
| Complete files for chat, streaming, thinking, multi-turn, JSON/Schema, tool loops and model-specific image/video features | [Official-source example index](en/docs/example-index.md) |
| Reasoning tokens, truncation, empty answers, tool history, interrupted streams, rate limits and production checks | [Production pitfalls](en/docs/production-pitfalls.md) |
| Integration, migration, debugging, unknown-model and evidence-review workflows | [Agent guide](agents/README.en.md) |
| Model-card-driven Python / TypeScript / cURL generation and capability-based example lookup | [Generator](skills/model-manual/scripts/generate_snippet.py) · [Example catalog tool](skills/model-manual/scripts/example_catalog.py) |
| Locked dependencies, offline regression tests, real file execution, sanitized reports and source-hash checks | [Verification and reproduction](en/docs/verification.md) |
| Chinese and English guides, six model manuals, parameter references and generated status pages | [Chinese edition](README.md) |

This is a content inventory, not a claim that every model supports every listed feature. Read [current per-file execution status](en/docs/example-status.md) for current file counts, passing evidence and outstanding cases. The older capability checks are separate: [historical workflow status](en/docs/verification-status.md).

## Covered models

Project rule: default calls and maintained examples use paid models only, with no automatic free-model fallback after errors. Follow each manual's official pricing link; promotional credits do not change a model's paid billing category. [Selection policy](en/docs/evidence-policy.md)

| Provider | Exact model / English manual | 中文说明书 |
|---|---|---|
| DeepSeek | [deepseek-flash](models/deepseek/deepseek-flash/README.en.md) | [中文](models/deepseek/deepseek-flash/README.md) |
| Kimi | [kimi-k2.6](models/kimi/kimi-k2.6/README.en.md) | [中文](models/kimi/kimi-k2.6/README.md) |
| Zhipu | [glm-4.7](models/zhipu/glm-4.7/README.en.md) | [中文](models/zhipu/glm-4.7/README.md) |
| Qwen | [qwen-flash](models/qwen/qwen-flash/README.en.md) | [中文](models/qwen/qwen-flash/README.md) |
| Doubao | [doubao-seed-2-1-pro-260628](models/doubao/doubao-seed-2-1-pro-260628/README.en.md) | [中文](models/doubao/doubao-seed-2-1-pro-260628/README.md) |
| MiniMax | [MiniMax-M2.7](models/minimax/MiniMax-M2.7/README.en.md) | [中文](models/minimax/MiniMax-M2.7/README.md) |

A model name is not a permanent availability guarantee. Check official lifecycle, subscription routing and region references, especially for older models and aliases. Another model from the same provider is not an automatic substitute. [Inclusion policy](en/docs/evidence-policy.md)

## One fact layer, two audiences, two languages

Model facts remain in the shared [machine-readable cards](skills/model-manual/references/models/); provider routing remains in [vendors.json](skills/model-manual/references/vendors.json). Both languages link to the same [source examples](models/) and [raw reports](verification/examples/). Translation is not a new API test, and the English edition does not silently switch API regions or credentials.

Prices and allowances link directly to official pages. Unknowns remain unknown, and rate limiting is not recast as lack of support. Both generated editions use the same data; the [translation checker](scripts/check_translations.py) tracks static page pairs and the source revision reviewed for each translation. It does not prove semantic translation accuracy. [Full policy](en/docs/evidence-policy.md)

## Maintenance, safety and license

Installation, offline checks, bilingual synchronization and explicitly authorized real calls are covered in [verification](en/docs/verification.md). Synchronized status pages do not imply that every example passed; [release checks](tests/check_example_release.py) distinguish that stricter condition with --require-passed. The existing [CI template](ci/offline-checks.yml) is still not enabled as GitHub Actions.

Keep keys in environment variables or a Git-ignored .env, never in code, chat, reports or commits. Do not overwrite an existing .env with the example template. [Safety policy](en/docs/evidence-policy.md) · [Ignore rules](.gitignore)

The organization was inspired by [HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter). This project is not affiliated with that project or any model provider. Licensed under the [Unlicense](LICENSE).
