"""真实验证 doubao-seed-2-1-pro-260628；支持 --report PATH。"""

import sys

from provider_verify import main


if __name__ == "__main__":
    sys.exit(main(single_vendor="doubao"))
