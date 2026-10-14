# Human guide: find a working path, understand parameters, read the evidence

[Repository entry](../README.en.md) · [中文](README.md) · [Agent guide](../agents/README.en.md)

This guide is for people making decisions, running examples, or assigning work to an agent—not separate beginner and expert groups. Humans and agents share [model cards](../skills/model-manual/references/models/), executable source, and reports rather than maintaining independent model facts. [Evidence policy](../en/docs/evidence-policy.md)

<a id="reading-path"></a>
## Read for the question you have now

| What you want to do | Start here | What you should establish |
|---|---|---|
| Make your first model call | [First call](../en/docs/first-call.md) | Environment, key, endpoint, model, and runnable file. |
| Use a familiar SDK with another provider | [Compatible-API pattern](../en/docs/compatible-api.md) | Shared structures versus model-specific fields. |
| Discover a provider's other language models | [Six language-model lists](../en/docs/model-lists/README.md) | Exact IDs, current documentation status, official prices and actual repository coverage. |
| Find the exact model's instructions | [Model directory](../models/README.en.md) and the table below | API ID, interface, lifecycle, and official sources. |
| Understand or tune parameters | [Parameters and tuning](../en/docs/parameters.md) | Purpose, defaults/unknowns, budgets, mode-specific effects. |
| Check prices and quotas | [Official cost links](../en/docs/pricing.md) | Rules for the actual account/region, not copied prices. |
| Diagnose a failed request | [Troubleshooting and key safety](../en/docs/troubleshooting.md) | What to retain after redaction and which layer to inspect first. |
| Avoid truncation, empty answers, and tool pitfalls | [Production pitfalls](../en/docs/production-pitfalls.md) | Termination, thinking budgets, complete history, business validation. |
| Find out what was actually tested | [File-level status](../en/docs/example-status.md) and [reproduction](../en/docs/verification.md) | Current source, input, parameters, environment, and report scope. |
| Ask an agent to integrate, migrate, or debug | [Agent guide](../agents/README.en.md) | Supply the business goal and constraints; route to exact-model material. |

Read chapters as needed. The [introduction](../en/docs/introduction.md) explains the structure; there is no requirement to read the whole book first.

## Six models with maintained detailed manuals

These are not the providers' complete inventories. The broader [language-model lists](../en/docs/model-lists/README.md) track official discovery, preview/legacy/alias entries and retirements. Missing manuals or live evidence are explicit; listed models do not automatically use the code below.

This table is a directory, not a quality ranking. “Example highlights” means code collected in the repository—not an exhaustive capability list and not a claim that every example or combination passed. Sources, adaptations, and current scope are in the [example index](../en/docs/example-index.md).

| Exact model | Manual | Parameters and file mapping | Example highlights |
|---|---|---|---|
| `deepseek-flash` | [DeepSeek](../models/deepseek/deepseek-flash/README.en.md) | [Parameters](../models/deepseek/deepseek-flash/parameters.en.md) | [Images/File IDs](../models/deepseek/deepseek-flash/examples/10_vision_files.py), [Responses images](../models/deepseek/deepseek-flash/examples/11_responses_vision.py), [FIM](../models/deepseek/deepseek-flash/examples/15_fim_completion.py). |
| `kimi-k2.6` | [Kimi](../models/kimi/kimi-k2.6/README.en.md) | [Parameters](../models/kimi/kimi-k2.6/parameters.en.md) | [Tool loop preserving reasoning](../models/kimi/kimi-k2.6/examples/08_thinking_tools.py), [local video](../models/kimi/kimi-k2.6/examples/09_video.py). |
| `glm-4.7` | [Zhipu](../models/zhipu/glm-4.7/README.en.md) | [Parameters](../models/zhipu/glm-4.7/parameters.en.md) | [Multi-turn history](../models/zhipu/glm-4.7/examples/06_multi_turn.py), [thinking/tool loop](../models/zhipu/glm-4.7/examples/07_thinking_tools.py). |
| `qwen-flash` | [Qwen](../models/qwen/qwen-flash/README.en.md) | [Parameters](../models/qwen/qwen-flash/parameters.en.md) | [JSON object](../models/qwen/qwen-flash/examples/04_json_output.py), [thinking/tool loop](../models/qwen/qwen-flash/examples/07_thinking_tools.py). |
| `doubao-seed-2-1-pro-260628` | [Doubao](../models/doubao/doubao-seed-2-1-pro-260628/README.en.md) | [Parameters](../models/doubao/doubao-seed-2-1-pro-260628/parameters.en.md) | [Thinking/tool history](../models/doubao/doubao-seed-2-1-pro-260628/examples/08_thinking_tools.py), [implicit-cache observation](../models/doubao/doubao-seed-2-1-pro-260628/examples/10_implicit_cache.py). |
| `MiniMax-M2.7` | [MiniMax](../models/minimax/MiniMax-M2.7/README.en.md) | [Parameters](../models/minimax/MiniMax-M2.7/parameters.en.md) | [Simulated tool loop](../models/minimax/MiniMax-M2.7/examples/05_tool_calling.py), [legacy native cURL](../models/minimax/MiniMax-M2.7/examples/07_native_curl.sh). |

