from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from .observation_processor import (
    normalize_title_for_frequency,
)

from .reference_token_analyzer import (
    build_reference_distribution,
)


# 숫자가 제거된 뒤 단독으로 남는 대표 단위·잡음
#
# 현재는 지나치게 많은 단어를 제외하지 않고,
# 명확한 잡음인 "개"만 기본 제외한다.
DEFAULT_EXCLUDED_TOKENS = {
    "개",
}

def build_search_keyword_distribution(
    excluded_counter: Counter[str],
    main_keyword: str,
    sample_count: int,
) -> list[dict[str, Any]]:
    """
    사용자가 입력한 검색키워드 구성 토큰의
    상품별 분포를 만든다.

    excluded_counter에는 기본 제외어도 들어갈 수 있으므로,
    실제 메인키워드 구성 토큰만 다시 선별한다.
    """
    normalized_main_keyword = (
        normalize_title_for_frequency(
            main_keyword
        )
    )

    main_keyword_tokens = list(
        dict.fromkeys(
            token
            for token in normalized_main_keyword.split()
            if token
        )
    )

    return [
        {
            "keyword": keyword,
            "product_count": (
                excluded_counter.get(
                    keyword,
                    0,
                )
            ),
            "ratio": (
                excluded_counter.get(
                    keyword,
                    0,
                ) / sample_count
                if sample_count > 0
                else 0.0
            ),
        }
        for keyword in main_keyword_tokens
    ]

def _counter_to_items(
    counter: Counter[str],
) -> list[dict[str, Any]]:
    """
    Counter를 JSON 저장과 출력에 편한 리스트로 변환한다.

    예:
        Counter({"스틸자": 7, "쇠자": 4})

        →

        [
            {"keyword": "스틸자", "count": 7},
            {"keyword": "쇠자", "count": 4},
        ]
    """
    return [
        {
            "keyword": keyword,
            "count": count,
        }
        for keyword, count in counter.most_common()
    ]


def _normalize_excluded_tokens(
    main_keyword: str,
    excluded_tokens: Iterable[str] | None = None,
) -> set[str]:
    """
    빈도 분석에서 제외할 토큰 집합을 만든다.

    제외 대상:
    - 메인키워드를 구성하는 단어
    - DEFAULT_EXCLUDED_TOKENS
    - 호출자가 별도로 전달한 제외어
    """
    normalized_main_keyword = normalize_title_for_frequency(
        main_keyword
    )

    main_keyword_tokens = set(
        normalized_main_keyword.split()
    )

    result = set(DEFAULT_EXCLUDED_TOKENS)
    result.update(main_keyword_tokens)

    if excluded_tokens:
        result.update(
            str(token).strip()
            for token in excluded_tokens
            if str(token).strip()
        )

    return result


def _get_sample_tokens(
    sample: dict[str, Any],
) -> list[str]:
    """
    상품 한 건의 토큰을 문자열 리스트로 정리한다.
    """
    tokens = sample.get("tokens", [])

    if not isinstance(tokens, list):
        return []

    return [
        str(token).strip()
        for token in tokens
        if str(token).strip()
    ]


def count_product_keywords(
    samples: list[dict[str, Any]],
) -> Counter[str]:
    """
    각 키워드가 포함된 상품 수를 계산한다.

    같은 상품명 안에서 동일한 키워드가 여러 번 등장해도
    상품 한 건당 한 번만 계산한다.

    예:
        ["투명", "박스테이프", "투명"]

        → 투명 1회
        → 박스테이프 1회
    """
    keyword_counter: Counter[str] = Counter()

    for sample in samples:
        tokens = _get_sample_tokens(sample)

        # dict.fromkeys()로 입력순서를 유지하며 중복 제거
        unique_tokens = list(
            dict.fromkeys(tokens)
        )

        keyword_counter.update(unique_tokens)

    return keyword_counter



def count_all_keywords(
    samples: list[dict[str, Any]],
) -> Counter[str]:
    """
    전체 상품명에서 토큰이 등장한 총횟수를 계산한다.

    같은 상품 안에 동일 토큰이 두 번 있으면
    두 번 계산한다.

    원본 관찰용 통계로만 사용한다.
    """
    keyword_counter: Counter[str] = Counter()

    for sample in samples:
        keyword_counter.update(
            _get_sample_tokens(sample)
        )

    return keyword_counter

def filter_keyword_counter(
    raw_counter: Counter[str],
    main_keyword: str,
    excluded_tokens: Iterable[str] | None = None,
) -> tuple[Counter[str], Counter[str]]:
    """
    전체 키워드 빈도에서 메인키워드와 잡음을 분리한다.

    Returns
    -------
    tuple
        분석에 사용할 Counter,
        분석에서 제외된 Counter
    """
    exclusion_set = _normalize_excluded_tokens(
        main_keyword=main_keyword,
        excluded_tokens=excluded_tokens,
    )

    filtered_counter: Counter[str] = Counter()
    excluded_counter: Counter[str] = Counter()

    for keyword, count in raw_counter.items():
        if keyword in exclusion_set:
            excluded_counter[keyword] = count
        else:
            filtered_counter[keyword] = count

    return filtered_counter, excluded_counter


