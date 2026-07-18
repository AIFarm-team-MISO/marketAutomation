from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from keywordObservation.keyword_observation_paths import (
    OBSERVATION_FILE,
)


def _safe_dict(
    value: Any,
) -> dict[str, Any]:
    if isinstance(
        value,
        dict,
    ):
        return value

    return {}


def load_observed_keyword_index(
    observation_path: Path = (
        OBSERVATION_FILE
    ),
) -> dict[str, Any]:
    """
    관찰 JSONL을 한 번만 순회하여
    이미 저장된 정규화 키워드 집합을 만든다.
    """
    result: dict[str, Any] = {
        "path": str(
            observation_path
        ),
        "record_count": 0,
        "invalid_line_count": 0,
        "keywords": set(),
        "casefold_keywords": set(),
    }

    if not observation_path.exists():
        return result

    try:
        with observation_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            for line in file:
                stripped = line.strip()

                if not stripped:
                    continue

                try:
                    record = json.loads(
                        stripped
                    )

                except json.JSONDecodeError:
                    result[
                        "invalid_line_count"
                    ] += 1
                    continue

                if not isinstance(
                    record,
                    dict,
                ):
                    result[
                        "invalid_line_count"
                    ] += 1
                    continue

                result[
                    "record_count"
                ] += 1

                query = _safe_dict(
                    record.get(
                        "query"
                    )
                )

                keyword = " ".join(
                    str(
                        query.get(
                            "normalized_keyword",
                            query.get(
                                "input_keyword",
                                "",
                            ),
                        )
                    ).split()
                )

                if not keyword:
                    continue

                result[
                    "keywords"
                ].add(
                    keyword
                )

                result[
                    "casefold_keywords"
                ].add(
                    keyword.casefold()
                )

    except OSError:
        return result

    return result
