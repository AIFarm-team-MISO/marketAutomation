from __future__ import annotations

import re
from typing import Any


# 완성된 한글 음절: 가~힣
COMPLETE_HANGUL_PATTERN = re.compile(r"[가-힣]")

# 단독 한글 자음·모음
HANGUL_JAMO_PATTERN = re.compile(r"[ㄱ-ㅎㅏ-ㅣ]")

LATIN_PATTERN = re.compile(r"[A-Za-z]")
DIGIT_PATTERN = re.compile(r"[0-9]")

# 한글 완성형, 영문, 숫자 중 하나라도 있는지 확인
SEARCHABLE_CHARACTER_PATTERN = re.compile(
    r"[가-힣A-Za-z0-9]"
)

MATCH_TOKEN_PATTERN = re.compile(
    r"[가-힣A-Za-z0-9]+"
)

QUERY_VALIDATOR_VERSION = "0.2.0"



def split_keyword_tokens(
    keyword: str,
) -> list[str]:
    """
    검색어를 비교용 토큰으로 분리한다.

    예:
        "박스테이프 대용량"
        → ["박스테이프", "대용량"]

        "직자/컷팅자"
        → ["직자", "컷팅자"]
    """
    normalized_keyword = normalize_spaces(
        keyword
    )

    return [
        token.lower()
        for token in MATCH_TOKEN_PATTERN.findall(
            normalized_keyword
        )
        if token
    ]

def extract_match_tokens(
    text: str,
) -> set[str]:
    """
    상품명에서 비교 가능한 독립 토큰을 추출한다.

    한글뿐 아니라 영문과 숫자도 유지한다.
    """
    return {
        token.lower()
        for token in MATCH_TOKEN_PATTERN.findall(
            str(text)
        )
        if token
    }


def normalize_spaces(text: str) -> str:
    """
    앞뒤 공백을 제거하고 연속 공백을 하나로 줄인다.
    """
    return " ".join(str(text).strip().split())


def normalize_for_match(text: str) -> str:
    """
    검색어 포함 여부 비교용으로 문자열을 정리한다.

    공백과 특수문자는 제거하고
    한글·영문·숫자만 유지한다.

    예:
        "배수구 덮개"
        → "배수구덮개"

        "직자/컷팅자"
        → "직자컷팅자"
    """
    normalized_text = re.sub(
        r"[^가-힣A-Za-z0-9]",
        "",
        str(text),
    )

    return normalized_text.lower()


def validate_keyword_format(
    keyword: str,
) -> dict[str, Any]:
    """
    API 호출 전 검색어 형식을 검사한다.

    명확히 잘못된 입력은 can_search=False로 반환한다.

    영문 상품명과 모델명 검색도 가능해야 하므로
    한글이 없더라도 영문 또는 숫자가 있으면 허용한다.
    """
    normalized_keyword = normalize_spaces(keyword)

    has_complete_hangul = bool(
        COMPLETE_HANGUL_PATTERN.search(
            normalized_keyword
        )
    )

    has_hangul_jamo = bool(
        HANGUL_JAMO_PATTERN.search(
            normalized_keyword
        )
    )

    has_latin = bool(
        LATIN_PATTERN.search(
            normalized_keyword
        )
    )

    has_digit = bool(
        DIGIT_PATTERN.search(
            normalized_keyword
        )
    )

    has_searchable_character = bool(
        SEARCHABLE_CHARACTER_PATTERN.search(
            normalized_keyword
        )
    )

    messages: list[str] = []
    status = "valid"
    can_search = True

    if not normalized_keyword:
        status = "invalid"
        can_search = False
        messages.append(
            "검색어가 비어 있습니다."
        )

    elif (
        has_hangul_jamo
        and not has_complete_hangul
        and not has_latin
        and not has_digit
    ):
        status = "invalid"
        can_search = False
        messages.append(
            "완성된 한글 음절이 없고 "
            "자음·모음만 입력되었습니다."
        )

    elif not has_searchable_character:
        status = "invalid"
        can_search = False
        messages.append(
            "검색 가능한 한글·영문·숫자가 없습니다."
        )

    elif has_hangul_jamo:
        # 완성형 한글과 자모가 섞인 경우
        # 오타일 수 있으므로 API 호출은 허용하되 경고
        status = "warning"
        messages.append(
            "완성된 한글과 단독 자음·모음이 "
            "함께 포함되어 있습니다."
        )
        messages.append(
            "한글 오타 여부를 확인해 주세요."
        )

    return {
        "validation_stage": "input_format",
        "status": status,
        "can_search": can_search,
        "normalized_keyword": normalized_keyword,
        "messages": messages,
        "checks": {
            "has_complete_hangul": (
                has_complete_hangul
            ),
            "has_hangul_jamo": has_hangul_jamo,
            "has_latin": has_latin,
            "has_digit": has_digit,
        },
    }


