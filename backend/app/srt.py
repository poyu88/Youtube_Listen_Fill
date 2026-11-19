"""SRT 字幕解析與挖空 token 產生。"""

from __future__ import annotations

import re
from typing import Any


_TIME_RE = re.compile(
    r"(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})[,.](?P<ms>\d{3})"
)


def _timestamp_to_seconds(value: str) -> float:
    """將 SRT 時間戳轉換為秒數。"""
    match = _TIME_RE.fullmatch(value.strip())
    if not match:
        raise ValueError(f"無法解析時間戳：{value}")
    hours = int(match.group("h"))
    minutes = int(match.group("m"))
    seconds = int(match.group("s"))
    millis = int(match.group("ms"))
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def tokenize_text(text: str) -> list[dict[str, str]]:
    """
    將英文字幕拆成挖空用 token。

    letter：需填入的字母；space：空白；punct：標點（不挖空）。
    """
    tokens: list[dict[str, str]] = []
    for char in text:
        if char.isalpha():
            tokens.append({"type": "letter", "value": char})
        elif char.isspace():
            tokens.append({"type": "space", "value": char})
        else:
            tokens.append({"type": "punct", "value": char})
    return tokens


def parse_srt(content: str) -> list[dict[str, Any]]:
    """
    解析 SRT 內容為分段列表。

    每段包含 index、start、end、text 與 tokens。
    """
    normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    blocks = re.split(r"\n\s*\n", normalized)
    segments: list[dict[str, Any]] = []

    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if len(lines) < 2:
            continue

        # 第一行可能是序號；時間軸可能在第一或第二行
        time_line_idx = 0
        if "-->" not in lines[0] and len(lines) >= 2 and "-->" in lines[1]:
            time_line_idx = 1
        if "-->" not in lines[time_line_idx]:
            continue

        start_raw, end_raw = [part.strip() for part in lines[time_line_idx].split("-->")]
        # 去掉可能的定位資訊（如 align:start）
        end_raw = end_raw.split()[0]
        text = " ".join(lines[time_line_idx + 1 :])
        # 移除簡易 HTML 標籤（常見於自動字幕）
        text = re.sub(r"<[^>]+>", "", text).strip()
        if not text:
            continue

        start = _timestamp_to_seconds(start_raw)
        end = _timestamp_to_seconds(end_raw)
        segments.append(
            {
                "index": len(segments),
                "start": start,
                "end": end,
                "text": text,
                "tokens": tokenize_text(text),
            }
        )

    return segments
