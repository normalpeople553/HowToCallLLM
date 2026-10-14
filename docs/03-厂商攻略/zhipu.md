# 智谱 GLM 官方资料卡

[English](../../en/docs/vendors/zhipu.md)

核对日期：**2026-10-14**。厂商事实以 [智谱开放文档](https://docs.bigmodel.cn/llms.txt)为准；仓库实测口径见[来源与核验规则](../来源与核验规则.md)。

| 项目 | 值与官方来源 |
|---|---|
| Key | [`ZHIPU_API_KEY`；管理页面](https://bigmodel.cn/usercenter/apikeys) |
| `base_url` | [`https://open.bigmodel.cn/api/paas/v4`](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction) |
| 项目默认模型 | [付费 `glm-4.7`](https://docs.bigmodel.cn/cn/guide/start/pricing) |
| 模型与价格 | [官方定价页](https://docs.bigmodel.cn/cn/guide/start/pricing) |
| OpenAI SDK | [官方兼容说明](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction) |
| 思考 | [官方思考模式文档](https://docs.bigmodel.cn/cn/guide/capabilities/thinking) |

完整可运行代码统一使用 [01_basic.py](../../models/zhipu/glm-4.7/examples/01_basic.py)，参数解释见[付费型号参数说明](../../models/zhipu/glm-4.7/parameters.md)。安装锁定依赖并配置 `ZHIPU_API_KEY` 后，在仓库根目录运行：

```bash
python models/zhipu/glm-4.7/examples/01_basic.py
```

项目规则：不再以免费 `glm-4.7-flash` 作为智谱默认，不在付费调用失败后回退免费型号。`glm-4.7` 的价格直接查[官方定价页](https://docs.bigmodel.cn/cn/guide/start/pricing)，不手抄固定数字。[项目选型规则](../来源与核验规则.md)

余额不等于并发额度。智谱 `1302` 表示账户速率限制，`1305` 表示平台服务过载，`1113` 才是账户欠费；付费型号也不能保证不会限流。[官方速率限制](https://docs.bigmodel.cn/cn/api/rate-limit) · [官方错误码](https://docs.bigmodel.cn/cn/api/api-code)

旧免费型号的[2026-10-13 历史报告](../../models/zhipu/glm-4.7-flash/verification/2026-10-13.json)仅作为排错记录保留，不能替代新付费型号的实测。当前准确源码与状态查[付费型号说明书](../../models/zhipu/glm-4.7/README.md)和[逐文件实测状态](../示例实测状态.md)；统一验证器另查[验证状态](../验证状态.md)。不同代际的思考限制须独立核对，不继承 GLM-4.7 配置。[GLM-5.3 Flash 文档](https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5.3-flash)
