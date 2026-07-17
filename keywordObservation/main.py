from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Any


# =========================================================
# 직접 실행할 때 프로젝트 루트를 import 경로에 추가
#
# 실행 예:
# python F:/marketAutomation/keywordObservation/main.py
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

KEYWORD_ITEMS_PER_LINE = 7
DISTRIBUTION_ITEMS_PER_LINE = 5


REFERENCE_SECTION_CONFIG = (
    (
        "quantity",
        "📦",
        "수량·구성",
    ),
    (
        "measurement",
        "📏",
        "규격·치수",
    ),
    (
        "english",
        "🔤",
        "영문 표현",
    ),
    (
        "model_code",
        "🏷️",
        "모델·상품코드",
    ),
)


# =========================================================
# 공통 안전 변환
# =========================================================

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


def _separator(
    char: str = "-",
) -> None:
    logger.log_separator(
        char=char,
        level="INFO",
        also_to_report=True,
    )


# =========================================================
# 리스트 출력
# =========================================================

def _log_wrapped_items(
    items: list[str],
    *,
    items_per_line: int,
    empty_message: str = "없음",
    indent: str = "",
    level: str = "INFO",
) -> None:
    """
    문자열 목록을 일정 개수씩 나누어 출력한다.
    """
    if not items:
        _log(
            f"{indent}{empty_message}",
            level=level,
        )
        return

    for start_index in range(
        0,
        len(items),
        items_per_line,
    ):
        line_items = items[
            start_index:
            start_index + items_per_line
        ]

        _log(
            indent + ", ".join(line_items),
            level=level,
        )


def _format_keyword_items(
    items: Any,
) -> list[str]:
    """
    다음 구조를 출력용 문자열로 변환한다.

    [
        {
            "keyword": "투명",
            "count": 12
        }
    ]
    """
    formatted_items: list[str] = []

    for item in _safe_list(items):
        if not isinstance(item, dict):
            continue

        keyword = str(
            item.get(
                "keyword",
                item.get(
                    "token",
                    "",
                ),
            )
        ).strip()

        if not keyword:
            continue

        count = _safe_int(
            item.get(
                "count",
                item.get(
                    "product_count",
                    0,
                ),
            )
        )

        formatted_items.append(
            f"{keyword}({count})"
        )

    return formatted_items


# =========================================================
# 상품별 상세 출력
# =========================================================

def print_samples(
    keyword: str,
    samples: list[dict[str, Any]],
) -> None:
    """
    처리된 상품명과 키워드 정보를 출력한다.

    source_item의 판매처·가격·링크·이미지 등은
    JSON에만 저장하고 여기에서는 출력하지 않는다.
    """
    if not samples:
        _log(
            (
                f"'{keyword}' 검색결과에 "
                "출력할 상품이 없습니다."
            ),
            level="WARNING",
        )
        return

    _log(
        (
            f" {keyword} - 상위 "
            f"{len(samples)}개 상품명 처리 시작"
        )
    )

    _separator(
        char="=",
    )

    for sample in samples:
        rank = _safe_int(
            sample.get("rank"),
            0,
        )

        original_title = str(
            sample.get(
                "original_title",
                "",
            )
        )

        brand = str(
            sample.get(
                "brand",
                "",
            )
        ).strip()

        cleaned_title = str(
            sample.get(
                "cleaned_title",
                "",
            )
        )

        frequency_title = str(
            sample.get(
                "frequency_title",
                "",
            )
        )

        tokens = _safe_list(
            sample.get("tokens")
        )

        removed_brands = _safe_list(
            sample.get(
                "removed_brands"
            )
        )

        category_path = str(
            sample.get(
                "category_path",
                "",
            )
        ).strip()

        _log(
            (
                f"{rank}. 원본상품명: "
                f"'{original_title}'"
            )
        )

        _log(
            (
                "   └ API 브랜드: "
                f"{brand or '없음'}"
            )
        )

        if removed_brands:
            _log(
                (
                    "   └ ❌ 제거된 브랜드명: "
                    f"{removed_brands}"
                )
            )

        else:
            _log(
                "   └ 제거된 브랜드명: 없음"
            )

        _log(
            (
                "   └ 브랜드 제거 상품명: "
                f"'{cleaned_title}'"
            )
        )

        _log(
            (
                "   └ 빈도분석 상품명: "
                f"'{frequency_title}'"
            )
        )

        _log(
            f"   └ 토큰: {tokens}"
        )

        _log(
            (
                "   └ 📚 카테고리: "
                f"{category_path or '없음'}"
            )
        )


