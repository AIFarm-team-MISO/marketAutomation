from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


# 파일 직접 실행과 모듈 실행을 모두 지원
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from keywordObservation.observation_store import (
    ALLOWED_COLLECTION_STATUSES,
    OBSERVATION_FILE,
    normalize_keyword,
)


REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "captured_at",
    "source_record_type",
    "query",
    "request",
    "processing",
    "samples",
    "aggregates",
    "query_validation",
    "related_keywords",
}


SOURCE_ITEM_FIELDS = {
    "mall_name",
    "lowest_price",
    "highest_price",
    "product_id",
    "product_type",
    "link",
    "image_url",
    "maker",
}


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(value)

    except (TypeError, ValueError):
        return default


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


def _parse_version(
    version: Any,
) -> tuple[int, ...]:
    """
    '1.2'를 (1, 2) 형태로 변환한다.
    """
    normalized_version = str(
        version
    ).strip()

    if not normalized_version:
        return ()

    version_parts: list[int] = []

    for part in normalized_version.split("."):
        try:
            version_parts.append(
                int(part)
            )

        except ValueError:
            return ()

    return tuple(
        version_parts
    )


def _get_record_keyword(
    observation: dict[str, Any],
) -> str:
    query = _safe_dict(
        observation.get("query")
    )

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


def _make_issue(
    *,
    severity: str,
    line_number: int,
    code: str,
    message: str,
    keyword: str = "",
    captured_at: str = "",
) -> dict[str, Any]:
    return {
        "severity": severity,
        "line_number": line_number,
        "code": code,
        "message": message,
        "keyword": keyword,
        "captured_at": captured_at,
    }


