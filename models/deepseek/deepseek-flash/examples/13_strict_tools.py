"""Beta strict 工具调用：严格 Schema 不等于业务参数正确。

改写自：https://api-docs.deepseek.com/guides/tool_calls/
使用 /beta、function.strict=true、所有属性 required、禁止额外属性。
项目补充：关闭思考，共享 _support.py 的本地业务校验和有界闭环。
天气为教学模拟数据。Beta 功能使用前应重新核对官方文档。
"""

from _support import make_client, weather_loop


def main():
    print(weather_loop(make_client(beta=True), thinking=False, strict=True))


if __name__ == "__main__":
    main()
