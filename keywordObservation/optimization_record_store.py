from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Iterable

from keywordObservation.keyword_observation_paths import (
    OPTIMIZATION_IMPORT_HISTORY_FILE,
    OPTIMIZATION_RECORD_FILE,
)
from keywordObservation.tag_text_utils import (
    normalize_keyword,
)


class OptimizationRecordStoreError(RuntimeError):
    pass



def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")



def _iter_jsonl(path) -> Iterable[dict[str, Any]]:
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
        raise OptimizationRecordStoreError(
            f"가공자료를 읽지 못했습니다: {error}"
        ) from error



def load_existing_optimization_fingerprints() -> set[str]:
    return {
        str(record.get("fingerprint", ""))
        for record in _iter_jsonl(OPTIMIZATION_RECORD_FILE)
        if str(record.get("fingerprint", ""))
    }



def append_optimization_records(
    records: list[dict[str, Any]],
    *,
    import_source: str = "optimization_workbook",
) -> dict[str, Any]:
    existing = load_existing_optimization_fingerprints()
    batch_id = str(uuid.uuid4())
    imported_at = _now_iso()
    appended: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    OPTIMIZATION_RECORD_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        with OPTIMIZATION_RECORD_FILE.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as file:
            for original in records:
                record = dict(original)
                fingerprint = str(record.get("fingerprint", ""))

                if not fingerprint:
                    skipped.append(record)
                    continue

                if fingerprint in existing:
                    skipped.append(record)
                    continue

                record.update(
                    {
                        "schema_version": "1.0",
                        "record_type": "optimization_record",
                        "batch_id": batch_id,
                        "imported_at": imported_at,
                        "import_source": import_source,
                        "registration_verified": True,
                    }
                )

                file.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    + "\n"
                )

                existing.add(fingerprint)
                appended.append(record)

    except OSError as error:
        raise OptimizationRecordStoreError(
            f"가공자료를 저장하지 못했습니다: {error}"
        ) from error

    return {
        "batch_id": batch_id,
        "imported_at": imported_at,
        "appended_count": len(appended),
        "skipped_count": len(skipped),
        "appended_records": appended,
        "skipped_records": skipped,
        "path": str(OPTIMIZATION_RECORD_FILE),
    }



def append_optimization_import_history(
    summary: dict[str, Any],
) -> str:
    OPTIMIZATION_IMPORT_HISTORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    record = {
        "schema_version": "1.0",
        "record_type": "optimization_import_history",
        "recorded_at": _now_iso(),
        **summary,
    }

    try:
        with OPTIMIZATION_IMPORT_HISTORY_FILE.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as file:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )
    except OSError as error:
        raise OptimizationRecordStoreError(
            f"가공자료 가져오기 이력을 저장하지 못했습니다: {error}"
        ) from error

    return str(OPTIMIZATION_IMPORT_HISTORY_FILE)



def find_optimization_records(
    keyword: str,
) -> list[dict[str, Any]]:
    target = normalize_keyword(keyword).casefold()

    return [
        record
        for record in _iter_jsonl(OPTIMIZATION_RECORD_FILE)
        if normalize_keyword(record.get("keyword", "")).casefold() == target
    ]



def load_all_optimization_records() -> list[dict[str, Any]]:
    return list(_iter_jsonl(OPTIMIZATION_RECORD_FILE))
