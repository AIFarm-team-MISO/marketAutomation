from __future__ import annotations

from collections import defaultdict
from typing import Any

from utils.global_logger import logger

from keywordObservation.keyword_relationship_store import (
    resolve_keyword_scope,
)
from keywordObservation.manual_tag_store import (
    find_manual_tag_usage,
)
from keywordObservation.optimization_record_store import (
    find_optimization_records,
)
from keywordObservation.tag_observation_store import (
    find_latest_tag_observation,
)
from keywordObservation.tag_registry_builder import (
    load_tag_registry,
)
from keywordObservation.tag_text_utils import (
    normalize_keyword,
    normalize_tag_text,
    tag_key,
)



def _log(message: str, level: str = "INFO") -> None:
    logger.log(
        message,
        level=level,
        also_to_report=True,
    )



def _separator(char: str = "-") -> None:
    logger.log_separator(
        char=char,
        level="INFO",
        also_to_report=True,
    )



def _format_tag(
    tag: dict[str, Any],
    *,
    include_rank: bool = False,
) -> str:
    text = normalize_tag_text(tag.get("text", ""))
    code = tag.get("code")
    rank = tag.get("rank")

    prefix = ""
    if include_rank and rank not in (None, ""):
        prefix = f"{rank}. "

    if code in (None, ""):
        return prefix + text

    return prefix + f"{text} (code: {code})"



def print_tag_search_observation(
    observation: dict[str, Any],
) -> None:
    keyword = normalize_keyword(
        observation.get("query_keyword", "")
    )
    observed_at = str(observation.get("observed_at", ""))
    tags = [
        item
        for item in observation.get("tags", [])
        if isinstance(item, dict)
    ]

    exact = [
        tag
        for tag in tags
        if tag.get("match_type") == "exact"
    ]
    related = [
        tag
        for tag in tags
        if tag.get("match_type") != "exact"
    ]

    _separator("=")
    _log(f"🏷️ 네이버 추천 태그 검색결과: '{keyword}'")

    if observed_at:
        _log(f"   └ 조회시각: {observed_at}")

    _log(f"   └ 반환태그: {len(tags)}개")

    _log("\n[정확일치]")
    if exact:
        for tag in exact:
            _log("   " + _format_tag(tag))
    else:
        _log("   없음")

    _log("\n[연관검색]")
    if related:
        for tag in related:
            _log("   " + _format_tag(tag, include_rank=True))
    else:
        _log("   없음")

    _separator("=")