def count_categories(
    samples: list[dict[str, Any]],
) -> Counter[str]:
    """
    상품별 전체 카테고리 경로의 빈도를 계산한다.
    """
    category_counter: Counter[str] = Counter()

    for sample in samples:
        category_path = str(
            sample.get("category_path", "")
        ).strip()

        if category_path:
            category_counter[category_path] += 1

    return category_counter


def build_top_categories(
    category_counter: Counter[str],
    sample_count: int,
    top_n: int = 3,
) -> list[dict[str, Any]]:
    """
    상위 카테고리 목록과 전체 표본 대비 비율을 만든다.
    """
    top_categories: list[dict[str, Any]] = []

    for category_path, count in category_counter.most_common(
        top_n
    ):
        ratio = (
            count / sample_count
            if sample_count > 0
            else 0.0
        )

        top_categories.append(
            {
                "category_path": category_path,
                "count": count,
                "ratio": ratio,
            }
        )

    return top_categories


def count_removed_brands(
    samples: list[dict[str, Any]],
) -> Counter[str]:
    """
    상위상품 처리 과정에서 실제 제거된 브랜드 빈도를 계산한다.
    """
    brand_counter: Counter[str] = Counter()

    for sample in samples:
        removed_brands = sample.get(
            "removed_brands",
            [],
        )

        if not isinstance(removed_brands, list):
            continue

        for brand in removed_brands:
            normalized_brand = str(brand).strip()

            if normalized_brand:
                brand_counter[normalized_brand] += 1

    return brand_counter


def analyze_samples(
    samples: list[dict[str, Any]],
    main_keyword: str,
    high_frequency_count: int = 5,
    category_top_n: int = 3,
    excluded_tokens: Iterable[str] | None = None,
) -> dict[str, Any]:
    """
    관찰용 상품 데이터를 종합 분석한다.

    분석 결과:
    - 원본 전체 키워드 빈도
    - 메인키워드·잡음 제거 후 키워드 빈도
    - 빈도우위 키워드
    - 빈도하위 키워드
    - 분석 제외 키워드
    - 카테고리 빈도
    - 카테고리 TOP 3
    - 제거 브랜드 빈도
    """
    if high_frequency_count < 1:
        raise ValueError(
            "high_frequency_count는 1 이상이어야 합니다."
        )

    if category_top_n < 1:
        raise ValueError(
            "category_top_n은 1 이상이어야 합니다."
        )

    sample_count = len(samples)

    # 상품명 전체에서 실제 토큰이 나타난 총횟수
    raw_keyword_counter = count_all_keywords(
        samples
    )

    # 키워드가 포함된 상품 수
    product_keyword_counter = count_product_keywords(
        samples
    )

    # 빈도우위·하위 분석은 상품 포함 수를 기준으로 계산
    filtered_keyword_counter, excluded_counter = (
        filter_keyword_counter(
            raw_counter=product_keyword_counter,
            main_keyword=main_keyword,
            excluded_tokens=excluded_tokens,
        )
    )

    # 기존 프로그램과 동일하게 빈도 상위 N개를 우위로 분류
    sorted_filtered_items = (
        filtered_keyword_counter.most_common()
    )

    high_frequency_items = sorted_filtered_items[
        :high_frequency_count
    ]

    low_frequency_items = sorted_filtered_items[
        high_frequency_count:
    ]

    high_frequency_counter = Counter(
        dict(high_frequency_items)
    )

    low_frequency_counter = Counter(
        dict(low_frequency_items)
    )

    # 카테고리 분석
    category_counter = count_categories(samples)

    top_categories = build_top_categories(
        category_counter=category_counter,
        sample_count=sample_count,
        top_n=category_top_n,
    )

    # 제거 브랜드 분석
    removed_brand_counter = count_removed_brands(samples)


    search_keyword_distribution = (
        build_search_keyword_distribution(
            excluded_counter=excluded_counter,
            main_keyword=main_keyword,
            sample_count=sample_count,
        )
    )

    reference_token_distribution = (
        build_reference_distribution(
            samples=samples
        )
    )

    return {
        "sample_count": sample_count,
        "frequency_basis": "product_presence",

        "raw_keyword_counts": dict(
            raw_keyword_counter.most_common()
        ),

        "product_keyword_counts": dict(
            product_keyword_counter.most_common()
        ),

        "keyword_counts": dict(
            filtered_keyword_counter.most_common()
        ),

        "high_frequency_keywords": (
            _counter_to_items(
                high_frequency_counter
            )
        ),

        "low_frequency_keywords": (
            _counter_to_items(
                low_frequency_counter
            )
        ),

        # 기존 자료 호환을 위해 유지
        "excluded_keywords": (
            _counter_to_items(
                excluded_counter
            )
        ),

        # 새 출력에 사용할 값
        "search_keyword_distribution": (
            search_keyword_distribution
        ),

        "reference_token_distribution": (
            reference_token_distribution
        ),

        "category_counts": dict(
            category_counter.most_common()
        ),

        "top_categories": top_categories,

        "removed_brand_counts": dict(
            removed_brand_counter.most_common()
        ),
    }