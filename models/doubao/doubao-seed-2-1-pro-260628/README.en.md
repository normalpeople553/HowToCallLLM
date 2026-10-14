# `doubao-seed-2-1-pro-260628` API manual

[中文](README.md) · [Human guide](../../../human/README.en.md) · [Parameter reference](parameters.en.md)

English translation of the [Chinese manual](README.md), source-checked there on **2026-10-13**. Code, manifests and reports are shared; original official URLs are preserved, including Chinese pages. Translation does not rerun API verification. Machine facts: [`doubao-seed-2-1-pro-260628.json`](../../../skills/model-manual/references/models/doubao-seed-2-1-pro-260628.json).

Find code/attribution in [sources.json](examples/sources.json) and the [example index](../../../en/docs/example-index.md). Keep [historical unified results](../../../en/docs/verification-status.md) separate from [current file results](../../../en/docs/example-status.md). Results apply only to the recorded source, input, parameters and environment. Fragments, modified requests and arbitrary generated combinations do not inherit passes. [Evidence policy](../../../en/docs/evidence-policy.md)

## 1. Identity and lifecycle

| Item | Recorded value | Source |
|---|---|---|
| Model ID | `doubao-seed-2-1-pro-260628` | [Model list][models] |
| Lifecycle | Listed as a past model; callable in the repository's historical test | [Model list][models]; [Historical report](verification/2026-10-13.json) |
| Base URL | `https://ark.cn-beijing.volces.com/api/v3` | [Online inference API][api] |
| Context | 256K tokens | [Model list][models] |
| Default / maximum output | 4K / 256K tokens | [Model list][models] |
| Documented capabilities | Thinking, multimodal understanding, tools, structured output | [Model list][models] |

The historical callable observation does not replace current file evidence or guarantee future availability. Check the current model list before choosing a long-term default.

## 2. Enable the model and run a basic request

Enable the exact model in the Ark console first. [Model activation](https://docs.volcengine.com/docs/ark/activation-management?lang=zh)

The shared [01_basic.py](examples/01_basic.py) reads ARK_API_KEY and uses the Base URL above. Authentication, direct Model ID use and compatible fields are defined by the [online inference API][api]. From the repository root, after setting ARK_API_KEY:

```bash
python -m pip install -r requirements-lock.txt
python models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py
```

Running files sends real requests and may incur charges. Runtime, reproduction and report boundaries are in [verification](../../../en/docs/verification.md). The executable is shared with the Chinese manual, not a new English script.

## 3. Thinking and streaming

This model defaults to thinking; thinking.type enabled/disabled switches it. Returned reasoning_content follows the model's documented reasoning-output behavior. [Deep thinking][thinking]

Python supplies the thinking object through extra_body; stream true returns delta.content. Use [02_streaming.py](examples/02_streaming.py), [03_thinking.py](examples/03_thinking.py) and the [parameter reference](parameters.en.md), including the distinction between a reasoning summary and original reasoning-token usage. [Online inference][api]

## 4. Structured output and tools

The model list marks structured output supported and recommends json_schema. Keep schemas simple and parse/validate again locally. [Model list][models] · [04_json_output.py](examples/04_json_output.py)

For tools, declare functions in tools, validate arguments, execute in the application and return tool results. [Model list][models] [05_tool_calling.py](examples/05_tool_calling.py) implements bounded simulated weather, matching tool_call_id return and a final answer; it is not live weather. [08_thinking_tools.py](examples/08_thinking_tools.py) retains complete thinking-related assistant fields for the thinking loop.

## 5. Images, video and prices

Image format/limits follow the [online inference API][api] and [model list][models]. The historical strict verifier's image fixture/assertions are recorded in its [report](verification/2026-10-13-strict.json), not inherited by a different current image file.

Use [06_vision.py](examples/06_vision.py) for the implemented image inputs and [09_video.py](examples/09_video.py) for the video URL path. Follow the files' input instructions and inspect [current execution evidence](../../../en/docs/example-status.md).

Prices vary with region, cache and promotions. This manual intentionally does not copy a potentially stale unit price; use [official pricing](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh).

## 6. Lifecycle recommendation

“Past model” does not mean the endpoint immediately stopped accepting requests; the historical repository report shows successful calls. Project recommendation: do not make that observation the sole long-term dependency of a new project. Before release, evaluate an alternative from the [current model list][models] and make the Model ID configurable rather than silently replacing it.

## 7. Fixed configuration and evidence

The shared configuration is provider doubao, exact Model ID above, Base URL above, environment variable ARK_API_KEY and explicit thinking-off object `{"thinking":{"type":"disabled"}}` through extra_body. The original configuration's lifecycle label past_but_callable describes its recorded observation, not a permanent guarantee. [Online inference][api] · [Model list][models]

The [Legacy smoke report](verification/2026-10-13.json) checks only the first tool-call response and image-request format for those features. Strict unified results are in [historical status](../../../en/docs/verification-status.md); original-file runs are in [example status](../../../en/docs/example-status.md).

The shared unified-verifier command is `python tests/verify_doubao_seed_2_1_pro.py --report /tmp/doubao-verification.json`; this sends real requests and is not execution of all advanced files. See [verification](../../../en/docs/verification.md) for locked setup and per-file commands.

## 8. Pitfalls

The legacy report's seven recorded passes do not make “still callable” equivalent to “suitable as a long-term default.” [Historical report](verification/2026-10-13.json) · [Model list][models]

Check complete output, thinking budgets, JSON business fields and tool history; distinguish tool strict mode from final-output schema strict mode. Read [parameters](parameters.en.md) and [production pitfalls](../../../en/docs/production-pitfalls.md) for the actual field-level restrictions and project safety checks.

[models]: https://docs.volcengine.com/docs/ark/model-list?lang=zh
[api]: https://docs.volcengine.com/docs/ark/online-inference-standard?lang=zh
[thinking]: https://docs.volcengine.com/docs/ark/deep-thinking?lang=zh
