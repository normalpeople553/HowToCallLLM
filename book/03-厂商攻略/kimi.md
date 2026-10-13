# Kimi（月之暗面）攻略

> 一句话定位：**长文本起家，读长文档/长材料顺手。**
> 📄 国内平台：<https://platform.moonshot.cn/> ｜ 定价：<https://platform.kimi.com/docs/pricing/chat-v1>
> ⚠️ 信息核对于 **2026-10-13**。

---

## 1. 注册与领 key

1. 打开 <https://platform.moonshot.cn/>，手机号注册实名；
2. 「API Key 管理」里创建并复制 `sk-` 开头的 key；
3. 免费额度以平台当期活动为准（历史上新用户常有体验额度），用完按量付费。

```bash
export MOONSHOT_API_KEY="sk-你的key"
```

## 2. 两行关键配置

| 参数 | 值 |
|---|---|
| `base_url`（国内） | `https://api.moonshot.cn/v1` |
| 推荐模型 | `moonshot-v1-8k` |

```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ["MOONSHOT_API_KEY"],
                base_url="https://api.moonshot.cn/v1")
resp = client.chat.completions.create(
    model="moonshot-v1-8k",
    messages=[{"role": "user", "content": "你好"}],
)
print(resp.choices[0].message.content)
```

## 3. 模型怎么选

Kimi 的模型名直接把**上下文长度**写进了名字里。📄 数据来自官方定价页（2026-10 核对），单位元 / 百万 tokens：

| 模型 | 上下文 | 输入 | 输出 | 什么时候用 |
|---|---|---|---|---|
| **`moonshot-v1-8k`** | 8K | 2 | 10 | 日常短问答，**最便宜，新手默认** |
| `moonshot-v1-32k` | 32K | 5 | 20 | 几十页材料 |
| `moonshot-v1-128k` | 128K | 10 | 30 | 整份合同/长报告 |

> 同名加 `-vision-preview` 的是支持图片输入的视觉版，价格与对应文本版一致。第一版我们只讲文本。

**省钱要点**：上下文越长越贵，而且输入是按实际发送量计费。**别为了"配置高"默认选 128k**——短对话用 8k 就够，差价能到 5 倍。

## 4. 新手易踩的坑

- 🌐 国内用 `.cn` 域名直连即可，无需代理；`.ai`（`api.moonshot.ai`）是海外平台，账号/key 不通用，别填混。
- 📛 模型名必须**连上下文后缀**写全：写 `moonshot-v1` 会报模型不存在，要写 `moonshot-v1-8k`。
- 📏 报 context length 超限：换更大的型号（8k→32k→128k），或精简发送内容。
- 🔑 `401` / `402`：同样是 key 或余额问题，对照[报错速查](../05-新手必会与报错速查.md)。

## 5. 适合谁 / 小结

- ✅ 主要诉求是**塞长文档让它总结、问答、抽取**：选它顺手；
- 一般日常短对话，它比 DeepSeek 略贵，新手练手也可先用智谱免费模型。