def _collect_keyword_records(keyword: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scope = resolve_keyword_scope(keyword)
    candidates = {
        normalize_keyword(scope.get("input_keyword", "")),
        normalize_keyword(scope.get("canonical_keyword", "")),
        *{
            normalize_keyword(alias)
            for alias in scope.get("aliases", [])
        },
    }
    candidates = {
        candidate.casefold()
        for candidate in candidates
        if candidate
    }

    manual_records: list[dict[str, Any]] = []
    optimization_records: list[dict[str, Any]] = []

    for candidate in candidates:
        manual_records.extend(
            find_manual_tag_usage(candidate)
        )
        optimization_records.extend(
            find_optimization_records(candidate)
        )

    # 동일 레코드 중복 방지
    manual_by_fingerprint = {
        str(record.get("fingerprint", id(record))): record
        for record in manual_records
    }
    optimization_by_fingerprint = {
        str(record.get("fingerprint", id(record))): record
        for record in optimization_records
    }

    return (
        list(manual_by_fingerprint.values()),
        list(optimization_by_fingerprint.values()),
    )



def print_keyword_knowledge(
    keyword: str,
    *,
    manual_tag_limit: int = 30,
    optimization_example_limit: int = 3,
    show_empty_sections: bool = True,
) -> bool:
    normalized_keyword = normalize_keyword(keyword)
    scope = resolve_keyword_scope(normalized_keyword)
    canonical_keyword = normalize_keyword(
        scope.get("canonical_keyword", normalized_keyword)
    ) or normalized_keyword

    tag_observation = (
        find_latest_tag_observation(canonical_keyword)
        or find_latest_tag_observation(normalized_keyword)
    )

    manual_records, optimization_records = _collect_keyword_records(
        normalized_keyword
    )

    has_data = bool(
        tag_observation
        or manual_records
        or optimization_records
    )

    if not has_data and not show_empty_sections:
        return False

    registry_payload = load_tag_registry()
    registry = registry_payload.get("tags", {})

    if not isinstance(registry, dict):
        registry = {}

    _separator("=")
    _log(f"🧩 키워드 지식자료: '{normalized_keyword}'")

    if canonical_keyword != normalized_keyword:
        _log(f"   └ 대표키워드: {canonical_keyword}")

    parent_keyword = normalize_keyword(
        scope.get("parent_keyword", "")
    )
    related_keywords = [
        normalize_keyword(value)
        for value in scope.get("related_keywords", [])
        if normalize_keyword(value)
    ]

    if parent_keyword:
        _log(f"   └ 상위키워드: {parent_keyword}")

    if related_keywords:
        _log("   └ 관련키워드: " + ", ".join(related_keywords))

    _separator("-")
    _log("🏷️ 네이버 추천 태그 저장자료")

    if tag_observation:
        observed_at = str(tag_observation.get("observed_at", ""))
        if observed_at:
            _log(f"   └ 최근조회: {observed_at}")

        exact_tags = [
            item
            for item in tag_observation.get("tags", [])
            if isinstance(item, dict)
            and item.get("match_type") == "exact"
        ]
        related_tags = [
            item
            for item in tag_observation.get("tags", [])
            if isinstance(item, dict)
            and item.get("match_type") != "exact"
        ]

        _log("   [정확일치]")
        if exact_tags:
            for tag in exact_tags:
                _log("      " + _format_tag(tag))
        else:
            _log("      없음")

        _log("   [연관검색]")
        if related_tags:
            for tag in related_tags:
                _log("      " + _format_tag(tag, include_rank=True))
        else:
            _log("      없음")
    else:
        _log(
            f"   저장자료 없음 — 최신 조회: 태그검색 {normalized_keyword}",
            level="WARNING",
        )

    _separator("-")
    _log("✅ 기존 직접 사용 태그")

    usage: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "text": "",
            "manual_count": 0,
            "optimization_count": 0,
            "codes": set(),
        }
    )

    for record in manual_records:
        text = normalize_tag_text(record.get("tag", ""))
        key = tag_key(text)
        if not key:
            continue

        usage[key]["text"] = text
        usage[key]["manual_count"] += 1

        code = record.get("tag_code")
        if code not in (None, ""):
            usage[key]["codes"].add(code)

    for record in optimization_records:
        for tag in record.get("tags", []):
            if not isinstance(tag, dict):
                continue

            text = normalize_tag_text(tag.get("text", ""))
            key = tag_key(text)
            if not key:
                continue

            usage[key]["text"] = text
            usage[key]["optimization_count"] += 1

            code = tag.get("code")
            if code not in (None, ""):
                usage[key]["codes"].add(code)

    sorted_usage = sorted(
        usage.items(),
        key=lambda item: (
            -(
                item[1]["manual_count"]
                + item[1]["optimization_count"]
            ),
            item[1]["text"],
        ),
    )

    if sorted_usage:
        for key, info in sorted_usage[:max(1, manual_tag_limit)]:
            registry_entry = registry.get(key, {})
            if not isinstance(registry_entry, dict):
                registry_entry = {}

            code = registry_entry.get("preferred_code")
            if code in (None, "") and info["codes"]:
                code = sorted(info["codes"])[0]

            status = str(registry_entry.get("status", "manual_registered"))
            restricted = registry_entry.get("restricted")

            details = [
                f"최적화가공 {info['optimization_count']}회"
                if info["optimization_count"]
                else "",
                f"수동추가 {info['manual_count']}회"
                if info["manual_count"]
                else "",
                f"code {code}"
                if code not in (None, "")
                else "",
                "제한태그"
                if restricted is True
                else "",
                status,
            ]

            details = [value for value in details if value]
            _log(
                f"   {info['text']} — "
                + " / ".join(details)
            )

        if len(sorted_usage) > manual_tag_limit:
            _log(
                f"   ... 외 {len(sorted_usage) - manual_tag_limit}개"
            )
    else:
        _log(
            f"   저장자료 없음 — 실제 등록 후: 태그추가 {normalized_keyword}",
            level="WARNING",
        )

    _separator("-")
    _log("🛠️ 과거 상품가공 사례")

    if optimization_records:
        ordered_records = sorted(
            optimization_records,
            key=lambda item: (
                str(item.get("imported_at", "")),
                str(item.get("source_file_name", "")),
                int(item.get("source_row", 0) or 0),
            ),
            reverse=True,
        )

        _log(f"   └ 전체 가공사례: {len(ordered_records)}건")

        for index, record in enumerate(
            ordered_records[:max(1, optimization_example_limit)],
            start=1,
        ):
            _log(
                f"\n   [{index}] {record.get('source_file_name', '')}"
                f" / {record.get('source_sheet', '')}"
                f" / {record.get('source_row', '')}행"
            )
            _log(
                "      원본: "
                + normalize_keyword(record.get("original_product_name", ""))
            )
            _log(
                "      가공: "
                + normalize_keyword(record.get("processed_product_name", ""))
            )
            tag_names = [
                normalize_tag_text(tag.get("text", ""))
                for tag in record.get("tags", [])
                if isinstance(tag, dict)
                and normalize_tag_text(tag.get("text", ""))
            ]
            _log("      태그: " + ", ".join(tag_names))
    else:
        _log(
            "   저장된 최적화가공 사례가 없습니다.",
            level="WARNING",
        )

    _separator("=")
    return has_data
