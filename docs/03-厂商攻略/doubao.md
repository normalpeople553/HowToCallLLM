# 豆包（火山方舟）攻略

> 一句话定位：**字节旗下，模型阵容最全（还托管 DeepSeek/Kimi/GLM），但开通流程最绕。**
> 📄 方舟控制台：<https://console.volcengine.com/ark> ｜ 价格：<https://docs.volcengine.com/docs/ark/model-pricing?lang=zh>
> ✅ 本文调用方式于 **2026-10-13 用真实 key 实测通过**。

---

## 0. 先说最大的坑：有 key 不等于能调，模型要单独"开通"

实测：拿着有效的 API Key 直接调一个没开通的模型，报的不是"没权限"，而是 **404**：

```text
InvalidEndpointOrModel.NotFound: The model or endpoint doubao-xxx does not exist or you do not have access to it.
```

所以豆包的正确顺序是：**注册实名 → 开通模型 → 拿 key → 调用**，中间那步千万别跳。

## 1. 注册、开通模型、领 key（三步）

1. 打开火山引擎 <https://www.volcengine.com/> 注册，完成**个人实名认证**；
2. 进入火山方舟，到「开通管理」**开通你要用的模型**：
   <https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement>
   （新手勾一个 `Doubao-Seed-2.1-pro` 或 lite 即可，新用户一般有免费 token 额度）
3. 到「API Key 管理」创建 key：
   <https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey>

```bash
export ARK_API_KEY="你的方舟key"
```

## 2. 两行关键配置（✅ 实测）

| 参数 | 值 |
|---|---|
| `base_url` | `https://ark.cn-beijing.volces.com/api/v3` |
| 新手模型 | `doubao-seed-2-1-pro-260628` |

```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ["ARK_API_KEY"],
                base_url="https://ark.cn-beijing.volces.com/api/v3")
resp = client.chat.completions.create(
    model="doubao-seed-2-1-pro-260628",                # 注意带日期版本号
    messages=[{"role": "user", "content": "你好"}],
    extra_body={"thinking": {"type": "disabled"}},     # 可选：关思考
    max_tokens=512,
)
print(resp.choices[0].message.content)
```

## 3. 模型怎么选

豆包用 **Model ID 直调**（模型名带日期戳，代表版本），实测以下 2.1 系列均可调（前提已开通）：

| 模型 ID | 定位 | 参考价格（输入/输出，元/百万） | 实测 |
|---|---|---|---|
| **`doubao-seed-2-1-pro-260628`** | 生产级旗舰，编程/Agent/多模态 | 6 / 30 | ✅ |
| `doubao-seed-2-1-turbo-260628` | 速度与成本均衡 | 约 3 / 15 | ✅ |
| `doubao-seed-2-1-lite-260915` | 轻量便宜 | 更低 | ✅ |

> 📄 具体分档价格以[官方价格页](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh)为准。
> 💡 老教程里的"推理接入点 `ep-xxxx`"是早期用法（先建 endpoint 再调），现在 Model ID 直调即可，新手不用建接入点。

## 4. 思考模式（✅ 实测）

seed-2-1 系列默认开思考，关闭方式与 DeepSeek/Kimi/智谱相同：

```python
extra_body={"thinking": {"type": "disabled"}}
```

实测：开启时算术题输出 29 token 且有思考链；关闭后输出 2 token、无思考链。

## 5. 新手易踩的坑

- 🚧 **忘记开通模型 → 404**（最高频，见第 0 节）。
- 📛 模型名带日期戳（`-260628`），新版发布后旧日期可能下线；报 404 先去[模型广场](https://ark.volcengine.com/region:cn-beijing/model)查当前 Model ID，或用一键体检脚本确认。
- 🧩 方舟还**托管 DeepSeek、Kimi、GLM、Qwen 等第三方模型**（在模型列表里都能看到），但同样要逐个开通，且走火山引擎计费。
- 🌐 国内直连，无需代理。

## 6. 适合谁 / 小结

- ✅ 想在一个平台里把各家模型都试一遍、或有字节生态/企业需求：方舟很合适；
- ✅ 要多模态（图、视频）生态：豆包系布局最全；
- 纯文本新手想省事：DeepSeek 注册即用；想零成本：智谱免费 Flash。
