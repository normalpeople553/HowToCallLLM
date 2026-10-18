# Optional call-llm skill

[中文](../../docs/call-llm-skill.md) · [Skill source](../../skills/call-llm/SKILL.md) · [Agent integration guide](../../agents/README.en.md)

`call-llm` is an installable entry point for this handbook. The user chooses whether to install it. In a software project, an agent using the skill gets integration rules, exact model cards, and examples from the fixed [HowToCallLLM repository](https://github.com/normalpeople553/HowToCallLLM), then changes that project. The skill does not keep another model catalog.

## Install

In an environment supporting Codex Skills, ask the agent:

> Use skill-installer to install `call-llm` from https://github.com/normalpeople553/HowToCallLLM/tree/main/skills/call-llm.

Only the repository's `skills/call-llm` directory is installed. Installation does not create or fill a key file. The internal skill name is `call-llm`, invoked as `$call-llm`; its display name is `call_llm`. Without installation, use the [Agent integration guide](../../agents/README.en.md) directly.

## Shared keyenv

On first use, the skill runs `init` from [`keyenv.py`](../../skills/call-llm/scripts/keyenv.py) and creates `~/.call-llm/keyenv` in the user's home directory. On Windows, the equivalent path is `$HOME\.call-llm\keyenv`. The file starts with empty variable names; fill only the provider keys you need. Existing files are not overwritten.

| Variable | Provider |
|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek |
| `MOONSHOT_API_KEY` | Kimi |
| `ZHIPU_API_KEY` | Zhipu GLM |
| `DASHSCOPE_API_KEY` | Qwen |
| `ARK_API_KEY` | Doubao Ark |
| `DOUBAO_VOICE_API_KEY` | Doubao Voice |
| `MINIMAX_API_KEY` | MiniMax |

Edit one `NAME=value` per line. Run `python <installed-skill-path>/scripts/keyenv.py status` to see which names are set without displaying values. The file lives outside project and Git directories; this repository's [`.gitignore`](../../.gitignore) also excludes an accidentally copied `keyenv`.

`keyenv` is a local plaintext file, not an operating-system credential vault. Use it only in a trusted personal development environment. Remote agents, containers, and deployed services do not automatically receive it; configure their credentials separately.

## Use in a project

In the current project, ask your agent:

> Use `$call-llm` to add a basic DeepSeek text call to this project. Keep its existing language and dependencies, run offline checks first, and show me how to start it.

Project code reads standard environment variables, not a hard-coded home path. To start a local project using the shared `keyenv`:

```powershell
python "$HOME\.codex\skills\call-llm\scripts\keyenv.py" run --key DEEPSEEK_API_KEY -- python app.py
```

```bash
python ~/.codex/skills/call-llm/scripts/keyenv.py run --key DEEPSEEK_API_KEY -- python app.py
```

Replace `app.py` with the project's start command. Only the selected key is injected from `keyenv` into that child process. An existing same-name environment variable takes precedence. Configure variables separately in production. Standalone examples in this repository do not load `keyenv` automatically; launch them through this wrapper as well.

The skill never reads or echoes full key values to the agent. It uses the [model-manual rules](../../skills/model-manual/SKILL.md) for exact IDs, parameters, and examples. Real API calls require user authorization; offline checks and historical example verification are reported separately.
