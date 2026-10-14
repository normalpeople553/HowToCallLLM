# Agent task workflows

[Chinese](workflows.md) | English

Read the sections relevant to the task. Model names, parameter values, and capability claims still come from the shared [model cards](models/). The [evidence policy](../../../en/docs/evidence-policy.md) governs maintenance of sources and evidence. This is the English workflow for the same Skill; translation does not create new calling or test evidence.

## Integration

Use for new model calls and specific JSON, streaming, tool, or image tasks.

1. Inspect the existing client, configuration, dependencies, and calling entry point to locate the change. Select capabilities from the task; do not enable thinking or add tools by default.
2. Read `identity`, `capabilities`, and `generation` in the exact model card. Read the corresponding parameter page below when explaining or adjusting fields. Check API, key environment variable, lifecycle, thinking controls, output-budget semantics, and task constraints. `documented` means official support is documented, not that a live test passed. Check official sources for unknown capabilities.
3. For existing functional code, query [example_catalog.py](../scripts/example_catalog.py) by exact model/capability and inspect its `examples/sources.json`, official sources, parameter notes, and evidence scope. If no matching example exists, use [generate_snippet.py](../scripts/generate_snippet.py) `--help` for supported combinations. Integrate the request and response checks into the project. Put Python vendor extensions in `extra_body` as the card specifies; check other APIs against the matching example instead of reusing Chat parameters. A rewritten combination does not inherit the original file's live evidence.
4. For JSON, check completion, parse the result, and validate application fields. For tools, allowlist names/arguments, return results, retain full messages, and bound the loop. For images, use the user's input; accepting an image request is not a recognition-accuracy evaluation.
5. Run relevant offline checks and provide commands plus any outstanding live verification. Follow the existing project's dependency management. Standalone repository examples use locked dependencies; see [verification and reproduction](../../../en/docs/verification.md).

Parameter pages map fields to example files and explain defaults/ranges, modes, and side effects; read only the model needed for the task. Check their official sources for vendor facts. Project budgets and application checks are not server limits. General terminology is in the [parameter guide](../../../en/docs/parameters.md).

| Exact model | English parameter reference |
|---|---|
| `deepseek-flash` | [Parameters](../../../models/deepseek/deepseek-flash/parameters.en.md) |
| `kimi-k2.6` | [Parameters](../../../models/kimi/kimi-k2.6/parameters.en.md) |
| `glm-4.7` | [Parameters](../../../models/zhipu/glm-4.7/parameters.en.md) |
| `qwen-flash` | [Parameters](../../../models/qwen/qwen-flash/parameters.en.md) |
| `doubao-seed-2-1-pro-260628` | [Parameters](../../../models/doubao/doubao-seed-2-1-pro-260628/parameters.en.md) |
| `MiniMax-M2.7` | [Parameters](../../../models/minimax/MiniMax-M2.7/parameters.en.md) |

Run these commands from the repository root; they only generate example code:

```bash
python skills/model-manual/scripts/generate_snippet.py --vendor qwen --model qwen-flash --task json --thinking off --max-tokens 2048
python skills/model-manual/scripts/generate_snippet.py --vendor kimi --model kimi-k2.6 --task tool --thinking off
```

If generation rejects a combination, distinguish an undeclared model capability from a missing template for that language. A missing template does not establish that the model lacks support. When handwritten implementation is needed, follow official documentation and project requirements, and state the actual verification scope.

## Migration

Use when changing vendor, model, or SDK. Read both source and target cards first. If the source is absent from the catalog, establish its configuration from existing code and official documentation, not by working backward from the target.

Compare only the features the project actually uses:

