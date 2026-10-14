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

Queries only read the local official-document snapshot and existing evidence, not keys or the network. Explain `checked_at`, `status`, row restrictions and official sources. `available` means officially listed, not a successful request by the current account. `billing=paid` does not establish pay-as-you-go access; previews may be subscription-only. Recheck official pages for current availability; live calls require separate authorization.

`repository_coverage` joins exact vendor and ID: `manual_path` / `parameters_path` refer to maintained-card pages, while `example_files` / `live_passed_files` refer to current-source evidence for that exact ID. Defaults, aliases, families and served versions do not transfer coverage. Discovery entries without cards do not enter the generator; free discovery entries do not change paid-default policy. Unknown IDs return no match, never a silent replacement.

If the user asks only for a model list, maintain bilingual fields and official sources in `data/model-lists/<vendor>.json`, then regenerate pages. Do not thereby create detailed cards, claim live tests or change defaults.

## Unknown models

If the requested model has no machine card, do not overwrite the default card's Model ID and continue generation.

1. First use discovery to locate the exact ID and sources, then check availability, lifecycle, required task capabilities and model-specific parameters in official model/API documentation. Retain official links and the check date. Absence from discovery does not establish lack of official support.
2. If the user only needs their project integrated, handwritten implementation from official sources is allowed with an explicit not-cataloged/not-live-tested scope. Do not expand this knowledge base without a request. State any unresolved critical behavior instead of guessing parameters.
3. If the user requests an addition to this manual, create a separate card in [models/](models/) and a manual plus necessary examples under repository `models/<vendor>/<model-id>/`. Follow neighboring card structures and generator validation. Every `value` or `status` source must resolve; do not copy other models' facts or reports. Use the schema's applicable unknown state for undocumented capabilities. `verified` requires a real report for that model.
4. Change a vendor's `default_model` only when the user requests it. Current verifiers fix their test models, and the [synchronizer](../scripts/sync_verification.py) only derives default-model vendor summaries. A new card does not automatically become the default or gain a verifier. Update affected offline checks and verification scripts when expanding coverage, so a new model is not accidentally tested as an old one.

For a new model without a shared-workflow report, use `verification: null` and `verification_scope: "not_run"`, not a fabricated path. The synchronizer shows this layer as untested/no registered report, uses — rather than zero counts, and never inherits another model's state. A broken nonempty reference still fails. MiniMax M2.7's model card keeps this state, but its standalone examples have separate file-level evidence; neither layer replaces the other. New models still need a card, manual, example source manifest, and offline checks.

## Evidence and verification

First distinguish a request for historical results, code verification, or new live calls. Ordinary integration permits code generation and offline checks, not unsolicited potentially billable model calls.

| Information | Source and reporting scope |
|---|---|
| Official support and parameter rules | Resolve source → sources in the model card; state the official claim and check date |
| Model-level shared workflow | Read the card's verification report for evidence identifier, model, parameters, and checks; null/not_run means this layer lacks a report. The [historical workflow page](../../../en/docs/verification-status.md) is a derived view |
| Current offline checks | Report commands and actual outcomes; do not call them successful online requests |
| Current status of a specific example | Read [example execution status](../../../en/docs/example-status.md), the model's examples/sources.json, and the referenced file report, evidence_scope, evidence identifier, and hashes; do not infer from a historical model report |
| Newly generated/rewritten code | Report only compilation, mocks, or live execution actually performed; a similar example's pass does not cover new parameter/task/tool/input combinations |

`mock_tested` is not server verification. Report `live=not_run`, missing keys/inputs/runtime, rate limits, timeouts, and failures separately; none counts as a pass. A model card may legitimately retain `verification: null` while a specific example has real HTTP passing evidence. Conversely, an old model workflow report cannot cover every advanced file. Read current results dynamically; never prewrite that all examples passed.

