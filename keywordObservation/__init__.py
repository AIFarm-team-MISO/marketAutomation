"""
네이버 쇼핑 키워드·카테고리 관찰 데이터 수집 패키지.
"""

from .naver_shopping_client import (
    NaverShoppingApiError,
    fetch_shopping_items,
    fetch_shopping_response,
)

from .observation_processor import (
    build_category_path,
    build_sample,
    build_samples,
    clean_html,
    normalize_title_for_frequency,
    remove_brand_from_title,
    tokenize_title,
    build_source_item,
)

from .observation_analyzer import (
    analyze_samples,
    build_top_categories,
    count_all_keywords,
    count_categories,
    count_removed_brands,
    filter_keyword_counter,
)

from .query_validator import (
    evaluate_search_result,
    extract_match_tokens,
    normalize_for_match,
    split_keyword_tokens,
    validate_keyword_format,
)

from .reference_token_analyzer import (
    REFERENCE_CATEGORY_NAMES,
    REFERENCE_CATEGORY_ORDER,
    build_reference_distribution,
    extract_reference_tokens,
    normalize_english_token,
    normalize_measurement_token,
    normalize_model_code_token,
    normalize_quantity_token,
    remove_reference_expressions,
    scan_reference_tokens,
)


__all__ = [
    "NaverShoppingApiError",
    "fetch_shopping_items",

    "build_category_path",
    "build_sample",
    "build_samples",
    "clean_html",
    "normalize_title_for_frequency",
    "remove_brand_from_title",
    "tokenize_title",

    "evaluate_search_result",
    "normalize_for_match",
    "validate_keyword_format",

    "analyze_samples",
    "build_top_categories",
    "count_all_keywords",
    "count_categories",
    "count_removed_brands",
    "filter_keyword_counter",
    "ObservationStoreError",
    "append_observation",
    "build_observation_record",
    "normalize_keyword",
    "find_latest_observation",
    "find_observations",
    "load_observations",
    "make_safe_filename",
    "save_pretty_observation",
    "normalize_spaces",
    "normalize_text_whitespace",

    "count_product_keywords",
    "extract_match_tokens",
    "split_keyword_tokens",
    "REFERENCE_CATEGORY_NAMES",
    "REFERENCE_CATEGORY_ORDER",
    "build_reference_distribution",
    "extract_reference_tokens",
    "normalize_english_token",
    "normalize_measurement_token",
    "normalize_model_code_token",
    "normalize_quantity_token",
    "remove_reference_expressions",
    "scan_reference_tokens",
    "build_source_item",
    "fetch_shopping_response",

    
]

__version__ = "0.11.0"