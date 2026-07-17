from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Any


REFERENCE_CATEGORY_NAMES = {
    "quantity": "수량·구성",
    "measurement": "규격·치수",
    "english": "영문 표현",
    "model_code": "모델·상품코드",
}

REFERENCE_CATEGORY_ORDER = (
    "quantity",
    "measurement",
    "english",
    "model_code",
)


# 숫자:
# 50
# 4.8
# 1,000
NUMBER_PATTERN_TEXT = r"\d+(?:[.,]\d+)?"


# 긴 단위를 앞에 배치한다.
MEASUREMENT_UNIT_PATTERN_TEXT = (
    r"(?:"
    r"킬로미터|센티미터|밀리미터|"
    r"킬로그램|밀리그램|"
    r"밀리리터|"
    r"미터|그램|리터|"
    r"micron|inch|"
    r"wh|mm|cm|km|"
    r"µm|μm|um|nm|"
    r"kg|mg|ml|"
    r"cc|oz|mic|"
    r"in|m|g|l|t|v|w"
    r")"
)


MEASUREMENT_COMPONENT_TEXT = (
    rf"{NUMBER_PATTERN_TEXT}"
    rf"\s*"
    rf"{MEASUREMENT_UNIT_PATTERN_TEXT}"
)


# 복합규격을 먼저 검사한다.
#
# 48mmx80m
# 25mm X 10M
# 10cm*20cm
# 3cm × 5cm
MEASUREMENT_PATTERN = re.compile(
    rf"""
    (?<![A-Za-z0-9])
    (?:
        {MEASUREMENT_COMPONENT_TEXT}
        (?:
            \s*[xX×*]\s*
            {MEASUREMENT_COMPONENT_TEXT}
        )+
        |
        {MEASUREMENT_COMPONENT_TEXT}
    )
    (?![A-Za-z0-9])
    """,
    re.IGNORECASE | re.VERBOSE,
)


# 수량·포장단위
#
# 50개
# 50개입
# 4롤
# 2세트
# 1박스
# 3P
QUANTITY_PATTERN = re.compile(
    rf"""
    (?<![A-Za-z0-9])
    {NUMBER_PATTERN_TEXT}
    \s*
    (?:
        개입|
        케이스|
        묶음|
        세트|
        박스|
        켤레|
        롤|
        매|
        장|
        개|
        봉|
        쌍|
        병|
        캔|
        팩|
        포|
        갑|
        통|
        pcs|
        ea|
        p
    )
    (?![A-Za-z0-9가-힣])
    """,
    re.IGNORECASE | re.VERBOSE,
)


# 영문과 숫자가 섞인 모델명·상품코드
#
# L50
# STR-30
# 3M4421
# VHB-4910
MODEL_CODE_PATTERN = re.compile(
    r"""
    (?<![A-Za-z0-9])
    (?=[A-Za-z0-9-]*[A-Za-z])
    (?=[A-Za-z0-9-]*\d)
    [A-Za-z0-9]+
    (?:-[A-Za-z0-9]+)*
    (?![A-Za-z0-9])
    """,
    re.VERBOSE,
)


# 영문으로만 이루어진 표현
#
# OPP
# SINIL
# PVC
# VHB
ENGLISH_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])[A-Za-z]{2,}(?![A-Za-z0-9])"
)


# 3M은 길이 3m가 아니라
# 브랜드 또는 모델 표현일 가능성이 높으므로 예외 처리한다.
MODEL_CODE_EXCEPTIONS = {
    "3M",
}


KOREAN_MEASUREMENT_UNIT_MAPPING = (
    ("킬로미터", "km"),
    ("센티미터", "cm"),
    ("밀리미터", "mm"),
    ("킬로그램", "kg"),
    ("밀리그램", "mg"),
    ("밀리리터", "ml"),
    ("미터", "m"),
    ("그램", "g"),
    ("리터", "l"),
)


