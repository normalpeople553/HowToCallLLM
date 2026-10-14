# `MiniMax-M2.7` API manual

[中文](README.md) · [Human guide](../../../human/README.en.md) · [Parameter reference](parameters.en.md)

English translation of the [Chinese manual](README.md), source-checked there on **2026-10-14**. Code, source manifests and reports are shared. Original official URLs are retained, including Chinese pages. Translation does not rerun API verification. Machine facts: [model card](../../../skills/model-manual/references/models/MiniMax-M2.7.json); attribution/commands: [sources.json](examples/sources.json); cross-model navigation: [example index](../../../en/docs/example-index.md).

[Historical unified verification](../../../en/docs/verification-status.md) and [current per-file execution](../../../en/docs/example-status.md) are separate. An absent unified report does not mean this model's files were never called. Each result applies only to its recorded source, parameters, input and environment; fragments, modified requests and generated combinations do not inherit passes. [Evidence policy](../../../en/docs/evidence-policy.md)

## Check lifecycle first

The official notice retires the M2.7 series: **new-user access stops on 2026-10-19; pay-as-you-go API service shuts down on 2026-11-18**. From 2026-10-19, M Plan / Token Plan requests using the old M2.7 name route to M3.1 Flash Preview, retaining the name as a compatibility entry. An old Model ID therefore does not necessarily identify the original serving model. [Official retirement/routing notice][lifecycle]

Project policy preserves the user's exact requested model rather than silently changing it to M3. Check account type and the notice before integration. The [generator](../../../skills/model-manual/scripts/generate_snippet.py) emits a lifecycle warning to stderr but still requests MiniMax-M2.7; it does not import undocumented new-model parameters to bypass the boundary.

## Identity and endpoints

| Item | Recorded value | Official source |
|---|---|---|
| Exact Model ID | `MiniMax-M2.7`, not MiniMax-M2.7-highspeed | [Chat API][chat] |
| Context | 204,800 tokens | [SDK model list][sdk] |
| Chat generation field | max_completion_tokens, integer at least 1; M2.x maximum 204800. Input remains subject to context constraints, not simultaneous independent maximum capacity. | [Chat parameters][chat] |
| OpenAI SDK Base URL | `https://api.minimax.cn/v1` | [SDK setup][sdk] |
| Chat Completions | `POST /v1/chat/completions` | [Chat API][chat] |
| Legacy native interface | `POST /v1/text/chatcompletion_v2`, deprecated but still listing M2.7 | [Native API][native] |

These are different interfaces. The project defaults to compatible Chat for client reuse, keeping the user's native cURL separately. Do not use the complete /text/chatcompletion_v2 endpoint as SDK base_url. [SDK][sdk] · [Native API][native]

## Environment and first run

