# 智谱 GLM 调用代码与人工核对

[全部代码阅读页](README.md) · [English](zhipu.en.md)

`glm-4.7` · [型号说明书](../../models/zhipu/glm-4.7/README.md) · [逐项参数说明](../../models/zhipu/glm-4.7/parameters.md)

## 运行完整示例

按[锁定环境步骤](../../docs/验证与复现.md)准备环境，在本地设置：`ZHIPU_API_KEY`。

独立示例读取已导出的环境变量，不自动加载 .env；执行下列命令会真实调用并可能计费。

```bash
python models/zhipu/glm-4.7/examples/01_basic.py
```

下面是完整源文件，逐字来自[规范文件](../../models/zhipu/glm-4.7/examples/01_basic.py)：

```python
"""付费 glm-4.7 基础对话；资料核对2026-10-14，不继承Flash历史实测。
官方型号：https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7
兼容接口：https://docs.bigmodel.cn/cn/guide/develop/openai/introduction
用法：设置 ZHIPU_API_KEY 后从仓库根运行本文件。参数解释见 ../parameters.md。
"""

import json
import math
import os
import random
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from openai import OpenAI


def make_client():
    """SDK settings, not model parameters; disable nested SDK retries."""
    return OpenAI(
        api_key=os.environ["ZHIPU_API_KEY"],
        base_url="https://open.bigmodel.cn/api/paas/v4/",
        timeout=120, max_retries=0,
    )


def create_with_backoff(client, **request):
    """Retry only a model HTTP request, never a local tool or consumed stream.

    Official codes: 1302 = rate limit, 1305 = overload. Other 429 codes
    can mean billing, entitlement or quota errors and are not retried here.
    https://docs.bigmodel.cn/cn/api/api-code
    SDK max_retries=0: https://developers.openai.com/api/reference/python#retries
    Three attempts, 1s/2s exponential delays plus <=0.25s jitter are local policy.
    """
    for attempt in range(3):
        try:
            return client.chat.completions.create(**request)
        except Exception as error:
            body = getattr(error, "body", None)
            payload = body.get("error", body) if isinstance(body, dict) else {}
            code = str(payload.get("code", "")) if isinstance(payload, dict) else ""
            if getattr(error, "status_code", None) != 429 or code not in {"1302", "1305"}:
                raise RuntimeError("API 请求失败；请在安全环境检查状态、权限、余额和参数，勿公开原始错误。") from None
            if attempt == 2:
                raise RuntimeError("1302/1305 限流在三次请求后仍未恢复；停止调用。") from None
            delay = 2 ** attempt + random.uniform(0, 0.25)
            headers = getattr(getattr(error, "response", None), "headers", {}) or {}
            retry_after = headers.get("retry-after")
            if retry_after is not None:
                try:
                    wait = float(retry_after)
                except (TypeError, ValueError):
                    try:
                        date = parsedate_to_datetime(retry_after)
                        if date.tzinfo is None:
                            date = date.replace(tzinfo=timezone.utc)
                        wait = (date - datetime.now(timezone.utc)).total_seconds()
                    except (TypeError, ValueError, OverflowError):
                        wait = 0
                if math.isfinite(wait) and wait >= 0:
                    if wait > 30:
                        raise RuntimeError("Retry-After 超过本例30秒等待上限；请稍后重新运行。") from None
                    delay = max(delay, wait)
            time.sleep(delay)
    raise RuntimeError("已达到请求尝试上限")


def completed_message(response):
    choices = getattr(response, "choices", None) or []
    if len(choices) != 1:
        raise RuntimeError("需要且只能有一个候选回答")
    choice = choices[0]
    message = choice.message
    if choice.finish_reason != "stop" or getattr(message, "tool_calls", None):
        raise RuntimeError("回答未正常结束或含未处理工具调用；不要当作完整结果。")
    if not isinstance(message.content, str) or not message.content.strip():
        raise RuntimeError("没有最终正文；请检查思考、生成预算与提示词。")
    return message


def print_usage(response):
    """Print only documented numeric token counts, not arbitrary provider fields."""
    usage = getattr(response, "usage", None)
    stats = {}
    for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = usage.get(name) if isinstance(usage, dict) else getattr(usage, name, None)
        if isinstance(value, int) and not isinstance(value, bool):
            stats[name] = value
    print("usage=" + json.dumps(stats, ensure_ascii=False), file=sys.stderr)


def main():
    client = make_client()
    response = create_with_backoff(
        client, model="glm-4.7",
        messages=[{"role": "user", "content": "用一句话介绍你自己"}],
    )
    print(completed_message(response).content)
    print_usage(response)


if __name__ == "__main__":
    main()
```

