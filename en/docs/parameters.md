# Parameters and tuning

[中文](../../docs/参数说明与调参.md) · [Human guide](../../human/README.en.md)

This page routes to six model-specific parameter guides and gives project reading recommendations. It does not maintain another potentially conflicting table of numeric defaults. Each guide explains fields for the **exact model, actual endpoint, and executable example file**. Official semantics link to official sources; project budgets and local checks link to code. [Maintenance policy](evidence-policy.md)

## Read the exact model's guide

| Exact model | Parameter guide and file-by-file mapping | Main topics |
|---|---|---|
| `deepseek-flash` | [DeepSeek parameters](../../models/deepseek/deepseek-flash/parameters.en.md) | Chat versus Responses fields, thinking and budgets, images/File IDs, strict tools, Beta/FIM. |
| `kimi-k2.6` | [Kimi parameters](../../models/kimi/kimi-k2.6/parameters.en.md) | Fixed sampling settings, reasoning history, JSON/Schema, image/video input shapes. |
| `glm-4.7` | [Zhipu parameters](../../models/zhipu/glm-4.7/parameters.en.md) | Paid-model scope, budget defaults, thinking tools, multi-turn history, bounded retries. |
| `qwen-flash` | [Qwen parameters](../../models/qwen/qwen-flash/parameters.en.md) | Sampling/budgets for the old exact model, thinking/JSON combinations, complete tool history. |
| `doubao-seed-2-1-pro-260628` | [Doubao parameters](../../models/doubao/doubao-seed-2-1-pro-260628/parameters.en.md) | Answer/reasoning budgets, strict tools, encrypted reasoning, image/video inputs, cache statistics. |
| `MiniMax-M2.7` | [MiniMax parameters](../../models/minimax/MiniMax-M2.7/parameters.en.md) | M2.7 versus M3, `reasoning_split`, unknown budget semantics, native versus compatible APIs. |

This is a content index, not a claim that every listed feature passed a real API test. Check [file-level execution status](example-status.md) and the corresponding reports. [Evidence policy](evidence-policy.md)

## First identify which layer a field belongs to

This is a project reading order. Return to the exact model page for vendor scope, defaults, and limits; do not copy a field across models merely because its name matches.

| Layer | Questions to answer | Material |
|---|---|---|
| Identity and interface | Which platform/region owns the key? Is `model` an exact ID or alias? Are you calling Chat, Responses, or a native API? | The model guide's identity/interface section; [example index](example-index.md). |
| Model request | How are message roles organized? How do sampling, budgets, thinking, `stream`, `tools`, or `response_format` work for this model? | Model guides and their actual file-by-file request mappings. |
| SDK / transport | Are `timeout`, `max_retries`, and `extra_body` client settings or server generation parameters? | [DeepSeek SDK explanation](../../models/deepseek/deepseek-flash/parameters.en.md), [MiniMax SDK explanation](../../models/minimax/MiniMax-M2.7/parameters.en.md), [official OpenAI Python SDK](https://developers.openai.com/api/reference/python). |
| Local safety and acceptance | Where are loop limits, allowed cities/orders/SKUs, simulated data, and JSON business checks enforced? | Actual example source; [production pitfalls](production-pitfalls.md). |
| Response and evidence | What did `finish_reason`, `usage`, and business status actually return? Do source fingerprints and parameters still match? | [File-level status](example-status.md), [verification and reproduction](verification.md). |

## Project recommendation: change one thing at a time

1. Choose the exact model and endpoint, then read that file's parameter mapping. Leave unknown defaults or semantics unknown; do not fill them with values from a newer model or another vendor. [Policy](evidence-policy.md)
2. First run the example's original request. Then adjust the prompt, output budget, thinking configuration, or sampling for the task. Recheck termination and answer content after each change; the previous result is not proof of the new parameters. [Reproduction](verification.md)
3. `temperature` and `top_p` describe sampling, not an “accuracy percentage.” Some models fix or ignore sampling fields. Check the exact model before deciding whether tuning is possible; “more varied” does not mean “more correct.” [DeepSeek sampling](../../models/deepseek/deepseek-flash/parameters.en.md) · [Kimi parameters](../../models/kimi/kimi-k2.6/parameters.en.md)
4. Plan the context window separately from a single generation budget. For `length`, empty content, or missing termination, inspect actual usage and mode first. A larger budget is not a universal fix. [DeepSeek budgets](../../models/deepseek/deepseek-flash/parameters.en.md) · [MiniMax budgets](../../models/minimax/MiniMax-M2.7/parameters.en.md) · [Production checks](production-pitfalls.md)
5. For machine-consumed results, explicitly select the supported JSON/Schema or tool protocol and validate locally. Low temperature is not a substitute for output structure and business validation. [Example index](example-index.md) · [Tool/JSON checks](production-pitfalls.md)

## Parameter documentation is not a passing test

Read evidence separately. [Historical unified verification](verification-status.md) covers only its named test cases; [file-level execution](example-status.md) covers one run of specified source, parameters, inputs, and environment. A successful ordinary request does not prove images, strict Schema, a tool loop, or another parameter combination. Exit code 0 alone cannot establish model-wide capability. [Evidence policy](evidence-policy.md)

Explanatory Markdown snippets and arbitrary generator outputs do not automatically enter file-level passing coverage. After changing source, inputs, or parameters, [rerun the relevant path](verification.md). Preserve earlier reports alongside the new one; an edit date or explanation cannot replace network evidence.
