"""上传图片一次并使用 file_id；IMAGE_PATH / IMAGE_FILE_ID 二选一。

官方来源：https://api-docs.deepseek.com/guides/files_api/
https://api-docs.deepseek.com/guides/vision/
项目补充：新上传文件设置一小时过期，避免永久存储；不会删除已有文件。
上传会把本地图片发送到 DeepSeek。请只使用获准上传的内容。
"""

import os
from pathlib import Path

from _support import completed_text, image_bytes, make_client


def main():
    path, file_id = os.getenv("IMAGE_PATH"), os.getenv("IMAGE_FILE_ID")
    if bool(path) == bool(file_id):
        raise ValueError("请只设置 IMAGE_PATH 或 IMAGE_FILE_ID 中的一个")
    if path:
        image_bytes(path, max_bytes=64 * 1024 * 1024)
    elif not file_id.startswith("file-api-"):
        raise ValueError("IMAGE_FILE_ID 需为 DeepSeek Files API 返回的 file-api-... ID")
    client = make_client()
    if path:
        with Path(path).open("rb") as image:
            uploaded = client.files.create(
                file=image, purpose="user_data",
                expires_after={"anchor": "created_at", "seconds": 3600},
            )
        file_id = uploaded.id
        print(f"已上传：{file_id}（一小时后过期，可在此之前复用）")
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": "请客观描述这张图片。"},
            {"type": "file", "file_id": file_id},
        ]}],
        extra_body={"thinking": {"type": "disabled"}},
    )
    print(completed_text(response))


if __name__ == "__main__":
    main()
