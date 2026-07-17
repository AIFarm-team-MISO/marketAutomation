from __future__ import annotations

from .reference_token_analyzer import (
    extract_reference_tokens,
    remove_reference_expressions,
)

import html
import re
from typing import Any
import unicodedata



# 영문 브랜드가 상품명에서 한글로 표시되는 대표 사례
BRAND_MAPPING = {
    "3M": "쓰리엠",
    "TESA": "테사",
    "SCOTCH": "스카치",
    "MONSTER": "몬스터",
    "UHU": "유후",
}
# 일반 개행·탭 외에 상품명에 섞일 수 있는
# 보이지 않는 유니코드 문자
INVISIBLE_CHARACTERS = {
    "\u200b",  # zero width space
    "\u200c",  # zero width non-joiner
    "\u200d",  # zero width joiner
    "\u2060",  # word joiner
    "\ufeff",  # byte order mark / zero width no-break space
}


def _safe_optional_int(
    value: Any,
) -> int | None:
    """
    API 숫자 값을 정수로 변환한다.

    0은 정상값으로 보존하고,
    변환할 수 없는 값만 None으로 처리한다.
    """
    if value is None:
        return None

    normalized_value = str(
        value
    ).strip()

    if not normalized_value:
        return None

    try:
        return int(normalized_value)

    except (TypeError, ValueError):
        return None


def build_source_item(
    item: dict[str, Any],
) -> dict[str, Any]:
    """
    API 원본 상품정보 중 나중에 복원하기 어려운
    필드만 저장용 구조로 변환한다.

    콘솔 출력에는 사용하지 않는다.
    """
    return {
        "mall_name": normalize_text_whitespace(
            item.get(
                "mallName",
                "",
            )
        ),

        "lowest_price": _safe_optional_int(
            item.get("lprice")
        ),

        "highest_price": _safe_optional_int(
            item.get("hprice")
        ),

        # 상품 ID는 계산할 값이 아니므로
        # 자릿수 보존을 위해 문자열로 저장
        "product_id": normalize_text_whitespace(
            item.get(
                "productId",
                "",
            )
        ),

        "product_type": _safe_optional_int(
            item.get("productType")
        ),

        "link": normalize_text_whitespace(
            item.get(
                "link",
                "",
            )
        ),

        "image_url": normalize_text_whitespace(
            item.get(
                "image",
                "",
            )
        ),

        "maker": normalize_text_whitespace(
            item.get(
                "maker",
                "",
            )
        ),
    }

def normalize_text_whitespace(text: str) -> str:
    """
    문자열 안의 줄바꿈, 탭, 제어문자와
    보이지 않는 유니코드 문자를 일반 공백으로 바꾼다.

    처리 대상 예:
    - \\n
    - \\r
    - \\t
    - 유니코드 줄 구분자
    - 유니코드 문단 구분자
    - zero width space

    마지막에는 연속된 공백을 하나로 정리한다.
    """
    if text is None:
        return ""

    normalized_text = unicodedata.normalize(
        "NFKC",
        str(text),
    )

    cleaned_characters: list[str] = []

    for character in normalized_text:
        category = unicodedata.category(character)

        if (
            character in INVISIBLE_CHARACTERS
            or category in {
                "Cc",  # 제어문자: 개행, 탭, 캐리지리턴 등
                "Cf",  # 보이지 않는 형식문자
                "Zl",  # 줄 구분자
                "Zp",  # 문단 구분자
            }
        ):
            cleaned_characters.append(" ")
        else:
            cleaned_characters.append(character)

    joined_text = "".join(cleaned_characters)

    # split()은 여러 종류의 공백을 모두 인식하므로
    # 단순 정규표현식보다 숨은 공백 처리에 안정적이다.
    return " ".join(joined_text.split())


# g2pk가 없어도 프로그램 전체가 중단되지 않도록 선택적으로 사용
try:
    from g2pk import G2p

    _g2p = G2p()
except ImportError:
    _g2p = None



def clean_html(text: str) -> str:
    """
    HTML 태그와 HTML 엔티티를 제거하고,
    줄바꿈·탭·보이지 않는 문자와 공백을 정리한다.

    예:
        "<b>알루미늄</b>\\n직자"
        → "알루미늄 직자"
    """
    if not text:
        return ""

    decoded_text = html.unescape(
        str(text)
    )

    without_html = re.sub(
        r"<[^>]*>",
        "",
        decoded_text,
    )

    return normalize_text_whitespace(
        without_html
    )


def normalize_spaces(text: str) -> str:
    """
    개행·탭·숨은 제어문자를 제거하고
    연속 공백을 하나로 정리한다.
    """
    return normalize_text_whitespace(text)



