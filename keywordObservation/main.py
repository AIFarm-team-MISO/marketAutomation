from __future__ import annotations

import sys
import time
import traceback
import uuid
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

from keywordObservation.keyword_observation_paths import (
    DICTIONARY_COLLECTION_HISTORY_FILE,
    KEYWORD_INPUT_DIR,
    ensure_data_layout,
)

from keywordObservation.keyword_observation_settings import (
    KeywordObservationSettingsError,
    load_keyword_observation_settings,
)

from keywordObservation.keyword_input_loader import (
    load_keywords_from_input_folder,
)

from keywordObservation.observation_keyword_index import (
    load_observed_keyword_index,
)

from keywordObservation.dictionary_add_controller import (
    run_dictionary_add,
)

from keywordObservation.dictionary_collection_history import (
    DictionaryCollectionHistoryError,
    append_dictionary_collection_history,
)

from keywordObservation.keyword_knowledge_reporter import (
    print_keyword_knowledge,
)

from keywordObservation.tag_command_controller import (
    run_manual_tag_add,
    run_optimization_import,
    run_tag_check,
    run_tag_search,
)

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
# 데이터 폴더와 실행 설정
# =========================================================

DATA_LAYOUT_MESSAGES = (
    ensure_data_layout()
)

SETTINGS_LOAD_ERROR = ""

try:
    SETTINGS = (
        load_keyword_observation_settings()
    )

except KeywordObservationSettingsError as error:
    SETTINGS_LOAD_ERROR = str(
        error
    )

    SETTINGS = {
        "display_count": 20,
        "default_sort": "sim",
        "api_collection_enabled": False,
        "keyword_column": "키워드",
        "supported_excel_extensions": [
            ".xlsx",
            ".xls",
            ".xlsm",
        ],
        "skip_existing_on_dictionary_add": True,
        "bulk_collection_delay_seconds": 0.5,
        "bulk_output_mode": "compact",
        "tag_api_enabled": False,
        "tag_check_delay_seconds": 0.2,
        "show_manual_tag_limit": 30,
        "show_optimization_example_limit": 3,
        "optimization_input_extensions": [
            ".xlsx",
            ".xlsm",
            ".xls",
        ],
    }


DISPLAY_COUNT = int(
    SETTINGS.get(
        "display_count",
        20,
    )
)

DEFAULT_SORT = str(
    SETTINGS.get(
        "default_sort",
        "sim",
    )
)

API_COLLECTION_ENABLED = bool(
    SETTINGS.get(
        "api_collection_enabled",
        True,
    )
)

KEYWORD_COLUMN = str(
    SETTINGS.get(
        "keyword_column",
        "키워드",
    )
)

SUPPORTED_EXCEL_EXTENSIONS = list(
    SETTINGS.get(
        "supported_excel_extensions",
        [
            ".xlsx",
            ".xls",
            ".xlsm",
        ],
    )
)

SKIP_EXISTING_ON_DICTIONARY_ADD = bool(
    SETTINGS.get(
        "skip_existing_on_dictionary_add",
        True,
    )
)

BULK_COLLECTION_DELAY_SECONDS = float(
    SETTINGS.get(
        "bulk_collection_delay_seconds",
        0.5,
    )
)

BULK_OUTPUT_MODE = str(
    SETTINGS.get(
        "bulk_output_mode",
        "compact",
    )
).strip().lower()


TAG_API_ENABLED = bool(
    SETTINGS.get(
        "tag_api_enabled",
        True,
    )
)

TAG_CHECK_DELAY_SECONDS = float(
    SETTINGS.get(
        "tag_check_delay_seconds",
        0.2,
    )
)

SHOW_MANUAL_TAG_LIMIT = int(
    SETTINGS.get(
        "show_manual_tag_limit",
        30,
    )
)

SHOW_OPTIMIZATION_EXAMPLE_LIMIT = int(
    SETTINGS.get(
        "show_optimization_example_limit",
        3,
    )
)

OPTIMIZATION_INPUT_EXTENSIONS = list(
    SETTINGS.get(
        "optimization_input_extensions",
        [
            ".xlsx",
            ".xlsm",
            ".xls",
        ],
    )
)


# =========================================================
# 명령 설정
# =========================================================

EXIT_COMMANDS = {
    "종료",
    "exit",
    "q",
}

