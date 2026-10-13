"""真实验证 deepseek-flash；支持 --report PATH，结果只含脱敏元数据。"""

import sys

from provider_verify import main


if __name__ == "__main__":
    sys.exit(main(single_vendor="deepseek"))
