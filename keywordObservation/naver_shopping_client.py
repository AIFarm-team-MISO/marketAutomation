from __future__ import annotations

import time
from typing import Any

import requests

from config.settings import (
    NAVER_CLIENT_ID,
    NAVER_CLIENT_SECRET,
)


NAVER_SHOPPING_API_URL = (
    "https://openapi.naver.com/v1/search/shop.json"
)

ALLOWED_SORT_VALUES = {
    "sim",
    "date",
    "asc",
    "dsc",
}

DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_RETRY_BASE_SECONDS = 1.0

RETRYABLE_STATUS_CODES = {
    429,
    500,
    502,
    503,
    504,
}


class NaverShoppingApiError(RuntimeError):
    """
    네이버 쇼핑 API 호출 실패를 나타내는 예외.

    retryable:
        같은 요청을 다시 시도할 가치가 있는지 표시한다.

    category 예:
        timeout
        network_error
        rate_limit
        server_error
        authentication_error
        request_error
        response_parse_error
    """

    def __init__(
        self,
        message: str,
        *,
        category: str,
        retryable: bool,
        status_code: int | None = None,
        error_code: str = "",
        error_message: str = "",
        attempt_count: int = 1,
    ) -> None:
        super().__init__(message)

        self.category = category
        self.retryable = retryable
        self.status_code = status_code
        self.error_code = error_code
        self.error_message = error_message
        self.attempt_count = attempt_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "retryable": self.retryable,
            "status_code": self.status_code,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "attempt_count": self.attempt_count,
            "message": str(self),
        }


def _validate_request(
    keyword: str,
    display: int,
    sort: str,
    max_attempts: int,
) -> str:
    normalized_keyword = str(keyword).strip()

    if not normalized_keyword:
        raise ValueError(
            "검색어가 비어 있습니다."
        )

    if not 1 <= display <= 100:
        raise ValueError(
            "display는 1 이상 100 이하여야 합니다."
        )

    if sort not in ALLOWED_SORT_VALUES:
        raise ValueError(
            f"지원하지 않는 정렬방식입니다: {sort}"
        )

    if max_attempts < 1:
        raise ValueError(
            "max_attempts는 1 이상이어야 합니다."
        )

    if not str(NAVER_CLIENT_ID).strip():
        raise ValueError(
            "NAVER_CLIENT_ID가 설정되지 않았습니다."
        )

    if not str(NAVER_CLIENT_SECRET).strip():
        raise ValueError(
            "NAVER_CLIENT_SECRET이 설정되지 않았습니다."
        )

    return normalized_keyword


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _extract_error_response(
    response: requests.Response,
) -> tuple[str, str]:
    """
    네이버 오류 응답에서 errorCode와
    errorMessage를 안전하게 추출한다.
    """
    error_code = ""
    error_message = ""

    try:
        payload = response.json()

        if isinstance(payload, dict):
            error_code = str(
                payload.get(
                    "errorCode",
                    "",
                )
            ).strip()

            error_message = str(
                payload.get(
                    "errorMessage",
                    "",
                )
            ).strip()

    except ValueError:
        error_message = str(
            response.text
        ).strip()[:500]

    return error_code, error_message


def _classify_http_error(
    response: requests.Response,
    attempt_count: int,
) -> NaverShoppingApiError:
    status_code = response.status_code

    error_code, error_message = (
        _extract_error_response(response)
    )

    if status_code == 400:
        category = "request_error"
        retryable = False

    elif status_code == 401:
        category = "authentication_error"
        retryable = False

    elif status_code == 403:
        category = "permission_error"
        retryable = False

    elif status_code == 404:
        category = "endpoint_error"
        retryable = False

    elif status_code == 429:
        category = "rate_limit"
        retryable = True

    elif status_code >= 500:
        category = "server_error"
        retryable = True

    else:
        category = "http_error"
        retryable = (
            status_code
            in RETRYABLE_STATUS_CODES
        )

    message = (
        "네이버 쇼핑 API 호출 실패: "
        f"HTTP {status_code}"
    )

    if error_code:
        message += f", 코드={error_code}"

    if error_message:
        message += f", 메시지={error_message}"

    return NaverShoppingApiError(
        message,
        category=category,
        retryable=retryable,
        status_code=status_code,
        error_code=error_code,
        error_message=error_message,
        attempt_count=attempt_count,
    )


