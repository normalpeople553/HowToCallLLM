# Official-documentation example index

[中文](../../docs/官方示例索引.md) | English

> Generated from each model's `examples/sources.json`. Update the manifests and regenerate; do not edit this page by hand.

These are project examples adapted from official documentation, not a vendor SDK or a verbatim mirror of official samples. Each manifest records the exact model, official sources, required environment variables, commands and adaptations. Maintainer execution records remain local and are not published with the repository.

## Usage

Install [requirements-lock.txt](../../requirements-lock.txt) from the repository root, then set the required key and inputs. Python examples share the locked environment. TypeScript runtime/SDK requirements are in [package.json](../../package.json); `npm ci` installs the locked SDK. The catalog's `npx tsx` command additionally uses tsx, while the file executor invokes Node directly; see [reproduction](verification.md). cURL examples need curl, bash, and Python. Images and videos are sent to the relevant vendor: use only material you are authorized to upload.

Read the [English model manuals](../../models/README.en.md) and parameter notes before calling a model. Query by capability without sending requests:

```bash
python skills/model-manual/scripts/example_catalog.py --model deepseek-flash --capability text
python skills/model-manual/scripts/example_catalog.py --vendor deepseek --capability vision
python skills/model-manual/scripts/example_catalog.py --model kimi-k2.6 --capability video_input
python skills/model-manual/scripts/example_catalog.py --write-index
python skills/model-manual/scripts/example_catalog.py --check
```

The machine-readable JSON remains in its canonical schema, including the original source metadata. Use `--model` alone to list capability keys. An unknown model or capability exits with code 2 and never falls back to another model; `text`, `chat` and `basic` are search aliases for `chat_completions`; returned capabilities, exact model IDs and verification states remain unchanged. known models include available keys and relevant integration boundaries in the diagnostics. `or` in the environment column means either input is sufficient; the API key is always required. Optional variables are documented in the files.

## Check and record boundaries

- `mock_tested`: a fake SDK checks request construction, message history, and failure handling; it does not prove server acceptance or answer quality.
- `compile_checked`: syntax compilation only. `not_run`: that class of check has not run.
- `live=private`: online records are kept only by the maintainer. This is neither a publicly verifiable pass nor a claim that no test ran. Public lookup does not read local reports.
- `live=not_run`: the manifest explicitly marks the online check as not run. Do not reinterpret unpublished `private` records as this state.
- Complete code and response checks remain public; execution JSON, request records, evidence IDs, source fingerprints and test statistics do not. Check account access, region, official lifecycle and input requirements before running.
- Maintained code does not establish support for every parameter combination, semantic accuracy, visual recognition quality or future availability. Read the model-specific parameter page.

## deepseek · `deepseek-flash`

Sources checked: 2026-10-14. [Canonical sources, commands, and adaptations](../../models/deepseek/deepseek-flash/examples/sources.json). [English model manual](../../models/deepseek/deepseek-flash/README.en.md).

Required reading: [parameter reference and file mapping](../../models/deepseek/deepseek-flash/parameters.en.md).

