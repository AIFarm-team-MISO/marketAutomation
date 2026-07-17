from __future__ import annotations

from typing import Any


# =========================================================
# 카테고리 집중도 판정 기준
# =========================================================

CONCENTRATED_MIN_RATIO = 0.80
PARTIAL_CONCENTRATION_MIN_RATIO = 0.60
MIXED_MIN_RATIO = 0.40


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


def _build_category_items(
    analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    category_counts를 우선 사용해 전체 카테고리를 정렬한다.

    과거 자료처럼 category_counts가 없으면
    top_categories를 대신 사용한다.
    """
    sample_count = _safe_int(
        analysis.get(
            "sample_count",
            0,
        )
    )

    category_counts = _safe_dict(
        analysis.get(
            "category_counts"
        )
    )

    category_items: list[dict[str, Any]] = []

    for category_path, raw_count in (
        category_counts.items()
    ):
        normalized_path = str(
            category_path
        ).strip()

        count = _safe_int(
            raw_count,
            0,
        )

        if not normalized_path or count < 1:
            continue

        ratio = (
            count / sample_count
            if sample_count > 0
            else 0.0
        )

        category_items.append(
            {
                "category_path": normalized_path,
                "count": count,
                "ratio": ratio,
            }
        )

    if category_items:
        category_items.sort(
            key=lambda item: (
                -_safe_int(
                    item.get("count"),
                    0,
                ),
                str(
                    item.get(
                        "category_path",
                        "",
                    )
                ),
            )
        )

        return category_items

    for item in _safe_list(
        analysis.get(
            "top_categories"
        )
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

        if not category_path or count < 1:
            continue

        ratio = _safe_float(
            item.get(
                "ratio",
                (
                    count / sample_count
                    if sample_count > 0
                    else 0.0
                ),
            )
        )

        category_items.append(
            {
                "category_path": category_path,
                "count": count,
                "ratio": ratio,
            }
        )

    category_items.sort(
        key=lambda item: (
            -_safe_int(
                item.get("count"),
                0,
            ),
            str(
                item.get(
                    "category_path",
                    "",
                )
            ),
        )
    )

    return category_items


def _judge_concentration(
    top_ratio: float,
    category_count: int,
) -> tuple[str, str, str]:
    """
    대표 카테고리 비율을 기준으로 집중도를 판정한다.

    이 값은 자동 카테고리 결정이 아니라
    검색결과의 혼합 정도를 알려주는 보조지표다.
    """
    if category_count < 1:
        return (
            "no_data",
            "자료 없음",
            "카테고리 자료가 없어 집중도를 판정할 수 없습니다.",
        )

    if top_ratio >= CONCENTRATED_MIN_RATIO:
        return (
            "concentrated",
            "집중",
            "검색결과가 대표 카테고리에 뚜렷하게 집중되어 있습니다.",
        )

    if (
        top_ratio
        >= PARTIAL_CONCENTRATION_MIN_RATIO
    ):
        return (
            "partial_concentration",
            "부분 집중",
            "대표 카테고리 중심이지만 다른 카테고리 상품도 함께 포함됩니다.",
        )

    if top_ratio >= MIXED_MIN_RATIO:
        return (
            "mixed",
            "혼합",
            "두 개 이상의 카테고리가 함께 노출되는 혼합 검색결과입니다.",
        )

    return (
        "dispersed",
        "분산",
        "검색결과가 여러 카테고리로 분산되어 검색어 세분화 검토가 필요합니다.",
    )


def analyze_category_concentration(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    """
    기존 카테고리 집계를 이용해 집중도 결과를 만든다.

    저장 값:
    - 1위·2위 전체 카테고리 경로
    - 각 카테고리의 건수와 비율
    - 1·2위 비율 격차
    - 상위 2개 합계 비율
    - 카테고리 종류 수
    - 집중도 판정과 설명
    """
    normalized_analysis = _safe_dict(
        analysis
    )

    sample_count = _safe_int(
        normalized_analysis.get(
            "sample_count",
            0,
        )
    )

    category_items = _build_category_items(
        normalized_analysis
    )

    top_item = (
        category_items[0]
        if category_items
        else {}
    )

    second_item = (
        category_items[1]
        if len(category_items) > 1
        else {}
    )

    top_category = str(
        top_item.get(
            "category_path",
            "",
        )
    ).strip()

    top_count = _safe_int(
        top_item.get(
            "count",
            0,
        )
    )

    top_ratio = _safe_float(
        top_item.get(
            "ratio",
            (
                top_count / sample_count
                if sample_count > 0
                else 0.0
            ),
        )
    )

    second_category = str(
        second_item.get(
            "category_path",
            "",
        )
    ).strip()

    second_count = _safe_int(
        second_item.get(
            "count",
            0,
        )
    )

    second_ratio = _safe_float(
        second_item.get(
            "ratio",
            (
                second_count / sample_count
                if sample_count > 0
                else 0.0
            ),
        )
    )

    gap_ratio = max(
        0.0,
        top_ratio - second_ratio,
    )

    top_two_ratio = min(
        1.0,
        max(
            0.0,
            top_ratio + second_ratio,
        ),
    )

    categorized_count = sum(
        _safe_int(
            item.get(
                "count",
                0,
            )
        )
        for item in category_items
    )

    status, label, description = (
        _judge_concentration(
            top_ratio=top_ratio,
            category_count=len(
                category_items
            ),
        )
    )

    return {
        "sample_count": sample_count,
        "categorized_count": (
            categorized_count
        ),
        "category_count": len(
            category_items
        ),
        "top_category": top_category,
        "top_count": top_count,
        "top_ratio": top_ratio,
        "second_category": second_category,
        "second_count": second_count,
        "second_ratio": second_ratio,
        "gap_ratio": gap_ratio,
        "top_two_ratio": top_two_ratio,
        "status": status,
        "label": label,
        "description": description,
        "thresholds": {
            "concentrated_min_ratio": (
                CONCENTRATED_MIN_RATIO
            ),
            "partial_concentration_min_ratio": (
                PARTIAL_CONCENTRATION_MIN_RATIO
            ),
            "mixed_min_ratio": (
                MIXED_MIN_RATIO
            ),
        },
    }
