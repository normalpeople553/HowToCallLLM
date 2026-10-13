# Kimi（月之暗面）攻略

> 一句话定位：**长文本与代码能力强的新一代模型；但模型名已换代，老教程全过期了。**
> 📄 国内平台：<https://platform.moonshot.cn/> ｜ 定价：<https://platform.kimi.com/docs/pricing/chat>
> ✅ 本文模型名与调用方式于 **2026-10-13 用真实 key 实测通过**。

---

## 0. 先说最大的坑：moonshot-v1 已经不能用了

网上 90% 的教程还在写 `moonshot-v1-8k`。实测：2026 年的新账号调用它会直接报错：

```text
404 - Not found the model moonshot-v1-8k or Permission denied
```

我们用 API 拉取了账号实际可用的模型，只有这四个：

```text
kimi-k3、kimi-k2.6、kimi-k2.7-code、kimi-k2.7-code-highspeed
```

**新项目请直接用下表的新名字。**

## 1. 注册与领 key

1. 打开 <https://platform.moonshot.cn/>，手机号注册实名；
2. 「API Key 管理」：<https://platform.moonshot.cn/console/api-keys> → 创建 → 复制 `sk-` 开头的 key；
3. 免费额度以平台当期活动为准。

```bash
export MOONSHOT_API_KEY="sk-你的key"
```

## 2. 两行关键配置（✅ 实测）

| 参数 | 值 |
|---|---|
| `base_url`（国内） | `https://api.moonshot.cn/v1` |
| 新手推荐模型 | `kimi-k2.6` |

```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ["MOONSHOT_API_KEY"],
                base_url="https://api.moonshot.cn/v1")
resp = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[{"role": "user", "content": "你好"}],
    extra_body={"thinking": {"type": "disabled"}},   # 可选：关掉思考更省
)
print(resp.choices[0].message.content)
```

## 3. 模型怎么选（✅ 实测可用 / 📄 价格核于 2026-10）

| 模型 | 定位 | 上下文 | 输入（未命中/命中缓存） | 输出 | 实测 |
|---|---|---|---|---|---|
| **`kimi-k2.6`** | 通用对话，文本款里最便宜 | 256K | 6.5 / 1.1 | 27 | ✅ |
| `kimi-k2.7-code` | 写代码专项 | 256K | 6.5 / 1.3 | 27 | 📄 |
| `kimi-k2.7-code-highspeed` | 写代码高速档 | 256K | 13 / 2.6 | 54 | ✅ |
| `kimi-k3` | 旗舰，最强、1M 长上下文 | 1M | 20 / 2 | 100 | ✅ |

单位：元 / 百万 tokens。

选型建议：

- 日常问答：`kimi-k2.6`，默认会思考，简单问题建议 `extra_body` 关思考省钱；
- 让 AI 写代码：`kimi-k2.7-code`（也常被编程工具选为国产后端）；
- 超长文档/最难的任务：`kimi-k3`，但价格是 k2.6 的三倍多，别拿它做小事。

## 4. 思考模式（✅ 实测）

k2.6 / k3 默认都先输出思考链（`reasoning_content`）。关闭：

```python
extra_body={"thinking": {"type": "disabled"}}
```

实测同一道算术题：默认 33 个输出 token（带思考），关闭后只 4 个。

## 5. 新手易踩的坑

- ❌ **`moonshot-v1-8k/32k/128k`**：新账号 404，别再抄老教程。
- 🌐 国内用 `api.moonshot.cn`（`.cn`）；海外站 `api.moonshot.ai`（`.ai`）的账号和 key 不通用。
- 💰 Kimi 现在没有早年那种 ¥2 的便宜档了，纯省钱练手不如[智谱免费模型](zhipu.md)。
- 🔑 `401` key 问题、`429` 限流、连接问题对照[报错速查](../05-新手必会与报错速查.md)。

## 6. 适合谁 / 小结

- ✅ 看重代码能力、长文本质量：值得用；
- 纯入门零成本：先用智谱免费 Flash；日常便宜主力：DeepSeek。