| Area | Behavior to confirm |
|---|---|
| Endpoint and identity | Key, base URL, Model ID, region, access enablement, and lifecycle |
| Thinking | Default behavior, control fields, SDK extension placement, and whether thinking history must be returned |
| Output budget | Parameter name/range and whether it includes thinking tokens |
| Messages and streaming | Roles, content structure, thinking fields, empty chunks, finish reasons, and usage |
| Structured output | JSON/Schema scope, thinking-mode restrictions, parsing, and application validation |
| Tool calling | tool_choice, argument constraints, tool_call_id, complete assistant messages, and loop limits |
| Multimodal and other APIs | Input formats, exact-model capabilities, and API type; do not add unused features |

Separate reusable application logic from protocol code that needs replacement, then implement the change. Replacing only the host and model name is not a completed migration; silently reducing a tool workflow to plain-text answers is also not acceptable.

Run project offline tests for changed behavior. Deliver the differences, changed locations, and unverified items. Call models for a live comparison only when requested. Explain that the observations concern fixed tasks; one execution does not establish a general quality ranking.

## Troubleshooting

Read the actual Model ID, endpoint, SDK version, sanitized request, original HTTP/business codes, finish reason, and available usage. Ask only for missing information that distinguishes likely causes, never the full key. Vendor `notes` are in [vendors.json](vendors.json), but exact-model rules take precedence.

The table provides investigation branches, not diagnoses from a status code alone. Cite the vendor's official source for error meanings and parameter behavior. See [production pitfalls](../../../en/docs/production-pitfalls.md) and [troubleshooting](../../../en/docs/troubleshooting.md) for mechanisms and code.

| Symptom | Next check |
|---|---|
| 401 / 403 | Verify the key's platform, permissions, region, and access enablement; retain the business code |
| 404 | Check endpoint path, model name, and deployment/access requirements separately; do not immediately conclude retirement |
| 400 | Compare parameters, thinking mode, message format, and tool history against the exact model card |
| 429 | Distinguish account limits from service load; use bounded backoff under official rules, not an unsupported-capability label |
| Timeout / 5xx | Inspect network and service responses, then choose timeouts and bounded retries appropriate to the request |
| HTTP 200 but empty or truncated text | Check finish_reason and thinking/answer budgets; retries do not repair an inadequate budget |
| Incomplete JSON or incorrect fields | Check completion, JSON instructions, parsing, and application validation; separate format from semantic errors |
| Interrupted stream or usage-chunk error | Check empty choices, termination chunks, and complete text, not merely whether some text arrived |
| Tool errors or infinite loop | Check tool names, full arguments, tool_call_id, thinking history, and loop limits |

Provide the smallest evidence-supported fix and a way to check it. If logs are missing or reproduction is unavailable, describe hypotheses as checks, not established causes. Retries of external writes must also account for duplicate application actions.

## Model discovery

For questions about a provider's other language models, query [model_catalog.py](../scripts/model_catalog.py) or the corresponding [language-model list](../../../en/docs/model-lists/README.md), rather than returning only the default from `vendors.json`. Run at the repository root:

```bash
python skills/model-manual/scripts/model_catalog.py --vendor deepseek
python skills/model-manual/scripts/model_catalog.py --vendor deepseek --model deepseek-v4-pro
```

Queries only read the local official-document snapshot and registered code, not private records, keys or the network. Explain `checked_at`, `status`, row restrictions and official sources. `available` means officially listed, not a successful request by the current account. `billing=paid` does not establish pay-as-you-go access; previews may be subscription-only. Recheck official pages for current availability; live calls require separate authorization.

`repository_coverage` joins exact vendor and ID: `manual_path` / `parameters_path` refer to maintained-card pages, while `example_files` identifies calling code for that exact ID. Public queries omit private execution statistics. Defaults, aliases, families and served versions do not transfer coverage. Discovery entries without cards do not enter the generator; free discovery entries do not change paid-default policy. Unknown IDs return no match, never a silent replacement.

If the user asks only for a model list, maintain bilingual fields and official sources in `data/model-lists/<vendor>.json`, then regenerate pages. Do not thereby create detailed cards, claim live tests or change defaults.

## Unknown models

If the requested model has no machine card, do not overwrite the default card's Model ID and continue generation.