def remove_brand_from_title(
    title: str,
    brand: str,
) -> tuple[str, list[str]]:
    """
    상품명에서 네이버 API가 제공한 브랜드명을 제거한다.

    제거 대상:
    1. API의 브랜드명 원문
    2. BRAND_MAPPING에 등록된 한글 브랜드명
    3. g2pk로 변환한 한글 발음 브랜드명

    Returns
    -------
    tuple[str, list[str]]
        브랜드 제거 후 상품명, 실제 제거된 브랜드명 목록
    """
    cleaned_title = clean_html(title)
    cleaned_brand = clean_html(brand)

    if not cleaned_brand:
        return cleaned_title, []

    brand_candidates: list[str] = [cleaned_brand]

    brand_upper = cleaned_brand.upper()

    mapped_brand = BRAND_MAPPING.get(brand_upper)
    if mapped_brand:
        brand_candidates.append(mapped_brand)

    if _g2p is not None:
        try:
            converted_brand = normalize_spaces(_g2p(cleaned_brand))

            if converted_brand:
                brand_candidates.append(converted_brand)
        except Exception:
            # 한글 발음 변환 실패는 브랜드 제거 전체 실패로 보지 않는다.
            pass

    # 같은 후보가 여러 번 생성되는 경우 제거한다.
    unique_candidates = list(dict.fromkeys(brand_candidates))

    # 긴 문자열부터 제거해야 일부 문자열만 먼저 지워지는 문제를 줄일 수 있다.
    unique_candidates.sort(key=len, reverse=True)

    removed_brands: list[str] = []

    for brand_candidate in unique_candidates:
        if not brand_candidate:
            continue

        # 영문 브랜드도 대소문자 구분 없이 제거
        pattern = re.compile(
            re.escape(brand_candidate),
            flags=re.IGNORECASE,
        )

        cleaned_title, removed_count = pattern.subn(
            " ",
            cleaned_title,
        )

        if removed_count > 0:
            removed_brands.append(brand_candidate)

    cleaned_title = normalize_spaces(cleaned_title)

    return cleaned_title, removed_brands


def normalize_title_for_frequency(
    title: str,
) -> str:
    """
    의미 키워드 빈도분석에 사용할 상품명으로 정제한다.

    수량·규격·영문·모델 표현은 먼저 제거하며,
    해당 값들은 별도의 참고정보 분포에서 사용한다.
    """
    if not title:
        return ""

    cleaned_title = clean_html(title)

    # 수량·규격·영문·모델 표현을 제거한다.
    semantic_title = remove_reference_expressions(
        cleaned_title
    )

    # 구분자는 삭제하지 않고 공백으로 변경
    semantic_title = re.sub(
        r"[/|,·+&_=()\[\]{}:;!?'\"<>\\-]+",
        " ",
        semantic_title,
    )

    # 의미 키워드는 한글과 공백만 유지
    semantic_title = re.sub(
        r"[^가-힣\s]",
        " ",
        semantic_title,
    )

    return normalize_spaces(
        semantic_title
    )


def tokenize_title(title: str) -> list[str]:
    """
    정제된 상품명을 공백 기준 토큰 리스트로 변환한다.
    """
    normalized_title = normalize_title_for_frequency(title)

    if not normalized_title:
        return []

    return normalized_title.split()


def build_category_path(item: dict[str, Any]) -> str:
    """
    네이버 API의 category1~category4를 전체 경로로 만든다.
    """

    category_names = [
    normalize_text_whitespace(
        item.get("category1", "")
    ),
    normalize_text_whitespace(
        item.get("category2", "")
    ),
    normalize_text_whitespace(
        item.get("category3", "")
    ),
    normalize_text_whitespace(
        item.get("category4", "")
    ),
]

    return " > ".join(
        category
        for category in category_names
        if category
    )


def build_sample(
    item: dict[str, Any],
    rank: int,
) -> dict[str, Any]:
    """
    네이버 쇼핑 API 상품 한 개를 관찰용 상품 데이터로 변환한다.

    반환 예:
    {
        "rank": 1,
        "original_title": "알루미늄 직자",
        "brand": "",
        "cleaned_title": "알루미늄 직자",
        "frequency_title": "알루미늄 직자",
        "tokens": ["알루미늄", "직자"],
        "category_path": "...",
        "removed_brands": []
    }
    """
    original_title = clean_html(
        str(item.get("title", ""))
    )

    brand = clean_html(
        str(item.get("brand", ""))
    )

    cleaned_title, removed_brands = remove_brand_from_title(
        title=original_title,
        brand=brand,
    )
    
    reference_tokens = extract_reference_tokens(
    cleaned_title
    )

    frequency_title = normalize_title_for_frequency(
        cleaned_title
    )

    tokens = tokenize_title(
        cleaned_title
    )

    source_item = build_source_item(
        item
    )

    category_path = build_category_path(item)


    return {
        "rank": rank,
        "original_title": original_title,
        "brand": brand,
        "cleaned_title": cleaned_title,
        "frequency_title": frequency_title,
        "tokens": tokens,
        "reference_tokens": reference_tokens,
        "category_path": category_path,
        "removed_brands": removed_brands,

        # 콘솔에는 출력하지 않고
        # JSONL과 최신 JSON에만 저장
        "source_item": source_item,

    }


def build_samples(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    네이버 쇼핑 API items 전체를 관찰용 상품 데이터로 변환한다.
    """
    samples: list[dict[str, Any]] = []

    for rank, item in enumerate(items, start=1):
        sample = build_sample(
            item=item,
            rank=rank,
        )
        samples.append(sample)

    return samples