def normalize_source_text(text: str) -> str:
    """
    참고정보 추출 전에 문자열을 정리한다.
    """
    if text is None:
        return ""

    normalized_text = unicodedata.normalize(
        "NFKC",
        str(text),
    )

    normalized_text = (
        normalized_text
        .replace("\u200b", " ")
        .replace("\u200c", " ")
        .replace("\u200d", " ")
        .replace("\u2060", " ")
        .replace("\ufeff", " ")
    )

    return " ".join(normalized_text.split())


def normalize_measurement_token(token: str) -> str:
    """
    규격 표현을 통일한다.

    예:
        80M         → 80m
        48mm X 80M  → 48mmx80m
        65MIC       → 65mic
        100미터     → 100m
    """
    normalized_token = unicodedata.normalize(
        "NFKC",
        str(token),
    )

    normalized_token = (
        normalized_token
        .replace("×", "x")
        .replace("*", "x")
        .replace("X", "x")
        .replace("μ", "u")
        .replace("µ", "u")
    )

    normalized_token = re.sub(
        r"\s+",
        "",
        normalized_token,
    )

    normalized_token = normalized_token.replace(
        ",",
        "",
    )

    normalized_token = normalized_token.lower()

    for korean_unit, english_unit in (
        KOREAN_MEASUREMENT_UNIT_MAPPING
    ):
        normalized_token = normalized_token.replace(
            korean_unit,
            english_unit,
        )

    return normalized_token


def normalize_quantity_token(token: str) -> str:
    """
    수량·구성 표현을 통일한다.

    예:
        50 개  → 50개
        3p     → 3P
        2pcs   → 2PCS
    """
    normalized_token = unicodedata.normalize(
        "NFKC",
        str(token),
    )

    normalized_token = re.sub(
        r"\s+",
        "",
        normalized_token,
    )

    normalized_token = normalized_token.replace(
        ",",
        "",
    )

    match = re.fullmatch(
        rf"""
        ({NUMBER_PATTERN_TEXT})
        (
            개입|
            케이스|
            묶음|
            세트|
            박스|
            켤레|
            롤|
            매|
            장|
            개|
            봉|
            쌍|
            병|
            캔|
            팩|
            포|
            갑|
            통|
            pcs|
            ea|
            p
        )
        """,
        normalized_token,
        re.IGNORECASE | re.VERBOSE,
    )

    if not match:
        return normalized_token

    number = match.group(1).replace(",", "")
    unit = match.group(2)

    if unit.lower() in {"p", "pcs", "ea"}:
        unit = unit.upper()

    return f"{number}{unit}"


def normalize_english_token(token: str) -> str:
    return str(token).strip().upper()


def normalize_model_code_token(token: str) -> str:
    normalized_token = unicodedata.normalize(
        "NFKC",
        str(token),
    )

    normalized_token = re.sub(
        r"\s+",
        "",
        normalized_token,
    )

    return normalized_token.upper()


def mask_pattern_matches(
    text: str,
    pattern: re.Pattern[str],
) -> tuple[list[str], str]:
    """
    정규표현식에 맞는 값을 추출하고,
    해당 구간을 같은 길이의 공백으로 바꾼다.

    문자열 길이를 유지하므로 다음 패턴 검사에서도
    겹치는 값이 중복 추출되지 않는다.
    """
    matches: list[str] = []
    characters = list(text)

    for match in pattern.finditer(text):
        matches.append(match.group(0))

        start_index, end_index = match.span()

        for index in range(
            start_index,
            end_index,
        ):
            characters[index] = " "

    return matches, "".join(characters)


