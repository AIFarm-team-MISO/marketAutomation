from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from utils.global_logger import logger

from keywordObservation.dictionary_collection_history import (
    DictionaryCollectionHistoryError,
    append_dictionary_collection_history,
)

from keywordObservation.keyword_input_loader import (
    load_keywords_from_input_folder,
)

from keywordObservation.keyword_observation_paths import (
    DICTIONARY_COLLECTION_HISTORY_FILE,
    KEYWORD_INPUT_DIR,
    OBSERVATION_FILE,
    REFERENCE_CANDIDATE_REGISTRY_FILE,
)

from keywordObservation.keyword_observation_settings import (
    load_keyword_observation_settings,
)

from keywordObservation.observation_keyword_index import (
    load_observed_keyword_index,
)

from keywordObservation.query_validator import (
    validate_keyword_format,
)


PREVIEW_ITEM_LIMIT = 30


def _log(
    message: str,
    level: str = "INFO",
) -> None:
    logger.log(
        message,
        level=level,
        also_to_report=True,
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


def _safe_list(
    value: Any,
) -> list[Any]:
    if isinstance(
        value,
        list,
    ):
        return value

    return []


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


def _format_elapsed(
    elapsed_seconds: float,
) -> str:
    total_seconds = max(
        0,
        int(
            round(
                elapsed_seconds
            )
        ),
    )

    minutes, seconds = divmod(
        total_seconds,
        60,
    )

    hours, minutes = divmod(
        minutes,
        60,
    )

    if hours:
        return (
            f"{hours}시간 "
            f"{minutes}분 "
            f"{seconds}초"
        )

    if minutes:
        return (
            f"{minutes}분 "
            f"{seconds}초"
        )

    return f"{seconds}초"


def _log_keyword_list(
    *,
    label: str,
    keywords: list[str],
    level: str = "INFO",
    limit: int = PREVIEW_ITEM_LIMIT,
) -> None:
    normalized = [
        str(keyword).strip()
        for keyword in keywords
        if str(
            keyword
        ).strip()
    ]

    _log(
        (
            f"   └ {label}: "
            f"{len(normalized)}개"
        ),
        level=level,
    )

    if not normalized:
        _log(
            "      └ 없음",
            level=level,
        )
        return

    preview = normalized[:limit]

    preview_text = ", ".join(
        preview
    )

    if len(
        normalized
    ) > limit:
        preview_text += (
            f" 외 "
            f"{len(normalized) - limit}개"
        )

    _log(
        (
            "      └ "
            f"{preview_text}"
        ),
        level=level,
    )


def _build_plan(
    settings: dict[str, Any],
) -> dict[str, Any]:
    keyword_column = str(
        settings.get(
            "keyword_column",
            "키워드",
        )
    ).strip() or "키워드"

    supported_extensions = [
        str(extension)
        for extension in _safe_list(
            settings.get(
                "supported_excel_extensions"
            )
        )
        if str(
            extension
        ).strip()
    ]

    load_result = (
        load_keywords_from_input_folder(
            input_directory=(
                KEYWORD_INPUT_DIR
            ),
            keyword_column=(
                keyword_column
            ),
            supported_extensions=(
                supported_extensions
            ),
        )
    )

    raw_keywords = [
        str(keyword)
        for keyword in _safe_list(
            load_result.get(
                "keywords"
            )
        )
        if str(
            keyword
        ).strip()
    ]

    observed_index = (
        load_observed_keyword_index()
    )

    observed_casefold = set(
        observed_index.get(
            "casefold_keywords",
            set(),
        )
    )

    skip_existing = bool(
        settings.get(
            "skip_existing_on_dictionary_add",
            True,
        )
    )

    sources_by_keyword = _safe_dict(
        load_result.get(
            "sources_by_keyword"
        )
    )

    existing_keywords: list[str] = []
    invalid_keywords: list[str] = []

    pending_keywords: list[
        dict[str, Any]
    ] = []

    normalized_seen: set[str] = set()

    for input_keyword in raw_keywords:
        validation = (
            validate_keyword_format(
                input_keyword
            )
        )

        if not bool(
            validation.get(
                "can_search",
                False,
            )
        ):
            invalid_keywords.append(
                input_keyword
            )
            continue

        normalized_keyword = " ".join(
            str(
                validation.get(
                    "normalized_keyword",
                    input_keyword,
                )
            ).split()
        )

        if not normalized_keyword:
            invalid_keywords.append(
                input_keyword
            )
            continue

        normalized_key = (
            normalized_keyword.casefold()
        )

        if normalized_key in normalized_seen:
            continue

        normalized_seen.add(
            normalized_key
        )

        if (
            skip_existing
            and normalized_key
            in observed_casefold
        ):
            existing_keywords.append(
                normalized_keyword
            )
            continue

        pending_keywords.append(
            {
                "input_keyword": (
                    input_keyword
                ),
                "normalized_keyword": (
                    normalized_keyword
                ),
                "source_files": list(
                    sources_by_keyword.get(
                        input_keyword,
                        [],
                    )
                ),
            }
        )

    return {
        "load_result": load_result,
        "raw_keywords": raw_keywords,
        "observed_index": observed_index,
        "existing_keywords": (
            existing_keywords
        ),
        "invalid_keywords": (
            invalid_keywords
        ),
        "pending_keywords": (
            pending_keywords
        ),
    }


def _print_plan(
    *,
    plan: dict[str, Any],
    settings: dict[str, Any],
) -> None:
    load_result = _safe_dict(
        plan.get(
            "load_result"
        )
    )

    files_found = [
        str(path)
        for path in _safe_list(
            load_result.get(
                "files_found"
            )
        )
    ]

    readable_files = [
        str(path)
        for path in _safe_list(
            load_result.get(
                "readable_files"
            )
        )
    ]

    existing_keywords = [
        str(keyword)
        for keyword in _safe_list(
            plan.get(
                "existing_keywords"
            )
        )
    ]

    invalid_keywords = [
        str(keyword)
        for keyword in _safe_list(
            plan.get(
                "invalid_keywords"
            )
        )
    ]

    pending_items = [
        item
        for item in _safe_list(
            plan.get(
                "pending_keywords"
            )
        )
        if isinstance(
            item,
            dict,
        )
    ]

    pending_keywords = [
        str(
            item.get(
                "normalized_keyword",
                item.get(
                    "input_keyword",
                    "",
                ),
            )
        )
        for item in pending_items
        if str(
            item.get(
                "normalized_keyword",
                item.get(
                    "input_keyword",
                    "",
                ),
            )
        ).strip()
    ]

    _log(
        "=" * 100
    )

    _log(
        "📋 사전추가 실행 전 확인"
    )

    _log(
        (
            "   └ 입력폴더: "
            f"{KEYWORD_INPUT_DIR}"
        )
    )

    _log(
        (
            "   └ 발견된 엑셀파일: "
            f"{len(files_found)}개"
        )
    )

    if files_found:
        _log(
            (
                "      └ "
                + ", ".join(
                    Path(path).name
                    for path in files_found
                )
            )
        )

    _log(
        (
            "   └ 정상적으로 읽은 파일: "
            f"{len(readable_files)}개"
        )
    )

    _log(
        (
            "   └ 전체 입력행: "
            f"{_safe_int(load_result.get('total_rows'))}개"
        )
    )

    _log(
        (
            "   └ 빈행 제외: "
            f"{_safe_int(load_result.get('blank_rows'))}개"
        )
    )

    _log(
        (
            "   └ 중복 제외: "
            f"{_safe_int(load_result.get('duplicate_rows'))}개"
        )
    )

    _log(
        (
            "   └ 고유 입력키워드: "
            f"{len(_safe_list(plan.get('raw_keywords')))}개"
        )
    )

    _log_keyword_list(
        label=(
            "사전에 이미 등록되어 제외될 키워드"
        ),
        keywords=existing_keywords,
    )

    _log_keyword_list(
        label=(
            "검색어 형식문제로 제외될 키워드"
        ),
        keywords=invalid_keywords,
        level="WARNING",
    )

    _log_keyword_list(
        label=(
            "이번에 새로 검색·저장할 키워드"
        ),
        keywords=pending_keywords,
    )

    read_errors = [
        item
        for item in _safe_list(
            load_result.get(
                "read_errors"
            )
        )
        if isinstance(
            item,
            dict,
        )
    ]

    missing_column_files = [
        str(path)
        for path in _safe_list(
            load_result.get(
                "missing_column_files"
            )
        )
    ]

    if read_errors:
        _log(
            (
                "   └ 읽기 실패 파일: "
                f"{len(read_errors)}개"
            ),
            level="WARNING",
        )

        for item in read_errors[:10]:
            _log(
                (
                    "      └ "
                    f"{Path(str(item.get('file', ''))).name}: "
                    f"{item.get('error', '')}"
                ),
                level="WARNING",
            )

    if missing_column_files:
        _log(
            (
                "   └ '키워드' 열이 없어 제외된 파일: "
                f"{len(missing_column_files)}개"
            ),
            level="WARNING",
        )

        _log(
            (
                "      └ "
                + ", ".join(
                    Path(path).name
                    for path in (
                        missing_column_files[:10]
                    )
                )
            ),
            level="WARNING",
        )

    _log(
        (
            "   └ API 호출 예정횟수: "
            f"{len(pending_items)}회"
        )
    )

    delay_seconds = max(
        0.0,
        float(
            settings.get(
                "bulk_collection_delay_seconds",
                0.5,
            )
        ),
    )

    if pending_items and delay_seconds:
        minimum_wait = (
            max(
                0,
                len(
                    pending_items
                )
                - 1,
            )
            * delay_seconds
        )

        _log(
            (
                "   └ 키워드 사이 최소 대기시간 합계: "
                f"{minimum_wait:.1f}초"
            )
        )

    _log(
        "=" * 100
    )


def _confirm() -> bool:
    """
    Windows 콘솔에서는 Enter 또는 Esc를 누르는 즉시 결정한다.

    Enter:
        신규 키워드 검색·저장 실행

    Esc:
        사전추가 취소 후 프로그램 종료

    기존 단축키 1/y, 2/q도 유지한다.
    """
    _log(
        "사전추가를 실행하시겠습니까?"
    )

    _log(
        (
            "   [Enter / 1 / y]  "
            "신규 키워드 검색·저장"
        )
    )

    _log(
        (
            "   [Esc / 2 / q]    "
            "취소 후 프로그램 종료"
        )
    )

    if (
        os.name == "nt"
        and sys.stdin.isatty()
    ):
        import msvcrt

        print(
            (
                "\n▶ Enter=실행 / "
                "Esc=종료: "
            ),
            end="",
            flush=True,
        )

        while True:
            key = msvcrt.getwch()

            if key == "\x03":
                raise KeyboardInterrupt

            if key in {
                "\x00",
                "\xe0",
            }:
                msvcrt.getwch()
                continue

            if key in {
                "\r",
                "\n",
            }:
                print(
                    "Enter"
                )
                return True

            if key == "\x1b":
                print(
                    "Esc"
                )
                return False

            normalized_key = (
                key.lower()
            )

            if normalized_key in {
                "1",
                "y",
            }:
                print(
                    key
                )
                return True

            if normalized_key in {
                "2",
                "q",
            }:
                print(
                    key
                )
                return False

            # 다른 키는 무시하고 Enter 또는 Esc 입력을 계속 기다린다.

    execute_values = {
        "",
        "1",
        "실행",
        "y",
        "yes",
    }

    cancel_values = {
        "esc",
        "escape",
        "2",
        "취소",
        "q",
        "exit",
        "종료",
        "n",
        "no",
    }

    while True:
        selection = input(
            (
                "\n▶ Enter=실행 / "
                "Esc=종료: "
            )
        ).strip().lower()

        if selection in execute_values:
            return True

        if selection in cancel_values:
            return False

        _log(
            (
                "Enter(실행) 또는 "
                "Esc(종료)를 입력해 주세요."
            ),
            level="WARNING",
        )


def _print_final_summary(
    *,
    plan: dict[str, Any],
    batch_id: str,
    elapsed_seconds: float,
    results: list[dict[str, Any]],
    interrupted: bool,
) -> None:
    existing_keywords = [
        str(keyword)
        for keyword in _safe_list(
            plan.get(
                "existing_keywords"
            )
        )
    ]

    invalid_keywords = [
        str(keyword)
        for keyword in _safe_list(
            plan.get(
                "invalid_keywords"
            )
        )
    ]

    pending_items = [
        item
        for item in _safe_list(
            plan.get(
                "pending_keywords"
            )
        )
        if isinstance(
            item,
            dict,
        )
    ]

    successful_keywords: list[str] = []
    no_result_keywords: list[str] = []
    failed_keywords: list[str] = []

    status_counts: dict[str, int] = {}

    total_sample_count = 0
    total_candidate_count = 0
    total_attempt_count = 0

    for result in results:
        keyword = str(
            result.get(
                "input_keyword",
                "",
            )
        ).strip()

        status = str(
            result.get(
                "status",
                "unknown",
            )
        )

        status_counts[
            status
        ] = (
            status_counts.get(
                status,
                0,
            )
            + 1
        )

        sample_count = _safe_int(
            result.get(
                "sample_count",
                0,
            )
        )

        total_sample_count += sample_count

        total_candidate_count += (
            _safe_int(
                result.get(
                    "reference_candidate_count",
                    0,
                )
            )
        )

        total_attempt_count += max(
            0,
            _safe_int(
                result.get(
                    "attempt_count",
                    0,
                )
            ),
        )

        if status == "success":
            successful_keywords.append(
                keyword
            )

            if sample_count == 0:
                no_result_keywords.append(
                    keyword
                )

        else:
            failed_keywords.append(
                (
                    f"{keyword}"
                    f"({status})"
                )
            )

    observed_before = _safe_dict(
        plan.get(
            "observed_index"
        )
    )

    observed_after = (
        load_observed_keyword_index()
    )

    before_count = len(
        set(
            observed_before.get(
                "casefold_keywords",
                set(),
            )
        )
    )

    after_count = len(
        set(
            observed_after.get(
                "casefold_keywords",
                set(),
            )
        )
    )

    _log(
        "=" * 100
    )

    _log(
        "📊 사전추가 최종 결과"
    )

    _log(
        (
            "   └ 작업 ID: "
            f"{batch_id}"
        )
    )

    _log(
        (
            "   └ 작업 종료상태: "
            + (
                "사용자 중단"
                if interrupted
                else "정상 완료"
            )
        ),
        level=(
            "WARNING"
            if interrupted
            else "INFO"
        ),
    )

    _log(
        (
            "   └ 총 소요시간: "
            f"{_format_elapsed(elapsed_seconds)}"
        )
    )

    _log(
        (
            "   └ 엑셀 고유키워드: "
            f"{len(_safe_list(plan.get('raw_keywords')))}개"
        )
    )

    _log(
        (
            "   └ 기존 사전자료로 제외: "
            f"{len(existing_keywords)}개"
        )
    )

    _log(
        (
            "   └ 형식문제로 제외: "
            f"{len(invalid_keywords)}개"
        )
    )

    _log(
        (
            "   └ 신규수집 예정: "
            f"{len(pending_items)}개"
        )
    )

    _log(
        (
            "   └ 실제 처리: "
            f"{len(results)}개"
        )
    )

    _log(
        (
            "   └ 저장 성공: "
            f"{len(successful_keywords)}개"
        )
    )

    _log(
        (
            "   └ 검색결과 0개로 저장: "
            f"{len(no_result_keywords)}개"
        ),
        level=(
            "WARNING"
            if no_result_keywords
            else "INFO"
        ),
    )

    _log(
        (
            "   └ 저장 실패: "
            f"{len(failed_keywords)}개"
        ),
        level=(
            "WARNING"
            if failed_keywords
            else "INFO"
        ),
    )

    _log(
        (
            "   └ 분석된 상품 합계: "
            f"{total_sample_count}개"
        )
    )

    _log(
        (
            "   └ API 전체 시도횟수: "
            f"{total_attempt_count}회"
        )
    )

    _log(
        (
            "   └ 새로 누적된 미분류 참고정보 후보: "
            f"{total_candidate_count}개"
        )
    )

    _log(
        (
            "   └ 관찰사전 고유키워드: "
            f"{before_count}개 → {after_count}개 "
            f"(증가 {max(0, after_count - before_count)}개)"
        )
    )

    if status_counts:
        status_text = ", ".join(
            (
                f"{status} {count}개"
            )
            for status, count in sorted(
                status_counts.items()
            )
        )

        _log(
            (
                "   └ 처리상태 분포: "
                f"{status_text}"
            )
        )

    _log_keyword_list(
        label="저장 성공 키워드",
        keywords=successful_keywords,
    )

    if no_result_keywords:
        _log_keyword_list(
            label=(
                "검색결과 없이 빈 관찰기록으로 저장된 키워드"
            ),
            keywords=no_result_keywords,
            level="WARNING",
        )

    if failed_keywords:
        _log_keyword_list(
            label="저장 실패 키워드",
            keywords=failed_keywords,
            level="WARNING",
        )

        _log(
            (
                "   └ 실패키워드는 다음 사전추가 "
                "실행 때 다시 대상이 됩니다."
            ),
            level="WARNING",
        )

    _log(
        (
            "   └ 관찰사전: "
            f"{OBSERVATION_FILE}"
        )
    )

    _log(
        (
            "   └ 실행이력: "
            f"{DICTIONARY_COLLECTION_HISTORY_FILE}"
        )
    )

    if total_candidate_count > 0:
        _log(
            (
                "   └ 미분류 후보파일: "
                f"{REFERENCE_CANDIDATE_REGISTRY_FILE}"
            ),
            level="WARNING",
        )

    _log(
        "=" * 100
    )


def run_dictionary_add(
    collect_keyword: Callable[..., dict[str, Any]],
) -> bool:
    """
    사전추가 전체 흐름을 처리한다.

    반환값:
        True  -> 프로그램 종료
        False -> 초기 메뉴로 복귀
    """
    settings = (
        load_keyword_observation_settings()
    )

    if not bool(
        settings.get(
            "api_collection_enabled",
            True,
        )
    ):
        _log(
            (
                "네이버 쇼핑 신규검색 기능이 "
                "비활성화되어 있어 사전추가를 "
                "실행할 수 없습니다."
            ),
            level="WARNING",
        )
        return False

    _log(
        (
            "📚 키워드 관찰사전 "
            "사전추가 자료를 확인합니다."
        )
    )

    plan = _build_plan(
        settings
    )

    load_result = _safe_dict(
        plan.get(
            "load_result"
        )
    )

    files_found = _safe_list(
        load_result.get(
            "files_found"
        )
    )

    if not files_found:
        _log(
            (
                "입력폴더에 엑셀파일이 없습니다. "
                "첫 번째 시트에 '키워드' 열을 만든 "
                "엑셀파일을 넣어 주세요."
            ),
            level="WARNING",
        )
        return False

    observed_index = _safe_dict(
        plan.get(
            "observed_index"
        )
    )

    invalid_line_count = _safe_int(
        observed_index.get(
            "invalid_line_count"
        )
    )

    if invalid_line_count > 0:
        _log(
            (
                "기존 관찰 JSONL에서 읽지 못한 줄이 "
                f"{invalid_line_count}개 있습니다. "
                "'검사' 명령으로 확인해 주세요."
            ),
            level="WARNING",
        )

    _print_plan(
        plan=plan,
        settings=settings,
    )

    pending_items = [
        item
        for item in _safe_list(
            plan.get(
                "pending_keywords"
            )
        )
        if isinstance(
            item,
            dict,
        )
    ]

    if not pending_items:
        _log(
            (
                "새로 수집할 키워드가 없어 "
                "API를 호출하지 않습니다."
            )
        )

        _log(
            (
                "사전추가 확인이 끝났으므로 "
                "프로그램을 종료합니다."
            )
        )

        return True

    if not _confirm():
        _log(
            (
                "사전추가를 취소했습니다. "
                "API 호출과 데이터 저장 없이 "
                "프로그램을 종료합니다."
            ),
            level="WARNING",
        )

        return True

    bulk_output_mode = str(
        settings.get(
            "bulk_output_mode",
            "compact",
        )
    ).strip().lower() or "compact"

    delay_seconds = max(
        0.0,
        float(
            settings.get(
                "bulk_collection_delay_seconds",
                0.5,
            )
        ),
    )

    _log(
        "=" * 100
    )

    _log(
        (
            "🚀 키워드 관찰사전 일괄추가를 "
            f"시작합니다: {len(pending_items)}개"
        )
    )

    _log(
        "=" * 100
    )

    batch_id = (
        uuid.uuid4().hex
    )

    started_at = (
        time.perf_counter()
    )

    results: list[
        dict[str, Any]
    ] = []

    interrupted = False
    total_count = len(
        pending_items
    )

    for index, item in enumerate(
        pending_items,
        start=1,
    ):
        input_keyword = str(
            item.get(
                "input_keyword",
                "",
            )
        )

        source_files = [
            str(path)
            for path in _safe_list(
                item.get(
                    "source_files"
                )
            )
        ]

        _log(
            (
                f"[{index}/{total_count}] "
                f"사전추가 검색: '{input_keyword}'"
            )
        )

        try:
            result = collect_keyword(
                input_keyword,
                output_mode=(
                    bulk_output_mode
                ),
            )

        except KeyboardInterrupt:
            interrupted = True

            _log(
                (
                    "사용자 요청으로 사전추가를 "
                    "중단합니다. 현재까지 처리된 "
                    "결과를 종합합니다."
                ),
                level="WARNING",
            )

            break

        except Exception as error:
            result = {
                "status": (
                    "unexpected_error"
                ),
                "input_keyword": (
                    input_keyword
                ),
                "normalized_keyword": "",
                "sample_count": 0,
                "reference_candidate_count": 0,
                "attempt_count": 0,
                "message": str(error),
            }

            _log(
                (
                    f"[{index}/{total_count}] "
                    f"'{input_keyword}' 처리 오류: "
                    f"{error}"
                ),
                level="ERROR",
            )

        result[
            "input_keyword"
        ] = input_keyword

        results.append(
            result
        )

        status = str(
            result.get(
                "status",
                "unknown",
            )
        )

        sample_count = _safe_int(
            result.get(
                "sample_count"
            )
        )

        if status == "success":
            if sample_count > 0:
                _log(
                    (
                        f"[{index}/{total_count}] "
                        f"저장 완료: '{input_keyword}' "
                        f"({sample_count}개)"
                    )
                )

            else:
                _log(
                    (
                        f"[{index}/{total_count}] "
                        f"검색결과 없음 저장 완료: "
                        f"'{input_keyword}'"
                    ),
                    level="WARNING",
                )

        else:
            _log(
                (
                    f"[{index}/{total_count}] "
                    f"저장 실패: '{input_keyword}' "
                    f"({status})"
                ),
                level="WARNING",
            )

        try:
            append_dictionary_collection_history(
                batch_id=batch_id,
                keyword=input_keyword,
                normalized_keyword=str(
                    result.get(
                        "normalized_keyword",
                        "",
                    )
                ),
                status=status,
                source_files=source_files,
                sample_count=sample_count,
                message=str(
                    result.get(
                        "message",
                        "",
                    )
                ),
            )

        except DictionaryCollectionHistoryError as error:
            _log(
                str(error),
                level="WARNING",
            )

        if (
            index < total_count
            and delay_seconds > 0
        ):
            time.sleep(
                delay_seconds
            )

    elapsed_seconds = (
        time.perf_counter()
        - started_at
    )

    _print_final_summary(
        plan=plan,
        batch_id=batch_id,
        elapsed_seconds=(
            elapsed_seconds
        ),
        results=results,
        interrupted=interrupted,
    )

    _log(
        "사전추가 작업이 끝났습니다."
    )

    return True