Read identity and lifecycle before calling. An old name remaining callable does not guarantee a fixed served version. MiniMax M2.7 has a retirement/subscription-routing notice; dates and platform distinctions are in its [manual](../models/minimax/MiniMax-M2.7/README.en.md) and the [official notice](https://platform.minimax.cn/docs/guides/models-intro).

## Recommended hands-on sequence

These are project workflow recommendations, not vendor guarantees of model correctness. [Policy and scope](../en/docs/evidence-policy.md)

1. At the repository root, create an isolated Python 3.10+ environment and install locked dependencies. Being able to `import` a package does not establish an identical environment. [Full procedure](../en/docs/verification.md)

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements-lock.txt
   ```

2. Set the exact model's key environment variable. If using `.env`, first confirm Git ignores it and add only the necessary fields. Do not overwrite an existing `.env` with a template or print its contents to check a key. [Key safety](../en/docs/troubleshooting.md#api-key-safety)

3. Select a canonical executable file from the [example index](../en/docs/example-index.md). Read its environment variables, input requirements, and simulated-data notes. Confirm you are authorized to upload any file; running an example can incur charges. [Execution/input policy](../en/docs/verification.md)

4. Read that file's parameter mapping and distinguish these layers. Leave unknowns unknown rather than borrowing from another model or provider. [Parameter guide](../en/docs/parameters.md)

   | Layer | Examples | Where to verify it |
   |---|---|---|
   | SDK / transport | `timeout`, `max_retries`, `extra_body` | Model guide's SDK explanation and pinned version. |
   | Model request | `model`, `messages`, budgets, thinking, `tools` | Exact-model official sources and actual endpoint. |
   | Local acceptance | Loop limits, city/order/SKU rules, JSON business checks | Canonical source and project conventions. |

5. Check termination, nonempty final content, and server business status. JSON also needs parsing/business validation; tools need arguments, IDs, and a complete message loop. HTTP 200 or process exit 0 alone is not the whole check. [Production checks](../en/docs/production-pitfalls.md)

6. After changing a prompt, budget, thinking setting, input, or protocol, retest the changed path. A passing original does not cover arbitrary new combinations. For real evidence, follow [reproduction](../en/docs/verification.md), save a new redacted report, and retain history.

Windows activation, Node/cURL dependencies, video inputs, and real-execution switches are in [verification and reproduction](../en/docs/verification.md). The installation fragment above sends no model request and does not create another API example.

## Which layer was “tested”?

| Evidence | What it establishes | What it does not establish |
|---|---|---|
| Official documentation / model card | Located official parameter/capability support for that exact model. | Success for your account, code, or every task. |
| [Historical unified verification](../en/docs/verification-status.md) | The fixed verifier's test cases and outcomes at the recorded time. | All advanced examples or current source passed. |
| [File-level execution](../en/docs/example-status.md) | Real execution evidence for specified source/dependency fingerprints, parameters, inputs, and environment. | Arbitrary rewrites, generated combinations, or general accuracy. |
| Compilation / offline mocks | Corresponding syntax and simulated boundary checks. | API acceptance or correctness of live business data. |

A card's `verification=null/not_run` can coexist with real executions of independent examples; neither report layer can impersonate the other. Rate limits, missing inputs, and observation gaps do not mean unsupported capability. Use the [evidence policy](../en/docs/evidence-policy.md) and dynamic status page for definitions and current results; this entry does not freeze a passing count.

## Give an agent a concrete goal

You can give a coding agent the following task instruction. It is not a new model API request example:

> Start from this repository's Agent guide and integrate the exact model I specify. Preserve the project's language and dependency conventions. Identify required capabilities, inputs, and parameters, then change the code and run offline checks. Make real calls only within my authorization. Separate official support, existing evidence, checks performed now, and unknowns in the handoff.

For migration, add the source/target models and business behavior that must be preserved. For debugging, provide redacted status codes, termination, and a minimal reproduction—not a complete key. [Agent guide](../agents/README.en.md) · [Troubleshooting](../en/docs/troubleshooting.md)