# =========================================================
# 상품명 참고정보 출력
# =========================================================

def _has_reference_distribution(
    analysis: dict[str, Any],
) -> bool:
    distribution = _safe_dict(
        analysis.get(
            "reference_token_distribution"
        )
    )

    for category, _, _ in (
        REFERENCE_SECTION_CONFIG
    ):
        if _safe_list(
            distribution.get(category)
        ):
            return True

    return False


def print_reference_token_distribution(
    analysis: dict[str, Any],
) -> None:
    """
    수량·규격·영문·모델코드의 상품별 분포를 출력한다.
    """
    distribution = _safe_dict(
        analysis.get(
            "reference_token_distribution"
        )
    )

    sample_count = _safe_int(
        distribution.get(
            "sample_count",
            analysis.get(
                "sample_count",
                0,
            ),
        )
    )

    if not _has_reference_distribution(
        analysis
    ):
        return

    _log(
        "📎 상품명 참고정보 분포"
    )

    for category, icon, label in (
        REFERENCE_SECTION_CONFIG
    ):
        category_items = _safe_list(
            distribution.get(category)
        )

        if not category_items:
            continue

        _log(
            f"   {icon} {label}"
        )

        formatted_items: list[str] = []

        for item in category_items:
            if not isinstance(item, dict):
                continue

            token = str(
                item.get(
                    "token",
                    "",
                )
            ).strip()

            if not token:
                continue

            product_count = _safe_int(
                item.get(
                    "product_count",
                    0,
                )
            )

            default_ratio = (
                product_count / sample_count
                if sample_count > 0
                else 0.0
            )

            ratio = _safe_float(
                item.get(
                    "ratio",
                    default_ratio,
                ),
                default_ratio,
            )

            formatted_items.append(
                (
                    f"{token}: "
                    f"{product_count}/{sample_count} "
                    f"({ratio * 100:.1f}%)"
                )
            )

        _log_wrapped_items(
            formatted_items,
            items_per_line=(
                DISTRIBUTION_ITEMS_PER_LINE
            ),
            indent="   ",
        )


# =========================================================
# 검색키워드 분포 출력
# =========================================================

def _build_legacy_search_distribution(
    analysis: dict[str, Any],
    keyword: str,
) -> list[dict[str, Any]]:
    """
    과거 저장자료에 search_keyword_distribution이 없을 때
    메인키워드 구성 단어만 선별해 분포를 복원한다.

    excluded_keywords 전체를 출력하지 않으므로
    '개'와 같은 기본 제외어가 검색키워드로 표시되지 않는다.
    """
    sample_count = _safe_int(
        analysis.get(
            "sample_count",
            0,
        )
    )

    keyword_tokens = list(
        dict.fromkeys(
            token
            for token in str(
                keyword
            ).split()
            if token
        )
    )

    product_keyword_counts = _safe_dict(
        analysis.get(
            "product_keyword_counts"
        )
    )

    excluded_count_mapping: dict[str, int] = {}

    for item in _safe_list(
        analysis.get(
            "excluded_keywords"
        )
    ):
        if not isinstance(item, dict):
            continue

        excluded_keyword = str(
            item.get(
                "keyword",
                "",
            )
        ).strip()

        if not excluded_keyword:
            continue

        excluded_count_mapping[
            excluded_keyword
        ] = _safe_int(
            item.get(
                "count",
                0,
            )
        )

    distribution: list[
        dict[str, Any]
    ] = []

    for keyword_token in keyword_tokens:
        product_count = _safe_int(
            product_keyword_counts.get(
                keyword_token,
                excluded_count_mapping.get(
                    keyword_token,
                    0,
                ),
            )
        )

        ratio = (
            product_count / sample_count
            if sample_count > 0
            else 0.0
        )

        distribution.append(
            {
                "keyword": keyword_token,
                "product_count": (
                    product_count
                ),
                "ratio": ratio,
            }
        )

    return distribution


