from __future__ import annotations

import time
from typing import Any

from utils.global_logger import logger

from keywordObservation.console_key_confirm import (
    confirm_enter_or_escape,
)
from keywordObservation.keyword_observation_paths import (
    OPTIMIZATION_INPUT_DIR,
)
from keywordObservation.keyword_knowledge_reporter import (
    print_tag_search_observation,
)
from keywordObservation.manual_tag_store import (
    ManualTagStoreError,
    append_manual_tag_usage,
)
from keywordObservation.naver_commerce_auth import (
    NaverCommerceAuthError,
)
from keywordObservation.naver_tag_client import (
    NaverTagApiError,
    NaverTagClient,
)
from keywordObservation.optimization_record_store import (
    OptimizationRecordStoreError,
    append_optimization_import_history,
    append_optimization_records,
    load_existing_optimization_fingerprints,
)
from keywordObservation.optimization_workbook_importer import (
    analyze_optimization_workbooks,
    discover_optimization_workbooks,
)
from keywordObservation.tag_observation_store import (
    TagObservationStoreError,
    append_recommend_tag_observation,
    append_restriction_observation,
)
from keywordObservation.tag_registry_builder import (
    TagRegistryBuildError,
    build_tag_registry,
)
from keywordObservation.tag_text_utils import (
    normalize_keyword,
    parse_manual_tag_input,
    tag_key,
)



def _log(message: str, level: str = "INFO") -> None:
    logger.log(
        message,
        level=level,
        also_to_report=True,
    )



def _separator(char: str = "-") -> None:
    logger.log_separator(
        char=char,
        level="INFO",
        also_to_report=True,
    )



_TAG_CLIENT: NaverTagClient | None = None


def _get_tag_client() -> NaverTagClient:
    global _TAG_CLIENT

    if _TAG_CLIENT is None:
        _TAG_CLIENT = NaverTagClient()

    return _TAG_CLIENT


def _print_api_error(error: Exception) -> None:
    _log(f"태그 API 처리 오류: {error}", level="ERROR")

    trace_id = str(getattr(error, "trace_id", ""))
    status_code = getattr(error, "status_code", None)
    payload = getattr(error, "payload", None)

    if status_code is not None:
        _log(f"   └ HTTP 상태: {status_code}", level="ERROR")
    if trace_id:
        _log(f"   └ Trace ID: {trace_id}", level="ERROR")
    if payload:
        _log(f"   └ 응답: {payload}", level="ERROR")



def run_tag_search(
    keyword: str,
    *,
    tag_api_enabled: bool = True,
) -> dict[str, Any] | None:
    normalized_keyword = normalize_keyword(keyword)

    if not normalized_keyword:
        _log("태그검색 키워드를 입력해 주세요.", level="WARNING")
        return None

    if not tag_api_enabled:
        _log("커머스 태그 API 기능이 비활성화되어 있습니다.", level="WARNING")
        return None

    _log(f"🏷️ 네이버 추천 태그 검색 시작: '{normalized_keyword}'")

    try:
        client = _get_tag_client()
        response = client.search_recommend_tags(normalized_keyword)

        history_path, readable_path, record = (
            append_recommend_tag_observation(
                keyword=normalized_keyword,
                tags=response.get("tags", []),
                response_metadata=response,
                source_command="태그검색",
            )
        )

        build_tag_registry()

        print_tag_search_observation(record)

        _log(f"💾 태그 관찰이력 저장 완료: {history_path}")
        _log(f"📖 읽기용 최신 태그파일 저장 완료: {readable_path}")
        return record

    except (
        NaverCommerceAuthError,
        NaverTagApiError,
        TagObservationStoreError,
        TagRegistryBuildError,
        ValueError,
    ) as error:
        _print_api_error(error)
        return None



