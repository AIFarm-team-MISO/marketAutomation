from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from keywordObservation.keyword_observation_paths import (
    MANUAL_TAG_USAGE_FILE,
)
from keywordObservation.tag_observation_store import (
    build_known_tag_code_map,
)
from keywordObservation.tag_text_utils import (
    normalize_keyword,
    normalize_tag_text,
    stable_fingerprint,
    tag_key,
)


class ManualTagStoreError(RuntimeError):
    pass



def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")



def _iter_records() -> Iterable[dict[str, Any]]:
    if not MANUAL_TAG_USAGE_FILE.exists():
        return

    try:
        with MANUAL_TAG_USAGE_FILE.open("r", encoding="utf-8") as file:
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
        raise ManualTagStoreError(
            f"수동 태그 사용이력을 읽지 못했습니다: {error}"
        ) from error



def _existing_fingerprints() -> set[str]:
    return {
        str(record.get("fingerprint", ""))
        for record in _iter_records()
        if str(record.get("fingerprint", ""))
    }



def append_manual_tag_usage(
    *,
    keyword: str,
    tags: list[dict[str, Any]],
    original_product_name: str = "",
    processed_product_name: str = "",
    seller_product_code: str = "",
    category: str = "",
    memo: str = "",
    source_type: str = "manual_registration",
) -> dict[str, Any]:
    normalized_keyword = normalize_keyword(keyword)

    if not normalized_keyword:
        raise ManualTagStoreError("메인키워드가 비어 있습니다.")

    known_codes = build_known_tag_code_map()
    existing = _existing_fingerprints()
    batch_id = str(uuid.uuid4())
    recorded_at = _now_iso()
    appended_records: list[dict[str, Any]] = []
    skipped_records: list[dict[str, Any]] = []

    MANUAL_TAG_USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        with MANUAL_TAG_USAGE_FILE.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as file:
            for item in tags:
                text = normalize_tag_text(item.get("text", ""))
                key = tag_key(text)

                if not key:
                    continue

                code = item.get("code")

                if code in (None, "") and key in known_codes:
                    code = known_codes[key].get("code")

                try:
                    normalized_code = int(code) if code not in (None, "") else None
                except (TypeError, ValueError):
                    normalized_code = None

                fingerprint_payload = {
                    "keyword": normalized_keyword,
                    "tag_key": key,
                    "seller_product_code": normalize_keyword(seller_product_code),
                    "processed_product_name": normalize_keyword(processed_product_name),
                    "source_type": source_type,
                }

                fingerprint = stable_fingerprint(fingerprint_payload)

                record = {
                    "schema_version": "1.0",
                    "record_type": "manual_tag_usage",
                    "batch_id": batch_id,
                    "recorded_at": recorded_at,
                    "keyword": normalized_keyword,
                    "tag": text,
                    "tag_code": normalized_code,
                    "registration_verified": True,
                    "source_type": source_type,
                    "original_product_name": normalize_keyword(original_product_name),
                    "processed_product_name": normalize_keyword(processed_product_name),
                    "seller_product_code": normalize_keyword(seller_product_code),
                    "category": normalize_keyword(category),
                    "memo": normalize_keyword(memo),
                    "fingerprint": fingerprint,
                }

                if fingerprint in existing:
                    skipped_records.append(record)
                    continue

                file.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    + "\n"
                )

                existing.add(fingerprint)
                appended_records.append(record)

    except OSError as error:
        raise ManualTagStoreError(
            f"수동 태그 사용이력을 저장하지 못했습니다: {error}"
        ) from error

    return {
        "batch_id": batch_id,
        "recorded_at": recorded_at,
        "appended_count": len(appended_records),
        "skipped_count": len(skipped_records),
        "appended_records": appended_records,
        "skipped_records": skipped_records,
        "path": str(MANUAL_TAG_USAGE_FILE),
    }



def find_manual_tag_usage(
    keyword: str,
) -> list[dict[str, Any]]:
    target = normalize_keyword(keyword).casefold()

    return [
        record
        for record in _iter_records()
        if normalize_keyword(record.get("keyword", "")).casefold() == target
    ]



def load_all_manual_tag_usage() -> list[dict[str, Any]]:
    return list(_iter_records())
