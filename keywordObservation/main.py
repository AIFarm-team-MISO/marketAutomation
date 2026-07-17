from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Any


# =========================================================
# 직접 실행할 때 프로젝트 루트를 import 경로에 추가
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from utils.global_logger import logger

from keywordObservation.naver_shopping_client import (
    NaverShoppingApiError,
    fetch_shopping_response,
)

from keywordObservation.observation_processor import (
    build_samples,
)

from keywordObservation.observation_analyzer import (
    analyze_samples,
)

from keywordObservation.category_concentration_analyzer import (
    analyze_category_concentration,
)

from keywordObservation.reference_classification_analyzer import (
    build_enhanced_reference_distribution,
)

from keywordObservation.reference_candidate_store import (
    ReferenceCandidateStoreError,
    update_reference_candidate_registry,
)

from keywordObservation.observation_detail_reporter import (
    print_analysis,
    print_api_error,
    print_format_validation,
    print_main_menu,
    print_query_validation,
    print_samples,
    print_saved_observation,
)

from keywordObservation.observation_reporter import (
    print_final_observation_summary,
)

from keywordObservation.query_validator import (
    evaluate_search_result,
    validate_keyword_format,
)

from keywordObservation.observation_store import (
    ObservationStoreError,
    append_observation,
    build_observation_record,
    ensure_latest_pretty_file,
    find_latest_observation,
)

from keywordObservation.observation_integrity import (
    check_observation_file,
    print_integrity_report,
)

from keywordObservation.observation_backup import (
    create_observation_backup,
    print_backup_result,
)


# =========================================================
# 실행 설정
# =========================================================

DISPLAY_COUNT = 20
DEFAULT_SORT = "sim"

EXIT_COMMANDS = {
    "종료",
    "exit",
    "q",
}

LOOKUP_COMMAND = "조회"
INTEGRITY_COMMAND = "검사"
BACKUP_COMMAND = "백업"
FORCE_BACKUP_COMMAND = "백업 강제"


# =========================================================
# 공통 처리
# =========================================================

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


def _log(
    message: str,
    level: str = "INFO",
) -> None:
    logger.log(
        message,
        level=level,
        also_to_report=True,
    )


def _prepare_observation_for_display(
    observation: dict[str, Any],
) -> dict[str, Any]:
    """
    과거 저장자료에 카테고리 집중도 값이 없으면
    기존 카테고리 집계로 화면 출력용 결과를 계산한다.

    원본 JSONL은 수정하지 않는다.
    """
    display_observation = dict(
        observation
    )

    analysis = dict(
        _safe_dict(
            observation.get(
                "aggregates"
            )
        )
    )

    if not _safe_dict(
        analysis.get(
            "category_concentration"
        )
    ):
        analysis[
            "category_concentration"
        ] = analyze_category_concentration(
            analysis
        )

    samples = [
        item
        for item in _safe_list(
            observation.get(
                "samples"
            )
        )
        if isinstance(
            item,
            dict,
        )
    ]

    reference_distribution = _safe_dict(
        analysis.get(
            "reference_token_distribution"
        )
    )

    if samples:
        # 사전이 수정된 뒤에도 기존 JSONL 원본은 건드리지 않고,
        # 조회할 때 현재 사전 기준으로 참고정보 분류를 다시 계산한다.
        analysis[
            "reference_token_distribution"
        ] = build_enhanced_reference_distribution(
            samples=samples,
            base_distribution=(
                reference_distribution
            ),
        )

    display_observation[
        "aggregates"
    ] = analysis

    return display_observation


# =========================================================
# 저장자료 조회
# =========================================================

def handle_lookup_command(
    keyword: str,
) -> None:
    normalized_keyword = " ".join(
        str(keyword).split()
    )

    if not normalized_keyword:
        _log(
            (
                "조회할 키워드를 입력해 주세요. "
                "예: 조회 박스테이프"
            ),
            level="WARNING",
        )
        return

    observation = find_latest_observation(
        normalized_keyword
    )

    if observation is None:
        _log(
            (
                "저장된 관찰자료가 없습니다: "
                f"'{normalized_keyword}'"
            ),
            level="WARNING",
        )
        return

    readable_path, repaired = (
        ensure_latest_pretty_file(
            keyword=normalized_keyword,
            observation=observation,
        )
    )

    if repaired and readable_path is not None:
        _log(
            (
                "♻️ 누락되거나 오래된 읽기용 "
                "최신파일 복구 완료: "
                f"{readable_path}"
            ),
            level="WARNING",
        )

    print_saved_observation(
        _prepare_observation_for_display(
            observation
        )
    )


