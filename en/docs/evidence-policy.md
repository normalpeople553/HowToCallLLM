# Sources and evidence policy

[中文](../../docs/来源与核验规则.md) · [Human guide](../../human/README.en.md) · [Agent guide](../../agents/README.en.md)

The project separates information into three categories. These are repository editorial rules; this document defines the rules themselves.

- **Official:** vendor facts—model IDs, endpoints, parameter behavior, prices, quotas, lifecycle—must link to official vendor documentation in the same paragraph, table row, or immediately adjacent text.
- **Tested:** provide the test date and links to a redacted report and its registered script. A test proves only the result at that time, for that account, model, and explicit scope. Report generation is explained in [verification and reproduction](verification.md).
- **Project convention:** editorial choices about selection, defaults, security habits, or troubleshooting order must be identified as project recommendations or rules, not presented as vendor promises.

Prices and free quotas change quickly. Copied numbers are not a permanent source of truth; link directly to official pages: [DeepSeek](https://api-docs.deepseek.com/quick_start/pricing/), [Kimi](https://platform.kimi.com/docs/pricing/chat), [Zhipu GLM](https://docs.bigmodel.cn/cn/guide/start/pricing), [Qwen](https://help.aliyun.com/zh/model-studio/model-pricing), [Doubao / Ark](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh), [MiniMax](https://platform.minimax.cn/docs/guides/pricing-paygo).

## Two entry paths, one set of facts

The [repository entry](../../README.en.md) routes humans to the [human guide](../../human/README.en.md) and agents to the [Agent guide](../../agents/README.en.md) and [Skill](../../skills/model-manual/SKILL.en.md). Navigation and task instructions differ, but facts and evidence are shared. Human tutorials are optional reference material; agents need not read them sequentially.

### Bilingual maintenance rules

Chinese and English provide human and agent guides, general chapters, model manuals and parameter references, but share machine cards, executable code and raw reports. Translation must not change model IDs, API regions, request parameters, prompts or verification states. A code change still requires the original real-verification procedure; translation cannot justify inheriting old evidence.

The [translation manifest](../translations.json) maps static pages and records hashes of Chinese source revisions reviewed by a person or agent. After a source change, the [translation checker](../../scripts/check_translations.py) requests review of the English version and checks cited external URLs and parameter-page example mappings. A hash identifies a revision needing review, not semantic translation accuracy. Do not blindly refresh hashes without reviewing the translation.

The two example indexes, file-execution status pages and historical model status pages are generated from the same facts and reports; generation/check commands handle both languages. Do not create translated model cards, executable examples or execution reports. Preserve existing links and verified source paths. [Synchronization and reproduction](verification.md)

Model-level machine facts live in [skills/model-manual/references/models/](../../skills/model-manual/references/models/). [vendors.json](../../skills/model-manual/references/vendors.json) provides vendor entry points, default models, and compatible summaries only. Exact-model constraints take precedence over vendor summaries; an unknown model cannot inherit the default model's thinking switch.

| Content | Maintained in | How other entry points use it |
|---|---|---|
| Exact-model parameters, capabilities, and official sources | Model machine cards | The generator reads them; human manuals reference and explain them, with corresponding prose updated when facts change. |
| Historical unified-verifier dates, scope, and outcomes | Original redacted reports referenced by model cards | The synchronizer derives vendor summaries and [unified verification status](verification-status.md). |
| Real executions of specific runnable files | [File-execution reports](../../verification/examples/) | [Example status](example-status.md) interprets files, source fingerprints, and actual requests; it does not automatically rewrite model capability. |
| Default models and vendor entry points | Routing fields in `vendors.json` | Agents locate material; nondefault models require lookup by exact ID. |
| Integration, migration, and troubleshooting workflows | [Agent workflows](../../skills/model-manual/references/workflows.en.md) | The Skill routes by task; the README supplies usage instructions. |
| Official-example sources, adaptations, and commands | Each model's `examples/sources.json` | The [example index](example-index.md) is generated from manifests; agents query by model/capability. |

### Rules for integrating official examples

Code adapted from official documentation is labeled `adapted_from_official`, not called an unmodified official example. Its manifest records the exact Model ID, capability, official pages, source-check date, required environment variables, run command, and project adaptations. Simulated data, validation, and loop limits are project additions rather than vendor requirements. If a vendor example changes to a new model, find explicit support for the collected model before adapting it; do not merely replace the name.

Record `verification.offline` and `verification.live` separately. `live=not_run` means the manifest has no registered live-execution evidence. Every other live status must reference an actual file-level report matching model, status, time, source, and support-file fingerprints. `passed` additionally requires the exact model's final real HTTP request to finish normally with nonempty final content. Streaming needs a termination event or actual transport EOF, not just a process exit code. See the [catalog validator](../../skills/model-manual/scripts/example_catalog.py).

A historical model-level pass cannot be copied into a new file's status. Cross-check later manifests and reports against [file-level status](example-status.md). Offline mocks establish only simulated scenarios, not API acceptance or result reliability. Explain nonintegrated capabilities with reasons and official sources; “no example yet” is not “unsupported.” Maintenance commands are in [verification and reproduction](verification.md).

For model identity, capability, and common-parameter changes, update the exact card and sources first, then affected examples and human explanations. Maintain example sources/adaptations in the model's manifest. For unified-verifier evidence, add a new report, update the card pointer, and run the synchronizer. For file-level evidence, preserve the new original report and source fingerprints, then check the current files against [example status](example-status.md). Do not hand-edit derived capability summaries or overwrite test dates with edit dates. The six [parameter guides](parameters.md) are human explanations that must agree with cards, executable source, and official sources.

## Capability states and verification evidence

For the unified-verifier summaries, `verified`, `documented`, and `unknown` respectively mean: the corresponding test passed; official support is documented but that test has no passing evidence; or no reliable conclusion is available. Read them with the dates and scope in [unified verification status](verification-status.md), not as real-time states of every example. `unknown` does not mean unsupported. [Synchronizer](../../skills/model-manual/scripts/sync_verification.py)

Official statements and test results are recorded separately. Official links support capability claims; reports support particular executions. A rate limit does not rewrite capability as unsupported. An accepted request does not establish a complete tool loop, output-boundary handling, or image-content recognition.

`verification=null` and `verification_scope=not_run` mean there is no **unified-verifier report registered by that model card**. They do not mean the file executor has never called the model; for MiniMax and other models, also inspect [example status](example-status.md). Do not create an empty success report or inherit another model's evidence. A nonempty pointer to a missing report is a validation failure. [Synchronizer](../../skills/model-manual/scripts/sync_verification.py)

Older reports checked only nonempty content, initial tool arguments, or image-request shape. Preserve them as historical basic verification; do not fill in unrecorded `finish_reason` or complete-loop outcomes as passing. New strict-verification reports record the actual SDK/code versions, safe parameters, termination, and classified outcomes. Preserve changes over time through new reports. [Historical report example](../../models/kimi/kimi-k2.6/verification/2026-10-13.json)

The file executor runs the original file and observes real network transport, without substituting mock responses for vendor results. Reports retain only allowlisted metadata. Judgments combine the file's own checks, actual requests, and normal completion—not process exit alone. Retain failures, rate limits, missing inputs/runtimes, and evidence gaps; do not promise that every manifest entry succeeds. [Executor](../../tests/run_example_files.py) · [File-level status and reports](example-status.md)

Do not claim “every example passed live testing” until every current executable file has complete passing evidence. The [release check](../../tests/check_example_release.py) with `--check` checks page synchronization only; add `--require-passed` to fail the release gate on remaining unpassed files. Earlier observation scopes and historical-report retention are explained in the [report notes](../../verification/README.en.md).

Explanatory code blocks, generator output, and changed input/parameter combinations do not inherit a linked file's passing result. Rerun the relevant path after source, helper, runtime, or parameter changes. Even a real model/tool loop using explicitly simulated data is not verification of live weather or a real business system. These are project evidence rules; parameter details are in the [tuning guide](parameters.md).

The repository requires Python 3.10+ and uses [locked dependencies](../../requirements-lock.txt) for reproduction. Installation, offline checks, and real API verification commands are in [verification and reproduction](verification.md).
