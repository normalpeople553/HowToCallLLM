"""五家固定型号的一键体检，复用完整验证器的严格判定与脱敏报告。

用法：python tests/verify_calls.py [kimi doubao] [--report NEW_PATH]
密钥从环境变量或仓库根 .env 读取；验证基础调用、流式和关闭思考。
完整 JSON、工具闭环和图片测试请运行各型号 tests/verify_*.py。
退出码：0 所有选定项通过；1 至少一项失败；2 限流/跳过/没有执行。
"""

import sys

from provider_verify import main


if __name__ == "__main__":
    sys.exit(main())
