from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


# =========================================================
# 기본 경로
# =========================================================

PACKAGE_DIR = Path(__file__).resolve().parent

DATA_DIR = PACKAGE_DIR / "data"

OBSERVATION_FILE = (
    DATA_DIR
    / "naver_shopping_observations.jsonl"
)

READABLE_DIR = DATA_DIR / "readable"

LATEST_READABLE_DIR = (
    READABLE_DIR
    / "latest"
)


# =========================================================
# 저장 구조 버전
# =========================================================

SCHEMA_VERSION = "1.2"

PROCESSOR_VERSION = "0.5.0"

ANALYZER_VERSION = "0.5.0"


# =========================================================
# 허용하는 수집상태
# =========================================================

ALLOWED_COLLECTION_STATUSES = {
    "success",
    "no_results",
    "partial",
}


class ObservationStoreError(RuntimeError):
    """
    관찰데이터 저장·조회 과정에서 발생하는 오류.
    """


def normalize_keyword(
    keyword: str,
) -> str:
    """
    검색어 앞뒤 공백과 연속 공백을 정리한다.

    예:
        "  박스테이프   대용량  "
        → "박스테이프 대용량"
    """
    if keyword is None:
        return ""

    return " ".join(
        str(keyword).split()
    )


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """
    값을 안전하게 정수로 변환한다.
    """
    try:
        return int(value)

    except (TypeError, ValueError):
        return default


def _safe_dict(
    value: Any,
) -> dict[str, Any]:
    """
    dict가 아닌 값은 빈 dict로 바꾼다.
    """
    if isinstance(value, dict):
        return value

    return {}


def _safe_list(
    value: Any,
) -> list[Any]:
    """
    list가 아닌 값은 빈 list로 바꾼다.
    """
    if isinstance(value, list):
        return value

    return []


def _get_current_iso_datetime() -> str:
    """
    현재 지역 시간대를 포함한 ISO 날짜를 만든다.

    예:
        2026-07-16T16:51:19+09:00
    """
    return (
        datetime.now()
        .astimezone()
        .replace(microsecond=0)
        .isoformat()
    )


def ensure_data_directory() -> None:
    """
    JSONL 및 읽기용 JSON 저장 폴더를 생성한다.
    """
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OBSERVATION_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    READABLE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    LATEST_READABLE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def _normalize_collection_status(
    response_metadata: dict[str, Any],
    received_count: int,
) -> str:
    """
    API 수집상태를 결정한다.

    response_metadata에 명시적인 상태가 있으면
    허용된 값에 한해 우선 적용한다.

    그렇지 않으면:
        받은 상품 있음 → success
        받은 상품 없음 → no_results
    """
    provided_status = str(
        response_metadata.get(
            "collection_status",
            "",
        )
    ).strip()

    if provided_status in (
        ALLOWED_COLLECTION_STATUSES
    ):
        return provided_status

    if received_count > 0:
        return "success"

    return "no_results"


