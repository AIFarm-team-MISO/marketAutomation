from __future__ import annotations

from typing import Any

from utils.global_logger import logger

from keywordObservation.category_concentration_analyzer import (
    analyze_category_concentration,
)


# =========================================================
# 최종 요약 설정
# =========================================================

SUMMARY_REFERENCE_MIN_RATIO = 0.15
SUMMARY_UNCLASSIFIED_MIN_RATIO = 0.10
SUMMARY_KEYWORDS_PER_LINE = 7
SUMMARY_ITEMS_PER_LINE = 4

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
    indent: str = "",
    empty_message: str = "없음",
) -> None:
    if not items:
        _log(
            f"{indent}{empty_message}"
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
            indent + ", ".join(
                line_items
            )
        )


def _format_keyword_items(
    items: Any,
) -> list[str]:
    result: list[str] = []

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

        result.append(
            f"{keyword}({count})"
        )

    return result


def _build_reference_summary(
    analysis: dict[str, Any],
    minimum_ratio: float,
) -> list[
    tuple[str, str, list[str]]
]:
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

    result: list[
        tuple[str, str, list[str]]
    ] = []

    for category, icon, label in (
        REFERENCE_SECTION_CONFIG
    ):
        formatted_items: list[str] = []

        for item in _safe_list(
            distribution.get(category)
        ):
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

            if ratio < minimum_ratio:
                continue

            formatted_items.append(
                (
                    f"{token} "
                    f"{product_count}/{sample_count} "
                    f"({ratio * 100:.1f}%)"
                )
            )

        if formatted_items:
            result.append(
                (
                    icon,
                    label,
                    formatted_items,
                )
            )

    return result



def _build_unclassified_summary(
    analysis: dict[str, Any],
    minimum_ratio: float,
) -> list[str]:
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

    result: list[str] = []

    for item in _safe_list(
        distribution.get(
            "unclassified"
        )
    ):
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

        if ratio < minimum_ratio:
            continue

        result.append(
            (
                f"{token} "
                f"{product_count}/{sample_count} "
                f"({ratio * 100:.1f}%)"
            )
        )

    return result

def _format_removed_brands(
    analysis: dict[str, Any],
) -> list[str]:
    removed_brand_counts = analysis.get(
        "removed_brand_counts",
        {},
    )

    result: list[str] = []

    if isinstance(
        removed_brand_counts,
        dict,
    ):
        for brand, raw_count in (
            removed_brand_counts.items()
        ):
            normalized_brand = str(
                brand
            ).strip()

            if not normalized_brand:
                continue

            result.append(
                (
                    f"{normalized_brand}"
                    f"({_safe_int(raw_count)})"
                )
            )

        return result

    return _format_keyword_items(
        removed_brand_counts
    )


