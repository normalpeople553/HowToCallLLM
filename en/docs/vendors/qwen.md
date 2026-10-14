# Qwen / Alibaba Cloud Model Studio: official-source reference

[中文](../../../docs/03-厂商攻略/qwen.md) · [Human guide](../../../human/README.en.md)

See the [Qwen language-model list](../model-lists/qwen.md) for other exact IDs, lifecycle, input modalities and official pricing. Check region and snapshot restrictions; a listing does not imply a detailed manual or live-call evidence.

Source verification date: **2026-10-13**. Vendor facts follow Alibaba Cloud's official Model Studio documentation; repository testing terminology follows the [evidence policy](../evidence-policy.md).

| Item | Value and official source |
|---|---|
| Key | [`DASHSCOPE_API_KEY`; management page](https://bailian.console.aliyun.com/?apiKey=1#/api-key) |
| `base_url` | [Official regional and Workspace address table](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/) |
| Project default | [`qwen-flash`](https://help.aliyun.com/zh/model-studio/getting-started/models) |
| Models | [Official model list](https://help.aliyun.com/zh/model-studio/getting-started/models) |
| Pricing | [Official pricing](https://help.aliyun.com/zh/model-studio/model-pricing) |
| Free quota | [Official new-user quota rules](https://help.aliyun.com/zh/model-studio/new-free-quota) |

Project examples retain the officially supported legacy address `https://dashscope.aliyuncs.com/compatible-mode/v1`. The documentation currently recommends regional domains containing `WorkspaceId`; new projects should choose from the official table. [Compatible interface and migration guide](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)

Run the shared [01_basic.py](../../../models/qwen/qwen-flash/examples/01_basic.py) for the environment-key, endpoint, `model="qwen-flash"`, and text-`messages` calling pattern. The executable source and its actual prompt are shared between language editions.

```bash
python models/qwen/qwen-flash/examples/01_basic.py
```

For models that support disabling thinking, the Python SDK syntax is `extra_body={"enable_thinking": False}`. The cURL and Node.js field positions differ; follow the official language-specific examples. [OpenAI-compatible documentation](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions/)

Free quotas apply only to the documented regions, models, and periods. Post-quota charging also follows the [official new-user quota rules](https://help.aliyun.com/zh/model-studio/new-free-quota).

Calling files and official attribution: [model manual](../../../models/qwen/qwen-flash/README.en.md) and [sources.json](../../../models/qwen/qwen-flash/examples/sources.json). Execution records stay local. Setup and commands: [reproduction](../verification.md).
