# DeepSeek 攻略

> 一句话定位：**价格屠夫 + 能打，综合最适合新手的第一家。**
> 📄 官方平台：<https://platform.deepseek.com/> ｜ docs：<https://api-docs.deepseek.com/zh-cn/>
> ⚠️ 信息核对于 **2026-10-13**，模型名/价格已更新至 V4 时代。

---

## 1. 注册与领 key

1. 打开 <https://platform.deepseek.com/>，手机号注册并完成实名；
2. 左侧「API keys」→「创建 API key」→ 复制 `sk-` 开头那串；
3. 新账户通常有**赠送余额**（具体金额/活动以充值页显示为准）；没有就充 **1～10 元**。
   - 扣费顺序是**先扣赠送余额，再扣充值余额**，放心用赠送的。

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

官方明确：`deepseek-chat` 和 `deepseek-reasoner` 两个老名字已于 **2026/07/24** 弃用，目前分别映射到 `deepseek-v4-flash` 的非思考 / 思考模式。**新项目直接写新名字**，别再抄网上的老教程。

## 4. 思考模式（2026 新情况）

V4 默认"先想再答"，更聪明但**思考过程也按输出 token 收费**。日常简单问答想省钱/提速，可以按官方[思考模式文档](https://api-docs.deepseek.com/zh-cn/guides/thinking_mode)关掉思考。新手先用默认跑通，不急着调。

## 5. 新手易踩的坑

- 🌐 **不用挂代理**：国内直连最稳，开着 VPN/代理反而可能连接失败。
- 🔑 `401`：key 填错或环境变量没生效（`echo $DEEPSEEK_API_KEY` 检查）。
- 💰 `402`：没余额。去平台看是赠送额度用完还是没充值。
- 📛 `Model Not Exist`：你抄了已弃用或写错的模型名，用表里的新名字。
- 🧠 长时间等待、账单变高：可能是思考模式 + 长 prompt 叠加，设个 `max_tokens`。

## 6. 适合谁 / 小结

- ✅ 想找一家"便宜、强、文档清楚、生态示例多"的主力：选它；
- ✅ 想零成本先练手：可以先吃新用户赠送额度，或换[智谱免费模型](zhipu.md)。
