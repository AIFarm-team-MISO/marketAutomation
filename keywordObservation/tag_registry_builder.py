from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from keywordObservation.keyword_observation_paths import (
    TAG_REGISTRY_FILE,
)
from keywordObservation.manual_tag_store import (
    load_all_manual_tag_usage,
)
from keywordObservation.optimization_record_store import (
    load_all_optimization_records,
)
from keywordObservation.tag_observation_store import (
    load_all_restriction_observations,
    load_all_tag_observations,
)
from keywordObservation.tag_text_utils import (
    normalize_keyword,
    normalize_tag_text,
    tag_key,
)


class TagRegistryBuildError(RuntimeError):
    pass



def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")



def _touch_entry(
    registry: dict[str, dict[str, Any]],
    *,
    text: str,
    observed_at: str,
) -> dict[str, Any]:
    key = tag_key(text)

    if key not in registry:
        registry[key] = {
            "tag_key": key,
            "display_text": normalize_tag_text(text),
            "preferred_code": None,
            "codes": [],
            "naver_exact_search_count": 0,
            "naver_related_search_count": 0,
            "naver_query_keywords": [],
            "manual_registration_count": 0,
            "optimization_usage_count": 0,
            "keywords": [],
            "restricted": None,
            "restriction_checked_at": "",
            "first_seen_at": observed_at,
            "last_seen_at": observed_at,
            "status": "observed",
        }

    entry = registry[key]

    if observed_at:
        if not entry.get("first_seen_at") or observed_at < entry["first_seen_at"]:
            entry["first_seen_at"] = observed_at
        if not entry.get("last_seen_at") or observed_at > entry["last_seen_at"]:
            entry["last_seen_at"] = observed_at

    return entry



def _append_unique(container: list[Any], value: Any) -> None:
    if value not in container:
        container.append(value)



def build_tag_registry() -> dict[str, Any]:
    registry: dict[str, dict[str, Any]] = {}

    for observation in load_all_tag_observations():
        observed_at = str(observation.get("observed_at", ""))
        query_keyword = normalize_keyword(
            observation.get("query_keyword", "")
        )

        for tag in observation.get("tags", []):
            if not isinstance(tag, dict):
                continue

            text = normalize_tag_text(tag.get("text", ""))

            if not text:
                continue

            entry = _touch_entry(
                registry,
                text=text,
                observed_at=observed_at,
            )

            code = tag.get("code")
            if code not in (None, ""):
                try:
                    normalized_code = int(code)
                except (TypeError, ValueError):
                    normalized_code = None

                if normalized_code is not None:
                    _append_unique(entry["codes"], normalized_code)
                    entry["preferred_code"] = normalized_code

            if str(tag.get("match_type", "")) == "exact":
                entry["naver_exact_search_count"] += 1
            else:
                entry["naver_related_search_count"] += 1

            if query_keyword:
                _append_unique(entry["naver_query_keywords"], query_keyword)

    for record in load_all_manual_tag_usage():
        text = normalize_tag_text(record.get("tag", ""))
        if not text:
            continue

        observed_at = str(record.get("recorded_at", ""))
        entry = _touch_entry(
            registry,
            text=text,
            observed_at=observed_at,
        )
        entry["manual_registration_count"] += 1

        keyword = normalize_keyword(record.get("keyword", ""))
        if keyword:
            _append_unique(entry["keywords"], keyword)

        code = record.get("tag_code")
        if code not in (None, ""):
            try:
                normalized_code = int(code)
            except (TypeError, ValueError):
                normalized_code = None

            if normalized_code is not None:
                _append_unique(entry["codes"], normalized_code)
                entry["preferred_code"] = normalized_code

    for record in load_all_optimization_records():
        observed_at = str(record.get("imported_at", ""))
        keyword = normalize_keyword(record.get("keyword", ""))

        for tag in record.get("tags", []):
            if not isinstance(tag, dict):
                continue

            text = normalize_tag_text(tag.get("text", ""))
            if not text:
                continue

            entry = _touch_entry(
                registry,
                text=text,
                observed_at=observed_at,
            )
            entry["optimization_usage_count"] += 1

            if keyword:
                _append_unique(entry["keywords"], keyword)

            code = tag.get("code")
            if code not in (None, ""):
                try:
                    normalized_code = int(code)
                except (TypeError, ValueError):
                    normalized_code = None

                if normalized_code is not None:
                    _append_unique(entry["codes"], normalized_code)
                    entry["preferred_code"] = normalized_code

    for observation in load_all_restriction_observations():
        observed_at = str(observation.get("observed_at", ""))

        for result in observation.get("results", []):
            if not isinstance(result, dict):
                continue

            text = normalize_tag_text(result.get("tag", ""))
            if not text:
                continue

            entry = _touch_entry(
                registry,
                text=text,
                observed_at=observed_at,
            )

            if observed_at >= str(entry.get("restriction_checked_at", "")):
                entry["restricted"] = bool(result.get("restricted", False))
                entry["restriction_checked_at"] = observed_at

    for entry in registry.values():
        entry["codes"].sort()
        entry["keywords"].sort()
        entry["naver_query_keywords"].sort()

        if entry.get("restricted") is True:
            status = "blocked"
        elif (
            entry.get("manual_registration_count", 0) > 0
            or entry.get("optimization_usage_count", 0) > 0
        ) and entry.get("naver_exact_search_count", 0) > 0:
            status = "manual_and_naver_exact"
        elif (
            entry.get("manual_registration_count", 0) > 0
            or entry.get("optimization_usage_count", 0) > 0
        ):
            status = "manual_registered"
        elif entry.get("naver_exact_search_count", 0) > 0:
            status = "naver_exact"
        else:
            status = "naver_related"

        entry["status"] = status

    payload = {
        "registry_version": "1.0",
        "built_at": _now_iso(),
        "tag_count": len(registry),
        "tags": dict(
            sorted(
                registry.items(),
                key=lambda item: item[1].get("display_text", ""),
            )
        ),
    }

    TAG_REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        TAG_REGISTRY_FILE.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        raise TagRegistryBuildError(
            f"통합 태그사전을 저장하지 못했습니다: {error}"
        ) from error

    return payload



def load_tag_registry() -> dict[str, Any]:
    if not TAG_REGISTRY_FILE.exists():
        return build_tag_registry()

    try:
        loaded = json.loads(
            TAG_REGISTRY_FILE.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return build_tag_registry()

    if not isinstance(loaded, dict):
        return build_tag_registry()

    return loaded



def find_registry_entry(tag: str) -> dict[str, Any] | None:
    loaded = load_tag_registry()
    tags = loaded.get("tags", {})

    if not isinstance(tags, dict):
        return None

    entry = tags.get(tag_key(tag))

    if isinstance(entry, dict):
        return entry

    return None