def run_manual_tag_add(keyword: str) -> dict[str, Any] | None:
    normalized_keyword = normalize_keyword(keyword)

    if not normalized_keyword:
        _log("태그를 연결할 메인키워드를 입력해 주세요.", level="WARNING")
        return None

    _separator("=")
    _log(f"✅ 실제 등록 태그 수동추가: '{normalized_keyword}'")
    _log("태그는 쉼표 또는 줄바꿈으로 구분합니다.")

    raw_tags = input("등록한 태그: ").strip()
    tags = parse_manual_tag_input(raw_tags)

    if not tags:
        _log("저장할 태그가 없습니다.", level="WARNING")
        return None

    original_product_name = input("원본상품명 [선택]: ").strip()
    processed_product_name = input("가공상품명 [선택]: ").strip()
    seller_product_code = input("판매자 상품코드 [선택]: ").strip()
    category = input("카테고리 [선택]: ").strip()
    memo = input("메모 [선택]: ").strip()

    _separator("-")
    _log(f"메인키워드: {normalized_keyword}")
    _log("저장 태그: " + ", ".join(tag["text"] for tag in tags))
    if original_product_name:
        _log(f"원본상품명: {original_product_name}")
    if processed_product_name:
        _log(f"가공상품명: {processed_product_name}")
    if seller_product_code:
        _log(f"판매자 상품코드: {seller_product_code}")
    if category:
        _log(f"카테고리: {category}")

    confirmed = confirm_enter_or_escape(
        execute_message="[Enter / 1 / y] 실제 등록 태그로 저장",
        cancel_message="[Esc / 2 / q] 저장 취소",
    )

    if not confirmed:
        _log("태그추가를 취소했습니다.", level="WARNING")
        return None

    try:
        result = append_manual_tag_usage(
            keyword=normalized_keyword,
            tags=tags,
            original_product_name=original_product_name,
            processed_product_name=processed_product_name,
            seller_product_code=seller_product_code,
            category=category,
            memo=memo,
        )
        build_tag_registry()

        _log(
            "✅ 수동 태그 저장 완료: "
            f"신규 {result['appended_count']}개 / "
            f"중복 생략 {result['skipped_count']}개"
        )
        _log(f"   └ 저장파일: {result['path']}")
        return result

    except (
        ManualTagStoreError,
        TagRegistryBuildError,
    ) as error:
        _log(f"수동 태그 저장 오류: {error}", level="ERROR")
        return None



def run_tag_check(
    raw_tags: str,
    *,
    tag_api_enabled: bool = True,
    delay_seconds: float = 0.2,
) -> dict[str, Any] | None:
    tags = parse_manual_tag_input(raw_tags)

    if not tags:
        _log("검사할 태그를 입력해 주세요.", level="WARNING")
        return None

    if not tag_api_enabled:
        _log("커머스 태그 API 기능이 비활성화되어 있습니다.", level="WARNING")
        return None

    tag_names = [tag["text"] for tag in tags]
    client = _get_tag_client()
    exact_results: list[dict[str, Any]] = []

    try:
        for index, tag in enumerate(tag_names):
            response = client.search_recommend_tags(tag)

            _, _, record = append_recommend_tag_observation(
                keyword=tag,
                tags=response.get("tags", []),
                response_metadata=response,
                source_command="태그검사",
            )

            exact_match = next(
                (
                    item
                    for item in record.get("tags", [])
                    if isinstance(item, dict)
                    and item.get("match_type") == "exact"
                ),
                None,
            )

            exact_results.append(
                {
                    "tag": tag,
                    "exact_match": exact_match,
                }
            )

            if delay_seconds > 0 and index < len(tag_names) - 1:
                time.sleep(delay_seconds)

        restriction_response = client.check_restricted_tags(tag_names)
        restriction_by_key = {
            tag_key(item.get("tag", "")): bool(item.get("restricted", False))
            for item in restriction_response.get("results", [])
            if isinstance(item, dict)
        }

        append_restriction_observation(
            requested_tags=tag_names,
            results=restriction_response.get("results", []),
            response_metadata=restriction_response,
        )

        build_tag_registry()

        _separator("=")
        _log("🧪 태그검사 결과")

        for result in exact_results:
            tag = result["tag"]
            exact_match = result["exact_match"]
            restricted = restriction_by_key.get(tag_key(tag))

            if exact_match:
                exact_text = f"정확일치 / code {exact_match.get('code')}"
            else:
                exact_text = "추천 태그 정확일치 없음"

            if restricted is True:
                restriction_text = "제한태그"
            elif restricted is False:
                restriction_text = "제한 아님"
            else:
                restriction_text = "제한응답 없음"

            _log(f"   {tag} — {exact_text} / {restriction_text}")

        _log(
            "※ 추천 태그 및 제한 API 결과와 별개로 상품 카테고리·내부 정책에 따라 "
            "실제 등록이 거부될 수 있습니다.",
            level="WARNING",
        )
        _separator("=")

        return {
            "exact_results": exact_results,
            "restriction_results": restriction_response.get("results", []),
        }

    except (
        NaverCommerceAuthError,
        NaverTagApiError,
        TagObservationStoreError,
        TagRegistryBuildError,
        ValueError,
    ) as error:
        _print_api_error(error)
        return None



