"""真实验证 kimi-k2.6；支持 --report PATH，结果只含脱敏元数据。"""

import sys

from provider_verify import main


if __name__ == "__main__":
    sys.exit(main(single_vendor="kimi"))
