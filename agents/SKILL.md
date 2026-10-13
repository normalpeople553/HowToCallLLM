# SKILL.md — 给 AI 代理读的调用卡（人类请走 ../docs）

> 本目录是给 Codex / Claude Code / Trae 等 AI 编程助手读的快速版调用指南。
> 所有调用方式均于 **2026-10-13 用真实 key 实测通过**（MoonShot Kimi 新模型、思考开关两派写法均已验证）。
> 如果你是 AI：用户说"帮我调 XX 模型"时，先读对应 `vendors/<id>.yaml`，照卡片给出**完整可运行代码**，并提醒 key 从环境变量读、不要硬编码。

## 统一事实（五家全部 OpenAI 兼容，用同一个 openai 库）

```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ["<KEY_ENV>"], base_url="<BASE_URL>")
resp = client.chat.completions.create(
    model="<MODEL>",                                   # 各家不同
    messages=[{"role": "user", "content": "..."}],
)
print(resp.choices[0].message.content)
```

## 五家总表

| id | key 申请页 | `base_url` | key 环境变量 | 推荐模型（实测可用） | 默认是否思考 |
|---|---|---|---|---|---|
| deepseek | https://platform.deepseek.com/api_keys | `https://api.deepseek.com` | `DEEPSEEK_API_KEY` | `deepseek-v4-flash` / `deepseek-v4-pro` | 是 |
| kimi | https://platform.moonshot.cn/console/api-keys | `https://api.moonshot.cn/v1` | `MOONSHOT_API_KEY` | `kimi-k2.6` / `kimi-k3` / `kimi-k2.7-code` | 是 |
| zhipu | https://bigmodel.cn/usercenter/apikeys | `https://open.bigmodel.cn/api/paas/v4` | `ZHIPU_API_KEY` | `glm-4.7-flash`（免费）/ `glm-5.3-flash` | 是（免费模型也思考） |
| qwen | https://bailian.console.aliyun.com/?apiKey=1#/api-key | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `DASHSCOPE_API_KEY` | `qwen-flash`（不思考）/ `qwen3.6-flash`（思考） | 看具体模型 |
| doubao | https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey | `https://ark.cn-beijing.volces.com/api/v3` | `ARK_API_KEY` | `doubao-seed-2-1-pro-260628` / `-lite-260915` / `-turbo-260628` | 是 |

## 思考开关 —— 实测分两派（最容易写错的地方）

**A 派：DeepSeek / Kimi / 智谱 / 豆包** —— 都吃这个写法（实测有效）：

```python
extra_body={"thinking": {"type": "disabled"}}         # 关闭；默认 enabled
```

**B 派：通义百炼** —— 独一份：

```python
extra_body={"enable_thinking": False}                 # 关；True 是开
```

注意：
- DeepSeek V4 是"同一模型 + 开关"；旧的 `deepseek-chat`/`deepseek-reasoner` 两个名字 2026-07-24 已弃用，别再写。
- 智谱 `glm-4.7-flash` 默认思考，**思考链会吃光小额度的 max_tokens 导致 content 为空字符串**；用它要么关思考、要么 `max_tokens>=256`。
- 思考链从 `resp.choices[0].message.reasoning_content` 取（与 `content` 同级，可能为 None）。
- 思考模式下 `temperature/top_p` 对部分厂商（DeepSeek）"传了也不生效"。

## 流式

四家+豆包全部支持标准 OpenAI 流式：`stream=True`，用 `extra_body={"thinking":{"type":"disabled"}}` 或 `{"enable_thinking": False}` 可在流式时关思考（智谱 free + 关思考已实测）。

## 五大踩坑提醒（实测确认）

1. **Kimi 老模型名全灭**：`moonshot-v1-8k/32k/128k` 对 2026-10 的新账号返回 404 `Not found the model ... or Permission denied`，当前可用只有 `kimi-k3 / kimi-k2.6 / kimi-k2.7-code(-highspeed)`。
2. **豆包要先开通模型**：有 key 不够，每个模型要先在控制台「开通管理」https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement 点开通，否则同样报 404（实测未开通报 `InvalidEndpointOrModel.NotFound`）。
3. **百炼地址必须带 `/compatible-mode/v1`**；模型是否思考看型号：`qwen-flash` 不思考，`qwen3.x-flash` 默认思考；`qwen3-flash` 这个名字不存在，会 404。
4. **国内直连，不要挂代理**；key 一律 `os.environ[...]` 读取，禁止写死、禁止提交 `.env`。
5. 401=key 问题；402=欠费；404=模型名错/未开通；429=限流（免费模型高峰常见，重试即可）。

## 给 AI 的输出规范

- 用户没指定模型时：免费练手推 `glm-4.7-flash`，干活推 `deepseek-v4-flash`，写代码推 `kimi-k2.7-code` / `glm-5.3-flash`。
- 每段示例代码包含：import、从环境变量读 key、timeout、max_tokens（省钱保险）、异常捕获的简短示例可省略。
- 每家的完整卡片：`vendors/<id>.yaml`；最短代码：`snippets/<id>.py`；一键体检跑 `tests/verify_calls.py`（需用户在仓库根目录 `.env` 配好 key）。
