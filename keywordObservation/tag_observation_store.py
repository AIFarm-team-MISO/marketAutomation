from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from keywordObservation.keyword_observation_paths import (
    NAVER_TAG_OBSERVATION_FILE,
    TAG_RESTRICTION_OBSERVATION_FILE,
    TAG_READABLE_LATEST_DIR,
)
from keywordObservation.tag_text_utils import (
    normalize_keyword,
    normalize_tag_text,
    stable_fingerprint,
    tag_key,
)


class TagObservationStoreError(RuntimeError):
    pass



def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")



def _append_jsonl(
    path: Path,
    record: dict[str, Any],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with path.open("a", encoding="utf-8", newline="\n") as file:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )
    except OSError as error:
        raise TagObservationStoreError(
            f"태그 관찰자료를 저장하지 못했습니다: {error}"
        ) from error

    return path



def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return

    try:
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                normalized = line.strip()

                if not normalized:
                    continue

                try:
                    record = json.loads(normalized)
                except json.JSONDecodeError:
                    continue

                if isinstance(record, dict):
                    yield record
    except OSError as error:
        raise TagObservationStoreError(
            f"태그 관찰자료를 읽지 못했습니다: {error}"
        ) from error



def _safe_filename(keyword: str) -> str:
    normalized = normalize_keyword(keyword)
    safe = re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", normalized).strip("_.")

    if not safe:
        safe = "keyword"

    digest = stable_fingerprint({"keyword": normalized})[:10]
    return f"{safe[:60]}_{digest}.json"



def _write_latest_pretty(record: dict[str, Any]) -> Path:
    keyword = str(record.get("query_keyword", ""))
    path = TAG_READABLE_LATEST_DIR / _safe_filename(keyword)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        path.write_text(
            json.dumps(
                record,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        raise TagObservationStoreError(
            f"읽기용 최신 태그파일을 저장하지 못했습니다: {error}"
        ) from error

    return path



def append_recommend_tag_observation(
    *,
    keyword: str,
    tags: list[dict[str, Any]],
    response_metadata: dict[str, Any] | None = None,
    source_command: str = "태그검색",
) -> tuple[Path, Path, dict[str, Any]]:
    normalized_keyword = normalize_keyword(keyword)
    metadata = response_metadata or {}
    keyword_key = tag_key(normalized_keyword)

    normalized_tags: list[dict[str, Any]] = []

    for index, item in enumerate(tags, start=1):
        text = normalize_tag_text(item.get("text", ""))

        if not text:
            continue

        code = item.get("code")

        try:
            normalized_code = int(code) if code not in (None, "") else None
        except (TypeError, ValueError):
            normalized_code = None

        normalized_tags.append(
            {
                "rank": index,
                "code": normalized_code,
                "text": text,
                "match_type": (
                    "exact"
                    if tag_key(text) == keyword_key
                    else "related"
                ),
            }
        )

    observed_at = _now_iso()

    record = {
        "schema_version": "1.0",
        "record_type": "naver_recommend_tag_observation",
        "observed_at": observed_at,
        "source_command": source_command,
        "query_keyword": normalized_keyword,
        "result_count": len(normalized_tags),
        "tags": normalized_tags,
        "response": {
            "status_code": metadata.get("status_code"),
            "trace_id": metadata.get("trace_id", ""),
            "request_url": metadata.get("request_url", ""),
            "attempt_count": metadata.get("attempt_count", 1),
        },
    }

    record["fingerprint"] = stable_fingerprint(
        {
            "query_keyword": normalized_keyword,
            "observed_at": observed_at,
            "tags": normalized_tags,
        }
    )

    history_path = _append_jsonl(
        NAVER_TAG_OBSERVATION_FILE,
        record,
    )
    readable_path = _write_latest_pretty(record)

    return history_path, readable_path, record



def append_restriction_observation(
    *,
    requested_tags: list[str],
    results: list[dict[str, Any]],
    response_metadata: dict[str, Any] | None = None,
) -> tuple[Path, dict[str, Any]]:
    metadata = response_metadata or {}
    observed_at = _now_iso()

    normalized_results = []

    for item in results:
        tag = normalize_tag_text(item.get("tag", ""))

        if not tag:
            continue

        normalized_results.append(
            {
                "tag": tag,
                "restricted": bool(item.get("restricted", False)),
            }
        )

    record = {
        "schema_version": "1.0",
        "record_type": "naver_tag_restriction_observation",
        "observed_at": observed_at,
        "requested_tags": [
            normalize_tag_text(tag)
            for tag in requested_tags
            if normalize_tag_text(tag)
        ],
        "results": normalized_results,
        "response": {
            "status_code": metadata.get("status_code"),
            "trace_id": metadata.get("trace_id", ""),
            "request_url": metadata.get("request_url", ""),
            "attempt_count": metadata.get("attempt_count", 1),
        },
    }

    record["fingerprint"] = stable_fingerprint(record)

    path = _append_jsonl(
        TAG_RESTRICTION_OBSERVATION_FILE,
        record,
    )

    return path, record



def find_latest_tag_observation(
    keyword: str,
) -> dict[str, Any] | None:
    target = normalize_keyword(keyword).casefold()
    latest: dict[str, Any] | None = None

    for record in _iter_jsonl(NAVER_TAG_OBSERVATION_FILE):
        record_keyword = normalize_keyword(
            record.get("query_keyword", "")
        ).casefold()

        if record_keyword == target:
            latest = record

    return latest



def load_all_tag_observations() -> list[dict[str, Any]]:
    return list(_iter_jsonl(NAVER_TAG_OBSERVATION_FILE))



def load_all_restriction_observations() -> list[dict[str, Any]]:
    return list(_iter_jsonl(TAG_RESTRICTION_OBSERVATION_FILE))



def build_known_tag_code_map() -> dict[str, dict[str, Any]]:
    known: dict[str, dict[str, Any]] = {}

    for observation in _iter_jsonl(NAVER_TAG_OBSERVATION_FILE):
        observed_at = str(observation.get("observed_at", ""))

        for tag in observation.get("tags", []):
            if not isinstance(tag, dict):
                continue

            text = normalize_tag_text(tag.get("text", ""))
            key = tag_key(text)
            code = tag.get("code")

            if not key or code in (None, ""):
                continue

            existing = known.get(key)

            if existing is None or observed_at >= str(
                existing.get("observed_at", "")
            ):
                known[key] = {
                    "text": text,
                    "code": code,
                    "observed_at": observed_at,
                }

    return known