Obtain the appropriate account key from [official key management](https://platform.minimax.cn/console/access?tab=api-keys). Authentication is Bearer; the project reads MINIMAX_API_KEY and does not put actual keys in examples/reports. [Chat authentication][chat] · [Project security policy](../../../en/docs/evidence-policy.md)

After setting MINIMAX_API_KEY, run from the repository root:

```bash
python -m pip install -r requirements-lock.txt
python models/minimax/MiniMax-M2.7/examples/01_basic.py
```

This sends real requests and may incur charges. The [locked dependencies](../../../requirements-lock.txt) are the repository's reproducible environment, not a vendor minimum-version guarantee. Offline tests use fake responses; real-file runs and their scope are documented under [verification](../../../en/docs/verification.md).

## Basic Chat and native cURL

Use the shared [01_basic.py](examples/01_basic.py) for official Chat fields plus environment credentials, timeout, reasoning separation and completion checks. The [native cURL file](examples/07_native_curl.sh) calls the distinct deprecated native endpoint and checks both business and completion status. These are existing canonical files, not new English scripts. [Chat API][chat] · [Native API][native]

The Chinese documentation contains abbreviated illustrative budgets of 4096 for Python and the user's original 1024 for native cURL. They do not guarantee enough output and are not the canonical files' 16384 budget. Read [the actual parameter map](parameters.en.md#example-map) before copying a setting.

HTTP 200 alone is insufficient: native responses also contain base_resp business status. The project checks finish_reason, nonempty final content and unhandled tools. [Native response fields][native] · [Production checks](../../../en/docs/production-pitfalls.md)

## Thinking, streaming and budgets

M2.x thinking **cannot be disabled**: thinking.type disabled is accepted but ignored; reasoning_effort does not adjust this model. reasoning_split true only moves thinking to reasoning_content; false leaves it in content's `<think>` tags. Neither turns thinking off. [M2.x rules][chat]

The generator therefore rejects `--thinking off` for M2.7. Its default reasoning_split true supports separating final text; example budgets are project settings, not output-length promises. [Generation card](../../../skills/model-manual/references/models/MiniMax-M2.7.json)

max_tokens is deprecated in favor of max_completion_tokens. The SDK page explicitly includes thinking in the old field, but the new field's cited definition does not equally explicitly establish that accounting. This repository leaves **M2.7 max_completion_tokens reasoning-inclusion semantics unconfirmed**, rather than copying the old field or another provider. [Chat parameters][chat] · [SDK parameters][sdk]

The project rejects length, empty final text and missing normal termination. stream true is a transport setting, independent of reasoning_split; implementations handle text deltas, thinking deltas and empty-choices usage blocks separately. [Streaming][chat] · [Project checks](../../../en/docs/production-pitfalls.md)

## Multi-turn and complete tool loops

Return complete assistant messages, including tool calls and thinking. Do not replace history with display-only text or remove `<think>` blocks; that can break continuity. [SDK function-call requirements][sdk]

[06_multi_turn.py](examples/06_multi_turn.py) covers ordinary history; [05_tool_calling.py](examples/05_tool_calling.py) implements a complete bounded loop. Weather is fixed simulated teaching data, not a live weather backend. Tool allowlisting, batch validation, call-ID deduplication and turn limits are project policies. [Shared manifest](examples/sources.json)

## Capabilities not transplanted to M2.7

| Feature | Integration boundary | Official source |
|---|---|---|
| JSON Mode / JSON Schema | Native response_format is documented only for MiniMax-Text-01; compatible Chat does not confirm that field for M2.7. No format-guaranteed JSON example is supplied. | [Native][native]; [Chat][chat] |
| Native images/video | The SDK multimodal section names M3/M3.1. Do not transplant their inputs; “not integrated” does not imply all external visual tools are impossible. | [SDK multimodal scope][sdk] |
| Anthropic, caching and other advanced paths | This batch focuses on Chat and the user's native endpoint; missing dependencies/full workflows are not a claim the vendor offers nothing else. | [Model-calling guide](https://platform.minimax.cn/docs/guides/text-generation) |

## Pricing, troubleshooting and evidence

Use [official pay-as-you-go pricing](https://platform.minimax.cn/docs/guides/pricing-paygo), not a copied number. Check subscription/pay-as-you-go keys, quotas and routing separately; one plan does not establish another API's availability. [Pricing/account rules](https://platform.minimax.cn/docs/guides/pricing-paygo) · [Lifecycle notice][lifecycle]

Project troubleshooting order: domain, account type, exact model and lifecycle; then HTTP/business status, output budget, complete termination and tool history. See [production pitfalls](../../../en/docs/production-pitfalls.md) and [parameters](parameters.en.md).

Card verification null / verification_scope not_run means no unified-verifier report is registered there, not that [per-file reports](../../../en/docs/example-status.md) contain no real requests. Check each file/report rather than promoting a basic call into a general capability claim. Reports omit keys and bodies; see [evidence policy](../../../en/docs/evidence-policy.md) and [verification](../../../en/docs/verification.md).

[lifecycle]: https://platform.minimax.cn/docs/guides/models-intro
[chat]: https://platform.minimax.cn/docs/api-reference/text-chat-openai
[sdk]: https://platform.minimax.cn/docs/api-reference/text-openai-api
[native]: https://platform.minimax.cn/docs/api-reference/text-post
