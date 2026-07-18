from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable


_TAG_SEGMENT_PATTERN = re.compile(
    r"#\s*(.*?)\s*(?:\((\d+)\))?\s*(?:×|$)",
    re.DOTALL,
)

_TAG_ID_SUFFIX_PATTERN = re.compile(
    r"^(.*?)\s*\((\d+)\)\s*$",
    re.DOTALL,
)



def normalize_keyword(value: Any) -> str:
    return " ".join(
        str(value or "")
        .replace("\u00a0", " ")
        .split()
    ).strip()



def normalize_tag_text(value: Any) -> str:
    normalized = normalize_keyword(value)

    while normalized.startswith("#"):
        normalized = normalized[1:].strip()

    while normalized.endswith("×"):
        normalized = normalized[:-1].strip()

    return normalized



def tag_key(value: Any) -> str:
    """
    태그 비교용 키.

    네이버 태그 검증에서 공백이 제거될 수 있다는 특성을 고려해
    공백을 제거하고 영문은 소문자로 통일한다.
    화면 출력에는 원래 태그명을 보존한다.
    """
    return (
        normalize_tag_text(value)
        .replace(" ", "")
        .casefold()
    )



def parse_tag_cell(value: Any) -> list[dict[str, Any]]:
    """
    최적화가공틀의 검색태그 문자열을 다음 형태로 변환한다.

    # 필기노트 (149380) ×# 오답노트 (382236) ×

    -> [{"text": "필기노트", "code": 149380}, ...]
    """
    raw_text = str(value or "").replace("\u00a0", " ").strip()

    if not raw_text:
        return []

    parsed: list[dict[str, Any]] = []

    for match in _TAG_SEGMENT_PATTERN.finditer(raw_text):
        text = normalize_tag_text(match.group(1))
        code_text = match.group(2)

        if not text:
            continue

        parsed.append(
            {
                "text": text,
                "code": int(code_text) if code_text else None,
            }
        )

    if parsed:
        return deduplicate_tags(parsed)

    # # 또는 × 표기가 없는 과거 자료도 최대한 읽는다.
    fallback_parts = re.split(
        r"[,\n\r;|]+",
        raw_text,
    )

    for part in fallback_parts:
        candidate = normalize_tag_text(part)

        if not candidate:
            continue

        suffix_match = _TAG_ID_SUFFIX_PATTERN.match(candidate)

        if suffix_match:
            text = normalize_tag_text(suffix_match.group(1))
            code_text = suffix_match.group(2)
        else:
            text = candidate
            code_text = None

        if text:
            parsed.append(
                {
                    "text": text,
                    "code": int(code_text) if code_text else None,
                }
            )

    return deduplicate_tags(parsed)



def parse_manual_tag_input(value: Any) -> list[dict[str, Any]]:
    """
    쉼표·줄바꿈·세미콜론 또는 최적화가공틀 형식의 태그를 읽는다.
    """
    raw_text = str(value or "").strip()

    if not raw_text:
        return []

    if "#" in raw_text or "×" in raw_text:
        parsed = parse_tag_cell(raw_text)

        if parsed:
            return parsed

    parts = re.split(
        r"[,\n\r;|]+",
        raw_text,
    )

    parsed: list[dict[str, Any]] = []

    for part in parts:
        candidate = normalize_tag_text(part)

        if not candidate:
            continue

        suffix_match = _TAG_ID_SUFFIX_PATTERN.match(candidate)

        if suffix_match:
            text = normalize_tag_text(suffix_match.group(1))
            code_text = suffix_match.group(2)
        else:
            text = candidate
            code_text = None

        parsed.append(
            {
                "text": text,
                "code": int(code_text) if code_text else None,
            }
        )

    return deduplicate_tags(parsed)



def deduplicate_tags(
    tags: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}

    for tag in tags:
        text = normalize_tag_text(tag.get("text", ""))
        key = tag_key(text)

        if not key:
            continue

        code = tag.get("code")

        if code in ("", None):
            normalized_code = None
        else:
            try:
                normalized_code = int(code)
            except (TypeError, ValueError):
                normalized_code = None

        existing = by_key.get(key)

        if existing is None:
            by_key[key] = {
                "text": text,
                "code": normalized_code,
            }
            continue

        if existing.get("code") is None and normalized_code is not None:
            existing["code"] = normalized_code

    return list(by_key.values())



def stable_fingerprint(data: Any) -> str:
    serialized = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()