LOOKUP_COMMAND = "조회"
SEARCH_COMMAND = "검색"
DICTIONARY_ADD_COMMAND = "사전추가"
TAG_SEARCH_COMMAND = "태그검색"
TAG_ADD_COMMAND = "태그추가"
TAG_CHECK_COMMAND = "태그검사"
OPTIMIZATION_IMPORT_COMMAND = "가공자료추가"
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

    except (
        TypeError,
        ValueError,
    ):
        return default


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
    기존 JSONL 원본은 수정하지 않고
    최신 참고정보 사전 기준으로 화면 출력값을 다시 계산한다.
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
) -> bool:
    normalized_keyword = " ".join(
        str(keyword).split()
    )

    if not normalized_keyword:
        _log(
            (
                "조회할 키워드를 입력해 주세요. "
                "예: 박스테이프"
            ),
            level="WARNING",
        )
        return False

    found_any_data = False

    observation = find_latest_observation(
        normalized_keyword
    )

    if observation is not None:
        readable_path, repaired = (
            ensure_latest_pretty_file(
                keyword=normalized_keyword,
                observation=observation,
            )
        )

        if (
            repaired
            and readable_path is not None
        ):
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
        found_any_data = True

    else:
        _log(
            (
                "저장된 네이버 쇼핑 관찰자료가 없습니다: "
                f"'{normalized_keyword}'"
            ),
            level="WARNING",
        )

        if API_COLLECTION_ENABLED:
            _log(
                (
                    "   └ 신규 쇼핑검색이 필요하면 "
                    f"'검색 {normalized_keyword}'를 "
                    "입력해 주세요."
                ),
                level="WARNING",
            )

    knowledge_found = print_keyword_knowledge(
        normalized_keyword,
        manual_tag_limit=SHOW_MANUAL_TAG_LIMIT,
        optimization_example_limit=(
            SHOW_OPTIMIZATION_EXAMPLE_LIMIT
        ),
        show_empty_sections=True,
    )

    found_any_data = (
        found_any_data
        or knowledge_found
    )

    if not found_any_data:
        _log(
            (
                "이 키워드와 연결된 저장자료가 아직 없습니다. "
                f"쇼핑자료: '검색 {normalized_keyword}', "
                f"태그자료: '태그검색 {normalized_keyword}'"
            ),
            level="WARNING",
        )

    return found_any_data


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
    *,
    output_mode: str = "full",
) -> dict[str, Any]:
    """
    네이버 쇼핑 검색부터 분석·저장까지 한 키워드를 처리한다.

    output_mode='full':
        기존 단일검색처럼 상세결과 전체 출력

    output_mode='compact':
        사전추가용으로 진행상황만 간단히 출력
    """
    normalized_output_mode = (
        str(output_mode)
        .strip()
        .lower()
    )

    show_full_output = (
        normalized_output_mode
        == "full"
    )

    if not API_COLLECTION_ENABLED:
        message = (
            "네이버 쇼핑 신규검색 기능이 "
            "비활성화되어 있습니다."
        )

        _log(
            message,
            level="WARNING",
        )

        return {
            "status": "api_disabled",
            "input_keyword": input_keyword,
            "normalized_keyword": "",
            "sample_count": 0,
            "message": message,
        }

    format_validation = (
        validate_keyword_format(
            input_keyword
        )
    )

    if show_full_output:
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
        message = (
            "잘못된 검색어이므로 API 호출과 "
            "관찰데이터 저장을 생략합니다."
        )

        _log(
            message,
            level="WARNING",
        )

        return {
            "status": "invalid_keyword",
            "input_keyword": input_keyword,
            "normalized_keyword": "",
            "sample_count": 0,
            "message": message,
        }

    normalized_keyword = str(
        format_validation.get(
            "normalized_keyword",
            input_keyword,
        )
    ).strip()

    if not normalized_keyword:
        message = (
            "정규화된 검색어가 비어 있습니다."
        )

        _log(
            message,
            level="ERROR",
        )

        return {
            "status": "invalid_keyword",
            "input_keyword": input_keyword,
            "normalized_keyword": "",
            "sample_count": 0,
            "message": message,
        }

    if show_full_output:
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
        if show_full_output:
            print_api_error(
                error
            )

        else:
            _log(
                (
                    "네이버 쇼핑 API 오류: "
                    f"'{normalized_keyword}' / {error}"
                ),
                level="ERROR",
            )

        return {
            "status": "api_error",
            "input_keyword": input_keyword,
            "normalized_keyword": (
                normalized_keyword
            ),
            "sample_count": 0,
            "message": str(error),
        }

    attempt_count = _safe_int(
        shopping_response.get(
            "attempt_count",
            1,
        ),
        1,
    )

    if (
        attempt_count > 1
        and show_full_output
    ):
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
        if isinstance(
            item,
            dict,
        )
    ]

    if show_full_output:
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

    if show_full_output:
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

    query_validation = (
        evaluate_search_result(
            keyword=normalized_keyword,
            samples=samples,
        )
    )

    if show_full_output:
        _log(
            "키워드 및 카테고리 분석 완료"
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
            query_validation=(
                query_validation
            ),
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

    if show_full_output:
        _log(
            (
                "💾 관찰이력 저장 완료: "
                f"{observation_path}"
            )
        )

        _log(
            (
                "📖 읽기용 최신파일 저장 완료: "
                f"{readable_path}"
            )
        )

    candidate_count = 0
    candidate_path = ""

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

        if (
            candidate_count > 0
            and show_full_output
        ):
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

    return {
        "status": "success",
        "input_keyword": input_keyword,
        "normalized_keyword": (
            normalized_keyword
        ),
        "sample_count": len(
            samples
        ),
        "observation_path": str(
            observation_path
        ),
        "readable_path": str(
            readable_path
        ),
        "reference_candidate_count": (
            candidate_count
        ),
        "reference_candidate_path": str(
            candidate_path
        ),
        "attempt_count": attempt_count,
        "message": "",
    }


# =========================================================
# 엑셀 기반 키워드 관찰사전 일괄 추가
# =========================================================

def handle_dictionary_add_command() -> bool:
    """
    사전추가 실행 전 엑셀 내용을 검토하고,
    실행 또는 취소 후 프로그램 종료 여부를 반환한다.
    """
    return run_dictionary_add(
        collect_keyword
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

    if normalized_command == TAG_SEARCH_COMMAND:
        _log(
            "태그검색 키워드를 함께 입력해 주세요. 예: 태그검색 양면테이프",
            level="WARNING",
        )
        return True

    tag_search_prefix = TAG_SEARCH_COMMAND + " "

    if normalized_command.startswith(tag_search_prefix):
        run_tag_search(
            normalized_command[len(tag_search_prefix):].strip(),
            tag_api_enabled=TAG_API_ENABLED,
        )
        return True

    if normalized_command == TAG_ADD_COMMAND:
        _log(
            "태그를 연결할 키워드를 함께 입력해 주세요. 예: 태그추가 양면테이프",
            level="WARNING",
        )
        return True

    tag_add_prefix = TAG_ADD_COMMAND + " "

    if normalized_command.startswith(tag_add_prefix):
        run_manual_tag_add(
            normalized_command[len(tag_add_prefix):].strip()
        )
        return True

    if normalized_command == TAG_CHECK_COMMAND:
        _log(
            "검사할 태그를 함께 입력해 주세요. 예: 태그검사 강력테이프, 투명테이프",
            level="WARNING",
        )
        return True

    tag_check_prefix = TAG_CHECK_COMMAND + " "

    if normalized_command.startswith(tag_check_prefix):
        run_tag_check(
            normalized_command[len(tag_check_prefix):].strip(),
            tag_api_enabled=TAG_API_ENABLED,
            delay_seconds=TAG_CHECK_DELAY_SECONDS,
        )
        return True

    if normalized_command == OPTIMIZATION_IMPORT_COMMAND:
        run_optimization_import(
            supported_extensions=OPTIMIZATION_INPUT_EXTENSIONS,
        )
        return True

    if normalized_command.startswith(OPTIMIZATION_IMPORT_COMMAND + " "):
        _log(
            (
                "가공자료추가는 별도 파일경로를 입력하지 않습니다. "
                "data/optimization_inputs 폴더에 엑셀을 넣은 뒤 "
                "'가공자료추가'만 입력해 주세요."
            ),
            level="WARNING",
        )
        return True

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

    if normalized_command == DICTIONARY_ADD_COMMAND:
        should_exit = (
            handle_dictionary_add_command()
        )

        return not should_exit

    if normalized_command.startswith(
        DICTIONARY_ADD_COMMAND + " "
    ):
        _log(
            (
                "사전추가는 별도 파일경로를 입력하지 않습니다. "
                f"엑셀파일을 {KEYWORD_INPUT_DIR}에 넣은 뒤 "
                "'사전추가'만 입력해 주세요."
            ),
            level="WARNING",
        )
        return True

    if normalized_command == SEARCH_COMMAND:
        _log(
            (
                "검색할 키워드를 함께 입력해 주세요. "
                "예: 검색 박스테이프"
            ),
            level="WARNING",
        )
        return True

    search_prefix = (
        SEARCH_COMMAND + " "
    )

    if normalized_command.startswith(
        search_prefix
    ):
        search_keyword = (
            normalized_command[
                len(search_prefix):
            ].strip()
        )

        collect_keyword(
            search_keyword,
            output_mode="full",
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

    # 명령어가 아닌 일반 입력은 기본적으로 사전조회한다.
    handle_lookup_command(
        normalized_command
    )

    return True


# =========================================================
# 메인 실행
# =========================================================

def main() -> None:
    _log(
        " 네이버 쇼핑 키워드 관찰사전 프로그램"
    )

    if SETTINGS_LOAD_ERROR:
        _log(
            (
                "키워드 관찰사전 설정 오류: "
                f"{SETTINGS_LOAD_ERROR}"
            ),
            level="ERROR",
        )

        _log(
            (
                "data/keyword_observation_settings.json을 "
                "수정한 뒤 다시 실행해 주세요."
            ),
            level="ERROR",
        )

        return

    for message in DATA_LAYOUT_MESSAGES:
        _log(
            (
                "♻️ "
                f"{message}"
            ),
            level="WARNING",
        )

    while True:
        try:
            print_main_menu()

            command = input(
                (
                    "\n📖 조회할 키워드 또는 "
                    "명령을 입력해 주세요: "
                )
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
