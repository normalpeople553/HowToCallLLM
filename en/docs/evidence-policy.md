# Source and publishing policy

[中文](../../docs/来源与核验规则.md) · English

These are repository editing and publishing rules, not vendor promises.

## What is public

Publish manuals, parameter explanations, official sources, executable calling code, pinned dependencies and offline checking tools. Do not publish execution JSON, model replies, reasoning text, HTTP request records, token statistics, execution source fingerprints or test times. Existing execution material stays local to the maintainer; see [local verification notes](../../verification/README.en.md).

Maintainers must actually run calling code before publishing it. Public pages omit the testing process and do not guarantee identical behavior for other accounts, regions, inputs or future service states. Readers should [reproduce calls](verification.md) in their own environment. Changed parameters, prompts, tools or media do not inherit the original result.

## Official facts and project conventions

Link official pages beside model identity, endpoint, parameter, pricing and lifecycle facts. Label defaults, security habits and troubleshooting choices as project recommendations or rules. Leave unconfirmed capabilities unknown; missing examples, rate limits or unpublished records do not establish lack of support.

Use official pricing entries: [DeepSeek](https://api-docs.deepseek.com/quick_start/pricing/), [Kimi](https://platform.kimi.com/docs/pricing/chat), [Zhipu GLM](https://docs.bigmodel.cn/cn/guide/start/pricing), [Qwen](https://help.aliyun.com/zh/model-studio/model-pricing), [Doubao Ark](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh), [MiniMax](https://platform.minimax.cn/docs/guides/pricing-paygo).

## Paid-model selection (project rule)

Provider defaults, maintained examples and generated defaults use paid models. Do not choose free models to save money or silently fall back after errors. Model-card `billing.type` references official pricing; credits do not change pay-as-you-go billing, and `Flash` does not imply free access. Check explicitly requested alternatives by exact ID instead of renaming them.

## Three entry points and shared facts

The [human guide](../../human/README.en.md) supports learning and review, the [model directory](../../models/README.en.md) groups manuals, parameters and code by exact model, and the [Agent guide](../../agents/README.en.md) provides integration, migration and troubleshooting. The canonical Agent entry is [SKILL.en.md](../../skills/model-manual/SKILL.en.md).

Maintain exact-model official facts in [model cards](../../skills/model-manual/references/models/); the [provider catalog](../../skills/model-manual/references/vendors.json) handles routing and defaults. The discovery [language-model lists](model-lists/README.md) track officially sourced lifecycle, modalities and pricing. Exclude retired models; aliases and families do not inherit repository coverage.

Label official adaptations `adapted_from_official`. Each `examples/sources.json` retains official sources, documentation check dates, environment variables, run commands and project adaptations. Public `verification.live=private` means execution records are unpublished, not `not_run` or publicly auditable proof of a pass. Model-card `verification=null` with `verification_scope=private` has the same publishing meaning; `not_run` means that shared workflow has no record. Public capability summaries derive `documented` or `unknown` from official sources, not `verified` from private records.

The [example index](example-index.md), [calling-code directory](example-status.md) and [human complete-code pages](../../human/examples/README.en.md) show code, purpose and attribution without private report links. Reading pages copy canonical source unchanged, do not introduce a second executable and do not claim the page itself was executed. Completion, JSON parsing and tool-loop checks remain in the code.

## Local verification and time minimization (project rule)

Local reports default to the Git-ignored `.local/evidence/`. Source fingerprints only help maintainers identify changes and are not displayed publicly. New reports omit execution dates, timestamps and durations, keys, message/reply/reasoning bodies, raw errors and request IDs. Functional timeouts, bounded retries and output-integrity checks remain. Never change old fingerprints to impersonate a rerun; absent local evidence stays explicitly absent rather than passing.

Ordinary integration and offline checks do not authorize live model requests. Run potentially billable tests that upload input only when explicitly requested. See [reproduction](verification.md). Removing records from the current public tree does not erase previously published Git history; do not automatically rewrite history or force-push. Keep official-document check dates and model lifecycle dates, which are not test dates.

## Bilingual maintenance (project rule)

Both languages share official cards and calling code. Do not create English report copies or rerun models for translation. Source hashes in the [translation manifest](../translations.json) track translation review, not execution fingerprints. Review the English text before updating a reviewed hash. Generation and checking commands are in [reproduction](verification.md).

The repository requires Python 3.10+ and [pinned dependencies](../../requirements-lock.txt). Offline mocks establish simulated boundaries, not API acceptance or business accuracy. Weather, order and inventory tools are teaching simulations, not live business systems.
