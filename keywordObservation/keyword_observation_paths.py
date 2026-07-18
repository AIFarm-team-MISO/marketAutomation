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

# =========================================================
# 태그·가공자료 경로
# =========================================================

PRIVATE_DATA_DIR = DATA_DIR / "private"

NAVER_COMMERCE_CREDENTIALS_FILE = (
    PRIVATE_DATA_DIR
    / "naver_commerce_credentials.json"
)

NAVER_COMMERCE_CREDENTIALS_EXAMPLE_FILE = (
    DATA_DIR
    / "naver_commerce_credentials.example.json"
)

NAVER_TAG_OBSERVATION_FILE = (
    DATA_DIR
    / "naver_tag_observations.jsonl"
)

TAG_RESTRICTION_OBSERVATION_FILE = (
    DATA_DIR
    / "tag_restriction_observations.jsonl"
)

MANUAL_TAG_USAGE_FILE = (
    DATA_DIR
    / "manual_tag_usage_records.jsonl"
)

OPTIMIZATION_RECORD_FILE = (
    DATA_DIR
    / "optimization_records.jsonl"
)

OPTIMIZATION_IMPORT_HISTORY_FILE = (
    DATA_DIR
    / "optimization_import_history.jsonl"
)

TAG_REGISTRY_FILE = (
    DATA_DIR
    / "tag_registry.json"
)

KEYWORD_RELATIONSHIPS_FILE = (
    DATA_DIR
    / "keyword_relationships.json"
)

OPTIMIZATION_INPUT_DIR = (
    DATA_DIR
    / "optimization_inputs"
)

TAG_READABLE_DIR = (
    DATA_DIR
    / "readable"
    / "tags"
)

TAG_READABLE_LATEST_DIR = (
    TAG_READABLE_DIR
    / "latest"
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


DEFAULT_COMMERCE_CREDENTIALS: dict[str, Any] = {
    "client_id": "여기에_애플리케이션_ID를_입력하세요",
    "client_secret": "여기에_애플리케이션_시크릿을_입력하세요",
    "token_type": "SELF",
    "account_id": "",
}


DEFAULT_KEYWORD_RELATIONSHIPS: dict[str, Any] = {
    "version": "1.0",
    "description": (
        "키워드의 별칭·상위키워드·관련키워드를 수동으로 관리합니다. "
        "문자열 포함만으로 자동 관계를 만들지 않습니다."
    ),
    "relationships": {},
}


DEFAULT_TAG_REGISTRY: dict[str, Any] = {
    "registry_version": "1.0",
    "built_at": "",
    "tag_count": 0,
    "tags": {},
}


OPTIMIZATION_INPUT_GUIDE = """최적화가공틀 엑셀파일을 이 폴더에 넣습니다.

지원 확장자
- .xlsx
- .xlsm
- .xls (pandas와 xlrd 필요)

프로그램 명령
가공자료추가

가공자료추가는 파일을 먼저 분석하고 정상기록·중복·불완전행을 요약한 뒤
Enter를 누른 경우에만 optimization_records.jsonl과 tag_registry.json에 저장합니다.
"""



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

    for directory in (
        DATA_DIR,
        KEYWORD_INPUT_DIR,
        PRIVATE_DATA_DIR,
        OPTIMIZATION_INPUT_DIR,
        TAG_READABLE_LATEST_DIR,
    ):
        directory.mkdir(
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

    if not NAVER_COMMERCE_CREDENTIALS_EXAMPLE_FILE.exists():
        _write_json(
            NAVER_COMMERCE_CREDENTIALS_EXAMPLE_FILE,
            DEFAULT_COMMERCE_CREDENTIALS,
        )

    if not NAVER_COMMERCE_CREDENTIALS_FILE.exists():
        _write_json(
            NAVER_COMMERCE_CREDENTIALS_FILE,
            DEFAULT_COMMERCE_CREDENTIALS,
        )
        messages.append(
            (
                "커머스API 인증 입력파일을 생성했습니다: "
                f"{NAVER_COMMERCE_CREDENTIALS_FILE}"
            )
        )

    if not KEYWORD_RELATIONSHIPS_FILE.exists():
        _write_json(
            KEYWORD_RELATIONSHIPS_FILE,
            DEFAULT_KEYWORD_RELATIONSHIPS,
        )

    if not TAG_REGISTRY_FILE.exists():
        _write_json(
            TAG_REGISTRY_FILE,
            DEFAULT_TAG_REGISTRY,
        )

    optimization_guide_path = (
        OPTIMIZATION_INPUT_DIR
        / "사용방법.txt"
    )

    if not optimization_guide_path.exists():
        optimization_guide_path.write_text(
            OPTIMIZATION_INPUT_GUIDE,
            encoding="utf-8",
        )

    return messages