def _get_category_concentration(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    stored_result = _safe_dict(
        analysis.get(
            "category_concentration"
        )
    )

    if stored_result:
        return stored_result

    return analyze_category_concentration(
        analysis
    )


def _build_keyword_interpretation_messages(
    analysis: dict[str, Any],
    query_validation: dict[str, Any],
) -> list[str]:
    messages: list[str] = []

    sample_count = _safe_int(
        query_validation.get(
            "sample_count",
            analysis.get(
                "sample_count",
                0,
            ),
        )
    )

    keyword_token_count = _safe_int(
        query_validation.get(
            "keyword_token_count",
            1,
        ),
        1,
    )

    included_count = _safe_int(
        query_validation.get(
            "all_token_match_count",
            query_validation.get(
                "phrase_match_count",
                0,
            ),
        )
    )

    included_ratio = _safe_float(
        query_validation.get(
            "all_token_match_ratio",
            query_validation.get(
                "match_ratio",
                (
                    included_count / sample_count
                    if sample_count > 0
                    else 0.0
                ),
            ),
        )
    )

    exact_count = _safe_int(
        query_validation.get(
            "exact_token_match_count",
            0,
        )
    )

    exact_ratio = (
        exact_count / sample_count
        if sample_count > 0
        else 0.0
    )

    if sample_count < 1:
        messages.append(
            "검색결과가 없어 키워드 적합성을 해석할 수 없습니다."
        )

    elif keyword_token_count > 1:
        phrase_ratio = _safe_float(
            query_validation.get(
                "phrase_match_ratio",
                0.0,
            )
        )

        if phrase_ratio >= 0.60:
            messages.append(
                "복합 검색어 전체 문구가 상위상품에 비교적 안정적으로 나타납니다."
            )

        elif included_ratio >= 0.60:
            messages.append(
                "각 검색어 토큰은 함께 포함되지만 전체 문구가 연속으로 쓰이는 비율은 낮습니다."
            )

        else:
            messages.append(
                "복합 검색어의 구성 토큰이 함께 나타나는 비율이 낮아 검색어 조합 검토가 필요합니다."
            )

    else:
        if (
            included_ratio >= 0.80
            and exact_ratio < 0.50
        ):
            messages.append(
                "검색어는 상품명에 널리 포함되지만 주로 다른 단어와 결합된 형태로 사용됩니다."
            )

        elif exact_ratio >= 0.60:
            messages.append(
                "검색어가 단독키워드로도 다수의 상위상품명에 나타납니다."
            )

        elif included_ratio < 0.50:
            messages.append(
                "검색어가 포함된 상위상품 비율이 낮아 메인키워드 적합성 검토가 필요합니다."
            )

        else:
            messages.append(
                "검색어 포함률과 단독키워드 분포현황을 함께 참고해 상품명 적용 범위를 판단해야 합니다."
            )

    return messages


def print_final_observation_summary(
    keyword: str,
    analysis: dict[str, Any],
    query_validation: dict[str, Any],
    *,
    reference_min_ratio: float = (
        SUMMARY_REFERENCE_MIN_RATIO
    ),
) -> None:
    """
    상세 분석 중 실제 판단에 필요한 값만 모아
    마지막 요약으로 출력한다.
    """
    normalized_keyword = " ".join(
        str(keyword).split()
    )

    sample_count = _safe_int(
        analysis.get(
            "sample_count",
            0,
        )
    )

    _separator(
        char="=",
    )

    _log(
        (
            "🧾 최종 관찰 요약"
            + (
                f": '{normalized_keyword}'"
                if normalized_keyword
                else ""
            )
        )
    )

    _separator()

    _log(
        "🔑 상품명 키워드"
    )

    _log(
        "   └ 빈도우위"
    )

    _log_wrapped_items(
        _format_keyword_items(
            analysis.get(
                "high_frequency_keywords"
            )
        ),
        items_per_line=(
            SUMMARY_KEYWORDS_PER_LINE
        ),
        indent="      ",
    )

    _log(
        "   └ 빈도하위"
    )

    _log_wrapped_items(
        _format_keyword_items(
            analysis.get(
                "low_frequency_keywords"
            )
        ),
        items_per_line=(
            SUMMARY_KEYWORDS_PER_LINE
        ),
        indent="      ",
    )

    _separator()

    _log(
        (
            "📎 주요 상품명 참고정보 "
            f"— 출현율 {reference_min_ratio * 100:.0f}% 이상"
        )
    )

    reference_sections = (
        _build_reference_summary(
            analysis=analysis,
            minimum_ratio=(
                reference_min_ratio
            ),
        )
    )

    if not reference_sections:
        _log(
            (
                "   └ 기준 이상으로 반복된 "
                "참고정보 없음"
            )
        )

    for icon, label, items in (
        reference_sections
    ):
        _log(
            f"   └ {icon} {label}"
        )

        _log_wrapped_items(
            items,
            items_per_line=(
                SUMMARY_ITEMS_PER_LINE
            ),
            indent="      ",
        )

    unclassified_summary = (
        _build_unclassified_summary(
            analysis=analysis,
            minimum_ratio=(
                SUMMARY_UNCLASSIFIED_MIN_RATIO
            ),
        )
    )

    if unclassified_summary:
        _log(
            (
                "   └ 🧪 미분류 후보 "
                f"— 출현율 "
                f"{SUMMARY_UNCLASSIFIED_MIN_RATIO * 100:.0f}% 이상"
            ),
            level="WARNING",
        )

        _log_wrapped_items(
            unclassified_summary,
            items_per_line=(
                SUMMARY_ITEMS_PER_LINE
            ),
            indent="      ",
        )

    _separator()

    _log(
        "🏷️ 제거된 브랜드"
    )

    _log_wrapped_items(
        _format_removed_brands(
            analysis
        ),
        items_per_line=(
            SUMMARY_KEYWORDS_PER_LINE
        ),
        indent="   └ ",
    )

    _separator()

    concentration = (
        _get_category_concentration(
            analysis
        )
    )

    top_category = str(
        concentration.get(
            "top_category",
            "",
        )
    ).strip()

    top_count = _safe_int(
        concentration.get(
            "top_count",
            0,
        )
    )

    top_ratio = _safe_float(
        concentration.get(
            "top_ratio",
            0.0,
        )
    )

    second_category = str(
        concentration.get(
            "second_category",
            "",
        )
    ).strip()

    second_count = _safe_int(
        concentration.get(
            "second_count",
            0,
        )
    )

    second_ratio = _safe_float(
        concentration.get(
            "second_ratio",
            0.0,
        )
    )

    gap_ratio = _safe_float(
        concentration.get(
            "gap_ratio",
            0.0,
        )
    )

    label = str(
        concentration.get(
            "label",
            "자료 없음",
        )
    ).strip() or "자료 없음"

    description = str(
        concentration.get(
            "description",
            "",
        )
    ).strip()

    _log(
        "📚 카테고리 요약"
    )

    if top_category:
        _log(
            (
                "   └ 1위: "
                f"{top_category}"
            )
        )

        _log(
            (
                "      └ 빈도: "
                f"{top_count}/{sample_count}, "
                f"비율: {top_ratio * 100:.1f}%"
            )
        )

    else:
        _log(
            "   └ 1위: 카테고리 자료 없음"
        )

    if second_category:
        _log(
            (
                "   └ 2위: "
                f"{second_category}"
            )
        )

        _log(
            (
                "      └ 빈도: "
                f"{second_count}/{sample_count}, "
                f"비율: {second_ratio * 100:.1f}%"
            )
        )

    else:
        _log(
            "   └ 2위: 없음"
        )

    _separator()

    _log(
        "🧭 최종 해석"
    )

    for message in (
        _build_keyword_interpretation_messages(
            analysis=analysis,
            query_validation=(
                _safe_dict(
                    query_validation
                )
            ),
        )
    ):
        _log(
            f"   └ {message}"
        )

    _log(
        (
            "   └ 카테고리 1·2위 격차: "
            f"{gap_ratio * 100:.1f}%p"
        )
    )

    _log(
        (
            "   └ 카테고리 집중도 판정: "
            f"{label}"
        )
    )

    if description:
        _log(
            (
                "   └ "
                f"{description}"
            )
        )

    _separator(
        char="=",
    )
