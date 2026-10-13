# 通义千问（阿里云百炼）攻略

> 一句话定位：**背靠阿里云，新用户免费额度大方，生态/企业集成强。**
> 📄 百炼平台：<https://bailian.console.aliyun.com/> ｜ 模型价格：<https://help.aliyun.com/zh/model-studio/model-pricing>
> ✅ 本文调用方式于 **2026-10-13 用真实 key 实测通过**（当前已到 qwen3.8 代际）。

---

## 1. 注册与领 key

1. 登录阿里云，进入**百炼大模型服务平台** <https://bailian.console.aliyun.com/>；
2. 完成阿里云**实名认证**（个人实名即可）；
3. 在控制台「API-KEY 管理」里创建 key（以 `sk-` 开头）；
4. 留意**新用户免费额度**：百炼对新用户提供免费试用额度，📄 规则见官方[免费额度说明](https://help.aliyun.com/zh/model-studio/)，注意额度**有有效期、可能限定地域**，拿到尽快试。

```bash
export DASHSCOPE_API_KEY="sk-你的key"
```

## 2. 两行关键配置

| 参数 | 值 |
|---|---|
| `base_url`（OpenAI 兼容模式） | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| 新手模型 | `qwen-flash`（或当期 `qwen3.x-flash`） |

```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"],
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
resp = client.chat.completions.create(
    model="qwen-flash",
    messages=[{"role": "user", "content": "你好"}],
)
print(resp.choices[0].message.content)
```

## 3. 模型怎么选

📄 百炼模型更新很快，名字带代际号，官方[模型列表](https://help.aliyun.com/zh/model-studio/getting-started/models)为准。截至核对日的家族大致是：

| 家族 | 示例模型 | 定位 |
|---|---|---|
| Max | `qwen3.8-max`、`qwen-max` | 旗舰，最强也最贵 |
| Plus | `qwen3.6-plus`、`qwen-plus` | 质量与成本均衡 |
| **Flash** | `qwen3.6-flash`、`qwen-flash` | **快、便宜，常带免费额度，新手默认** |
| Turbo | `qwen-turbo` | 老牌便宜款 |
| Long | `qwen-long` | 超长文本场景 |

💡 不带具体版本号的别名（如 `qwen-flash`、`qwen-plus`、`qwen-max`）通常会**自动指向当前稳定版本**，新手用别名最省心，不用每次跟版本号；想锁死版本再写全 `qwen3.6-flash` 这种全名。

## 4. 新手易踩的坑

- 🧩 **必须走"兼容模式"地址**：`base_url` 里的 `/compatible-mode/v1` 一段不能漏；老的 DashScope 原生接口参数风格不同，网上新旧教程混着，认准兼容模式。
- 🧠 **思考开关百炼独一份**：别的四家是 `extra_body={"thinking":{"type":"disabled"}}`，百炼是 `extra_body={"enable_thinking": False}`（✅ 实测：`qwen3.6-flash` 默认开思考、有 500+ 字思考链，关掉后输出只有 2 token）。
- 📛 **没有 `qwen3-flash` 这个模型**（实测 404）：要思考款就写带版本号的 `qwen3.6-flash` 这类全名；不思考的日常款直接用别名 `qwen-flash`。
- 🪪 需要阿里云账号 + **实名**，并确认对应模型服务已开通（首次在控制台点一下开通/同意协议）。
- ⏳ **免费额度有有效期和地域限制**，跨地域可能无法抵扣；想防止超额扣费，可在控制台开启"仅免费额度"模式（额度用完即停）。
- 🌐 国内直连，无需代理。

## 5. 适合谁 / 小结

- ✅ 已经在用阿里云、或未来要做企业/云上部署：生态衔接最好；
- ✅ 想靠**新用户免费额度**比较系统地试一圈模型：合适；
- 纯个人学习想长期白嫖：[智谱免费 Flash](zhipu.md) 更无压力；追求极致便宜主力：[DeepSeek](deepseek.md)。
