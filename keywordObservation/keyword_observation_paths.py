from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data"

OBSERVATION_FILE = (
    DATA_DIR
    / "naver_shopping_observations.jsonl"
)

REFERENCE_DICTIONARY_FILE = (
    DATA_DIR
    / "reference_dictionary.json"
)

REFERENCE_CANDIDATE_REGISTRY_FILE = (
    DATA_DIR
    / "reference_candidate_registry.json"
)

SETTINGS_FILE = (
    DATA_DIR
    / "keyword_observation_settings.json"
)

KEYWORD_INPUT_DIR = (
    DATA_DIR
    / "keyword_inputs"
)

DICTIONARY_COLLECTION_HISTORY_FILE = (
    DATA_DIR
    / "dictionary_collection_history.jsonl"
)

LEGACY_REFERENCE_DICTIONARY_FILE = (
    PACKAGE_DIR
    / "reference_rules"
    / "reference_dictionary.json"
)


DEFAULT_REFERENCE_DICTIONARY: dict[
    str,
    Any,
] = {
    "dictionary_version": "1.0",
    "description": (
        "참고정보 자동분류에서 추가로 인정하거나 제외할 표현을 "
        "관리합니다. approved의 값은 상품명에 동일한 표현이 "
        "있을 때 해당 분류로 추가되고, aliases는 다른 표기를 "
        "approved의 표준 표현으로 통일하며, "
        "ignored_candidates는 미분류 후보에서 제외합니다."
    ),
    "approved": {
        "quantity": [
            "1+1",
            "2+1",
        ],
        "measurement": [],
        "specification": [
            "A3",
            "A4",
            "A5",
            "B4",
            "B5",
        ],
        "option": [
            "대/중/소",
            "S/M/L",
        ],
        "english": [],
        "model_code": [],
    },
    "aliases": {
        "대·중·소": "대/중/소",
        "대중소": "대/중/소",
        "에이포": "A4",
        "에이쓰리": "A3",
    },
    "ignored_candidates": [],
}


def _read_json(
    path: Path,
) -> dict[str, Any] | None:
    try:
        loaded = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return None

    if isinstance(
        loaded,
        dict,
    ):
        return loaded

    return None


def _write_json(
    path: Path,
    data: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def ensure_data_layout() -> list[str]:
    """
    keywordObservation에서 사용하는 설정·입력·사전·운영자료를
    data 폴더 아래에 모아 관리한다.

    과거 reference_rules/reference_dictionary.json이 남아 있으면
    새 data/reference_dictionary.json으로 안전하게 이전한다.
    """
    messages: list[str] = []

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    KEYWORD_INPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    legacy_dictionary = _read_json(
        LEGACY_REFERENCE_DICTIONARY_FILE
    )

    current_dictionary = _read_json(
        REFERENCE_DICTIONARY_FILE
    )

    if (
        legacy_dictionary is not None
        and current_dictionary is None
    ):
        shutil.copy2(
            LEGACY_REFERENCE_DICTIONARY_FILE,
            REFERENCE_DICTIONARY_FILE,
        )

        messages.append(
            (
                "기존 참고정보 사전을 data 폴더로 복사했습니다: "
                f"{REFERENCE_DICTIONARY_FILE}"
            )
        )

    elif (
        legacy_dictionary is not None
        and current_dictionary
        == DEFAULT_REFERENCE_DICTIONARY
        and legacy_dictionary
        != current_dictionary
    ):
        # 배포본 기본사전보다 기존 사용자의 사전이 우선이다.
        shutil.copy2(
            LEGACY_REFERENCE_DICTIONARY_FILE,
            REFERENCE_DICTIONARY_FILE,
        )

        messages.append(
            (
                "기존에 수정한 참고정보 사전을 우선 적용했습니다: "
                f"{REFERENCE_DICTIONARY_FILE}"
            )
        )

    elif current_dictionary is None:
        _write_json(
            REFERENCE_DICTIONARY_FILE,
            DEFAULT_REFERENCE_DICTIONARY,
        )

        messages.append(
            (
                "기본 참고정보 사전을 생성했습니다: "
                f"{REFERENCE_DICTIONARY_FILE}"
            )
        )

    return messages