def _make_record_hash(
    observation: dict[str, Any],
) -> str:
    """
    JSON 객체 전체를 기준으로 중복 여부를 판별한다.
    """
    serialized = json.dumps(
        observation,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def _validate_iso_datetime(
    value: Any,
) -> bool:
    normalized_value = str(
        value
    ).strip()

    if not normalized_value:
        return False

    try:
        datetime.fromisoformat(
            normalized_value
        )

    except ValueError:
        return False

    return True


def validate_observation_record(
    observation: dict[str, Any],
    line_number: int,
) -> list[dict[str, Any]]:
    """
    관찰기록 한 건의 구조와 주요 값들을 검사한다.
    """
    issues: list[
        dict[str, Any]
    ] = []

    keyword = _get_record_keyword(
        observation
    )

    captured_at = str(
        observation.get(
            "captured_at",
            "",
        )
    ).strip()

    schema_version = str(
        observation.get(
            "schema_version",
            "",
        )
    ).strip()

    schema_version_tuple = (
        _parse_version(
            schema_version
        )
    )

    # -----------------------------------------------------
    # 최상위 필드 검사
    # -----------------------------------------------------

    missing_fields = sorted(
        REQUIRED_TOP_LEVEL_FIELDS
        - set(observation.keys())
    )

    if missing_fields:
        issues.append(
            _make_issue(
                severity="error",
                line_number=line_number,
                code="missing_top_level_fields",
                message=(
                    "필수 최상위 필드 누락: "
                    + ", ".join(
                        missing_fields
                    )
                ),
                keyword=keyword,
                captured_at=captured_at,
            )
        )

    if not schema_version:
        issues.append(
            _make_issue(
                severity="error",
                line_number=line_number,
                code="missing_schema_version",
                message=(
                    "schema_version이 없습니다."
                ),
                keyword=keyword,
                captured_at=captured_at,
            )
        )

    elif not schema_version_tuple:
        issues.append(
            _make_issue(
                severity="warning",
                line_number=line_number,
                code="invalid_schema_version",
                message=(
                    "schema_version 형식을 "
                    f"해석할 수 없습니다: {schema_version}"
                ),
                keyword=keyword,
                captured_at=captured_at,
            )
        )

    # -----------------------------------------------------
    # 수집시각 검사
    # -----------------------------------------------------

    if not _validate_iso_datetime(
        captured_at
    ):
        issues.append(
            _make_issue(
                severity="error",
                line_number=line_number,
                code="invalid_captured_at",
                message=(
                    "captured_at이 정상적인 "
                    f"ISO 날짜가 아닙니다: {captured_at}"
                ),
                keyword=keyword,
                captured_at=captured_at,
            )
        )

    # -----------------------------------------------------
    # 검색어 검사
    # -----------------------------------------------------

    if not keyword:
        issues.append(
            _make_issue(
                severity="error",
                line_number=line_number,
                code="missing_keyword",
                message=(
                    "query에 검색어가 없습니다."
                ),
                keyword=keyword,
                captured_at=captured_at,
            )
        )

    # -----------------------------------------------------
    # 요청정보 검사
    # -----------------------------------------------------

    request = _safe_dict(
        observation.get("request")
    )

    request_display = _safe_int(
        request.get("display"),
        0,
    )

    if request_display < 1:
        issues.append(
            _make_issue(
                severity="error",
                line_number=line_number,
                code="invalid_request_display",
                message=(
                    "request.display는 "
                    "1 이상이어야 합니다."
                ),
                keyword=keyword,
                captured_at=captured_at,
            )
        )

    request_sort = str(
        request.get(
            "sort",
            "",
        )
    ).strip()

    if not request_sort:
        issues.append(
            _make_issue(
                severity="warning",
                line_number=line_number,
                code="missing_request_sort",
                message=(
                    "request.sort가 없습니다."
                ),
                keyword=keyword,
                captured_at=captured_at,
            )
        )

    # -----------------------------------------------------
    # 샘플 검사
    # -----------------------------------------------------

    samples_value = observation.get(
        "samples"
    )

    if not isinstance(
        samples_value,
        list,
    ):
        issues.append(
            _make_issue(
                severity="error",
                line_number=line_number,
                code="invalid_samples_type",
                message=(
                    "samples가 list 형식이 아닙니다."
                ),
                keyword=keyword,
                captured_at=captured_at,
            )
        )

    samples = [
        sample
        for sample in _safe_list(
            samples_value
        )
        if isinstance(sample, dict)
    ]

    sample_count = len(
        samples
    )

    if sample_count != len(
        _safe_list(samples_value)
    ):
        issues.append(
            _make_issue(
                severity="error",
                line_number=line_number,
                code="invalid_sample_item",
                message=(
                    "samples 안에 dict가 아닌 "
                    "항목이 있습니다."
                ),
                keyword=keyword,
                captured_at=captured_at,
            )
        )

    processing = _safe_dict(
        observation.get("processing")
    )

    processing_sample_count = (
        _safe_int(
            processing.get(
                "sample_count"
            ),
            -1,
        )
    )

    if (
        processing_sample_count
        != sample_count
    ):
        issues.append(
            _make_issue(
                severity="error",
                line_number=line_number,
                code="processing_sample_count_mismatch",
                message=(
                    "processing.sample_count와 "
                    "실제 samples 수가 다릅니다: "
                    f"{processing_sample_count} != "
                    f"{sample_count}"
                ),
                keyword=keyword,
                captured_at=captured_at,
            )
        )

    # -----------------------------------------------------
    # API 응답정보 검사
    # schema 1.2 이상에서 필수
    # -----------------------------------------------------

    response_value = observation.get(
        "response"
    )

    response = _safe_dict(
        response_value
    )

    if (
        schema_version_tuple
        and schema_version_tuple >= (1, 2)
        and not isinstance(
            response_value,
            dict,
        )
    ):
        issues.append(
            _make_issue(
                severity="error",
                line_number=line_number,
                code="missing_response",
                message=(
                    "schema 1.2 이상 기록에 "
                    "response가 없습니다."
                ),
                keyword=keyword,
                captured_at=captured_at,
            )
        )

    collection_status = str(
        response.get(
            "collection_status",
            "",
        )
    ).strip()

    if response:
        if (
            collection_status
            not in ALLOWED_COLLECTION_STATUSES
        ):
            issues.append(
                _make_issue(
                    severity="error",
                    line_number=line_number,
                    code="invalid_collection_status",
                    message=(
                        "알 수 없는 수집상태입니다: "
                        f"{collection_status}"
                    ),
                    keyword=keyword,
                    captured_at=captured_at,
                )
            )

        received_count = _safe_int(
            response.get(
                "received_count"
            ),
            -1,
        )

        attempt_count = _safe_int(
            response.get(
                "attempt_count"
            ),
            0,
        )

        if received_count < 0:
            issues.append(
                _make_issue(
                    severity="error",
                    line_number=line_number,
                    code="invalid_received_count",
                    message=(
                        "response.received_count가 "
                        "0보다 작거나 없습니다."
                    ),
                    keyword=keyword,
                    captured_at=captured_at,
                )
            )

        if attempt_count < 1:
            issues.append(
                _make_issue(
                    severity="error",
                    line_number=line_number,
                    code="invalid_attempt_count",
                    message=(
                        "response.attempt_count는 "
                        "1 이상이어야 합니다."
                    ),
                    keyword=keyword,
                    captured_at=captured_at,
                )
            )

        if (
            received_count >= 0
            and received_count
            != sample_count
        ):
            issues.append(
                _make_issue(
                    severity="warning",
                    line_number=line_number,
                    code="received_sample_count_mismatch",
                    message=(
                        "API 수신 수와 처리 샘플 수가 "
                        "다릅니다: "
                        f"{received_count} != "
                        f"{sample_count}"
                    ),
                    keyword=keyword,
                    captured_at=captured_at,
                )
            )

        if (
            collection_status
            == "no_results"
            and sample_count > 0
        ):
            issues.append(
                _make_issue(
                    severity="error",
                    line_number=line_number,
                    code="no_results_with_samples",
                    message=(
                        "수집상태는 no_results인데 "
                        "samples가 존재합니다."
                    ),
                    keyword=keyword,
                    captured_at=captured_at,
                )
            )

        if (
            collection_status
            == "success"
            and sample_count == 0
        ):
            issues.append(
                _make_issue(
                    severity="warning",
                    line_number=line_number,
                    code="success_without_samples",
                    message=(
                        "수집상태는 success인데 "
                        "samples가 없습니다."
                    ),
                    keyword=keyword,
                    captured_at=captured_at,
                )
            )

    # -----------------------------------------------------
    # 분석결과 수 검사
    # -----------------------------------------------------

    aggregates = _safe_dict(
        observation.get("aggregates")
    )

    aggregates_sample_count = (
        _safe_int(
            aggregates.get(
                "sample_count"
            ),
            sample_count,
        )
    )

    if (
        aggregates
        and aggregates_sample_count
        != sample_count
    ):
        issues.append(
            _make_issue(
                severity="warning",
                line_number=line_number,
                code="aggregates_sample_count_mismatch",
                message=(
                    "aggregates.sample_count와 "
                    "실제 samples 수가 다릅니다: "
                    f"{aggregates_sample_count} != "
                    f"{sample_count}"
                ),
                keyword=keyword,
                captured_at=captured_at,
            )
        )

    query_validation = _safe_dict(
        observation.get(
            "query_validation"
        )
    )

    validation_sample_count = (
        _safe_int(
            query_validation.get(
                "sample_count"
            ),
            sample_count,
        )
    )

    if (
        query_validation
        and validation_sample_count
        != sample_count
    ):
        issues.append(
            _make_issue(
                severity="warning",
                line_number=line_number,
                code="validation_sample_count_mismatch",
                message=(
                    "query_validation.sample_count와 "
                    "실제 samples 수가 다릅니다: "
                    f"{validation_sample_count} != "
                    f"{sample_count}"
                ),
                keyword=keyword,
                captured_at=captured_at,
            )
        )

    # -----------------------------------------------------
    # 개별 상품 검사
    # -----------------------------------------------------

    ranks: list[int] = []
    product_ids: list[str] = []

    for sample_index, sample in enumerate(
        samples,
        start=1,
    ):
        rank = _safe_int(
            sample.get("rank"),
            0,
        )

        if rank < 1:
            issues.append(
                _make_issue(
                    severity="warning",
                    line_number=line_number,
                    code="invalid_sample_rank",
                    message=(
                        f"{sample_index}번째 sample의 "
                        "rank가 없습니다."
                    ),
                    keyword=keyword,
                    captured_at=captured_at,
                )
            )

        else:
            ranks.append(
                rank
            )

        original_title = str(
            sample.get(
                "original_title",
                "",
            )
        ).strip()

        if not original_title:
            issues.append(
                _make_issue(
                    severity="warning",
                    line_number=line_number,
                    code="missing_original_title",
                    message=(
                        f"{sample_index}번째 sample의 "
                        "original_title이 비어 있습니다."
                    ),
                    keyword=keyword,
                    captured_at=captured_at,
                )
            )

        if (
            schema_version_tuple
            and schema_version_tuple >= (1, 2)
        ):
            source_item_value = sample.get(
                "source_item"
            )

            if not isinstance(
                source_item_value,
                dict,
            ):
                issues.append(
                    _make_issue(
                        severity="warning",
                        line_number=line_number,
                        code="missing_source_item",
                        message=(
                            f"{sample_index}번째 sample에 "
                            "source_item이 없습니다."
                        ),
                        keyword=keyword,
                        captured_at=captured_at,
                    )
                )

                continue

            source_item = source_item_value

            missing_source_fields = sorted(
                SOURCE_ITEM_FIELDS
                - set(source_item.keys())
            )

            if missing_source_fields:
                issues.append(
                    _make_issue(
                        severity="warning",
                        line_number=line_number,
                        code="missing_source_item_fields",
                        message=(
                            f"{sample_index}번째 sample의 "
                            "source_item 필드 누락: "
                            + ", ".join(
                                missing_source_fields
                            )
                        ),
                        keyword=keyword,
                        captured_at=captured_at,
                    )
                )

            product_id = str(
                source_item.get(
                    "product_id",
                    "",
                )
            ).strip()

            if product_id:
                product_ids.append(
                    product_id
                )

    # 순위 중복 검사
    duplicated_ranks = [
        rank
        for rank, count in Counter(
            ranks
        ).items()
        if count > 1
    ]

    if duplicated_ranks:
        issues.append(
            _make_issue(
                severity="warning",
                line_number=line_number,
                code="duplicated_ranks",
                message=(
                    "중복된 상품 순위가 있습니다: "
                    + ", ".join(
                        str(rank)
                        for rank in sorted(
                            duplicated_ranks
                        )
                    )
                ),
                keyword=keyword,
                captured_at=captured_at,
            )
        )

    # 상품 ID 중복 검사
    duplicated_product_ids = [
        product_id
        for product_id, count in Counter(
            product_ids
        ).items()
        if count > 1
    ]

    if duplicated_product_ids:
        issues.append(
            _make_issue(
                severity="warning",
                line_number=line_number,
                code="duplicated_product_ids",
                message=(
                    "한 관찰기록 안에 중복된 "
                    "product_id가 있습니다: "
                    + ", ".join(
                        duplicated_product_ids
                    )
                ),
                keyword=keyword,
                captured_at=captured_at,
            )
        )

    return issues


def check_observation_file(
    file_path: Path | str = (
        OBSERVATION_FILE
    ),
) -> dict[str, Any]:
    """
    JSONL 전체 파일의 무결성을 검사한다.

    파일 내용은 수정하지 않는다.
    """
    target_path = Path(
        file_path
    )

    result: dict[str, Any] = {
        "file_path": str(
            target_path
        ),
        "exists": (
            target_path.exists()
        ),
        "file_size_bytes": 0,
        "total_lines": 0,
        "empty_lines": 0,
        "valid_json_lines": 0,
        "record_count": 0,
        "keyword_count": 0,
        "schema_versions": {},
        "status_counts": {},
        "error_count": 0,
        "warning_count": 0,
        "duplicate_record_count": 0,
        "is_healthy": False,
        "issues": [],
    }

    if not target_path.exists():
        result["issues"].append(
            _make_issue(
                severity="error",
                line_number=0,
                code="file_not_found",
                message=(
                    "관찰이력 JSONL 파일이 없습니다."
                ),
            )
        )

        result["error_count"] = 1

        return result

    try:
        result["file_size_bytes"] = (
            target_path.stat().st_size
        )

    except OSError:
        pass

    keyword_counter: Counter[str] = (
        Counter()
    )

    schema_counter: Counter[str] = (
        Counter()
    )

    status_counter: Counter[str] = (
        Counter()
    )

    record_hashes: dict[
        str,
        int,
    ] = {}

    timestamp_keys: dict[
        tuple[str, str],
        int,
    ] = {}

    try:
        with target_path.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            for line_number, line in enumerate(
                file,
                start=1,
            ):
                result["total_lines"] += 1

                normalized_line = (
                    line.strip()
                )

                if not normalized_line:
                    result["empty_lines"] += 1
                    continue

                try:
                    observation = json.loads(
                        normalized_line
                    )

                except json.JSONDecodeError as error:
                    result["issues"].append(
                        _make_issue(
                            severity="error",
                            line_number=line_number,
                            code="invalid_json",
                            message=(
                                "JSON 해석 실패: "
                                f"{error}"
                            ),
                        )
                    )

                    continue

                result[
                    "valid_json_lines"
                ] += 1

                if not isinstance(
                    observation,
                    dict,
                ):
                    result["issues"].append(
                        _make_issue(
                            severity="error",
                            line_number=line_number,
                            code="invalid_record_type",
                            message=(
                                "관찰기록이 JSON 객체가 "
                                "아닙니다."
                            ),
                        )
                    )

                    continue

                result["record_count"] += 1

                keyword = _get_record_keyword(
                    observation
                )

                captured_at = str(
                    observation.get(
                        "captured_at",
                        "",
                    )
                ).strip()

                schema_version = str(
                    observation.get(
                        "schema_version",
                        "",
                    )
                ).strip() or "unknown"

                response = _safe_dict(
                    observation.get(
                        "response"
                    )
                )

                collection_status = str(
                    response.get(
                        "collection_status",
                        "",
                    )
                ).strip() or "legacy_or_unknown"

                if keyword:
                    keyword_counter[
                        keyword
                    ] += 1

                schema_counter[
                    schema_version
                ] += 1

                status_counter[
                    collection_status
                ] += 1

                # 완전히 동일한 JSON 객체 검사
                record_hash = (
                    _make_record_hash(
                        observation
                    )
                )

                if record_hash in record_hashes:
                    original_line = (
                        record_hashes[
                            record_hash
                        ]
                    )

                    result["issues"].append(
                        _make_issue(
                            severity="warning",
                            line_number=line_number,
                            code="exact_duplicate_record",
                            message=(
                                "완전히 동일한 관찰기록이 "
                                "이미 존재합니다. "
                                f"최초 줄: {original_line}"
                            ),
                            keyword=keyword,
                            captured_at=captured_at,
                        )
                    )

                    result[
                        "duplicate_record_count"
                    ] += 1

                else:
                    record_hashes[
                        record_hash
                    ] = line_number

                # 같은 키워드와 수집시각 중복 검사
                timestamp_key = (
                    keyword,
                    captured_at,
                )

                if (
                    keyword
                    and captured_at
                    and timestamp_key
                    in timestamp_keys
                ):
                    original_line = (
                        timestamp_keys[
                            timestamp_key
                        ]
                    )

                    result["issues"].append(
                        _make_issue(
                            severity="warning",
                            line_number=line_number,
                            code="duplicate_keyword_timestamp",
                            message=(
                                "같은 검색어와 수집시각의 "
                                "기록이 이미 존재합니다. "
                                f"최초 줄: {original_line}"
                            ),
                            keyword=keyword,
                            captured_at=captured_at,
                        )
                    )

                else:
                    timestamp_keys[
                        timestamp_key
                    ] = line_number

                result["issues"].extend(
                    validate_observation_record(
                        observation=observation,
                        line_number=line_number,
                    )
                )

    except (
        OSError,
        UnicodeDecodeError,
    ) as error:
        result["issues"].append(
            _make_issue(
                severity="error",
                line_number=0,
                code="file_read_error",
                message=(
                    "JSONL 파일을 읽지 못했습니다: "
                    f"{error}"
                ),
            )
        )

    result["keyword_count"] = len(
        keyword_counter
    )

    result["schema_versions"] = dict(
        schema_counter
    )

    result["status_counts"] = dict(
        status_counter
    )

    result["error_count"] = sum(
        1
        for issue in result["issues"]
        if issue.get(
            "severity"
        ) == "error"
    )

    result["warning_count"] = sum(
        1
        for issue in result["issues"]
        if issue.get(
            "severity"
        ) == "warning"
    )

    result["is_healthy"] = (
        result["error_count"] == 0
    )

    return result


def print_integrity_report(
    result: dict[str, Any],
    max_issues: int = 50,
) -> None:
    """
    검사결과를 사람이 읽기 쉽게 출력한다.
    """
    print(
        "=" * 100
    )

    print(
        "네이버 쇼핑 관찰이력 무결성 검사"
    )

    print(
        "=" * 100
    )

    print(
        f"파일: {result.get('file_path', '')}"
    )

    print(
        f"파일 존재: {result.get('exists', False)}"
    )

    print(
        "파일 크기: "
        f"{result.get('file_size_bytes', 0):,} bytes"
    )

    print(
        f"전체 줄 수: {result.get('total_lines', 0)}"
    )

    print(
        "정상 JSON 줄 수: "
        f"{result.get('valid_json_lines', 0)}"
    )

    print(
        f"관찰기록 수: {result.get('record_count', 0)}"
    )

    print(
        f"고유 검색어 수: {result.get('keyword_count', 0)}"
    )

    print(
        "스키마 분포: "
        f"{result.get('schema_versions', {})}"
    )

    print(
        "수집상태 분포: "
        f"{result.get('status_counts', {})}"
    )

    print(
        f"오류: {result.get('error_count', 0)}"
    )

    print(
        f"경고: {result.get('warning_count', 0)}"
    )

    print(
        "완전 중복 기록: "
        f"{result.get('duplicate_record_count', 0)}"
    )

    print(
        "최종 상태: "
        + (
            "정상"
            if result.get(
                "is_healthy"
            )
            else "확인 필요"
        )
    )

    issues = _safe_list(
        result.get("issues")
    )

    if not issues:
        print(
            "-" * 100
        )

        print(
            "발견된 문제 없음"
        )

        return

    print(
        "-" * 100
    )

    print(
        f"문제 목록 - 최대 {max_issues}건 출력"
    )

    for issue in issues[
        :max_issues
    ]:
        severity = str(
            issue.get(
                "severity",
                "",
            )
        ).upper()

        line_number = _safe_int(
            issue.get(
                "line_number"
            ),
            0,
        )

        code = str(
            issue.get(
                "code",
                "",
            )
        )

        keyword = str(
            issue.get(
                "keyword",
                "",
            )
        )

        message = str(
            issue.get(
                "message",
                "",
            )
        )

        print(
            (
                f"[{severity}] "
                f"줄 {line_number} "
                f"[{code}] "
                f"{keyword} "
                f"- {message}"
            ).strip()
        )

    hidden_issue_count = (
        len(issues)
        - max_issues
    )

    if hidden_issue_count > 0:
        print(
            (
                "... 추가 문제 "
                f"{hidden_issue_count}건 생략"
            )
        )


def main() -> None:
    result = check_observation_file()

    print_integrity_report(
        result
    )


if __name__ == "__main__":
    main()