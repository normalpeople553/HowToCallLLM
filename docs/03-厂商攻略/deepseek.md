# DeepSeek 攻略

> 一句话定位：**价格屠夫 + 能打，综合最适合新手的第一家。**
> 📄 官方平台：<https://platform.deepseek.com/> ｜ docs：<https://api-docs.deepseek.com/zh-cn/>
> ✅ 本文调用方式于 **2026-10-13 用真实 key 实测通过**，模型名/价格为 V4 时代。

---

## 1. 注册与领 key

1. 打开 <https://platform.deepseek.com/>，手机号注册并完成实名；
2. 左侧「API keys」→「创建 API key」→ 复制 `sk-` 开头那串；
3. 账户余额分「充值余额」和「赠送余额」两种。📄 官方扣费规则：两者并存时**优先扣减赠送余额**（[模型与价格页 · 扣费规则](https://api-docs.deepseek.com/zh-cn/quick_start/pricing)）。赠送余额是否发放、金额多少以控制台显示为准；没有就充 **1～10 元**。

环境变量：

```bash
export DEEPSEEK_API_KEY="sk-你的key"
```

## 2. 两行关键配置

| 参数 | 值 |
|---|---|
| `base_url` | `https://api.deepseek.com`（OpenAI 格式） |
| 推荐模型 | `deepseek-v4-flash` |

```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"],
                base_url="https://api.deepseek.com")
resp = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "你好"}],
)
print(resp.choices[0].message.content)
```

完整可运行版本见 [`../../examples/01_quickstart.py`](../../examples/01_quickstart.py)。

## 3. 模型怎么选

📄 信息全部来自官方[模型与价格页](https://api-docs.deepseek.com/zh-cn/quick_start/pricing)（2026-10 核对）：

| 模型 | 定位 | 上下文 | 输入（缓存未命中/命中） | 输出 |
|---|---|---|---|---|
| **`deepseek-v4-flash`** | 日常首选，便宜快，默认开思考 | 1M | 1 元 / **0.02 元** | 2 元 |
| `deepseek-v4-pro` | 更难的任务，质量更高 | 1M | 3 元 / 0.025 元 | 6 元 |

- 单位：元 / 百万 tokens。
- **上下文 1M**（约合几十万汉字），绝大多数场景完全够用。
- 两个模型都支持 JSON 输出、Tool Calls（函数调用）。

### ⚠️ 注意旧模型名已弃用

官方明确：`deepseek-chat` 和 `deepseek-reasoner` 两个老名字已于 **2026/07/24** 弃用，目前分别映射到 `deepseek-v4-flash` 的非思考 / 思考模式。**新项目直接写新名字。**

## 4. 思考模式（✅ 实测 2026-10-13）

V4 默认"先想再答"，更聪明，但**思考过程也按输出 token 计费**——简单任务建议关闭，更省也更快。

关闭写法（OpenAI SDK 要放进 `extra_body`）：

```python
resp = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "1+1=?"}],
    extra_body={"thinking": {"type": "disabled"}},   # enabled=开（默认）/ disabled=关
)
# 思考链在 resp.choices[0].message.reasoning_content，正式回答在 .content
```

注意：思考模式下 `temperature`、`top_p` 等参数传了也不生效。新手先用默认跑通，日常简单问答再关掉省钱。📄 [官方思考模式文档](https://api-docs.deepseek.com/zh-cn/guides/thinking_mode)。

## 5. 注意事项

- 🌐 **不用挂代理**：国内直连即可，开着 VPN/代理反而可能连接失败。
- 🔑 `401`：key 填错或环境变量没生效（`echo $DEEPSEEK_API_KEY` 检查）。
- 💰 `402`：没余额。去平台控制台确认余额。
- 📛 `Model Not Exist`：模型名写错或用了已弃用的老名字，用第 3 节表格里的名字。
- 🧠 思考模式的输出更费 token，给请求设个 `max_tokens` 控制成本。

## 6. 适合谁 / 小结

- ✅ 想找一家"便宜、强、文档清楚、生态示例多"的主力：选它；
- ✅ 想零成本先练手：换[智谱免费模型](zhipu.md)。