## 关键行应该怎么看

- [第 24 行](../../models/zhipu/glm-4.7/examples/01_basic.py#L24)：SDK 自动重试已关闭，本地退避函数负责有限重试；不要叠加两层重试。 [参数依据](../../models/zhipu/glm-4.7/parameters.md)
- [第 28 行](../../models/zhipu/glm-4.7/examples/01_basic.py#L28)：只有 HTTP 429 且业务码为 1302/1305 才进入本例重试，最多三次；不是所有 429 都会稍等即恢复。 [参数依据](../../models/zhipu/glm-4.7/parameters.md)
- [第 97 行](../../models/zhipu/glm-4.7/examples/01_basic.py#L97)：核对付费准确型号 glm-4.7；不能换成免费 Flash 后继承本文件的实测。01 也未显式设置思考开关或输出预算。 [参数依据](../../models/zhipu/glm-4.7/parameters.md)
- [第 70 行](../../models/zhipu/glm-4.7/examples/01_basic.py#L70)：唯一候选、正常结束、无待处理工具、非空正文都要检查；固定脱敏错误不应被改成公开输出完整原始响应。 [参数依据](../../models/zhipu/glm-4.7/parameters.md)

## 运行后应该检查什么

代码把最终正文写到标准输出，把用量写到标准错误流。回答措辞不是固定值，原始报告也刻意不保存回答正文。正常结束、非空正文是验收条件，不证明答案事实准确。抛出异常表示相应检查未通过，不应通过删除校验函数掩盖。

[实际输出与校验逻辑](../../models/zhipu/glm-4.7/examples/01_basic.py) · [证据边界](../../docs/来源与核验规则.md)

## 对应的原始实测证据

当前源码已有通过的真实 HTTP 证据。[原始脱敏报告](../../verification/examples/2026-10-14-zhipu-paid-attempt2.json) · [当前状态](../../docs/示例实测状态.md)

源文件 SHA-256：`ad0906242fa2c9590a4885b4a35fca59fbc40c97baef2e4ce8880a3062664469`

本页是该准确文件的阅读视图，不是又一次线上实测；它不验证 Agent 改写后的代码、任意提示词/参数组合、其他型号或当前账户可用性。

## 官方出处与进阶示例

- [官方出处 1](https://docs.bigmodel.cn/cn/guide/models/text/glm-4.7)
- [官方出处 2](https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8)
- [官方出处 3](https://docs.bigmodel.cn/cn/api/api-code)

[全部参数解释与官方引用](../../models/zhipu/glm-4.7/parameters.md)

- [streaming · 02_streaming.py](../../models/zhipu/glm-4.7/examples/02_streaming.py)
- [thinking · 03_thinking.py](../../models/zhipu/glm-4.7/examples/03_thinking.py)
- [json_object · 04_json_output.py](../../models/zhipu/glm-4.7/examples/04_json_output.py)
- [tool_calling · 05_tool_calling.py](../../models/zhipu/glm-4.7/examples/05_tool_calling.py)
- [multi_turn · 06_multi_turn.py](../../models/zhipu/glm-4.7/examples/06_multi_turn.py)
- [thinking_tool_calling · 07_thinking_tools.py](../../models/zhipu/glm-4.7/examples/07_thinking_tools.py)