def print_search_keyword_distribution(
    analysis: dict[str, Any],
    keyword: str,
) -> None:
    """
    사용자가 입력한 검색어 구성 단어별 분포를 출력한다.
    """
    distribution_items = _safe_list(
        analysis.get(
            "search_keyword_distribution"
        )
    )

    if not distribution_items:
        distribution_items = (
            _build_legacy_search_distribution(
                analysis=analysis,
                keyword=keyword,
            )
        )

    if not distribution_items:
        return

    sample_count = _safe_int(
        analysis.get(
            "sample_count",
            0,
        )
    )

    _log(
        "🔎 검색키워드 분포현황"
    )

    formatted_items: list[str] = []

    for item in distribution_items:
        if not isinstance(item, dict):
            continue

        item_keyword = str(
            item.get(
                "keyword",
                "",
            )
        ).strip()

        if not item_keyword:
            continue

        product_count = _safe_int(
            item.get(
                "product_count",
                item.get(
                    "count",
                    0,
                ),
            )
        )

        default_ratio = (
            product_count / sample_count
            if sample_count > 0
            else 0.0
        )

        ratio = _safe_float(
            item.get(
                "ratio",
                default_ratio,
            ),
            default_ratio,
        )

        formatted_items.append(
            (
                f"{item_keyword}: "
                f"{product_count}/{sample_count} "
                f"({ratio * 100:.1f}%)"
            )
        )

    _log_wrapped_items(
        formatted_items,
        items_per_line=(
            DISTRIBUTION_ITEMS_PER_LINE
        ),
        indent="   ",
    )


# =========================================================
# 카테고리 출력
# =========================================================

def print_categories(
    analysis: dict[str, Any],
) -> None:
    top_categories = _safe_list(
        analysis.get(
            "top_categories"
        )
    )

    sample_count = _safe_int(
        analysis.get(
            "sample_count",
            0,
        )
    )

    _log(
        "📚 네이버 상위 카테고리 TOP 3"
    )

    if not top_categories:
        _log(
            "   카테고리 자료 없음",
            level="WARNING",
        )
        return

    for index, item in enumerate(
        top_categories,
        start=1,
    ):
        if not isinstance(item, dict):
            continue

        category_path = str(
            item.get(
                "category_path",
                "",
            )
        ).strip()

        count = _safe_int(
            item.get(
                "count",
                0,
            )
        )

        default_ratio = (
            count / sample_count
            if sample_count > 0
            else 0.0
        )

        ratio = _safe_float(
            item.get(
                "ratio",
                default_ratio,
            ),
            default_ratio,
        )

        _log(
            (
                f"   {index}. "
                f"{category_path or '카테고리 없음'}"
            )
        )

        _log(
            (
                f"      └ 빈도: "
                f"{count}/{sample_count}, "
                f"비율: {ratio * 100:.1f}%"
            )
        )


# =========================================================
# 제거 브랜드 출력
# =========================================================

