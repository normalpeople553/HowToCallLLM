"""真实验证付费 glm-4.7；429 有界重试后标记 rate_limited。"""

import sys

from provider_verify import main


if __name__ == "__main__":
    sys.exit(main(single_vendor="zhipu"))