1. First use discovery to locate the exact ID and sources, then check availability, lifecycle, required task capabilities and model-specific parameters in official model/API documentation. Retain official links and the check date. Absence from discovery does not establish lack of official support.
2. If the user only needs their project integrated, handwritten implementation from official sources is allowed with an explicit not-cataloged/not-live-tested scope. Do not expand this knowledge base without a request. State any unresolved critical behavior instead of guessing parameters.
3. If the user requests an addition to this manual, create a separate card in [models/](models/) and a manual plus necessary examples under repository `models/<vendor>/<model-id>/`. Follow neighboring card structures and generator validation. Every `value` or `status` source must resolve; do not copy other models' facts or records. Use the schema's applicable unknown state for undocumented capabilities. Actually run new calling code before publication; keep execution records local.
4. Change a vendor's `default_model` only when the user requests it. Current verifiers fix their test models, and the [synchronizer](../scripts/sync_verification.py) only derives default-model vendor summaries. A new card does not automatically become the default or gain a verifier. Update affected offline checks and verification scripts when expanding coverage, so a new model is not accidentally tested as an old one.

For a new model without a shared-workflow record, use `verification: null` and `verification_scope: "not_run"`, not a fabricated path. For an existing unpublished record, use `verification:null` and `verification_scope:private`. Public synchronization shows official attribution and publication boundaries, not counts or reports, and reads no local execution records. New models still need a card, manual, example source manifest and offline checks.

## Evidence and verification

Distinguish explanation, offline checking and live reproduction. Ordinary integration does not authorize potentially billable requests or input uploads.

The public repository provides official attribution, parameters, canonical code and run commands, not execution reports, model replies, statistics or execution fingerprints. `verification.live=private` and `verification_scope=private` mean records are unpublished, not unexecuted or publicly auditable proof of a pass. State missing local records explicitly; model cards, code existence and offline mocks do not establish live success.

- Calling guidance: locate the exact model's source and official attribution without requiring the reader to supply private maintainer records.
- Present availability: recheck official lifecycle, account and input requirements; historical maintenance results do not guarantee current access.
- Generated or changed code: report only compilation, mocks or authorized live execution actually performed, without inheriting an original example's pass.
- Maintainer checking: read `.local/evidence/` only when needed; retain source/dependency identity, real HTTP and completion checks, without rewriting old hashes to impersonate a rerun. Missing, broken or stale private evidence cannot become a pass.

### Reproduce real examples only as authorized

After installing pinned dependencies, query inventory from the repository root. The default reads no key and sends no request:

```bash
python tests/run_example_files.py --vendor kimi
```

Execute only after explicit authorization. Reports default to the Git-ignored local directory:

```bash
python tests/run_example_files.py --execute --file models/kimi/kimi-k2.6/examples/01_basic.py
```

Read only needed environment credentials or an ignored .env; do not echo or commit them. Do not accidentally upload private media. Inputs, video options, timeout/delay controls and exit codes are in [reproduction](../../../en/docs/verification.md). Private reports omit execution times, durations and reply bodies. Never publish them in the public repository. The unified verifier covers its fixed checks, not every example.

Maintainers may explicitly run `python tests/check_example_release.py --check --require-passed` to inspect complete local evidence. Ordinary public clones use `--check` for the code directory and must not claim a private pass without records. Public pages and queries must not change based on private records.

After maintaining public cards, source or documentation, run:

```bash
python -m unittest discover -s tests -p 'test_*.py'
python skills/model-manual/scripts/sync_verification.py --check
python skills/model-manual/scripts/example_catalog.py --check
python skills/model-manual/scripts/model_catalog.py --check
python scripts/render_human_examples.py --check
python tests/check_example_release.py --check
```

Regenerate affected pages before checking. Deliver the chosen model, official attribution, code, environment variables, run instructions and checks actually performed; explain uncertainty in troubleshooting and behavior changes in migrations. Do not label offline checking as a new live pass.
