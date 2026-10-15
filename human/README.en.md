# Human guide: learn calls, read code, review implementations

[Repository entry](../README.en.md) · [Model directory](../models/README.en.md) · [Agent integration instructions](../agents/README.en.md) · [中文](README.md)

This guide helps you make calls, understand parameters and code, and review an Agent's implementation. Humans and agents share [model cards](../skills/model-manual/references/models/), calling source; execution records stay local. Check facts and test scope under the [evidence policy](../en/docs/evidence-policy.md).

<a id="reading-path"></a>
## Read for the question you have now

- Learn to call models: [First call](../en/docs/first-call.md) covers the environment, key, endpoint, and run steps; the [compatible-API pattern](../en/docs/compatible-api.md) explains shared structures and model-specific differences.
- Build your first Agent: continue in the standalone [Agent Manual](https://github.com/normalpeople553/HowToBuildAgent) to learn model decisions, tool execution, message history, stop conditions, and safety boundaries.
- Read code and review an Agent: [Code reading and human review](examples/README.en.md) displays complete original Python files, important-line explanations, parameter sources and run instructions, with checklists for streaming, JSON, tools, and images.
- Understand parameters and costs: [Parameters and tuning](../en/docs/parameters.md) explains fields, budgets, and mode effects; [official cost links](../en/docs/pricing.md) lead to pricing and quota references to check for your account and region.
- Debug and avoid pitfalls: [Troubleshooting and key safety](../en/docs/troubleshooting.md) helps retain redacted errors and locate the problem; [production pitfalls](../en/docs/production-pitfalls.md) covers truncation, empty answers, thinking budgets, tool history, and interrupted streams.

Use the [model directory](../models/README.en.md) for each provider's current language models, exact API IDs, manuals, parameters, and feature examples. It distinguishes official listings, maintained manuals and code. Check capabilities and lifecycle in the exact model's material.

Read chapters as needed. The [introduction](../en/docs/introduction.md) explains the structure; there is no requirement to read the whole book first.

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

6. After changing a prompt, budget, thinking setting, input, or protocol, retest the changed path. A passing original does not cover arbitrary new combinations. For real evidence, follow [reproduction](../en/docs/verification.md), keep redacted records locally without publishing the testing process.

Windows activation, Node/cURL dependencies, video inputs, and real-execution switches are in [verification and reproduction](../en/docs/verification.md). The installation fragment above sends no model request and does not create another API example.

## Code and verification boundaries

Official documentation and model cards explain parameters and capabilities; calling code shows implementation. Compilation and offline mocks check syntax and simulated boundaries, not current account-level API success. Maintainer reports, replies, statistics and execution fingerprints stay local and are not displayed here. Reproduce with your own account, inputs and parameters; see [reproduction](../en/docs/verification.md) and [publishing policy](../en/docs/evidence-policy.md).

## Give an agent a concrete goal

You can give a coding agent the following task instruction. It is not a new model API request example:

> Start from this repository's Agent integration instructions and integrate the exact model I specify. Preserve the project's language and dependency conventions. Identify required capabilities, inputs, and parameters, then change the code and run offline checks. Make real calls only within my authorization. Separate official support, existing evidence, checks performed now, and unknowns in the handoff.

For migration, add the source/target models and business behavior that must be preserved. For debugging, provide redacted status codes, termination, and a minimal reproduction—not a complete key. [Agent integration instructions](../agents/README.en.md) · [Troubleshooting](../en/docs/troubleshooting.md)
