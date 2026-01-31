#!/usr/bin/env python3

import io
import json
import sys
from datetime import datetime, timezone, timedelta


CARD_WIDTH = 380
CARD_HEIGHT = 580

KST = timezone(timedelta(hours=9))

# 횟수별 등급 테마 (ref.png 유공패 색상 기반)
# (최소횟수, 등급명, 상단 그라디언트 시작, 상단 그라디언트 끝, 액센트색, 바 그라디언트 끝)
TIERS = [
    (300, "최고명예대장", "#1A1A2E", "#0F3460", "#E94560", "#E94560"),
    (200, "명예대장",     "#C41E3A", "#A01830", "#C41E3A", "#E85D75"),
    (100, "명예장",       "#1B3A6B", "#102A50", "#2E5EA6", "#5B8BD4"),
    (50,  "금장",         "#B8860B", "#8B6914", "#B8860B", "#D4A843"),
    (30,  "은장",         "#8C8C8C", "#6B6B6B", "#8C8C8C", "#AAAAAA"),
    (0,   "",             "#9E5A63", "#7A4049", "#9E5A63", "#C47A84"),
]


def get_tier(total):
    for min_count, name, top1, top2, accent, bar_end in TIERS:
        if total >= min_count:
            return {
                "name": name,
                "top1": top1, "top2": top2,
                "accent": accent, "bar_end": bar_end,
            }
    return TIERS[-1]


SVG_TEMPLATE = """\
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="top-bg" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:{top1}"/>
      <stop offset="100%" style="stop-color:{top2}"/>
    </linearGradient>
    <linearGradient id="body-bg" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#F8F6F3"/>
      <stop offset="100%" style="stop-color:#EEEAE4"/>
    </linearGradient>
    <linearGradient id="bar-fill" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{accent}"/>
      <stop offset="100%" style="stop-color:{bar_end}"/>
    </linearGradient>
    <filter id="shadow" x="-5%" y="-3%" width="110%" height="110%">
      <feDropShadow dx="0" dy="2" stdDeviation="6" flood-color="#00000022"/>
    </filter>
  </defs>

  <!-- 카드 외곽 -->
  <rect x="10" y="10" width="{inner_w}" height="{inner_h}" rx="12" fill="url(#body-bg)" filter="url(#shadow)"/>

  <!-- 상단 컬러 영역 -->
  <rect x="10" y="10" width="{inner_w}" height="160" rx="12" fill="url(#top-bg)"/>
  <rect x="10" y="100" width="{inner_w}" height="70" fill="url(#top-bg)"/>

  <!-- 십자가 심볼 -->
  <rect x="{cross_cx_h}" y="38" width="60" height="20" rx="4" fill="#FFFFFF" opacity="0.9"/>
  <rect x="{cross_cx_v}" y="18" width="20" height="60" rx="4" fill="#FFFFFF" opacity="0.9"/>

  <!-- 헌혈 기록 타이틀 -->
  <text x="{cx}" y="115" text-anchor="middle"
        font-family="'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif" font-size="13" font-weight="400"
        fill="rgba(255,255,255,0.7)" letter-spacing="6">헌혈 기록</text>
  <text x="{cx}" y="155" text-anchor="middle"
        font-family="'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif" font-size="15"
        fill="rgba(255,255,255,0.6)" letter-spacing="2">{tier_label}</text>

  <!-- 총 헌혈 횟수 -->
  <text x="{cx}" y="225" text-anchor="middle"
        font-family="'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif" font-size="14" font-weight="400"
        fill="#888">총 헌혈 횟수</text>
  <text x="{cx}" y="280" text-anchor="middle"
        font-family="'Segoe UI', 'Malgun Gothic', sans-serif" font-size="64" font-weight="800"
        fill="{accent}">{total}</text>
  <text x="{total_suffix_x}" y="280" text-anchor="start"
        font-family="'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif" font-size="18" font-weight="400"
        fill="{accent}">회</text>

  <!-- 구분선 -->
  <line x1="50" y1="305" x2="{line_x2}" y2="305" stroke="#D6D0C8" stroke-width="1"/>

  <!-- 종류별 내역 -->
{bars}

  <!-- 날짜 -->
  <line x1="50" y1="{footer_line_y}" x2="{line_x2}" y2="{footer_line_y}" stroke="#D6D0C8" stroke-width="1"/>
  <text x="{cx}" y="{footer_y}" text-anchor="middle"
        font-family="'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif" font-size="11"
        fill="#AAA">{date} 기준</text>
</svg>"""

BAR_TEMPLATE = """\
  <text x="50" y="{label_y}" font-family="'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif"
        font-size="13" fill="#555">{label}</text>
  <text x="{value_x}" y="{label_y}" text-anchor="end"
        font-family="'Segoe UI', 'Malgun Gothic', sans-serif" font-size="13" font-weight="700"
        fill="#333">{count}회</text>
  <rect x="50" y="{bar_y}" width="{bar_max}" height="10" rx="5" fill="#E8E2DA"/>
  <rect x="50" y="{bar_y}" width="{fill_width}" height="10" rx="5" fill="url(#bar-fill)"/>"""


def generate_svg(data):
    total = data["total"]
    breakdown = data["breakdown"]
    tier = get_tier(total)

    max_count = max(breakdown.values()) if breakdown.values() else 1
    if max_count == 0:
        max_count = 1

    inner_w = CARD_WIDTH - 20
    cx = CARD_WIDTH // 2
    bar_max = inner_w - 80
    value_x = inner_w - 30 + 10

    digit_width = len(str(total)) * 36
    total_suffix_x = cx + digit_width // 2 + 2

    # 등급명이 있으면 표시, 없으면 부제
    tier_label = tier["name"] if tier["name"] else "나의 헌혈 이야기"

    bars_parts = []
    start_y = 330
    row_height = 44

    for i, (label, count) in enumerate(breakdown.items()):
        label_y = start_y + i * row_height
        bar_y = label_y + 8
        fill_width = max(int((count / max_count) * bar_max), 6) if count > 0 else 0
        bars_parts.append(BAR_TEMPLATE.format(
            label=label,
            label_y=label_y,
            bar_y=bar_y,
            bar_max=bar_max,
            fill_width=fill_width,
            count=count,
            value_x=value_x,
        ))

    date_str = datetime.now(KST).strftime("%Y.%m.%d")
    num_categories = len(breakdown)
    footer_line_y = start_y + num_categories * row_height + 15
    footer_y = footer_line_y + 25

    card_height = max(CARD_HEIGHT, footer_y + 25)
    inner_h = card_height - 20

    return SVG_TEMPLATE.format(
        width=CARD_WIDTH,
        height=card_height,
        inner_w=inner_w,
        inner_h=inner_h,
        cx=cx,
        cross_cx_h=cx - 30,
        cross_cx_v=cx - 10,
        total=total,
        total_suffix_x=total_suffix_x,
        tier_label=tier_label,
        bars="\n".join(bars_parts),
        date=date_str,
        line_x2=inner_w - 30 + 10,
        footer_line_y=footer_line_y,
        footer_y=footer_y,
        top1=tier["top1"],
        top2=tier["top2"],
        accent=tier["accent"],
        bar_end=tier["bar_end"],
    )


def main():
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    raw = sys.stdin.read().strip()
    if not raw:
        print("Error: No JSON input provided on stdin.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(raw)
    svg = generate_svg(data)

    output_path = "output/blood-card.svg"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Card generated: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
