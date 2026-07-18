from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from keywordObservation.keyword_observation_paths import (
    DICTIONARY_COLLECTION_HISTORY_FILE,
)


class DictionaryCollectionHistoryError(
    RuntimeError
):
    pass


def _now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).astimezone().isoformat(
        timespec="seconds"
    )


def append_dictionary_collection_history(
    *,
    batch_id: str,
    keyword: str,
    status: str,
    source_files: list[str] | None = None,
    normalized_keyword: str = "",
    sample_count: int = 0,
    message: str = "",
    history_path: Path = (
        DICTIONARY_COLLECTION_HISTORY_FILE
    ),
) -> Path:
    """
    사전추가 명령의 키워드별 결과를 JSONL로 남긴다.
    """
    record: dict[str, Any] = {
        "recorded_at": _now_iso(),
        "batch_id": batch_id,
        "keyword": keyword,
        "normalized_keyword": (
            normalized_keyword
        ),
        "status": status,
        "sample_count": int(
            sample_count
        ),
        "source_files": list(
            source_files
            or []
        ),
        "message": message,
    }

    history_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    serialized = json.dumps(
        record,
        ensure_ascii=False,
    )

    try:
        with history_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                serialized
                + os.linesep
            )

    except OSError as error:
        raise DictionaryCollectionHistoryError(
            (
                "사전추가 실행이력을 "
                f"저장하지 못했습니다: {error}"
            )
        ) from error

    return history_path
