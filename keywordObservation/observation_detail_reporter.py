from __future__ import annotations

from typing import Any

from utils.global_logger import logger

from keywordObservation.naver_shopping_client import (
    NaverShoppingApiError,
)

from keywordObservation.observation_reporter import (
    print_final_observation_summary,
)


# =========================================================
# 출력 설정
# =========================================================

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
        "specification",
        "⚙️",
        "사양·표준",
    ),
    (
        "option",
        "🎛️",
        "옵션·선택",
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

    unclassified_items = _safe_list(
        distribution.get(
            "unclassified"
        )
    )

    if unclassified_items:
        _log(
            "   🧪 미분류 참고정보 후보"
        )

        formatted_candidates: list[str] = []

        for item in unclassified_items:
            if not isinstance(
                item,
                dict,
            ):
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

            ratio = _safe_float(
                item.get(
                    "ratio",
                    0.0,
                )
            )

            formatted_candidates.append(
                (
                    f"{token}: "
                    f"{product_count}/{sample_count} "
                    f"({ratio * 100:.1f}%)"
                )
            )

        _log_wrapped_items(
            formatted_candidates,
            items_per_line=(
                DISTRIBUTION_ITEMS_PER_LINE
            ),
            indent="   ",
            level="WARNING",
        )

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

def print_analysis(
    keyword: str,
    analysis: dict[str, Any],
) -> None:
    """
    키워드, 참고정보 및 카테고리 상세분석을 출력한다.
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

    exact_token_match_ratio = (
        exact_token_match_count / sample_count
        if sample_count > 0
        else 0.0
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
                    "   └ 단독키워드 분포현황: "
                    f"{exact_token_match_count}/"
                    f"{sample_count} "
                    f"({exact_token_match_ratio * 100:.1f}%)"
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
                    "   └ 단독키워드 분포현황: "
                    f"{exact_token_match_count}/"
                    f"{sample_count} "
                    f"({exact_token_match_ratio * 100:.1f}%)"
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

    analysis = dict(
        _safe_dict(
            observation.get("aggregates")
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

    print_final_observation_summary(
        keyword=keyword,
        analysis=analysis,
        query_validation=query_validation,
    )

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
        "📌 네이버 쇼핑 키워드·태그 지식사전"
    )

    _log(
        "   [키워드 입력]     저장된 쇼핑·태그·가공자료 통합조회"
    )

    _log(
        "   조회 [키워드]     통합 저장자료 조회 — 기존 명령 호환"
    )

    _log(
        "   검색 [키워드]     네이버 쇼핑 신규검색 후 저장"
    )

    _log(
        "   태그검색 [키워드] 커머스API 추천 태그 신규조회·저장"
    )

    _log(
        "   태그추가 [키워드] 실제 상품등록에 사용한 태그 수동저장"
    )

    _log(
        "   태그검사 [태그]   추천태그 정확일치·제한 여부 검사"
    )

    _log(
        "   사전추가          키워드 엑셀 요약 후 쇼핑자료 일괄수집"
    )

    _log(
        "   가공자료추가      최적화가공틀 요약 후 가공사례·태그 저장"
    )

    _log(
        "   검사              쇼핑 관찰이력 무결성 검사"
    )

    _log(
        "   백업              변경된 쇼핑 관찰이력 압축 백업"
    )

    _log(
        "   백업 강제         동일 내용도 새 쇼핑 관찰이력 백업 생성"
    )

    _log(
        "   Enter / q / exit / 종료   프로그램 종료"
    )

    _separator(
        char="=",
    )
