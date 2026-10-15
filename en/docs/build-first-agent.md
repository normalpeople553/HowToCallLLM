# 07 · From one model call to your first Agent

[中文](../../docs/07-从模型调用到第一个Agent.md) · [Human guide](../../human/README.en.md)

This chapter is for readers who can make one model call but have not built an Agent. The goal is not a general-purpose Agent framework. It is to understand and run one minimal tool loop: the user asks about weather, the model decides whether to request a tool, the application validates and executes that tool, and the result goes back to the model for a final answer.

The executable reference is the repository's existing [`05_tool_calling.py`](../../models/deepseek/deepseek-flash/examples/05_tool_calling.py). Its model, fields and tool-message shape come from DeepSeek's official [Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/) and [Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/); compare client usage with the [OpenAI Python SDK](https://github.com/openai/openai-python). This page does not create a second executable call and does not treat other models as automatically compatible.

## 1. Separate a model call from an Agent

A normal model call usually sends `messages`, receives an answer, and ends.

For this chapter, an **Agent** is an application structure: the program repeatedly lets the model choose the next step, permits requests for registered tools, validates and executes those tools in application code, and returns a final result only after a stop condition is met. This is the project's teaching definition, not a vendor-wide standard definition of “Agent.”

The minimum loop has five parts:

| Part | Owner | In this example |
|---|---|---|
| Goal | Developer | A system message requires weather questions to use the tool and identify simulated data |
| Decision | Model | Return final text or request calls through `tool_calls` |
| Tool | Your application | `get_weather(city)` returns fixed teaching data |
| State | Your application | `messages` stores user, assistant and tool messages |
| Boundaries | Your application | Tool allowlist, argument validation, unique IDs, maximum turns and completion checks |

Showing a function description to the model does not execute a local function. In the official tool-call flow, the application reads the requested tool and arguments, performs the actual function, and returns the result with the matching `tool_call_id`. [Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)

## 2. Run the existing complete loop first

From the repository root, follow [verification and reproduction](verification.md) to create an environment and install the locked dependencies. The basic example reads the process environment and does not load `.env` automatically.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
export DEEPSEEK_API_KEY="your key"
python models/deepseek/deepseek-flash/examples/05_tool_calling.py
```

See the [first-call guide](first-call.md) for Windows PowerShell activation and key setup. The final command makes real vendor requests and may incur charges; run it only with an authorized key and environment. The public repository provides source, references and reproduction steps, not the maintainer's execution reports. [Evidence policy](evidence-policy.md)

The weather result is fixed simulated data, not a live weather lookup. A successful run establishes this model/code/input/environment loop only. It does not establish real weather accuracy or transfer automatically to an edited version.

## 3. Read the code in execution order

### Step one: describe the tool to the model

The function description inside `tools` contains:

- `name`: the tool name the model must return;
- `description`: guidance for when to use it;
- `parameters`: a JSON Schema description of arguments;
- `required` and `additionalProperties`: required fields and rejection of undeclared fields.

These fields describe what the model may request. They do not grant computer control, network access or Python execution. DeepSeek currently supports function tools, and tool names must be unique; use the current [Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/) for the full field definition.

### Step two: implement the actual tool in your application

`get_weather(city)` is an ordinary Python function. The model only generates arguments such as `{"city":"Hangzhou"}`. The application decides which function runs, which database it reaches, and whether any side effect is allowed.

Start with a side-effect-free simulated tool. If you replace it with email, payment, deletion, or production-data mutation, add identity, authorization, idempotency and explicit confirmation. Those are project safety recommendations, not capabilities supplied automatically by the model.

### Step three: validate requested calls

Before any execution, the example's `validate_call` checks that:

1. the call type is function;
2. the name is in the allowlist;
3. `tool_call_id` is nonempty and not repeated;
4. arguments parse as JSON;
5. the field set, type, length and control characters match local rules.

Model-generated arguments are untrusted input. JSON Schema helps generation, but the application still validates before real execution; external systems also require business authorization. The example validates the complete batch before running any call, avoiding partial-batch side effects.

### Step four: preserve message history

When the model requests a tool, the program appends the complete assistant message, then appends one `role="tool"` message per result. Each tool message carries the original `tool_call_id` so the model can associate the result with its request. [Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)

When DeepSeek thinking mode is enabled together with `tools`, subsequent requests must also preserve prior `reasoning_content`; the official guide says an incomplete replay can produce HTTP 400. Keeping the complete SDK assistant message avoids manually dropping fields. [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/)

### Step five: loop until completion or a stop

The control flow can be expressed as the following pseudocode. It explains the algorithm and is not another executable API example:

```text
Repeat at most N turns:
    Send messages and tools to the model
    If the model requests tools:
        Validate the whole batch
        Store the complete assistant message
        Run allowed tools and store tool results
        Continue to the next turn
    Otherwise:
        Check normal completion and nonempty text
        Return the final answer
If no completion after N turns: fail and stop
```

The example allows at most six model turns and requires at least one actual tool execution. `max_model_turns` is an application safety boundary, not a model request parameter.

## 4. Why `while True` is not enough

A tool-capable program can affect external systems. Even with successful model requests, an Agent can still fail by:

- repeatedly requesting one tool and increasing cost or side effects;
- producing valid JSON for an operation the user is not authorized to perform;
- retrying after a successful side effect and executing it twice;
- sending sensitive tool output back to the model or logs;
- returning `tool_calls` while the program mistakes empty content for a final answer;
- continuing after a failure with incomplete message history.

A minimum Agent therefore needs a turn or total budget, a tool allowlist, argument and authorization checks, explicit success criteria, a failure-stop path, and duplicate-execution protection for side effects. These are project-level engineering recommendations; a real business system also needs appropriate audit records, timeouts, rate limits and human confirmation.

## 5. Grow the simulated example into your Agent

Expand in this order and test each change separately:

1. **Replace the tool internals**: keep the `get_weather(city)` contract and replace the fixed value with a service you are authorized to call.
2. **Add a second read-only tool**: for example order lookup or retrieval. Give each tool its own allowlist entry and validation; never `eval` model text.
3. **Add business state**: store user identity, session ID and necessary history in your system. `messages` is model context, not a reliable database.
4. **Add side effects**: implement permission and confirmation before send, update or delete operations. Record an auditable business ID instead of trusting model text that says “success.”
5. **Add an Agent framework last**: once tool protocol, message history and stop conditions are clear, a framework may manage the loop. It does not establish exact-model parameters, business authorization or result truth for you.

When changing provider or model, start from the [model directory](../../models/README.en.md) to identify the exact API ID, then read that model's parameters and tool examples. OpenAI-compatible does not mean that thinking fields, tool selection, strict mode or message replay rules are identical. [Compatible-API guide](compatible-api.md)

## 6. Testing order

Split checks into four layers:

| Layer | What can be checked without a model call | What a real request checks |
|---|---|---|
| Tool function | Expected structure for fixed inputs; errors and authorization | External-service account, network and real-data permission |
| Argument validation | Rejection of invalid JSON, unknown tools, missing fields and repeated IDs | Whether real model arguments pass the same validator |
| Agent loop | Constructed assistant/tool messages, branches, turn limits and stops | Whether the model actually requests a tool and returns final text |
| Business result | Local assertions over simulated output | Whether the real result is correct, complete and auditable |

Offline checks do not establish current vendor availability; one real request does not establish reliability for every input. Retest the changed path after modifying prompts, tools, models, parameters or history. [Verification and reproduction](verification.md)

## 7. First-Agent checklist

- [ ] Use the exact model and its official tool-call documentation.
- [ ] Read keys only from environment variables; never print or hard-code them.
- [ ] Use a fixed allowlist of tool names.
- [ ] Parse and validate arguments before execution.
- [ ] Preserve the complete assistant tool call and return the matching `tool_call_id`.
- [ ] Set a maximum turn count, timeout or total budget.
- [ ] Check final termination and nonempty content.
- [ ] Label simulated data instead of presenting it as a real business result.
- [ ] Protect side-effecting tools with authorization, confirmation and deduplication.
- [ ] Revalidate the edited version in an authorized environment.

After this loop works, you understand the central engineering structure of an Agent. The next useful step is to make one real but low-risk tool reliable, then add state, retrieval, authorization and observability gradually.
