from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .observation_store import (
    OBSERVATION_FILE,
    normalize_keyword,
)


# =========================================================
# 검색 인덱스 기본 경로·버전
# =========================================================

PACKAGE_DIR = Path(__file__).resolve().parent

SEARCH_INDEX_DIR = (
    PACKAGE_DIR
    / "data"
    / "search_index"
)

OBSERVATION_SEARCH_INDEX_FILE = (
    SEARCH_INDEX_DIR
    / "observation_search_index.json"
)

SEARCH_INDEX_SCHEMA_VERSION = "1.1"
SUPPORTED_SEARCH_INDEX_SCHEMA_VERSIONS = {
    "1.0",
    "1.1",
}

# 원본이 기존 인덱스 생성 이후 단순 추가(append)되었는지
# 가볍게 확인하기 위한 앞·뒤 바이트 지문 크기.
SOURCE_SIGNATURE_CHUNK_SIZE = 4096


class ObservationSearchIndexError(RuntimeError):
    """
    관찰사전 검색 인덱스 생성·조회·갱신 과정에서 발생하는 오류.
    """


def _get_current_iso_datetime() -> str:
    """
    현재 지역 시간대를 포함한 ISO 날짜 문자열을 만든다.
    """
    return (
        datetime.now()
        .astimezone()
        .replace(microsecond=0)
        .isoformat()
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

    except (
        TypeError,
        ValueError,
    ):
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


def _extract_record_keyword(
    observation: dict[str, Any],
) -> str:
    """
    관찰기록의 query에서 검색 키워드를 추출한다.

    normalized_keyword가 있으면 우선 사용하고,
    없으면 input_keyword를 사용한다.
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


def _atomic_write_json(
    target_path: Path,
    data: dict[str, Any],
) -> None:
    """
    임시파일에 먼저 저장한 뒤 최종 인덱스 파일로 교체한다.

    처리 도중 프로그램이 중단돼도 기존 인덱스가
    반쯤 작성된 파일로 바뀌는 것을 방지한다.
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
            prefix=f".{target_path.stem}_",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            json.dump(
                data,
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

        raise ObservationSearchIndexError(
            (
                "검색 인덱스 파일 저장에 실패했습니다: "
                f"{target_path}"
            )
        ) from error


def _hash_bytes(
    data: bytes,
) -> str:
    """
    바이트 자료의 SHA-256 해시를 반환한다.
    """
    return hashlib.sha256(data).hexdigest()


def _read_source_signatures(
    source_path: Path,
    indexed_size_bytes: int,
) -> dict[str, Any]:
    """
    현재까지 인덱싱한 원본 구간의 앞부분과 끝부분 지문을 만든다.

    이후 업데이트에서 원본의 기존 구간이 바뀌지 않고
    뒤에 새 기록만 추가됐는지 확인하는 용도다.
    """
    if indexed_size_bytes < 0:
        raise ObservationSearchIndexError(
            "인덱싱 원본 크기가 올바르지 않습니다."
        )

    try:
        actual_size_bytes = source_path.stat().st_size

        if actual_size_bytes < indexed_size_bytes:
            raise ObservationSearchIndexError(
                (
                    "원본 파일이 인덱싱 기준 크기보다 작습니다: "
                    f"현재 {actual_size_bytes:,}바이트 / "
                    f"기준 {indexed_size_bytes:,}바이트"
                )
            )

        first_chunk_size = min(
            SOURCE_SIGNATURE_CHUNK_SIZE,
            indexed_size_bytes,
        )
        tail_chunk_size = min(
            SOURCE_SIGNATURE_CHUNK_SIZE,
            indexed_size_bytes,
        )

        with source_path.open("rb") as source_file:
            first_chunk = source_file.read(
                first_chunk_size
            )

            if tail_chunk_size > 0:
                source_file.seek(
                    indexed_size_bytes
                    - tail_chunk_size
                )
                tail_chunk = source_file.read(
                    tail_chunk_size
                )
            else:
                tail_chunk = b""

    except ObservationSearchIndexError:
        raise

    except OSError as error:
        raise ObservationSearchIndexError(
            (
                "원본 파일 지문을 확인하지 못했습니다: "
                f"{source_path}"
            )
        ) from error

    return {
        "algorithm": "sha256",
        "first_chunk_size_bytes": (
            first_chunk_size
        ),
        "first_chunk_sha256": (
            _hash_bytes(first_chunk)
        ),
        "indexed_tail_size_bytes": (
            tail_chunk_size
        ),
        "indexed_tail_sha256": (
            _hash_bytes(tail_chunk)
        ),
    }


def _verify_append_only_source(
    source_path: Path,
    previous_size_bytes: int,
    signatures: dict[str, Any],
) -> bool:
    """
    기존 인덱싱 구간이 그대로 유지됐는지 확인한다.

    Returns
    -------
    bool
        지문 검증을 실제 수행했으면 True.
        구버전 인덱스라 지문이 없으면 False.
    """
    first_chunk_size = _safe_int(
        signatures.get(
            "first_chunk_size_bytes"
        )
    )
    first_chunk_sha256 = str(
        signatures.get(
            "first_chunk_sha256",
            "",
        )
    ).strip()

    tail_chunk_size = _safe_int(
        signatures.get(
            "indexed_tail_size_bytes"
        )
    )
    tail_chunk_sha256 = str(
        signatures.get(
            "indexed_tail_sha256",
            "",
        )
    ).strip()

    has_signatures = (
        first_chunk_size >= 0
        and tail_chunk_size >= 0
        and bool(first_chunk_sha256)
        and bool(tail_chunk_sha256)
    )

    if not has_signatures:
        # schema 1.0으로 재구축된 기존 인덱스도
        # 첫 업데이트는 가능하게 하며, 저장 후 1.1 지문을 추가한다.
        return False

    try:
        with source_path.open("rb") as source_file:
            first_chunk = source_file.read(
                first_chunk_size
            )

            if tail_chunk_size > 0:
                source_file.seek(
                    previous_size_bytes
                    - tail_chunk_size
                )
                tail_chunk = source_file.read(
                    tail_chunk_size
                )
            else:
                tail_chunk = b""

    except OSError as error:
        raise ObservationSearchIndexError(
            (
                "업데이트 전 원본 파일 지문을 읽지 못했습니다: "
                f"{source_path}"
            )
        ) from error

    if _hash_bytes(first_chunk) != first_chunk_sha256:
        raise ObservationSearchIndexError(
            (
                "관찰사전 앞부분이 기존 인덱스 생성 이후 변경됐습니다. "
                "증분 업데이트 대신 '검색인덱스 재구축'을 실행해 주세요."
            )
        )

    if _hash_bytes(tail_chunk) != tail_chunk_sha256:
        raise ObservationSearchIndexError(
            (
                "관찰사전의 기존 인덱싱 구간이 변경됐습니다. "
                "증분 업데이트 대신 '검색인덱스 재구축'을 실행해 주세요."
            )
        )

    return True


def load_observation_search_index(
    index_path: Path | str = (
        OBSERVATION_SEARCH_INDEX_FILE
    ),
) -> dict[str, Any]:
    """
    저장된 검색 인덱스 파일을 읽고 기본 구조를 검사한다.
    """
    target_path = Path(index_path)

    if not target_path.exists():
        raise ObservationSearchIndexError(
            (
                "검색 인덱스 파일이 없습니다: "
                f"{target_path}\n"
                "먼저 '검색인덱스 재구축'을 실행해 주세요."
            )
        )

    try:
        with target_path.open(
            mode="r",
            encoding="utf-8",
        ) as index_file:
            index_data = json.load(
                index_file
            )

    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as error:
        raise ObservationSearchIndexError(
            (
                "검색 인덱스 파일을 읽지 못했습니다: "
                f"{target_path}\n"
                "'검색인덱스 재구축'을 실행해 주세요."
            )
        ) from error

    if not isinstance(index_data, dict):
        raise ObservationSearchIndexError(
            (
                "검색 인덱스가 객체 형식이 아닙니다: "
                f"{target_path}"
            )
        )

    schema_version = str(
        index_data.get(
            "schema_version",
            "",
        )
    ).strip()

    if schema_version not in (
        SUPPORTED_SEARCH_INDEX_SCHEMA_VERSIONS
    ):
        raise ObservationSearchIndexError(
            (
                "지원하지 않는 검색 인덱스 버전입니다: "
                f"'{schema_version}'\n"
                "'검색인덱스 재구축'을 실행해 주세요."
            )
        )

    keywords = _safe_list(
        index_data.get(
            "keywords"
        )
    )

    if any(
        not isinstance(keyword, str)
        for keyword in keywords
    ):
        raise ObservationSearchIndexError(
            "검색 인덱스의 키워드 목록 형식이 올바르지 않습니다."
        )

    normalized_keywords = [
        normalize_keyword(keyword)
        for keyword in keywords
        if normalize_keyword(keyword)
    ]

    if len(normalized_keywords) != len(
        set(normalized_keywords)
    ):
        raise ObservationSearchIndexError(
            (
                "검색 인덱스에 중복 키워드가 있습니다. "
                "'검색인덱스 재구축'을 실행해 주세요."
            )
        )

    source = _safe_dict(
        index_data.get(
            "source"
        )
    )

    source_size_bytes = _safe_int(
        source.get(
            "size_bytes"
        ),
        -1,
    )

    if source_size_bytes < 0:
        raise ObservationSearchIndexError(
            (
                "검색 인덱스에 원본 파일 크기 정보가 없습니다. "
                "'검색인덱스 재구축'을 실행해 주세요."
            )
        )

    # 이후 함수에서 정규화된 값을 그대로 사용할 수 있게 정리한다.
    index_data["keywords"] = normalized_keywords
    index_data["keyword_count"] = len(
        normalized_keywords
    )

    return index_data



def load_observation_search_memory_index(
    index_path: Path | str = (
        OBSERVATION_SEARCH_INDEX_FILE
    ),
) -> dict[str, Any]:
    """
    저장된 검색 인덱스를 빠른 조회용 메모리 구조로 변환한다.

    디스크 인덱스의 키워드 목록을 한 번 읽어 다음 두 구조를 만든다.

    - keyword_list: 포함검색과 정렬에 사용하는 불변 튜플
    - keyword_set: 정확 일치 여부를 빠르게 확인하는 불변 집합

    이 메모리 구조는 프로그램이 종료되면 사라지며,
    다음 실행 시 인덱스 파일에서 다시 생성한다.
    """
    target_path = Path(
        index_path
    )

    index_data = load_observation_search_index(
        target_path
    )

    keyword_list = tuple(
        index_data.get(
            "keywords",
            [],
        )
    )

    keyword_set = frozenset(
        keyword_list
    )

    if len(keyword_list) != len(keyword_set):
        raise ObservationSearchIndexError(
            (
                "검색 인덱스 메모리 변환 중 중복 키워드가 "
                "확인됐습니다. '검색인덱스 재구축'을 실행해 주세요."
            )
        )

    return {
        "loaded": True,
        "keyword_list": keyword_list,
        "keyword_set": keyword_set,
        "keyword_count": len(keyword_list),
        "schema_version": str(
            index_data.get(
                "schema_version",
                "",
            )
        ),
        "built_at": str(
            index_data.get(
                "built_at",
                "",
            )
        ),
        "updated_at": str(
            index_data.get(
                "updated_at",
                "",
            )
        ),
        "index_path": str(
            target_path
        ),
    }



def find_containing_search_keywords(
    search_term: str,
    keyword_list: tuple[str, ...] | list[str],
    *,
    exclude_exact: bool = True,
) -> list[str]:
    """
    메모리 키워드 목록에서 입력어를 포함하는 키워드를 찾는다.

    검색 순서는 다음 기준을 따른다.

    1. 입력어로 시작하는 키워드
    2. 입력어가 중간이나 끝에 포함된 키워드
    3. 글자 수가 짧은 키워드
    4. 가나다·영문 순서

    정확 일치 키워드는 별도 결과로 표시할 수 있도록 기본적으로
    연관 키워드 목록에서 제외한다. JSONL이나 latest 파일은 읽지 않고
    프로그램 시작 시 메모리에 올린 keyword_list만 순회한다.
    """
    normalized_term = normalize_keyword(
        search_term
    )

    if not normalized_term:
        return []

    folded_term = normalized_term.casefold()
    ranked_matches: list[tuple[tuple[Any, ...], str]] = []

    for raw_keyword in keyword_list:
        normalized_keyword = normalize_keyword(
            raw_keyword
        )

        if not normalized_keyword:
            continue

        folded_keyword = normalized_keyword.casefold()

        if (
            exclude_exact
            and folded_keyword == folded_term
        ):
            continue

        match_position = folded_keyword.find(
            folded_term
        )

        if match_position < 0:
            continue

        starts_with_term = (
            match_position == 0
        )

        rank = (
            0 if starts_with_term else 1,
            len(normalized_keyword),
            folded_keyword,
            normalized_keyword,
        )

        ranked_matches.append(
            (
                rank,
                normalized_keyword,
            )
        )

    ranked_matches.sort(
        key=lambda item: item[0]
    )

    return [
        keyword
        for _, keyword in ranked_matches
    ]



def get_observation_search_index_status(
    source_path: Path | str = OBSERVATION_FILE,
    index_path: Path | str = (
        OBSERVATION_SEARCH_INDEX_FILE
    ),
) -> dict[str, Any]:
    """
    검색 인덱스와 관찰사전 원본의 현재 상태를 빠르게 비교한다.

    이 함수는 원본 JSONL 전체를 읽지 않고 다음 정보만 확인한다.

    - 검색 인덱스 파일 존재·해석 가능 여부
    - 인덱스에 기록된 키워드 수와 관찰기록 수
    - 현재 원본 파일 크기와 인덱싱 기준 크기
    - 기존 인덱싱 구간의 앞·뒤 지문
    - 업데이트 또는 재구축 필요 여부

    Returns
    -------
    dict
        status_code
            ready
            update_required
            rebuild_required
            source_missing

        recommended_command
            현재 상태에서 권장하는 명령. 필요한 작업이 없으면 빈 문자열.
    """
    observation_path = Path(
        source_path
    )
    target_path = Path(
        index_path
    )

    base_result: dict[str, Any] = {
        "source_path": str(
            observation_path
        ),
        "index_path": str(
            target_path
        ),
        "source_exists": (
            observation_path.exists()
        ),
        "index_exists": (
            target_path.exists()
        ),
        "status_code": "",
        "status_label": "",
        "message": "",
        "recommended_command": "",
        "schema_version": "",
        "built_at": "",
        "updated_at": "",
        "update_count": 0,
        "keyword_count": 0,
        "duplicate_record_count": 0,
        "indexed_valid_record_count": 0,
        "indexed_total_line_count": 0,
        "indexed_size_bytes": 0,
        "current_size_bytes": 0,
        "pending_size_bytes": 0,
        "indexed_modified_time_ns": 0,
        "current_modified_time_ns": 0,
        "last_update_mode": "",
        "last_added_keyword_count": 0,
        "last_appended_valid_record_count": 0,
        "signature_available": False,
        "signature_verified": False,
    }

    if not observation_path.exists():
        base_result.update(
            {
                "status_code": "source_missing",
                "status_label": "관찰사전 원본 없음",
                "message": (
                    "관찰사전 원본 파일을 찾을 수 없습니다."
                ),
            }
        )
        return base_result

    try:
        source_stat = observation_path.stat()

    except OSError as error:
        raise ObservationSearchIndexError(
            (
                "관찰사전 원본의 파일정보를 확인하지 못했습니다: "
                f"{observation_path}"
            )
        ) from error

    current_size_bytes = int(
        source_stat.st_size
    )
    current_modified_time_ns = int(
        source_stat.st_mtime_ns
    )

    base_result[
        "current_size_bytes"
    ] = current_size_bytes
    base_result[
        "current_modified_time_ns"
    ] = current_modified_time_ns

    if not target_path.exists():
        base_result.update(
            {
                "status_code": "rebuild_required",
                "status_label": "재구축 필요",
                "message": (
                    "검색 인덱스 파일이 없습니다."
                ),
                "recommended_command": (
                    "검색인덱스 재구축"
                ),
            }
        )
        return base_result

    try:
        index_data = load_observation_search_index(
            index_path=target_path
        )

    except ObservationSearchIndexError as error:
        base_result.update(
            {
                "status_code": "rebuild_required",
                "status_label": "재구축 필요",
                "message": str(error),
                "recommended_command": (
                    "검색인덱스 재구축"
                ),
            }
        )
        return base_result

    source = _safe_dict(
        index_data.get(
            "source"
        )
    )
    last_update = _safe_dict(
        index_data.get(
            "last_update"
        )
    )
    signatures = _safe_dict(
        source.get(
            "signatures"
        )
    )

    indexed_size_bytes = _safe_int(
        source.get(
            "size_bytes"
        ),
        -1,
    )
    indexed_modified_time_ns = _safe_int(
        source.get(
            "modified_time_ns"
        )
    )

    stored_source_path = str(
        source.get(
            "file_path",
            "",
        )
    ).strip()

    base_result.update(
        {
            "schema_version": str(
                index_data.get(
                    "schema_version",
                    "",
                )
            ).strip(),
            "built_at": str(
                index_data.get(
                    "built_at",
                    "",
                )
            ).strip(),
            "updated_at": str(
                index_data.get(
                    "updated_at",
                    "",
                )
            ).strip(),
            "update_count": _safe_int(
                index_data.get(
                    "update_count"
                )
            ),
            "keyword_count": _safe_int(
                index_data.get(
                    "keyword_count"
                )
            ),
            "duplicate_record_count": _safe_int(
                index_data.get(
                    "duplicate_record_count"
                )
            ),
            "indexed_valid_record_count": _safe_int(
                source.get(
                    "valid_record_count"
                )
            ),
            "indexed_total_line_count": _safe_int(
                source.get(
                    "total_line_count"
                )
            ),
            "indexed_size_bytes": max(
                0,
                indexed_size_bytes,
            ),
            "pending_size_bytes": max(
                0,
                current_size_bytes
                - max(0, indexed_size_bytes),
            ),
            "indexed_modified_time_ns": (
                indexed_modified_time_ns
            ),
            "last_update_mode": str(
                last_update.get(
                    "mode",
                    "",
                )
            ).strip(),
            "last_added_keyword_count": _safe_int(
                last_update.get(
                    "added_keyword_count"
                )
            ),
            "last_appended_valid_record_count": _safe_int(
                last_update.get(
                    "appended_valid_record_count"
                )
            ),
            "signature_available": bool(
                str(
                    signatures.get(
                        "first_chunk_sha256",
                        "",
                    )
                ).strip()
                and str(
                    signatures.get(
                        "indexed_tail_sha256",
                        "",
                    )
                ).strip()
            ),
        }
    )

    if indexed_size_bytes < 0:
        base_result.update(
            {
                "status_code": "rebuild_required",
                "status_label": "재구축 필요",
                "message": (
                    "인덱스의 원본 크기 정보가 올바르지 않습니다."
                ),
                "recommended_command": (
                    "검색인덱스 재구축"
                ),
            }
        )
        return base_result

    if stored_source_path:
        try:
            stored_normalized_path = os.path.normcase(
                os.path.abspath(
                    stored_source_path
                )
            )
            current_normalized_path = os.path.normcase(
                os.path.abspath(
                    str(observation_path)
                )
            )

        except (OSError, ValueError):
            stored_normalized_path = stored_source_path.casefold()
            current_normalized_path = str(
                observation_path
            ).casefold()

        if (
            stored_normalized_path
            != current_normalized_path
        ):
            base_result.update(
                {
                    "status_code": "rebuild_required",
                    "status_label": "재구축 필요",
                    "message": (
                        "검색 인덱스가 현재 관찰사전과 다른 원본 경로를 "
                        "기준으로 생성됐습니다."
                    ),
                    "recommended_command": (
                        "검색인덱스 재구축"
                    ),
                }
            )
            return base_result

    if current_size_bytes < indexed_size_bytes:
        base_result.update(
            {
                "status_code": "rebuild_required",
                "status_label": "재구축 필요",
                "message": (
                    "현재 관찰사전이 인덱싱 기준보다 작습니다. "
                    "기존 자료가 삭제되거나 원본이 교체된 것으로 보입니다."
                ),
                "recommended_command": (
                    "검색인덱스 재구축"
                ),
            }
        )
        return base_result

    if current_size_bytes > indexed_size_bytes:
        try:
            signature_verified = (
                _verify_append_only_source(
                    source_path=observation_path,
                    previous_size_bytes=(
                        indexed_size_bytes
                    ),
                    signatures=signatures,
                )
            )

        except ObservationSearchIndexError as error:
            base_result.update(
                {
                    "status_code": "rebuild_required",
                    "status_label": "재구축 필요",
                    "message": str(error),
                    "recommended_command": (
                        "검색인덱스 재구축"
                    ),
                }
            )
            return base_result

        base_result.update(
            {
                "status_code": "update_required",
                "status_label": "업데이트 필요",
                "message": (
                    "검색 인덱스 생성 이후 관찰사전에 새 자료가 추가됐습니다."
                ),
                "recommended_command": (
                    "검색인덱스 업데이트"
                ),
                "signature_verified": (
                    signature_verified
                ),
            }
        )
        return base_result

    # 파일 크기는 같지만 수정시각이 달라졌다면 단순 append가 아니다.
    # 상태 확인에서 원본 전체를 해시하지 않으므로 안전하게 재구축을 권장한다.
    if (
        indexed_modified_time_ns > 0
        and current_modified_time_ns
        != indexed_modified_time_ns
    ):
        base_result.update(
            {
                "status_code": "rebuild_required",
                "status_label": "재구축 필요",
                "message": (
                    "관찰사전 크기는 같지만 수정시각이 달라졌습니다. "
                    "기존 자료가 수정됐을 가능성이 있어 재구축이 필요합니다."
                ),
                "recommended_command": (
                    "검색인덱스 재구축"
                ),
            }
        )
        return base_result

    base_result.update(
        {
            "status_code": "ready",
            "status_label": "최신",
            "message": (
                "검색 인덱스가 현재 관찰사전과 일치합니다."
            ),
            "recommended_command": "",
            "signature_verified": bool(
                base_result.get(
                    "signature_available"
                )
            ),
        }
    )
    return base_result

def rebuild_observation_search_index(
    source_path: Path | str = OBSERVATION_FILE,
    target_path: Path | str = (
        OBSERVATION_SEARCH_INDEX_FILE
    ),
    *,
    progress_callback: (
        Callable[[int], None]
        | None
    ) = None,
    progress_interval: int = 5000,
) -> dict[str, Any]:
    """
    관찰사전 JSONL 전체를 한 번 읽어 검색용 키워드 인덱스를
    처음부터 다시 생성한다.

    저장되는 핵심자료는 고유 키워드 목록이며,
    정확일치용 set과 포함검색용 list는 이후 프로그램 시작 시
    이 파일을 읽어 메모리에 만들 수 있다.

    원본 JSONL은 수정하지 않는다.
    """
    observation_path = Path(
        source_path
    )
    index_path = Path(
        target_path
    )

    if not observation_path.exists():
        raise ObservationSearchIndexError(
            (
                "관찰사전 원본 파일이 없습니다: "
                f"{observation_path}"
            )
        )

    if progress_interval < 1:
        progress_interval = 5000

    keyword_set: set[str] = set()

    total_line_count = 0
    empty_line_count = 0
    valid_record_count = 0
    missing_keyword_count = 0

    try:
        with observation_path.open(
            mode="r",
            encoding="utf-8",
        ) as source_file:
            for line_number, line in enumerate(
                source_file,
                start=1,
            ):
                total_line_count += 1

                normalized_line = line.strip()

                if not normalized_line:
                    empty_line_count += 1
                    continue

                try:
                    observation = json.loads(
                        normalized_line
                    )

                except json.JSONDecodeError as error:
                    raise ObservationSearchIndexError(
                        (
                            "관찰사전 JSONL 해석 실패: "
                            f"{observation_path}, "
                            f"{line_number}번째 줄, "
                            f"{error}"
                        )
                    ) from error

                if not isinstance(
                    observation,
                    dict,
                ):
                    raise ObservationSearchIndexError(
                        (
                            "관찰사전 기록이 객체 형식이 아닙니다: "
                            f"{observation_path}, "
                            f"{line_number}번째 줄"
                        )
                    )

                valid_record_count += 1

                keyword = _extract_record_keyword(
                    observation
                )

                if keyword:
                    keyword_set.add(
                        keyword
                    )
                else:
                    missing_keyword_count += 1

                if (
                    progress_callback is not None
                    and valid_record_count
                    % progress_interval
                    == 0
                ):
                    progress_callback(
                        valid_record_count
                    )

    except ObservationSearchIndexError:
        raise

    except (
        OSError,
        UnicodeDecodeError,
    ) as error:
        raise ObservationSearchIndexError(
            (
                "관찰사전 원본을 읽지 못했습니다: "
                f"{observation_path}"
            )
        ) from error

    keywords = sorted(
        keyword_set,
        key=lambda keyword: (
            keyword.casefold(),
            keyword,
        ),
    )

    duplicate_record_count = max(
        0,
        valid_record_count
        - missing_keyword_count
        - len(keywords),
    )

    try:
        source_stat = observation_path.stat()
    except OSError as error:
        raise ObservationSearchIndexError(
            (
                "관찰사전 원본의 파일정보를 확인하지 못했습니다: "
                f"{observation_path}"
            )
        ) from error

    source_signatures = _read_source_signatures(
        source_path=observation_path,
        indexed_size_bytes=int(
            source_stat.st_size
        ),
    )

    current_datetime = (
        _get_current_iso_datetime()
    )

    index_data: dict[str, Any] = {
        "schema_version": (
            SEARCH_INDEX_SCHEMA_VERSION
        ),
        "built_at": current_datetime,
        "updated_at": current_datetime,
        "update_count": 0,
        "source": {
            "file_path": str(
                observation_path
            ),
            "size_bytes": int(
                source_stat.st_size
            ),
            "modified_time_ns": int(
                source_stat.st_mtime_ns
            ),
            "total_line_count": (
                total_line_count
            ),
            "valid_record_count": (
                valid_record_count
            ),
            "empty_line_count": (
                empty_line_count
            ),
            "missing_keyword_count": (
                missing_keyword_count
            ),
            "signatures": source_signatures,
        },
        "keyword_count": len(
            keywords
        ),
        "duplicate_record_count": (
            duplicate_record_count
        ),
        "keywords": keywords,
        "last_update": {
            "mode": "rebuild",
            "updated_at": current_datetime,
            "previous_size_bytes": 0,
            "appended_size_bytes": int(
                source_stat.st_size
            ),
            "appended_line_count": (
                total_line_count
            ),
            "appended_valid_record_count": (
                valid_record_count
            ),
            "appended_empty_line_count": (
                empty_line_count
            ),
            "appended_missing_keyword_count": (
                missing_keyword_count
            ),
            "added_keyword_count": len(
                keywords
            ),
        },
    }

    _atomic_write_json(
        target_path=index_path,
        data=index_data,
    )

    return {
        "index_path": str(
            index_path
        ),
        "source_path": str(
            observation_path
        ),
        "source_size_bytes": int(
            source_stat.st_size
        ),
        "total_line_count": (
            total_line_count
        ),
        "valid_record_count": (
            valid_record_count
        ),
        "empty_line_count": (
            empty_line_count
        ),
        "missing_keyword_count": (
            missing_keyword_count
        ),
        "duplicate_record_count": (
            duplicate_record_count
        ),
        "keyword_count": len(
            keywords
        ),
        "built_at": current_datetime,
    }


def update_observation_search_index(
    source_path: Path | str = OBSERVATION_FILE,
    target_path: Path | str = (
        OBSERVATION_SEARCH_INDEX_FILE
    ),
    *,
    progress_callback: (
        Callable[[int], None]
        | None
    ) = None,
    progress_interval: int = 1000,
) -> dict[str, Any]:
    """
    기존 검색 인덱스 생성 이후 JSONL 끝에 추가된 기록만 읽어
    신규 키워드를 인덱스에 반영한다.

    원본 JSONL의 기존 구간이 삭제·수정된 경우에는 업데이트하지
    않고 재구축을 요청한다. 검색 인덱스 파일이 없거나 손상된
    경우에도 재구축이 필요하다.
    """
    observation_path = Path(
        source_path
    )
    index_path = Path(
        target_path
    )

    if not observation_path.exists():
        raise ObservationSearchIndexError(
            (
                "관찰사전 원본 파일이 없습니다: "
                f"{observation_path}"
            )
        )

    if progress_interval < 1:
        progress_interval = 1000

    index_data = load_observation_search_index(
        index_path=index_path
    )

    previous_source = _safe_dict(
        index_data.get(
            "source"
        )
    )

    previous_size_bytes = _safe_int(
        previous_source.get(
            "size_bytes"
        ),
        -1,
    )

    if previous_size_bytes < 0:
        raise ObservationSearchIndexError(
            (
                "검색 인덱스의 원본 크기 정보가 올바르지 않습니다. "
                "'검색인덱스 재구축'을 실행해 주세요."
            )
        )

    try:
        source_stat_before = observation_path.stat()
    except OSError as error:
        raise ObservationSearchIndexError(
            (
                "관찰사전 원본의 파일정보를 확인하지 못했습니다: "
                f"{observation_path}"
            )
        ) from error

    current_size_bytes = int(
        source_stat_before.st_size
    )

    if current_size_bytes < previous_size_bytes:
        raise ObservationSearchIndexError(
            (
                "관찰사전 원본 크기가 기존 인덱스보다 작아졌습니다. "
                "자료가 삭제되거나 교체된 것으로 보입니다. "
                "'검색인덱스 재구축'을 실행해 주세요."
            )
        )

    # 기존 인덱싱 구간의 앞·끝 지문을 확인한다.
    # 구버전 1.0 인덱스는 지문이 없으므로 첫 업데이트 후 1.1로 전환한다.
    signature_verified = _verify_append_only_source(
        source_path=observation_path,
        previous_size_bytes=previous_size_bytes,
        signatures=_safe_dict(
            previous_source.get(
                "signatures"
            )
        ),
    )

    existing_keywords = {
        normalize_keyword(keyword)
        for keyword in _safe_list(
            index_data.get(
                "keywords"
            )
        )
        if normalize_keyword(keyword)
    }

    appended_size_bytes = max(
        0,
        current_size_bytes
        - previous_size_bytes,
    )

    appended_line_count = 0
    appended_empty_line_count = 0
    appended_valid_record_count = 0
    appended_missing_keyword_count = 0
    added_keywords: set[str] = set()

    previous_total_line_count = _safe_int(
        previous_source.get(
            "total_line_count"
        )
    )

    if appended_size_bytes > 0:
        try:
            with observation_path.open(
                mode="rb",
            ) as source_file:
                # 재구축 시 기록한 바이트 위치부터 새 자료만 읽는다.
                source_file.seek(
                    previous_size_bytes
                )

                for relative_line_number, raw_line in enumerate(
                    source_file,
                    start=1,
                ):
                    appended_line_count += 1
                    absolute_line_number = (
                        previous_total_line_count
                        + relative_line_number
                    )

                    try:
                        line = raw_line.decode(
                            "utf-8"
                        )
                    except UnicodeDecodeError as error:
                        raise ObservationSearchIndexError(
                            (
                                "추가된 관찰기록의 UTF-8 해석 실패: "
                                f"{observation_path}, "
                                f"{absolute_line_number}번째 줄"
                            )
                        ) from error

                    normalized_line = line.strip()

                    if not normalized_line:
                        appended_empty_line_count += 1
                        continue

                    try:
                        observation = json.loads(
                            normalized_line
                        )
                    except json.JSONDecodeError as error:
                        raise ObservationSearchIndexError(
                            (
                                "추가된 관찰사전 JSONL 해석 실패: "
                                f"{observation_path}, "
                                f"{absolute_line_number}번째 줄, "
                                f"{error}"
                            )
                        ) from error

                    if not isinstance(
                        observation,
                        dict,
                    ):
                        raise ObservationSearchIndexError(
                            (
                                "추가된 관찰기록이 객체 형식이 아닙니다: "
                                f"{observation_path}, "
                                f"{absolute_line_number}번째 줄"
                            )
                        )

                    appended_valid_record_count += 1

                    keyword = _extract_record_keyword(
                        observation
                    )

                    if not keyword:
                        appended_missing_keyword_count += 1
                    elif keyword not in existing_keywords:
                        existing_keywords.add(
                            keyword
                        )
                        added_keywords.add(
                            keyword
                        )

                    if (
                        progress_callback is not None
                        and appended_valid_record_count
                        % progress_interval
                        == 0
                    ):
                        progress_callback(
                            appended_valid_record_count
                        )

        except ObservationSearchIndexError:
            raise

        except OSError as error:
            raise ObservationSearchIndexError(
                (
                    "추가된 관찰기록을 읽지 못했습니다: "
                    f"{observation_path}"
                )
            ) from error

    # 처리 중 다른 프로세스가 원본에 자료를 더 붙였는지 확인한다.
    try:
        source_stat_after = observation_path.stat()
    except OSError as error:
        raise ObservationSearchIndexError(
            (
                "업데이트 후 관찰사전 파일정보를 확인하지 못했습니다: "
                f"{observation_path}"
            )
        ) from error

    if int(source_stat_after.st_size) != current_size_bytes:
        raise ObservationSearchIndexError(
            (
                "검색 인덱스 업데이트 중 관찰사전에 새 자료가 추가됐습니다. "
                "이번 인덱스는 저장하지 않았습니다. 잠시 후 다시 실행해 주세요."
            )
        )

    keywords = sorted(
        existing_keywords,
        key=lambda keyword: (
            keyword.casefold(),
            keyword,
        ),
    )

    total_line_count = (
        previous_total_line_count
        + appended_line_count
    )
    valid_record_count = (
        _safe_int(
            previous_source.get(
                "valid_record_count"
            )
        )
        + appended_valid_record_count
    )
    empty_line_count = (
        _safe_int(
            previous_source.get(
                "empty_line_count"
            )
        )
        + appended_empty_line_count
    )
    missing_keyword_count = (
        _safe_int(
            previous_source.get(
                "missing_keyword_count"
            )
        )
        + appended_missing_keyword_count
    )

    duplicate_record_count = max(
        0,
        valid_record_count
        - missing_keyword_count
        - len(keywords),
    )

    current_datetime = (
        _get_current_iso_datetime()
    )

    source_signatures = _read_source_signatures(
        source_path=observation_path,
        indexed_size_bytes=current_size_bytes,
    )

    index_data["schema_version"] = (
        SEARCH_INDEX_SCHEMA_VERSION
    )
    index_data["updated_at"] = (
        current_datetime
    )
    index_data["update_count"] = (
        _safe_int(
            index_data.get(
                "update_count"
            )
        )
        + 1
    )
    index_data["source"] = {
        "file_path": str(
            observation_path
        ),
        "size_bytes": (
            current_size_bytes
        ),
        "modified_time_ns": int(
            source_stat_after.st_mtime_ns
        ),
        "total_line_count": (
            total_line_count
        ),
        "valid_record_count": (
            valid_record_count
        ),
        "empty_line_count": (
            empty_line_count
        ),
        "missing_keyword_count": (
            missing_keyword_count
        ),
        "signatures": source_signatures,
    }
    index_data["keyword_count"] = len(
        keywords
    )
    index_data["duplicate_record_count"] = (
        duplicate_record_count
    )
    index_data["keywords"] = keywords
    index_data["last_update"] = {
        "mode": "incremental",
        "updated_at": current_datetime,
        "previous_size_bytes": (
            previous_size_bytes
        ),
        "appended_size_bytes": (
            appended_size_bytes
        ),
        "appended_line_count": (
            appended_line_count
        ),
        "appended_valid_record_count": (
            appended_valid_record_count
        ),
        "appended_empty_line_count": (
            appended_empty_line_count
        ),
        "appended_missing_keyword_count": (
            appended_missing_keyword_count
        ),
        "added_keyword_count": len(
            added_keywords
        ),
        "signature_verified": (
            signature_verified
        ),
    }

    _atomic_write_json(
        target_path=index_path,
        data=index_data,
    )

    return {
        "index_path": str(
            index_path
        ),
        "source_path": str(
            observation_path
        ),
        "previous_size_bytes": (
            previous_size_bytes
        ),
        "source_size_bytes": (
            current_size_bytes
        ),
        "appended_size_bytes": (
            appended_size_bytes
        ),
        "appended_line_count": (
            appended_line_count
        ),
        "appended_valid_record_count": (
            appended_valid_record_count
        ),
        "appended_empty_line_count": (
            appended_empty_line_count
        ),
        "appended_missing_keyword_count": (
            appended_missing_keyword_count
        ),
        "added_keyword_count": len(
            added_keywords
        ),
        "keyword_count": len(
            keywords
        ),
        "duplicate_record_count": (
            duplicate_record_count
        ),
        "updated_at": current_datetime,
        "signature_verified": (
            signature_verified
        ),
        "no_changes": (
            appended_size_bytes == 0
        ),
    }
