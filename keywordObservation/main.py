from __future__ import annotations

import json
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

from keywordObservation.observation_search_index import (
    ObservationSearchIndexError,
    find_containing_search_keywords,
    get_observation_search_index_status,
    load_observation_search_memory_index,
    rebuild_observation_search_index,
    update_observation_search_index,
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
    get_latest_pretty_path,
    normalize_keyword,
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

# 검색 인덱스 관리 명령
# 오늘은 메뉴와 명령 진입점만 구성하고,
# 실제 인덱스 생성·갱신 로직은 다음 작업에서 연결한다.
SEARCH_INDEX_STATUS_COMMAND = "검색인덱스 상태"
SEARCH_INDEX_UPDATE_COMMAND = "검색인덱스 업데이트"
SEARCH_INDEX_REBUILD_COMMAND = "검색인덱스 재구축"

# 정확 일치가 없는 일반 빠른 검색 결과의 페이지 크기.
FAST_SEARCH_PAGE_SIZE = 20

# 정확 일치 상세자료에서 연관검색을 열었을 때의 페이지 크기.
FAST_RELATED_SEARCH_PAGE_SIZE = 5

# 영문 메뉴키를 한글 입력상태에서도 동일하게 사용할 수 있도록
# 두벌식 자판의 호환 자모를 영문키로 되돌린다.
# 예: Q/q/ㅂ -> q, N/n/ㅜ -> n
KOREAN_MENU_KEY_TO_ENGLISH = {
    "ㅂ": "q",
    "ㅃ": "q",
    "ㅈ": "w",
    "ㅉ": "w",
    "ㄷ": "e",
    "ㄸ": "e",
    "ㄱ": "r",
    "ㄲ": "r",
    "ㅅ": "t",
    "ㅆ": "t",
    "ㅛ": "y",
    "ㅕ": "u",
    "ㅑ": "i",
    "ㅐ": "o",
    "ㅒ": "o",
    "ㅔ": "p",
    "ㅖ": "p",
    "ㅁ": "a",
    "ㄴ": "s",
    "ㅇ": "d",
    "ㄹ": "f",
    "ㅎ": "g",
    "ㅗ": "h",
    "ㅓ": "j",
    "ㅏ": "k",
    "ㅣ": "l",
    "ㅋ": "z",
    "ㅌ": "x",
    "ㅊ": "c",
    "ㅍ": "v",
    "ㅠ": "b",
    "ㅜ": "n",
    "ㅡ": "m",
}

# 페이지 이동은 화면에 <- / ->로 표시한다.
# 기존 N/P와 유니코드 화살표도 호환 입력으로 유지한다.
FAST_SEARCH_NEXT_COMMANDS = {"->", "→", "n", "다음"}
FAST_SEARCH_PREVIOUS_COMMANDS = {"<-", "←", "p", "이전"}
FAST_SEARCH_NEW_COMMANDS = {"s", "새검색", "재검색"}
FAST_SEARCH_RELATED_COMMANDS = {"r", "연관", "연관검색", "연관검색어"}
FAST_SEARCH_MAIN_COMMANDS = {"0", "m", "메인"}


# =========================================================
# 실행 중 검색 인덱스 메모리 상태
# =========================================================

SEARCH_INDEX_MEMORY: dict[str, Any] = {
    "loaded": False,
    "keyword_list": tuple(),
    "keyword_set": frozenset(),
    "keyword_count": 0,
    "schema_version": "",
    "built_at": "",
    "updated_at": "",
    "index_path": "",
    "loaded_at": "",
}


# =========================================================
# 조회 세션 메뉴 설정
# =========================================================

LOOKUP_MENU_RELATED_COMMANDS = {
    "연관",
    "연관검색",
}

LOOKUP_MENU_NEW_COMMANDS = {
    "1",
    "새조회",
    "상세조회",
}

LOOKUP_MENU_MAIN_COMMANDS = {
    "0",
    "메인",
    "m",
}


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


def _normalize_menu_command(
    value: Any,
) -> str:
    """
    메뉴 명령을 소문자 영문 기준으로 정규화한다.

    한글 입력상태에서 영문 단축키를 누르면 입력되는 호환 자모도
    같은 명령으로 처리한다. 예: ㅂ -> q, ㅜ -> n, ㅡ -> m.
    """
    normalized_value = str(
        value
    ).strip().lower()

    if len(normalized_value) == 1:
        return KOREAN_MENU_KEY_TO_ENGLISH.get(
            normalized_value,
            normalized_value,
        )

    return normalized_value


def _is_exit_command(
    value: Any,
) -> bool:
    return (
        _normalize_menu_command(value)
        in EXIT_COMMANDS
    )


def _is_menu_command(
    value: Any,
    commands: set[str],
) -> bool:
    return (
        _normalize_menu_command(value)
        in commands
    )



def _reset_search_index_memory() -> None:
    """
    실행 중 검색 인덱스 메모리를 빈 상태로 되돌린다.
    """
    global SEARCH_INDEX_MEMORY

    SEARCH_INDEX_MEMORY = {
        "loaded": False,
        "keyword_list": tuple(),
        "keyword_set": frozenset(),
        "keyword_count": 0,
        "schema_version": "",
        "built_at": "",
        "updated_at": "",
        "index_path": "",
        "loaded_at": "",
    }


def reload_search_index_memory(
    *,
    context: str = "프로그램 시작",
) -> bool:
    """
    디스크 검색 인덱스를 실행 중 메모리에 올린다.

    관찰사전과 인덱스가 최신 상태일 때만 메모리에 적재한다.
    업데이트 또는 재구축이 필요한 상태라면 빠른 검색 메모리를
    비워 두고 필요한 관리 명령을 안내한다.
    """
    global SEARCH_INDEX_MEMORY

    started_at = time.perf_counter()

    try:
        status = get_observation_search_index_status()

    except ObservationSearchIndexError as error:
        _reset_search_index_memory()
        _log(
            (
                "검색 인덱스 메모리 준비 오류: "
                f"{error}"
            ),
            level="ERROR",
        )
        return False

    status_code = str(
        status.get(
            "status_code",
            "",
        )
    ).strip()

    if status_code != "ready":
        _reset_search_index_memory()

        recommended_command = str(
            status.get(
                "recommended_command",
                "검색인덱스 상태",
            )
        ).strip()

        message = str(
            status.get(
                "message",
                "검색 인덱스를 바로 사용할 수 없는 상태입니다.",
            )
        ).strip()

        _log(
            (
                "⚠️ 검색 인덱스를 메모리에 올리지 않았습니다. "
                f"{message}"
            ),
            level="WARNING",
        )

        if recommended_command:
            _log(
                (
                    "   권장 작업: "
                    f"{recommended_command}"
                ),
                level="WARNING",
            )

        return False

    try:
        memory_index = (
            load_observation_search_memory_index()
        )

    except ObservationSearchIndexError as error:
        _reset_search_index_memory()
        _log(
            (
                "검색 인덱스 메모리 로딩 오류: "
                f"{error}"
            ),
            level="ERROR",
        )
        return False

    elapsed_seconds = (
        time.perf_counter()
        - started_at
    )

    SEARCH_INDEX_MEMORY = dict(
        memory_index
    )
    SEARCH_INDEX_MEMORY[
        "loaded_at"
    ] = time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    _log(
        (
            "✅ 검색 인덱스 메모리 로딩 완료 "
            f"({context})"
        )
    )
    _log(
        (
            "   검색키워드: "
            f"{_safe_int(SEARCH_INDEX_MEMORY.get('keyword_count')):,}개"
        )
    )
    _log(
        (
            "   인덱스 버전: "
            f"{SEARCH_INDEX_MEMORY.get('schema_version', '')}"
        )
    )
    _log(
        (
            "   로딩 시간: "
            f"{elapsed_seconds:.2f}초"
        )
    )

    return True


def print_main_menu() -> None:
    """
    키워드 관찰사전의 최종 메뉴 구조를 출력한다.

    현재 단계에서는 메뉴와 명령 진입점만 먼저 구성한다.
    일반 키워드의 빠른 검색과 검색 인덱스 관리는
    다음 개발 단계에서 실제 기능을 연결한다.
    """
    _log("=" * 100)
    _log("📌 네이버 쇼핑 키워드·태그 지식사전")
    _log("-" * 100)
    _log("[키워드 입력]         빠른 사전검색 — 정확·포함 키워드 탐색")
    _log("조회 [키워드]         상세 통합조회 — latest 파일 자동 점검·복구")
    _log("검색 [키워드]         네이버 쇼핑 신규검색 후 저장")
    _log("-" * 100)
    _log("검색인덱스 상태       검색 인덱스 키워드 수·갱신상태 확인")
    _log("검색인덱스 업데이트   신규 관찰 키워드를 기존 인덱스에 반영")
    _log("검색인덱스 재구축     전체 관찰사전 기준으로 인덱스 다시 생성")
    _log("-" * 100)
    _log("태그검색 [키워드]     커머스API 추천 태그 신규조회·저장")
    _log("태그추가 [키워드]     실제 상품등록에 사용한 태그 수동저장")
    _log("태그검사 [태그]       추천태그 정확일치·제한 여부 검사")
    _log("사전추가              키워드 엑셀 요약 후 쇼핑자료 일괄수집")
    _log("가공자료추가          최적화가공틀 요약 후 가공사례·태그 저장")
    _log("-" * 100)
    _log("검사                  쇼핑 관찰이력 무결성 검사")
    _log("백업                  변경된 쇼핑 관찰이력 압축 백업")
    _log("백업 강제             동일 내용도 새 쇼핑 관찰이력 백업 생성")
    _log("Enter / Q / exit / 종료   프로그램 종료")
    _log("※ 한글 입력 상태에서도 영문 메뉴키와 같은 자판 위치의 한글키를 사용할 수 있습니다.")
    _log("=" * 100)


def _build_fast_search_result(
    keyword: str,
    *,
    include_related: bool = True,
    related_only: bool = False,
) -> dict[str, Any]:
    """
    메모리 검색 인덱스에서 정확 일치와 포함 일치 결과를 만든다.

    정확 일치가 발견되고 ``include_related``가 False이면
    포함검색을 수행하지 않는다. 따라서 최초 키워드 입력에서
    정확 일치 자료를 가장 빠르게 바로 열 수 있다.

    JSONL 관찰사전이나 latest 파일은 읽지 않는다.
    """
    normalized_keyword = normalize_keyword(
        keyword
    )

    if not normalized_keyword:
        raise ValueError(
            "빠르게 검색할 키워드를 입력해 주세요."
        )

    if not bool(
        SEARCH_INDEX_MEMORY.get(
            "loaded",
            False,
        )
    ):
        raise ValueError(
            "빠른 검색용 메모리 인덱스가 준비되지 않았습니다. "
            "먼저 '검색인덱스 상태'를 확인해 주세요."
        )

    keyword_set = SEARCH_INDEX_MEMORY.get(
        "keyword_set",
        frozenset(),
    )
    keyword_list = SEARCH_INDEX_MEMORY.get(
        "keyword_list",
        tuple(),
    )

    if not isinstance(
        keyword_set,
        (
            set,
            frozenset,
        ),
    ):
        raise ValueError(
            "빠른 검색용 정확 일치 인덱스가 올바르지 않습니다. "
            "프로그램을 다시 실행하거나 '검색인덱스 재구축'을 실행해 주세요."
        )

    if not isinstance(
        keyword_list,
        (
            list,
            tuple,
        ),
    ):
        raise ValueError(
            "빠른 검색용 포함검색 인덱스가 올바르지 않습니다. "
            "프로그램을 다시 실행하거나 '검색인덱스 재구축'을 실행해 주세요."
        )

    started_at = time.perf_counter()

    found_exact_match = (
        normalized_keyword
        in keyword_set
    )

    should_find_related = (
        include_related
        or not found_exact_match
    )

    related_keywords: list[str] = []

    if should_find_related:
        related_keywords = (
            find_containing_search_keywords(
                normalized_keyword,
                keyword_list,
                exclude_exact=True,
            )
        )

    elapsed_milliseconds = (
        time.perf_counter()
        - started_at
    ) * 1000.0

    if related_only:
        result_keywords = list(
            related_keywords
        )
    else:
        result_keywords: list[str] = []

        if found_exact_match:
            result_keywords.append(
                normalized_keyword
            )

        result_keywords.extend(
            related_keywords
        )

    return {
        "query": normalized_keyword,
        "found_exact_match": found_exact_match,
        "exact_keyword": (
            normalized_keyword
            if found_exact_match
            else ""
        ),
        "related_keywords": related_keywords,
        "related_loaded": should_find_related,
        "related_only": related_only,
        "result_keywords": result_keywords,
        "result_count": len(result_keywords),
        "search_target_count": _safe_int(
            SEARCH_INDEX_MEMORY.get(
                "keyword_count"
            )
        ),
        "elapsed_milliseconds": elapsed_milliseconds,
    }

def _print_fast_search_page(
    result: dict[str, Any],
    *,
    page_index: int,
) -> int:
    """
    빠른 검색결과 한 페이지와 하단 메뉴를 출력한다.

    Returns
    -------
    int
        전체 페이지 수. 검색결과가 없어도 1을 반환한다.
    """
    query = str(
        result.get(
            "query",
            "",
        )
    )
    found_exact_match = bool(
        result.get(
            "found_exact_match",
            False,
        )
    )
    related_only = bool(
        result.get(
            "related_only",
            False,
        )
    )
    result_keywords = [
        str(item)
        for item in _safe_list(
            result.get(
                "result_keywords"
            )
        )
        if str(item).strip()
    ]
    result_count = len(
        result_keywords
    )

    page_size = (
        FAST_RELATED_SEARCH_PAGE_SIZE
        if related_only
        else FAST_SEARCH_PAGE_SIZE
    )

    total_pages = max(
        1,
        (
            result_count
            + page_size
            - 1
        )
        // page_size,
    )
    safe_page_index = min(
        max(page_index, 0),
        total_pages - 1,
    )
    start_index = (
        safe_page_index
        * page_size
    )
    end_index = min(
        start_index
        + page_size,
        result_count,
    )

    _log("=" * 100)
    _log(
        (
            (
                "🔗 연관검색: "
                if related_only
                else "🔎 빠른 사전검색: "
            )
            + f"'{query}'"
        )
    )

    if related_only and found_exact_match:
        _log(
            (
                "   연관 검색결과: "
                f"{result_count:,}개 | "
                f"현재 페이지: {safe_page_index + 1:,}/{total_pages:,}"
            )
        )
        _log("-" * 100)
        _log(
            f"     0. {query} [정확 일치 결과로 돌아가기]"
        )

        if result_count > 0:
            _log("-" * 100)

    elif result_count > 0:
        _log(
            (
                "   검색결과: "
                f"{result_count:,}개 | "
                f"현재 페이지: {safe_page_index + 1:,}/{total_pages:,}"
            )
        )
        _log("-" * 100)

    if result_count > 0:
        for global_index in range(
            start_index,
            end_index,
        ):
            result_keyword = (
                result_keywords[
                    global_index
                ]
            )
            exact_label = (
                " [정확 일치]"
                if (
                    found_exact_match
                    and not related_only
                    and global_index == 0
                )
                else ""
            )
            _log(
                (
                    f"   {global_index + 1:>3}. "
                    f"{result_keyword}"
                    f"{exact_label}"
                )
            )

    else:
        if related_only:
            _log(
                "ℹ️ 입력어를 포함하는 다른 저장 키워드가 없습니다."
            )
        else:
            _log(
                "ℹ️ 정확히 일치하거나 입력어 전체를 포함하는 저장 키워드가 없습니다."
            )

        if not (
            related_only
            and found_exact_match
        ):
            _log(
                "   검색 범위를 넓히려면 더 짧거나 다른 키워드를 직접 입력해 주세요."
            )

    _log("-" * 100)
    _log(
        (
            "   검색 대상: "
            f"{_safe_int(result.get('search_target_count')):,}개 | "
            "검색 시간: "
            f"{float(result.get('elapsed_milliseconds', 0.0)):.4f}ms"
        )
    )

    if found_exact_match and not related_only:
        _log(
            "[Enter] 정확 일치 자료 보기"
        )

    if result_count > 0:
        _log(
            "[번호] 해당 키워드 자료 보기"
        )

    if total_pages > 1:
        _log(
            "[←] 이전 페이지    [→] 다음 페이지"
        )

    if related_only and found_exact_match:
        _log(
            "[0] 정확 일치 자료 보기    [S] 새 키워드 입력    [M] 메인 메뉴    [Q] 프로그램 종료"
        )
    else:
        _log(
            "[S] 새 키워드 입력    [M / 0] 메인 메뉴    [Q] 프로그램 종료"
        )
    _log(
        "또는 이 입력창에 새 키워드를 바로 입력할 수 있습니다."
    )
    _log(
        "※ 한글 입력 상태에서도 영문 메뉴키와 같은 자판 위치의 한글키를 사용할 수 있습니다."
    )
    _log("=" * 100)

    return total_pages


def _input_with_page_arrow_keys(
    prompt: str,
) -> str:
    """
    빠른 검색결과 메뉴에서 실제 좌우 방향키를 페이지 명령으로 받는다.

    Windows에서는 ``input()``이 방향키를 문자열로 전달하지 않고
    콘솔의 커서 이동·명령 이력 기능으로 처리한다. 따라서 이 메뉴만
    ``msvcrt.getwch()``로 읽어 좌측 방향키는 ``<-``, 우측 방향키는
    ``->`` 명령으로 변환한다.

    일반 문자·한글·숫자·붙여넣기·Backspace·Enter 입력도 함께 받는다.
    방향키는 입력창이 비어 있을 때 페이지 이동 명령으로 처리한다.
    다른 운영체제에서는 기존 ``input()``으로 되돌아간다.
    """
    if sys.platform != "win32":
        return input(prompt).strip()

    try:
        import msvcrt

    except ImportError:
        return input(prompt).strip()

    print(
        prompt,
        end="",
        flush=True,
    )

    entered_characters: list[str] = []

    while True:
        character = msvcrt.getwch()

        # Windows 콘솔의 확장키는 2바이트 순서로 전달된다.
        if character in {"\x00", "\xe0"}:
            extended_key = msvcrt.getwch()

            # 입력 중인 문자가 없을 때만 좌우 방향키를
            # 페이지 이동 명령으로 즉시 확정한다.
            if not entered_characters:
                if extended_key == "K":
                    print("←")
                    return "<-"

                if extended_key == "M":
                    print("→")
                    return "->"

            # 그 밖의 기능키는 이 메뉴에서 사용하지 않는다.
            continue

        if character in {"\r", "\n"}:
            print()
            return "".join(
                entered_characters
            ).strip()

        if character == "\x03":
            # Ctrl+C
            print()
            raise KeyboardInterrupt

        if character == "\b":
            if entered_characters:
                entered_characters.pop()
                print(
                    "\b \b",
                    end="",
                    flush=True,
                )
            continue

        # Esc, Tab, Ctrl+Z 등 제어문자는 입력값에서 제외한다.
        if not character.isprintable():
            continue

        entered_characters.append(
            character
        )
        print(
            character,
            end="",
            flush=True,
        )


def _prompt_fast_search_keyword() -> tuple[str, str]:
    """
    빠른 검색세션에서 새 검색어를 별도로 입력받는다.

    Returns
    -------
    tuple[str, str]
        (동작, 키워드)
        동작은 search, main, exit 중 하나이다.
    """
    while True:
        entered_value = input(
            "\n📖 새 빠른검색 키워드 입력 (M/0: 메인, Q: 종료): "
        ).strip()

        if _is_exit_command(
            entered_value
        ):
            return "exit", ""

        if _is_menu_command(
            entered_value,
            FAST_SEARCH_MAIN_COMMANDS,
        ):
            return "main", ""

        normalized_keyword = normalize_keyword(
            entered_value
        )

        if normalized_keyword:
            return "search", normalized_keyword

        _log(
            "빠르게 검색할 키워드를 입력해 주세요.",
            level="WARNING",
        )


def _get_observation_keyword_for_fast_view(
    observation: dict[str, Any],
) -> str:
    """
    읽기용 latest JSON 내부에서 검색키워드를 안전하게 추출한다.
    """
    query = _safe_dict(
        observation.get(
            "query"
        )
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


def _load_fast_selected_observation(
    keyword: str,
) -> tuple[
    dict[str, Any] | None,
    Path | None,
    str,
    float,
]:
    """
    빠른 검색에서 선택된 키워드의 최신자료를 불러온다.

    처리 순서
    ---------
    1. readable/latest의 키워드 JSON을 직접 읽는다.
    2. 파일이 정상이고 내부 키워드가 일치하면 즉시 반환한다.
    3. 파일이 없거나 손상됐거나 다른 키워드 파일이면 그때만
       JSONL 원본에서 최신 관찰기록을 찾아 latest 파일을 복구한다.

    빠른 조회에서는 latest 파일과 JSONL의 날짜를 매번 비교하지 않는다.
    일반 조회 명령인 ``조회 [키워드]``만 기존처럼 최신성 점검을 담당한다.
    """
    normalized_keyword = normalize_keyword(
        keyword
    )

    if not normalized_keyword:
        raise ObservationStoreError(
            "빠르게 조회할 키워드가 비어 있습니다."
        )

    started_at = time.perf_counter()
    latest_path = get_latest_pretty_path(
        normalized_keyword
    )

    latest_failure_reason = ""

    if latest_path.exists():
        try:
            with latest_path.open(
                mode="r",
                encoding="utf-8",
            ) as file:
                loaded_observation = json.load(
                    file
                )

        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            latest_failure_reason = (
                "latest 파일이 손상됐거나 읽을 수 없음"
            )

        else:
            if not isinstance(
                loaded_observation,
                dict,
            ):
                latest_failure_reason = (
                    "latest 파일이 JSON 객체 형식이 아님"
                )

            else:
                stored_keyword = (
                    _get_observation_keyword_for_fast_view(
                        loaded_observation
                    )
                )

                if (
                    stored_keyword
                    != normalized_keyword
                ):
                    latest_failure_reason = (
                        "latest 파일 내부 키워드가 선택 키워드와 다름"
                    )

                else:
                    elapsed_milliseconds = (
                        time.perf_counter()
                        - started_at
                    ) * 1000.0

                    return (
                        loaded_observation,
                        latest_path,
                        "latest",
                        elapsed_milliseconds,
                    )

    else:
        latest_failure_reason = (
            "latest 파일이 없음"
        )

    # latest 파일을 바로 사용할 수 없을 때만 904MB JSONL 원본에서
    # 해당 키워드의 최신 기록을 찾아 복구한다.
    observation = find_latest_observation(
        normalized_keyword
    )

    if observation is None:
        elapsed_milliseconds = (
            time.perf_counter()
            - started_at
        ) * 1000.0

        return (
            None,
            latest_path,
            latest_failure_reason,
            elapsed_milliseconds,
        )

    repaired_path, _ = ensure_latest_pretty_file(
        keyword=normalized_keyword,
        observation=observation,
        force=True,
    )

    elapsed_milliseconds = (
        time.perf_counter()
        - started_at
    ) * 1000.0

    return (
        observation,
        repaired_path,
        "jsonl_repair",
        elapsed_milliseconds,
    )


def _print_fast_selected_keyword_detail(
    keyword: str,
) -> bool:
    """
    선택된 키워드의 쇼핑 관찰자료와 연결된 지식자료를 출력한다.

    쇼핑자료는 readable/latest를 우선 사용하고, latest를 바로 쓸 수
    없을 때만 JSONL 원본 조회와 latest 복구를 수행한다.
    """
    normalized_keyword = normalize_keyword(
        keyword
    )

    found_any_data = False

    try:
        (
            observation,
            readable_path,
            source_type,
            elapsed_milliseconds,
        ) = _load_fast_selected_observation(
            normalized_keyword
        )

    except ObservationStoreError as error:
        _log(
            (
                "빠른 상세자료 조회 오류: "
                f"{error}"
            ),
            level="ERROR",
        )
        observation = None
        readable_path = None
        source_type = "error"
        elapsed_milliseconds = 0.0

    if observation is not None:
        if source_type == "latest":
            _log(
                (
                    "⚡ latest 파일 직접 조회 완료: "
                    f"'{normalized_keyword}' "
                    f"({elapsed_milliseconds:.2f}ms)"
                )
            )

        elif source_type == "jsonl_repair":
            _log(
                (
                    "♻️ latest 파일이 없거나 손상되어 "
                    "관찰사전 원본에서 복구했습니다: "
                    f"{readable_path} "
                    f"({elapsed_milliseconds / 1000.0:.2f}초)"
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
                    f"'검색 {normalized_keyword}'를 입력해 주세요."
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


def _run_fast_selected_keyword_detail(
    keyword: str,
    *,
    allow_back: bool = True,
    allow_related_search: bool = False,
) -> tuple[str, str]:
    """
    선택한 키워드의 상세 통합자료를 출력한 뒤
    빠른 검색세션의 다음 동작을 입력받는다.

    상세 메뉴는 숫자 중심으로 표시한다.
    정확 일치 키워드에서는 1번으로 연관검색을 열 수 있고,
    연관검색 목록에서 0번으로 돌아온 뒤에도 같은 메뉴가 유지된다.
    """
    _print_fast_selected_keyword_detail(
        keyword
    )

    while True:
        print()
        print("=" * 76)
        print(
            f"📚 선택 키워드 상세자료: '{keyword}'"
        )
        print("-" * 76)

        if allow_back:
            print("Enter. 이전 검색결과로 돌아가기")

        if allow_related_search:
            print("1. 연관검색 보여주기")

        print("2. 새 키워드 입력")
        print("3. 메인 메뉴")
        print("4. 프로그램 종료")
        print("또는 새 키워드를 바로 입력")
        print("※ 한글 입력 상태에서도 영문 메뉴키와 같은 자판 위치의 한글키를 사용할 수 있습니다.")
        print("=" * 76)

        entered_value = input(
            "\n다음 작업을 입력해 주세요: "
        ).strip()

        if not entered_value:
            if allow_back:
                return "back", ""

            _log(
                "메뉴 번호 또는 새 검색키워드를 입력해 주세요.",
                level="WARNING",
            )
            continue

        # 숫자 메뉴를 우선 처리한다.
        if entered_value == "1":
            if allow_related_search:
                return "related", keyword

            _log(
                "현재 상세자료에서는 연관검색 메뉴를 사용할 수 없습니다.",
                level="WARNING",
            )
            continue

        if entered_value == "2":
            return _prompt_fast_search_keyword()

        if entered_value == "3":
            return "main", ""

        if entered_value == "4":
            return "exit", ""

        # 기존 영문·한글 자판 단축키도 호환 입력으로만 유지한다.
        if _is_exit_command(
            entered_value
        ):
            return "exit", ""

        if _is_menu_command(
            entered_value,
            FAST_SEARCH_MAIN_COMMANDS,
        ):
            return "main", ""

        if (
            allow_related_search
            and _is_menu_command(
                entered_value,
                FAST_SEARCH_RELATED_COMMANDS,
            )
        ):
            return "related", keyword

        if _is_menu_command(
            entered_value,
            FAST_SEARCH_NEW_COMMANDS,
        ):
            return _prompt_fast_search_keyword()

        normalized_keyword = normalize_keyword(
            entered_value
        )

        if normalized_keyword:
            return "search", normalized_keyword

        _log(
            "메뉴 번호 또는 새 검색키워드를 입력해 주세요.",
            level="WARNING",
        )

def run_fast_search_session(
    initial_keyword: str,
) -> bool:
    """
    일반 키워드 입력 후 빠른 검색 전용 세션을 유지한다.

    처리 원칙
    ---------
    1. 정확 일치가 있으면 포함검색을 생략하고 상세자료를 즉시 연다.
    2. 상세자료 하단의 1번 메뉴를 선택할 때만 연관검색을 수행한다.
    3. 연관검색 목록은 한 페이지에 5개씩 표시한다.
    4. 연관검색 목록의 0번은 최초 정확 일치 상세자료로 돌아간다.
    5. 0번으로 돌아온 상세자료에서도 1번 연관검색 메뉴를 유지한다.
    6. 정확 일치가 없으면 처음부터 포함검색 목록을 표시한다.
    """
    current_keyword = normalize_keyword(
        initial_keyword
    )

    if not current_keyword:
        _log(
            "빠르게 검색할 키워드를 입력해 주세요.",
            level="WARNING",
        )
        return True

    while True:
        try:
            initial_result = _build_fast_search_result(
                current_keyword,
                include_related=False,
            )

        except ValueError as error:
            _log(
                str(error),
                level="WARNING",
            )
            return True

        found_exact_match = bool(
            initial_result.get(
                "found_exact_match",
                False,
            )
        )
        exact_keyword = str(
            initial_result.get(
                "exact_keyword",
                "",
            )
        ).strip()

        # 정확 일치가 있으면 연관검색 목록을 만들거나 출력하지 않고
        # latest 상세자료를 즉시 연다.
        if found_exact_match and exact_keyword:
            action, next_keyword = (
                _run_fast_selected_keyword_detail(
                    exact_keyword,
                    allow_back=False,
                    allow_related_search=True,
                )
            )

            if action == "exit":
                return False

            if action == "main":
                return True

            if action == "search":
                current_keyword = next_keyword
                continue

            if action == "related":
                try:
                    result = _build_fast_search_result(
                        current_keyword,
                        include_related=True,
                        related_only=True,
                    )

                except ValueError as error:
                    _log(
                        str(error),
                        level="WARNING",
                    )
                    return True

            else:
                continue

        else:
            # 정확 일치가 없으면 최초 검색에서 포함검색까지 수행한다.
            result = initial_result

        page_index = 0

        while True:
            total_pages = _print_fast_search_page(
                result,
                page_index=page_index,
            )

            entered_value = _input_with_page_arrow_keys(
                "\n▶ 번호·메뉴 또는 새 키워드: "
            )

            result_keywords = [
                str(item)
                for item in _safe_list(
                    result.get(
                        "result_keywords"
                    )
                )
                if str(item).strip()
            ]

            selected_keyword = ""

            if not entered_value:
                _log(
                    "번호나 새 검색키워드를 입력해 주세요.",
                    level="WARNING",
                )
                continue

            if _is_exit_command(
                entered_value
            ):
                return False

            related_exact_keyword = str(
                result.get(
                    "exact_keyword",
                    "",
                )
            ).strip()
            is_related_result = bool(
                result.get(
                    "related_only",
                    False,
                )
            )

            # 연관검색 목록에서는 0번이 메인 메뉴가 아니라
            # 최초 정확 일치 키워드의 상세자료로 돌아가는 기능이다.
            if (
                entered_value == "0"
                and is_related_result
                and related_exact_keyword
            ):
                action, next_keyword = (
                    _run_fast_selected_keyword_detail(
                        related_exact_keyword,
                        allow_back=True,
                        allow_related_search=True,
                    )
                )

                if action == "exit":
                    return False

                if action == "main":
                    return True

                if action == "search":
                    current_keyword = next_keyword
                    break

                if action == "related":
                    # 이미 같은 연관검색 목록 안에 있으므로
                    # 기존 페이지를 그대로 다시 표시한다.
                    continue

                # back이면 같은 연관검색 결과 페이지로 돌아간다.
                continue

            if _is_menu_command(
                entered_value,
                FAST_SEARCH_MAIN_COMMANDS,
            ):
                return True

            if _is_menu_command(
                entered_value,
                FAST_SEARCH_NEW_COMMANDS,
            ):
                action, next_keyword = (
                    _prompt_fast_search_keyword()
                )

                if action == "exit":
                    return False

                if action == "main":
                    return True

                current_keyword = next_keyword
                break

            if _is_menu_command(
                entered_value,
                FAST_SEARCH_NEXT_COMMANDS,
            ):
                if page_index + 1 < total_pages:
                    page_index += 1
                else:
                    _log(
                        "마지막 페이지입니다.",
                        level="WARNING",
                    )
                continue

            if _is_menu_command(
                entered_value,
                FAST_SEARCH_PREVIOUS_COMMANDS,
            ):
                if page_index > 0:
                    page_index -= 1
                else:
                    _log(
                        "첫 페이지입니다.",
                        level="WARNING",
                    )
                continue

            if entered_value.isdigit():
                selected_index = int(
                    entered_value
                ) - 1

                if (
                    0 <= selected_index
                    < len(result_keywords)
                ):
                    selected_keyword = (
                        result_keywords[
                            selected_index
                        ]
                    )
                else:
                    _log(
                        (
                            "검색결과 번호 범위를 확인해 주세요: "
                            f"1~{len(result_keywords):,}"
                        ),
                        level="WARNING",
                    )
                    continue

            else:
                next_keyword = normalize_keyword(
                    entered_value
                )

                if next_keyword:
                    current_keyword = next_keyword
                    break

                _log(
                    "번호·메뉴 또는 새 검색키워드를 입력해 주세요.",
                    level="WARNING",
                )
                continue

            if selected_keyword:
                action, next_keyword = (
                    _run_fast_selected_keyword_detail(
                        selected_keyword,
                        allow_back=True,
                        allow_related_search=False,
                    )
                )

                if action == "exit":
                    return False

                if action == "main":
                    return True

                if action == "search":
                    current_keyword = next_keyword
                    break

                # back이면 같은 연관검색 결과 페이지를 다시 보여준다.
                continue

def handle_search_index_placeholder(
    command_name: str,
) -> None:
    """
    아직 구현하지 않은 검색 인덱스 메뉴의 임시 진입점.
    """
    _log(
        (
            f"'{command_name}' 기능은 아직 구현 전입니다. "
            "검색인덱스 재구축부터 순서대로 연결합니다."
        ),
        level="WARNING",
    )



def _format_file_size(
    size_bytes: Any,
) -> str:
    """
    바이트 크기를 사람이 보기 쉬운 단위로 표시한다.
    """
    size_value = max(
        0,
        _safe_int(size_bytes),
    )

    if size_value < 1024:
        return f"{size_value:,}바이트"

    size_float = float(
        size_value
    )

    for unit in (
        "KB",
        "MB",
        "GB",
        "TB",
    ):
        size_float /= 1024.0

        if (
            size_float < 1024.0
            or unit == "TB"
        ):
            return (
                f"{size_float:,.2f}{unit} "
                f"({size_value:,}바이트)"
            )

    return f"{size_value:,}바이트"


def _get_search_index_update_mode_label(
    mode: str,
) -> str:
    """
    인덱스 갱신방식을 화면용 한글로 바꾼다.
    """
    normalized_mode = str(
        mode
    ).strip().lower()

    if normalized_mode == "rebuild":
        return "전체 재구축"

    if normalized_mode == "incremental":
        return "증분 업데이트"

    return normalized_mode or "기록 없음"


def handle_search_index_status_command() -> None:
    """
    검색 인덱스 파일과 관찰사전 원본의 동기화 상태를 출력한다.

    원본 JSONL 전체를 읽지 않고 파일정보와 저장된 지문만 사용하므로
    빠르게 상태를 확인할 수 있다.
    """
    _log(
        "🔎 검색 인덱스 상태를 확인합니다."
    )

    started_at = time.perf_counter()

    try:
        result = (
            get_observation_search_index_status()
        )

    except ObservationSearchIndexError as error:
        _log(
            (
                "검색 인덱스 상태 확인 오류: "
                f"{error}"
            ),
            level="ERROR",
        )
        return

    elapsed_seconds = (
        time.perf_counter()
        - started_at
    )

    status_code = str(
        result.get(
            "status_code",
            "",
        )
    ).strip()
    status_label = str(
        result.get(
            "status_label",
            "확인 필요",
        )
    ).strip()

    if status_code == "ready":
        status_icon = "✅"
        status_level = "INFO"

    elif status_code == "update_required":
        status_icon = "⚠️"
        status_level = "WARNING"

    else:
        status_icon = "❌"
        status_level = "ERROR"

    _log("=" * 100)
    _log(
        (
            f"{status_icon} 검색 인덱스 상태: "
            f"{status_label}"
        ),
        level=status_level,
    )
    _log(
        (
            "   상태 설명: "
            f"{result.get('message', '')}"
        ),
        level=(
            "INFO"
            if status_code == "ready"
            else status_level
        ),
    )

    if bool(
        result.get(
            "index_exists"
        )
    ):
        _log(
            (
                "   전체 검색키워드: "
                f"{_safe_int(result.get('keyword_count')):,}개"
            )
        )
        _log(
            (
                "   인덱싱 관찰기록: "
                f"{_safe_int(result.get('indexed_valid_record_count')):,}건"
            )
        )
        _log(
            (
                "   중복 관찰기록: "
                f"{_safe_int(result.get('duplicate_record_count')):,}건"
            )
        )
        _log(
            (
                "   인덱스 버전: "
                f"{result.get('schema_version', '')}"
            )
        )
        _log(
            (
                "   최초 재구축 시각: "
                f"{result.get('built_at', '') or '기록 없음'}"
            )
        )
        _log(
            (
                "   마지막 갱신 시각: "
                f"{result.get('updated_at', '') or '기록 없음'}"
            )
        )
        _log(
            (
                "   누적 업데이트 횟수: "
                f"{_safe_int(result.get('update_count')):,}회"
            )
        )
        _log(
            (
                "   마지막 갱신방식: "
                f"{_get_search_index_update_mode_label(result.get('last_update_mode', ''))}"
            )
        )
        _log(
            (
                "   마지막 확인 관찰기록: "
                f"{_safe_int(result.get('last_appended_valid_record_count')):,}건"
            )
        )
        _log(
            (
                "   마지막 추가 키워드: "
                f"{_safe_int(result.get('last_added_keyword_count')):,}개"
            )
        )

    _log(
        (
            "   현재 관찰사전 크기: "
            f"{_format_file_size(result.get('current_size_bytes'))}"
        )
    )

    if bool(
        result.get(
            "index_exists"
        )
    ):
        _log(
            (
                "   인덱싱 기준 크기: "
                f"{_format_file_size(result.get('indexed_size_bytes'))}"
            )
        )
        _log(
            (
                "   미반영 추가 크기: "
                f"{_format_file_size(result.get('pending_size_bytes'))}"
            ),
            level=(
                "WARNING"
                if _safe_int(
                    result.get(
                        "pending_size_bytes"
                    )
                ) > 0
                else "INFO"
            ),
        )

    recommended_command = str(
        result.get(
            "recommended_command",
            "",
        )
    ).strip()

    if recommended_command:
        _log(
            (
                "   권장 작업: "
                f"{recommended_command}"
            ),
            level=status_level,
        )
    else:
        _log(
            "   권장 작업: 없음 — 바로 빠른 검색을 사용할 수 있습니다."
        )

    _log(
        (
            "   인덱스 경로: "
            f"{result.get('index_path', '')}"
        )
    )
    _log(
        (
            "   관찰사전 경로: "
            f"{result.get('source_path', '')}"
        )
    )
    _log(
        (
            "   확인 시간: "
            f"{elapsed_seconds:.2f}초"
        )
    )
    _log("=" * 100)

def handle_search_index_rebuild_command() -> None:
    """
    관찰사전 JSONL 전체를 기준으로 검색 인덱스를 새로 만든다.

    원본 관찰사전은 수정하지 않고,
    기존 검색 인덱스 파일만 안전하게 교체한다.
    """
    _log(
        "🔄 검색 인덱스 재구축을 시작합니다."
    )
    _log(
        (
            "관찰사전 전체를 한 번 읽어 고유 키워드 목록을 "
            "새로 생성합니다. 원본 관찰자료는 변경하지 않습니다."
        )
    )

    started_at = time.perf_counter()

    def print_progress(
        processed_record_count: int,
    ) -> None:
        _log(
            (
                "   └ 관찰기록 "
                f"{processed_record_count:,}건 확인 중..."
            )
        )

    try:
        result = rebuild_observation_search_index(
            progress_callback=print_progress,
            progress_interval=5000,
        )

    except ObservationSearchIndexError as error:
        _log(
            (
                "검색 인덱스 재구축 오류: "
                f"{error}"
            ),
            level="ERROR",
        )
        return

    elapsed_seconds = (
        time.perf_counter()
        - started_at
    )

    _log("=" * 100)
    _log("✅ 검색 인덱스 재구축 완료")
    _log(
        (
            "   원본 관찰기록: "
            f"{_safe_int(result.get('valid_record_count')):,}건"
        )
    )
    _log(
        (
            "   고유 검색키워드: "
            f"{_safe_int(result.get('keyword_count')):,}개"
        )
    )
    _log(
        (
            "   중복 관찰기록: "
            f"{_safe_int(result.get('duplicate_record_count')):,}건"
        )
    )

    missing_keyword_count = _safe_int(
        result.get(
            "missing_keyword_count"
        )
    )

    if missing_keyword_count > 0:
        _log(
            (
                "   키워드 없는 기록: "
                f"{missing_keyword_count:,}건"
            ),
            level="WARNING",
        )

    _log(
        (
            "   저장 경로: "
            f"{result.get('index_path', '')}"
        )
    )
    _log(
        (
            "   처리 시간: "
            f"{elapsed_seconds:.2f}초"
        )
    )
    _log("=" * 100)

    reload_search_index_memory(
        context="재구축 후 새로고침",
    )


def handle_search_index_update_command() -> None:
    """
    기존 검색 인덱스 생성 이후 관찰사전 끝에 추가된 기록만 읽어
    신규 키워드를 기존 인덱스에 반영한다.

    원본 관찰사전과 기존 검색 인덱스의 기존 자료는 수정하지 않고,
    갱신된 검색 인덱스 파일만 안전하게 교체한다.
    """
    _log(
        "🔄 검색 인덱스 업데이트를 시작합니다."
    )
    _log(
        (
            "기존 인덱스 이후에 추가된 관찰기록만 확인합니다. "
            "기존 관찰기록 전체는 다시 읽지 않습니다."
        )
    )

    started_at = time.perf_counter()

    def print_progress(
        processed_record_count: int,
    ) -> None:
        _log(
            (
                "   └ 추가 관찰기록 "
                f"{processed_record_count:,}건 확인 중..."
            )
        )

    try:
        result = update_observation_search_index(
            progress_callback=print_progress,
            progress_interval=1000,
        )

    except ObservationSearchIndexError as error:
        _log(
            (
                "검색 인덱스 업데이트 오류: "
                f"{error}"
            ),
            level="ERROR",
        )
        return

    elapsed_seconds = (
        time.perf_counter()
        - started_at
    )

    _log("=" * 100)

    if bool(
        result.get(
            "no_changes",
            False,
        )
    ):
        _log(
            "ℹ️ 검색 인덱스 업데이트 완료: 새 관찰기록이 없습니다."
        )
    else:
        _log(
            "✅ 검색 인덱스 업데이트 완료"
        )

    _log(
        (
            "   새로 확인한 관찰기록: "
            f"{_safe_int(result.get('appended_valid_record_count')):,}건"
        )
    )
    _log(
        (
            "   새로 추가된 고유키워드: "
            f"{_safe_int(result.get('added_keyword_count')):,}개"
        )
    )
    _log(
        (
            "   현재 전체 검색키워드: "
            f"{_safe_int(result.get('keyword_count')):,}개"
        )
    )

    appended_missing_keyword_count = _safe_int(
        result.get(
            "appended_missing_keyword_count"
        )
    )

    if appended_missing_keyword_count > 0:
        _log(
            (
                "   새 기록 중 키워드 없음: "
                f"{appended_missing_keyword_count:,}건"
            ),
            level="WARNING",
        )

    if not bool(
        result.get(
            "signature_verified",
            False,
        )
    ):
        _log(
            (
                "   참고: 기존 인덱스가 구버전이라 이번에는 "
                "파일크기 기준으로 업데이트했습니다. "
                "이번 저장부터 원본 변경 검증정보가 추가됩니다."
            ),
            level="WARNING",
        )

    _log(
        (
            "   저장 경로: "
            f"{result.get('index_path', '')}"
        )
    )
    _log(
        (
            "   처리 시간: "
            f"{elapsed_seconds:.2f}초"
        )
    )
    _log("=" * 100)

    reload_search_index_memory(
        context="업데이트 후 새로고침",
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


def print_lookup_navigation_menu(
    keyword: str,
    *,
    found_exact_data: bool,
) -> None:
    """
    상세 통합조회가 끝난 뒤 보여줄 이동 메뉴를 출력한다.

    연관 키워드 탐색은 일반 키워드의 빠른 사전검색 메뉴에서
    담당하고, 조회 명령은 정확 일치 상세조회와 latest 복구에
    집중하도록 역할을 분리한다.
    """
    lookup_status = (
        "정확 일치 자료 있음"
        if found_exact_data
        else "정확 일치 자료 없음"
    )

    print()
    print("=" * 72)
    print(
        f"📚 상세조회 메뉴: '{keyword}' "
        f"[{lookup_status}]"
    )
    print("-" * 72)
    print("1. 다른 키워드 상세조회")
    print("0 / M. 최초 메뉴로 돌아가기")
    print("Q. 프로그램 종료")
    print("※ 한글 입력 상태에서도 영문 메뉴키와 같은 자판 위치의 한글키를 사용할 수 있습니다.")
    print("=" * 72)


def prompt_new_lookup_keyword() -> tuple[str, bool]:
    """
    상세조회 세션 안에서 새로운 키워드를 입력받는다.

    Returns
    -------
    tuple[str, bool]
        새 키워드, 프로그램 종료 여부.

        키워드가 빈 문자열이고 종료 여부가 False이면
        최초 메뉴로 돌아간다는 뜻이다.
    """
    while True:
        entered_value = input(
            (
                "\n📖 새 상세조회 키워드 입력 "
                "(0/M: 최초 메뉴, Q: 종료): "
            )
        ).strip()

        if _is_exit_command(
            entered_value
        ):
            return "", True

        if _is_menu_command(
            entered_value,
            LOOKUP_MENU_MAIN_COMMANDS,
        ):
            return "", False

        normalized_keyword = " ".join(
            entered_value.split()
        )

        if normalized_keyword:
            return normalized_keyword, False

        _log(
            "상세조회할 키워드를 입력해 주세요.",
            level="WARNING",
        )


def run_lookup_session(
    initial_keyword: str,
) -> bool:
    """
    정확 일치 상세 통합조회와 조회 후 이동 메뉴를 처리한다.

    Returns
    -------
    bool
        True: 최초 메뉴로 돌아감
        False: 프로그램 종료
    """
    current_keyword = " ".join(
        str(initial_keyword).split()
    )

    if not current_keyword:
        _log(
            "상세조회할 키워드를 입력해 주세요.",
            level="WARNING",
        )
        return True

    while True:
        found_exact_data = handle_lookup_command(
            current_keyword
        )

        while True:
            print_lookup_navigation_menu(
                current_keyword,
                found_exact_data=found_exact_data,
            )

            selected_command = input(
                "\n메뉴를 선택해 주세요: "
            ).strip()

            if _is_exit_command(
                selected_command
            ):
                return False

            if _is_menu_command(
                selected_command,
                LOOKUP_MENU_MAIN_COMMANDS,
            ):
                return True

            if _is_menu_command(
                selected_command,
                LOOKUP_MENU_NEW_COMMANDS,
            ):
                next_keyword, should_exit = (
                    prompt_new_lookup_keyword()
                )

                if should_exit:
                    return False

                if not next_keyword:
                    return True

                current_keyword = next_keyword
                break

            _log(
                (
                    "올바른 메뉴를 선택해 주세요. "
                    "1, 0/M 또는 Q를 사용할 수 있습니다."
                ),
                level="WARNING",
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

    if _is_exit_command(
        normalized_command
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

    if normalized_command == SEARCH_INDEX_REBUILD_COMMAND:
        handle_search_index_rebuild_command()
        return True

    if normalized_command == SEARCH_INDEX_UPDATE_COMMAND:
        handle_search_index_update_command()
        return True

    if normalized_command == SEARCH_INDEX_STATUS_COMMAND:
        handle_search_index_status_command()
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

        return run_lookup_session(
            lookup_keyword
        )

    # 명령어가 아닌 일반 입력은 빠른 검색 전용 세션으로 처리한다.
    # 세션 안에서는 메인 메뉴를 반복 출력하지 않고 결과 하단의
    # 이동 메뉴와 새 키워드 직접입력을 사용한다.
    return run_fast_search_session(
        normalized_command
    )


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

    reload_search_index_memory(
        context="프로그램 시작",
    )

    while True:
        try:
            print_main_menu()

            command = input(
                (
                    "\n📖 빠르게 찾을 키워드 또는 "
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