# =========================================================
# 무결성 검사 및 백업
# =========================================================

def handle_integrity_command() -> None:
    _log(
        "🔎 관찰이력 무결성 검사를 시작합니다."
    )

    result = check_observation_file()

    print_integrity_report(
        result
    )

    if result.get(
        "is_healthy"
    ):
        _log(
            "✅ 관찰이력 무결성 검사 완료: 정상"
        )

    else:
        _log(
            (
                "⚠️ 관찰이력 무결성 검사 완료: "
                "확인이 필요한 문제가 있습니다."
            ),
            level="WARNING",
        )


def handle_backup_command(
    *,
    force: bool = False,
) -> None:
    if force:
        _log(
            "💾 관찰이력 강제 백업을 시작합니다."
        )

    else:
        _log(
            "💾 관찰이력 백업을 시작합니다."
        )

    result = create_observation_backup(
        force=force
    )

    print_backup_result(
        result
    )

    if result.get(
        "created"
    ):
        _log(
            (
                "✅ 관찰이력 백업 생성 완료: "
                f"{result.get('backup_path', '')}"
            )
        )

    else:
        _log(
            (
                "ℹ️ 동일한 내용의 백업이 이미 있어 "
                "새 백업 생성을 생략했습니다."
            )
        )


# =========================================================
# 신규 키워드 수집
# =========================================================

def collect_keyword(
    input_keyword: str,
) -> None:
    format_validation = (
        validate_keyword_format(
            input_keyword
        )
    )

    print_format_validation(
        format_validation
    )

    can_search = bool(
        format_validation.get(
            "can_search",
            False,
        )
    )

    if not can_search:
        _log(
            (
                "잘못된 검색어이므로 API 호출과 "
                "관찰데이터 저장을 생략합니다."
            ),
            level="WARNING",
        )
        return

    normalized_keyword = str(
        format_validation.get(
            "normalized_keyword",
            input_keyword,
        )
    ).strip()

    if not normalized_keyword:
        _log(
            "정규화된 검색어가 비어 있습니다.",
            level="ERROR",
        )
        return

    _log(
        (
            "네이버 쇼핑 검색 시작: "
            f"'{normalized_keyword}'"
        )
    )

    try:
        shopping_response = (
            fetch_shopping_response(
                keyword=normalized_keyword,
                display=DISPLAY_COUNT,
                sort=DEFAULT_SORT,
            )
        )

    except NaverShoppingApiError as error:
        print_api_error(
            error
        )
        return

    attempt_count = _safe_int(
        shopping_response.get(
            "attempt_count",
            1,
        ),
        1,
    )

    if attempt_count > 1:
        _log(
            (
                "네이버 쇼핑 API가 "
                f"{attempt_count}번째 시도에서 "
                "정상 응답했습니다."
            ),
            level="WARNING",
        )

    items = [
        item
        for item in _safe_list(
            shopping_response.get(
                "items",
                [],
            )
        )
        if isinstance(item, dict)
    ]

    if items:
        _log(
            (
                "네이버 쇼핑 상품 "
                f"{len(items)}개 수신 완료"
            )
        )

    else:
        _log(
            (
                "네이버 쇼핑 검색결과 없음: "
                "빈 결과를 정상 관찰기록으로 "
                "저장합니다."
            ),
            level="WARNING",
        )

    samples = build_samples(
        items
    )

    _log(
        (
            "관찰용 상품 데이터 "
            f"{len(samples)}개 변환 완료"
        )
    )

    analysis = analyze_samples(
        samples=samples,
        main_keyword=normalized_keyword,
    )

    analysis[
        "reference_token_distribution"
    ] = build_enhanced_reference_distribution(
        samples=samples,
        base_distribution=_safe_dict(
            analysis.get(
                "reference_token_distribution"
            )
        ),
    )

    analysis[
        "category_concentration"
    ] = analyze_category_concentration(
        analysis
    )

    _log(
        "키워드 및 카테고리 분석 완료"
    )

    query_validation = (
        evaluate_search_result(
            keyword=normalized_keyword,
            samples=samples,
        )
    )

    if samples:
        print_samples(
            keyword=normalized_keyword,
            samples=samples,
        )

    else:
        _log(
            (
                f"'{normalized_keyword}'의 "
                "상품 상세출력은 생략합니다."
            ),
            level="WARNING",
        )

    print_analysis(
        keyword=normalized_keyword,
        analysis=analysis,
    )

    print_query_validation(
        query_validation
    )

    print_final_observation_summary(
        keyword=normalized_keyword,
        analysis=analysis,
        query_validation=query_validation,
    )

    observation_record = (
        build_observation_record(
            keyword=input_keyword,
            display=DISPLAY_COUNT,
            sort=DEFAULT_SORT,
            samples=samples,
            analysis=analysis,
            query_validation=(
                query_validation
            ),
            response_metadata=(
                shopping_response
            ),
        )
    )

    observation_path = append_observation(
        observation_record
    )

    _log(
        (
            "💾 관찰이력 저장 완료: "
            f"{observation_path}"
        )
    )

    readable_path, _ = (
        ensure_latest_pretty_file(
            keyword=normalized_keyword,
            observation=observation_record,
            force=True,
        )
    )

    if readable_path is None:
        raise ObservationStoreError(
            "읽기용 최신파일을 생성하지 못했습니다."
        )

    _log(
        (
            "📖 읽기용 최신파일 저장 완료: "
            f"{readable_path}"
        )
    )

    try:
        candidate_path, candidate_count = (
            update_reference_candidate_registry(
                keyword=normalized_keyword,
                reference_distribution=(
                    _safe_dict(
                        analysis.get(
                            "reference_token_distribution"
                        )
                    )
                ),
            )
        )

        if candidate_count > 0:
            _log(
                (
                    "🧪 미분류 참고정보 후보 "
                    f"{candidate_count}개 누적 완료: "
                    f"{candidate_path}"
                ),
                level="WARNING",
            )

    except ReferenceCandidateStoreError as error:
        _log(
            (
                "미분류 참고정보 후보 저장 오류: "
                f"{error}"
            ),
            level="WARNING",
        )