def build_observation_record(
    keyword: str,
    display: int,
    sort: str,
    samples: list[dict[str, Any]],
    analysis: dict[str, Any],
    query_validation: dict[str, Any],
    source_record_type: str = (
        "direct_api_capture"
    ),
    response_metadata: (
        dict[str, Any] | None
    ) = None,
    captured_at: str | None = None,
) -> dict[str, Any]:
    """
    네이버 쇼핑 관찰기록 한 건을 만든다.

    Parameters
    ----------
    keyword
        사용자가 입력한 검색어.

    display
        요청한 상품 수.

    sort
        API 정렬방식.

    samples
        처리된 상품 샘플 목록.

    analysis
        키워드·카테고리·참고정보 분석 결과.

    query_validation
        검색어와 검색결과의 검증 결과.

    source_record_type
        자료 생성 출처.

        예:
            direct_api_capture
            historical_import

    response_metadata
        fetch_shopping_response()에서 반환된
        API 응답 요약.

    captured_at
        별도 날짜를 지정하지 않으면 현재 시간이 사용된다.
    """
    normalized_keyword = normalize_keyword(
        keyword
    )

    if not normalized_keyword:
        raise ObservationStoreError(
            "관찰기록의 검색어가 비어 있습니다."
        )

    if display < 1:
        raise ObservationStoreError(
            "display는 1 이상이어야 합니다."
        )

    normalized_sort = str(sort).strip()

    if not normalized_sort:
        raise ObservationStoreError(
            "sort가 비어 있습니다."
        )

    normalized_samples = [
        sample
        for sample in _safe_list(samples)
        if isinstance(sample, dict)
    ]

    normalized_analysis = _safe_dict(
        analysis
    )

    normalized_validation = _safe_dict(
        query_validation
    )

    normalized_response = _safe_dict(
        response_metadata
    )

    processed_sample_count = len(
        normalized_samples
    )

    # API에서 실제로 받은 상품 수.
    #
    # response_metadata가 없는 과거 호출은
    # 처리된 sample 수를 사용한다.
    api_received_count = _safe_int(
        normalized_response.get(
            "received_count",
            processed_sample_count,
        ),
        processed_sample_count,
    )

    if api_received_count < 0:
        api_received_count = 0

    collection_status = (
        _normalize_collection_status(
            response_metadata=(
                normalized_response
            ),
            received_count=(
                api_received_count
            ),
        )
    )

    response_total = _safe_int(
        normalized_response.get(
            "total",
            api_received_count,
        ),
        api_received_count,
    )

    response_start = _safe_int(
        normalized_response.get(
            "start",
            1,
        ),
        1,
    )

    response_display = _safe_int(
        normalized_response.get(
            "display",
            api_received_count,
        ),
        api_received_count,
    )

    attempt_count = _safe_int(
        normalized_response.get(
            "attempt_count",
            1,
        ),
        1,
    )

    if attempt_count < 1:
        attempt_count = 1

    normalized_captured_at = str(
        captured_at or ""
    ).strip()

    if not normalized_captured_at:
        normalized_captured_at = (
            _get_current_iso_datetime()
        )

    return {
        "schema_version": (
            SCHEMA_VERSION
        ),

        "captured_at": (
            normalized_captured_at
        ),

        "source_record_type": str(
            source_record_type
        ).strip() or "direct_api_capture",

        "query": {
            "input_keyword": str(
                keyword
            ).strip(),

            "normalized_keyword": (
                normalized_keyword
            ),
        },

        "request": {
            "source": (
                "naver_search_shopping_api"
            ),

            "display": int(display),

            "sort": normalized_sort,
        },

        # API 응답 및 수집상태
        "response": {
            "collection_status": (
                collection_status
            ),

            # 전체 검색결과 수
            "total": response_total,

            # 요청 시작 위치
            "start": response_start,

            # API 응답 display 값
            "display": response_display,

            # API에서 실제 수신한 상품 수
            "received_count": (
                api_received_count
            ),

            # API 응답 생성일
            "last_build_date": str(
                normalized_response.get(
                    "last_build_date",
                    "",
                )
            ).strip(),

            # 재시도 포함 최종 시도 횟수
            "attempt_count": (
                attempt_count
            ),
        },

        "processing": {
            # 실제 sample 변환에 성공한 수
            "sample_count": (
                processed_sample_count
            ),

            "processor_version": (
                PROCESSOR_VERSION
            ),

            "analyzer_version": (
                ANALYZER_VERSION
            ),
        },

        # 상품명·카테고리·참고정보와
        # source_item 원본 부가정보가 저장된다.
        "samples": normalized_samples,

        "aggregates": (
            normalized_analysis
        ),

        "query_validation": (
            normalized_validation
        ),

        # SearchAd 연결 등을 위해 미리 유지
        "related_keywords": [],
    }