def run_optimization_import(
    *,
    supported_extensions: list[str],
) -> bool:
    paths = discover_optimization_workbooks(
        OPTIMIZATION_INPUT_DIR,
        extensions=supported_extensions,
    )

    if not paths:
        _log(
            "가공자료 엑셀파일이 없습니다. "
            f"'{OPTIMIZATION_INPUT_DIR}'에 파일을 넣어 주세요.",
            level="WARNING",
        )
        return False

    _log("🛠️ 최적화가공틀 분석을 시작합니다.")
    preview = analyze_optimization_workbooks(paths)
    existing = load_existing_optimization_fingerprints()
    new_records = [
        record
        for record in preview.get("records", [])
        if record.get("fingerprint") not in existing
    ]
    duplicate_count = preview.get("valid_record_count", 0) - len(new_records)

    _separator("=")
    _log("📋 가공자료추가 실행 전 요약")
    _log(f"   입력폴더: {OPTIMIZATION_INPUT_DIR}")
    _log(f"   엑셀파일: {len(paths)}개")
    for summary in preview.get("file_summaries", []):
        _log(
            f"      {summary.get('source_file')} — "
            f"시트 {summary.get('sheet_count')} / "
            f"정상 {summary.get('valid_record_count')} / "
            f"불완전 {summary.get('invalid_row_count')}"
        )
    _log(f"   정상 가공기록: {preview.get('valid_record_count', 0)}건")
    _log(f"   기존 중복: {duplicate_count}건")
    _log(f"   신규 저장예정: {len(new_records)}건")
    _log(f"   고유 메인키워드: {preview.get('unique_keyword_count', 0)}개")
    _log(f"   고유 검증태그: {preview.get('unique_tag_count', 0)}개")
    _log(f"   불완전 행: {preview.get('invalid_row_count', 0)}건")
    _log(f"   파일 오류: {preview.get('error_count', 0)}건")

    if preview.get("errors"):
        for error in preview["errors"]:
            _log(
                f"      오류: {error.get('source_file')} / {error.get('message')}",
                level="ERROR",
            )

    if not new_records:
        _log("새로 저장할 가공자료가 없습니다.")
        return False

    confirmed = confirm_enter_or_escape(
        execute_message="[Enter / 1 / y] 신규 가공자료와 검증태그 저장",
        cancel_message="[Esc / 2 / q] 저장 취소",
    )

    if not confirmed:
        _log("가공자료추가를 취소했습니다.", level="WARNING")
        return False

    try:
        result = append_optimization_records(new_records)
        registry = build_tag_registry()
        history_path = append_optimization_import_history(
            {
                "batch_id": result["batch_id"],
                "input_files": [path.name for path in paths],
                "analyzed_record_count": preview.get("valid_record_count", 0),
                "new_record_count": result["appended_count"],
                "duplicate_record_count": duplicate_count + result["skipped_count"],
                "invalid_row_count": preview.get("invalid_row_count", 0),
                "unique_keyword_count": preview.get("unique_keyword_count", 0),
                "unique_tag_count": preview.get("unique_tag_count", 0),
                "registry_tag_count": registry.get("tag_count", 0),
            }
        )

        _separator("=")
        _log("✅ 가공자료추가 완료")
        _log(f"   신규 가공기록: {result['appended_count']}건")
        _log(f"   중복 생략: {result['skipped_count']}건")
        _log(f"   통합 태그사전: {registry.get('tag_count', 0)}개")
        _log(f"   가공자료 파일: {result['path']}")
        _log(f"   가져오기 이력: {history_path}")
        _separator("=")
        return True

    except (
        OptimizationRecordStoreError,
        TagRegistryBuildError,
    ) as error:
        _log(f"가공자료 저장 오류: {error}", level="ERROR")
        return False