Compare `source_sha256` with current file and dependency identity. Dependencies include same-directory `_*.py`; the cross-model entry point also includes model cards and the vendor catalog; language-specific trace helpers are included according to executor/catalog rules. Mismatched hashes mean old evidence cannot represent the current version: re-execute and retain a new report. Never edit old report hashes to repair status. `example_catalog.py --check` checks linked file evidence against current source without sending requests. The [English example index](../../../en/docs/example-index.md) is generated from those manifests.

Read real HTTP metadata alongside the original file's process result. Telemetry collection/decompression failure does not establish that the original API call failed; inspect exit_code, telemetry_error/telemetry_overflow, and completion evidence. Older Shell/TypeScript reports may only contain original_file_process_exit_and_its_response_checks; do not claim observed HTTP status, usage, or served-model metadata for those records. A normal response pass only establishes the recorded input/parameter workflow, not general accuracy.

### Reproduce real examples only as authorized

For integration/explanation alone, use offline checks. Execute only authorized vendors/files after the user explicitly requests live calls. Run the following from the repository root after installing locked dependencies. The default inventory command reads no key and calls no model:

```bash
python tests/run_example_files.py --vendor kimi
```

Executing a registered file requires explicit `--execute` and a new, nonexistent report path, for example:

```bash
python tests/run_example_files.py --execute --file models/kimi/kimi-k2.6/examples/01_basic.py --report /tmp/model-manual-kimi-example-new.json
```

Configure only the needed environment variables; do not echo or commit keys, or print `.env` to check its existence. The executor defaults to generated image/video teaching fixtures. If Doubao video needs an authorized public HTTPS input, provide it explicitly with `--video-url`; do not accidentally inherit private media. File selection, timeouts/delays, and language dependencies follow the [executor's help](../../../tests/run_example_files.py). Unregistered generated files cannot use this entry point to impersonate evidence for a registered file.

The original shared verifier still covers its fixed checks; see [verification and reproduction](../../../en/docs/verification.md) for entry points and exit codes. Its coverage differs from the file executor. After adding a file report, update sources.json references only when the target file, dependency hashes, and outcomes match, then regenerate the index. Do not also promote the entire model to verified.

Resolve paths relative to the file defining them: vendors.json model_card/model_manual paths are relative to its directory, but vendor-summary verification paths are repository-root-relative. A model card's verification path is relative to the card directory. Do not mix the two report-path rules.

A card's last_checked_at is the official-document check date and remains intact. New file reports use schema 2 and strict unified reports use schema 3, with a random UUIDv4 evidence_id. Do not store or display tested_at or duration_seconds; privacy.test_timestamps_saved and privacy.duration_saved are both false. An identifier does not express order or prove real-time availability. Privacy redaction must not promote basic reports to strict verification. See the [time-minimization rule](../../../en/docs/evidence-policy.md#minimize-execution-time-information-project-rule). verified also requires matching specific checks; a historical smoke check does not establish a complete strict workflow. Preserve failed, rate-limited, and skipped outcomes instead of relabeling them unsupported.

If asked whether a model works now, historical results cannot establish present availability. State the evidence scope and freshness limitations and rerun only when the user requests live verification. Recheck official sources when documentation conflicts with a card; locate differences in original reports when summaries disagree. Do not rewrite historical outcomes to make wording consistent.

After maintaining cards or reports, run from the repository root:

```bash
python -m unittest discover -s tests -p 'test_*.py'
python skills/model-manual/scripts/sync_verification.py --check
python skills/model-manual/scripts/example_catalog.py --check
```

To update derived summaries, run synchronization without --check first, then recheck. Rules for live requests, report storage, and exit codes remain in [verification and reproduction](../../../en/docs/verification.md).

Deliver what the task needs: actual vendor/model and sources, code/changes, dependencies and environment variables, commands, completed checks, and unverified parts. For migration, include behavior differences; for troubleshooting, include evidence for the cause and how to check the fix.
