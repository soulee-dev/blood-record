#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from generate_card import generate_svg

SAMPLES = {
    "default": {"total": 15, "breakdown": {"전혈": 10, "혈장": 2, "혈소판": 3, "혈소판혈장": 0, "기타": 0}},
    "silver":  {"total": 35, "breakdown": {"전혈": 20, "혈장": 5, "혈소판": 8, "혈소판혈장": 2, "기타": 0}},
    "gold":    {"total": 55, "breakdown": {"전혈": 30, "혈장": 10, "혈소판": 12, "혈소판혈장": 3, "기타": 0}},
    "honor":   {"total": 120, "breakdown": {"전혈": 60, "혈장": 20, "혈소판": 30, "혈소판혈장": 10, "기타": 0}},
    "grand":   {"total": 210, "breakdown": {"전혈": 100, "혈장": 40, "혈소판": 50, "혈소판혈장": 15, "기타": 5}},
    "supreme": {"total": 350, "breakdown": {"전혈": 150, "혈장": 70, "혈소판": 80, "혈소판혈장": 40, "기타": 10}},
}


def main():
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    os.makedirs(docs_dir, exist_ok=True)

    for name, data in SAMPLES.items():
        svg = generate_svg(data)
        path = os.path.join(docs_dir, f"{name}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"  {name}.svg ({len(svg) // 1024}KB)")

    print(f"\n{len(SAMPLES)}개 샘플 생성 완료 → docs/")


if __name__ == "__main__":
    main()
