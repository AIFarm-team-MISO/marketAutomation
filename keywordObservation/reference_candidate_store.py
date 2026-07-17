from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data"

CANDIDATE_REGISTRY_FILE = (
    DATA_DIR
    / "reference_candidate_registry.json"
)

REGISTRY_SCHEMA_VERSION = "1.0"


class ReferenceCandidateStoreError(
    RuntimeError
):
    pass


def _safe_dict(
    value: Any,
) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    return {}


def _safe_list(
    value: Any,
) -> list[Any]:
    if isinstance(value, list):
        return value

    return []


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(value)

    except (TypeError, ValueError):
        return default


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def _now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).astimezone().isoformat(
        timespec="seconds"
    )


def _load_registry(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": (
                REGISTRY_SCHEMA_VERSION
            ),
            "updated_at": "",
            "candidates": {},
        }

    try:
        loaded = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ) as error:
        raise ReferenceCandidateStoreError(
            (
                "미분류 후보 누적파일을 "
                f"읽지 못했습니다: {error}"
            )
        ) from error

    registry = _safe_dict(
        loaded
    )

    registry.setdefault(
        "schema_version",
        REGISTRY_SCHEMA_VERSION,
    )

    registry.setdefault(
        "updated_at",
        "",
    )

    registry.setdefault(
        "candidates",
        {},
    )

    return registry


def _atomic_write_json(
    path: Path,
    data: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=path.name + ".",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            json.dump(
                data,
                temporary_file,
                ensure_ascii=False,
                indent=2,
            )

            temporary_file.write(
                "\n"
            )

            temporary_path = Path(
                temporary_file.name
            )

        os.replace(
            temporary_path,
            path,
        )

    except OSError as error:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            temporary_path.unlink(
                missing_ok=True
            )

        raise ReferenceCandidateStoreError(
            (
                "미분류 후보 누적파일을 "
                f"저장하지 못했습니다: {error}"
            )
        ) from error


def update_reference_candidate_registry(
    *,
    keyword: str,
    reference_distribution: dict[str, Any],
    registry_path: Path | None = None,
) -> tuple[Path, int]:
    """
    관찰 결과의 미분류 참고정보 후보를 누적한다.

    자동으로 사전에 승격하지 않고 status='pending'으로 저장한다.
    사용자가 검토한 뒤 사전에 추가하거나 무시목록으로 보낸다.
    """
    path = (
        registry_path
        or CANDIDATE_REGISTRY_FILE
    )

    candidates = _safe_list(
        _safe_dict(
            reference_distribution
        ).get(
            "unclassified"
        )
    )

    if not candidates:
        return path, 0

    registry = _load_registry(
        path
    )

    candidate_mapping = _safe_dict(
        registry.get(
            "candidates"
        )
    )

    now = _now_iso()
    normalized_keyword = " ".join(
        str(keyword).split()
    )

    updated_count = 0

    for item in candidates:
        if not isinstance(
            item,
            dict,
        ):
            continue

        token = str(
            item.get(
                "token",
                "",
            )
        ).strip()

        if not token:
            continue

        current = _safe_dict(
            candidate_mapping.get(
                token
            )
        )

        current.setdefault(
            "token",
            token,
        )

        current.setdefault(
            "status",
            "pending",
        )

        current.setdefault(
            "first_seen_at",
            now,
        )

        current[
            "last_seen_at"
        ] = now

        current[
            "observation_count"
        ] = (
            _safe_int(
                current.get(
                    "observation_count",
                    0,
                )
            )
            + 1
        )

        current[
            "total_product_count"
        ] = (
            _safe_int(
                current.get(
                    "total_product_count",
                    0,
                )
            )
            + _safe_int(
                item.get(
                    "product_count",
                    0,
                )
            )
        )

        current[
            "max_ratio"
        ] = max(
            _safe_float(
                current.get(
                    "max_ratio",
                    0.0,
                )
            ),
            _safe_float(
                item.get(
                    "ratio",
                    0.0,
                )
            ),
        )

        keywords = [
            str(value)
            for value in _safe_list(
                current.get(
                    "keywords"
                )
            )
            if str(value).strip()
        ]

        if (
            normalized_keyword
            and normalized_keyword
            not in keywords
        ):
            keywords.append(
                normalized_keyword
            )

        current[
            "keywords"
        ] = keywords[:20]

        examples = [
            str(value)
            for value in _safe_list(
                current.get(
                    "examples"
                )
            )
            if str(value).strip()
        ]

        for example in _safe_list(
            item.get(
                "examples"
            )
        ):
            normalized_example = str(
                example
            ).strip()

            if (
                normalized_example
                and normalized_example
                not in examples
            ):
                examples.append(
                    normalized_example
                )

        current[
            "examples"
        ] = examples[:5]

        candidate_mapping[
            token
        ] = current

        updated_count += 1

    registry[
        "schema_version"
    ] = REGISTRY_SCHEMA_VERSION

    registry[
        "updated_at"
    ] = now

    registry[
        "candidates"
    ] = dict(
        sorted(
            candidate_mapping.items(),
            key=lambda pair: (
                -_safe_int(
                    _safe_dict(
                        pair[1]
                    ).get(
                        "observation_count",
                        0,
                    )
                ),
                -_safe_int(
                    _safe_dict(
                        pair[1]
                    ).get(
                        "total_product_count",
                        0,
                    )
                ),
                pair[0],
            ),
        )
    )

    _atomic_write_json(
        path,
        registry,
    )

    return path, updated_count