# =========================================================
# 명령 처리
# =========================================================

def process_command(
    command: str,
) -> bool:
    normalized_command = str(
        command
    ).strip()

    if not normalized_command:
        return False

    if normalized_command.lower() in (
        EXIT_COMMANDS
    ):
        return False

    if normalized_command == INTEGRITY_COMMAND:
        handle_integrity_command()
        return True

    if normalized_command == BACKUP_COMMAND:
        handle_backup_command(
            force=False
        )
        return True

    if normalized_command == FORCE_BACKUP_COMMAND:
        handle_backup_command(
            force=True
        )
        return True

    if normalized_command == LOOKUP_COMMAND:
        _log(
            (
                "조회할 키워드를 함께 입력해 주세요. "
                "예: 조회 박스테이프"
            ),
            level="WARNING",
        )
        return True

    lookup_prefix = (
        LOOKUP_COMMAND + " "
    )

    if normalized_command.startswith(
        lookup_prefix
    ):
        lookup_keyword = (
            normalized_command[
                len(lookup_prefix):
            ].strip()
        )

        handle_lookup_command(
            lookup_keyword
        )

        return True

    collect_keyword(
        normalized_command
    )

    return True


# =========================================================
# 메인 실행
# =========================================================

def main() -> None:
    _log(
        " 네이버 쇼핑 관찰데이터 수집 프로그램"
    )

    while True:
        try:
            print_main_menu()

            command = input(
                "\n🔍 명령 또는 키워드를 입력해 주세요: "
            )

            should_continue = process_command(
                command
            )

            if not should_continue:
                _log(
                    "프로그램을 종료합니다."
                )
                break

        except ObservationStoreError as error:
            _log(
                (
                    "관찰데이터 저장·조회 오류: "
                    f"{error}"
                ),
                level="ERROR",
            )

        except ValueError as error:
            _log(
                (
                    "입력 또는 데이터 처리 오류: "
                    f"{error}"
                ),
                level="ERROR",
            )

        except KeyboardInterrupt:
            _log(
                (
                    "사용자 요청으로 "
                    "프로그램을 종료합니다."
                ),
                level="WARNING",
            )
            break

        except EOFError:
            _log(
                "입력이 종료되어 프로그램을 끝냅니다."
            )
            break

        except Exception as error:
            _log(
                (
                    "예상하지 못한 오류가 발생했습니다: "
                    f"{error}"
                ),
                level="ERROR",
            )

            _log(
                traceback.format_exc(),
                level="ERROR",
            )


if __name__ == "__main__":
    main()