def _get_retry_delay(
    attempt_count: int,
    retry_base_seconds: float,
    response: requests.Response | None = None,
) -> float:
    """
    1초, 2초, 4초 형태의 지수 대기시간을 만든다.

    Retry-After 헤더가 숫자로 제공되면
    그 값을 우선 사용한다.
    """
    if response is not None:
        retry_after = str(
            response.headers.get(
                "Retry-After",
                "",
            )
        ).strip()

        try:
            if retry_after:
                return max(
                    0.0,
                    float(retry_after),
                )
        except ValueError:
            pass

    return max(
        0.0,
        retry_base_seconds
        * (2 ** (attempt_count - 1)),
    )


def _sleep_before_retry(
    *,
    attempt_count: int,
    retry_base_seconds: float,
    response: requests.Response | None = None,
) -> None:
    delay_seconds = _get_retry_delay(
        attempt_count=attempt_count,
        retry_base_seconds=(
            retry_base_seconds
        ),
        response=response,
    )

    if delay_seconds > 0:
        time.sleep(delay_seconds)


def fetch_shopping_response(
    keyword: str,
    display: int = 20,
    sort: str = "sim",
    *,
    timeout_seconds: float = (
        DEFAULT_TIMEOUT_SECONDS
    ),
    max_attempts: int = (
        DEFAULT_MAX_ATTEMPTS
    ),
    retry_base_seconds: float = (
        DEFAULT_RETRY_BASE_SECONDS
    ),
) -> dict[str, Any]:
    """
    네이버 쇼핑 API를 호출하고 전체 응답 요약을 반환한다.

    재시도 대상:
    - 타임아웃
    - 연결 오류
    - HTTP 429
    - HTTP 500 계열
    - 일시적인 JSON 파싱 오류
    - 비정상 응답 구조

    검색결과가 없는 경우:
    - 오류로 처리하지 않는다.
    - items=[]인 정상 응답을 반환한다.
    """
    normalized_keyword = _validate_request(
        keyword=keyword,
        display=display,
        sort=sort,
        max_attempts=max_attempts,
    )

    headers = {
        "X-Naver-Client-Id": (
            NAVER_CLIENT_ID
        ),
        "X-Naver-Client-Secret": (
            NAVER_CLIENT_SECRET
        ),
    }

    params = {
        "query": normalized_keyword,
        "display": display,
        "start": 1,
        "sort": sort,
    }

    last_error: (
        NaverShoppingApiError | None
    ) = None

    for attempt_count in range(
        1,
        max_attempts + 1,
    ):
        try:
            response = requests.get(
                NAVER_SHOPPING_API_URL,
                headers=headers,
                params=params,
                timeout=timeout_seconds,
            )

        except requests.Timeout as error:
            api_error = NaverShoppingApiError(
                (
                    "네이버 쇼핑 API 응답시간을 "
                    "초과했습니다."
                ),
                category="timeout",
                retryable=True,
                error_message=str(error),
                attempt_count=attempt_count,
            )

            last_error = api_error

            if attempt_count >= max_attempts:
                raise api_error from error

            _sleep_before_retry(
                attempt_count=attempt_count,
                retry_base_seconds=(
                    retry_base_seconds
                ),
            )

            continue

        except requests.ConnectionError as error:
            api_error = NaverShoppingApiError(
                (
                    "네이버 쇼핑 API 연결에 "
                    "실패했습니다."
                ),
                category="network_error",
                retryable=True,
                error_message=str(error),
                attempt_count=attempt_count,
            )

            last_error = api_error

            if attempt_count >= max_attempts:
                raise api_error from error

            _sleep_before_retry(
                attempt_count=attempt_count,
                retry_base_seconds=(
                    retry_base_seconds
                ),
            )

            continue

        except requests.RequestException as error:
            api_error = NaverShoppingApiError(
                (
                    "네이버 쇼핑 API 요청 중 "
                    "통신 오류가 발생했습니다."
                ),
                category="network_error",
                retryable=True,
                error_message=str(error),
                attempt_count=attempt_count,
            )

            last_error = api_error

            if attempt_count >= max_attempts:
                raise api_error from error

            _sleep_before_retry(
                attempt_count=attempt_count,
                retry_base_seconds=(
                    retry_base_seconds
                ),
            )

            continue

        if response.status_code != 200:
            api_error = _classify_http_error(
                response=response,
                attempt_count=attempt_count,
            )

            last_error = api_error

            if (
                api_error.retryable
                and attempt_count < max_attempts
            ):
                _sleep_before_retry(
                    attempt_count=attempt_count,
                    retry_base_seconds=(
                        retry_base_seconds
                    ),
                    response=response,
                )

                continue

            raise api_error

        try:
            payload = response.json()

        except ValueError as error:
            api_error = NaverShoppingApiError(
                (
                    "네이버 쇼핑 API 응답을 "
                    "JSON으로 해석하지 못했습니다."
                ),
                category=(
                    "response_parse_error"
                ),
                retryable=True,
                status_code=(
                    response.status_code
                ),
                error_message=str(error),
                attempt_count=attempt_count,
            )

            last_error = api_error

            if attempt_count >= max_attempts:
                raise api_error from error

            _sleep_before_retry(
                attempt_count=attempt_count,
                retry_base_seconds=(
                    retry_base_seconds
                ),
                response=response,
            )

            continue

        if not isinstance(payload, dict):
            api_error = NaverShoppingApiError(
                (
                    "네이버 쇼핑 API 응답이 "
                    "JSON 객체 형식이 아닙니다."
                ),
                category=(
                    "response_format_error"
                ),
                retryable=True,
                status_code=(
                    response.status_code
                ),
                attempt_count=attempt_count,
            )

            last_error = api_error

            if attempt_count >= max_attempts:
                raise api_error

            _sleep_before_retry(
                attempt_count=attempt_count,
                retry_base_seconds=(
                    retry_base_seconds
                ),
                response=response,
            )

            continue

        items = payload.get("items")

        if not isinstance(items, list):
            api_error = NaverShoppingApiError(
                (
                    "네이버 쇼핑 API 응답의 "
                    "items가 배열 형식이 아닙니다."
                ),
                category=(
                    "response_format_error"
                ),
                retryable=True,
                status_code=(
                    response.status_code
                ),
                attempt_count=attempt_count,
            )

            last_error = api_error

            if attempt_count >= max_attempts:
                raise api_error

            _sleep_before_retry(
                attempt_count=attempt_count,
                retry_base_seconds=(
                    retry_base_seconds
                ),
                response=response,
            )

            continue

        # items=[]도 정상 성공으로 반환한다.
        return {
            "items": items,
            "total": _safe_int(
                payload.get("total"),
                0,
            ),
            "start": _safe_int(
                payload.get("start"),
                1,
            ),
            "display": _safe_int(
                payload.get("display"),
                len(items),
            ),
            "last_build_date": str(
                payload.get(
                    "lastBuildDate",
                    "",
                )
            ).strip(),
            "received_count": len(items),
            "attempt_count": attempt_count,
        }

    if last_error is not None:
        raise last_error

    raise NaverShoppingApiError(
        "네이버 쇼핑 API 호출에 실패했습니다.",
        category="unknown_error",
        retryable=False,
        attempt_count=max_attempts,
    )


def fetch_shopping_items(
    keyword: str,
    display: int = 20,
    sort: str = "sim",
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """
    이전 코드와의 호환을 위한 함수.

    새 코드에서는 fetch_shopping_response() 사용을 권장한다.
    """
    response = fetch_shopping_response(
        keyword=keyword,
        display=display,
        sort=sort,
        **kwargs,
    )

    return response["items"]