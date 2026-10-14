# `glm-4.7-flash` API manual

[中文](README.md) · [Human guide](../../../human/README.en.md) · [Parameter reference](parameters.en.md)

English translation of the [Chinese manual](README.md), source-checked there on **2026-10-13**. Code, source manifests and reports are shared. Official URLs are unchanged, including Chinese pages. Translation does not rerun API verification. Machine facts: [`glm-4.7-flash.json`](../../../skills/model-manual/references/models/glm-4.7-flash.json).

Find attribution and commands in [sources.json](examples/sources.json) and the [example index](../../../en/docs/example-index.md). Keep [historical unified verification](../../../en/docs/verification-status.md) separate from [current file results](../../../en/docs/example-status.md): a result applies only to its source, inputs, parameters and environment. Fragments, modified requests and generated combinations do not inherit passes. [Evidence policy](../../../en/docs/evidence-policy.md)

## 1. At a glance

| Item | Recorded value | Official source |
|---|---|---|
| Model ID | `glm-4.7-flash` | [Chat API][api] |
| Base URL | `https://open.bigmodel.cn/api/paas/v4/` | [OpenAI compatibility][sdk] |
| Context | 200K tokens | [Pricing][pricing] |
| Maximum output | 128K tokens | [Chat API][api] |
| Price | Free input and output in the cited source snapshot | [Pricing][pricing] |

Consult official pages for current service terms. Parameter interpretation and unknown defaults are in the [full reference](parameters.en.md).

## 2. First call

Official compatible examples use ZAI_API_KEY. This repository instead reads ZHIPU_API_KEY for consistency with its existing overview; these are local names and do not change authentication. [OpenAI compatibility][sdk]

After setting ZHIPU_API_KEY, run the shared executable from the repository root:

```bash
python -m pip install -r requirements-lock.txt
python models/zhipu/glm-4.7-flash/examples/01_basic.py
```

This sends a real request. [01_basic.py](examples/01_basic.py) contains completion/nonempty checks; it is not a separately translated script. Request and response fields follow the [Chat API][api]. Environment, evidence and exit codes: [verification](../../../en/docs/verification.md).

## 3. Thinking and streaming

GLM-4.7 defaults to thinking. `thinking.type=disabled` turns it off; reasoning appears in reasoning_content. Python examples use extra_body to send the thinking object at the JSON top level. [Thinking mode][thinking] · [Deep thinking](https://docs.bigmodel.cn/cn/guide/capabilities/thinking)

stream true returns delta.content. Use [02_streaming.py](examples/02_streaming.py) and [03_thinking.py](examples/03_thinking.py), with their completion checks. [Chat API][api]

## 4. JSON and tools

JSON Object mode uses `response_format={"type":"json_object"}`; tools declares functions and tool_choice follows the exact model's documented selection scope. See [04_json_output.py](examples/04_json_output.py), [05_tool_calling.py](examples/05_tool_calling.py) and the [API][api].

Applications must parse/validate JSON and tool arguments before execution; this is project safety policy, not a claim that a tool schema alone activates server-side strict mode. [Evidence policy](../../../en/docs/evidence-policy.md) · [Detailed tool/JSON parameters](parameters.en.md)

## 5. Historical and per-file results

The **2026-10-13 legacy smoke report** recorded HTTP 429, including business codes 1302 (account rate limit) and 1305 (excessive model traffic). [Legacy report](verification/2026-10-13.json)

The same day's strict unified verifier used the locked SDK: the basic request timed out, the streaming request still returned 429/1305 after bounded retries, and four later tests were skipped. It had no passed item. This is historical evidence, not the current status of every file, and not proof that the model lacks an official capability. [Strict report](verification/2026-10-13-strict.json) · [Current file status](../../../en/docs/example-status.md)

Project recommendation: bounded exponential backoff with jitter for 429, record persistent rate limits separately, and do not interpret them as unsupported capabilities. [Evidence policy](../../../en/docs/evidence-policy.md)

The shared unified-verifier entry point is `python tests/verify_glm_4_7_flash.py --report /tmp/glm-4.7-flash-verification.json`. It sends real requests; per-file commands and setup are in [verification](../../../en/docs/verification.md). Results remain split between [historical status](../../../en/docs/verification-status.md) and [file status](../../../en/docs/example-status.md).

## 6. Fixed connection configuration

The shared configuration is provider zhipu, exact model glm-4.7-flash, Base URL `https://open.bigmodel.cn/api/paas/v4/`, key variable ZHIPU_API_KEY and explicit thinking-off object `{"thinking":{"type":"disabled"}}` through Python extra_body. Connection configuration does not embed a live success status. [Compatibility][sdk] · [API][api]

[05_tool_calling.py](examples/05_tool_calling.py) includes argument checks, simulated execution, result return and a bounded final-answer loop. Its real execution outcome must come from a matching-source [file report](../../../en/docs/example-status.md), not a historical basic request.

## 7. Pitfalls

429 is not automatically an invalid key or unsupported model. Classify it using HTTP status, business codes and the bounded-retry outcome. The original dated evidence is the [legacy report](verification/2026-10-13.json); general handling is in [production pitfalls](../../../en/docs/production-pitfalls.md). See [parameters](parameters.en.md) before adding thinking retention, strict tools, schema output or other models' fields.

[api]: https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8
[sdk]: https://docs.bigmodel.cn/cn/guide/develop/openai/introduction
[pricing]: https://docs.bigmodel.cn/cn/guide/start/pricing
[thinking]: https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode
