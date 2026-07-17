from __future__ import annotations

import html
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


CLASSIFIER_VERSION = "0.1.0"

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_DICTIONARY_PATH = (
    PACKAGE_DIR
    / "reference_rules"
    / "reference_dictionary.json"
)

REFERENCE_CATEGORIES = (
    "quantity",
    "measurement",
    "specification",
    "option",
    "english",
    "model_code",
)

NUMBER_PATTERN = r"\d+(?:\.\d+)?"

QUANTITY_UNIT_PATTERN = (
    r"(?:개입|매입|개|매|장|롤|팩|박스|세트|쌍|"
    r"조|봉|병|캔|포|p|pcs?)"
)

MEASUREMENT_UNIT_PATTERN = (
    r"(?:mm|cm|km|m|μm|um|mic|mil|inch|in|"
    r"ml|l|cc|mg|kg|g|oz|lb|t)"
)

ELECTRICAL_UNIT_PATTERN = (
    r"(?:v|w|a|ma|mah|wh|kw|hz|khz|mhz|"
    r"db|bar|psi|pa|kpa|mpa)"
)

PROMOTION_PATTERN = re.compile(
    rf"(?<![A-Za-z0-9])"
    rf"({NUMBER_PATTERN}\s*{QUANTITY_UNIT_PATTERN}?"
    rf"\s*\+\s*"
    rf"{NUMBER_PATTERN}\s*{QUANTITY_UNIT_PATTERN}?)"
    rf"(?![A-Za-z0-9])",
    re.IGNORECASE,
)

QUANTITY_SET_PATTERN = re.compile(
    rf"(?<![\d.])"
    rf"({NUMBER_PATTERN})\s*"
    rf"(개|매|장|롤|팩|박스|쌍|조|봉|병|캔|포)"
    rf"\s*(세트)"
    rf"(?![A-Za-z가-힣])",
    re.IGNORECASE,
)

QUANTITY_PATTERN = re.compile(
    rf"(?<![\d.])"
    rf"({NUMBER_PATTERN})\s*"
    rf"({QUANTITY_UNIT_PATTERN})"
    rf"(?![A-Za-z가-힣])",
    re.IGNORECASE,
)

COMPOSITE_MEASUREMENT_PATTERN = re.compile(
    rf"(?<![\d.])"
    rf"({NUMBER_PATTERN})\s*({MEASUREMENT_UNIT_PATTERN})?"
    rf"\s*x\s*"
    rf"({NUMBER_PATTERN})\s*({MEASUREMENT_UNIT_PATTERN})?"
    rf"(?:\s*x\s*"
    rf"({NUMBER_PATTERN})\s*({MEASUREMENT_UNIT_PATTERN})?"
    rf")?",
    re.IGNORECASE,
)

RANGE_MEASUREMENT_PATTERN = re.compile(
    rf"(?<![\d.])"
    rf"({NUMBER_PATTERN})\s*[~\-]\s*"
    rf"({NUMBER_PATTERN})\s*"
    rf"({MEASUREMENT_UNIT_PATTERN})"
    rf"(?![A-Za-z])",
    re.IGNORECASE,
)

SCALAR_MEASUREMENT_PATTERN = re.compile(
    rf"(?<![\d.])"
    rf"({NUMBER_PATTERN})\s*"
    rf"({MEASUREMENT_UNIT_PATTERN})"
    rf"(?![A-Za-z])",
    re.IGNORECASE,
)

ELECTRICAL_SPEC_PATTERN = re.compile(
    rf"(?<![\d.])"
    rf"({NUMBER_PATTERN})\s*"
    rf"({ELECTRICAL_UNIT_PATTERN})"
    rf"(?![A-Za-z])",
    re.IGNORECASE,
)

PAPER_SPEC_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])"
    r"([AB]\s*[0-9]{1,2})"
    r"(?![A-Za-z0-9])",
    re.IGNORECASE,
)

NUMBER_SPEC_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(?:NO\.?|№)\s*([0-9]+(?:\.[0-9]+)?)"
    r"(?![A-Za-z0-9])",
    re.IGNORECASE,
)

IP_SPEC_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(IP[0-9]{2,3})"
    r"(?![A-Za-z0-9])",
    re.IGNORECASE,
)

OPTION_PATTERN = re.compile(
    r"(?<![A-Za-z가-힣])"
    r"(대\s*[/·,]\s*중\s*[/·,]\s*소"
    r"|S\s*/\s*M\s*/\s*L)"
    r"(?![A-Za-z가-힣])",
    re.IGNORECASE,
)

CANDIDATE_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])"
    r"([A-Za-z0-9]+"
    r"(?:[._/+~\-][A-Za-z0-9]+)*)"
    r"(?![A-Za-z0-9])"
)


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


def _normalize_text(
    value: Any,
) -> str:
    text = unicodedata.normalize(
        "NFKC",
        html.unescape(
            str(value or "")
        ),
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = (
        text
        .replace("×", "x")
        .replace("✕", "x")
        .replace("＊", "x")
        .replace("*", "x")
        .replace("–", "-")
        .replace("—", "-")
        .replace("〜", "~")
        .replace("～", "~")
    )

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def _normalize_unit(
    unit: str,
) -> str:
    normalized = str(
        unit
    ).strip().lower()

    mapping = {
        "pcs": "P",
        "pc": "P",
        "p": "P",
        "um": "μm",
        "μm": "μm",
        "inch": "in",
    }

    return mapping.get(
        normalized,
        normalized,
    )


def _normalize_quantity(
    raw: str,
) -> str:
    text = re.sub(
        r"\s+",
        "",
        raw,
    )

    text = re.sub(
        r"(?i)pcs?",
        "P",
        text,
    )

    text = re.sub(
        r"(?i)(?<=\d)p",
        "P",
        text,
    )

    return text


def _normalize_measurement(
    numbers: list[str],
    units: list[str],
) -> str:
    normalized_units = [
        _normalize_unit(unit)
        if unit
        else ""
        for unit in units
    ]

    fallback_unit = next(
        (
            unit
            for unit in reversed(
                normalized_units
            )
            if unit
        ),
        "",
    )

    parts: list[str] = []

    for number, unit in zip(
        numbers,
        normalized_units,
    ):
        parts.append(
            f"{number}{unit or fallback_unit}"
        )

    return "x".join(parts)


def _span_overlaps(
    start: int,
    end: int,
    spans: Iterable[
        tuple[int, int]
    ],
) -> bool:
    return any(
        start < existing_end
        and end > existing_start
        for existing_start, existing_end in spans
    )


def _load_dictionary(
    dictionary_path: Path | None = None,
) -> dict[str, Any]:
    path = (
        dictionary_path
        or DEFAULT_DICTIONARY_PATH
    )

    if not path.exists():
        return {
            "dictionary_version": "missing",
            "approved": {},
            "aliases": {},
            "ignored_candidates": [],
        }

    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {
            "dictionary_version": "invalid",
            "approved": {},
            "aliases": {},
            "ignored_candidates": [],
        }

    return _safe_dict(data)


def _extract_existing_tokens(
    sample: dict[str, Any],
) -> dict[str, set[str]]:
    result = {
        category: set()
        for category in (
            REFERENCE_CATEGORIES
        )
    }

    reference_tokens = _safe_dict(
        sample.get(
            "reference_tokens"
        )
    )

    for category in (
        "quantity",
        "measurement",
        "english",
        "model_code",
        "specification",
        "option",
    ):
        for token in _safe_list(
            reference_tokens.get(
                category
            )
        ):
            normalized = str(
                token
            ).strip()

            if normalized:
                result[
                    category
                ].add(normalized)

    return result


def _extract_dictionary_tokens(
    normalized_title: str,
    dictionary: dict[str, Any],
) -> dict[str, set[str]]:
    result = {
        category: set()
        for category in (
            REFERENCE_CATEGORIES
        )
    }

    approved = _safe_dict(
        dictionary.get(
            "approved"
        )
    )

    aliases = {
        str(key): str(value)
        for key, value in _safe_dict(
            dictionary.get(
                "aliases"
            )
        ).items()
        if str(key).strip()
        and str(value).strip()
    }

    searchable_title = (
        normalized_title.casefold()
    )

    for category in (
        REFERENCE_CATEGORIES
    ):
        for raw_token in _safe_list(
            approved.get(
                category
            )
        ):
            token = str(
                raw_token
            ).strip()

            if (
                token
                and token.casefold()
                in searchable_title
            ):
                result[
                    category
                ].add(token)

    for source, target in (
        aliases.items()
    ):
        if source.casefold() not in (
            searchable_title
        ):
            continue

        target_casefold = (
            target.casefold()
        )

        matched_category = None

        for category in (
            REFERENCE_CATEGORIES
        ):
            approved_values = {
                str(value)
                .strip()
                .casefold()
                for value in _safe_list(
                    approved.get(
                        category
                    )
                )
            }

            if target_casefold in (
                approved_values
            ):
                matched_category = (
                    category
                )
                break

        if matched_category:
            result[
                matched_category
            ].add(target)

    return result


def _extract_builtin_tokens(
    normalized_title: str,
) -> tuple[
    dict[str, set[str]],
    list[tuple[int, int]],
]:
    result = {
        category: set()
        for category in (
            REFERENCE_CATEGORIES
        )
    }

    matched_spans: list[
        tuple[int, int]
    ] = []

    for match in PROMOTION_PATTERN.finditer(
        normalized_title
    ):
        result[
            "quantity"
        ].add(
            _normalize_quantity(
                match.group(1)
            )
        )

        matched_spans.append(
            match.span()
        )

    for match in QUANTITY_SET_PATTERN.finditer(
        normalized_title
    ):
        if _span_overlaps(
            *match.span(),
            matched_spans,
        ):
            continue

        result[
            "quantity"
        ].add(
            (
                f"{match.group(1)}"
                f"{match.group(2)}세트"
            )
        )

        matched_spans.append(
            match.span()
        )

    for match in QUANTITY_PATTERN.finditer(
        normalized_title
    ):
        if _span_overlaps(
            *match.span(),
            matched_spans,
        ):
            continue

        unit = _normalize_unit(
            match.group(2)
        )

        result[
            "quantity"
        ].add(
            f"{match.group(1)}{unit}"
        )

        matched_spans.append(
            match.span()
        )

    for match in COMPOSITE_MEASUREMENT_PATTERN.finditer(
        normalized_title
    ):
        if _span_overlaps(
            *match.span(),
            matched_spans,
        ):
            continue

        numbers = [
            match.group(1),
            match.group(3),
        ]

        units = [
            match.group(2) or "",
            match.group(4) or "",
        ]

        if match.group(5):
            numbers.append(
                match.group(5)
            )

            units.append(
                match.group(6) or ""
            )

        if not any(units):
            continue

        result[
            "measurement"
        ].add(
            _normalize_measurement(
                numbers,
                units,
            )
        )

        matched_spans.append(
            match.span()
        )

    for match in RANGE_MEASUREMENT_PATTERN.finditer(
        normalized_title
    ):
        if _span_overlaps(
            *match.span(),
            matched_spans,
        ):
            continue

        unit = _normalize_unit(
            match.group(3)
        )

        result[
            "measurement"
        ].add(
            (
                f"{match.group(1)}"
                f"~{match.group(2)}"
                f"{unit}"
            )
        )

        matched_spans.append(
            match.span()
        )

    for match in SCALAR_MEASUREMENT_PATTERN.finditer(
        normalized_title
    ):
        if _span_overlaps(
            *match.span(),
            matched_spans,
        ):
            continue

        unit = _normalize_unit(
            match.group(2)
        )

        result[
            "measurement"
        ].add(
            f"{match.group(1)}{unit}"
        )

        matched_spans.append(
            match.span()
        )

    for match in ELECTRICAL_SPEC_PATTERN.finditer(
        normalized_title
    ):
        if _span_overlaps(
            *match.span(),
            matched_spans,
        ):
            continue

        unit = str(
            match.group(2)
        ).upper()

        result[
            "specification"
        ].add(
            f"{match.group(1)}{unit}"
        )

        matched_spans.append(
            match.span()
        )

    for match in PAPER_SPEC_PATTERN.finditer(
        normalized_title
    ):
        if _span_overlaps(
            *match.span(),
            matched_spans,
        ):
            continue

        result[
            "specification"
        ].add(
            re.sub(
                r"\s+",
                "",
                match.group(1),
            ).upper()
        )

        matched_spans.append(
            match.span()
        )

    for match in NUMBER_SPEC_PATTERN.finditer(
        normalized_title
    ):
        if _span_overlaps(
            *match.span(),
            matched_spans,
        ):
            continue

        result[
            "specification"
        ].add(
            f"No.{match.group(1)}"
        )

        matched_spans.append(
            match.span()
        )

    for match in IP_SPEC_PATTERN.finditer(
        normalized_title
    ):
        if _span_overlaps(
            *match.span(),
            matched_spans,
        ):
            continue

        result[
            "specification"
        ].add(
            match.group(1).upper()
        )

        matched_spans.append(
            match.span()
        )

    for match in OPTION_PATTERN.finditer(
        normalized_title
    ):
        if _span_overlaps(
            *match.span(),
            matched_spans,
        ):
            continue

        raw = re.sub(
            r"\s+",
            "",
            match.group(1),
        )

        if re.search(
            r"대",
            raw,
        ):
            normalized = "대/중/소"

        else:
            normalized = "S/M/L"

        result[
            "option"
        ].add(normalized)

        matched_spans.append(
            match.span()
        )

    return result, matched_spans


def _extract_unclassified_candidates(
    normalized_title: str,
    matched_spans: list[
        tuple[int, int]
    ],
    recognized_tokens: set[str],
    dictionary: dict[str, Any],
) -> set[str]:
    ignored_candidates = {
        str(token)
        .strip()
        .casefold()
        for token in _safe_list(
            dictionary.get(
                "ignored_candidates"
            )
        )
        if str(token).strip()
    }

    recognized_casefold = {
        str(token)
        .strip()
        .casefold()
        for token in recognized_tokens
        if str(token).strip()
    }

    result: set[str] = set()

    for match in CANDIDATE_PATTERN.finditer(
        normalized_title
    ):
        if _span_overlaps(
            *match.span(),
            matched_spans,
        ):
            continue

        token = match.group(1).strip()

        if len(token) < 2:
            continue

        token_casefold = (
            token.casefold()
        )

        if token_casefold in (
            recognized_casefold
        ):
            continue

        if token_casefold in (
            ignored_candidates
        ):
            continue

        if token.isdigit():
            continue

        has_digit = any(
            char.isdigit()
            for char in token
        )

        uppercase_count = sum(
            char.isupper()
            for char in token
        )

        has_reference_symbol = any(
            symbol in token
            for symbol in (
                "+",
                "/",
                ".",
                "-",
                "~",
            )
        )

        if not (
            has_digit
            or uppercase_count >= 2
            or has_reference_symbol
        ):
            continue

        result.add(token)

    return result


def _merge_category_tokens(
    *mappings: dict[
        str,
        set[str],
    ],
) -> dict[str, set[str]]:
    result = {
        category: set()
        for category in (
            REFERENCE_CATEGORIES
        )
    }

    for mapping in mappings:
        for category in (
            REFERENCE_CATEGORIES
        ):
            result[
                category
            ].update(
                mapping.get(
                    category,
                    set(),
                )
            )

    return result


def _distribution_items(
    counter: Counter[str],
    sample_count: int,
    examples: dict[
        str,
        list[str],
    ] | None = None,
) -> list[dict[str, Any]]:
    items: list[
        dict[str, Any]
    ] = []

    for token, product_count in (
        counter.most_common()
    ):
        item: dict[str, Any] = {
            "token": token,
            "product_count": product_count,
            "ratio": (
                product_count / sample_count
                if sample_count > 0
                else 0.0
            ),
        }

        if examples is not None:
            item[
                "examples"
            ] = examples.get(
                token,
                [],
            )[:3]

        items.append(item)

    return items


def build_enhanced_reference_distribution(
    samples: list[dict[str, Any]],
    base_distribution: dict[str, Any] | None = None,
    dictionary_path: Path | None = None,
) -> dict[str, Any]:
    """
    기존 참고정보 분류를 유지하면서 다음 표현을 보강한다.

    - 1+1, 2P+1P, 10매입, 5개세트
    - 0.5T, 10~20cm, 80x50x30mm
    - 220V, 20W, A4, B5, No.12, IP65
    - 대/중/소, S/M/L
    - 아직 분류되지 않은 영문·숫자 혼합 후보

    모든 빈도는 상품 존재 수를 기준으로 계산한다.
    """
    dictionary = _load_dictionary(
        dictionary_path
    )

    sample_count = len(samples)

    category_counters = {
        category: Counter()
        for category in (
            REFERENCE_CATEGORIES
        )
    }

    candidate_counter: Counter[
        str
    ] = Counter()

    candidate_examples: dict[
        str,
        list[str],
    ] = defaultdict(list)

    for sample in samples:
        original_title = str(
            sample.get(
                "original_title",
                sample.get(
                    "cleaned_title",
                    "",
                ),
            )
        )

        normalized_title = (
            _normalize_text(
                original_title
            )
        )

        existing_tokens = (
            _extract_existing_tokens(
                sample
            )
        )

        builtin_tokens, matched_spans = (
            _extract_builtin_tokens(
                normalized_title
            )
        )

        dictionary_tokens = (
            _extract_dictionary_tokens(
                normalized_title,
                dictionary,
            )
        )

        merged_tokens = (
            _merge_category_tokens(
                existing_tokens,
                builtin_tokens,
                dictionary_tokens,
            )
        )

        for category in (
            REFERENCE_CATEGORIES
        ):
            category_counters[
                category
            ].update(
                merged_tokens[
                    category
                ]
            )

        recognized_tokens = set().union(
            *merged_tokens.values()
        )

        candidates = (
            _extract_unclassified_candidates(
                normalized_title=(
                    normalized_title
                ),
                matched_spans=(
                    matched_spans
                ),
                recognized_tokens=(
                    recognized_tokens
                ),
                dictionary=dictionary,
            )
        )

        candidate_counter.update(
            candidates
        )

        for candidate in candidates:
            if (
                original_title
                and original_title
                not in candidate_examples[
                    candidate
                ]
            ):
                candidate_examples[
                    candidate
                ].append(
                    original_title
                )

    # 과거 집계만 있고 sample.reference_tokens가 없는 경우를 보완한다.
    normalized_base = _safe_dict(
        base_distribution
    )

    for category in (
        REFERENCE_CATEGORIES
    ):
        for item in _safe_list(
            normalized_base.get(
                category
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

            product_count = int(
                item.get(
                    "product_count",
                    0,
                )
                or 0
            )

            if (
                token
                and product_count
                > category_counters[
                    category
                ].get(
                    token,
                    0,
                )
            ):
                category_counters[
                    category
                ][
                    token
                ] = product_count

    result: dict[str, Any] = {
        "sample_count": sample_count,
        "distribution_basis": (
            "product_presence"
        ),
        "classification_version": (
            CLASSIFIER_VERSION
        ),
        "dictionary_version": str(
            dictionary.get(
                "dictionary_version",
                "unknown",
            )
        ),
    }

    for category in (
        REFERENCE_CATEGORIES
    ):
        result[
            category
        ] = _distribution_items(
            category_counters[
                category
            ],
            sample_count,
        )

    result[
        "unclassified"
    ] = _distribution_items(
        candidate_counter,
        sample_count,
        examples=candidate_examples,
    )

    return result
