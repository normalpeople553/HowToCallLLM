# 逐文件执行报告

中文 · [English](README.en.md)

这里保存 [逐文件执行器](../tests/run_example_files.py) 的真实厂商 API 尝试；不保存密钥、请求消息、响应正文、思考原文或原始错误。当前哪些文件具有完整有效证据，以[示例实测状态](../docs/示例实测状态.md)为准，而不是把历史报告中的 `passed` 逐条相加。

报告保留每次尝试，正常新增执行不覆盖已有结果。执行时间和耗时已按[隐私规则](../docs/来源与核验规则.md#实测时间最小化项目规则)移除，以随机 `evidence_id` 关联证据；旧路径及 Git 历史未改。`source_sha256` 绑定实际示例及支持依赖，`requests` 记录真实 HTTP 元数据，`exit_code` 记录原文件执行结果。一次通过只覆盖该次执行、型号、参数和输入分支，不保证未来可用、输出总是正确、全部可选输入分支或任意新生成组合都通过。[执行与判定实现](../tests/run_example_files.py) · [文件级来源规则](../docs/来源与核验规则.md)

## 历史报告的判读

- 早期 `attempt1` 使用的旁观器没有解压部分 HTTP 响应，部分 Shell/TypeScript 记录也只有原文件退出结果。虽然原脚本确实执行了，但其中部分 `passed` 缺少完整 HTTP 结束/正文元数据，不能作为当前发布证据。后续 `attempt2` 的部分 `failed` 同样是旁观证据不足，不代表原脚本或厂商能力失败；原始 `exit_code` 可供区分。[早期 DeepSeek 报告](examples/2026-10-14-deepseek-attempt1.json) · [FIM 补跑记录](examples/2026-10-14-deepseek-fim-attempt2.json)
- 后续报告旁观解压后的统计副本，仍向原 SDK 逐字节交付真实响应；Python、Node、cURL 都要求实际请求元数据。发布检查会用当前规则重新核验旧记录，不能只相信旧的状态字符串。[执行器](../tests/run_example_files.py) · [Node 旁观器](../tests/live_fetch.mjs) · [cURL 旁观器](../tests/live_curl.py) · [发布检查](../tests/check_example_release.py)
- MiniMax 的一次流式执行观察到非空正文、`finish_reason=stop`、用量和实际传输 EOF，但没有 `[DONE]`。这里只记录这次端点行为，不外推成所有请求的协议保证；判定必须有明确正常结束，并确实读尽传输或收到终止事件，不能把“连接关闭”本身当成功。[此次记录](examples/2026-10-14-minimax-stream-attempt4.json) · [判定测试](../tests/test_live_example_runner.py)
- 智谱 HTTP 429 不代表鉴权失败或能力不支持。报告出现的 `1305`，官方定义为该模型当前访问量过大，应稍后再试；`1302` 是账户速率限制，两者不能只凭 429 混为一谈。[官方错误码](https://docs.bigmodel.cn/cn/api/api-code) · [此次流式尝试](examples/2026-10-14-zhipu-stream-attempt3.json)

图片使用执行器生成的纯红 PNG；Kimi 视频使用本地生成的短红色视频；豆包视频选用[官方视频文档](https://docs.volcengine.com/docs/ark/video-understanding?lang=zh)中的公开教学素材。未读取用户私人照片、视频；普通示例的通过不等于图片识别准确率测试。工具函数的数据为示例本地模拟，真实 API 调用不意味着天气、订单或库存也来自真实业务系统。[输入生成实现](../tests/run_example_files.py) · [型号示例目录](../docs/官方示例索引.md)