def _serialize_json_line(
    observation: dict[str, Any],
) -> str:
    """
    JSONL 저장용 한 줄 JSON 문자열을 만든다.
    """
    try:
        return json.dumps(
            observation,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    except (
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        raise ObservationStoreError(
            (
                "관찰기록을 JSON 문자열로 "
                "변환하지 못했습니다."
            )
        ) from error


def append_observation(
    observation: dict[str, Any],
    file_path: Path | str = (
        OBSERVATION_FILE
    ),
) -> Path:
    """
    관찰기록 한 건을 JSONL 파일 끝에 추가한다.

    각 관찰기록은 정확히 한 줄에 저장된다.
    """
    if not isinstance(observation, dict):
        raise ObservationStoreError(
            "저장할 관찰기록은 dict여야 합니다."
        )

    target_path = Path(file_path)

    target_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    serialized_line = (
        _serialize_json_line(
            observation
        )
    )

    try:
        with target_path.open(
            mode="a",
            encoding="utf-8",
            newline="\n",
        ) as file:
            file.write(serialized_line)
            file.write("\n")

            # 운영체제 버퍼까지 최대한 즉시 반영
            file.flush()
            os.fsync(file.fileno())

    except OSError as error:
        raise ObservationStoreError(
            (
                "관찰이력 JSONL 저장에 "
                f"실패했습니다: {target_path}"
            )
        ) from error

    return target_path


def make_safe_filename(
    text: str,
    max_length: int = 120,
) -> str:
    """
    Windows에서도 사용할 수 있는 파일명으로 바꾼다.
    """
    normalized_text = normalize_keyword(
        text
    )

    # Windows 금지문자 및 제어문자
    safe_name = re.sub(
        r'[<>:"/\\|?*\x00-\x1f]',
        "_",
        normalized_text,
    )

    # 연속 밑줄 정리
    safe_name = re.sub(
        r"_+",
        "_",
        safe_name,
    )

    # Windows에서는 파일명 끝의 점과 공백 사용 불가
    safe_name = safe_name.strip(
        " ._"
    )

    if not safe_name:
        safe_name = "unknown_keyword"

    return safe_name[:max_length]


def _get_record_keyword(
    observation: dict[str, Any],
) -> str:
    """
    관찰기록에서 검색어를 추출한다.
    """
    query = observation.get(
        "query",
        {},
    )

    if not isinstance(query, dict):
        return ""

    normalized_keyword = normalize_keyword(
        query.get(
            "normalized_keyword",
            "",
        )
    )

    if normalized_keyword:
        return normalized_keyword

    return normalize_keyword(
        query.get(
            "input_keyword",
            "",
        )
    )


def _atomic_write_pretty_json(
    target_path: Path,
    observation: dict[str, Any],
) -> None:
    """
    읽기용 JSON을 임시파일에 먼저 저장한 뒤
    최종 파일로 교체한다.

    저장 중 프로그램이 중단돼도 기존 최신파일이
    반쯤 작성된 상태로 남는 가능성을 줄인다.
    """
    target_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=target_path.parent,
            prefix=(
                f".{target_path.stem}_"
            ),
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            json.dump(
                observation,
                temporary_file,
                ensure_ascii=False,
                indent=2,
            )

            temporary_file.write("\n")
            temporary_file.flush()

            os.fsync(
                temporary_file.fileno()
            )

            temporary_path = Path(
                temporary_file.name
            )

        os.replace(
            temporary_path,
            target_path,
        )

    except (
        OSError,
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            try:
                temporary_path.unlink()
            except OSError:
                pass

        raise ObservationStoreError(
            (
                "읽기용 최신 JSON 저장에 "
                f"실패했습니다: {target_path}"
            )
        ) from error


def save_pretty_observation(
    observation: dict[str, Any],
    keyword: str | None = None,
    directory: Path | str = (
        LATEST_READABLE_DIR
    ),
) -> Path:
    """
    키워드별 최신 관찰기록을 들여쓰기된 JSON으로 저장한다.

    keyword가 생략되면 observation.query에서
    검색어를 자동 추출한다.
    """
    if not isinstance(observation, dict):
        raise ObservationStoreError(
            "읽기용으로 저장할 관찰기록은 dict여야 합니다."
        )

    selected_keyword = normalize_keyword(
        keyword or ""
    )

    if not selected_keyword:
        selected_keyword = (
            _get_record_keyword(
                observation
            )
        )

    if not selected_keyword:
        raise ObservationStoreError(
            (
                "읽기용 JSON 파일명을 만들 "
                "검색어가 없습니다."
            )
        )

    safe_filename = make_safe_filename(
        selected_keyword
    )

    target_path = (
        Path(directory)
        / f"{safe_filename}.json"
    )

    _atomic_write_pretty_json(
        target_path=target_path,
        observation=observation,
    )

    return target_path


def load_observations(
    file_path: Path | str = (
        OBSERVATION_FILE
    ),
) -> list[dict[str, Any]]:
    """
    JSONL 관찰기록을 모두 읽는다.

    빈 줄은 건너뛰며,
    잘못된 JSON이 있으면 줄 번호를 포함해 오류를 발생시킨다.
    """
    target_path = Path(file_path)

    if not target_path.exists():
        return []

    observations: list[
        dict[str, Any]
    ] = []

    try:
        with target_path.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            for line_number, line in enumerate(
                file,
                start=1,
            ):
                normalized_line = line.strip()

                if not normalized_line:
                    continue

                try:
                    observation = json.loads(
                        normalized_line
                    )

                except json.JSONDecodeError as error:
                    raise ObservationStoreError(
                        (
                            "JSONL 해석 실패: "
                            f"{target_path}, "
                            f"{line_number}번째 줄, "
                            f"{error}"
                        )
                    ) from error

                if not isinstance(
                    observation,
                    dict,
                ):
                    raise ObservationStoreError(
                        (
                            "JSONL 관찰기록이 "
                            "객체 형식이 아닙니다: "
                            f"{target_path}, "
                            f"{line_number}번째 줄"
                        )
                    )

                observations.append(
                    observation
                )

    except ObservationStoreError:
        raise

    except OSError as error:
        raise ObservationStoreError(
            (
                "관찰이력 JSONL을 읽지 "
                f"못했습니다: {target_path}"
            )
        ) from error

    return observations


def find_observations(
    keyword: str,
    observations: (
        Iterable[dict[str, Any]]
        | None
    ) = None,
    file_path: Path | str = (
        OBSERVATION_FILE
    ),
) -> list[dict[str, Any]]:
    """
    검색어가 정확히 일치하는 모든 관찰기록을 찾는다.
    """
    normalized_keyword = normalize_keyword(
        keyword
    )

    if not normalized_keyword:
        return []

    source_observations = (
        list(observations)
        if observations is not None
        else load_observations(
            file_path=file_path
        )
    )

    return [
        observation
        for observation in source_observations
        if isinstance(observation, dict)
        and _get_record_keyword(
            observation
        ) == normalized_keyword
    ]


def _get_capture_datetime(
    observation: dict[str, Any],
) -> datetime:
    """
    관찰기록의 captured_at을 비교 가능한 날짜로 변환한다.

    과거 자료에 시간대가 없으면 UTC로 간주한다.
    날짜를 해석할 수 없으면 가장 오래된 날짜로 처리한다.
    """
    captured_at = str(
        observation.get(
            "captured_at",
            "",
        )
    ).strip()

    try:
        parsed_datetime = (
            datetime.fromisoformat(
                captured_at
            )
        )

    except (
        TypeError,
        ValueError,
    ):
        return datetime.min.replace(
            tzinfo=timezone.utc
        )

    if parsed_datetime.tzinfo is None:
        return parsed_datetime.replace(
            tzinfo=timezone.utc
        )

    return parsed_datetime


def find_latest_observation(
    keyword: str,
    observations: (
        Iterable[dict[str, Any]]
        | None
    ) = None,
    file_path: Path | str = (
        OBSERVATION_FILE
    ),
) -> dict[str, Any] | None:
    """
    특정 검색어의 가장 최근 관찰기록을 반환한다.
    """
    matched_observations = (
        find_observations(
            keyword=keyword,
            observations=observations,
            file_path=file_path,
        )
    )

    if not matched_observations:
        return None

    return max(
        matched_observations,
        key=_get_capture_datetime,
    )


def get_latest_pretty_path(
    keyword: str,
    directory: Path | str = (
        LATEST_READABLE_DIR
    ),
) -> Path:
    """
    검색어에 해당하는 읽기용 최신 JSON 경로를 만든다.
    """
    normalized_keyword = normalize_keyword(
        keyword
    )

    if not normalized_keyword:
        raise ObservationStoreError(
            "읽기용 최신파일의 검색어가 비어 있습니다."
        )

    return (
        Path(directory)
        / f"{make_safe_filename(normalized_keyword)}.json"
    )


def _load_pretty_json_safely(
    file_path: Path,
) -> dict[str, Any] | None:
    """
    읽기용 JSON을 안전하게 읽는다.

    파일이 없거나 손상되면 None을 반환한다.
    """
    if not file_path.exists():
        return None

    try:
        with file_path.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            loaded_data = json.load(file)

    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ):
        return None

    if not isinstance(
        loaded_data,
        dict,
    ):
        return None

    return loaded_data


def ensure_latest_pretty_file(
    keyword: str,
    observation: dict[str, Any] | None = None,
    directory: Path | str = (
        LATEST_READABLE_DIR
    ),
    file_path: Path | str = (
        OBSERVATION_FILE
    ),
    force: bool = False,
) -> tuple[Path | None, bool]:
    """
    읽기용 최신 JSON이 없거나 손상됐거나 오래된 경우
    JSONL의 최신 관찰기록으로 다시 생성한다.

    Returns
    -------
    tuple
        파일 경로,
        이번 호출에서 새로 작성했는지 여부
    """
    normalized_keyword = normalize_keyword(
        keyword
    )

    if not normalized_keyword:
        raise ObservationStoreError(
            "최신파일을 확인할 검색어가 비어 있습니다."
        )

    # 이미 최신 관찰기록이 전달됐다면 그것을 사용한다.
    # 그렇지 않으면 JSONL에서 찾아온다.
    latest_observation = (
        observation
        if isinstance(observation, dict)
        else find_latest_observation(
            keyword=normalized_keyword,
            file_path=file_path,
        )
    )

    if latest_observation is None:
        return None, False

    target_path = get_latest_pretty_path(
        keyword=normalized_keyword,
        directory=directory,
    )

    should_write = (
        force
        or not target_path.exists()
    )

    if not should_write:
        existing_observation = (
            _load_pretty_json_safely(
                target_path
            )
        )

        # 파일은 있으나 정상 JSON이 아님
        if existing_observation is None:
            should_write = True

        else:
            existing_keyword = (
                _get_record_keyword(
                    existing_observation
                )
            )

            # 파일 내부 검색어가 현재 검색어와 다름
            if (
                existing_keyword
                != normalized_keyword
            ):
                should_write = True

            else:
                existing_datetime = (
                    _get_capture_datetime(
                        existing_observation
                    )
                )

                latest_datetime = (
                    _get_capture_datetime(
                        latest_observation
                    )
                )

                # JSONL 쪽 자료가 더 최신임
                if (
                    existing_datetime
                    < latest_datetime
                ):
                    should_write = True

    if should_write:
        target_path = (
            save_pretty_observation(
                observation=latest_observation,
                keyword=normalized_keyword,
                directory=directory,
            )
        )

    return target_path, should_write



def rebuild_latest_pretty_files(
    file_path: Path | str = (
        OBSERVATION_FILE
    ),
    directory: Path | str = (
        LATEST_READABLE_DIR
    ),
) -> dict[str, Path]:
    """
    JSONL 전체를 읽어 검색어별 가장 최신 기록으로
    읽기용 JSON 파일을 다시 생성한다.

    Returns
    -------
    dict
        검색어와 생성된 파일 경로.
    """
    observations = load_observations(
        file_path=file_path
    )

    latest_by_keyword: dict[
        str,
        dict[str, Any],
    ] = {}

    for observation in observations:
        keyword = _get_record_keyword(
            observation
        )

        if not keyword:
            continue

        current_latest = (
            latest_by_keyword.get(
                keyword
            )
        )

        if current_latest is None:
            latest_by_keyword[
                keyword
            ] = observation

            continue

        if (
            _get_capture_datetime(
                observation
            )
            >
            _get_capture_datetime(
                current_latest
            )
        ):
            latest_by_keyword[
                keyword
            ] = observation

    saved_paths: dict[str, Path] = {}

    for keyword, observation in (
        latest_by_keyword.items()
    ):
        saved_paths[keyword] = (
            save_pretty_observation(
                observation=observation,
                keyword=keyword,
                directory=directory,
            )
        )

    return saved_paths