| Capability / file | Search key | Required environment | Official sources | Offline check / online records |
|---|---|---|---|---|
| [chat_completions · 01_basic.py](../../models/deepseek/deepseek-flash/examples/01_basic.py) | `chat_completions` | DEEPSEEK_API_KEY | [Official source 1](https://api-docs.deepseek.com/api/create-chat-completion/) | mock_tested / private |
| [streaming · 02_streaming.py](../../models/deepseek/deepseek-flash/examples/02_streaming.py) | `streaming` | DEEPSEEK_API_KEY | [Official source 1](https://api-docs.deepseek.com/api/create-chat-completion/) | mock_tested / private |
| [thinking · 03_thinking.py](../../models/deepseek/deepseek-flash/examples/03_thinking.py) | `thinking` | DEEPSEEK_API_KEY | [Official source 1](https://api-docs.deepseek.com/guides/thinking_mode/) | mock_tested / private |
| [json_object · 04_json_output.py](../../models/deepseek/deepseek-flash/examples/04_json_output.py) | `json_object` | DEEPSEEK_API_KEY | [Official source 1](https://api-docs.deepseek.com/guides/json_mode/) | mock_tested / private |
| [tool_calling · 05_tool_calling.py](../../models/deepseek/deepseek-flash/examples/05_tool_calling.py) | `tool_calling` | DEEPSEEK_API_KEY | [Official source 1](https://api-docs.deepseek.com/guides/tool_calls/) | mock_tested / private |
| [vision · 06_vision.py](../../models/deepseek/deepseek-flash/examples/06_vision.py) | `vision` | DEEPSEEK_API_KEY<br>IMAGE_URL  or  IMAGE_PATH | [Official source 1](https://api-docs.deepseek.com/guides/vision/) | mock_tested / private |
| [chat_completions · 07_typescript.ts](../../models/deepseek/deepseek-flash/examples/07_typescript.ts) | `chat_completions` | DEEPSEEK_API_KEY | [Official source 1](https://api-docs.deepseek.com/api/create-chat-completion/) | not_run / private |
| [chat_completions · 08_curl.sh](../../models/deepseek/deepseek-flash/examples/08_curl.sh) | `chat_completions` | DEEPSEEK_API_KEY | [Official source 1](https://api-docs.deepseek.com/api/create-chat-completion/) | mock_tested / private |
| [multi_turn · 09_multi_turn.py](../../models/deepseek/deepseek-flash/examples/09_multi_turn.py) | `multi_turn` | DEEPSEEK_API_KEY | [Official source 1](https://api-docs.deepseek.com/guides/multi_round_chat/) | mock_tested / private |
| [vision_files · 10_vision_files.py](../../models/deepseek/deepseek-flash/examples/10_vision_files.py) | `vision_files` | DEEPSEEK_API_KEY<br>IMAGE_PATH  or  IMAGE_FILE_ID | [Official source 1](https://api-docs.deepseek.com/guides/files_api/) · [Official source 2](https://api-docs.deepseek.com/guides/vision/) | mock_tested / private |
| [responses_vision · 11_responses_vision.py](../../models/deepseek/deepseek-flash/examples/11_responses_vision.py) | `responses_vision` | DEEPSEEK_API_KEY<br>IMAGE_URL  or  IMAGE_PATH | [Official source 1](https://api-docs.deepseek.com/guides/responses_api/) · [Official source 2](https://api-docs.deepseek.com/guides/vision/) · [Official source 3](https://api-docs.deepseek.com/guides/thinking_mode/) | mock_tested / private |
| [thinking_tool_calling · 12_thinking_tools.py](../../models/deepseek/deepseek-flash/examples/12_thinking_tools.py) | `thinking_tool_calling` | DEEPSEEK_API_KEY | [Official source 1](https://api-docs.deepseek.com/guides/thinking_mode/) · [Official source 2](https://api-docs.deepseek.com/guides/tool_calls/) | mock_tested / private |
| [strict_tool_calling · 13_strict_tools.py](../../models/deepseek/deepseek-flash/examples/13_strict_tools.py) | `strict_tool_calling` | DEEPSEEK_API_KEY | [Official source 1](https://api-docs.deepseek.com/guides/tool_calls/) | mock_tested / private |
| [chat_prefix_completion · 14_prefix_completion.py](../../models/deepseek/deepseek-flash/examples/14_prefix_completion.py) | `chat_prefix_completion` | DEEPSEEK_API_KEY | [Official source 1](https://api-docs.deepseek.com/guides/chat_prefix_completion/) | mock_tested / private |
| [fim_completion · 15_fim_completion.py](../../models/deepseek/deepseek-flash/examples/15_fim_completion.py) | `fim_completion` | DEEPSEEK_API_KEY | [Official source 1](https://api-docs.deepseek.com/guides/fim_completion/) | mock_tested / private |

### Integration gaps and model-specific boundaries

A missing example does not establish that the model lacks the capability. These entries are taken from the same source manifest.

- `anthropic_api`: An official compatible endpoint exists. This batch adds neither the anthropic dependency nor an example; that is not a claim of unsupported functionality. [Official source 1](https://api-docs.deepseek.com/guides/vision/)
- `context_caching`: No dedicated cache-observation example was added in this batch. The official cache rules remain authoritative. [Official source 1](https://api-docs.deepseek.com/guides/kv_cache/)

## doubao · `doubao-seed-2-1-pro-260628`

Sources checked: 2026-10-14. [Canonical sources, commands, and adaptations](../../models/doubao/doubao-seed-2-1-pro-260628/examples/sources.json). [English model manual](../../models/doubao/doubao-seed-2-1-pro-260628/README.en.md).

Required reading: [parameter reference and file mapping](../../models/doubao/doubao-seed-2-1-pro-260628/parameters.en.md).

| Capability / file | Search key | Required environment | Official sources | Offline check / online records |
|---|---|---|---|---|
| [chat_completions · 01_basic.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/01_basic.py) | `chat_completions` | ARK_API_KEY | [Official source 1](https://docs.volcengine.com/docs/ark/compatible-with-openai-sdk?lang=zh) · [Official source 2](https://docs.volcengine.com/docs/ark/model-list?lang=zh) | mock_tested / private |
| [streaming · 02_streaming.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/02_streaming.py) | `streaming` | ARK_API_KEY | [Official source 1](https://docs.volcengine.com/docs/ark/streaming-output?lang=zh) · [Official source 2](https://docs.volcengine.com/docs/ark/compatible-with-openai-sdk?lang=zh) | mock_tested / private |
| [thinking · 03_thinking.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/03_thinking.py) | `thinking` | ARK_API_KEY | [Official source 1](https://docs.volcengine.com/docs/ark/deep-thinking?lang=zh) | mock_tested / private |
| [structured_output · 04_json_output.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/04_json_output.py) | `structured_output` | ARK_API_KEY | [Official source 1](https://docs.volcengine.com/docs/ark/structured-output-beta?lang=zh) · [Official source 2](https://docs.volcengine.com/docs/ark/model-list?lang=zh) | mock_tested / private |
| [tool_calling · 05_tool_calling.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/05_tool_calling.py) | `tool_calling` | ARK_API_KEY | [Official source 1](https://docs.volcengine.com/docs/ark/function-calling?lang=zh) · [Official source 2](https://docs.volcengine.com/docs/ark/model-list?lang=zh) | mock_tested / private |
| [vision · 06_vision.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/06_vision.py) | `vision` | ARK_API_KEY<br>IMAGE_URL  or  IMAGE_PATH | [Official source 1](https://docs.volcengine.com/docs/ark/image-understanding?lang=zh) · [Official source 2](https://docs.volcengine.com/docs/ark/model-list?lang=zh) | mock_tested / private |
| [multi_turn · 07_multi_turn.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/07_multi_turn.py) | `multi_turn` | ARK_API_KEY | [Official source 1](https://docs.volcengine.com/docs/ark/context-management?lang=zh) · [Official source 2](https://docs.volcengine.com/docs/ark/text-generation?lang=zh) | mock_tested / private |
| [thinking_tool_calling · 08_thinking_tools.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/08_thinking_tools.py) | `thinking_tool_calling` | ARK_API_KEY | [Official source 1](https://docs.volcengine.com/docs/ark/deep-thinking?lang=zh) · [Official source 2](https://docs.volcengine.com/docs/ark/function-calling?lang=zh) | mock_tested / private |
| [video_input · 09_video.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/09_video.py) | `video_input` | ARK_API_KEY<br>VIDEO_URL | [Official source 1](https://docs.volcengine.com/docs/ark/video-understanding?lang=zh) · [Official source 2](https://docs.volcengine.com/docs/ark/model-list?lang=zh) | mock_tested / private |
| [context_caching · 10_implicit_cache.py](../../models/doubao/doubao-seed-2-1-pro-260628/examples/10_implicit_cache.py) | `context_caching` | ARK_API_KEY | [Official source 1](https://docs.volcengine.com/docs/ark/context-cache?lang=zh) · [Official source 2](https://docs.volcengine.com/docs/ark/model-list?lang=zh) | mock_tested / private |

### Integration gaps and model-specific boundaries

A missing example does not establish that the model lacks the capability. These entries are taken from the same source manifest.

- `explicit_cache`: The official matrix lists Responses API prefix and session caching for this model. This batch uses Chat API and only observes implicit caching without creating resources; explicit cache creation, reuse, expiration, and storage billing are not covered. [Official source 1](https://docs.volcengine.com/docs/ark/context-cache?lang=zh) · [Official source 2](https://docs.volcengine.com/docs/ark/model-list?lang=zh)
- `files_video_preprocessing`: The current Files video tutorial uses version 260915 and model-specific preprocessing settings. Their applicability to 260628 has not been checked individually, so the example only uses video_url.url without an upload. [Official source 1](https://docs.volcengine.com/docs/ark/video-understanding?lang=zh)
- `video_embedded_audio`: This batch covers visual video understanding only. Embedded-audio limits and parameters for this historical model have not been independently verified; a visual-input pass is not an audio-understanding pass. [Official source 1](https://docs.volcengine.com/docs/ark/video-understanding?lang=zh)
- `responses_builtin_tools`: The official matrix lists Responses tools such as web access and MCP for this model. These complete tool examples use local simulated functions through Chat API and do not mix tool schemas from different APIs. [Official source 1](https://docs.volcengine.com/docs/ark/model-list?lang=zh) · [Official source 2](https://docs.volcengine.com/docs/ark/online-content-plugin-guide?lang=zh)

## kimi · `kimi-k2.6`

Sources checked: 2026-10-14. [Canonical sources, commands, and adaptations](../../models/kimi/kimi-k2.6/examples/sources.json). [English model manual](../../models/kimi/kimi-k2.6/README.en.md).

Required reading: [parameter reference and file mapping](../../models/kimi/kimi-k2.6/parameters.en.md).

| Capability / file | Search key | Required environment | Official sources | Offline check / online records |
|---|---|---|---|---|
| [chat_completions · 01_basic.py](../../models/kimi/kimi-k2.6/examples/01_basic.py) | `chat_completions` | MOONSHOT_API_KEY | [Official source 1](https://platform.kimi.com/docs/api/chat) · [Official source 2](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart) | mock_tested / private |
| [streaming · 02_streaming.py](../../models/kimi/kimi-k2.6/examples/02_streaming.py) | `streaming` | MOONSHOT_API_KEY | [Official source 1](https://platform.kimi.com/docs/guide/utilize-the-streaming-output-feature-of-kimi-api) · [Official source 2](https://platform.kimi.com/docs/api/chat) · [Official source 3](https://platform.kimi.com/docs/guide/use-thinking-models) | mock_tested / private |
| [thinking · 03_thinking.py](../../models/kimi/kimi-k2.6/examples/03_thinking.py) | `thinking` | MOONSHOT_API_KEY | [Official source 1](https://platform.kimi.com/docs/guide/use-thinking-models) · [Official source 2](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart) | mock_tested / private |
| [json_object · 04_json_output.py](../../models/kimi/kimi-k2.6/examples/04_json_output.py) | `json_object` | MOONSHOT_API_KEY | [Official source 1](https://platform.kimi.com/docs/guide/use-json-mode-feature-of-kimi-api) · [Official source 2](https://platform.kimi.com/docs/api/chat) | mock_tested / private |
| [tool_calling · 05_tool_calling.py](../../models/kimi/kimi-k2.6/examples/05_tool_calling.py) | `tool_calling` | MOONSHOT_API_KEY | [Official source 1](https://platform.kimi.com/docs/guide/use-kimi-api-to-complete-tool-calls) · [Official source 2](https://platform.kimi.com/docs/guide/use-thinking-models) | mock_tested / private |
| [vision · 06_vision.py](../../models/kimi/kimi-k2.6/examples/06_vision.py) | `vision` | MOONSHOT_API_KEY<br>IMAGE_PATH | [Official source 1](https://platform.kimi.com/docs/guide/use-kimi-vision-model) · [Official source 2](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart) · [Official source 3](https://platform.kimi.com/docs/api/chat) | mock_tested / private |
| [multi_turn · 07_multi_turn.py](../../models/kimi/kimi-k2.6/examples/07_multi_turn.py) | `multi_turn` | MOONSHOT_API_KEY | [Official source 1](https://platform.kimi.com/docs/guide/engage-in-multi-turn-conversations-using-kimi-api) · [Official source 2](https://platform.kimi.com/docs/guide/use-thinking-models) | mock_tested / private |
| [thinking_tool_calling · 08_thinking_tools.py](../../models/kimi/kimi-k2.6/examples/08_thinking_tools.py) | `thinking_tool_calling` | MOONSHOT_API_KEY | [Official source 1](https://platform.kimi.com/docs/guide/use-thinking-models) · [Official source 2](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart) · [Official source 3](https://platform.kimi.com/docs/guide/use-kimi-api-to-complete-tool-calls) | mock_tested / private |
| [video_input · 09_video.py](../../models/kimi/kimi-k2.6/examples/09_video.py) | `video_input` | MOONSHOT_API_KEY<br>VIDEO_PATH | [Official source 1](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart) · [Official source 2](https://platform.kimi.com/docs/guide/use-kimi-vision-model) · [Official source 3](https://platform.kimi.com/docs/api/chat) | mock_tested / private |
| [json_schema · 10_json_schema.py](../../models/kimi/kimi-k2.6/examples/10_json_schema.py) | `json_schema` | MOONSHOT_API_KEY | [Official source 1](https://platform.kimi.com/docs/guide/response_format) · [Official source 2](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart) | mock_tested / private |

### Integration gaps and model-specific boundaries

A missing example does not establish that the model lacks the capability. These entries are taken from the same source manifest.

- `remote_image_url`: The current vision and Chat API documentation lists base64 or ms:// file references and explicitly excludes remote image URLs. Example 06 no longer forwards those URLs directly. [Official source 1](https://platform.kimi.com/docs/guide/use-kimi-vision-model) · [Official source 2](https://platform.kimi.com/docs/api/chat)
- `complex_json_schema_and_partial_mode`: The K2.6 documentation warns that complex $ref/oneOf and Partial Mode combinations may be unstable. This batch includes simple schemas plus application validation, not complex combinations. [Official source 1](https://platform.kimi.com/docs/guide/response_format)
- `builtin_web_search`: The K2.6 page says web-search documentation is being upgraded and discourages current use. Built-in $web_search also has thinking-mode compatibility restrictions, so it is not integrated here. [Official source 1](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart)
- `uploaded_video_file_reference`: Official vision documentation describes uploads and ms:// references. This batch only includes local short MP4/base64 input; file lifecycle and upload-polling workflows are not integrated. [Official source 1](https://platform.kimi.com/docs/guide/use-kimi-vision-model) · [Official source 2](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart)

## minimax · `MiniMax-M2.7`

Sources checked: 2026-10-14. [Canonical sources, commands, and adaptations](../../models/minimax/MiniMax-M2.7/examples/sources.json). [English model manual](../../models/minimax/MiniMax-M2.7/README.en.md).

Required reading: [parameter reference and file mapping](../../models/minimax/MiniMax-M2.7/parameters.en.md).

| Capability / file | Search key | Required environment | Official sources | Offline check / online records |
|---|---|---|---|---|
| [chat_completions · 01_basic.py](../../models/minimax/MiniMax-M2.7/examples/01_basic.py) | `chat_completions` | MINIMAX_API_KEY | [Official source 1](https://platform.minimax.cn/docs/api-reference/text-openai-api) · [Official source 2](https://platform.minimax.cn/docs/api-reference/text-chat-openai) · [Official source 3](https://platform.minimax.cn/docs/guides/models-intro) | mock_tested / private |
| [streaming · 02_streaming.py](../../models/minimax/MiniMax-M2.7/examples/02_streaming.py) | `streaming` | MINIMAX_API_KEY | [Official source 1](https://platform.minimax.cn/docs/api-reference/text-chat-openai) · [Official source 2](https://platform.minimax.cn/docs/api-reference/text-openai-api) · [Official source 3](https://platform.minimax.cn/docs/guides/models-intro) | mock_tested / private |
| [thinking · 03_thinking.py](../../models/minimax/MiniMax-M2.7/examples/03_thinking.py) | `thinking` | MINIMAX_API_KEY | [Official source 1](https://platform.minimax.cn/docs/api-reference/text-chat-openai) · [Official source 2](https://platform.minimax.cn/docs/api-reference/text-openai-api) · [Official source 3](https://platform.minimax.cn/docs/guides/models-intro) | mock_tested / private |
| [tool_calling · 05_tool_calling.py](../../models/minimax/MiniMax-M2.7/examples/05_tool_calling.py) | `tool_calling` | MINIMAX_API_KEY | [Official source 1](https://platform.minimax.cn/docs/api-reference/text-openai-api) · [Official source 2](https://platform.minimax.cn/docs/api-reference/text-chat-openai) · [Official source 3](https://platform.minimax.cn/docs/guides/models-intro) | mock_tested / private |
| [multi_turn · 06_multi_turn.py](../../models/minimax/MiniMax-M2.7/examples/06_multi_turn.py) | `multi_turn` | MINIMAX_API_KEY | [Official source 1](https://platform.minimax.cn/docs/api-reference/text-openai-api) · [Official source 2](https://platform.minimax.cn/docs/api-reference/text-chat-openai) · [Official source 3](https://platform.minimax.cn/docs/guides/models-intro) | mock_tested / private |
| [native_chat_completions · 07_native_curl.sh](../../models/minimax/MiniMax-M2.7/examples/07_native_curl.sh) | `native_chat_completions` | MINIMAX_API_KEY | [Official source 1](https://platform.minimax.cn/docs/api-reference/text-post) · [Official source 2](https://platform.minimax.cn/docs/api-reference/text-openai-api) · [Official source 3](https://platform.minimax.io/docs/api-reference/text-openai-api) · [Official source 4](https://platform.minimax.cn/docs/guides/models-intro) | mock_tested / private |

### Integration gaps and model-specific boundaries

A missing example does not establish that the model lacks the capability. These entries are taken from the same source manifest.

- `json_object`: The hosted native API limits response_format to MiniMax-Text-01; a hosted M2.7 JSON-guarantee parameter is unconfirmed in the OpenAI-compatible API. Self-hosted documentation or a JSON prompt is not treated as hosted JSON Mode support; no 04_json_output.py is created. [Official source 1](https://platform.minimax.cn/docs/api-reference/text-post) · [Official source 2](https://platform.minimax.cn/docs/api-reference/text-chat-openai)
- `json_schema`: Hosted MiniMax-M2.7 response_format/json_schema support is unconfirmed. Native documentation names MiniMax-Text-01 only; support is not inherited from other models or self-hosted APIs. [Official source 1](https://platform.minimax.cn/docs/api-reference/text-post) · [Official source 2](https://platform.minimax.cn/docs/api-reference/text-chat-openai)
- `thinking_off`: Official documentation says M2.x thinking cannot be disabled: disabled is accepted but ignored. reasoning_split only changes output formatting. [Official source 1](https://platform.minimax.cn/docs/api-reference/text-chat-openai) · [Official source 2](https://platform.minimax.cn/docs/api-reference/text-openai-api)
- `reasoning_effort_control`: Current documentation only declares reasoning_effort effective for MiniMax-M3.1-Flash-Preview. M2.7 examples do not add an ineffective thinking-effort control. [Official source 1](https://platform.minimax.cn/docs/api-reference/text-chat-openai)
- `vision`: Current official OpenAI-compatible image input covers MiniMax-M3.1-Flash-Preview and MiniMax-M3. Image input for M2.7 is unconfirmed here; examples from other models are not reused. [Official source 1](https://platform.minimax.cn/docs/api-reference/text-openai-api)
- `video_input`: Current official multimodal-input instructions target the M3 family. This batch does not transplant its video_url protocol to M2.7. [Official source 1](https://platform.minimax.cn/docs/api-reference/text-openai-api)
- `legacy_minimaxi_domain_verification`: Current mainland documentation lists api.minimax.cn and international documentation lists api.minimax.io. The old api.minimaxi.com domain was not live-tested in this batch; no alias-compatibility promise is made. [Official source 1](https://platform.minimax.cn/docs/api-reference/text-post) · [Official source 2](https://platform.minimax.cn/docs/api-reference/text-openai-api) · [Official source 3](https://platform.minimax.io/docs/api-reference/text-openai-api)
- `subscription_alias_identity_after_migration`: The official notice stops new-user M2.7 access on 2026-10-19 and retires its pay-as-you-go API on 2026-11-18. M Plan/Token Plan requests using old names reroute to M3.1 Flash Preview from 2026-10-19. These examples retain the exact model name; rerouted subscription responses are not original-M2.7 test evidence. [Official source 1](https://platform.minimax.cn/docs/guides/models-intro)

## qwen · `qwen-flash`

Sources checked: 2026-10-14. [Canonical sources, commands, and adaptations](../../models/qwen/qwen-flash/examples/sources.json). [English model manual](../../models/qwen/qwen-flash/README.en.md).

Required reading: [parameter reference and file mapping](../../models/qwen/qwen-flash/parameters.en.md).

| Capability / file | Search key | Required environment | Official sources | Offline check / online records |
|---|---|---|---|---|
| [chat_completions · 01_basic.py](../../models/qwen/qwen-flash/examples/01_basic.py) | `chat_completions` | DASHSCOPE_API_KEY | [Official source 1](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions) | mock_tested / private |
| [streaming · 02_streaming.py](../../models/qwen/qwen-flash/examples/02_streaming.py) | `streaming` | DASHSCOPE_API_KEY | [Official source 1](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions) | mock_tested / private |
| [thinking · 03_thinking.py](../../models/qwen/qwen-flash/examples/03_thinking.py) | `thinking` | DASHSCOPE_API_KEY | [Official source 1](https://help.aliyun.com/zh/model-studio/deep-thinking) · [Official source 2](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions) | mock_tested / private |
| [json_object · 04_json_output.py](../../models/qwen/qwen-flash/examples/04_json_output.py) | `json_object` | DASHSCOPE_API_KEY | [Official source 1](https://help.aliyun.com/zh/model-studio/qwen-structured-output) | mock_tested / private |
| [tool_calling · 05_tool_calling.py](../../models/qwen/qwen-flash/examples/05_tool_calling.py) | `tool_calling` | DASHSCOPE_API_KEY | [Official source 1](https://help.aliyun.com/zh/model-studio/qwen-function-calling) | mock_tested / private |
| [multi_turn · 06_multi_turn.py](../../models/qwen/qwen-flash/examples/06_multi_turn.py) | `multi_turn` | DASHSCOPE_API_KEY | [Official source 1](https://help.aliyun.com/zh/model-studio/multi-round-conversation) | mock_tested / private |
| [thinking_tool_calling · 07_thinking_tools.py](../../models/qwen/qwen-flash/examples/07_thinking_tools.py) | `thinking_tool_calling` | DASHSCOPE_API_KEY | [Official source 1](https://help.aliyun.com/zh/model-studio/qwen-function-calling) · [Official source 2](https://help.aliyun.com/zh/model-studio/deep-thinking) · [Official source 3](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions) | mock_tested / private |

### Integration gaps and model-specific boundaries

A missing example does not establish that the model lacks the capability. These entries are taken from the same source manifest.

- `vision`: The official Function Calling matrix lists Qwen-Flash as a text-generation model. Its image input was not verified here; Qwen-VL or newer multimodal examples must not be transplanted. [Official source 1](https://help.aliyun.com/zh/model-studio/qwen-function-calling)
- `preserved_thinking`: The current preserve_thinking support list does not include the older qwen-flash. Thinking-tool examples return complete messages without adding that parameter. [Official source 1](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)
- `max_completion_tokens`: The documented parameter support list starts at Qwen3.5-Flash. It is not directly applied to the older qwen-flash; the examples retain the documented max_tokens answer budget. [Official source 1](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)

## zhipu · `glm-4.7`

Sources checked: 2026-10-14. [Canonical sources, commands, and adaptations](../../models/zhipu/glm-4.7/examples/sources.json). [English model manual](../../models/zhipu/glm-4.7/README.en.md).

Required reading: [parameter reference and file mapping](../../models/zhipu/glm-4.7/parameters.en.md).

| Capability / file | Search key | Required environment | Official sources | Offline check / online records |
|---|---|---|---|---|
| [chat_completions · 01_basic.py](../../models/zhipu/glm-4.7/examples/01_basic.py) | `chat_completions` | ZHIPU_API_KEY | [Official source 1](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7) · [Official source 2](https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8) · [Official source 3](https://docs.bigmodel.cn/cn/api/api-code) | mock_tested / private |
| [streaming · 02_streaming.py](../../models/zhipu/glm-4.7/examples/02_streaming.py) | `streaming` | ZHIPU_API_KEY | [Official source 1](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7) · [Official source 2](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7) · [Official source 3](https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8) · [Official source 4](https://docs.bigmodel.cn/cn/api/api-code) | mock_tested / private |
| [thinking · 03_thinking.py](../../models/zhipu/glm-4.7/examples/03_thinking.py) | `thinking` | ZHIPU_API_KEY | [Official source 1](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7) · [Official source 2](https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode) · [Official source 3](https://docs.bigmodel.cn/cn/api/api-code) | mock_tested / private |
| [json_object · 04_json_output.py](../../models/zhipu/glm-4.7/examples/04_json_output.py) | `json_object` | ZHIPU_API_KEY | [Official source 1](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7) · [Official source 2](https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8) · [Official source 3](https://docs.bigmodel.cn/cn/api/api-code) | mock_tested / private |
| [tool_calling · 05_tool_calling.py](../../models/zhipu/glm-4.7/examples/05_tool_calling.py) | `tool_calling` | ZHIPU_API_KEY | [Official source 1](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7) · [Official source 2](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7) · [Official source 3](https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode) · [Official source 4](https://docs.bigmodel.cn/cn/api/api-code) | mock_tested / private |
| [multi_turn · 06_multi_turn.py](../../models/zhipu/glm-4.7/examples/06_multi_turn.py) | `multi_turn` | ZHIPU_API_KEY | [Official source 1](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7) · [Official source 2](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7) · [Official source 3](https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8) · [Official source 4](https://docs.bigmodel.cn/cn/api/api-code) | mock_tested / private |
| [thinking_tool_calling · 07_thinking_tools.py](../../models/zhipu/glm-4.7/examples/07_thinking_tools.py) | `thinking_tool_calling` | ZHIPU_API_KEY | [Official source 1](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7) · [Official source 2](https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode) · [Official source 3](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7) · [Official source 4](https://docs.bigmodel.cn/cn/api/api-code) | mock_tested / private |

### Integration gaps and model-specific boundaries

A missing example does not establish that the model lacks the capability. These entries are taken from the same source manifest.

- `vision`: The official model page lists text for both input and output modalities. Image examples for GLM vision models must not be transplanted. [Official source 1](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7)
- `context_caching`: The official page lists context caching, but this batch adds no cache-hit observation example. Model-specific usage fields still need checking; two requests do not guarantee a cache hit. [Official source 1](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7)
- `server_json_schema_and_strict_tools`: The current text-request schema lists text/json_object only, and FunctionObject does not list strict. Client-side JSON Schema validation and other vendors' strict-tool capabilities are not transplanted to this model. [Official source 1](https://docs.bigmodel.cn/openapi/openapi.json)
