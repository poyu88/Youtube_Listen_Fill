"""YouTube WEBVTT（含逐字時間）解析與練習用分段重建。"""

from __future__ import annotations

import re
from typing import Any

from .srt import tokenize_text

_TIME_RE = re.compile(
    r"(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})[.,](?P<ms>\d{3})"
)
_CUE_HEADER_RE = re.compile(
    r"^(?P<start>\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(?P<end>\d{2}:\d{2}:\d{2}[.,]\d{3})"
)
_KARAOKE_SPLIT_RE = re.compile(r"<(\d{2}:\d{2}:\d{2}\.\d{3})><c>")
_TAG_RE = re.compile(r"</?c>|</?c\s[^>]*>", re.IGNORECASE)
_NOISE_RE = re.compile(r"^\[(?:music|applause|laughter|cheers|silence)\]$", re.IGNORECASE)

# 練習分段：避免過碎／過長
_MAX_WORDS = 12
_MAX_DURATION = 8.0
_GAP_BREAK = 0.9


def _timestamp_to_seconds(value: str) -> float:
    """將 VTT／SRT 時間戳轉換為秒數。"""
    match = _TIME_RE.fullmatch(value.strip())
    if not match:
        raise ValueError(f"無法解析時間戳：{value}")
    hours = int(match.group("h"))
    minutes = int(match.group("m"))
    seconds = int(match.group("s"))
    millis = int(match.group("ms"))
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def _clean_word(text: str) -> str:
    """清理 karaoke 片段中的殘餘標籤與空白。"""
    text = _TAG_RE.sub("", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def _parse_karaoke_line(line: str, cue_start: float) -> list[tuple[float, str]]:
    """
    解析含逐字時間的一行字幕。

    例：hello<00:00:09.800><c> welcome</c><00:00:10.160><c> to</c>
    """
    line = line.strip()
    if not line:
        return []

    if "<c>" not in line and not _KARAOKE_SPLIT_RE.search(line):
        text = _clean_word(line)
        if not text:
            return []
        # 無逐字標記時依空白切開，避免整句被當成一個 token
        return [(cue_start, part) for part in text.split() if part]

    parts = _KARAOKE_SPLIT_RE.split(line)
    words: list[tuple[float, str]] = []

    leading = _clean_word(parts[0])
    if leading:
        # leading 也可能含多詞（少見）
        for part in leading.split():
            words.append((cue_start, part))

    idx = 1
    while idx + 1 < len(parts):
        ts_raw = parts[idx]
        word = _clean_word(parts[idx + 1])
        if word:
            for part in word.split():
                words.append((_timestamp_to_seconds(ts_raw), part))
        idx += 2

    return words


def _iter_youtube_vtt_cues(content: str) -> list[tuple[float, float, list[str]]]:
    """
    逐行解析 YouTube VTT cue。

    注意：cue 內部可能有「只有空白」的列（雙列顯示的上空列），
    不可用 \\n\\s*\\n 切開，否則會讓 karaoke 行與時間軸脫節。
    """
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    cues: list[tuple[float, float, list[str]]] = []
    i = 0

    while i < len(lines):
        raw = lines[i]
        match = _CUE_HEADER_RE.match(raw.strip())
        if not match:
            i += 1
            continue

        start = _timestamp_to_seconds(match.group("start"))
        end = _timestamp_to_seconds(match.group("end"))
        i += 1
        payload: list[str] = []

        while i < len(lines):
            nxt = lines[i]
            # 下一個 cue 時間軸：結束本 cue
            if _CUE_HEADER_RE.match(nxt.strip()):
                break
            # 真正的空行（完全空白）：結束本 cue
            if nxt == "":
                i += 1
                break
            # 只有空白的列：YouTube 雙列字幕的上空列，略過但繼續讀
            if not nxt.strip():
                i += 1
                continue
            # cue 識別碼列（少見）後接時間軸時，交由外層處理
            if "-->" not in nxt and i + 1 < len(lines) and "-->" in lines[i + 1]:
                break
            payload.append(nxt.strip())
            i += 1

        cues.append((start, end, payload))

    return cues


def _extract_words_from_youtube_vtt(content: str) -> list[tuple[float, str]]:
    """
    從 YouTube 自動字幕 VTT 抽出依時間排序的詞序列。

    只取每個 cue 的最後一行（新出現的詞），略過滾動視窗中的重複列。
    """
    collected: list[tuple[float, str]] = []

    for start, end, payload in _iter_youtube_vtt_cues(content):
        # 過渡用極短 cue 多半是整句重印，略過以免重複
        if end - start < 0.02:
            continue
        if not payload:
            continue

        last_line = payload[-1]
        if _NOISE_RE.match(last_line):
            continue
        words = _parse_karaoke_line(last_line, start)
        collected.extend(words)

    collected.sort(key=lambda item: item[0])
    deduped: list[tuple[float, str]] = []
    for start, word in collected:
        if not word or _NOISE_RE.match(word):
            continue
        if deduped:
            prev_start, prev_word = deduped[-1]
            if prev_word.lower() == word.lower() and abs(prev_start - start) < 0.2:
                continue
        deduped.append((start, word))

    # 合併被行寬切斷的連字號詞（english- + speaking → english-speaking）
    merged: list[tuple[float, str]] = []
    i = 0
    while i < len(deduped):
        start, word = deduped[i]
        if word.endswith("-") and i + 1 < len(deduped):
            _, nxt_word = deduped[i + 1]
            merged.append((start, word + nxt_word))
            i += 2
            continue
        merged.append((start, word))
        i += 1

    return merged


def _merge_tiny_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """把過短碎段併入相鄰分段，改善聽打單位。"""
    if not segments:
        return []

    merged: list[dict[str, Any]] = [segments[0].copy()]
    for seg in segments[1:]:
        prev = merged[-1]
        prev_words = prev["text"].split()
        cur_words = seg["text"].split()
        gap = seg["start"] - prev["end"]
        # 單／雙詞碎段，且與前段接近 → 合併
        if len(cur_words) <= 2 and gap <= 1.25 and not prev["text"][-1:] in ".?!":
            prev["text"] = f"{prev['text']} {seg['text']}".strip()
            prev["end"] = max(prev["end"], seg["end"])
            prev["tokens"] = tokenize_text(prev["text"])
            continue
        if len(prev_words) <= 2 and gap <= 1.25 and not prev["text"][-1:] in ".?!":
            prev["text"] = f"{prev['text']} {seg['text']}".strip()
            prev["end"] = max(prev["end"], seg["end"])
            prev["tokens"] = tokenize_text(prev["text"])
            continue
        merged.append(seg.copy())

    for i, seg in enumerate(merged):
        seg["index"] = i
    return merged


def _group_words_into_segments(
    words: list[tuple[float, str]],
) -> list[dict[str, Any]]:
    """將詞序列組成不重疊的練習分段。"""
    if not words:
        return []

    segments: list[dict[str, Any]] = []
    bucket: list[tuple[float, str]] = []

    def flush() -> None:
        nonlocal bucket
        if not bucket:
            return
        text = " ".join(word for _, word in bucket)
        text = re.sub(r"\s+", " ", text).strip()
        if not text or _NOISE_RE.match(text):
            bucket = []
            return
        start = bucket[0][0]
        last_start = bucket[-1][0]
        end = last_start + max(0.6, min(2.5, 0.35 * len(bucket)))
        segments.append(
            {
                "index": len(segments),
                "start": start,
                "end": end,
                "text": text,
                "tokens": tokenize_text(text),
            }
        )
        bucket = []

    for start, word in words:
        if bucket:
            prev_start, prev_word = bucket[-1]
            gap = start - prev_start
            duration = start - bucket[0][0]
            break_here = False
            if gap >= _GAP_BREAK:
                # 桶內詞很少時，中等停頓先不切開，避免留下單字碎段（如 course / loud）
                if len(bucket) <= 2 and gap < 2.0:
                    break_here = False
                else:
                    break_here = True
            elif duration >= _MAX_DURATION:
                break_here = True
            elif len(bucket) >= _MAX_WORDS:
                break_here = True
            elif prev_word[-1:] in ".?!":
                break_here = True

            if break_here:
                flush()

        bucket.append((start, word))

    flush()

    # 先合併碎段（此時 end 尚未被裁切，間隔才有意義）
    segments = _merge_tiny_segments(segments)

    # 再用下一段 start 裁切 end，徹底消除重疊
    for i in range(len(segments) - 1):
        next_start = segments[i + 1]["start"]
        segments[i]["end"] = min(
            segments[i]["end"],
            max(segments[i]["start"] + 0.3, next_start),
        )
        if segments[i]["end"] <= segments[i]["start"]:
            segments[i]["end"] = min(next_start, segments[i]["start"] + 0.4)

    return segments


def parse_vtt(content: str) -> list[dict[str, Any]]:
    """
    解析 WEBVTT 為練習分段。

    對 YouTube 自動字幕會先抽出逐字時間再重組，避免 SRT 滾動視窗造成的重疊與碎句。
    """
    if "<c>" in content or re.search(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", content):
        words = _extract_words_from_youtube_vtt(content)
        return _group_words_into_segments(words)

    # 一般（非 karaoke）VTT：依 cue 解析，並裁切重疊
    segments: list[dict[str, Any]] = []
    for start, end, payload in _iter_youtube_vtt_cues(content):
        text = " ".join(payload)
        text = re.sub(r"<[^>]+>", "", text).strip()
        text = re.sub(r"\s+", " ", text)
        if not text or _NOISE_RE.match(text):
            continue
        segments.append(
            {
                "index": len(segments),
                "start": start,
                "end": end,
                "text": text,
                "tokens": tokenize_text(text),
            }
        )

    for i in range(len(segments) - 1):
        next_start = segments[i + 1]["start"]
        if segments[i]["end"] > next_start:
            segments[i]["end"] = next_start

    return segments
