# 智谱 GLM 攻略

> 一句话定位：**有长期免费的 Flash 模型，零成本练手首选。**
> 📄 开放平台：<https://bigmodel.cn/> ｜ 定价：<https://docs.bigmodel.cn/cn/guide/start/pricing>
> ✅ 本文调用方式于 **2026-10-13 用真实 key 实测通过**（当前旗舰已到 GLM-5.3）。

---

## 1. 注册与领 key

1. 打开 <https://bigmodel.cn/>，手机号注册并完成实名认证（**免费模型也要实名**）；
2. 进入控制台「API Keys」创建并复制；
3. 新用户通常有赠送资源包；更关键的是——**GLM-4-Flash 系列模型长期免费**，练手基本不花钱。

```bash
export ZHIPU_API_KEY="你的key"
```

## 2. 两行关键配置

| 参数 | 值 |
|---|---|
| `base_url` | `https://open.bigmodel.cn/api/paas/v4` |
| 免费模型 | `glm-4.7-flash` |

```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ["ZHIPU_API_KEY"],
                base_url="https://open.bigmodel.cn/api/paas/v4")
resp = client.chat.completions.create(
    model="glm-4.7-flash",                                # 免费模型
    messages=[{"role": "user", "content": "你好"}],
    extra_body={"thinking": {"type": "disabled"}},        # 建议新手关掉：免费模型默认也思考
    max_tokens=256,
)
print(resp.choices[0].message.content)
```

> **实测大坑（2026-10-13）**：免费的 `glm-4.7-flash` **默认开启思考**。如果 `max_tokens` 设太小（比如 64），思考链会先把额度用光，导致 `content` 返回**空字符串**——看起来像"模型坏了"。对策二选一：① 加 `extra_body={"thinking": {"type": "disabled"}}` 关思考；② `max_tokens >= 256`。
> 另外免费模型不会出现在 `/models` 列表接口里，但可以直接调用，这是正常的。

## 3. 模型怎么选

📄 数据来自官方[定价页](https://docs.bigmodel.cn/cn/guide/start/pricing)（2026-10 核对），单位元 / 百万 tokens：

| 模型 | 定位 | 输入 | 输出 |
|---|---|---|---|
| **`glm-4.7-flash`** | 免费、轻量、速度快 | **免费** | **免费** |
| `glm-4-flash-250414` | 免费的另一款稳定版 | **免费** | **免费** |
| `glm-z1-flash` | 免费的**推理**模型（会"思考"） | **免费** | **免费** |
| `glm-5.3-flash` | 新一代高性价比，多模态 | 0.8 | 2.8 |
| `glm-5.3` | 当前旗舰，能力最强 | 8 | 28 |

选型建议：

- **学习、做 demo、跑小工具**：直接 `glm-4.7-flash`，白嫖；
- 需要推理/数学/代码但想免费：试 `glm-z1-flash`；
- 免费模型不够用、要更强质量：再上 `glm-5.3-flash`（依旧很便宜）或旗舰 `glm-5.3`。

## 4. 新手易踩的坑

- 🔡 **模型名用小写**：网页上宣传写作 "GLM-4.7-Flash"，代码里填小写 `glm-4.7-flash`。
- 🪪 报鉴权错误先确认已**实名认证**，否则免费模型也调不动。
- 🌍 国内平台是 `open.bigmodel.cn`；`api.z.ai` 是智谱**国际版**，key 不通用，别照抄国外教程。
- 📛 免费模型也有**并发/RPM 限流**（不是无限猛调），学习够用，高并发要付费或提额。
- 🔑 `401` / `402` 等通用错误对照[报错速查](../05-新手必会与报错速查.md)。

## 5. 适合谁 / 小结

- ✅ **完全不想花钱、先把流程跑通**：四家里面它最香，`glm-4.7-flash` 白嫖；
- ✅ 想要免费的推理模型：`glm-z1-flash`；
- 要最强综合能力再考虑付费旗舰，或对比 [DeepSeek](deepseek.md)。
