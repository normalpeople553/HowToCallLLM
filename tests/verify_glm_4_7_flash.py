"""真实验证 glm-4.7-flash；不输出密钥、回答、思考内容或工具参数。"""

import json
import os
import sys
import time

from openai import OpenAI

from provider_verify import require_content, run_tests, usage_summary


MODEL = "glm-4.7-flash"


def main() -> int:
    key = os.environ.get("ZHIPU_API_KEY")
    if not key:
        print("未设置 ZHIPU_API_KEY；未发送请求。")
        return 2
    client = OpenAI(api_key=key, base_url="https://open.bigmodel.cn/api/paas/v4/", timeout=45, max_retries=0)
    tests = []

    def call(**kwargs):
        for attempt in range(4):
            try:
                return client.chat.completions.create(model=MODEL, **kwargs)
            except Exception as exc:
                if "429" not in str(exc) or attempt == 3:
                    raise
                time.sleep(2 ** attempt)

    def basic():
        r = call(messages=[{"role": "user", "content": "只回复：收到"}], max_tokens=128, extra_body={"thinking": {"type": "disabled"}})
        return f"{usage_summary(r)}, chars={len(require_content(r))}"
    tests.append(("普通调用", basic))

    def streaming():
        stream = call(messages=[{"role": "user", "content": "只回复：流式正常"}], stream=True, max_tokens=128, extra_body={"thinking": {"type": "disabled"}})
        content = "".join(c.choices[0].delta.content or "" for c in stream)
        if not content.strip():
            raise AssertionError("流式正文为空")
        return f"chars={len(content)}"
    tests.append(("流式输出", streaming))

    def thinking_on():
        r = call(messages=[{"role": "user", "content": "9.11 和 9.8 哪个更大？"}], max_tokens=1024, extra_body={"thinking": {"type": "enabled"}})
        answer = require_content(r)
        reasoning = getattr(r.choices[0].message, "reasoning_content", None) or ""
        if not reasoning.strip():
            raise AssertionError("未收到 reasoning_content")
        return f"{usage_summary(r)}, reasoning_chars={len(reasoning)}, answer_chars={len(answer)}"
    tests.append(("开启思考", thinking_on))

    def thinking_off():
        r = call(messages=[{"role": "user", "content": "1+1 等于几？"}], max_tokens=128, extra_body={"thinking": {"type": "disabled"}})
        require_content(r)
        if getattr(r.choices[0].message, "reasoning_content", None):
            raise AssertionError("关闭思考后仍收到 reasoning_content")
        return usage_summary(r)
    tests.append(("关闭思考", thinking_off))

    def json_output():
        r = call(messages=[{"role": "system", "content": "只返回 json：{\"ok\":true}"}, {"role": "user", "content": "返回 ok 为 true 的 json"}], response_format={"type": "json_object"}, max_tokens=128, extra_body={"thinking": {"type": "disabled"}})
        if json.loads(require_content(r)).get("ok") is not True:
            raise AssertionError("JSON 内容不符")
        return usage_summary(r)
    tests.append(("JSON Output", json_output))

    def tool_calling():
        tools = [{"type": "function", "function": {"name": "get_weather", "description": "查询城市天气", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]
        r = call(messages=[{"role": "user", "content": "查询杭州天气"}], tools=tools, tool_choice={"type": "function", "function": {"name": "get_weather"}}, max_tokens=256, extra_body={"thinking": {"type": "disabled"}})
        calls = r.choices[0].message.tool_calls or []
        if not calls or calls[0].function.name != "get_weather":
            raise AssertionError("未收到预期工具调用")
        json.loads(calls[0].function.arguments)
        return f"{usage_summary(r)}, calls={len(calls)}"
    tests.append(("Tool Calling", tool_calling))
    return run_tests(tests)


if __name__ == "__main__":
    sys.exit(main())
