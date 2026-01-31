#!/usr/bin/env python3
"""Pretendard 폰트를 카드에 필요한 글자만 서브셋하여 base64 Python 모듈로 저장."""

import base64
import os
from fontTools.subset import Subsetter, Options
from fontTools.ttLib import TTFont

# 카드에 등장하는 모든 문자
CHARS = set(
    # 숫자, 기호
    "0123456789.,:회 "
    # 헤더/라벨
    "헌혈기록나의이야총횟수"
    "전장소판기타"
    # 등급명
    "은금명예대최고"
    # 푸터
    "년월일준"
    # 가로형
    "종류별내역"
)

FONTS_DIR = os.path.join(os.path.dirname(__file__), "..", "fonts")

FONT_FILES = {
    "regular": "Pretendard-Regular.woff2",
    "bold": "Pretendard-Bold.woff2",
    "extrabold": "Pretendard-ExtraBold.woff2",
}


def subset_font(input_path, text):
    font = TTFont(input_path)

    options = Options()
    options.flavor = "woff2"
    options.desubroutinize = True

    subsetter = Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)

    tmp_path = input_path + ".subset.woff2"
    font.save(tmp_path)
    font.close()

    with open(tmp_path, "rb") as f:
        data = f.read()
    os.remove(tmp_path)

    return base64.b64encode(data).decode("ascii")


def main():
    text = "".join(CHARS)
    results = {}

    for weight, filename in FONT_FILES.items():
        path = os.path.join(FONTS_DIR, filename)
        print(f"Subsetting {filename}...")
        b64 = subset_font(path, text)
        results[weight] = b64
        # 서브셋 크기 확인
        size_kb = len(base64.b64decode(b64)) / 1024
        print(f"  -> {size_kb:.1f} KB")

    # Python 모듈로 저장
    out_path = os.path.join(os.path.dirname(__file__), "font_data.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('"""Pretendard 서브셋 폰트 (base64 woff2)."""\n\n')
        for weight, b64 in results.items():
            f.write(f'PRETENDARD_{weight.upper()} = (\n')
            # 76자씩 줄바꿈
            for i in range(0, len(b64), 76):
                f.write(f'    "{b64[i:i+76]}"\n')
            f.write(")\n\n")

    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