def evaluate_search_result(
    keyword: str,
    samples: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    API 호출 후 상위상품과 검색어의 관련성을 검사한다.

    검사 방식:
    1. 검색어 전체 문구가 연속된 형태로 포함됐는지
    2. 검색어를 구성하는 모든 토큰이 상품명에 포함됐는지
    3. 검색어 토큰이 각각 독립된 단어로 포함됐는지
    """
    format_validation = validate_keyword_format(
        keyword
    )

    normalized_keyword = format_validation[
        "normalized_keyword"
    ]

    sample_count = len(samples)

    normalized_match_keyword = normalize_for_match(
        normalized_keyword
    )

    keyword_tokens = split_keyword_tokens(
        normalized_keyword
    )

    phrase_match_count = 0
    all_token_match_count = 0
    exact_token_match_count = 0

    for sample in samples:
        original_title = str(
            sample.get("original_title", "")
        )

        cleaned_title = str(
            sample.get("cleaned_title", "")
        )

        frequency_title = str(
            sample.get("frequency_title", "")
        )

        candidate_titles = (
            original_title,
            cleaned_title,
            frequency_title,
        )

        compact_titles = [
            normalize_for_match(title)
            for title in candidate_titles
        ]

        # -------------------------------------------------
        # 1. 전체 검색문구가 순서대로 연속 포함됐는지
        #
        # 박스테이프 대용량
        # → 박스테이프대용량
        # -------------------------------------------------
        phrase_matched = any(
            normalized_match_keyword
            and normalized_match_keyword
            in compact_title
            for compact_title in compact_titles
        )

        if phrase_matched:
            phrase_match_count += 1

        # -------------------------------------------------
        # 2. 검색어의 모든 토큰이 상품명 안에 있는지
        #
        # 순서가 떨어져 있어도 인정:
        # "박스테이프 투명 경포장 대용량"
        # -------------------------------------------------
        all_tokens_matched = bool(
            keyword_tokens
        ) and all(
            any(
                keyword_token in compact_title
                for compact_title in compact_titles
            )
            for keyword_token in keyword_tokens
        )

        if all_tokens_matched:
            all_token_match_count += 1

        # -------------------------------------------------
        # 3. 모든 검색어 토큰이 독립 단어로 존재하는지
        # -------------------------------------------------
        title_tokens: set[str] = set()

        for title in candidate_titles:
            title_tokens.update(
                extract_match_tokens(title)
            )

        exact_tokens_matched = bool(
            keyword_tokens
        ) and all(
            keyword_token in title_tokens
            for keyword_token in keyword_tokens
        )

        if exact_tokens_matched:
            exact_token_match_count += 1

    phrase_match_ratio = (
        phrase_match_count / sample_count
        if sample_count > 0
        else 0.0
    )

    all_token_match_ratio = (
        all_token_match_count / sample_count
        if sample_count > 0
        else 0.0
    )

    exact_token_match_ratio = (
        exact_token_match_count / sample_count
        if sample_count > 0
        else 0.0
    )

    messages = list(
        format_validation.get("messages", [])
    )

    status = format_validation["status"]

    if not format_validation["can_search"]:
        status = "invalid"

    elif sample_count == 0:
        status = "no_results"

        messages.append(
            "네이버 쇼핑 검색결과가 없습니다."
        )

    elif sample_count < 5:
        status = "warning"

        messages.append(
            f"검색결과가 {sample_count}개뿐이므로 "
            "판단 표본이 부족합니다."
        )

    elif all_token_match_count == 0:
        status = "warning"

        messages.append(
            "상위상품명에 검색어를 구성하는 "
            "모든 단어가 함께 등장하지 않습니다."
        )

        messages.append(
            "오타이거나 검색 관련성이 낮은 "
            "키워드일 수 있습니다."
        )

    elif all_token_match_ratio < 0.10:
        status = "warning"

        messages.append(
            "모든 검색어 토큰이 포함된 상품의 "
            "비율이 10% 미만입니다."
        )

    elif all_token_match_ratio < 0.25:
        status = "review"

        messages.append(
            "모든 검색어 토큰이 포함된 상품의 "
            "비율이 25% 미만입니다."
        )

        messages.append(
            "검색결과와 카테고리를 함께 "
            "확인하는 것이 좋습니다."
        )

    elif status == "valid":
        status = "valid"

    return {
        "validator_version": (
            QUERY_VALIDATOR_VERSION
        ),
        "validation_stage": "search_result",
        "status": status,
        "can_search": format_validation[
            "can_search"
        ],
        "normalized_keyword": normalized_keyword,

        "keyword_tokens": keyword_tokens,
        "keyword_token_count": len(
            keyword_tokens
        ),

        "sample_count": sample_count,

        # 전체 검색문구가 연속으로 포함된 상품
        "phrase_match_count": (
            phrase_match_count
        ),
        "phrase_match_ratio": (
            phrase_match_ratio
        ),

        # 검색어를 구성하는 모든 토큰이 포함된 상품
        "all_token_match_count": (
            all_token_match_count
        ),
        "all_token_match_ratio": (
            all_token_match_ratio
        ),

        # 모든 검색어 토큰이 독립 단어로 포함된 상품
        "exact_token_match_count": (
            exact_token_match_count
        ),
        "exact_token_match_ratio": (
            exact_token_match_ratio
        ),

        # 기존 코드와의 호환을 위한 필드
        "compact_match_count": (
            phrase_match_count
        ),
        "match_ratio": (
            all_token_match_ratio
        ),

        "messages": messages,
        "checks": format_validation[
            "checks"
        ],
    }