def scan_reference_tokens(
    text: str,
) -> tuple[dict[str, list[str]], str]:
    """
    문자열에서 상품명 참고정보를 분류하여 추출한다.

    우선순위:
    1. 규격·치수
    2. 수량·구성
    3. 모델·상품코드
    4. 영문 표현

    반환:
        분류된 참고정보,
        참고정보를 제거한 나머지 문자열
    """
    remaining_text = normalize_source_text(text)

    result: dict[str, list[str]] = {
        category: []
        for category in REFERENCE_CATEGORY_ORDER
    }

    # --------------------------------------------
    # 1. 규격·치수
    # --------------------------------------------
    measurement_matches, remaining_text = (
        mask_pattern_matches(
            remaining_text,
            MEASUREMENT_PATTERN,
        )
    )

    for raw_token in measurement_matches:
        compact_token = re.sub(
            r"\s+",
            "",
            raw_token,
        ).upper()

        if compact_token in MODEL_CODE_EXCEPTIONS:
            result["model_code"].append(
                normalize_model_code_token(
                    raw_token
                )
            )
        else:
            result["measurement"].append(
                normalize_measurement_token(
                    raw_token
                )
            )

    # --------------------------------------------
    # 2. 수량·구성
    # --------------------------------------------
    quantity_matches, remaining_text = (
        mask_pattern_matches(
            remaining_text,
            QUANTITY_PATTERN,
        )
    )

    for raw_token in quantity_matches:
        result["quantity"].append(
            normalize_quantity_token(raw_token)
        )

    # --------------------------------------------
    # 3. 모델·상품코드
    # --------------------------------------------
    model_matches, remaining_text = (
        mask_pattern_matches(
            remaining_text,
            MODEL_CODE_PATTERN,
        )
    )

    for raw_token in model_matches:
        result["model_code"].append(
            normalize_model_code_token(raw_token)
        )

    # --------------------------------------------
    # 4. 영문 표현
    # --------------------------------------------
    english_matches, remaining_text = (
        mask_pattern_matches(
            remaining_text,
            ENGLISH_PATTERN,
        )
    )

    for raw_token in english_matches:
        result["english"].append(
            normalize_english_token(raw_token)
        )

    # 상품 한 건 안에서는 같은 참고정보를 한 번만 보존
    for category in REFERENCE_CATEGORY_ORDER:
        result[category] = list(
            dict.fromkeys(
                token
                for token in result[category]
                if token
            )
        )

    remaining_text = " ".join(
        remaining_text.split()
    )

    return result, remaining_text


def extract_reference_tokens(
    text: str,
) -> dict[str, list[str]]:
    """
    문자열에서 참고정보만 추출한다.
    """
    reference_tokens, _ = scan_reference_tokens(
        text
    )

    return reference_tokens


def remove_reference_expressions(
    text: str,
) -> str:
    """
    수량·규격·영문·모델 정보를 제거하고
    의미 키워드용 문자열만 반환한다.
    """
    _, remaining_text = scan_reference_tokens(
        text
    )

    return remaining_text


def build_reference_distribution(
    samples: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    참고정보가 포함된 상품 수를 계산한다.

    한 상품명 안에서 동일 표현이 여러 번 등장해도
    상품 한 건당 한 번만 계산한다.
    """
    sample_count = len(samples)

    counters: dict[str, Counter[str]] = {
        category: Counter()
        for category in REFERENCE_CATEGORY_ORDER
    }

    for sample in samples:
        reference_tokens = sample.get(
            "reference_tokens",
            {},
        )

        if not isinstance(
            reference_tokens,
            dict,
        ):
            reference_tokens = {}

        # 이전 형식의 샘플을 읽을 때는
        # 저장된 상품명에서 다시 추출한다.
        if not reference_tokens:
            source_title = str(
                sample.get(
                    "cleaned_title",
                    sample.get(
                        "original_title",
                        "",
                    ),
                )
            )

            reference_tokens = (
                extract_reference_tokens(
                    source_title
                )
            )

        for category in REFERENCE_CATEGORY_ORDER:
            tokens = reference_tokens.get(
                category,
                [],
            )

            if not isinstance(tokens, list):
                continue

            unique_tokens = list(
                dict.fromkeys(
                    str(token).strip()
                    for token in tokens
                    if str(token).strip()
                )
            )

            counters[category].update(
                unique_tokens
            )

    distribution: dict[str, Any] = {
        "sample_count": sample_count,
        "distribution_basis": (
            "product_presence"
        ),
    }

    for category in REFERENCE_CATEGORY_ORDER:
        distribution[category] = [
            {
                "token": token,
                "product_count": count,
                "ratio": (
                    count / sample_count
                    if sample_count > 0
                    else 0.0
                ),
            }
            for token, count
            in counters[category].most_common()
        ]

    return distribution