"""思考模式 + 工具闭环；完整回传 reasoning_content，不只复制正文。

改写自：https://api-docs.deepseek.com/guides/thinking_mode/
https://api-docs.deepseek.com/guides/tool_calls/
项目补充：共享 _support.py 的允许列表、整批校验和最多六轮限制。
天气为教学模拟数据；不会执行模型生成的代码。
"""

from _support import make_client, weather_loop


def main():
    print(weather_loop(make_client(), thinking=True))


if __name__ == "__main__":
    main()
