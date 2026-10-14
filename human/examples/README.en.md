# Read model calls and review Agent code

[Human guide](../README.en.md) · [中文](README.md)

Choose a model below to read complete, executable Python code with line-linked explanations, parameter references, run commands and original execution evidence. Use it to learn the call and review an Agent's implementation.

Code blocks are copied unchanged from the canonical files in models/, not shortened teaching fragments. Both languages show the same executed code, including its original comments and prompts. Review identity, request semantics and completion checks; variable names and wrappers need not look identical. Changes to model, parameters, inputs or protocol require their own verification.

## Choose a worked example

| Model | Code and review notes |
|---|---|
| `deepseek-flash` | [DeepSeek](deepseek.en.md) |
| `kimi-k2.6` | [Kimi](kimi.en.md) |
| `glm-4.7` | [Zhipu GLM](zhipu.en.md) |
| `qwen-flash` | [Qwen](qwen.en.md) |
| `doubao-seed-2-1-pro-260628` | [Doubao](doubao.en.md) |
| `MiniMax-M2.7` | [MiniMax](minimax.en.md) |

## Before running

Use the locked environment in [verification](../../en/docs/verification.md) and set the listed key environment variable locally. Reading these pages or running the renderer makes no API request; running a Python example calls the provider and may incur charges. A root .env is not automatically loaded by standalone examples. Never publish a key or overwrite an existing .env with a template.

## Human review checklist

Project review criteria: compare these behaviors with the exact model's parameter guide and official sources. No single visual inspection proves production readiness.

1. Identity and safety: verify exact model, API product/region and key variable. No hard-coded or logged secrets, and no silent free-model fallback.
2. Parameters: separate SDK options, model request fields and local application checks. An output budget is not a setting for the context window; omission is not an explicit switch. Verify thinking and budget semantics for that exact model.
3. Results: check normal completion, final content and any provider business status. Thinking-only content, truncation and a pending tool call are not a complete final answer.
4. Evidence: request exact changed files, commands and test scope. Offline mocks, accepted HTTP requests, old-file reports and the Agent's own assertion are different evidence.

[Parameter definitions](../../en/docs/parameters.md) · [Evidence and safety rules](../../en/docs/evidence-policy.md)

## Review advanced behavior

- [Streaming](../../models/zhipu/glm-4.7/examples/02_streaming.py)：Handle empty choices, require normal completion and nonempty content, close in finally, and do not replay after interrupted consumption. [Parameters](../../models/zhipu/glm-4.7/parameters.en.md)
- [JSON](../../models/kimi/kimi-k2.6/examples/04_json_output.py)：Check model-specific response_format and prompting; validate completion before parsing JSON, then check fields, types and application values. [Parameters](../../models/kimi/kimi-k2.6/parameters.en.md)
- [Tool loop](../../models/zhipu/glm-4.7/examples/07_thinking_tools.py)：Validate the entire batch of names, IDs and arguments before allowlisted execution. Return complete assistant history and matching tool_call_id results, bound rounds and obtain a final answer. Inventory data is simulated. [Parameters](../../models/zhipu/glm-4.7/parameters.en.md)
- [Images](../../models/kimi/kimi-k2.6/examples/06_vision.py)：Check the exact model and input format. This example reads local PNG/JPEG into a content array; do not transplant another provider's remote-URL format. Request acceptance does not establish recognition accuracy. [Parameters](../../models/kimi/kimi-k2.6/parameters.en.md)

These links open the existing full files, not generic cross-model templates. Check their current per-file status and input requirements before running; the basic examples' reports do not cover every advanced combination.

[Per-file status](../../en/docs/example-status.md) · [All feature examples](../../en/docs/example-index.md) · [Page renderer](../../scripts/render_human_examples.py)