def print_removed_brand_distribution(
    analysis: dict[str, Any],
) -> None:
    removed_brand_counts = analysis.get(
        "removed_brand_counts",
        {},
    )

    formatted_items: list[str] = []

    if isinstance(
        removed_brand_counts,
        dict,
    ):
        for brand, count in (
            removed_brand_counts.items()
        ):
            normalized_brand = str(
                brand
            ).strip()

            if not normalized_brand:
                continue

            formatted_items.append(
                (
                    f"{normalized_brand}"
                    f"({_safe_int(count)})"
                )
            )

    elif isinstance(
        removed_brand_counts,
        list,
    ):
        formatted_items = (
            _format_keyword_items(
                removed_brand_counts
            )
        )

    _log(
        "🏷️ 제거된 브랜드 빈도"
    )

    _log_wrapped_items(
        formatted_items,
        items_per_line=(
            KEYWORD_ITEMS_PER_LINE
        ),
    )


# =========================================================
# 전체 분석 출력
# =========================================================

def print_analysis(
    keyword: str,
    analysis: dict[str, Any],
) -> None:
    """
    키워드, 참고정보, 검색어 분포 및 카테고리를 출력한다.
    """
    _separator(
        char="=",
    )

    _log(
        "🔝 빈도우위 키워드 🔝"
    )

    high_frequency_items = (
        _format_keyword_items(
            analysis.get(
                "high_frequency_keywords"
            )
        )
    )

    _log_wrapped_items(
        high_frequency_items,
        items_per_line=(
            KEYWORD_ITEMS_PER_LINE
        ),
    )

    _separator()

    _log(
        "🧵 빈도하위 키워드 🧵"
    )

    low_frequency_items = (
        _format_keyword_items(
            analysis.get(
                "low_frequency_keywords"
            )
        )
    )

    _log_wrapped_items(
        low_frequency_items,
        items_per_line=(
            KEYWORD_ITEMS_PER_LINE
        ),
    )

    if _has_reference_distribution(
        analysis
    ):
        _separator()

        print_reference_token_distribution(
            analysis
        )

    _separator()

    print_search_keyword_distribution(
        analysis=analysis,
        keyword=keyword,
    )

    _separator()

    print_categories(
        analysis
    )

    _separator()

    print_removed_brand_distribution(
        analysis
    )

    _separator(
        char="=",
    )


# =========================================================
# 검색어 형식 검사 출력
# =========================================================

def print_format_validation(
    validation: dict[str, Any],
) -> None:
    status = str(
        validation.get(
            "status",
            "",
        )
    ).strip()

    normalized_keyword = str(
        validation.get(
            "normalized_keyword",
            "",
        )
    ).strip()

    if status == "invalid":
        icon = "❌"
        heading = "검색어 형식 확인 필요"
        level = "WARNING"

    elif status == "warning":
        icon = "⚠️"
        heading = "검색어 형식 주의"
        level = "WARNING"

    else:
        return

    _log(
        (
            f"{icon} {heading}: "
            f"'{normalized_keyword}'"
        ),
        level=level,
    )

    for message in _safe_list(
        validation.get("messages")
    ):
        normalized_message = str(
            message
        ).strip()

        if normalized_message:
            _log(
                (
                    "   └ "
                    f"{normalized_message}"
                ),
                level=level,
            )


# =========================================================
# 검색결과 검증 출력
# =========================================================

