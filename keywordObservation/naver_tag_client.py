from __future__ import annotations

from typing import Any, Iterable

import requests

from keywordObservation.naver_commerce_auth import (
    NaverCommerceAuthenticator,
    NaverCommerceAuthError,
)
from keywordObservation.tag_text_utils import (
    deduplicate_tags,
    normalize_keyword,
    normalize_tag_text,
)


BASE_URL = "https://api.commerce.naver.com/external"


class NaverTagApiError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        payload: Any = None,
        trace_id: str = "",
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload
        self.trace_id = trace_id
        self.retryable = retryable



def _response_payload(
    response: requests.Response,
) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text



def _trace_id(
    response: requests.Response,
) -> str:
    return str(
        response.headers.get("GNCP-GW-Trace-ID")
        or response.headers.get("gncp-gw-trace-id")
        or ""
    )


class NaverTagClient:
    def __init__(
        self,
        *,
        authenticator: NaverCommerceAuthenticator | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.session = session or requests.Session()
        self.authenticator = authenticator or NaverCommerceAuthenticator(
            session=self.session
        )

    def _request(
        self,
        *,
        method: str,
        path: str,
        params: Any = None,
    ) -> dict[str, Any]:
        last_response: requests.Response | None = None

        for attempt in (1, 2):
            try:
                access_token = self.authenticator.get_access_token(
                    force_refresh=(attempt == 2)
                )
            except NaverCommerceAuthError:
                raise

            try:
                response = self.session.request(
                    method=method,
                    url=BASE_URL + path,
                    headers={
                        "Accept": "application/json;charset=UTF-8",
                        "Authorization": f"Bearer {access_token}",
                    },
                    params=params,
                    timeout=30,
                )
            except requests.RequestException as error:
                raise NaverTagApiError(
                    f"네이버 태그 API 요청이 실패했습니다: {error}",
                    retryable=True,
                ) from error

            last_response = response
            payload = _response_payload(response)
            trace_id = _trace_id(response)

            if response.ok:
                return {
                    "payload": payload,
                    "status_code": response.status_code,
                    "trace_id": trace_id,
                    "request_url": response.url,
                    "attempt_count": attempt,
                }

            body_code = ""
            if isinstance(payload, dict):
                body_code = str(payload.get("code", ""))

            should_refresh = (
                attempt == 1
                and response.status_code == 401
                and body_code in {"", "GW.AUTHN", "UNAUTHORIZED"}
            )

            if should_refresh:
                self.authenticator.clear_token()
                continue

            raise NaverTagApiError(
                (
                    "네이버 태그 API 호출 실패: "
                    f"HTTP {response.status_code}"
                ),
                status_code=response.status_code,
                payload=payload,
                trace_id=trace_id,
                retryable=response.status_code in {429, 500, 502, 503, 504},
            )

        raise NaverTagApiError(
            "네이버 태그 API 요청에 실패했습니다.",
            status_code=(
                last_response.status_code
                if last_response is not None
                else None
            ),
            payload=(
                _response_payload(last_response)
                if last_response is not None
                else None
            ),
            trace_id=(
                _trace_id(last_response)
                if last_response is not None
                else ""
            ),
        )

    def search_recommend_tags(
        self,
        keyword: str,
    ) -> dict[str, Any]:
        normalized_keyword = normalize_keyword(keyword)

        if not normalized_keyword:
            raise ValueError("추천 태그 검색어가 비어 있습니다.")

        response_data = self._request(
            method="GET",
            path="/v2/tags/recommend-tags",
            params={"keyword": normalized_keyword},
        )

        payload = response_data.get("payload")

        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict):
            items = (
                payload.get("contents")
                or payload.get("items")
                or payload.get("data")
                or payload.get("results")
                or []
            )
        else:
            items = []

        tags: list[dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            text = normalize_tag_text(item.get("text", ""))

            if not text:
                continue

            tags.append(
                {
                    "text": text,
                    "code": item.get("code"),
                }
            )

        response_data["keyword"] = normalized_keyword
        response_data["tags"] = deduplicate_tags(tags)
        response_data["result_count"] = len(response_data["tags"])

        return response_data

    def check_restricted_tags(
        self,
        tags: Iterable[str],
    ) -> dict[str, Any]:
        normalized_tags = []
        seen: set[str] = set()

        for tag in tags:
            normalized = normalize_tag_text(tag)
            key = normalized.casefold()

            if normalized and key not in seen:
                seen.add(key)
                normalized_tags.append(normalized)

        if not normalized_tags:
            raise ValueError("제한 여부를 검사할 태그가 없습니다.")

        # 공식 규격: Query Parameters tags string[]
        params = [
            ("tags", tag)
            for tag in normalized_tags
        ]

        response_data = self._request(
            method="GET",
            path="/v2/tags/restricted-tags",
            params=params,
        )

        payload = response_data.get("payload")
        results: list[dict[str, Any]] = []

        if isinstance(payload, list):
            for item in payload:
                if not isinstance(item, dict):
                    continue

                tag = normalize_tag_text(item.get("tag", ""))

                if not tag:
                    continue

                results.append(
                    {
                        "tag": tag,
                        "restricted": bool(item.get("restricted", False)),
                    }
                )

        response_data["requested_tags"] = normalized_tags
        response_data["results"] = results

        return response_data
