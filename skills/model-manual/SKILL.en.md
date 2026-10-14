---
name: model-manual
description: Integrate, migrate, or troubleshoot model API calls for DeepSeek, Kimi, Zhipu GLM, Qwen, Doubao, and MiniMax. Use for Chinese-vendor API configuration, model-specific parameters, streaming, JSON, tool calling, or checking a model not yet cataloged.
---

# Model Manual · Agent entry point

[Chinese](SKILL.md) | English · [Agent guide](../../agents/README.en.md) · [Human guide](../../human/README.en.md)

This is the English reading entry for the same `model-manual` Skill, not another installable Skill. Complete the user's model-calling task in their project; there is no need to read the whole tutorial in sequence. Machine cards, scripts, examples, and reports are shared across languages. A translation is not new execution evidence.

## Identify the task and exact model

1. Determine the vendor, model, language, and API style from the request and existing project. Ask only for missing information that affects implementation. Without an existing project or a requested language, use Python; without a requested model, read the vendor's `default_model`. Project defaults and maintained examples use paid models only: check the card's `billing.type.value=paid` and its official pricing source. Never silently fall back to a free model after an error. Check an explicitly requested different model by its original ID rather than renaming it. [Project selection policy](../../en/docs/evidence-policy.md)
2. Locate the vendor in [references/vendors.json](references/vendors.json), then read the exact model's card in [references/models/](references/models/). The catalog's `model_card` and `model_manual` refer only to the default model; another requested model requires an exact Model ID lookup. For English prose, use that model's `README.en.md` and `parameters.en.md`, not a replacement machine card.
3. Read parameters from `generation`, capabilities from `capabilities`, and resolve factual `source` references against the card's `sources`. Check lifecycle and subscription routing in `identity` first: an old Model ID does not guarantee the actual served version. When explaining parameters, use the [six model-specific parameter references](references/workflows.en.md#integration). Distinguish SDK options, server parameters, and application limits in examples.
4. Read only the relevant section of the [task workflows](references/workflows.en.md), selected below, then implement and check the change.

For functional code, first query the [official-example catalog](scripts/example_catalog.py): `python skills/model-manual/scripts/example_catalog.py --model <exact-model-id> --capability <capability-key>`. It returns files, parameter-reference paths, official sources, environment variables, commands, and evidence scope. Read only matching examples and their dependencies; use the English parameter-reference sibling for explanations. See the [English example index](../../en/docs/example-index.md) and [current file-execution status](../../en/docs/example-status.md). Missing combinations never fall back to another model; a missing example does not establish lack of support.

| User task | Workflow section | Focus |
|---|---|---|
| New integration, JSON extraction, streaming, or tools | Integration | Check the task/language combination and generate with the exact model's parameters |
| Change vendor/model or upgrade an SDK | Migration | Compare source and target, preserve application behavior, and handle parameter/message differences |
| Errors, empty text, interrupted streams, or tool loops | Troubleshooting | Diagnose with the actual response and exact model |
| A model absent from the catalog | Unknown models | Check official sources; do not inherit default-model parameters |
| Capability evidence or explicitly requested live tests | Evidence and verification | Separate model reports, file evidence, and generated code; execute only as authorized |

## Generate calling code

Run from the repository root. These commands generate code without sending model requests:

```bash
python skills/model-manual/scripts/generate_snippet.py --help
python skills/model-manual/scripts/generate_snippet.py --vendor kimi --language python --thinking off
python skills/model-manual/scripts/generate_snippet.py --vendor qwen --language typescript --stream
python skills/model-manual/scripts/generate_snippet.py --vendor kimi --task tool --thinking off
python skills/model-manual/scripts/generate_snippet.py --vendor qwen --task json --thinking off --max-tokens 2048
```

Languages are `python`, `typescript`, and `curl`; the script's help and exact model card determine supported task combinations. Resolve unknown models, unsupported combinations, and lifecycle restrictions first. Do not bypass them by renaming models, removing checks, or borrowing another model's parameters. Preserve the existing project's language, dependencies, and code style.

## Delivery and boundaries

- Deliver runnable code or project changes, necessary environment variables and commands, and the checks actually completed. Keep the response concise when the user only wants code.
- Cite official sources from the card for vendor parameter/capability claims. Link prices and quotas directly to official pages. Label project judgments as project recommendations under the [evidence policy](../../en/docs/evidence-policy.md).
- Read keys from the model's specified environment variables; never hardcode or echo them. Unless the user explicitly requests live calls, only generate/modify code or perform offline checks.
- Preserve output-integrity checks: finish reasons and nonempty text for ordinary/JSON results; empty `choices` and completion state for streams; validated tool names/arguments, matching `tool_call_id`, full assistant messages, and bounded loops for tools. Example tool data is simulated.
- Model-card `verification: null` / `verification_scope: not_run` means only that the model-level shared workflow has no report. It cannot override an example's real HTTP report, and one passing file cannot upgrade an entire model card. Follow [evidence and verification](references/workflows.en.md#evidence-and-verification) to check original reports, scope, and current hashes.
- A passing existing file does not validate arbitrary generated parameter/task combinations. Changed file or support-dependency hashes require re-execution. `verified` is limited to the report's date, model, and checks; rate limits, missing keys, or missing evidence do not establish unsupported functionality.
- Do not invent a thinking-off switch for a model that cannot disable thinking. Formatting options such as `reasoning_split` are not thinking-off controls. Read request defaults, budget names, and permitted thinking modes from the exact card.
- Resolve summary conflicts using the exact card and original reports. The [file executor](../../tests/run_example_files.py) lists examples by default; only `--execute` sends requests. Authorization, commands, and report synchronization are covered in [evidence and verification](references/workflows.en.md#evidence-and-verification). Compilation, mocks, and historical tests must not be reported as a new live pass.

The generator mainly covers cataloged models' Chat Completions. Advanced examples include additional APIs/features checked for their exact model; use their source manifests. Chat Completions compatibility does not establish compatibility with every OpenAI API, and one example does not prove every parameter is supported.