def print_query_validation(
    validation: dict[str, Any],
) -> None:
    if not validation:
        return

    status = str(
        validation.get(
            "status",
            "",
        )
    ).strip()

    normalized_keyword = str(
        validation.get(
            "normalized_keyword",
            "",
        )
    ).strip()

    if status == "valid":
        icon = "✅"
        heading = "네이버 메인키워드"
        level = "INFO"

    elif status == "review":
        icon = "⚠️"
        heading = "네이버 메인키워드 검토 필요"
        level = "WARNING"

    elif status == "no_results":
        icon = "⚠️"
        heading = "네이버 검색결과 없음"
        level = "WARNING"

    elif status == "invalid":
        icon = "❌"
        heading = "검색어 형식 확인 필요"
        level = "WARNING"

    else:
        icon = "⚠️"
        heading = "네이버 메인키워드 주의"
        level = "WARNING"

    _log(
        (
            f"{icon} {heading}: "
            f"'{normalized_keyword}'"
        ),
        level=level,
    )

    sample_count = _safe_int(
        validation.get(
            "sample_count",
            0,
        )
    )

    keyword_token_count = _safe_int(
        validation.get(
            "keyword_token_count",
            1,
        ),
        1,
    )

    phrase_match_count = _safe_int(
        validation.get(
            "phrase_match_count",
            validation.get(
                "compact_match_count",
                0,
            ),
        )
    )

    phrase_match_ratio = _safe_float(
        validation.get(
            "phrase_match_ratio",
            (
                phrase_match_count
                / sample_count
                if sample_count > 0
                else 0.0
            ),
        )
    )

    all_token_match_count = _safe_int(
        validation.get(
            "all_token_match_count",
            phrase_match_count,
        )
    )

    all_token_match_ratio = _safe_float(
        validation.get(
            "all_token_match_ratio",
            validation.get(
                "match_ratio",
                (
                    all_token_match_count
                    / sample_count
                    if sample_count > 0
                    else 0.0
                ),
            ),
        )
    )

    exact_token_match_count = _safe_int(
        validation.get(
            "exact_token_match_count",
            0,
        )
    )

    if sample_count > 0:
        if keyword_token_count > 1:
            _log(
                (
                    "   └ 전체 문구 연속 일치: "
                    f"{phrase_match_count}/"
                    f"{sample_count} "
                    f"({phrase_match_ratio * 100:.1f}%)"
                ),
                level=level,
            )

            _log(
                (
                    "   └ 모든 검색어 토큰 포함: "
                    f"{all_token_match_count}/"
                    f"{sample_count} "
                    f"({all_token_match_ratio * 100:.1f}%)"
                ),
                level=level,
            )

            _log(
                (
                    "   └ 모든 토큰 독립 일치: "
                    f"{exact_token_match_count}/"
                    f"{sample_count}"
                ),
                level=level,
            )

        else:
            _log(
                (
                    "   └ 검색어 포함 상품: "
                    f"{all_token_match_count}/"
                    f"{sample_count} "
                    f"({all_token_match_ratio * 100:.1f}%)"
                ),
                level=level,
            )

            _log(
                (
                    "   └ 독립 토큰 일치 상품: "
                    f"{exact_token_match_count}/"
                    f"{sample_count}"
                ),
                level=level,
            )

    for message in _safe_list(
        validation.get("messages")
    ):
        normalized_message = str(
            message
        ).strip()

        if normalized_message:
            _log(
                (
                    "   └ "
                    f"{normalized_message}"
                ),
                level=level,
            )


# =========================================================
# 저장자료 조회
# =========================================================

def _get_observation_keyword(
    observation: dict[str, Any],
) -> str:
    query = _safe_dict(
        observation.get("query")
    )

    normalized_keyword = str(
        query.get(
            "normalized_keyword",
            "",
        )
    ).strip()

    if normalized_keyword:
        return normalized_keyword

    return str(
        query.get(
            "input_keyword",
            "",
        )
    ).strip()


def print_saved_observation(
    observation: dict[str, Any],
) -> None:
    """
    저장된 최신 관찰기록을 콘솔에 출력한다.
    """
    keyword = _get_observation_keyword(
        observation
    )

    captured_at = str(
        observation.get(
            "captured_at",
            "",
        )
    ).strip()

    response = _safe_dict(
        observation.get("response")
    )

    samples = [
        sample
        for sample in _safe_list(
            observation.get("samples")
        )
        if isinstance(sample, dict)
    ]

    analysis = _safe_dict(
        observation.get("aggregates")
    )

    query_validation = _safe_dict(
        observation.get(
            "query_validation"
        )
    )

    collection_status = str(
        response.get(
            "collection_status",
            (
                "success"
                if samples
                else "no_results"
            ),
        )
    ).strip()

    _log(
        (
            f"📖 저장된 최신 관찰자료: "
            f"'{keyword}'"
        )
    )

    if captured_at:
        _log(
            f"   └ 수집시각: {captured_at}"
        )

    _log(
        (
            "   └ 수집상태: "
            f"{collection_status}"
        )
    )

    if samples:
        print_samples(
            keyword=keyword,
            samples=samples,
        )

    else:
        _log(
            "저장된 상품 샘플이 없습니다.",
            level="WARNING",
        )

    print_analysis(
        keyword=keyword,
        analysis=analysis,
    )

    print_query_validation(
        query_validation
    )


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
        observation
    )


