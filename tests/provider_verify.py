"""真实 API 验证脚本共享工具；只生成脱敏摘要。"""

import base64
import struct
import zlib


def make_test_png(width: int = 32, height: int = 32) -> str:
    """返回纯红色 PNG 的 data URL，不依赖文件或第三方图片。"""

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    scanlines = b"".join(b"\x00" + b"\xff\x00\x00" * width for _ in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(scanlines))
        + chunk(b"IEND", b"")
    )
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


def require_content(response) -> str:
    content = response.choices[0].message.content or ""
    if not content.strip():
        raise AssertionError("正文为空")
    return content


def usage_summary(response) -> str:
    usage = response.usage
    if not usage:
        return "usage unavailable"
    return f"input={usage.prompt_tokens}, output={usage.completion_tokens}"


def run_tests(tests) -> int:
    failed = 0
    for name, test in tests:
        try:
            detail = test()
            print(f"PASS {name}: {detail}")
        except Exception as exc:
            failed += 1
            message = str(exc).replace("\n", " ")[:180]
            print(f"FAIL {name}: {type(exc).__name__}: {message}")
    print(f"完成：{len(tests) - failed}/{len(tests)} 通过")
    return 1 if failed else 0