# =========================================================
# 무결성 검사 및 백업
# =========================================================

def handle_integrity_command() -> None:
    """
    관찰이력 JSONL 전체의 무결성을 검사한다.

    파일 내용은 수정하지 않는다.
    """
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
    """
    관찰이력 JSONL을 gzip으로 압축 백업한다.

    force=True이면 같은 내용의 백업이 있어도
    새 백업을 생성한다.
    """
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
# API 오류 출력
# =========================================================

def print_api_error(
    error: NaverShoppingApiError,
) -> None:
    retryable = bool(
        getattr(
            error,
            "retryable",
            False,
        )
    )

    level = (
        "WARNING"
        if retryable
        else "ERROR"
    )

    category = str(
        getattr(
            error,
            "category",
            "unknown_error",
        )
    )

    attempt_count = _safe_int(
        getattr(
            error,
            "attempt_count",
            1,
        ),
        1,
    )

    status_code = getattr(
        error,
        "status_code",
        None,
    )

    _log(
        (
            "네이버 쇼핑 API 처리 실패: "
            f"{error}"
        ),
        level=level,
    )

    _log(
        (
            "   └ 오류 분류: "
            f"{category}"
        ),
        level=level,
    )

    if status_code is not None:
        _log(
            (
                "   └ HTTP 상태: "
                f"{status_code}"
            ),
            level=level,
        )

    _log(
        (
            "   └ 재시도 가능 여부: "
            f"{retryable}"
        ),
        level=level,
    )

    _log(
        (
            "   └ 실행 시도 횟수: "
            f"{attempt_count}"
        ),
        level=level,
    )

    _log(
        (
            "수집에 실패한 자료는 정상 관찰이력에 "
            "저장하지 않습니다."
        ),
        level=level,
    )


# =========================================================
# 신규 키워드 수집
# =========================================================

def collect_keyword(
    input_keyword: str,
) -> None:
    """
    키워드 한 건을 호출·처리·분석·저장한다.
    """
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

    raw_items = shopping_response.get(
        "items",
        [],
    )

    items = [
        item
        for item in _safe_list(raw_items)
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

            # 신규 수집 결과는 반드시 최신파일에 반영
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


# =========================================================
# 명령 처리
# =========================================================

def process_command(
    command: str,
) -> bool:
    """
    명령을 처리한다.

    Returns
    -------
    bool
        계속 실행하면 True,
        종료하면 False.
    """
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
# 메인 메뉴
# =========================================================

def print_main_menu() -> None:
    """
    사용 가능한 명령을 보기 좋게 출력한다.

    프로그램 시작 시와 각 명령 처리 후
    다음 입력을 받기 전에 매번 표시한다.
    """
    _separator(
        char="=",
    )

    _log(
        "📌 네이버 쇼핑 관찰데이터 메뉴"
    )

    _log(
        "   [키워드 입력]     신규 검색결과 수집"
    )

    _log(
        "   조회 [키워드]     저장된 최신자료 조회"
    )

    _log(
        "   검사              관찰이력 무결성 검사"
    )

    _log(
        "   백업              변경된 관찰이력 압축 백업"
    )

    _log(
        "   백업 강제         동일 내용도 새 백업 생성"
    )

    _log(
        "   Enter / q / exit / 종료   프로그램 종료"
    )

    _separator(
        char="=",
    )


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